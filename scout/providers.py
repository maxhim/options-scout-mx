"""Market data providers.

Every provider returns plain dicts so the rest of the engine does not care
where data came from.

Contract dict: symbol, type ('call'|'put'), strike, exp (YYYY-MM-DD), bid, ask,
last, volume, oi, iv (decimal), delta.
Bar dict: date, open, high, low, close, volume.
"""
from __future__ import annotations

import datetime as dt
import math
import os
import random
import zlib

from .mathx import bs_delta, bs_price, implied_vol, implied_vol

D = dt.date


def _iso(d: D) -> str:
    return d.isoformat()


class Provider:
    name = "base"

    def __init__(self, as_of: D):
        self.as_of = as_of

    def history(self, ticker: str, days: int = 400) -> list[dict]:
        raise NotImplementedError

    def expirations(self, ticker: str) -> list[str]:
        raise NotImplementedError

    def chain(self, ticker: str, exp: str) -> list[dict]:
        raise NotImplementedError

    def earnings_date(self, ticker: str) -> str | None:
        return None

    def recent_split(self, ticker: str, days: int = 30) -> tuple[str, float] | None:
        """(date, ratio) of a stock split in the last `days`, if the source knows it."""
        return None


# --------------------------------------------------------------------------- Tradier
class TradierProvider(Provider):
    """Tradier brokerage API (free real-time data with a brokerage account).

    env: TRADIER_TOKEN, optional TRADIER_SANDBOX=1 (delayed sandbox data).
    """

    name = "tradier"

    def __init__(self, as_of: D):
        super().__init__(as_of)
        import requests  # local import keeps demo mode dependency-free

        token = os.environ.get("TRADIER_TOKEN")
        if not token:
            raise RuntimeError("TRADIER_TOKEN is not set")
        sandbox = os.environ.get("TRADIER_SANDBOX") == "1"
        self.base = "https://sandbox.tradier.com/v1" if sandbox else "https://api.tradier.com/v1"
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/json"})

    def _get(self, path: str, **params):
        r = self.s.get(self.base + path, params=params, timeout=20)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _aslist(x):
        if x is None:
            return []
        return x if isinstance(x, list) else [x]

    def history(self, ticker, days=400):
        start = self.as_of - dt.timedelta(days=int(days * 1.5))
        j = self._get("/markets/history", symbol=ticker, interval="daily", start=_iso(start))
        rows = self._aslist((j.get("history") or {}).get("day"))
        return [
            {k: (r[k] if k == "date" else float(r[k] or 0)) for k in ("date", "open", "high", "low", "close", "volume")}
            for r in rows
        ]

    def expirations(self, ticker):
        j = self._get("/markets/options/expirations", symbol=ticker, includeAllRoots="true")
        return self._aslist((j.get("expirations") or {}).get("date"))

    def chain(self, ticker, exp):
        j = self._get("/markets/options/chains", symbol=ticker, expiration=exp, greeks="true")
        out = []
        for o in self._aslist((j.get("options") or {}).get("option")):
            g = o.get("greeks") or {}
            out.append(
                {
                    "symbol": o["symbol"],
                    "type": o["option_type"],
                    "strike": float(o["strike"]),
                    "exp": o["expiration_date"],
                    "bid": float(o.get("bid") or 0),
                    "ask": float(o.get("ask") or 0),
                    "last": float(o.get("last") or 0),
                    "volume": int(o.get("volume") or 0),
                    "oi": int(o.get("open_interest") or 0),
                    "iv": float(g.get("mid_iv") or g.get("smv_vol") or 0),
                    "delta": float(g.get("delta") or 0),
                }
            )
        return out


