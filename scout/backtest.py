"""Historical test of the price-based signals: does the trend still work in a panic, and does the snap-back?

Uses the same formulas as the daily engine (signals.compute / ideas.exhaustion) on daily bars,
so a rule that wins here is the rule that runs in the brief.

What it can and cannot test
- Price signals (trend, strength vs SPY, 5-day move, RSI, volume spike, sector move): yes, years back.
- Option flow (new OI, unusual volume, skew): no history at Yahoo, the daily journal tests those.
- Option trades: approximated. A one-week at-the-money option is priced with Black-Scholes at
  max(HV20, HV60) x 1.15 (implied vol usually sits above realized) plus 5% for the bid-ask spread,
  and held to expiry. Good for comparing signals with each other, not a promise of real P&L.
- Universe: today's liquid large caps, so the sample leans towards winners (survivorship). Results are
  shown both raw and relative to SPY; compare signals against each other, not against zero.

Signals are taken at the close of day t and trades enter at that close (the brief runs before the close).
"""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from . import sectors

HOLD = 5             # trading days: weekly options
OPT_DAYS = 7         # calendar days to expiry for the option proxy
IV_MULT = 1.15       # implied over realized volatility
SPREAD = 0.05        # paid on entry, as a share of the premium
IS_END = "2023-06-30"  # in-sample until this date, out-of-sample after
_erf = np.frompyfunc(math.erf, 1, 1)


def _ncdf(x):
    return 0.5 * (1.0 + _erf(np.asarray(x, dtype=float) / math.sqrt(2.0)).astype(float))


def atm_premium(iv, t=OPT_DAYS / 365, r=0.04):
    """At-the-money call price as a share of the stock price."""
    iv = np.maximum(np.asarray(iv, dtype=float), 0.05)
    d1 = (r + 0.5 * iv ** 2) * t / (iv * math.sqrt(t))
    d2 = d1 - iv * math.sqrt(t)
    return _ncdf(d1) - math.exp(-r * t) * _ncdf(d2)


def frames(bars: dict[str, list[dict]]) -> dict[str, pd.DataFrame]:
    def col(k):
        return pd.DataFrame({t: pd.Series({b["date"]: b[k] for b in bs}) for t, bs in bars.items() if bs}).sort_index()
    return {k: col(k) for k in ("close", "volume")}


