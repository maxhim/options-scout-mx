import datetime as dt
import math
from pathlib import Path

from scout import ideas, journal, pipeline, report, signals
from scout.__main__ import load_cfg
from scout.mathx import bs_delta, bs_price, prob_above
from scout.providers import DemoProvider
from scout.storage import Store

CFG = load_cfg(str(Path(__file__).resolve().parent.parent / "config.yaml"))
# keep tests fast and independent of synthetic volumes
CFG["universe"].update(tickers=CFG["universe"]["tickers"][:12], deep_scan=14, min_dollar_volume=0, min_option_oi=0)


def test_black_scholes_parity():
    s, k, t, iv = 100, 105, 0.1, 0.4
    c, p = bs_price("call", s, k, t, iv), bs_price("put", s, k, t, iv)
    assert abs((c - p) - (s - k * math.exp(-0.04 * t))) < 1e-9
    assert 0 < bs_delta("call", s, k, t, iv) < 0.5
    assert abs(prob_above(s, 1e-6, t, iv) - 1) < 1e-6


def test_signals_detect_new_oi_and_unusual():
    as_of = dt.date(2026, 11, 20)
    chain = [
        {"symbol": "X1", "type": "call", "strike": 105, "exp": "2026-11-27", "bid": 1, "ask": 1.1, "last": 1,
         "volume": 3000, "oi": 1000, "iv": 0.4, "delta": 0.3},
        {"symbol": "X2", "type": "put", "strike": 95, "exp": "2026-11-27", "bid": 1, "ask": 1.1, "last": 1,
         "volume": 10, "oi": 1000, "iv": 0.4, "delta": -0.3},
        {"symbol": "X3", "type": "call", "strike": 100, "exp": "2026-11-27", "bid": 2, "ask": 2.1, "last": 2,
         "volume": 10, "oi": 500, "iv": 0.4, "delta": 0.5},
        {"symbol": "X4", "type": "put", "strike": 100, "exp": "2026-11-27", "bid": 2, "ask": 2.1, "last": 2,
         "volume": 10, "oi": 500, "iv": 0.4, "delta": -0.5},
    ]
    prev = {"X1": {"oi": 200, "volume": 900}, "X2": {"oi": 1000, "volume": 5}}
    bars = [{"date": str(i), "open": 100, "high": 101, "low": 99, "close": 100 + i * 0.01, "volume": 1} for i in range(60)]
    m = signals.compute("X", as_of, bars, {"2026-11-27": chain}, prev, [], None, CFG)
    assert m["flow_bias"] > 0.9            # only calls gained OI
    assert m["unusual"][0]["symbol"] == "X1"
    assert m["confirmed"][0]["symbol"] == "X1"
    assert m["pcr_oi"] == 1500 / 1500


def test_option_plan_respects_limits():
    as_of = dt.date(2026, 11, 20)
    prov = DemoProvider(as_of)
    for t in ("AAPL", "NVDA", "W", "COIN"):
        bars = prov.history(t, 200)
        chains = {e: prov.chain(t, e) for e in prov.expirations(t)}
        m = signals.compute(t, as_of, bars, chains, None, [], prov.earnings_date(t), CFG)
        for side in ("bull", "bear"):
            sc = ideas.score(m, CFG) | {"side": side}
            plan, why = ideas.build_option(m, sc, chains, as_of, CFG)
            if plan:
                assert plan["cost_usd"] <= CFG["options"]["max_premium_usd"] + 1e-9
                assert plan["be_to_em"] <= CFG["options"]["max_be_to_em"] + 1e-9
                assert CFG["options"]["dte_min"] <= plan["dte"] <= CFG["options"]["dte_max"]
            else:
                assert why


def test_pipeline_and_journal(tmp_path):
    store = Store(tmp_path / "t.db")
    end = dt.date(2026, 11, 24)
    days = [end - dt.timedelta(days=i) for i in range(30) if (end - dt.timedelta(days=i)).weekday() < 5][::-1]
    brief = None
    for d in days:
        brief = pipeline.run(d, DemoProvider(d, end=end), store, CFG, log=lambda *_: None)
    assert brief["scanner"]
    assert store.closed_recs(), "journal should close some ideas over 20+ sessions"
    st = journal.stats(store.closed_recs())
    assert st["all"]["n"] == len(store.closed_recs())
    page = report.render_html(brief)
    assert page.startswith("<!DOCTYPE html>") and "демо-данные" in page
    assert report.render_text(brief)


