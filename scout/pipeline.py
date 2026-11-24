"""One daily run: fetch -> signals -> score -> ideas -> journal -> brief."""
from __future__ import annotations

import datetime as dt
import traceback

from . import ideas, journal, signals
from . import market as market_tab
from .mathx import mid

D = dt.date


def _dte(e, as_of):
    return (D.fromisoformat(e) - as_of).days


def run(as_of: D, provider, store, cfg: dict, log=print) -> dict:
    iso = as_of.isoformat()
    scan_max = cfg["signals"]["scan_dte_max"]
    open_exps: dict[str, set] = {}
    for rec in store.open_recs():
        if rec["plan"].get("exp"):
            open_exps.setdefault(rec["ticker"], set()).add(rec["plan"]["exp"])

    rows, bars_today, chains_today, errors = [], {}, {}, []
    market = cfg.get("market", [])
    for t in market + [x for x in cfg["watchlist"] if x not in market]:
        try:
            bars = provider.history(t, 300)
            if len(bars) < 30:
                raise RuntimeError("мало истории цен")
            bars_today[t] = bars[-1]
            exps = [e for e in provider.expirations(t) if 0 <= _dte(e, as_of) <= scan_max]
            exps = sorted(set(exps) | {e for e in open_exps.get(t, ()) if _dte(e, as_of) >= 0})
            px = bars[-1]["close"]
            # stale pre-split strikes (e.g. a 1800 put on a $78 stock) poison flow and volume signals
            chains = {e: [r for r in provider.chain(t, e) if 0.2 * px <= r["strike"] <= 5 * px] for e in exps}
            split = provider.recent_split(t)
            flat = [r for c in chains.values() for r in c]
            chains_today[t] = {r["symbol"]: r for r in flat}
            pd = store.prev_date(t, iso)
            prev = store.chain_on(t, pd) if pd else None
            earn = str(cfg.get("earnings", {}).get(t) or "") or provider.earnings_date(t)
            m = signals.compute(t, as_of, bars, chains, prev, store.iv_history(t, iso), earn, cfg)
            if split:
                m["split"] = split
                if pd is None or pd < split[0]:  # yesterday's OI is in pre-split contracts: no valid comparison
                    m.update(flow_bias=0.0, confirmed_bias=0.0, confirmed=[], has_prev=False)
            store.save_chain(iso, t, flat)
            store.save_metrics(iso, t, {k: v for k, v in m.items() if k not in ("em",)})
            sc = ideas.score(m, cfg)
            row = {"ticker": t, "market": t in market, "m": m, "s": sc}
            if t not in market:
                plan, why = ideas.build_option(m, sc, chains, as_of, cfg)
                row["option"], row["option_why"] = plan, why
                row["option_score"] = ideas.option_score(sc, plan) if plan else 0
                row["stock"] = ideas.build_stock(m, sc, cfg, as_of)
                row["why"] = ideas.tags(m, sc)
            rows.append(row)
            log(f"{t:6} dir={sc['direction']:+.2f} opt={row.get('option_score', 0):.0f} stk={sc['stock_score']:.0f}")
        except Exception as ex:  # one bad ticker must not kill the brief
            errors.append({"ticker": t, "error": str(ex)})
            log(f"{t}: ERROR {ex}")
            log(traceback.format_exc(limit=2))

    closed_today = journal.evaluate(store, as_of, bars_today, chains_today)

    oc = cfg["output"]
    names = [r for r in rows if not r["market"]]
    opt = sorted([r for r in names if r.get("option") and r["option_score"] >= oc["min_score"]],
                 key=lambda r: -r["option_score"])[: oc["top_options"]]
    stk = sorted([r for r in names if r.get("stock") and r["s"]["stock_score"] >= oc["min_score"]],
                 key=lambda r: -r["s"]["stock_score"])[: oc["top_stocks"]]
    opened = {(rec["ticker"], rec["kind"]): rec["as_of"] for rec in store.open_recs()}
    new_ideas = []
    for kind, lst, key in (("option", opt, "option"), ("stock", stk, "stock")):
        for r in lst:
            since = opened.get((r["ticker"], kind))
            r[f"{kind}_open_since"] = since
            if since is None:
                sc_ = r["option_score"] if kind == "option" else r["s"]["stock_score"]
                store.add_rec(iso, r["ticker"], kind, r["s"]["side"], sc_, r["s"]["driver"], r[key])
                new_ideas.append({"kind": kind, "row": r, "score": sc_})

    avoid = []
    for r in names:
        m = r["m"]
        rich = (m.get("iv_rank") or 0) > 70 or (m.get("iv_hv") or 0) > 1.4
        if m["earnings_in_window"] and rich:
            avoid.append({"ticker": r["ticker"], "why": f"отчёт через {m['earnings_days']} дн. и дорогая IV: покупка опционов = ставка против IV crush"})
        elif not r.get("option") and r.get("option_why") == "безубыток дальше ожидаемого движения" and r["s"]["conviction"] >= 0.3:
            avoid.append({"ticker": r["ticker"], "why": "сигнал есть, но дешёвые контракты требуют движения больше ожидаемого"})

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

    store.prune_chains(10)
    store.commit()
    closed = store.closed_recs()
    since30 = (as_of - dt.timedelta(days=30)).isoformat()
    return {
        "as_of": iso, "provider": provider.name, "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
        "market": [r for r in rows if r["market"]], "options": opt, "stocks": stk, "avoid": avoid[:6],
        "scanner": sorted(names, key=lambda r: -max(r.get("option_score", 0), r["s"]["stock_score"])),
        "open": [o for o in open_view if o["as_of"] < iso], "closed_today": closed_today, "new_ideas": new_ideas,
        "week_closed": [c for c in closed if c["exit_date"] >= (as_of - dt.timedelta(days=as_of.weekday())).isoformat()],
        "stats_all": journal.stats(closed), "stats_30": journal.stats(closed, since30),
        "recent_closed": closed[-12:][::-1], "errors": errors,
        "account": cfg["account"], "macro": market_tab.build(provider, as_of, rows, log),
    }