def panel(bars: dict[str, list[dict]], hold: int = HOLD) -> pd.DataFrame:
    """One row per (date, ticker) with every signal and the forward result."""
    f = frames(bars)
    c_all, v_all = f["close"], f["volume"]
    spx = c_all.get("^GSPC")
    vix = c_all.get("^VIX")
    spy = c_all["SPY"]
    names = [t for t in c_all.columns if not t.startswith("^") and t not in ("SPY", "QQQ")]
    c, v = c_all[names], v_all[names]
    c = c.where(c > 0)

    sma20, sma50 = c.rolling(20).mean(), c.rolling(50).mean()
    ret5, ret20 = c / c.shift(5) - 1, c / c.shift(20) - 1
    trend = (0.5 * np.sign(c - sma20) + 0.3 * np.sign(sma20 - sma50) + 0.2 * (ret5 / 0.05).clip(-1, 1)).clip(-1, 1)
    d = c.diff()
    g, l = d.clip(lower=0).rolling(14).sum(), (-d).clip(lower=0).rolling(14).sum()
    rsi = 100 - 100 / (1 + g / l.replace(0, np.nan))
    rsi = rsi.where(l > 0, 100.0)
    lr = np.log(c / c.shift(1))
    hv20, hv60 = lr.rolling(20).std() * math.sqrt(252), lr.rolling(60).std() * math.sqrt(252)
    em5 = hv20 * math.sqrt(5 / 252)                  # one expected weekly move
    rs20 = ret20.sub(spy / spy.shift(20) - 1, axis=0)
    vr = v / v.rolling(50).mean().shift(1)
    news = vr.rolling(5).max() >= 2.0                # a volume spike in the last 5 days: the move had its own story

    grp = {t: sectors.group(t) for t in names}
    sec5 = pd.DataFrame(index=c.index)
    for gname in set(grp.values()):
        members = [t for t in names if grp[t] == gname]
        sec5[gname] = ret5[members].median(axis=1) if len(members) >= 3 and not gname.startswith("solo") else np.nan
    spy5 = spy / spy.shift(5) - 1
    sec_of = pd.DataFrame({t: (sec5[grp[t]] if grp[t] in sec5 else spy5) for t in names}).fillna(
        pd.DataFrame({t: spy5 for t in names}))
    idio5 = ret5 - sec_of

    fwd = c.shift(-hold) / c - 1
    spy_fwd = spy.shift(-hold) / spy - 1
    iv = np.maximum(hv20, hv60) * IV_MULT
    prem = pd.DataFrame(atm_premium(iv.values), index=iv.index, columns=iv.columns) * (1 + SPREAD)

    dd = spx / spx.rolling(63).max() - 1 if spx is not None else pd.Series(np.nan, index=c.index)
    cols = {"trend": trend, "rs20": rs20, "ret5": ret5, "rsi": rsi, "em5": em5, "news": news, "idio5": idio5,
            "fwd": fwd, "prem": prem, "hv20": hv20}
    p = pd.concat({k: x.stack(future_stack=True) for k, x in cols.items()}, axis=1)
    p.index.names = ["date", "ticker"]
    p = p.reset_index().dropna(subset=["trend", "rs20", "rsi", "em5", "fwd", "prem"])
    p["spy_fwd"] = p["date"].map(spy_fwd)
    p["vix"] = p["date"].map(vix) if vix is not None else np.nan
    p["dd"] = p["date"].map(dd)
    p["sector"] = p["ticker"].map(grp)
    p["news"] = p["news"].astype(bool)
    return p


def regimes(p: pd.DataFrame) -> pd.DataFrame:
    p["vix_b"] = pd.cut(p["vix"], [0, 17, 22, 28, 200], labels=["VIX<17", "17-22", "22-28", "VIX>=28"], right=False)
    p["dd_b"] = pd.cut(p["dd"], [-1, -0.10, -0.05, 1], labels=["SPX -10%+", "SPX -5..-10%", "SPX near high"], right=False)
    p["panic"] = (p["vix"] >= 25) | (p["dd"] <= -0.07)
    p["period"] = np.where(p["date"] <= IS_END, "in-sample", "out-of-sample")
    return p


def events(p: pd.DataFrame) -> pd.DataFrame:
    """Signal events with their direction. The same ticker-day can be in more than one."""
    ex_bear = (p["rsi"] < 30) | (p["ret5"] < -2 * p["em5"])   # ideas.exhaustion, bear side
    ex_bull = (p["rsi"] > 70) | (p["ret5"] > 2 * p["em5"])
    own_down, own_up = p["idio5"] <= -p["em5"], p["idio5"] >= p["em5"]
    rows = []
    for name, mask, side in [
        ("baseline: any stock, long", pd.Series(True, index=p.index), 1),
        ("trend long", (p["trend"] >= 0.6) & (p["rs20"] > 0.02) & ~ex_bull, 1),
        ("trend short", (p["trend"] <= -0.6) & (p["rs20"] < -0.02) & ~ex_bear, -1),
        ("trend short, already stretched", (p["trend"] <= -0.6) & ex_bear, -1),
        ("trend long, already stretched", (p["trend"] >= 0.6) & ex_bull, 1),
        ("rebound long: fell with its sector, no volume spike", ex_bear & ~own_down & ~p["news"], 1),
        ("rebound long: own drop, no volume spike", ex_bear & own_down & ~p["news"], 1),
        ("rebound long: drop on a volume spike (news)", ex_bear & p["news"], 1),
        ("fade short: spike, no volume spike", ex_bull & ~p["news"], -1),
        ("fade short: spike on a volume spike (news)", ex_bull & p["news"], -1),
    ]:
        e = p[mask].copy()
        e["signal"], e["side"] = name, side
        rows.append(e)
    e = pd.concat(rows, ignore_index=True)
    e["ret"] = e["side"] * e["fwd"]
    e["excess"] = e["side"] * (e["fwd"] - e["spy_fwd"])
    e["opt"] = np.maximum(0.0, e["ret"]) / e["prem"] - 1   # one-week ATM call (long) or put (short), held to expiry
    return e


