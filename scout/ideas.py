"""Scoring and trade construction."""
from __future__ import annotations

import datetime as dt
import math

from .mathx import clip, mid, prob_above

D = dt.date
NAMES = {"trend": "тренд", "flow": "новый OI", "unusual": "необычный объём", "confirmed": "подтверждённый поток"}


def _usd(x: float) -> str:
    return f"${x / 1e6:.1f}M" if abs(x) >= 1e6 else f"${x / 1e3:.0f}K"


def exhaustion(m: dict, sign: int, cfg: dict) -> dict | None:
    """Is the idea chasing a move that already ran too far? Shorts after a crash, longs after a spike.

    Too far = RSI beyond the threshold, or the 5-day move bigger than `weeks` expected weekly moves
    (expected weekly move from the higher of IV30 and HV20)."""
    ex = cfg.get("signals", {}).get("exhaustion", {})
    rsi = m.get("rsi14") or 50
    r5 = m.get("ret5") or 0
    vols = [v for v in (m.get("iv30"), m.get("hv20")) if v]
    em_w = max(vols) * math.sqrt(5 / 252) if vols else None
    k = ex.get("weeks", 2.0)
    lo, hi = ex.get("rsi_low", 30), ex.get("rsi_high", 70)
    if sign < 0 and (rsi < lo or (em_w and r5 < -k * em_w)):
        return {"rsi": rsi, "ret5": r5, "em_w": em_w}
    if sign > 0 and (rsi > hi or (em_w and r5 > k * em_w)):
        return {"rsi": rsi, "ret5": r5, "em_w": em_w}
    return None


def score(m: dict, cfg: dict) -> dict:
    w = cfg["signals"]["weights"]
    comps = {"trend": m["trend"], "flow": m["flow_bias"], "unusual": m["unusual_bias"], "confirmed": m["confirmed_bias"]}
    d = sum(w[k] * v for k, v in comps.items())
    rsi = m.get("rsi14") or 50
    side = "bull" if d >= 0 else "bear"
    sign = 1 if d >= 0 else -1
    contrib = {k: w[k] * v * sign for k, v in comps.items()}
    driver = max(contrib, key=contrib.get)
    conv = min(1.0, abs(d) / 0.8)
    rs = m.get("rs20")
    against_rs = rs is not None and ((sign > 0 and rs < -0.02) or (sign < 0 and rs > 0.02))
    if against_rs:  # a short on a stock stronger than the market is a bet on the market, not on the stock
        conv *= 0.5
    ext = exhaustion(m, sign, cfg)
    if ext:  # the move already ran too far in the idea's direction: snap-back risk
        conv *= 0.5

    if m.get("iv_rank") is not None:
        cost = 1 - m["iv_rank"] / 100
    elif m.get("iv_hv"):
        cost = 1 - clip((m["iv_hv"] - 0.8) / 0.8, 0, 1)
    else:
        cost = 0.5

    stock = 100 * conv * (1 if m["trend"] * sign > 0 else 0.5)

    reasons, reasons_en = [], []

    def R(ru, en):
        reasons.append(ru)
        reasons_en.append(en)

    if abs(m["trend"]) >= 0.3:
        up, above = m["trend"] > 0, m["price"] > (m["sma20"] or 0)
        R(("Тренд вверх" if up else "Тренд вниз") + f": цена {'выше' if above else 'ниже'} SMA20, 5 дн. {m['ret5']:+.1%}",
          ("Uptrend" if up else "Downtrend") + f": price {'above' if above else 'below'} SMA20, 5d {m['ret5']:+.1%}")
    if rs is not None and abs(rs) >= 0.02:
        R(f"{'Сильнее' if rs > 0 else 'Слабее'} рынка: {rs * 100:+.1f}% к SPY за 20 дн."
          + (" — против направления идеи, сила снижена вдвое" if against_rs else ""),
          f"{'Stronger' if rs > 0 else 'Weaker'} than the market: {rs * 100:+.1f}% vs SPY over 20d"
          + (" — against the idea's direction, strength halved" if against_rs else ""))
    if m["has_prev"] and (m["new_call_prem"] + m["new_put_prem"]) > 0:
        R(f"Новый OI: колы {_usd(m['new_call_prem'])} против путов {_usd(m['new_put_prem'])}",
          f"New OI: calls {_usd(m['new_call_prem'])} vs puts {_usd(m['new_put_prem'])}")
    if m["unusual"]:
        u = m["unusual"][0]
        R(f"Необычный объём {_usd(m['unusual_premium'])}; крупнейший: {u['type']} {u['strike']:g} {u['exp'][5:]} ({u['volume']:,} при OI {u['oi']:,})",
          f"Unusual volume {_usd(m['unusual_premium'])}; largest: {u['type']} {u['strike']:g} {u['exp'][5:]} ({u['volume']:,} vs OI {u['oi']:,})")
    if m["confirmed"]:
        c = m["confirmed"][0]
        R(f"Вчерашний поток закрепился в OI: {c['type']} {c['strike']:g} {c['exp'][5:]} (+{c['d_oi']:,} OI)",
          f"Yesterday's flow stuck as open interest: {c['type']} {c['strike']:g} {c['exp'][5:]} (+{c['d_oi']:,} OI)")
    if m.get("iv_rank") is not None:
        k = m["iv_rank"]
        R(f"IV Rank {k:.0f}: опционы {'дешёвые' if k < 30 else 'дорогие' if k > 70 else 'по средней цене'}",
          f"IV Rank {k:.0f}: options are {'cheap' if k < 30 else 'expensive' if k > 70 else 'fairly priced'}")
    elif m.get("iv_hv"):
        k = m["iv_hv"]
        R(f"IV/HV {k:.2f}: опционы {'дешёвые' if k < 1 else 'дорогие' if k > 1.4 else 'по средней цене'} (IV Rank появится после {20 - m['iv_hist_n']} дн. истории)",
          f"IV/HV {k:.2f}: options are {'cheap' if k < 1 else 'expensive' if k > 1.4 else 'fairly priced'} (IV Rank after {20 - m['iv_hist_n']} more days of history)")
    if m["earnings_in_window"]:
        R(f"Отчёт через {m['earnings_days']} дн. ({m['earnings']}): после него IV падает (IV crush)",
          f"Earnings in {m['earnings_days']}d ({m['earnings']}): IV usually drops afterwards (IV crush)")
    if m.get("split"):
        sd = f"{m['split'][0][8:]}.{m['split'][0][5:7]}"
        R(f"Сплит {m['split'][1]:g}:1 с {sd}: история пересчитана, сигналы по потоку опционов в первые дни после сплита ненадёжны",
          f"{m['split'][1]:g}:1 split on {sd}: history was restated, option-flow signals are unreliable for the first days")
    if ext:
        mv = f"{ext['ret5'] * 100:+.1f}%".replace("-", "−")
        emw = f" при ожидаемом недельном ±{ext['em_w'] * 100:.1f}%" if ext["em_w"] else ""
        emw_en = f" vs an expected weekly ±{ext['em_w'] * 100:.1f}%" if ext["em_w"] else ""
        R(f"Риск отскока: за 5 дн. {mv}{emw}, RSI {ext['rsi']:.0f} — движение уже ушло далеко, сила снижена вдвое",
          f"Snap-back risk: {mv} in 5d{emw_en}, RSI {ext['rsi']:.0f} — the move already ran far, strength halved")
    elif rsi > 75 or rsi < 25:
        R(f"RSI {rsi:.0f}: перегрет{'' if rsi > 75 else ' вниз'}, риск отката",
          f"RSI {rsi:.0f}: {'overbought' if rsi > 75 else 'oversold'}, pullback risk")

    return {"direction": d, "side": side, "conviction": conv, "cost": cost, "driver": driver,
            "driver_name": NAMES[driver], "stock_score": stock, "components": comps, "reasons": reasons,
            "exhausted": bool(ext),
            "reasons_en": reasons_en}


