"""Monthly refresh of the candidate list (config.yaml -> universe.tickers).

Daily runs still filter the list by price, dollar volume and option open interest;
this only decides who is a candidate at all. Source: Yahoo screener (yfinance).
"""
from __future__ import annotations

import re
from pathlib import Path

TARGET = 120      # list size
KEEP_RANK = 200   # a current name stays while it ranks within this many (avoids monthly churn)


def screen_yahoo(min_cap=10e9, min_price=30, min_avg_vol=1_000_000, pages=2) -> list[dict]:
    import yfinance as yf
    from yfinance import EquityQuery as Q

    q = Q("and", [Q("eq", ["region", "us"]), Q("gte", ["intradaymarketcap", min_cap]),
                  Q("gte", ["intradayprice", min_price]), Q("gte", ["avgdailyvol3m", min_avg_vol])])
    out = []
    for p in range(pages):  # Yahoo returns at most 250 rows per request
        res = yf.screen(q, offset=p * 250, size=250, sortField="avgdailyvol3m", sortAsc=False)
        quotes = (res or {}).get("quotes", [])
        out += quotes
        if len(quotes) < 250:
            break
    return out


def rank(quotes: list[dict]) -> list[str]:
    """Common stocks ranked by average dollar volume (price x 3-month average volume)."""
    rows = []
    for q in quotes:
        sym = q.get("symbol") or ""
        if q.get("quoteType", "EQUITY") != "EQUITY" or not sym or "." in sym or "-" in sym:
            continue  # ETFs, preferred shares, foreign share classes
        px = q.get("regularMarketPrice") or 0
        vol = q.get("averageDailyVolume3Month") or q.get("averageDailyVolume10Day") or 0
        rows.append((px * vol, sym))
    return [s for _, s in sorted(rows, reverse=True)]


def merge(current: list[str], ranked: list[str]) -> list[str]:
    keep = set(ranked[:KEEP_RANK])
    new = [t for t in current if t in keep]
    for t in ranked:
        if len(new) >= TARGET:
            break
        if t not in new:
            new.append(t)
    return new


def write_config(path: Path, tickers: list[str]):
    text = path.read_text(encoding="utf-8")
    lines, row = [], []
    for t in tickers:
        row.append(t)
        if len(", ".join(row)) > 96:
            lines.append(", ".join(row))
            row = []
    if row:
        lines.append(", ".join(row))
    block = "  tickers: [" + (",\n            ".join(lines)) + "]"
    new, n = re.subn(r"  tickers: \[[^\]]*\]", block, text, count=1)
    if not n:
        raise RuntimeError("universe.tickers not found in config")
    path.write_text(new, encoding="utf-8")


def refresh(cfg_path: Path, current: list[str], screen=screen_yahoo) -> dict:
    ranked = rank(screen())
    if len(ranked) < 50:  # Yahoo hiccup: never wipe the list on a bad response
        raise RuntimeError(f"screener returned only {len(ranked)} stocks, list left unchanged")
    new = merge(current, ranked)
    write_config(cfg_path, new)
    return {"added": [t for t in new if t not in current], "removed": [t for t in current if t not in new], "size": len(new)}


def render(diff: dict) -> str:
    def lst(xs):
        return ", ".join(xs) if xs else "нет"
    return (f"🗂 <b>Список кандидатов обновлён</b> · {diff['size']} бумаг\n"
            f"➕ {lst(diff['added'])}\n➖ {lst(diff['removed'])}\n"
            "<i>Отбор: акции США, капитализация от $10 млрд, цена от $30, по долларовому обороту.</i>")
