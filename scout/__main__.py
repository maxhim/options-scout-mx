"""CLI.

  python -m scout run                      # today, provider from SCOUT_PROVIDER (default yfinance)
  python -m scout run --window             # evening brief, only inside the last session hour (cron)
  python -m scout run --intraday           # daytime alert: new strong ideas + closed ones (cron)
  python -m scout run --test               # manual check: works on a copy of the DB, journal untouched
  python -m scout run --provider tradier
  python -m scout run --date 2026-11-24 --provider demo
  python -m scout demo --days 40           # simulate 40 sessions on synthetic data
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

import yaml

from . import llm, notify, pipeline, report
from .providers import DemoProvider, make_provider
from .storage import Store

ROOT = Path(__file__).resolve().parent.parent


def load_cfg(path: str | None) -> dict:
    with open(path or ROOT / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg.setdefault("market", ["SPY", "QQQ"])
    cfg["earnings"] = {k: str(v) for k, v in (cfg.get("earnings") or {}).items()}
    return cfg


def write_outputs(brief: dict, out: Path, dated=True, weekly=False):
    """Russian page at reports/, English at reports/en/. Returns (texts by language, slim json)."""
    out.mkdir(parents=True, exist_ok=True)
    page = report.render_html(brief, "ru")
    if dated:  # the dated page also marks "evening brief done today"
        (out / f"{brief['as_of']}.html").write_text(page, encoding="utf-8")
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / "en").mkdir(exist_ok=True)
    (out / "en" / "index.html").write_text(report.render_html(brief, "en"), encoding="utf-8")
    slim = {k: brief[k] for k in ("as_of", "provider", "avoid", "stats_all", "stats_30", "errors")}
    slim["options"] = [{"ticker": r["ticker"], "score": r["option_score"], "plan": r["option"],
                        "reasons": r["s"]["reasons"]} for r in brief["options"]]
    slim["stocks"] = [{"ticker": r["ticker"], "score": r["s"]["stock_score"], "plan": r["stock"],
                       "reasons": r["s"]["reasons"]} for r in brief["stocks"]]
    (out / "brief.json").write_text(json.dumps(slim, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    texts = {lang: report.render_text(brief, weekly=weekly, lang=lang) for lang in ("ru", "en")}
    (out / "brief.txt").write_text(texts["ru"], encoding="utf-8")
    return texts, slim


def opening_rush(ny: dt.datetime) -> bool:
    """09:30-10:00 New York on a weekday."""
    return ny.weekday() < 5 and dt.time(9, 30) <= ny.time() < dt.time(10, 0)


def bot_username(cfg: dict) -> str:
    """The bot's @username for the subscribe button: asked from Telegram, else config."""
    token = os.environ.get("TELEGRAM_TOKEN")
    if token:
        try:
            import requests

            r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=15)
            if r.ok:
                return r.json()["result"]["username"]
        except Exception:
            pass
    return (cfg.get("telegram") or {}).get("bot_username") or "option_scout_bot"


def deliver(texts: dict, test: bool, subs_path: Path):
    """Test runs go to the owner only; real runs to every subscriber in their language."""
    from . import subscribers

    texts = {k: v for k, v in texts.items() if v}
    if test:
        if texts:
            notify.telegram(texts["ru"], notify.site_url("ru"))
        return None, None
    # subscribers are synced on every real run, even when there is nothing to send
    data = subscribers.run_sync(subs_path) or {}
    if not texts:
        return 0, data
    n = notify.broadcast(texts, subscribers.recipients(data, os.environ.get("TELEGRAM_CHAT_ID")))
    print(f"delivered to {n} chats")
    return n, data


def record_run(store, brief, mode, delivered, subs, out: Path, subs_path: Path):
    """Run history (counts only) for the admin page, then rebuild the encrypted admin page."""
    from . import admin, subscribers

    owner = os.environ.get("TELEGRAM_CHAT_ID")
    if subs is None and os.environ.get("TELEGRAM_TOKEN"):
        try:
            subs = subscribers.load(subs_path, os.environ["TELEGRAM_TOKEN"])
        except Exception:
            subs = None
    u = brief.get("universe") or {}
    rg = (brief.get("macro") or {}).get("regime") or {}
    n_subs = len([c for c in subs.get("subs", {}) if c != str(owner)]) if subs else None
    store.log_run({"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "as_of": brief["as_of"],
                   "mode": mode, "options": len(brief["options"]), "stocks": len(brief["stocks"]),
                   "checked": u.get("checked"), "liquid": u.get("passed"), "deep": u.get("deep"),
                   "errors": len(brief["errors"]), "delivered": delivered, "subscribers": n_subs,
                   "regime": rg.get("label"), "vix": rg.get("vix")})
    repo = os.environ.get("GITHUB_REPOSITORY", "maxhim/options-scout-mx")
    gc = os.environ.get("GOATCOUNTER_CODE")
    links = {"сайт": notify.site_url("ru"), "Actions": f"https://github.com/{repo}/actions",
             "посещения (GoatCounter)": f"https://{gc}.goatcounter.com" if gc else None}
    if admin.write(out, store, subs, owner, links):
        print("admin page updated")