def test_yfinance_parsing_with_fake_module(monkeypatch):
    """Yahoo is unreachable in CI sandboxes: check parsing on a fake yfinance."""
    import sys
    import types

    import pandas as pd

    from scout.mathx import bs_price
    from scout.providers import YFinanceProvider

    as_of = dt.date(2026, 11, 20)
    idx = pd.date_range(end="2026-11-23", periods=80, freq="B", tz="America/New_York")
    hist = pd.DataFrame({"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": [100 + i * 0.1 for i in range(80)],
                         "Volume": 1e6}, index=idx)
    s = float(hist[hist.index.date <= as_of]["Close"].iloc[-1])
    t = 7 / 365
    fair = bs_price("call", s, 110, t, 0.45)
    calls = pd.DataFrame([
        {"contractSymbol": "ABC261127C00110000", "strike": 110.0, "lastPrice": fair, "bid": fair - 0.02,
         "ask": fair + 0.02, "volume": float("nan"), "openInterest": 1200.0, "impliedVolatility": 0.00001},
        {"contractSymbol": "ABC261127C00105000", "strike": 105.0, "lastPrice": 1.0, "bid": 0.9, "ask": 1.1,
         "volume": 800.0, "openInterest": float("nan"), "impliedVolatility": 0.5},
    ])
    puts = pd.DataFrame(columns=calls.columns)

    class FakeTicker:
        options = ("2026-11-27",)
        calendar = {"Earnings Date": [dt.date(2026, 11, 2), dt.date(2027, 2, 3)]}

        def __init__(self, sym):
            pass

        def history(self, **kw):
            return hist

        def option_chain(self, exp):
            return types.SimpleNamespace(calls=calls, puts=puts)

    monkeypatch.setitem(sys.modules, "yfinance", types.SimpleNamespace(Ticker=FakeTicker))
    p = YFinanceProvider(as_of)
    p.pause = 0
    bars = p.history("ABC")
    assert bars[-1]["date"] == "2026-11-20"            # no look-ahead past as_of
    rows = p.chain("ABC", "2026-11-27")
    junk = next(r for r in rows if r["strike"] == 110)
    assert abs(junk["iv"] - 0.45) < 0.02               # junk IV re-solved from price
    assert junk["volume"] == 0 and 0 < junk["delta"] < 0.5
    assert next(r for r in rows if r["strike"] == 105)["oi"] == 0
    assert p.earnings_date("ABC") == "2027-02-03"


def test_stock_target_is_realistic_and_one_share():
    as_of = dt.date(2026, 11, 24)
    m = {"price": 78.0, "atr14": 9.0, "iv30": 0.9, "hv20": 0.8}
    p = ideas.build_stock(m, {"side": "bear"}, CFG, as_of)
    assert p and "shares" not in p
    assert p["target"] > 50  # ~1 sigma over 10 days, not a 50% crash
    assert abs(p["target_pct"] / p["stop_pct"] - p["rr"]) < 1e-9 and p["rr"] >= 1.5
    assert p["exit_by"] == "2026-12-08"
    assert ideas.build_stock({"price": 100, "atr14": 20, "iv30": 0.2}, {"side": "bull"}, CFG, as_of) is None


def test_telegram_html_and_alert(tmp_path):
    from scout import notify
    store = Store(tmp_path / "t.db")
    end = dt.date(2026, 11, 24)
    days = [end - dt.timedelta(days=i) for i in range(25) if (end - dt.timedelta(days=i)).weekday() < 5][::-1]
    for d in days:
        b = pipeline.run(d, DemoProvider(d, end=end), store, CFG, log=lambda *_: None)
    txt = report.render_text(b, weekly=True)
    assert "<b>" in txt and "Охота за неделю" in txt and "сила" in txt and "рынок:" in txt
    assert txt.count("<b>") == txt.count("</b>") and txt.count("<i>") == txt.count("</i>")
    long = "\n".join(["<b>x</b> " * 20] * 200)
    cut = notify._fit(long)
    assert len(cut) <= notify.LIMIT and cut.count("<b>") == cut.count("</b>")
    alert = report.render_alert(b | {"new_ideas": [], "closed_today": []}, "11:00")
    assert alert is None


def test_high_vol_stock_kept_with_warning():
    as_of = dt.date(2026, 11, 24)
    # IV prices in 70%, but the stock really moves ~150% a year with a $9.5 daily range
    m = {"price": 78.0, "atr14": 9.5, "iv30": 0.7, "hv20": 1.5}
    p = ideas.build_stock(m, {"side": "bear"}, CFG, as_of)
    assert p and p["high_vol"] and p["vol"] == 1.5
    assert p["rr"] >= 1.0 and 50 < p["target"] < 78


