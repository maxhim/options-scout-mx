"""Sector groups for the diversification cap and the labels in the brief.

Finer than GICS where it matters for risk: semiconductors are split from software and hardware,
because a basket of chip shorts is one bet, not five. Unknown tickers (e.g. added by the monthly
universe refresh) fall back to the data source's sector, then to their own group (never capped together).
"""
from __future__ import annotations

GROUPS = {
    "semis": ("Полупроводники", "Semiconductors",
              "NVDA AMD AVGO INTC QCOM MU TXN AMAT LRCX KLAC MRVL ARM TSM SNDK ON ADI NXPI MCHP ASML"),
    "hardware": ("Железо и хранение", "Hardware & storage", "AAPL DELL SMCI WDC STX CSCO ANET HPE HPQ"),
    "software": ("Софт и облака", "Software & cloud",
                 "MSFT ORCL CRM ADBE NOW SNOW PLTR CRWD PANW ZS NET DDOG IBM APP INTU WDAY MDB TEAM"),
    "internet": ("Интернет и платформы", "Internet & platforms",
                 "GOOGL GOOG META AMZN NFLX SHOP UBER ABNB DASH RDDT BABA PDD W SPOT PINS SNAP JD"),
    "fintech": ("Финтех и крипто", "Fintech & crypto", "COIN HOOD MSTR XYZ PYPL SOFI AFRM"),
    "finance": ("Банки и финансы", "Banks & finance", "JPM BAC WFC C GS MS SCHW AXP V MA BLK BX KKR"),
    "health": ("Здравоохранение", "Healthcare",
               "LLY UNH JNJ PFE MRK ABBV AMGN GILD VRTX ISRG TMO NVO HIMS REGN BMY CVS DHR"),
    "consumer": ("Потребительский сектор", "Consumer",
                 "WMT COST TGT HD LOW NKE SBUX MCD CMG LULU DIS KO PEP PG TJX BKNG"),
    "energy": ("Нефть и газ", "Oil & gas", "XOM CVX OXY COP SLB EOG HAL"),
    "industrial": ("Промышленность и оборона", "Industrials & defense", "BA CAT DE GE LMT RTX UPS FDX HON NOC"),
    "power": ("Энергетика и электросети", "Power & clean energy", "GEV CEG VST FSLR ENPH NEE"),
    "autos": ("Автопром", "Autos", "TSLA RACE GM F RIVN"),
}
_BY_TICKER = {t: g for g, (_, _, ts) in GROUPS.items() for t in ts.split()}
_YF = {  # data-source sector -> our group, for tickers not listed above
    "Technology": "software", "Communication Services": "internet", "Financial Services": "finance",
    "Healthcare": "health", "Consumer Cyclical": "consumer", "Consumer Defensive": "consumer",
    "Energy": "energy", "Industrials": "industrial", "Utilities": "power",
}


def group(ticker: str, source_sector: str | None = None) -> str:
    if ticker in _BY_TICKER:
        return _BY_TICKER[ticker]
    if source_sector in _YF:
        return _YF[source_sector]
    return "solo:" + ticker  # unknown: its own group, never capped together with others


def label(g: str, lang: str = "ru") -> str:
    if g in GROUPS:
        return GROUPS[g][1 if lang == "en" else 0]
    return ""


def cap(rows: list, max_per: int, counts: dict, key=lambda r: r["sector"]) -> list:
    """Keep ranking order, skip rows whose sector already has max_per picks. Updates counts."""
    out = []
    for r in rows:
        g = key(r)
        if counts.get(g, 0) >= max_per:
            continue
        counts[g] = counts.get(g, 0) + 1
        out.append(r)
    return out