def main():
    ap = argparse.ArgumentParser(prog="scout")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--date")
    r.add_argument("--provider", default=os.environ.get("SCOUT_PROVIDER", "yfinance"))
    r.add_argument("--window", action="store_true",
                   help="cron guard: evening brief only 15:00-16:30 New York once a day; with --intraday only in its slots")
    r.add_argument("--db", default=str(ROOT / "data" / "scout.db"))
    r.add_argument("--out", default=str(ROOT / "reports"))
    r.add_argument("--config")
    r.add_argument("--notify", action="store_true")
    r.add_argument("--intraday", action="store_true", help="daytime alert run (11:00 and 13:30 New York)")
    r.add_argument("--test", action="store_true", help="run on a throwaway copy of the DB")
    u = sub.add_parser("universe", help="monthly refresh of universe.tickers in config.yaml")
    u.add_argument("--config")
    u.add_argument("--notify", action="store_true")
    d = sub.add_parser("demo")
    d.add_argument("--days", type=int, default=40)
    d.add_argument("--end", default=dt.date.today().isoformat())
    d.add_argument("--db", default=str(ROOT / "data" / "demo.db"))
    d.add_argument("--out", default=str(ROOT / "reports" / "demo"))
    d.add_argument("--config")
    a = ap.parse_args()
    cfg = load_cfg(a.config)

    if a.cmd == "universe":
        from . import universe

        path = Path(a.config) if a.config else ROOT / "config.yaml"
        diff = universe.refresh(path, cfg["universe"]["tickers"])
        text = universe.render(diff)
        print(text)
        if a.notify and (diff["added"] or diff["removed"]):
            notify.telegram(text)  # service message: owner only
        return

    if a.cmd == "run":
        from zoneinfo import ZoneInfo

        ny = dt.datetime.now(ZoneInfo("America/New_York"))
        as_of = dt.date.fromisoformat(a.date) if a.date else ny.date()
        if a.window and not a.intraday:
            if ny.weekday() >= 5 or not (dt.time(15, 0) <= ny.time() <= dt.time(16, 30)):
                print(f"outside scan window ({ny:%H:%M} New York), skipping")
                return
            if (Path(a.out) / f"{as_of}.html").exists():
                print("already ran today, skipping")
                return
        if a.window and a.intraday:
            # two cron entries per slot cover summer/winter time; only the one landing here runs
            slots = [(dt.time(10, 55), dt.time(11, 50)), (dt.time(13, 25), dt.time(14, 20))]
            if ny.weekday() >= 5 or not any(lo <= ny.time() <= hi for lo, hi in slots):
                print(f"outside intraday slots ({ny:%H:%M} New York), skipping")
                return
        if not (a.window or a.test or a.intraday) and opening_rush(ny):
            print(f"{ny:%H:%M} New York: the first 30 minutes of the session have wide option spreads and jumpy prices; "
                  "a production brief is not run now. Use mode=test, or run after 10:00 (or before the open).")
            return
        db = a.db
        chains_db = str(Path(a.db).with_name(Path(a.db).stem + "-chains.db"))
        if a.test:
            import shutil
            import tempfile

            tmp = Path(tempfile.mkdtemp())
            for src in (a.db, chains_db):
                if Path(src).exists():
                    shutil.copy(src, tmp / Path(src).name)
            db, chains_db = str(tmp / Path(a.db).name), str(tmp / Path(chains_db).name)
        if a.intraday:
            cfg["output"]["min_score"] = max(cfg["output"]["min_score"], cfg.get("alerts", {}).get("min_score", 55))
        store = Store(db, chains_db)
        brief = pipeline.run(as_of, make_provider(a.provider, as_of), store, cfg)
        brief["test"] = a.test
        # Yahoo revises the day's close after the bell and drops option quotes: flag such runs
        brief["off_hours"] = ny.weekday() >= 5 or not (dt.time(9, 30) <= ny.time() <= dt.time(16, 0)) or as_of != ny.date()
        brief["bot"] = bot_username(cfg)
        brief["goatcounter"] = os.environ.get("GOATCOUNTER_CODE")
        subs_path = Path(a.db).with_name("subscribers.enc")
        weekly = as_of.weekday() == 4 and not a.intraday
        # only the scheduled evening run marks "brief done today": a manual run must not cancel it
        texts, slim = write_outputs(brief, Path(a.out), dated=a.window and not (a.test or a.intraday), weekly=weekly)
        if a.intraday:
            alerts = {lang: report.render_alert(brief, f"{ny:%H:%M}", lang) for lang in ("ru", "en")}
            print(alerts["ru"] or "intraday: nothing new")
            n, subs = deliver(alerts, a.test, subs_path) if a.notify else (None, None)
            if not a.test:
                record_run(store, brief, "alert", n, subs, Path(a.out), subs_path)
            return
        text = texts["ru"]
        summary = None
        try:
            summary = llm.summarize(text, slim)
        except Exception as ex:
            print("LLM summary skipped:", ex)
        if summary:
            import html  # the summary is plain text: escape it and put it under the title
            text = text.replace("\n", "\n\n💬 " + html.escape(summary) + "\n", 1)
        texts["ru"] = text
        print(text)
        n, subs = deliver(texts, a.test, subs_path) if a.notify else (None, None)
        if not a.test:
            record_run(store, brief, "brief", n, subs, Path(a.out), subs_path)
    else:
        # synthetic volumes and OI are arbitrary: liquidity filters would only hide demo tickers
        cfg["universe"].update(min_dollar_volume=0, min_option_oi=0)
        if Path(a.db).exists():
            Path(a.db).unlink()
        end = dt.date.fromisoformat(a.end)
        store = Store(a.db)
        days, x = [], end
        while len(days) < a.days:
            if x.weekday() < 5:
                days.append(x)
            x -= dt.timedelta(days=1)
        brief = None
        for day in days[::-1]:
            brief = pipeline.run(day, DemoProvider(day, end=end), store, cfg, log=lambda *_: None)
            print(day, "ideas:", len(brief["options"]), "+", len(brief["stocks"]), "closed:", len(brief["closed_today"]))
        texts, _ = write_outputs(brief, Path(a.out))
        print(texts["ru"])


if __name__ == "__main__":
    main()
