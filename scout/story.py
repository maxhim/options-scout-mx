"""Market story: 5-8 plain sentences about yesterday and today, in Russian and English.

With ANTHROPIC_API_KEY the numbers and headlines go to Claude, which writes the text; it may only
use the facts it is given. Without a key, or if the call fails, a template builds a shorter text
from the same numbers.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re

from . import sectors

MODEL = os.environ.get("SCOUT_MODEL", "claude-sonnet-5-5")
WD_RU = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]


def _p(x, digits=1):
    return f"{x * 100:+.{digits}f}%".replace("-", "−") if x is not None else "—"


def facts(provider, as_of: dt.date, sm: dict, vix, vix_chg, events, log=print) -> dict:
    """Everything the text may mention, already computed. Headlines for the biggest movers explain the moves."""
    movers = (sm.get("losers") or []) + (sm.get("gainers") or []) + (sm.get("losers_yday") or []) + (sm.get("gainers_yday") or [])
    tickers = list(dict.fromkeys(m["ticker"] for m in sorted(movers, key=lambda m: -abs(m["chg"]))))[:5]
    why = {}
    for t in tickers:
        try:
            why[t] = [n["title"] for n in provider.news([t], 2)]
        except Exception as ex:
            log(f"news {t}: {ex}")
    pct = lambda items: [{**i, "chg": round(i["chg"] * 100, 2)} for i in items or []]
    sec = lambda items: [{"sector": sectors.label(i["sector"], "en"), "chg": round(i["chg"] * 100, 2)} for i in items or []]
    idx = lambda items, k: {i["name"]: round(i[k] * 100, 2) for i in items or [] if i.get(k) is not None}
    other = {}
    for o in sm.get("other") or []:
        key = "today" if sm.get("live") else "yday"
        if o["name"] == "10Y":
            other["10Y yield %"] = round(o["last"], 2)
            if o.get(key + "_abs") is not None:
                other["10Y change bp"] = round(o[key + "_abs"] * 100)
        else:
            other[o["name"]] = {"last": round(o["last"], 1), "chg %": round((o.get(key) or 0) * 100, 2)}
    return {
        "date": as_of.isoformat(), "weekday": as_of.strftime("%A"),
        "today_session_has_data": bool(sm.get("live")),
        "yesterday_indices_pct": idx(sm.get("indices"), "yday"),
        "today_indices_pct": idx(sm.get("indices"), "today") if sm.get("live") else {},
        "today_futures_pct": idx(sm.get("futures"), "today"),
        "yesterday_sectors_pct": sec(sm.get("sectors_yday")),
        "today_sectors_pct": sec(sm.get("sectors_today")),
        "yesterday_biggest_moves_pct": pct((sm.get("losers_yday") or []) + (sm.get("gainers_yday") or [])),
        "today_biggest_moves_pct": pct((sm.get("losers") or []) + (sm.get("gainers") or [])),
        "headlines_for_movers": why,
        "market_headlines": [n["title"] for n in sm.get("news") or []],
        "vix": round(vix, 1) if vix is not None else None,
        "vix_change_pct": round(vix_chg * 100, 1) if vix_chg is not None else None,
        "rates_oil_crypto": other,
        "macro_events": [{"name": e["name"], "day": e.get("day_ny"), "time_ny": e.get("ny"), "actual": e.get("actual"),
                          "expected": e.get("expected"), "importance": e.get("imp")}
                         for e in events or [] if e.get("day_ny") and e["day_ny"] <= as_of.isoformat()][-8:],
    }


PROMPT = """You write the daily market summary for a stock and options idea service.
Write a short story of what happened in the US stock market yesterday and today: 5-8 sentences, one paragraph.
Rules:
- Use only the facts in the JSON below. Do not invent numbers, events or causes.
- Name a cause only if a headline supports it; otherwise describe what moved without a reason.
- Tell a story, not a list of percentages: what led, what lagged, rotation between groups, whether today continued or reversed yesterday, what volatility, rates and oil say. At most 6 numbers in total.
- If today_session_has_data is false, "today" is the pre-market: use futures and say the session has not opened yet.
- No trading advice, no predictions, no markdown, no emoji.
Return JSON only: {"ru": "<Russian text>", "en": "<English text>"}. The Russian must be natural Russian, not a translation; keep tickers in Latin letters.

