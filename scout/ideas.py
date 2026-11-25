"""Scoring and trade construction."""
from __future__ import annotations

import datetime as dt
import math

from .mathx import clip, mid, prob_above

D = dt.date
NAMES = {"trend": "тренд", "flow": "новый OI", "unusual": "необычный объём", "confirmed": "подтверждённый поток"}


def _usd(x: float) -> str:
    return f"${x / 1e6:.1f}M" if abs(x) >= 1e6 else f"${x / 1e3:.0f}K"


def score(m: dict, cfg: dict) -> dict:
    w = cfg["signals"]["weights"]
    comps = {"trend": m["trend"], "flow": m["flow_bias"], "unusual": m["unusual_bias"], "confirmed": m["confirmed_bias"]}
    d = sum(w[k] * v for k, v in comps.items())
    rsi = m.get("rsi14") or 50
    if d > 0 and rsi > 75:
        d -= 0.1
    if d < 0 and rsi < 25:
        d += 0.1
    side = "bull" if d >= 0 else "bear"
    sign = 1 if d >= 0 else -1
    contrib = {k: w[k] * v * sign for k, v in comps.items()}
    driver = max(contrib, key=contrib.get)
    conv = min(1.0, abs(d) / 0.8)
    rs = m.get("rs20")
    against_rs = rs is not None and ((sign > 0 and rs < -0.02) or (sign < 0 and rs > 0.02))
    if against_rs:  # a short on a stock stronger than the market is a bet on the market, not on the stock
        conv *= 0.5

    if m.get("iv_rank") is not None:
        cost = 1 - m["iv_rank"] / 100
    elif m.get("iv_hv"):
        cost = 1 - clip((m["iv_hv"] - 0.8) / 0.8, 0, 1)
    else:
        cost = 0.5

    stock = 100 * conv * (1 if m["trend"] * sign > 0 else 0.5)

    reasons = []
    if abs(m["trend"]) >= 0.3:
        reasons.append(("Тренд вверх" if m["trend"] > 0 else "Тренд вниз")
                       + f": цена {'выше' if m['price'] > (m['sma20'] or 0) else 'ниже'} SMA20, 5 дн. {m['ret5']:+.1%}")
    if rs is not None and abs(rs) >= 0.02:
        reasons.append(f"{'Сильнее' if rs > 0 else 'Слабее'} рынка: {rs * 100:+.1f}% к SPY за 20 дн."
                       + (" — против направления идеи, сила снижена вдвое" if against_rs else ""))
    if m["has_prev"] and (m["new_call_prem"] + m["new_put_prem"]) > 0:
        reasons.append(f"Новый OI: колы {_usd(m['new_call_prem'])} против путов {_usd(m['new_put_prem'])}")
    if m["unusual"]:
        u = m["unusual"][0]
        reasons.append(f"Необычный объём {_usd(m['unusual_premium'])}; крупнейший: "
                       f"{u['type']} {u['strike']:g} {u['exp'][5:]} ({u['volume']:,} при OI {u['oi']:,})")
    if m["confirmed"]:
        c = m["confirmed"][0]
        reasons.append(f"Вчерашний поток закрепился в OI: {c['type']} {c['strike']:g} {c['exp'][5:]} (+{c['d_oi']:,} OI)")
    if m.get("iv_rank") is not None:
        reasons.append(f"IV Rank {m['iv_rank']:.0f}: опционы {'дешёвые' if m['iv_rank'] < 30 else 'дорогие' if m['iv_rank'] > 70 else 'по средней цене'}")
    elif m.get("iv_hv"):
        reasons.append(f"IV/HV {m['iv_hv']:.2f}: опционы {'дешёвые' if m['iv_hv'] < 1 else 'дорогие' if m['iv_hv'] > 1.4 else 'по средней цене'} "
                       f"(IV Rank появится после {20 - m['iv_hist_n']} дн. истории)")
    if m["earnings_in_window"]:
        reasons.append(f"Отчёт через {m['earnings_days']} дн. ({m['earnings']}): после него IV падает (IV crush)")
    if m.get("split"):
        reasons.append(f"Сплит {m['split'][1]:g}:1 с {m['split'][0][8:]}.{m['split'][0][5:7]}: "
                       "история пересчитана, сигналы по потоку опционов в первые дни после сплита ненадёжны")
    if rsi > 75 or rsi < 25:
        reasons.append(f"RSI {rsi:.0f}: перегрет{'' if rsi > 75 else ' вниз'}, риск отката")

    return {"direction": d, "side": side, "conviction": conv, "cost": cost, "driver": driver,
            "driver_name": NAMES[driver], "stock_score": stock, "components": comps, "reasons": reasons}


