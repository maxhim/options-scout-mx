"""Market tab: regime (VIX, SPY trend, breadth), macro calendar with local times, watchlist earnings."""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

NY, MAD = ZoneInfo("America/New_York"), ZoneInfo("Europe/Madrid")

HIGH = ("cpi", "consumer price", "pce", "nonfarm", "payroll", "unemployment rate", "fomc", "fed interest",
        "interest rate decision", "gdp", "ppi", "producer price", "retail sales", "ism ")
MEDIUM = ("jobless", "claims", "consumer confidence", "sentiment", "durable", "housing", "home sales",
          "industrial production", "pmi", "jolts", "trade balance", "fed ", "powell", "minutes", "adp")


def importance(name: str) -> str:
    n = name.lower() + " "
    if any(k in n for k in HIGH):
        return "high"
    if any(k in n for k in MEDIUM):
        return "medium"
    return "low"


def events_view(events: list[dict]) -> list[dict]:
    out = []
    for e in events:
        t = dt.datetime.fromisoformat(e["time"])
        out.append(e | {"imp": importance(e["name"]), "day": t.astimezone(MAD).date().isoformat(),
                        "day_ny": t.astimezone(NY).date().isoformat(),
                        "mad": t.astimezone(MAD).strftime("%H:%M"), "ny": t.astimezone(NY).strftime("%H:%M")})
    return [e for e in out if e["imp"] != "low"]


def regime(vix: float | None, vix_chg: float | None, spy_trend: float | None, breadth: float | None) -> dict:
    """Plain-language market state. Thresholds are rules of thumb, not a model."""
    if vix is not None and vix >= 25:
        key, label, note = "stress", "Стресс", "Опционы дорогие: недельные стоят с наценкой за страх. Брать ближе к деньгам и меньшим размером."
        label_en, note_en = "Stress", "Options are expensive: weeklies carry a fear premium. Stay closer to the money and size smaller."
    elif (vix is not None and vix >= 20) or (breadth is not None and breadth < 0.35):
        key, label, note = "nervous", "Нервный рынок", "Волатильность выше нормы или растёт мало бумаг: стопы выбивает чаще, размер позиций меньше."
        label_en, note_en = "Nervous", "Volatility above normal or few stocks rising: stops get hit more often, size positions smaller."
    elif spy_trend is not None and spy_trend > 0.2 and (breadth or 0) >= 0.55:
        key, label, note = "calm_up", "Спокойный рост", "Широкий рост и низкий VIX: идеи на рост работают лучше, опционы относительно дешёвые."
        label_en, note_en = "Calm uptrend", "Broad gains and a low VIX: long ideas work better, options are relatively cheap."
    elif spy_trend is not None and spy_trend < -0.2:
        key, label, note = "weak", "Слабость", "Индекс ниже средних: идеи на рост рискованнее, шорты по тренду в приоритете."
        label_en, note_en = "Weak", "The index is below its averages: long ideas are riskier, trend shorts come first."
    else:
        key, label, note = "neutral", "Нейтрально", "Явного режима нет: решают сигналы по отдельным бумагам."
        label_en, note_en = "Neutral", "No clear regime: single-stock signals decide."
    return {"key": key, "label": label, "note": note, "label_en": label_en, "note_en": note_en, "vix": vix, "vix_chg": vix_chg,
            "spy_trend": spy_trend, "breadth": breadth}


# What the summary tracks. Futures stand in for the indices before the open.
WATCH = {"^GSPC": "S&P 500", "^NDX": "Nasdaq-100", "^DJI": "Dow", "ES=F": "S&P 500 fut", "NQ=F": "Nasdaq fut",
         "YM=F": "Dow fut", "BZ=F": "Brent", "BTC-USD": "Bitcoin", "^TNX": "10Y"}


def _chg(bars, i):
    """Close-to-close change of bar i vs the bar before it."""
    try:
        return bars[i]["close"] / bars[i - 1]["close"] - 1
    except (IndexError, ZeroDivisionError, KeyError):
        return None


