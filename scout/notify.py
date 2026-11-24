"""Telegram delivery (optional). env: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID."""
from __future__ import annotations

import os


def telegram(text: str, url: str | None = None) -> bool:
    token, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    import requests

    if url:
        text += f"\n\nПолный бриф: {url}"
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text[:4000], "disable_web_page_preview": True}, timeout=20)
    r.raise_for_status()
    return True