def _dte(exp, as_of):
    return (D.fromisoformat(exp) - as_of).days


def build_option(m: dict, sc: dict, chains: dict, as_of: D, cfg: dict) -> tuple[dict | None, str]:
    oc, acc = cfg["options"], cfg["account"]
    s, right = m["price"], ("call" if sc["side"] == "bull" else "put")
    sgn = 1 if right == "call" else -1
    budget = acc["size_usd"] * acc["risk_per_trade_pct"] / 100
    best, why = None, "нет экспираций в окне"
    for e in sorted(chains):
        dte = _dte(e, as_of)
        if not (oc["dte_min"] <= dte <= oc["dte_max"]):
            continue
        t = dte / 365
        em = m["em"].get(e) or ((m["iv30"] or 0.5) * math.sqrt(t))
        cands = [r for r in chains[e] if r["type"] == right]
        why = "нет ликвидных контрактов дешевле лимита"
        for r in cands:
            ask, bid = r["ask"], r["bid"]
            if bid <= 0 or ask <= 0 or ask * 100 > oc["max_premium_usd"] or ask * 100 > budget:
                continue
            if (ask - bid) / mid(bid, ask) > oc["max_spread_pct"] or r["oi"] < oc["min_open_interest"]:
                continue
            if not (oc["delta_min"] <= abs(r["delta"]) <= oc["delta_max"]):
                continue
            be = r["strike"] + sgn * ask
            req = sgn * (be / s - 1)
            ratio = req / em if em > 0 else 9
            if ratio > oc["max_be_to_em"]:
                why = "безубыток дальше ожидаемого движения"
                continue
            pa = prob_above(s, be, t, r["iv"] or m["iv30"] or 0.5)
            plan = {"type": "option", "symbol": r["symbol"], "right": right, "strike": r["strike"], "exp": e,
                    "dte": dte, "entry": ask, "cost_usd": ask * 100, "contracts": 1,
                    "breakeven": be, "req_move_pct": req, "em_pct": em, "be_to_em": ratio,
                    "pop": pa if right == "call" else 1 - pa, "delta": r["delta"], "iv": r["iv"],
                    "target": round(ask * (1 + oc["target_pct"] / 100), 2),
                    "stop": round(ask * (1 - oc["stop_pct"] / 100), 2), "underlying": s, "exit_by": e}
            key = (ratio, abs(abs(r["delta"]) - 0.35))
            if best is None or key < best[0]:
                best = (key, plan)
    if best:
        return best[1], ""
    spread = build_spread(m, sc, chains, as_of, cfg)
    if spread:
        return spread, ""
    return None, why


def build_spread(m, sc, chains, as_of, cfg):
    """Debit vertical: when single legs are too expensive (high IV or earnings)."""
    oc, acc = cfg["options"], cfg["account"]
    s, right = m["price"], ("call" if sc["side"] == "bull" else "put")
    sgn = 1 if right == "call" else -1
    budget = min(oc["max_premium_usd"], acc["size_usd"] * acc["risk_per_trade_pct"] / 100)
    best = None
    for e in sorted(chains):
        dte = _dte(e, as_of)
        if not (oc["dte_min"] <= dte <= oc["dte_max"]):
            continue
        em = m["em"].get(e) or 0.05
        legs = sorted([r for r in chains[e] if r["type"] == right and r["bid"] > 0], key=lambda r: r["strike"])
        if not legs:
            continue
        long = min(legs, key=lambda r: abs(r["strike"] - s))
        target_k = s * (1 + sgn * em)
        shorts = [r for r in legs if sgn * (r["strike"] - long["strike"]) > 0]
        if not shorts:
            continue
        short = min(shorts, key=lambda r: abs(r["strike"] - target_k))
        debit = round(long["ask"] - short["bid"], 2)
        width = abs(short["strike"] - long["strike"])
        if debit <= 0 or debit * 100 > budget or debit >= width:
            continue
        be = long["strike"] + sgn * debit
        req = sgn * (be / s - 1)
        if req / em > oc["max_be_to_em"]:
            continue
        t = dte / 365
        pa = prob_above(s, be, t, long["iv"] or 0.5)
        plan = {"type": "spread", "symbol": long["symbol"], "short_symbol": short["symbol"], "right": right,
                "strike": long["strike"], "short_strike": short["strike"], "exp": e, "dte": dte,
                "entry": debit, "cost_usd": debit * 100, "contracts": 1,
                "max_profit_usd": (width - debit) * 100, "breakeven": be, "req_move_pct": req, "em_pct": em,
                "be_to_em": req / em, "pop": pa if right == "call" else 1 - pa, "delta": long["delta"],
                "iv": long["iv"], "target": round(debit + 0.6 * (width - debit), 2),
                "stop": round(debit * 0.5, 2), "underlying": s, "exit_by": e}
        rr = (width - debit) / debit
        if best is None or rr > best[0]:
            best = (rr, plan)
    return best[1] if best else None