def test_split_garbage_is_filtered(tmp_path):
    as_of = dt.date(2026, 11, 24)

    class SplitDemo(DemoProvider):
        def chain(self, ticker, exp):
            rows = super().chain(ticker, exp)
            junk = dict(rows[0], symbol=rows[0]["symbol"] + "OLD", strike=rows[0]["strike"] * 40,
                        volume=50_000, oi=10, type="put", bid=900.0, ask=905.0, last=900.0)
            return rows + [junk]

        def recent_split(self, ticker, days=30):
            return ("2026-11-20", 8.0) if ticker == "SNDK" else None

    store = Store(tmp_path / "s.db")
    b = pipeline.run(as_of, SplitDemo(as_of, end=as_of), store, CFG, log=lambda *_: None)
    for r in b["scanner"]:
        assert all(u["strike"] < 5 * r["m"]["price"] for u in r["m"]["unusual"])
    sndk = next(r for r in b["scanner"] if r["ticker"] == "SNDK")
    assert sndk["m"]["split"] and any("Сплит 8:1" in x for x in sndk["s"]["reasons"])


def test_atr_ignores_one_broken_bar():
    bars = [{"open": 100, "high": 101, "low": 99, "close": 100} for _ in range(30)]
    bars[-3] = {"open": 100, "high": 800, "low": 99, "close": 100}  # unadjusted split bar
    assert signals.price_stats(bars)["atr14"] < 3


def test_market_tab_and_page_tabs(tmp_path):
    from scout import market
    as_of = dt.date(2026, 11, 24)
    b = pipeline.run(as_of, DemoProvider(as_of, end=as_of), Store(tmp_path / "m.db"), CFG, log=lambda *_: None)
    mac = b["macro"]
    assert mac["regime"]["label"] and mac["events"] and all(e["imp"] in ("high", "medium") for e in mac["events"])
    assert market.importance("Core PCE Price Index m/m") == "high"
    page = report.render_html(b)
    for t in ('data-t=\'opt\'', 'data-t=\'stk\'', 'data-t=\'mkt\'', 'data-t=\'jr\''):
        assert t in page
    assert page.count('class="srow"') <= 10


def test_universe_filters_and_shortlist(tmp_path):
    import copy
    as_of = dt.date(2026, 11, 24)
    cfg = copy.deepcopy(CFG)
    cfg["universe"].update(min_price=200, deep_scan=6)
    b = pipeline.run(as_of, DemoProvider(as_of, end=as_of), Store(tmp_path / "u.db"), cfg, log=lambda *_: None)
    u = b["universe"]
    assert u["checked"] >= u["passed"] and u["dropped"] > 0
    for r in b["scanner"]:
        if not r.get("watch"):
            assert r["m"]["price"] >= 200
    assert len([r for r in b["scanner"] if not r.get("watch")]) <= 6


def test_universe_refresh_rewrites_config_safely(tmp_path):
    import shutil

    import pytest

    from scout import universe
    cfg_path = tmp_path / "config.yaml"
    shutil.copy(Path(__file__).resolve().parent.parent / "config.yaml", cfg_path)
    current = load_cfg(str(cfg_path))["universe"]["tickers"]
    # fake screener: 300 names; current names rank 151-260 (outside TARGET, inside KEEP_RANK for most)
    fake = [{"symbol": f"N{i:03d}", "quoteType": "EQUITY", "regularMarketPrice": 100, "averageDailyVolume3Month": 10_000_000 - i}
            for i in range(150)]
    fake += [{"symbol": t, "quoteType": "EQUITY", "regularMarketPrice": 100, "averageDailyVolume3Month": 1_000_000 - i}
             for i, t in enumerate(current)]
    fake += [{"symbol": "SPYX", "quoteType": "ETF", "regularMarketPrice": 500, "averageDailyVolume3Month": 9e9}]
    diff = universe.refresh(cfg_path, current, screen=lambda: fake)
    cfg2 = load_cfg(str(cfg_path))
    new = cfg2["universe"]["tickers"]
    assert len(new) == universe.TARGET and "SPYX" not in new
    assert cfg2["watchlist"] and cfg2["options"]["max_premium_usd"] == 100  # rest of the file intact
    assert set(diff["removed"]) == set(current) - set(new)
    kept = [t for t in current if t in new]
    assert kept == current[:len(kept)]  # incumbents inside KEEP_RANK stay
    with pytest.raises(RuntimeError):
        universe.refresh(cfg_path, new, screen=lambda: fake[:10])
    assert load_cfg(str(cfg_path))["universe"]["tickers"] == new


