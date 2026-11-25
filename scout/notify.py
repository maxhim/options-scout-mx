"""Telegram delivery (optional). env: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID. Text is Telegram HTML."""
from __future__ import annotations

import html
import os
import time

LIMIT = 4000
LINK = {"ru": "Полный бриф", "en": "Full brief"}


def _fit(text: str) -> str:
    """Cut on line boundaries so HTML tags are never split."""
    if len(text) <= LIMIT:
        return text
    out, n = [], 0
    for line in text.split("\n"):
        if n + len(line) + 1 > LIMIT - 40:
            out.append("…")
            break
        out.append(line)
        n += len(line) + 1
    return "\n".join(out)


def _post(token, chat, text):
    import requests

    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": _fit(text), "parse_mode": "HTML",
                            "disable_web_page_preview": True}, timeout=20)
    return r.ok


def with_link(text: str, url: str | None, lang: str = "ru") -> str:
    if not url:
        return text
    return text + f'\n\n🔗 <a href="{html.escape(url, quote=True)}">{LINK[lang]}</a>'


def site_url(lang: str) -> str | None:
    base = os.environ.get("SCOUT_REPORT_URL")
    if not base:
        return None
    return base.rstrip("/") + ("/en/" if lang == "en" else "/")


def telegram(text: str, url: str | None = None) -> bool:
    """Owner only (test runs, service messages)."""
    token, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    return _post(token, chat, with_link(text, url))


def broadcast(texts: dict[str, str], recipients: dict[str, str]) -> int:
    """texts: lang -> message; recipients: chat_id -> lang. Returns messages delivered."""
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        return 0
    sent = 0
    for chat, lang in recipients.items():
        text = texts.get(lang) or texts.get("ru")
        if not text:
            continue
        sent += bool(_post(token, chat, with_link(text, site_url(lang), lang)))
        time.sleep(0.05)  # well under Telegram's 30 messages/second
    return sent
