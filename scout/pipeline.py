"""One daily run: fetch -> signals -> score -> ideas -> journal -> brief."""
from __future__ import annotations

import datetime as dt
import traceback

from . import ideas, journal, sectors, signals
from . import market as market_tab
from .mathx import mid

D = dt.date


def _dte(e, as_of):
    return (D.fromisoformat(e) - as_of).days


def run(as_of: D, provider, store, cfg: dict, log=print, record: bool = True) -> dict:
    iso = as_of.isoformat()
    scan_max = cfg["signals"]["scan_dte_max"]
    open_exps: dict[str, set] = {}
    for rec in store.open_recs():
        if rec["plan"].get("exp"):
            open_exps.setdefault(rec["ticker"], set()).add(rec["plan"]["exp"])

    rows, bars_today, chains_today, errors = [], {}, {}, []
    market = cfg.get("market", [])
    modes = list(cfg["options"].get("modes") or {"short": None})
    panic = market_tab.panic_state(provider, as_of, cfg, log)
    if panic["panic"]:
        log(f"PANIC regime: VIX {panic['vix']}, S&P from 3-month high {panic['dd']}: bearish trend ideas are off")
    uni = cfg.get("universe", {})
    open_tk = {rec["ticker"] for rec in store.open_recs()}

    # ---- stage 1: cheap prices for the whole universe, liquidity filter, preliminary rank
    names = list(dict.fromkeys(cfg["watchlist"] + uni.get("tickers", [])))
    all_bars = provider.history_many(list(dict.fromkeys(market + names + sorted(open_tk))), 300)
    spy = all_bars.get("SPY") or []
    spy_r20 = spy[-1]["close"] / spy[-21]["close"] - 1 if len(spy) > 21 else None
    passed, prelim, dropped, dvols = [], {}, 0, {}
    for t in names:
        bars = all_bars.get(t) or []
        if len(bars) < 60:
            dropped += 1
            continue
        px = bars[-1]["close"]
        dvol = sum(b["close"] * b["volume"] for b in bars[-20:]) / 20
        if px < uni.get("min_price", 0) or dvol < uni.get("min_dollar_volume", 0):
            dropped += 1
            continue
        ps = signals.price_stats(bars)
        tr = 0.5 * (1 if ps["sma20"] and px > ps["sma20"] else -1) + 0.3 * (
            1 if ps["sma20"] and ps["sma50"] and ps["sma20"] > ps["sma50"] else -1) + 0.2 * max(-1, min(1, ps["ret5"] / 0.05))
        rs = (ps["ret20"] - spy_r20) if (ps.get("ret20") is not None and spy_r20 is not None) else 0
        prelim[t] = abs(0.6 * tr + 0.4 * max(-1, min(1, rs / 0.1)))
        dvols[t] = dvol
        passed.append(t)
    n_deep = uni.get("deep_scan", 30)
    deep = [t for t in cfg["watchlist"] if t in prelim]
    # ties are common (signals saturate): break them by liquidity, then by name, so the same data
    # always gives the same shortlist
    deep += [t for t in sorted(passed, key=lambda t: (-round(prelim[t], 6), -dvols[t], t))
             if t not in deep][: max(0, n_deep - len(deep))]
    deep = list(dict.fromkeys(market + deep + [t for t in sorted(open_tk) if t in all_bars]))
    universe_info = {"checked": len(names), "passed": len(passed), "dropped": dropped, "deep": len(deep) - len(market)}
    log(f"universe: {len(names)} checked, {len(passed)} liquid, {len(deep)} deep-scanned")

    # ---- stage 2: option chains and full signals for the shortlist
    for t in deep:
        try:
            bars = all_bars.get(t) or provider.history(t, 300)
            if len(bars) < 30:
                raise RuntimeError("мало истории цен")
            bars_today[t] = bars[-1]
            exps = [e for e in provider.expirations(t) if 0 <= _dte(e, as_of) <= scan_max]
            exps = sorted(set(exps) | {e for e in open_exps.get(t, ()) if _dte(e, as_of) >= 0})
            px = bars[-1]["close"]
            # stale pre-split strikes (e.g. a 1800 put on a $78 stock) poison flow and volume signals
            chains = {e: [r for r in provider.chain(t, e) if 0.2 * px <= r["strike"] <= 5 * px] for e in exps}
            flat = [r for c in chains.values() for r in c]
            chains_today[t] = {r["symbol"]: r for r in flat}
            atm_oi = sum(r["oi"] for r in flat if abs(r["strike"] / px - 1) <= 0.1)
            if t not in market and t not in open_tk and atm_oi < uni.get("min_option_oi", 0):
                universe_info["dropped"] += 1
                universe_info["deep"] -= 1
                log(f"{t}: options too thin (OI near the money {atm_oi})")
                continue
            split = provider.recent_split(t)
            pd = store.prev_date(t, iso)
            prev = store.chain_on(t, pd) if pd else None
            earn = None if t in market else (str(cfg.get("earnings", {}).get(t) or "") or provider.earnings_date(t))
            m = signals.compute(t, as_of, bars, chains, prev, store.iv_history(t, iso), earn, cfg)
            if t not in market:  # observed only, not in the score yet: the journal tests it first
                try:
                    m.update(provider.short_interest(t) or {})
                except Exception as ex:
                    log(f"{t}: short interest: {ex}")
            m["rs20"] = (m["ret20"] - spy_r20) if (m.get("ret20") is not None and spy_r20 is not None and t != "SPY") else None
            if split:
                m["split"] = split
                if pd is None or pd < split[0]:  # yesterday's OI is in pre-split contracts: no valid comparison
                    m.update(flow_bias=0.0, confirmed_bias=0.0, confirmed=[], has_prev=False)
            store.save_chain(iso, t, flat)
            store.save_metrics(iso, t, {k: v for k, v in m.items() if k not in ("em",)})
            sc = ideas.score(m, cfg)
            row = {"ticker": t, "market": t in market, "watch": t in cfg["watchlist"], "m": m, "s": sc,
                   "sector": sectors.group(t)}
            if t not in market:
                row["tiers_by_mode"], row["rebound_by_mode"] = {}, {}
                for mode in modes:
                    mc = ideas.mode_cfg(cfg, mode)
                    tiers = ideas.build_option_tiers(m, sc, chains, as_of, mc)
                    row["tiers_by_mode"][mode] = {k: (p, ideas.option_score(sc, p)) for k, (p, _) in tiers.items() if p}
                    if mode == modes[0]:
                        row["option_why"] = next((w for _, w in tiers.values() if w), "")
                    rb_plan, rb_score, _ = ideas.build_rebound(m, sc, chains, as_of, mc)
                    if rb_plan:
                        row["rebound_by_mode"][mode] = (rb_plan, rb_score)
                row["option_tiers"] = row["tiers_by_mode"][modes[0]]
                allt = [v for tm in row["tiers_by_mode"].values() for v in tm.values()]
                best = max(allt, key=lambda v: v[1], default=None)
                row["option"], row["option_score"] = (best[0], best[1]) if best else (None, 0)
                if best:
                    row["option_why"] = ""
                if modes[0] in row["rebound_by_mode"]:
                    row["rebound"], row["rebound_score"] = row["rebound_by_mode"][modes[0]]
                row["stock"] = ideas.build_stock(m, sc, cfg, as_of)
                row["why"] = ideas.tags(m, sc)
                row["why_en"] = ideas.tags(m, sc, "en")
            rows.append(row)
            log(f"{t:6} dir={sc['direction']:+.2f} opt={row.get('option_score', 0):.0f} stk={sc['stock_score']:.0f}"
                + (f"  opt: {row['option_why']}" if row.get("option_why") else ""))
        except Exception as ex:  # one bad ticker must not kill the brief
            errors.append({"ticker": t, "error": str(ex)})
            log(f"{t}: ERROR {ex}")
            log(traceback.format_exc(limit=2))

    closed_today = journal.evaluate(store, as_of, bars_today, chains_today)

    oc = cfg["output"]
    names = [r for r in rows if not r["market"]]
    def rank_key(score):
        # equal strength -> stronger relative move vs SPY first, then more liquid, then by name
        return lambda r: (-round(score(r), 6), -abs(r["m"].get("rs20") or 0), -dvols.get(r["ticker"], 0), r["ticker"])

    # diversification: at most N ideas per sector across the whole brief (options first)
    per = oc.get("max_per_sector", 2)
    counts: dict = {}
    # panic: no bearish trend ideas (backtest: trend shorts lose when the market is in a panic)
    allowed = lambda r: not (panic["panic"] and r["s"]["side"] == "bear")
    # options: the best idea in each price tier, separately for each expiration mode
    # (short = weeklies, long = 2-5 weeks; both are journaled to compare them after 3 months)
    opt = []
    for mode in modes:
        used, cnt = set(), (counts if mode == modes[0] else {})
        for tier in cfg["options"].get("tiers", []):
            k = tier["key"]
            tm = lambda r: r.get("tiers_by_mode", {}).get(mode, {})
            cands = [r for r in names if r["ticker"] not in used and k in tm(r) and tm(r)[k][1] >= tier["min_score"] and allowed(r)]
            cands = sectors.cap(sorted(cands, key=rank_key(lambda r, k=k: tm(r)[k][1])), per, dict(cnt))
            if cands:
                r = cands[0]
                plan, sc_ = tm(r)[k]
                opt.append(dict(r, option=dict(plan, tier=k, mode=mode), option_score=sc_, tier=k, mode=mode))
                used.add(r["ticker"])
                cnt[r["sector"]] = cnt.get(r["sector"], 0) + 1
    # counter-trend section: calls after an overstretched drop (shorts after spikes lost in the backtest)
    rb_cfg = cfg["options"].get("rebound", {})
    rebounds = []
    for mode in modes:
        cands = [r for r in names if mode in r.get("rebound_by_mode", {})
                 and r["rebound_by_mode"][mode][1] >= rb_cfg.get("min_score", 50) and r["s"]["side"] == "bear"]
        for r in sorted(cands, key=rank_key(lambda r: r["rebound_by_mode"][mode][1]))[: rb_cfg.get("max_ideas", 1)]:
            e = r["s"]["exhaust"]
            plan, sc_ = r["rebound_by_mode"][mode]
            mv = f"{e['ret5'] * 100:+.1f}%".replace("-", "−")
            rebounds.append(dict(r, option=dict(plan, tier="rebound", mode=mode), option_score=sc_, tier="rebound", mode=mode,
                                 s=dict(r["s"], side="bull", driver="rebound"),
                                 why=f"отскок после {mv} за 5 дн., RSI {e['rsi']:.0f}",
                                 why_en=f"snap-back after {mv} in 5d, RSI {e['rsi']:.0f}"))
    stk = sectors.cap(sorted([r for r in names if r.get("stock") and r["s"]["stock_score"] >= oc["min_score"] and allowed(r)],
                             key=rank_key(lambda r: r["s"]["stock_score"])), per, counts)[: oc["top_stocks"]]
    picked = {r["ticker"] for r in opt} | {r["ticker"] for r in stk}
    near = sorted([r for r in names if r["ticker"] not in picked and (r.get("option") or r.get("stock"))],
                  key=rank_key(lambda r: max(r.get("option_score", 0), r["s"]["stock_score"])))[:3]
    opened = {(rec["ticker"], rec["kind"]): rec["as_of"] for rec in store.open_recs()}
    new_ideas = []
    long_kind = lambda base, r: base + ("_long" if r.get("mode") == "long" else "")
    for base, lst, key in (("option", opt, "option"), ("stock", stk, "stock"), ("rebound", rebounds, "option")):
        for r in lst:
            kind = long_kind(base, r)
            since = opened.get((r["ticker"], kind))
            r[f"{key}_open_since"] = since
            if since is None:
                sc_ = r["option_score"] if kind in ("option", "rebound") else r["s"]["stock_score"]
                if record:  # the track record keeps only the pre-close brief's ideas
                    store.add_rec(iso, r["ticker"], kind, r["s"]["side"], sc_, r["s"]["driver"], r[key])
                new_ideas.append({"kind": kind, "row": r, "score": sc_})

    avoid = []
    for r in names:
        m = r["m"]
        rich = (m.get("iv_rank") or 0) > 70 or (m.get("iv_hv") or 0) > 1.4
        if m["earnings_in_window"] and rich:
            avoid.append({"ticker": r["ticker"], "why": f"отчёт через {m['earnings_days']} дн. и дорогая IV: покупка опционов = ставка против IV crush",
                          "why_en": f"earnings in {m['earnings_days']}d and expensive IV: buying options is a bet against IV crush"})
        elif not r.get("option") and r.get("option_why") == "безубыток дальше ожидаемого движения" and r["s"]["conviction"] >= 0.3:
            avoid.append({"ticker": r["ticker"], "why": "сигнал есть, но дешёвые контракты требуют движения больше ожидаемого",
                          "why_en": "there is a signal, but cheap contracts need a bigger move than expected"})

    open_view = []
    for rec in store.open_recs():
        p, t = rec["plan"], rec["ticker"]
        cur = None
        if p["type"] in ("option", "spread"):
            ch = chains_today.get(t, {})
            r1 = ch.get(p["symbol"])
            if r1:
                cur = mid(r1["bid"], r1["ask"], r1["last"])
                if p["type"] == "spread":
                    r2 = ch.get(p["short_symbol"])
                    cur = cur - mid(r2["bid"], r2["ask"], r2["last"]) if r2 else None
        elif t in bars_today:
            cur = bars_today[t]["close"]
        open_view.append({**rec, "current": cur, "pnl": journal.pnl(rec, cur)})

    store.prune_chains(3)
    store.commit()
    closed = store.closed_recs()
    since30 = (as_of - dt.timedelta(days=30)).isoformat()
    return {
        "as_of": iso, "provider": provider.name, "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
        "market": [r for r in rows if r["market"]], "options": opt, "stocks": stk, "avoid": avoid[:6],
        "scanner": sorted(names, key=lambda r: -max(r.get("option_score", 0), r["s"]["stock_score"])),
        "open": [o for o in open_view if o["as_of"] < iso], "closed_today": closed_today, "new_ideas": new_ideas, "recorded": record, "rebounds": rebounds,
        "week_closed": [c for c in closed if c["exit_date"] >= (as_of - dt.timedelta(days=as_of.weekday())).isoformat()],
        "stats_all": journal.stats(closed), "stats_30": journal.stats(closed, since30),
        "recent_closed": closed[-12:][::-1], "errors": errors,
        "account": cfg["account"], "universe": universe_info, "near": near, "min_score": cfg["output"]["min_score"], "min_score_options": min((t["min_score"] for t in cfg["options"].get("tiers", [])), default=60),
        "macro": market_tab.build(provider, as_of, rows, log, all_bars), "panic": panic,
        "dropped_bear": sorted({r["ticker"] for r in names if panic["panic"] and r["s"]["side"] == "bear"
                                and (r.get("option") or r.get("stock"))}),
    }