def option_score(sc: dict, plan: dict) -> float:
    edge = clip(1.5 - plan["be_to_em"], 0, 1)  # be at 0.5 EM or closer -> full edge
    return 100 * (0.6 * sc["conviction"] + 0.25 * sc["cost"] + 0.15 * edge)


def add_trading_days(d: D, n: int) -> D:
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def build_stock(m: dict, sc: dict, cfg: dict, as_of: D) -> dict | None:
    """One-share idea. Target = expected move over the holding period; stop = the larger of 1 ATR
    (daily noise) and target / reward_risk.
    Volatility = max(IV30, HV20): when a stock actually moves more than options price in, the target
    and the stop both widen with it instead of the idea being dropped. If daily noise still forces
    a stop wider than target / min_reward_risk, the idea stays but is marked high-volatility."""
    st = cfg["stocks"]
    atr, s = m.get("atr14"), m["price"]
    vols = [v for v in (m.get("iv30"), m.get("hv20")) if v]
    if not atr or not vols:
        return None
    vol = max(vols)
    sgn = 1 if sc["side"] == "bull" else -1
    hold = st["max_hold_days"]
    move = s * vol * math.sqrt(hold / 252) * st.get("target_sigma", 1.0)
    stop_d = max(st.get("stop_atr_min", 1.0) * atr, move / st["reward_risk"])
    rr = move / stop_d
    if rr < 1.0:  # the stop would be further than the target: not a trade
        return None
    high_vol = vol >= st.get("high_vol", 0.6) or rr < st.get("min_reward_risk", 1.5)
    return {"type": "stock", "side": sc["side"], "entry": s, "stop": s - sgn * stop_d, "target": s + sgn * move,
            "target_pct": move / s, "stop_pct": stop_d / s, "rr": rr, "vol": vol, "high_vol": high_vol,
            "max_hold_days": hold, "exit_by": add_trading_days(as_of, hold).isoformat()}


def tags(m: dict, sc: dict) -> str:
    """2-4 words: why this idea, for the Telegram line and card header."""
    bull = sc["side"] == "bull"
    drv = {"trend": "тренд вверх" if bull else "тренд вниз",
           "flow": "приток денег в колы" if bull else "приток денег в путы",
           "unusual": "всплеск объёма в колах" if bull else "всплеск объёма в путах",
           "confirmed": "крупный поток закрепился в OI"}[sc["driver"]]
    out = [drv]
    rs = m.get("rs20")
    if rs is not None and abs(rs) >= 0.03 and (rs > 0) == bull:
        out.append("сильнее рынка" if bull else "слабее рынка")
    r5 = m.get("ret5") or 0
    if abs(r5) >= 0.03 and (r5 > 0) == bull:
        out.append(f"{m['ret5'] * 100:+.1f}% за 5 дн.".replace("-", "−"))
    rsi = m.get("rsi14") or 50
    if rsi < 25:
        out.append("перепродан")
    elif rsi > 75:
        out.append("перекуплен")
    if m.get("split"):
        out.append("сплит, данные неполные")
    if m.get("earnings_in_window"):
        out.append(f"отчёт через {m['earnings_days']} дн.")
    return ", ".join(out[:3])