def _dte(exp, as_of):
    return (D.fromisoformat(exp) - as_of).days


REJECT_RU = {"quote": "нет котировок", "price": "дороже лимита", "spread": "широкий спред", "oi": "мало OI",
             "delta": "дельта вне диапазона", "be": "безубыток дальше ожидаемого движения", "dte": "нет экспираций в окне"}


def _liquid(r, oc) -> bool:
    return (r["bid"] > 0 and r["ask"] > 0 and (r["ask"] - r["bid"]) / mid(r["bid"], r["ask"]) <= oc["max_spread_pct"]
            and r["oi"] >= oc["min_open_interest"])


def build_option(m: dict, sc: dict, chains: dict, as_of: D, cfg: dict) -> tuple[dict | None, str]:
    """Best single contract within the price cap; otherwise the best debit spread that fits it.
    Returns (plan, why_not) where why_not names the filter that removed the most contracts."""
    oc = cfg["options"]
    cap = oc["max_premium_usd"]
    s, right = m["price"], ("call" if sc["side"] == "bull" else "put")
    sgn = 1 if right == "call" else -1
    best, rej = None, {}

    def no(k):
        rej[k] = rej.get(k, 0) + 1

    for e in sorted(chains):
        dte = _dte(e, as_of)
        if not (oc["dte_min"] <= dte <= oc["dte_max"]):
            continue
        t = dte / 365
        em = m["em"].get(e) or ((m["iv30"] or 0.5) * math.sqrt(t))
        for r in (x for x in chains[e] if x["type"] == right):
            ask, bid = r["ask"], r["bid"]
            if bid <= 0 or ask <= 0:
                no("quote"); continue
            if ask * 100 > cap:
                no("price"); continue
            if (ask - bid) / mid(bid, ask) > oc["max_spread_pct"]:
                no("spread"); continue
            if r["oi"] < oc["min_open_interest"]:
                no("oi"); continue
            if not (oc["delta_min"] <= abs(r["delta"]) <= oc["delta_max"]):
                no("delta"); continue
            be = r["strike"] + sgn * ask
            req = sgn * (be / s - 1)
            ratio = req / em if em > 0 else 9
            if ratio > oc["max_be_to_em"]:
                no("be"); continue
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
    if not rej:
        return None, REJECT_RU["dte"]
    top = max(rej, key=rej.get)
    return None, REJECT_RU[top] + " (" + ", ".join(f"{REJECT_RU[k]}: {v}" for k, v in sorted(rej.items(), key=lambda kv: -kv[1])) + ")"


