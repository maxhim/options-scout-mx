"""Telegram subscribers without a server.

On every scheduled run the engine pulls new bot messages (getUpdates), applies /start and /stop,
answers them, and stores the list in data/subscribers.enc, encrypted with a key derived from
TELEGRAM_TOKEN, so the public repo never exposes who is subscribed.
The owner (TELEGRAM_CHAT_ID) always receives everything, in Russian.

Limitation: replies to /start arrive at the next run (up to a few hours), not instantly;
instant replies would need an always-on webhook.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

WELCOME = {
    "ru": ("🦅 <b>Falco Scout</b>: подписка оформлена.\n"
           "Бриф приходит по будням в 21:35 по Мадриду (15:35 Нью-Йорк), днём — алерты о сильных идеях. "
           "По пятницам — итоги недели.\nОтписаться: /stop · English: /start en\n"
           "<i>Аналитика, не инвестиционный совет.</i>"),
    "en": ("🦅 <b>Falco Scout</b>: you're subscribed.\n"
           "The brief arrives on weekdays at 3:35 pm New York time, plus intraday alerts on strong ideas "
           "and a weekly recap on Fridays.\nUnsubscribe: /stop · Русский: /start ru\n"
           "<i>Analytics, not investment advice.</i>"),
}
BYE = {"ru": "Подписка отменена. Вернуться: /start", "en": "Unsubscribed. Come back any time: /start"}


def _fernet(token: str):
    from cryptography.fernet import Fernet
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(("falco-subs:" + token).encode()).digest()))


def load(path: Path, token: str) -> dict:
    if not path.exists():
        return {"offset": 0, "subs": {}}
    return json.loads(_fernet(token).decrypt(path.read_bytes()))


def save(path: Path, token: str, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_fernet(token).encrypt(json.dumps(data, sort_keys=True).encode()))


def _lang(text: str, user: dict) -> str:
    arg = text.split(maxsplit=1)[1].strip().lower() if " " in text else ""
    if arg in ("ru", "en"):
        return arg
    return "ru" if str(user.get("language_code", "")).startswith(("ru", "uk", "be", "kk")) else "en"


def _who(user: dict) -> str:
    if user.get("username"):
        return "@" + user["username"]
    return " ".join(x for x in (user.get("first_name"), user.get("last_name")) if x) or "без имени"


def sync(token: str, data: dict, send, get_updates, owner: str | None = None) -> list[str]:
    """Apply /start and /stop from new messages. Returns a short log; tells the owner who joined or left."""
    log, events = [], []
    updates = get_updates(data.get("offset", 0))
    for u in updates:
        data["offset"] = max(data.get("offset", 0), u["update_id"] + 1)
        msg = u.get("message") or {}
        chat, text = msg.get("chat", {}), (msg.get("text") or "").strip()
        if chat.get("type") != "private" or not text.startswith("/"):
            continue
        cid, cmd = str(chat["id"]), text.split()[0].split("@")[0].lower()
        user = msg.get("from", {})
        if cmd == "/start":
            lang = _lang(text, user)
            new = cid not in data["subs"]
            data["subs"][cid] = {"lang": lang, "since": data["subs"].get(cid, {}).get("since") or dt.date.today().isoformat(),
                                 "who": _who(user)}
            send(cid, WELCOME[lang])
            log.append(f"+{lang}")
            if new and cid != str(owner):
                events.append(f"🆕 Новый подписчик: {_who(user)} ({lang})")
        elif cmd == "/stop" and cid in data["subs"]:
            sub = data["subs"].pop(cid)
            send(cid, BYE[sub["lang"]])
            log.append("-")
            if cid != str(owner):
                events.append(f"➖ Отписался: {sub.get('who') or _who(user)}")
    if events and owner:
        others = len([c for c in data["subs"] if c != str(owner)])
        send(str(owner), "\n".join(events) + f"\nВсего подписчиков (кроме тебя): {others}")
    return log


def recipients(data: dict, owner: str | None) -> dict[str, str]:
    """chat_id -> language; the owner always gets Russian."""
    out = {cid: s["lang"] for cid, s in data.get("subs", {}).items()}
    if owner:
        out[str(owner)] = "ru"
    return out


def telegram_api(token: str):
    import requests

    base = f"https://api.telegram.org/bot{token}"

    def get_updates(offset):
        r = requests.get(f"{base}/getUpdates", params={"offset": offset, "timeout": 0,
                                                       "allowed_updates": json.dumps(["message"])}, timeout=20)
        r.raise_for_status()
        return r.json().get("result", [])

    def send(chat_id, text):
        try:
            requests.post(f"{base}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                                                        "disable_web_page_preview": True}, timeout=20)
        except Exception as ex:  # one blocked user must not stop the rest
            print("telegram send failed:", ex)

    return get_updates, send


def run_sync(path: Path) -> dict | None:
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        return None
    data = load(path, token)
    get_updates, send = telegram_api(token)
    try:
        log = sync(token, data, send, get_updates, os.environ.get("TELEGRAM_CHAT_ID"))
        if log:
            print("subscribers:", " ".join(log), "· total", len(data["subs"]))
    except Exception as ex:
        print("subscriber sync skipped:", ex)
    save(path, token, data)
    return data