def summary(provider, as_of: dt.date, all_bars: dict | None, log=print) -> dict:
    """Yesterday and today in numbers: indices (futures before the open), rates, oil, bitcoin,
    best/worst sectors and stocks among the liquid universe, plus a few headlines."""
    from . import sectors

    try:
        px = provider.history_many(list(WATCH), 10) or {}
    except Exception as ex:
        log(f"market summary: {ex}")
        px = {}
    iso = as_of.isoformat()
    spx = px.get("^GSPC") or []
    live = bool(spx) and spx[-1]["date"] == iso   # today's session already has a bar
    yi, ti = (-2, -1) if live else (-1, None)

    def pair(sym):
        b = px.get(sym) or []
        if len(b) < 3:
            return None
        yd = len(b) + yi
        return {"name": WATCH[sym], "last": b[-1]["close"], "yday": _chg(b, yd),
                "today": _chg(b, len(b) - 1) if live else None,
                "yday_abs": b[yd]["close"] - b[yd - 1]["close"],
                "today_abs": (b[-1]["close"] - b[-2]["close"]) if live else None}

    idx = [p for p in (pair(s) for s in ("^GSPC", "^NDX", "^DJI")) if p]
    fut = [] if live else [p for p in (pair(s) for s in ("ES=F", "NQ=F", "YM=F")) if p]
    if fut:  # before the open the futures' last bar is today's move so far
        for f in fut:
            b = px.get({"S&P 500 fut": "ES=F", "Nasdaq fut": "NQ=F", "Dow fut": "YM=F"}[f["name"]])
            f["today"] = _chg(b, len(b) - 1)
    other = [p for p in (pair(s) for s in ("BZ=F", "BTC-USD", "^TNX")) if p]

    def day_moves(today: bool):
        """Stock and sector moves of one session: today's (if it has a bar) or the previous one."""
        movers, by_sec = [], {}
        for t, b in (all_bars or {}).items():
            if t in WATCH or t in ("SPY", "QQQ") or len(b) < 4:
                continue
            has_today = b[-1]["date"] == iso
            if today and not has_today:
                continue
            ch = _chg(b, len(b) - 1 if (today or not has_today) else len(b) - 2)
            if ch is None:
                continue
            movers.append((ch, t))
            g = sectors.group(t)
            if not g.startswith("solo"):
                by_sec.setdefault(g, []).append(ch)
        movers.sort()
        secs = sorted(((sum(v) / len(v), g) for g, v in by_sec.items() if len(v) >= 3))
        return movers, secs

    movers, secs = day_moves(True) if live else ([], [])
    y_movers, y_secs = day_moves(False)
    try:
        news = provider.news(["^GSPC", "SPY", "QQQ"], 4)
    except Exception as ex:
        log(f"news: {ex}")
        news = []
    return {"live": live, "indices": idx, "futures": fut, "other": other,
            "losers": [{"ticker": t, "chg": c} for c, t in movers[:3] if c < 0],
            "gainers": [{"ticker": t, "chg": c} for c, t in reversed(movers[-3:]) if c > 0],
            "best_sector": secs[-1][1] if secs else None, "best_sector_chg": secs[-1][0] if secs else None,
            "worst_sector": secs[0][1] if secs else None, "worst_sector_chg": secs[0][0] if secs else None,
            "news": news,
            "sectors_today": [{"sector": g, "chg": c} for c, g in secs],
            "sectors_yday": [{"sector": g, "chg": c} for c, g in y_secs],
            "losers_yday": [{"ticker": t, "chg": c} for c, t in y_movers[:3] if c < 0],
            "gainers_yday": [{"ticker": t, "chg": c} for c, t in reversed(y_movers[-3:]) if c > 0]}


def build(provider, as_of: dt.date, rows: list[dict], log=print, all_bars: dict | None = None) -> dict:
    vix = vix_chg = None
    try:
        vb = provider.history("^VIX", 10)
        if vb:
            vix = vb[-1]["close"]
            vix_chg = vb[-1]["close"] / vb[-2]["close"] - 1 if len(vb) > 1 else None
    except Exception as ex:
        log(f"VIX: {ex}")
    names = [r for r in rows if not r["market"]]
    above = [r["m"]["price"] > r["m"]["sma20"] for r in names if r["m"].get("sma20")]
    breadth = sum(above) / len(above) if above else None
    spy = next((r for r in rows if r["ticker"] == "SPY"), None)
    events, ev_err = [], None
    try:
        events = events_view(provider.econ_events(as_of, as_of + dt.timedelta(days=7)))
    except Exception as ex:
        ev_err = str(ex)[:120]
        log(f"economic calendar: {ex}")
    earn = sorted(({"ticker": r["ticker"], "date": r["m"]["earnings"], "days": r["m"]["earnings_days"]}
                   for r in names if r["m"].get("earnings") and r["m"].get("earnings_days") is not None
                   and 0 <= r["m"]["earnings_days"] <= 21), key=lambda x: x["date"])
    try:
        summ = summary(provider, as_of, all_bars, log)
    except Exception as ex:  # the summary must never break the brief
        log(f"market summary failed: {ex}")
        summ = None
    if summ:
        from . import story
        try:
            summ["story"] = story.build(provider, as_of, summ, vix, vix_chg, events, log)
        except Exception as ex:
            log(f"market story failed: {ex}")
    return {"regime": regime(vix, vix_chg, spy["m"]["trend"] if spy else None, breadth), "summary": summ,
            "events": events, "events_error": ev_err, "earnings": earn,
            "index": [{"ticker": r["ticker"], "price": r["m"]["price"], "ret5": r["m"]["ret5"],
                       "trend": r["m"]["trend"], "iv30": r["m"].get("iv30"),
                       "day": r["m"]["price"] / r["m"]["prev_close"] - 1 if r["m"].get("prev_close") else None}
                      for r in rows if r["market"]]}
