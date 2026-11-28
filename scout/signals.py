"""Per-ticker signal computation. All numbers come from code, never from an LLM."""
from __future__ import annotations

import datetime as dt
import math

from .mathx import clip, mid

D = dt.date


def _sma(xs, n):
    return sum(xs[-n:]) / n if len(xs) >= n else None


def _rsi(closes, n=14):
    if len(closes) <= n:
        return None
    gains = losses = 0.0
    for a, b in zip(closes[-n - 1:-1], closes[-n:]):
        ch = b - a
        gains += max(ch, 0)
        losses += max(-ch, 0)
    if losses == 0:
        return 100.0
    rs = gains / losses
    return 100 - 100 / (1 + rs)


def price_stats(bars: list[dict]) -> dict:
    c = [b["close"] for b in bars]
    rets = [math.log(b / a) for a, b in zip(c[-21:-1], c[-20:])] if len(c) > 21 else []
    hv20 = (sum((r - sum(rets) / len(rets)) ** 2 for r in rets) / (len(rets) - 1)) ** 0.5 * math.sqrt(252) if len(rets) > 2 else None
    trs = []
    for p, b in zip(bars[-15:-1], bars[-14:]):
        trs.append(max(b["high"] - b["low"], abs(b["high"] - p["close"]), abs(b["low"] - p["close"])))
    if trs:  # one broken bar (e.g. a split the source adjusted late) must not blow up the stop
        med = sorted(trs)[len(trs) // 2]
        trs = [x for x in trs if x <= 4 * med] or trs
    return {
        "price": c[-1],
        "prev_close": c[-2] if len(c) > 1 else c[-1],
        "hv20": hv20,
        "atr14": sum(trs) / len(trs) if trs else None,
        "sma20": _sma(c, 20),
        "sma50": _sma(c, 50),
        "rsi14": _rsi(c),
        "ret5": c[-1] / c[-6] - 1 if len(c) > 6 else 0.0,
        "ret20": c[-1] / c[-21] - 1 if len(c) > 21 else None,
    }


def _atm(rows, s):
    strikes = sorted({r["strike"] for r in rows})
    if not strikes:
        return None, None, None
    k = min(strikes, key=lambda x: abs(x - s))
    call = next((r for r in rows if r["strike"] == k and r["type"] == "call"), None)
    put = next((r for r in rows if r["strike"] == k and r["type"] == "put"), None)
    return k, call, put


def _dte(exp: str, as_of: D) -> int:
    return (D.fromisoformat(exp) - as_of).days


def informed(chains: dict, exps: list[str], as_of: D, s: float, rows: list[dict], stock_volume: float) -> dict:
    """Option-market measures that research links to future stock returns:
    - skew: OTM put IV (strike ~0.95 of the price) minus ATM call IV, ~30-day expiry. Steeper -> weaker
      returns ahead (Xing, Zhang, Zhao 2010).
    - cp_iv: call minus put IV at the same strikes near the money, OI-weighted. Negative -> weaker returns
      (Cremers, Weinbaum 2010).
    - os_ratio: option contracts traded / shares traded today. High -> weaker returns (Johnson, So 2012).
    - otm_call_share / otm_put_share: out-of-the-money calls (puts) in today's option volume
      (more OTM calls -> stronger returns ahead)."""
    out = {"skew": None, "cp_iv": None, "os_ratio": None, "otm_call_share": None, "otm_put_share": None}
    if exps:
        e30 = min(exps, key=lambda e: abs(_dte(e, as_of) - 30))
        ch = [r for r in chains[e30] if (r.get("iv") or 0) > 0.01]
        puts = [r for r in ch if r["type"] == "put" and 0.80 <= r["strike"] / s <= 0.95]
        calls = [r for r in ch if r["type"] == "call" and 0.95 <= r["strike"] / s <= 1.05]
        if puts and calls:
            p = min(puts, key=lambda r: abs(r["strike"] / s - 0.95))
            c = min(calls, key=lambda r: abs(r["strike"] / s - 1))
            out["skew"] = p["iv"] - c["iv"]
        by_k = {}
        for r in ch:
            if 0.9 <= r["strike"] / s <= 1.1:
                by_k.setdefault(r["strike"], {})[r["type"]] = r
        pairs = [(v["call"]["iv"] - v["put"]["iv"], v["call"]["oi"] + v["put"]["oi"]) for v in by_k.values()
                 if "call" in v and "put" in v]
        w = sum(n for _, n in pairs)
        if pairs:
            out["cp_iv"] = sum(d * n for d, n in pairs) / w if w else sum(d for d, _ in pairs) / len(pairs)
    vol = sum(r["volume"] for r in rows)
    if stock_volume > 0:
        out["os_ratio"] = vol / stock_volume
    if vol > 0:
        out["otm_call_share"] = sum(r["volume"] for r in rows if r["type"] == "call" and r["strike"] > s * 1.02) / vol
        out["otm_put_share"] = sum(r["volume"] for r in rows if r["type"] == "put" and r["strike"] < s * 0.98) / vol
    return out


def compute(ticker: str, as_of: D, bars: list[dict], chains: dict[str, list[dict]],
            prev: dict | None, iv_hist: list[float], earnings: str | None, cfg: dict) -> dict:
    sc = cfg["signals"]
    oc = cfg["options"]
    m = {"ticker": ticker, **price_stats(bars)}
    s = m["price"]

    # ---- implied vol (30-day ATM) and IV rank
    exps = sorted(chains)
    m["iv30"] = None
    if exps:
        e30 = min(exps, key=lambda e: abs(_dte(e, as_of) - 30))
        _, c, p = _atm(chains[e30], s)
        ivs = [x["iv"] for x in (c, p) if x and x["iv"] > 0]
        m["iv30"] = sum(ivs) / len(ivs) if ivs else None
    m["iv_hist_n"] = len(iv_hist)
    if m["iv30"] and len(iv_hist) >= 20:
        lo, hi = min(iv_hist + [m["iv30"]]), max(iv_hist + [m["iv30"]])
        m["iv_rank"] = 100 * (m["iv30"] - lo) / (hi - lo) if hi > lo else 50.0
    else:
        m["iv_rank"] = None
    m["iv_hv"] = m["iv30"] / m["hv20"] if m["iv30"] and m["hv20"] else None

    # ---- expected move per expiry (ATM straddle)
    m["em"] = {}
    for e in exps:
        k, c, p = _atm(chains[e], s)
        if c and p:
            m["em"][e] = (mid(c["bid"], c["ask"], c["last"]) + mid(p["bid"], p["ask"], p["last"])) / s

    # ---- open interest structure
    rows = [r for e in exps if _dte(e, as_of) <= sc["scan_dte_max"] for r in chains[e]]
    coi = sum(r["oi"] for r in rows if r["type"] == "call")
    poi = sum(r["oi"] for r in rows if r["type"] == "put")
    cv = sum(r["volume"] for r in rows if r["type"] == "call")
    pv = sum(r["volume"] for r in rows if r["type"] == "put")
    m["pcr_oi"] = poi / coi if coi else None
    m["pcr_vol"] = pv / cv if cv else None
    calls_above = [r for r in rows if r["type"] == "call" and r["strike"] >= s]
    puts_below = [r for r in rows if r["type"] == "put" and r["strike"] <= s]
    m["call_wall"] = max(calls_above, key=lambda r: r["oi"])["strike"] if calls_above else None
    m["put_wall"] = max(puts_below, key=lambda r: r["oi"])["strike"] if puts_below else None
    if exps:
        near = chains[exps[0]]
        ks = sorted({r["strike"] for r in near})
        def pain(k):
            return sum(r["oi"] * max(0, (k - r["strike"]) if r["type"] == "call" else (r["strike"] - k)) for r in near)
        m["max_pain"] = min(ks, key=pain) if ks else None
        m["max_pain_exp"] = exps[0]

    def bias(c, p, floor):
        return (c - p) / (c + p) if c + p >= floor else 0.0

    # ---- unusual volume today (volume > OI)
    unusual = []
    for r in rows:
        if r["volume"] >= sc["unusual_min_volume"] and r["volume"] >= sc["unusual_vol_oi"] * max(r["oi"], 1):
            prem = r["volume"] * mid(r["bid"], r["ask"], r["last"]) * 100
            unusual.append({"symbol": r["symbol"], "type": r["type"], "strike": r["strike"], "exp": r["exp"],
                            "volume": r["volume"], "oi": r["oi"], "premium": prem})
    unusual.sort(key=lambda u: -u["premium"])
    uc = sum(u["premium"] for u in unusual if u["type"] == "call")
    up = sum(u["premium"] for u in unusual if u["type"] == "put")
    m["unusual"] = unusual[:5]
    m["unusual_premium"] = uc + up
    m["unusual_bias"] = bias(uc, up, 25_000)

    # ---- OI change vs previous snapshot (new positions, premium-weighted)
    m["has_prev"] = bool(prev)
    nc = npt = cc = cp = 0.0
    confirmed = []
    if prev:
        for r in rows:
            p = prev.get(r["symbol"])
            if not p:
                continue
            px = mid(r["bid"], r["ask"], r["last"])
            d_oi = r["oi"] - p["oi"]
            if d_oi > 0:
                if r["type"] == "call":
                    nc += d_oi * px * 100
                else:
                    npt += d_oi * px * 100
            # yesterday's unusual volume that stuck as new open interest
            if (p["volume"] >= sc["unusual_min_volume"] and p["volume"] >= sc["unusual_vol_oi"] * max(p["oi"], 1)
                    and d_oi >= 0.5 * p["volume"]):
                prem = p["volume"] * px * 100
                confirmed.append({"symbol": r["symbol"], "type": r["type"], "strike": r["strike"], "exp": r["exp"],
                                  "d_oi": d_oi, "premium": prem})
                if r["type"] == "call":
                    cc += prem
                else:
                    cp += prem
    m["new_call_prem"], m["new_put_prem"] = nc, npt
    m["flow_bias"] = bias(nc, npt, 50_000)
    confirmed.sort(key=lambda x: -x["premium"])
    m["confirmed"] = confirmed[:5]
    m["confirmed_bias"] = bias(cc, cp, 25_000)

    # ---- what informed option traders may be saying (observed only, not in the score yet)
    m.update(informed(chains, exps, as_of, s, rows, bars[-1].get("volume") or 0))

    # ---- trend
    t = 0.0
    if m["sma20"]:
        t += 0.5 * (1 if s > m["sma20"] else -1)
    if m["sma20"] and m["sma50"]:
        t += 0.3 * (1 if m["sma20"] > m["sma50"] else -1)
    t += 0.2 * clip(m["ret5"] / 0.05)
    m["trend"] = clip(t)

    # ---- earnings
    m["earnings"] = earnings
    m["earnings_days"] = (D.fromisoformat(earnings) - as_of).days if earnings else None
    horizon = max([oc["dte_max"]] + [md["dte_max"] for md in (oc.get("modes") or {}).values()])
    m["earnings_in_window"] = m["earnings_days"] is not None and 0 <= m["earnings_days"] <= horizon
    return m
