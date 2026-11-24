"""CLI.

  python -m scout run                      # today, provider from SCOUT_PROVIDER (default yfinance)
  python -m scout run --window             # only inside the last session hour (for cron)
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


def write_outputs(brief: dict, out: Path, quiet=False):
    out.mkdir(parents=True, exist_ok=True)
    page = report.render_html(brief)
    (out / f"{brief['as_of']}.html").write_text(page, encoding="utf-8")
    (out / "index.html").write_text(page, encoding="utf-8")
    slim = {k: brief[k] for k in ("as_of", "provider", "avoid", "stats_all", "stats_30", "errors")}
    slim["options"] = [{"ticker": r["ticker"], "score": r["option_score"], "plan": r["option"],
                        "reasons": r["s"]["reasons"]} for r in brief["options"]]
    slim["stocks"] = [{"ticker": r["ticker"], "score": r["s"]["stock_score"], "plan": r["stock"],
                       "reasons": r["s"]["reasons"]} for r in brief["stocks"]]
    (out / "brief.json").write_text(json.dumps(slim, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    text = report.render_text(brief)
    (out / "brief.txt").write_text(text, encoding="utf-8")
    return text, slim


def main():
    ap = argparse.ArgumentParser(prog="scout")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--date")
    r.add_argument("--provider", default=os.environ.get("SCOUT_PROVIDER", "yfinance"))
    r.add_argument("--window", action="store_true", help="run only 15:00-16:30 New York time, once a day")
    r.add_argument("--db", default=str(ROOT / "data" / "scout.db"))
    r.add_argument("--out", default=str(ROOT / "reports"))
    r.add_argument("--config")
    r.add_argument("--notify", action="store_true")
    d = sub.add_parser("demo")
    d.add_argument("--days", type=int, default=40)
    d.add_argument("--end", default=dt.date.today().isoformat())
    d.add_argument("--db", default=str(ROOT / "data" / "demo.db"))
    d.add_argument("--out", default=str(ROOT / "reports" / "demo"))
    d.add_argument("--config")
    a = ap.parse_args()
    cfg = load_cfg(a.config)

    if a.cmd == "run":
        from zoneinfo import ZoneInfo

        ny = dt.datetime.now(ZoneInfo("America/New_York"))
        as_of = dt.date.fromisoformat(a.date) if a.date else ny.date()
        if a.window:
            if ny.weekday() >= 5 or not (dt.time(15, 0) <= ny.time() <= dt.time(16, 30)):
                print(f"outside scan window ({ny:%H:%M} New York), skipping")
                return
            if (Path(a.out) / f"{as_of}.html").exists():
                print("already ran today, skipping")
                return
        store = Store(a.db)
        brief = pipeline.run(as_of, make_provider(a.provider, as_of), store, cfg)
        text, slim = write_outputs(brief, Path(a.out))
        summary = None
        try:
            summary = llm.summarize(text, slim)
        except Exception as ex:
            print("LLM summary skipped:", ex)
        if summary:
            text = summary + "\n\n" + text
        print(text)
        if a.notify:
            notify.telegram(text, os.environ.get("SCOUT_REPORT_URL"))
    else:
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
        text, _ = write_outputs(brief, Path(a.out))
        print(text)


if __name__ == "__main__":
    main()
