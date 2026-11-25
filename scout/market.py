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
        key, label, note = "stress", "Стресс", "Опционы дорогие: покупка недельных — переплата за страх. Спреды вместо одиночных опционов."
        label_en, note_en = "Stress", "Options are expensive: buying weeklies means overpaying for fear. Prefer spreads to single options."
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


def build(provider, as_of: dt.date, rows: list[dict], log=print) -> dict:
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
    return {"regime": regime(vix, vix_chg, spy["m"]["trend"] if spy else None, breadth),
            "events": events, "events_error": ev_err, "earnings": earn,
            "index": [{"ticker": r["ticker"], "price": r["m"]["price"], "ret5": r["m"]["ret5"],
                       "trend": r["m"]["trend"], "iv30": r["m"].get("iv30"),
                       "day": r["m"]["price"] / r["m"]["prev_close"] - 1 if r["m"].get("prev_close") else None}
                      for r in rows if r["market"]]}