# --------------------------------------------------------------------------- yfinance
def _f(x) -> float:
    """NaN/None-safe float."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if math.isnan(x) else x


class YFinanceProvider(Provider):
    """Free, no API key. Unofficial Yahoo data: good for a personal scanner.

    Yahoo quirks handled here:
    - bid/ask often read 0 outside market hours -> run the scan during the session
      (the GitHub workflow runs ~45 min before the close);
    - its impliedVolatility is noisy -> IV is recomputed from the mid price;
    - occasional rate limits (HTTP 429), mostly from cloud IPs -> retries with backoff.
    """

    name = "yfinance"

    def __init__(self, as_of: D, pause: float = 0.4):
        super().__init__(as_of)
        import yfinance  # pip install yfinance

        self._yf = yfinance
        self._t: dict = {}
        self._px: dict = {}
        self.pause = pause

    def _retry(self, fn, *a, tries=4):
        import time

        for n in range(tries):
            try:
                out = fn(*a)
                time.sleep(self.pause)
                return out
            except Exception:  # yfinance raises assorted errors on 429/timeouts
                if n == tries - 1:
                    raise
                time.sleep(2 ** n * 3)

    def recent_split(self, ticker, days=30):
        try:
            sp = self._retry(lambda: self._tk(ticker).splits)
        except Exception:
            return None
        found = None
        for idx, ratio in (sp.items() if sp is not None else []):
            d = idx.date()
            if 0 <= (self.as_of - d).days <= days and ratio and float(ratio) != 1:
                found = (d.isoformat(), float(ratio))
        return found

    def _tk(self, ticker):
        if ticker not in self._t:
            self._t[ticker] = self._yf.Ticker(ticker)
        return self._t[ticker]

    def history(self, ticker, days=400):
        h = self._retry(lambda: self._tk(ticker).history(period="2y", auto_adjust=False))
        rows = [
            {"date": idx.date().isoformat(), "open": _f(r.Open), "high": _f(r.High),
             "low": _f(r.Low), "close": _f(r.Close), "volume": _f(r.Volume)}
            for idx, r in h.iterrows() if _f(r.Close) > 0 and idx.date() <= self.as_of
        ]
        if rows:
            self._px[ticker] = rows[-1]["close"]
        return rows[-days:]

    def expirations(self, ticker):
        return list(self._retry(lambda: self._tk(ticker).options))

    def chain(self, ticker, exp):
        oc = self._retry(lambda: self._tk(ticker).option_chain(exp))
        s = self._px.get(ticker) or self.history(ticker, 5)[-1]["close"]
        t = max((D.fromisoformat(exp) - self.as_of).days, 1) / 365
        out = []
        for kind, df in (("call", oc.calls), ("put", oc.puts)):
            if df is None:
                continue
            for r in df.itertuples():
                k, bid, ask, last = _f(r.strike), _f(r.bid), _f(r.ask), _f(r.lastPrice)
                if k <= 0:
                    continue
                px = (bid + ask) / 2 if bid > 0 and ask > 0 else 0.0
                iv = implied_vol(kind, px, s, k, t) if px > 0 else None
                if iv is None:
                    yiv = _f(r.impliedVolatility)
                    iv = yiv if 0.03 < yiv < 5 else 0.0
                out.append({
                    "symbol": r.contractSymbol, "type": kind, "strike": k, "exp": exp,
                    "bid": bid, "ask": ask, "last": last,
                    "volume": int(_f(r.volume)), "oi": int(_f(r.openInterest)),
                    "iv": round(iv, 4), "delta": round(bs_delta(kind, s, k, t, iv), 4) if iv > 0 else 0.0,
                })
        return out

    def earnings_date(self, ticker):
        try:
            cal = self._retry(lambda: self._tk(ticker).calendar, tries=2)
            ed = cal.get("Earnings Date") if isinstance(cal, dict) else None
            if ed:
                future = [d for d in ed if d >= self.as_of] or ed
                return min(future).isoformat()
        except Exception:
            pass
        return None


# --------------------------------------------------------------------------- Demo
def _seed(*parts) -> int:
    return zlib.crc32("|".join(map(str, parts)).encode())


def _bdays(end: D, n: int) -> list[D]:
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= dt.timedelta(days=1)
    return out[::-1]


class DemoProvider(Provider):
    """Deterministic synthetic market. No edge is baked in: flows are random,
    so journal results in demo mode mean nothing — it only exercises the code."""

    name = "demo"
    _cache: dict = {}

    def __init__(self, as_of: D, end: D | None = None):
        super().__init__(as_of)
        self.end = end or as_of
        self.days = _bdays(self.end + dt.timedelta(days=60), 520)  # include future for expiries
        self.idx = {d: i for i, d in enumerate(self.days)}

    def _path(self, ticker):
        key = (ticker, self.days[-1])
        if key in self._cache:
            return self._cache[key]
        rnd = random.Random(_seed("path", ticker))
        vol = 0.25 + rnd.random() * 0.55
        px = 40 + rnd.random() * 460
        closes, ivs = [], []
        drift = 0.0
        for i, _ in enumerate(self.days):
            if i % 25 == 0:
                drift = rnd.gauss(0, 0.6)
            r = drift / 252 + rnd.gauss(0, vol / math.sqrt(252))
            px *= math.exp(r)
            closes.append(px)
            ivs.append(vol * (1 + 0.25 * math.sin(i / 17 + rnd.random())) * (0.9 + 0.2 * rnd.random()))
        phase = rnd.randrange(63)
        self._cache[key] = (closes, ivs, vol, phase)
        return self._cache[key]

    def _i(self) -> int:
        d = self.as_of
        while d not in self.idx:
            d -= dt.timedelta(days=1)
        return self.idx[d]

    def history(self, ticker, days=400):
        closes, *_ = self._path(ticker)
        i = self._i()
        out = []
        for j in range(max(1, i - days + 1), i + 1):
            c, p = closes[j], closes[j - 1]
            rnd = random.Random(_seed("bar", ticker, j))
            hi = max(c, p) * (1 + rnd.random() * 0.012)
            lo = min(c, p) * (1 - rnd.random() * 0.012)
            out.append({"date": _iso(self.days[j]), "open": p, "high": hi, "low": lo, "close": c,
                        "volume": 1e6 * (1 + rnd.random())})
        return out

    def earnings_date(self, ticker):
        *_, phase = self._path(ticker)
        i = self._i()
        k = i + ((phase - i) % 63)
        return _iso(self.days[min(k, len(self.days) - 1)])

    def expirations(self, ticker):
        out, d = [], self.as_of + dt.timedelta(days=1)
        while d <= self.as_of + dt.timedelta(days=60):
            if d.weekday() == 4:
                out.append(_iso(d))
            d += dt.timedelta(days=1)
        return out

    def _flow(self, ticker, j, exp, strike, kind, s):
        """Unusual one-sided buying on random days (today's volume -> tomorrow's OI)."""
        rnd = random.Random(_seed("flow", ticker, j))
        if rnd.random() > 0.18:
            return 0
        side = "call" if rnd.random() < 0.5 else "put"
        exps = self.expirations(ticker)[:3]
        if kind != side or exp not in exps:
            return 0
        m = (strike / s - 1) * (1 if side == "call" else -1)
        if not (0.0 <= m <= 0.10):
            return 0
        return int(800 + 2500 * random.Random(_seed("fsz", ticker, j, exp, strike)).random())

    def chain(self, ticker, exp):
        closes, ivs, _, phase = self._path(ticker)
        i = self._i()
        s, base_iv = closes[i], ivs[i]
        ed = D.fromisoformat(self.earnings_date(ticker))
        e = D.fromisoformat(exp)
        if self.as_of <= ed <= e:
            base_iv *= 1.35  # earnings premium
        t = max((e - self.as_of).days, 1) / 365
        step = 1 if s < 60 else 2.5 if s < 150 else 5 if s < 400 else 10
        k0 = round(s / step) * step
        out = []
        for n in range(-12, 13):
            k = k0 + n * step
            if k <= 0:
                continue
            mny = math.log(k / s)
            iv = base_iv * (1 + 0.9 * mny * mny - 0.15 * mny)
            for kind in ("call", "put"):
                fair = bs_price(kind, s, k, t, iv)
                spr = max(0.02, fair * 0.04)
                bid = max(0.0, round(fair - spr / 2, 2))
                ask = round(fair + spr / 2, 2) if fair > 0.005 else 0.01
                sym = f"{ticker}{e:%y%m%d}{'C' if kind == 'call' else 'P'}{int(k * 1000):08d}"
                u = random.Random(_seed("oi", sym)).random()
                base = int(3000 * math.exp(-((mny / 0.12) ** 2)) * (0.4 + u)) + 20
                cum = sum(self._flow(ticker, j, exp, k, kind, closes[j]) for j in range(max(0, i - 10), i))
                vol_today = int(base * 0.08 * random.Random(_seed("v", sym, i)).random())
                vol_today += self._flow(ticker, i, exp, k, kind, s)
                out.append({"symbol": sym, "type": kind, "strike": k, "exp": exp, "bid": bid, "ask": ask,
                            "last": round(fair, 2), "volume": vol_today, "oi": base + cum,
                            "iv": round(iv, 4), "delta": round(bs_delta(kind, s, k, t, iv), 4)})
        return out


def make_provider(name: str, as_of: D, **kw) -> Provider:
    name = name.lower()
    if name == "tradier":
        return TradierProvider(as_of)
    if name in ("yfinance", "yahoo"):
        return YFinanceProvider(as_of)
    if name == "demo":
        return DemoProvider(as_of, **kw)
    raise ValueError(f"unknown provider {name}")
