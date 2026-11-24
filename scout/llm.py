"""Optional plain-language summary via the Anthropic API (env: ANTHROPIC_API_KEY).

The model only rewrites numbers the engine already computed; it never picks trades.
"""
from __future__ import annotations

import json
import os

MODEL = os.environ.get("SCOUT_MODEL", "claude-sonnet-5-5")


def summarize(brief_text: str, facts: dict) -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    import requests

    prompt = (
        "Ты помощник трейдера. Ниже готовый бриф и факты в JSON, посчитанные кодом. "
        "Напиши 4-6 коротких строк по-русски: главное за день и на что смотреть. "
        "Используй только числа из данных, ничего не придумывай, не давай новых сделок.\n\n"
        f"БРИФ:\n{brief_text}\n\nФАКТЫ:\n{json.dumps(facts, ensure_ascii=False, default=str)[:12000]}"
    )
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": MODEL, "max_tokens": 600, "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text").strip()