def stats(e: pd.DataFrame, by: list[str], hold: int = HOLD) -> pd.DataFrame:
    """Day-clustered stats: every day weighs the same, however many tickers fired that day.
    t is divided by sqrt(hold) because holding windows overlap."""
    out = []
    for key, sub in e.groupby(by, observed=True):
        key = key if isinstance(key, tuple) else (key,)
        d = sub.groupby("date").agg(ret=("ret", "mean"), excess=("excess", "mean"), opt=("opt", "mean"))
        nd = len(d)
        sd = d["ret"].std() if nd > 2 else np.nan
        out.append({**dict(zip(by, key)), "days": nd, "events": len(sub),
                    "avg %": 100 * d["ret"].mean(), "vs SPY %": 100 * d["excess"].mean(),
                    "hit %": 100 * (sub["ret"] > 0).mean(),
                    "option avg %": 100 * d["opt"].mean(), "option median %": 100 * sub["opt"].median(),
                    "option x2 %": 100 * (sub["opt"] >= 1).mean(),
                    "t": d["ret"].mean() / (sd / math.sqrt(nd)) / math.sqrt(hold) if sd and sd > 0 else np.nan})
    return pd.DataFrame(out)


# ---------------------------------------------------------------- strategies: a trade history per rule set

def _pick(day: pd.DataFrame, n: int, busy: set, rank) -> pd.DataFrame:
    day = day[~day["ticker"].isin(busy)].copy()
    if day.empty:
        return day
    day["rank"] = rank(day)
    day = day.sort_values(["rank", "ticker"], ascending=[False, True])
    return day.groupby("sector", sort=False).head(1).head(n)   # one idea per sector per day


def simulate(e: pd.DataFrame, rule: str, n: int = 3, hold: int = HOLD) -> pd.DataFrame:
    """Each day take up to n ideas, at most one per sector, no ticker twice while a trade is open."""
    trend_sigs = {"trend long", "trend short"}
    rebound = {"rebound long: fell with its sector, no volume spike", "rebound long: own drop, no volume spike"}
    if rule == "now":            # what the brief does today: trend ideas, stretched ones demoted
        pool = e[e["signal"].isin(trend_sigs)]
    elif rule == "regime":       # trend when calm; in a panic no trend shorts, rebounds instead
        calm = e[e["signal"].isin(trend_sigs) & ~e["panic"]]
        panic = e[e["panic"] & (e["signal"].isin(rebound) | (e["signal"] == "trend long"))]
        pool = pd.concat([calm, panic])
    elif rule == "rebound only":
        pool = e[e["signal"].isin(rebound)]
    else:
        raise ValueError(rule)

    def rank(d):
        tr = d["trend"].abs() + 2 * d["rs20"].abs()
        reb = -d["ret5"] / d["em5"]
        return np.where(d["signal"].isin(rebound), reb, tr)

    dates = sorted(pool["date"].unique())
    all_dates = sorted(e["date"].unique())
    pos = {d: i for i, d in enumerate(all_dates)}
    open_until: dict[str, int] = {}
    trades = []
    for d in dates:
        i = pos[d]
        busy = {t for t, j in open_until.items() if j > i}
        pick = _pick(pool[pool["date"] == d], n, busy, rank)
        for _, r in pick.iterrows():
            open_until[r["ticker"]] = i + hold
            trades.append(r)
    t = pd.DataFrame(trades)
    if not t.empty:
        t["rule"] = rule
        t["year"] = t["date"].str[:4]
    return t