def build_spread(m, sc, chains, as_of, cfg):
    """Debit vertical that fits the price cap: long leg at the money, short leg as far out as the
    budget allows (up to the expected move). Both legs must be liquid."""
    oc = cfg["options"]
    cap = oc["max_premium_usd"]
    s, right = m["price"], ("call" if sc["side"] == "bull" else "put")
    sgn = 1 if right == "call" else -1
    best = None
    for e in sorted(chains):
        dte = _dte(e, as_of)
        if not (oc["dte_min"] <= dte <= oc["dte_max"]):
            continue
        t = dte / 365
        em = m["em"].get(e) or ((m["iv30"] or 0.5) * math.sqrt(t))
        legs = sorted([r for r in chains[e] if r["type"] == right and _liquid(r, oc)], key=lambda r: r["strike"])
        if len(legs) < 2:
            continue
        long = min(legs, key=lambda r: abs(r["strike"] - s))
        for short in legs:
            width = sgn * (short["strike"] - long["strike"])
            if width <= 0 or width > s * em * 1.2:
                continue
            debit = round(long["ask"] - short["bid"], 2)
            if debit <= 0 or debit * 100 > cap or debit >= width:
                continue
            be = long["strike"] + sgn * debit
            req = sgn * (be / s - 1)
            if req / em > oc["max_be_to_em"]:
                continue
            pa = prob_above(s, be, t, long["iv"] or m["iv30"] or 0.5)
            plan = {"type": "spread", "symbol": long["symbol"], "short_symbol": short["symbol"], "right": right,
                    "strike": long["strike"], "short_strike": short["strike"], "exp": e, "dte": dte,
                    "entry": debit, "cost_usd": debit * 100, "contracts": 1,
                    "max_profit_usd": (width - debit) * 100, "breakeven": be, "req_move_pct": req, "em_pct": em,
                    "be_to_em": req / em, "pop": pa if right == "call" else 1 - pa, "delta": long["delta"],
                    "iv": long["iv"], "target": round(debit + 0.6 * (width - debit), 2),
                    "stop": round(debit * 0.5, 2), "underlying": s, "exit_by": e}
            # payoff per dollar risked, weighted by the chance of finishing past break-even
            q = (width - debit) / debit * plan["pop"]
            if best is None or q > best[0]:
                best = (q, plan)
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


def tags(m: dict, sc: dict, lang: str = "ru") -> str:
    """2-4 words: why this idea, for the Telegram line and card header."""
    en = lang == "en"
    bull = sc["side"] == "bull"
    drv = {"trend": ("uptrend" if bull else "downtrend") if en else ("тренд вверх" if bull else "тренд вниз"),
           "flow": ("money flowing into " + ("calls" if bull else "puts")) if en else ("приток денег в " + ("колы" if bull else "путы")),
           "unusual": ("volume spike in " + ("calls" if bull else "puts")) if en else ("всплеск объёма в " + ("колах" if bull else "путах")),
           "confirmed": "large flow stuck as OI" if en else "крупный поток закрепился в OI"}[sc["driver"]]
    out = [drv]
    if sc.get("exhausted"):  # the most important caveat goes right after the main signal
        out.append("snap-back risk" if en else "риск отскока")
    rs = m.get("rs20")
    if rs is not None and abs(rs) >= 0.03 and (rs > 0) == bull:
        out.append(("stronger than market" if bull else "weaker than market") if en else ("сильнее рынка" if bull else "слабее рынка"))
    r5 = m.get("ret5") or 0
    if abs(r5) >= 0.03 and (r5 > 0) == bull:
        out.append((f"{r5 * 100:+.1f}% in 5d" if en else f"{r5 * 100:+.1f}% за 5 дн.").replace("-", "−"))
    rsi = m.get("rsi14") or 50
    if sc.get("exhausted"):
        pass
    elif rsi < 25:
        out.append("oversold" if en else "перепродан")
    elif rsi > 75:
        out.append("overbought" if en else "перекуплен")
    if m.get("split"):
        out.append("split, partial data" if en else "сплит, данные неполные")
    if m.get("earnings_in_window"):
        out.append(f"earnings in {m['earnings_days']}d" if en else f"отчёт через {m['earnings_days']} дн.")
    return ", ".join(out[:3])
