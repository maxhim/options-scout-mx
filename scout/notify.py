"""Telegram delivery (optional). env: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID. Text is Telegram HTML."""
from __future__ import annotations

import html
import os

LIMIT = 4000


def _fit(text: str) -> str:
    """Cut on line boundaries so HTML tags are never split."""
    if len(text) <= LIMIT:
        return text
    out, n = [], 0
    for line in text.split("\n"):
        if n + len(line) + 1 > LIMIT - 40:
            out.append("… (полностью — на странице брифа)")
            break
        out.append(line)
        n += len(line) + 1
    return "\n".join(out)


def telegram(text: str, url: str | None = None) -> bool:
    token, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    import requests

    if url:
        text += f'\n\n🔗 <a href="{html.escape(url, quote=True)}">Полный бриф</a>'
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": _fit(text), "parse_mode": "HTML",
                            "disable_web_page_preview": True}, timeout=20)
    r.raise_for_status()
    return True