def trade_stats(t: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    g = t.groupby(by, observed=True)
    return pd.DataFrame({
        "trades": g.size(), "hit %": 100 * g["ret"].apply(lambda x: (x > 0).mean()),
        "stock avg %": 100 * g["ret"].mean(), "vs SPY %": 100 * g["excess"].mean(),
        "option avg %": 100 * g["opt"].mean(), "option median %": 100 * g["opt"].median(),
        "option x2 %": 100 * g["opt"].apply(lambda x: (x >= 1).mean()),
        "option P&L per $100": g["opt"].sum() * 100,
    }).reset_index()


def _md(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_нет данных_\n"
    df = df.copy()
    for k in df.columns:
        if df[k].dtype.kind == "f":
            df[k] = df[k].map(lambda x: "" if pd.isna(x) else f"{x:,.1f}" if k != "t" else f"{x:.2f}")
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "".join("| " + " | ".join(map(str, r)) + " |\n" for r in df.itertuples(index=False))


def run(bars: dict[str, list[dict]], out: Path, log=print) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    p = regimes(panel(bars))
    e = events(p)
    log(f"backtest: {p['ticker'].nunique()} tickers, {p['date'].nunique()} days "
        f"({p['date'].min()}..{p['date'].max()}), {len(e)} signal events")
    sections = {
        "Сигналы целиком": stats(e, ["signal"]),
        "Сигналы по периодам (до/после " + IS_END + ")": stats(e, ["signal", "period"]),
        "Сигналы по VIX": stats(e, ["signal", "vix_b"]),
        "Сигналы по просадке S&P 500 от 3-мес. максимума": stats(e, ["signal", "dd_b"]),
        "Сигналы: паника (VIX>=25 или S&P -7% от максимума) против спокойного рынка": stats(e, ["signal", "panic"]),
    }
    trades = pd.concat([simulate(e, r) for r in ("now", "regime", "rebound only")], ignore_index=True)
    trades["panic"] = trades["panic"].astype(bool)
    strat = {
        "Стратегии целиком": trade_stats(trades, ["rule"]),
        "Стратегии по периодам": trade_stats(trades, ["rule", "period"]),
        "Стратегии по годам": trade_stats(trades, ["rule", "year"]),
        "Стратегии: паника против спокойного рынка": trade_stats(trades, ["rule", "panic"]),
    }
    md = [f"# Бэктест сигналов · {dt.date.today()}\n",
          f"{p['ticker'].nunique()} тикеров, {p['date'].min()} — {p['date'].max()}, удержание {HOLD} торговых дней. "
          f"Опцион: недельный ATM по Блэку–Шоулзу (IV = max(HV20, HV60)×{IV_MULT}, +{SPREAD:.0%} на спред), до экспирации. "
          "Статистика по дням: каждый день весит одинаково. t скорректирован на перекрытие окон (÷√5); |t| > 2 — заметно.\n"]
    for k, v in {**sections, **strat}.items():
        md.append(f"\n## {k}\n\n" + _md(v))
    (out / "summary.md").write_text("".join(md), encoding="utf-8")
    keep = ["rule", "date", "ticker", "sector", "signal", "side", "trend", "rs20", "ret5", "rsi", "news", "vix", "dd",
            "panic", "fwd", "spy_fwd", "ret", "excess", "prem", "opt"]
    trades[keep].to_csv(out / "trades.csv", index=False, float_format="%.5f")
    summary = {k: v.to_dict(orient="records") for k, v in {**sections, **strat}.items()}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, default=str, indent=1), encoding="utf-8")
    return summary
