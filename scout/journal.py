"""Automatic tracking of every recommendation and its outcome."""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from .mathx import mid

D = dt.date


def _intrinsic(right, k, s):
    return max(0.0, s - k) if right == "call" else max(0.0, k - s)


def _mark(chain: dict, symbol: str):
    r = chain.get(symbol)
    return mid(r["bid"], r["ask"], r.get("last")) if r else None


def evaluate(store, as_of: D, bars: dict[str, dict], chains: dict[str, dict]) -> list[dict]:
    """Close open recs that hit target/stop/expiry. Returns the list of closed today."""
    closed = []
    iso = as_of.isoformat()
    for rec in store.open_recs():
        if rec["as_of"] >= iso:
            continue
        t, p = rec["ticker"], rec["plan"]
        bar = bars.get(t)
        if not bar:
            continue
        s = bar["close"]
        exit_px = reason = None
        if p["type"] in ("option", "spread"):
            ch = chains.get(t, {})
            dte = (D.fromisoformat(p["exp"]) - as_of).days
            if dte <= 0:
                val = _intrinsic(p["right"], p["strike"], s)
                if p["type"] == "spread":
                    val -= _intrinsic(p["right"], p["short_strike"], s)
                exit_px, reason = val, "экспирация"
            else:
                mk = _mark(ch, p["symbol"])
                if mk is not None and p["type"] == "spread":
                    sm = _mark(ch, p["short_symbol"])
                    mk = None if sm is None else mk - sm
                if mk is not None:
                    if mk >= p["target"]:
                        exit_px, reason = mk, "тейк"
                    elif mk <= p["stop"]:
                        exit_px, reason = mk, "стоп"
                    elif dte <= 1:
                        exit_px, reason = mk, "выход по времени"
            if exit_px is not None:
                r = (exit_px - p["entry"]) / p["entry"]
        else:
            bull = p["side"] == "bull"
            risk = abs(p["entry"] - p["stop"])
            held = (as_of - D.fromisoformat(rec["as_of"])).days * 5 // 7
            hit_stop = bar["low"] <= p["stop"] if bull else bar["high"] >= p["stop"]
            hit_tgt = bar["high"] >= p["target"] if bull else bar["low"] <= p["target"]
            if hit_stop:
                exit_px, reason = p["stop"], "стоп"
            elif hit_tgt:
                exit_px, reason = p["target"], "тейк"
            elif held >= p["max_hold_days"]:
                exit_px, reason = s, "выход по времени"
            if exit_px is not None:
                r = (exit_px - p["entry"]) / risk * (1 if bull else -1)
        if exit_px is not None:
            store.close_rec(rec["id"], iso, exit_px, r, reason)
            closed.append({**rec, "exit_price": exit_px, "result_r": r, "exit_reason": reason})
    return closed


def stats(recs: list[dict], since: str | None = None) -> dict:
    rs = [x for x in recs if since is None or x["exit_date"] >= since]

    def agg(xs):
        n = len(xs)
        if not n:
            return {"n": 0, "win": None, "avg_r": None, "sum_r": 0.0}
        wins = sum(1 for x in xs if x["result_r"] > 0)
        tot = sum(x["result_r"] for x in xs)
        return {"n": n, "win": wins / n, "avg_r": tot / n, "sum_r": tot}

    by_kind, by_driver = defaultdict(list), defaultdict(list)
    for x in rs:
        by_kind["акции" if x["kind"] == "stock" else "опционы"].append(x)
        by_driver[x["driver"]].append(x)
    return {"all": agg(rs), "kind": {k: agg(v) for k, v in by_kind.items()},
            "driver": {k: agg(v) for k, v in by_driver.items()}}
