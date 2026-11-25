"""SQLite storage: daily chain snapshots, IV history, recommendations journal."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

CHAIN_SCHEMA = """
CREATE TABLE IF NOT EXISTS chain (
  as_of TEXT, ticker TEXT, symbol TEXT, type TEXT, strike REAL, exp TEXT,
  bid REAL, ask REAL, volume INTEGER, oi INTEGER, iv REAL, delta REAL,
  PRIMARY KEY (as_of, symbol)
);
CREATE INDEX IF NOT EXISTS chain_t ON chain(ticker, as_of);
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS metrics (
  as_of TEXT, ticker TEXT, price REAL, iv30 REAL, hv20 REAL, data TEXT,
  PRIMARY KEY (as_of, ticker)
);
CREATE TABLE IF NOT EXISTS runs (
  ts TEXT, as_of TEXT, mode TEXT, options INTEGER, stocks INTEGER, checked INTEGER, liquid INTEGER,
  deep INTEGER, errors INTEGER, delivered INTEGER, subscribers INTEGER, regime TEXT, vix REAL
);
CREATE TABLE IF NOT EXISTS recs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  as_of TEXT, ticker TEXT, kind TEXT, side TEXT, score REAL, driver TEXT,
  plan TEXT, status TEXT DEFAULT 'open',
  exit_date TEXT, exit_price REAL, result_r REAL, exit_reason TEXT
);
"""


class Store:
    """Journal + metrics live in `path` (small, committed to git).
    Option-chain snapshots live in `chain_path` (big, only the last few days are needed;
    kept in the Actions cache). Without chain_path both live in one file (tests, demo)."""

    def __init__(self, path: str | Path, chain_path: str | Path | None = None):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        if chain_path and Path(chain_path).resolve() != Path(path).resolve():
            self.cdb = sqlite3.connect(str(chain_path))
            self.cdb.row_factory = sqlite3.Row
            self.cdb.executescript(CHAIN_SCHEMA)
            self._migrate_chains()
        else:
            self.db.executescript(CHAIN_SCHEMA)
            self.cdb = self.db

    def _migrate_chains(self):
        """Older versions kept chains in the main file: move them out once and shrink it."""
        has = self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='chain'").fetchone()
        if not has:
            return
        if not self.cdb.execute("SELECT 1 FROM chain LIMIT 1").fetchone():
            rows = self.db.execute("SELECT * FROM chain").fetchall()
            self.cdb.executemany("INSERT OR REPLACE INTO chain VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [tuple(r) for r in rows])
            self.cdb.commit()
        self.db.execute("DROP TABLE chain")
        self.db.commit()
        self.db.execute("VACUUM")

    # ---- chains
    def save_chain(self, as_of: str, ticker: str, rows: list[dict]):
        self.cdb.executemany(
            "INSERT OR REPLACE INTO chain VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            [(as_of, ticker, r["symbol"], r["type"], r["strike"], r["exp"], r["bid"], r["ask"],
              r["volume"], r["oi"], r["iv"], r["delta"]) for r in rows],
        )

    def prev_date(self, ticker: str, as_of: str) -> str | None:
        r = self.cdb.execute(
            "SELECT MAX(as_of) d FROM chain WHERE ticker=? AND as_of<?", (ticker, as_of)
        ).fetchone()
        return r["d"] if r else None

    def chain_on(self, ticker: str, as_of: str) -> dict[str, sqlite3.Row]:
        rows = self.cdb.execute("SELECT * FROM chain WHERE ticker=? AND as_of=?", (ticker, as_of))
        return {r["symbol"]: r for r in rows}

    def prune_chains(self, keep_days: int = 3):
        """Chains are big: only yesterday's snapshot is needed (metrics keep the long history)."""
        self.cdb.execute(
            "DELETE FROM chain WHERE as_of NOT IN (SELECT DISTINCT as_of FROM chain ORDER BY as_of DESC LIMIT ?)",
            (keep_days,),
        )

    # ---- metrics / iv history
    def save_metrics(self, as_of: str, ticker: str, m: dict):
        self.db.execute(
            "INSERT OR REPLACE INTO metrics VALUES (?,?,?,?,?,?)",
            (as_of, ticker, m.get("price"), m.get("iv30"), m.get("hv20"), json.dumps(m, default=str)),
        )

    def iv_history(self, ticker: str, as_of: str, n: int = 252) -> list[float]:
        rows = self.db.execute(
            "SELECT iv30 FROM metrics WHERE ticker=? AND as_of<? AND iv30 IS NOT NULL ORDER BY as_of DESC LIMIT ?",
            (ticker, as_of, n),
        )
        return [r["iv30"] for r in rows]

    def metrics_on(self, ticker: str, as_of: str) -> dict | None:
        r = self.db.execute("SELECT data FROM metrics WHERE ticker=? AND as_of=?", (ticker, as_of)).fetchone()
        return json.loads(r["data"]) if r else None

    # ---- journal
    def add_rec(self, as_of, ticker, kind, side, score, driver, plan: dict):
        self.db.execute(
            "INSERT INTO recs (as_of,ticker,kind,side,score,driver,plan) VALUES (?,?,?,?,?,?,?)",
            (as_of, ticker, kind, side, score, driver, json.dumps(plan)),
        )

    def log_run(self, row: dict):
        cols = ["ts", "as_of", "mode", "options", "stocks", "checked", "liquid", "deep", "errors",
                "delivered", "subscribers", "regime", "vix"]
        self.db.execute(f"INSERT INTO runs ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                        [row.get(c) for c in cols])
        self.db.commit()

    def runs(self, limit: int = 60) -> list[dict]:
        return [dict(r) for r in self.db.execute("SELECT * FROM runs ORDER BY ts DESC LIMIT ?", (limit,))]

    def open_recs(self):
        return [dict(r) | {"plan": json.loads(r["plan"])} for r in
                self.db.execute("SELECT * FROM recs WHERE status='open' ORDER BY as_of")]

    def closed_recs(self):
        return [dict(r) | {"plan": json.loads(r["plan"])} for r in
                self.db.execute("SELECT * FROM recs WHERE status='closed' ORDER BY exit_date")]

    def has_open(self, ticker: str, kind: str) -> bool:
        return self.db.execute(
            "SELECT 1 FROM recs WHERE status='open' AND ticker=? AND kind=?", (ticker, kind)
        ).fetchone() is not None

    def close_rec(self, rid: int, date: str, price: float, r: float, reason: str):
        self.db.execute(
            "UPDATE recs SET status='closed', exit_date=?, exit_price=?, result_r=?, exit_reason=? WHERE id=?",
            (date, price, r, reason, rid),
        )

    def commit(self):
        self.db.commit()
        if self.cdb is not self.db:
            self.cdb.commit()