FACTS:
"""


def ask_claude(f: dict) -> dict | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    import requests

    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": MODEL, "max_tokens": 1200,
              "messages": [{"role": "user", "content": PROMPT + json.dumps(f, ensure_ascii=False, default=str)}]},
        timeout=90,
    )
    r.raise_for_status()
    text = "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")
    m = re.search(r"\{.*\}", text, re.S)
    out = json.loads(m.group(0)) if m else {}
    if isinstance(out.get("ru"), str) and isinstance(out.get("en"), str) and out["ru"].strip() and out["en"].strip():
        return {"ru": out["ru"].strip(), "en": out["en"].strip()}
    return None


def template(sm: dict, vix, lang: str) -> str:
    """Fallback without a model: a few sentences from the same numbers."""
    ru = lang == "ru"
    t = (lambda a, b: a if ru else b)
    idx = {i["name"]: i for i in sm.get("indices") or []}
    out = []

    def day(key, label):
        s, n, d = (idx.get(k, {}).get(key) for k in ("S&P 500", "Nasdaq-100", "Dow"))
        if s is None:
            return
        line = t(f"{label} S&P 500 {_p(s)}", f"{label} the S&P 500 {('rose' if s >= 0 else 'fell')} {abs(s) * 100:.1f}%")
        if n is not None and d is not None:
            if n - d <= -0.012:
                line += t(f": техи отставали (Nasdaq-100 {_p(n)}), а Dow держался лучше ({_p(d)}) — деньги уходили из роста в старую экономику",
                          f": tech lagged (Nasdaq-100 {_p(n)}) while the Dow held up better ({_p(d)}), money rotating out of growth")
            elif n - d >= 0.012:
                line += t(f": вели техи (Nasdaq-100 {_p(n)}), Dow отставал ({_p(d)})",
                          f": tech led (Nasdaq-100 {_p(n)}), the Dow lagged ({_p(d)})")
            else:
                line += t(f", Nasdaq-100 {_p(n)}, Dow {_p(d)}", f", Nasdaq-100 {_p(n)}, Dow {_p(d)}")
        out.append(line + ".")

    def secs(items, movers, label):
        if not items:
            return
        lo, hi = items[0], items[-1]
        name = lambda g: sectors.label(g, lang)
        line = t(f"{label} хуже всех были {name(lo['sector'])} ({_p(lo['chg'])})", f"{label} {name(lo['sector'])} were weakest ({_p(lo['chg'])})")
        if hi["sector"] != lo["sector"] and hi["chg"] > 0:
            line += t(f", лучше всех — {name(hi['sector'])} ({_p(hi['chg'])})", f", {name(hi['sector'])} strongest ({_p(hi['chg'])})")
        big = max(movers or [], key=lambda m: abs(m["chg"]), default=None)
        if big and abs(big["chg"]) >= 0.05:
            line += t(f"; сильнее всего двигалась {big['ticker']} ({_p(big['chg'])})", f"; the biggest mover was {big['ticker']} ({_p(big['chg'])})")
        out.append(line + ".")

    day("yday", t("Вчера", "Yesterday"))
    secs(sm.get("sectors_yday"), (sm.get("losers_yday") or []) + (sm.get("gainers_yday") or []), t("Среди секторов", "Among sectors,"))
    if sm.get("live"):
        y, d = idx.get("S&P 500", {}).get("yday"), idx.get("S&P 500", {}).get("today")
        day("today", t("Сегодня", "Today"))
        if y is not None and d is not None and abs(y) > 0.003 and abs(d) > 0.003:
            out.append(t("Это продолжение вчерашнего движения." if (y > 0) == (d > 0) else "Рынок развернулся после вчерашнего.",
                         "That extended yesterday's move." if (y > 0) == (d > 0) else "The market reversed yesterday's move."))
        secs(sm.get("sectors_today"), (sm.get("losers") or []) + (sm.get("gainers") or []), t("Сегодня", "Today"))
    else:
        f = {i["name"]: i.get("today") for i in sm.get("futures") or []}
        if f.get("S&P 500 fut") is not None:
            out.append(t(f"Торги ещё не открылись, фьючерс на S&P 500 {_p(f['S&P 500 fut'])}.",
                         f"The session has not opened yet; S&P 500 futures are {_p(f['S&P 500 fut'])}."))
    if vix is not None:
        out.append(t(f"VIX {vix:.1f}: " + ("страх высокий, опционы дорогие." if vix >= 25 else "волатильность выше нормы." if vix >= 20 else "волатильность спокойная."),
                     f"VIX {vix:.1f}: " + ("fear is high and options are expensive." if vix >= 25 else "volatility is above normal." if vix >= 20 else "volatility is calm.")))
    return " ".join(out)


def build(provider, as_of, sm, vix, vix_chg, events, log=print) -> dict:
    """{"ru", "en", "source": "ai"|"auto"}"""
    try:
        ai = ask_claude(facts(provider, as_of, sm, vix, vix_chg, events, log))
        if ai:
            return ai | {"source": "ai"}
    except Exception as ex:
        log(f"market story via Claude failed, using the template: {str(ex)[:200]}")
    return {"ru": template(sm, vix, "ru"), "en": template(sm, vix, "en"), "source": "auto"}
