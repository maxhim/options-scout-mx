"""Black-Scholes and small numeric helpers (no scipy dependency)."""
from __future__ import annotations

import math

R = 0.04  # risk-free rate used for greeks/probabilities


def ncdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _d1d2(s: float, k: float, t: float, iv: float, r: float = R):
    t = max(t, 1e-6)
    iv = max(iv, 1e-4)
    d1 = (math.log(s / k) + (r + 0.5 * iv * iv) * t) / (iv * math.sqrt(t))
    return d1, d1 - iv * math.sqrt(t)


def bs_price(kind: str, s: float, k: float, t: float, iv: float, r: float = R) -> float:
    d1, d2 = _d1d2(s, k, t, iv, r)
    if kind == "call":
        return s * ncdf(d1) - k * math.exp(-r * t) * ncdf(d2)
    return k * math.exp(-r * t) * ncdf(-d2) - s * ncdf(-d1)


def bs_delta(kind: str, s: float, k: float, t: float, iv: float, r: float = R) -> float:
    d1, _ = _d1d2(s, k, t, iv, r)
    return ncdf(d1) if kind == "call" else ncdf(d1) - 1.0


def prob_above(s: float, k: float, t: float, iv: float, r: float = R) -> float:
    """Risk-neutral probability that price ends above k at expiry."""
    _, d2 = _d1d2(s, k, t, iv, r)
    return ncdf(d2)


def clip(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def mid(bid: float | None, ask: float | None, last: float | None = None) -> float:
    bid = bid or 0.0
    ask = ask or 0.0
    if bid > 0 and ask > 0:
        return (bid + ask) / 2
    return ask or bid or (last or 0.0)


def implied_vol(kind: str, price: float, s: float, k: float, t: float, r: float = R) -> float | None:
    """Bisection IV solver; None when price is outside no-arbitrage bounds."""
    if price <= 0 or s <= 0 or k <= 0 or t <= 0:
        return None
    intrinsic = max(0.0, s - k * math.exp(-r * t)) if kind == "call" else max(0.0, k * math.exp(-r * t) - s)
    if price < intrinsic - 1e-9:
        return None
    lo, hi = 1e-3, 5.0
    if bs_price(kind, s, k, t, hi, r) < price:
        return None
    for _ in range(60):
        m = (lo + hi) / 2
        if bs_price(kind, s, k, t, m, r) > price:
            hi = m
        else:
            lo = m
    return (lo + hi) / 2


def implied_vol(kind: str, price: float, s: float, k: float, t: float, r: float = R) -> float | None:
    """Bisection IV from an option price; None when price is outside no-arbitrage bounds."""
    if price <= 0 or s <= 0 or k <= 0 or t <= 0:
        return None
    intrinsic = max(0.0, s - k) if kind == "call" else max(0.0, k - s)
    if price < intrinsic * 0.999 or price >= (s if kind == "call" else k):
        return None
    lo, hi = 0.005, 6.0
    if bs_price(kind, s, k, t, hi, r) < price:
        return None
    for _ in range(60):
        m = (lo + hi) / 2
        if bs_price(kind, s, k, t, m, r) > price:
            hi = m
        else:
            lo = m
    return (lo + hi) / 2
