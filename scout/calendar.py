"""NYSE trading sessions: holidays and early closes (pandas_market_calendars, XNYS).

Without the library, falls back to weekdays 09:30-16:00 New York (no holidays)."""
from __future__ import annotations

import datetime as dt
from functools import lru_cache
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")


@lru_cache(maxsize=64)
def session(day: dt.date) -> tuple[dt.datetime, dt.datetime] | None:
    """(open, close) in New York time, or None when the exchange is closed that day."""
    try:
        import pandas_market_calendars as mcal

        s = mcal.get_calendar("XNYS").schedule(start_date=day.isoformat(), end_date=day.isoformat())
        if s.empty:
            return None
        r = s.iloc[0]
        return r.market_open.tz_convert(NY).to_pydatetime(), r.market_close.tz_convert(NY).to_pydatetime()
    except ImportError:
        if day.weekday() >= 5:
            return None
        return (dt.datetime.combine(day, dt.time(9, 30), NY), dt.datetime.combine(day, dt.time(16, 0), NY))


def _aware(ny: dt.datetime) -> dt.datetime:
    return ny if ny.tzinfo else ny.replace(tzinfo=NY)


def in_session(ny: dt.datetime) -> bool:
    ny = _aware(ny)
    s = session(ny.date())
    return bool(s) and s[0] <= ny <= s[1]


def preclose(ny: dt.datetime, before_min: int = 60, after_min: int = 30) -> bool:
    """The last hour of the session (+30 min of slack for delayed cron runs)."""
    ny = _aware(ny)
    s = session(ny.date())
    return bool(s) and s[1] - dt.timedelta(minutes=before_min) <= ny <= s[1] + dt.timedelta(minutes=after_min)


def opening_rush(ny: dt.datetime, minutes: int = 30) -> bool:
    ny = _aware(ny)
    s = session(ny.date())
    return bool(s) and s[0] <= ny < s[0] + dt.timedelta(minutes=minutes)