def _brief(tmp_path):
    as_of = dt.date(2026, 11, 24)
    return pipeline.run(as_of, DemoProvider(as_of, end=as_of), Store(tmp_path / "p.db"), CFG, log=lambda *_: None)


def test_page_script_is_valid_js_in_both_languages(tmp_path):
    import re
    import shutil
    import subprocess

    import pytest
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    b = _brief(tmp_path)
    for lang in ("ru", "en"):
        page = report.render_html(b, lang)
        js = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
        f = tmp_path / f"page_{lang}.js"
        f.write_text(js)
        res = subprocess.run([node, "--check", str(f)], capture_output=True, text=True)
        assert res.returncode == 0, res.stderr


def test_english_page_and_texts(tmp_path):
    import re
    b = _brief(tmp_path)
    page = report.render_html(b, "en")
    assert 'lang="en"' in page and "Track record" in page and "t.me/" in page and "?start=en" in page
    visible = re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", "", page, flags=re.S))
    assert not re.search(r"[А-Яа-яЁё]{4,}", visible), re.findall(r"[А-Яа-яЁё]{4,}", visible)[:5]
    txt = report.render_text(b, lang="en")
    assert not re.search(r"[А-Яа-яЁё]{4,}", re.sub(r"<[^>]+>", "", txt))
    ru = report.render_html(b, "ru")
    assert "Вижу" not in ru and "сокол видит" not in ru and "?start=ru" in ru


def test_subscribers_sync_and_encryption(tmp_path):
    from scout import subscribers as S
    tok = "123:abc"
    upd = [
        {"update_id": 10, "message": {"chat": {"id": 1, "type": "private"}, "from": {"language_code": "ru"}, "text": "/start"}},
        {"update_id": 11, "message": {"chat": {"id": 2, "type": "private"}, "from": {"language_code": "ru"}, "text": "/start en"}},
        {"update_id": 12, "message": {"chat": {"id": -5, "type": "group"}, "text": "/start"}},
        {"update_id": 13, "message": {"chat": {"id": 3, "type": "private"}, "from": {"language_code": "de"}, "text": "/start"}},
        {"update_id": 14, "message": {"chat": {"id": 3, "type": "private"}, "text": "/stop"}},
    ]
    sent = []
    data = {"offset": 0, "subs": {}}
    S.sync(tok, data, lambda c, t_: sent.append((c, t_)), lambda off: [u for u in upd if u["update_id"] >= off])
    assert data["subs"] == {"1": {"lang": "ru", "since": data["subs"]["1"]["since"]},
                            "2": {"lang": "en", "since": data["subs"]["2"]["since"]}}
    assert data["offset"] == 15 and len(sent) == 4
    path = tmp_path / "subscribers.enc"
    S.save(path, tok, data)
    assert b"subs" not in path.read_bytes()          # nothing readable in the public repo
    assert S.load(path, tok) == data
    rec = S.recipients(data, "999")
    assert rec == {"1": "ru", "2": "en", "999": "ru"}


def test_same_data_gives_same_brief(tmp_path):
    as_of = dt.date(2026, 11, 24)
    picks = []
    for i in range(2):
        b = pipeline.run(as_of, DemoProvider(as_of, end=as_of), Store(tmp_path / f"d{i}.db"), CFG, log=lambda *_: None)
        picks.append(([r["ticker"] for r in b["options"]], [r["ticker"] for r in b["stocks"]], [r["ticker"] for r in b["scanner"]]))
    assert picks[0] == picks[1]


def test_sector_cap_and_labels(tmp_path):
    import copy
    from scout import sectors
    rows = [{"ticker": t, "sector": sectors.group(t)} for t in ["MRVL", "WDC", "LRCX", "TSM", "AMAT", "GEV", "JPM"]]
    picked = sectors.cap(rows, 2, {})
    assert [r["ticker"] for r in picked] == ["MRVL", "WDC", "LRCX", "GEV", "JPM"]  # TSM, AMAT: third chip name
    cfg = copy.deepcopy(CFG)
    cfg["output"].update(min_score=0, max_per_sector=1)
    as_of = dt.date(2026, 11, 24)
    b = pipeline.run(as_of, DemoProvider(as_of, end=as_of), Store(tmp_path / "s.db"), cfg, log=lambda *_: None)
    secs = [r["sector"] for r in b["options"] + b["stocks"]]
    assert len(secs) == len(set(secs))
    txt = report.render_text(b)
    assert any(sectors.label(s_) in txt for s_ in secs if not s_.startswith("solo"))
