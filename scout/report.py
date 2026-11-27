"""Daily brief rendering: self-contained HTML page (RU and EN) + short Telegram texts."""
from __future__ import annotations

import datetime as _dt
import html
from urllib.parse import quote

from . import sectors
from .ideas import NAMES, TIER_LABEL

E = html.escape
_LANG = "ru"


def t(ru: str, en: str) -> str:
    return en if _LANG == "en" else ru


def _set(lang):
    global _LANG
    _LANG = "en" if lang == "en" else "ru"


NAMES_EN = {"trend": "trend", "flow": "new OI", "unusual": "unusual volume", "confirmed": "confirmed flow"}
EXIT_EN = {"тейк": "take-profit", "стоп": "stop", "экспирация": "expiry", "выход по времени": "time exit"}
RU_DAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
RU_MON = ["", "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
EN_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
EN_MON = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def _side(side):
    return t("рост", "long") if side == "bull" else t("падение", "short")


def _p(x, d=1):
    return "—" if x is None else f"{x * 100:.{d}f}%"


def _n(x, d=2):
    return "—" if x is None else f"{x:,.{d}f}"


def _usd(x):
    if x is None:
        return "—"
    return f"${x / 1e6:.1f}M" if abs(x) >= 1e6 else f"${x / 1e3:.0f}K" if abs(x) >= 1e3 else f"${x:,.0f}"


def _exp(e):
    """Short date: 27.11 in Russian, 11/27 in English."""
    return f"{e[5:7]}/{e[8:10]}" if _LANG == "en" else f"{e[8:10]}.{e[5:7]}"


_date = _exp


def _pct(x, d=1, sign=True):
    if x is None:
        return "—"
    return (f"{x * 100:+.{d}f}%" if sign else f"{x * 100:.{d}f}%").replace("-", "−")


def _long_day(iso):
    d = _dt.date.fromisoformat(iso)
    if _LANG == "en":
        return f"{EN_DAYS[d.weekday()]}, {EN_MON[d.month]} {d.day}"
    return f"{RU_DAYS[d.weekday()]}, {d.day} {RU_MON[d.month]}"


def _plural(n, one, few, many):
    n = abs(n) % 100
    if 11 <= n <= 14:
        return many
    return one if n % 10 == 1 else few if 2 <= n % 10 <= 4 else many


def _targets(n):
    if _LANG == "en":
        return f"{n} target{'s' if n != 1 else ''}"
    return f"{n} {_plural(n, 'цель', 'цели', 'целей')}"


def _sec(r):
    return sectors.label(r.get("sector", ""), _LANG)


def _why(r):
    return r.get("why_en" if _LANG == "en" else "why", "") or r.get("why", "")


def _reasons(s):
    return s.get("reasons_en") if _LANG == "en" and s.get("reasons_en") else s["reasons"]


def _right(p):
    return t("колл", "call") if p["right"] == "call" else t("пут", "put")


def structure(p: dict, ticker: str) -> str:
    r = _right(p)
    if p["type"] == "spread":
        return f"{ticker} {r}{t('-спред', ' spread')} {p['strike']:g}/{p['short_strike']:g}, {t('экспирация', 'exp.')} {_exp(p['exp'])}"
    return f"{ticker} {r} {p['strike']:g}, {t('экспирация', 'exp.')} {_exp(p['exp'])}"


def idea_label(rec: dict) -> str:
    p, tk = rec["plan"], rec["ticker"]
    if p["type"] == "stock":
        act = t("Покупка", "Long") if p["side"] == "bull" else t("Шорт", "Short")
        return f"{act} {tk} {t('от', 'at')} ${p['entry']:,.2f}"
    return f"{structure(p, tk)} {t('за', 'at')} ${p['entry']:.2f}"


def _exit_reason(x):
    return EXIT_EN.get(x, x) if _LANG == "en" else x


def _since_note(since, as_of):
    if not since:
        return ""
    if since == as_of:
        return t("повтор: идея из дневного алерта", "repeat: from today's intraday alert")
    return t(f"повтор: идея открыта {_date(since)}", f"repeat: opened {_date(since)}")


def _be(p):
    """Move needed to break even, signed in the direction of the trade (puts need a fall)."""
    return p["req_move_pct"] * (1 if p["right"] == "call" else -1)


def _mode(r):
    m = r.get("mode") or (r.get("option") or {}).get("mode")
    return {"short": t("до 2 нед.", "≤2 wks"), "long": t("2–5 нед.", "2–5 wks")}.get(m, "")


def _tier(r):
    k = r.get("tier") or (r.get("option") or {}).get("tier")
    if k == "rebound":
        lab = t("на отскок · эксперимент", "snap-back · experimental")
    else:
        lab = TIER_LABEL.get(k)
        lab = (lab[1] if _LANG == "en" else lab[0]) if lab else ""
    md = _mode(r)
    return f"{lab} · {md}" if lab and md else lab or md


def _panic_note(b, html=True):
    pn = b.get("panic") or {}
    if not pn.get("panic"):
        return ""
    bits = []
    if pn.get("vix") is not None:
        bits.append(f"VIX {pn['vix']:.1f}")
    if pn.get("dd") is not None:
        dd = f"{pn['dd'] * 100:+.1f}%".replace("-", "−")
        bits.append(t(f"S&P {dd} от максимума за 3 мес.", f"S&P {dd} from its 3-month high"))
    dropped = b.get("dropped_bear") or []
    off = ", ".join(dropped[:5]) + (t(f" и ещё {len(dropped) - 5}", f" and {len(dropped) - 5} more") if len(dropped) > 5 else "")
    txt = t(f"Режим паники ({', '.join(bits)}): медвежьи идеи по тренду отключены — в панике рынок отскакивает и шорты по тренду исторически проигрывают."
            + (f" Отсеяны: {off}." if off else ""),
            f"Panic regime ({', '.join(bits)}): bearish trend ideas are off — in a panic the market rebounds and trend shorts have lost historically."
            + (f" Dropped: {off}." if off else ""))
    return f"<p class='note panic'>⚠️ {E(txt)}</p>" if html else f"⚠️ <i>{E(txt)}</i>"


def _option_card(r, as_of):
    p, s, m = r["option"], r["s"], r["m"]
    em_w = min(100, p["em_pct"] / max(p["em_pct"], p["req_move_pct"], 1e-9) * 100)
    be_w = min(100, max(0, p["req_move_pct"]) / max(p["em_pct"], p["req_move_pct"], 1e-9) * 100)
    r_ = _right(p)
    what = (t(f"Купить {r_}-спред", f"Buy {r_} spread") + f" {p['strike']:g}/{p['short_strike']:g}" if p["type"] == "spread"
            else t(f"Купить {r_}", f"Buy {r_}") + f" {p['strike']:g}")
    extra = (f"<div><dt>{t('Макс. прибыль', 'Max profit')}</dt><dd>${p['max_profit_usd']:,.0f}</dd></div>" if p["type"] == "spread" else "")
    if p.get("payoff_em") is not None:
        extra += f"<div><dt>{t('При ожидаемом движении', 'On the expected move')}</dt><dd>+{p['payoff_em'] * 100:.0f}%</dd></div>"
    reasons = "".join(f"<li>{E(x)}</li>" for x in _reasons(s))
    since = _since_note(r.get("option_open_since"), as_of)
    return f"""<article class="card">
<header><h3>{E(r['ticker'])}</h3><span class="tag {s['side']}">{_side(s['side'])}</span>{f'<span class="sec">{E(_sec(r))}</span>' if _sec(r) else ''}
<span class="score">{t('сила', 'strength')} <b>{r['option_score']:.0f}</b></span></header>
{f'<p class="tier">{E(_tier(r))}</p>' if _tier(r) else ''}<p class="why1">{E(_why(r))}</p>
<p class="trade">{E(what)}, {t('экспирация', 'expires')} {_exp(p['exp'])}</p>
<p class="cost">${p['entry']:.2f} {t('за опцион', 'per option')}, ${p['cost_usd']:,.0f} {t('за контракт. Это максимальный убыток.', 'per contract. That is the maximum loss.')}{(' · ' + E(since)) if since else ''}</p>
<div class="move"><div class="lbl">{t('Нужно до безубытка', 'Move to break even')} <b>{_pct(_be(p))}</b> · {t('ожидаемое движение', 'expected move')} <b>±{_pct(p['em_pct'], sign=False)}</b></div>
<div class="bar"><i class="em" style="width:{em_w:.0f}%"></i><i class="be" style="left:{be_w:.0f}%"></i></div></div>
<dl class="kv">
<div><dt>{t('Цена акции', 'Stock price')}</dt><dd>${m['price']:,.2f}</dd></div>
<div><dt>{t('Безубыток', 'Break-even')}</dt><dd>${p['breakeven']:,.2f}</dd></div>
<div><dt>{t('Тейк', 'Take-profit')}</dt><dd>${p['target']:.2f} (+{(p['target'] / p['entry'] - 1) * 100:.0f}%)</dd></div>
<div><dt>{t('Стоп', 'Stop')}</dt><dd>${p['stop']:.2f} (−{(1 - p['stop'] / p['entry']) * 100:.0f}%)</dd></div>
<div><dt>{t('Вероятность прибыли', 'Chance of profit')}</dt><dd>{_pct(p['pop'], 0, sign=False)}</dd></div>
<div><dt>{t('Выход', 'Exit')}</dt><dd>{t('до', 'by')} {_exp(p['exp'])}</dd></div>{extra}
</dl>
<details><summary>{t('Все сигналы', 'All signals')}</summary><ul class="why">{reasons}</ul></details>
</article>"""


def _stock_card(r, as_of):
    p, s = r["stock"], r["s"]
    bull = s["side"] == "bull"
    reasons = "".join(f"<li>{E(x)}</li>" for x in _reasons(s))
    since = _since_note(r.get("stock_open_since"), as_of)
    warn = t(f"⚠ Высокая волатильность ({p['vol'] * 100:.0f}% годовых): цель и стоп шире обычного, цена может пройти стоп за один день. Риск точнее ограничить опционом.",
             f"⚠ High volatility ({p['vol'] * 100:.0f}% a year): target and stop are wider than usual and price can gap through the stop in one day. An option caps the risk more precisely.")
    return f"""<article class="card">
<header><h3>{E(r['ticker'])}</h3><span class="tag {s['side']}">{_side(s['side'])}</span>{f'<span class="sec">{E(_sec(r))}</span>' if _sec(r) else ''}
<span class="score">{t('сила', 'strength')} <b>{s['stock_score']:.0f}</b></span></header>
<p class="why1">{E(_why(r))}</p>
<p class="trade">{t('Покупка', 'Long') if bull else t('Шорт', 'Short')} {t('от', 'at')} ${p['entry']:,.2f}</p>
<p class="cost">{t('Держать до', 'Hold until')} {_date(p['exit_by'])}{(' · ' + E(since)) if since else ''}</p>
<dl class="kv">
<div><dt>{t('Цель', 'Target')}</dt><dd class="up">${p['target']:,.2f} ({_pct(p['target_pct'] * (1 if bull else -1))})</dd></div>
<div><dt>{t('Стоп', 'Stop')}</dt><dd class="dn">${p['stop']:,.2f} ({_pct(p['stop_pct'] * (-1 if bull else 1))})</dd></div>
<div><dt>{t('Потенциал : риск', 'Reward : risk')}</dt><dd>{p['rr']:.1f} : 1</dd></div>
<div><dt>{t('Ожид. движение', 'Expected move')}</dt><dd>±{_pct(p['target_pct'], sign=False)} {t('за', 'in')} {p['max_hold_days']} {t('дн.', 'days')}</dd></div>
</dl>
{f'<p class="warn">{E(warn)}</p>' if p.get('high_vol') else ''}
<details><summary>{t('Все сигналы', 'All signals')}</summary><ul class="why">{reasons}</ul></details>
</article>"""


def _scan_item(r):
    """One row of the top list: compact summary, details on tap."""
    m, s = r["m"], r["s"]
    ch = m["price"] / m["prev_close"] - 1 if m.get("prev_close") else None
    em = next(iter(m["em"].values()), None) if m.get("em") else None
    v = max(r.get("option_score", 0), s["stock_score"])
    side = "bull" if s["direction"] >= 0 else "bear"
    earn = (f"{_exp(m['earnings'])}, {t('через', 'in')} {m['earnings_days']} {t('дн.', 'd')}"
            if m.get("earnings") and m["earnings_days"] is not None and m["earnings_days"] >= 0 else "—")
    flow = f"{_usd(m['new_call_prem'])} / {_usd(m['new_put_prem'])}" if m["has_prev"] else t("нет вчерашних данных", "no data from yesterday")
    reasons = "".join(f"<li>{E(x)}</li>" for x in _reasons(s))
    return f"""<details class="srow"><summary>
<b class="tk">{E(r['ticker'])}{'<small>★</small>' if r.get('watch') else ''}</b><span class="arr {side}">{'▲' if side == 'bull' else '▼'}</span>
<span class="sbar"><i class="{side}" style="width:{v:.0f}%"></i></span><b class="sv">{v:.0f}</b>
<span class="num px">${m['price']:,.2f}</span><span class="num chg {'up' if (ch or 0) >= 0 else 'dn'}">{'—' if ch is None else _pct(ch)}</span>
</summary><div class="sdet"><p class="why1">{E(_sec(r) + ' · ' if _sec(r) else '')}{E(_why(r))}</p><dl class="kv3">
<div><dt>IV30</dt><dd>{_p(m['iv30'], 0)}</dd></div><div><dt>IV Rank</dt><dd>{_n(m['iv_rank'], 0) if m['iv_rank'] is not None else '—'}</dd></div>
<div><dt>IV/HV</dt><dd>{_n(m['iv_hv'])}</dd></div><div><dt>{t('Ожид. движение', 'Expected move')}</dt><dd>{_p(em)}</dd></div>
<div><dt>{t('Put/Call по OI', 'Put/Call OI')}</dt><dd>{_n(m['pcr_oi'])}</dd></div><div><dt>{t('Новый OI колы / путы', 'New OI calls / puts')}</dt><dd>{flow}</dd></div>
<div><dt>{t('Необычный объём', 'Unusual volume')}</dt><dd>{_usd(m['unusual_premium'])}</dd></div><div><dt>{t('Стены OI путы / колы', 'OI walls puts / calls')}</dt><dd>{_n(m['put_wall'], 1)} / {_n(m['call_wall'], 1)}</dd></div>
<div><dt>{t('Отчёт', 'Earnings')}</dt><dd>{earn}</dd></div></dl><ul class="why">{reasons}</ul></div></details>"""


def _open_row(rec):
    p, chg = rec["plan"], rec.get("pnl")
    cls = "" if chg is None else ("up" if chg >= 0 else "dn")
    return (f"<tr><td>{_date(rec['as_of'])}</td><td>{E(idea_label(rec))}</td>"
            f"<td class='num'>{_n(rec.get('current'))}</td><td class='num {cls}'>{_pct(chg)}</td>"
            f"<td class='nw'>{t('до', 'by')} {_date(p.get('exit_by') or p.get('exp') or rec['as_of'])}</td></tr>")


def _closed_row(rec):
    r = rec["result_r"]
    return (f"<tr><td class='nw'>{_date(rec['as_of'])} → {_date(rec['exit_date'])}</td><td>{E(idea_label(rec))}</td>"
            f"<td class='num'>{_n(rec['exit_price'])}</td><td>{E(_exit_reason(rec['exit_reason']))}</td>"
            f"<td class='num {'up' if r > 0 else 'dn'}'>{_pct(r)}</td></tr>")


LOGO = ('<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" fill="#161b22"/>'
        '<path d="M12 56C10 36 17 20 32 16C42 13.5 51 17 55 25L56 27C58 28 58 31 56 32L51.5 33C50 38 46.5 41 42 42C41.5 47 41 51 41 56Z" fill="#f7f1e6"/>'
        '<path d="M12 44C11 31 18 19 32 16C41 14 49 16.5 53.5 22.5C49 20 43 19.5 38.5 21C34 22.5 31 26 30 31C27 37 20 41 12.6 44Z" fill="#5b7088"/>'
        '<path d="M36.5 34C36 37.5 37 40 39 41.5C40.6 39.5 40.6 36.5 39.6 34Z" fill="#5b7088" opacity=".55"/>'
        '<circle cx="42" cy="27.5" r="4.6" fill="#f2a93b"/><circle cx="42.4" cy="27.8" r="3" fill="#161b22"/>'
        '<circle cx="43.6" cy="26.4" r="1.15" fill="#fff"/>'
        '<path d="M50.5 24C55.5 23.3 60.3 25.8 60.6 30.2C60.8 33.3 59 35.6 56.6 35.4C57.4 33.8 57 32.6 55.4 32.6L50.6 32.8Z" fill="#f2a93b"/>'
        '<path d="M50.8 32.6C52.6 33.8 54.6 34 56 33.4" stroke="#c9821f" stroke-width="1" fill="none" stroke-linecap="round"/></svg>')

BIRD = ('<svg viewBox="26 0 60 70" aria-hidden="true"><g fill="currentColor">'
        '<path d="M43 32.5L27 30.5L27 39.5L43 37.5Z"/>'
        '<path d="M38 35C45 30 62 29.5 72 31.5C76 32.3 79 33.6 80.5 35C79 36.4 76 37.7 72 38.5C62 40.5 45 40 38 35Z"/>'
        '<path class="w w1" d="M68 32C70 22 64 10 50 2C55 12 55 22 52 32Z"/>'
        '<path class="w w2" d="M68 38C70 48 64 60 50 68C55 58 55 48 52 38Z"/></g>'
        '<path d="M80 34L84 35L80 36.2Z" fill="#f2a93b"/></svg>')



TG_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M21.5 4.3 2.9 11.5c-1.3.5-1.3 1.3-.2 1.6l4.8 1.5 1.8 5.6c.2.6.4.8.9.8.4 0 .6-.2.9-.4l2.3-2.2 4.7 3.5c.9.5 1.5.2 1.7-.8l3.1-14.6c.3-1.3-.5-1.9-1.4-1.6ZM8.6 14.3l9.2-5.8c.4-.3.8-.1.5.2l-7.6 6.9-.3 3.2-1.8-4.5Z"/></svg>')

CSS = """
:root{color-scheme:dark;--bg:#0b1020;--card:#121a2e;--card2:#172139;--line:#222c45;--ink:#e8ecf4;--mut:#8b95ad;
--y:#f5a524;--acc:#7c8cff;--up:#34d399;--dn:#f87171}
*{box-sizing:border-box;min-width:0}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 Manrope,system-ui,sans-serif;overflow-x:clip}
.wrap{max-width:1100px;margin:0 auto;padding:clamp(14px,3vw,36px) max(4vw,14px) 40px}
h1,h2,.brand b,.kpi b,.big{font-family:Unbounded,Manrope,system-ui,sans-serif;font-weight:600;letter-spacing:-.01em}
h1{font-size:clamp(28px,4.4vw,44px);line-height:1.1;margin:0;text-wrap:balance}h2{font-size:20px;margin:0 0 4px}h3{font-size:20px;margin:0}
a{color:var(--acc)}
.top{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:10px;margin-right:auto}.brand svg{width:38px;height:38px;flex:none;border-radius:10px}.brand b{font-size:18px}
.lang{color:var(--mut);font-size:14px;font-weight:600;text-decoration:none;padding:6px 10px;border:1px solid var(--line);border-radius:999px}
.sub-btn{display:inline-flex;align-items:center;gap:8px;background:var(--y);color:#141006;font-weight:700;font-size:14px;text-decoration:none;
 padding:8px 14px;border-radius:999px;white-space:nowrap}.sub-btn svg{width:18px;height:18px}
.sub-btn:hover{filter:brightness(1.08)}.sub-btn .sm{display:none}
.hero{position:relative;height:160px;margin:16px 0 10px;border-radius:16px;overflow:hidden;border:1px solid var(--line);
 background:radial-gradient(120% 140% at 85% 0%,#25306b 0%,#151d3a 45%,#0f1630 100%)}
.hero h1{position:absolute;left:20px;bottom:16px;max-width:70%;z-index:1}.hero .sub2{position:absolute;left:20px;top:14px;margin:0;color:var(--mut);font-size:14px;z-index:1}
.hero .ridge{position:absolute;left:0;bottom:0;width:100%;height:40px;opacity:.6}
.falcon{position:absolute;left:0;top:0;width:64px;height:64px;color:#e8ecf4;cursor:pointer;z-index:2;will-change:transform;transform:translate(70%,30px)}
.falcon svg{width:100%;height:100%;display:block}
.falcon .w{transform-box:fill-box;animation:flap 1.1s ease-in-out infinite}.falcon .w1{transform-origin:50% 100%}.falcon .w2{transform-origin:50% 0}
@keyframes flap{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.55)}}
.say{position:absolute;right:14px;top:12px;max-width:min(60%,320px);background:var(--card2);border:1px solid var(--line);border-radius:12px;padding:8px 12px;font-size:14px;
 opacity:0;transform:translateY(-6px);transition:.25s;z-index:3;pointer-events:none}.say.on{opacity:1;transform:none}
.badge{display:inline-block;background:var(--y);color:#141006;padding:1px 8px;border-radius:4px;font-size:12px;font-weight:700;margin-left:6px}
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}.kpi small{display:block;color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.05em}
.kpi b{display:block;font-size:22px;line-height:1.3}.kpi span{font-size:13px;color:var(--mut)}
.kpi.reg-stress b,.kpi.reg-nervous b{color:var(--dn)}.kpi.reg-calm_up b{color:var(--up)}
.tabs{display:flex;gap:4px;margin:22px 0 0;border-bottom:1px solid var(--line);overflow-x:auto;scrollbar-width:none;position:sticky;top:0;background:var(--bg);z-index:5}
.tabs button{font:inherit;font-weight:600;font-size:15px;color:var(--mut);background:none;border:0;border-bottom:3px solid transparent;padding:12px 12px 10px;cursor:pointer;white-space:nowrap}
.tabs button[aria-selected=true]{color:var(--ink);border-color:var(--y)}.tabs button i{font-style:normal;font-size:12px;background:var(--card2);border-radius:9px;padding:0 6px;margin-left:4px}
.pane{padding-top:18px}.pane[hidden]{display:none}
.sub{color:var(--mut);margin:0;font-size:14px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,330px),1fr));gap:14px;margin-top:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}
.card header{display:flex;align-items:center;gap:8px}.score{margin-left:auto;color:var(--mut);font-size:14px}.score b{font-size:20px;color:var(--ink)}
.tag{font-size:12px;font-weight:700;padding:2px 8px;border-radius:4px;white-space:nowrap}.tag.bull{background:rgba(52,211,153,.15);color:var(--up)}.tag.bear{background:rgba(248,113,113,.15);color:var(--dn)}
.tier{display:inline-block;margin:8px 0 0;font-size:12px;font-weight:700;color:var(--y);border:1px solid rgba(245,165,36,.4);border-radius:999px;padding:1px 9px}
.sum{margin:10px 0 0;font-size:15px}.sum b{white-space:nowrap}.sum .dn,.sum .up{font-weight:700}.news{margin:10px 0 0;padding-left:18px;font-size:14px}.news li{margin:3px 0}.news small{color:var(--mut)}
.sec{font-size:12px;color:var(--mut);border:1px solid var(--line);border-radius:4px;padding:1px 7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.trade{font-weight:700;font-size:17px;margin:10px 0 2px}.cost{color:var(--mut);margin:0 0 10px;font-size:14px}
.move .lbl{font-size:14px}.bar{position:relative;height:8px;border-radius:4px;background:var(--line);margin:6px 0 12px}
.bar .em{position:absolute;inset:0 auto 0 0;background:rgba(124,140,255,.55);border-radius:4px}
.bar .be{position:absolute;top:-4px;width:3px;height:16px;background:var(--y);transform:translateX(-1px)}
.kv{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px 14px;margin:0}.kv dt,.kv3 dt{font-size:12px;color:var(--mut)}.kv dd,.kv3 dd{margin:0;font-weight:700}
.kv3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px 14px;margin:8px 0}
.why{margin:8px 0 0;padding-left:18px;font-size:14px}.why1{margin:6px 0 0;font-size:14px;color:var(--mut)}
details>summary{cursor:pointer}details.more{margin-top:10px;font-size:14px}details.more summary{color:var(--mut)}
.warn{font-size:13px;margin:10px 0 0;padding:8px 10px;border-radius:8px;background:rgba(245,165,36,.12);color:#f6c56b}
.srow{border-bottom:1px solid var(--line)}.srow summary,.shead{display:grid;grid-template-columns:4.2em 1.2em minmax(40px,1fr) 2em 5.6em 4.4em;gap:8px;align-items:center;padding:10px 2px;list-style:none}
.shead{margin-top:10px;padding-block:6px;border-bottom:1px solid var(--line);font-size:12px;color:var(--mut);font-weight:600}.shead span:nth-child(3){grid-column:3/5}.shead span:nth-child(4){display:none}
.srow summary::-webkit-details-marker{display:none}.srow[open] summary{background:var(--card)}.sdet{padding:4px 2px 14px}
.arr.bull{color:var(--up)}.arr.bear{color:var(--dn)}.sbar{height:8px;background:var(--line);border-radius:4px;overflow:hidden}
.sbar i{display:block;height:100%;transform-origin:left;animation:grow .9s cubic-bezier(.2,.7,.2,1) both}.sbar i.bull{background:var(--up)}.sbar i.bear{background:var(--dn)}.sv{text-align:right}
@keyframes grow{from{transform:scaleX(0)}}
.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}.px,.chg{font-size:14px}
.up{color:var(--up)}.dn{color:var(--dn)}.nw{white-space:nowrap}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:12px;color:var(--mut);font-weight:600;white-space:nowrap}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:24px}
.slab{background:linear-gradient(135deg,#2a3577,#1a2350);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:18px}.slab .big{font-size:34px;line-height:1}.slab p{margin:4px 0 0;color:#c9d0e3}
.reg{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:18px}.reg h3{font-size:22px}.reg p{margin:6px 0 0}
.idx{display:flex;gap:18px;flex-wrap:wrap;margin-top:10px;font-size:14px}
.day{margin:16px 0 4px;font-size:13px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em;font-weight:700}
.ev{display:grid;grid-template-columns:3.4em 5.2em minmax(0,1fr) auto;gap:10px;align-items:baseline;padding:8px 0;border-bottom:1px solid var(--line);font-size:14px}
.imp{font-size:11px;font-weight:700;padding:1px 6px;border-radius:4px;text-align:center}.imp.high{background:rgba(248,113,113,.15);color:var(--dn)}
.imp.medium{background:rgba(245,165,36,.15);color:var(--y)}.ev small{color:var(--mut)}
.join{display:flex;align-items:center;gap:14px;flex-wrap:wrap;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin-top:28px}
.join p{margin:0;flex:1 1 260px;color:var(--mut);font-size:14px}.join b{color:var(--ink)}
.empty{color:var(--mut);padding:10px 0}.note{font-size:13px;color:var(--mut)}.note.panic{color:#f5c56b;border:1px solid rgba(245,197,107,.35);border-radius:10px;padding:10px 12px;margin:0 0 14px}.avoid{padding-left:18px}.avoid li{margin:4px 0}
.legend p{margin:8px 0}.legend b{display:block}
@media (prefers-reduced-motion:reduce){.falcon .w,.sbar i{animation:none}}
@media(max-width:760px){.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.two{grid-template-columns:minmax(0,1fr)}.kv3{grid-template-columns:repeat(2,minmax(0,1fr))}
.ev{grid-template-columns:3.2em minmax(0,1fr) auto}.ev .ny{display:none}}
@media(max-width:600px){.falcon{width:50px;height:50px}.hero{height:150px}.hero h1{max-width:92%;font-size:28px}.sub-btn .lg{display:none}.sub-btn .sm{display:inline}.sub-btn{padding:8px 12px}
.stack thead{display:none}.stack tr{display:grid;padding-block:8px}
.stack td{display:flow-root;border:0;padding:2px 0;padding-inline-start:7em;text-align:start}
.stack td::before{content:attr(data-l);float:inline-start;width:6.5em;margin-inline-start:-7em;color:var(--mut)}.stack td:empty{display:none}}
"""

# Tabs first: nothing in the falcon code below can ever break navigation.
JS = """{
const tabs=[...document.querySelectorAll('.tabs button')];
const show=id=>{for(const b of tabs){const on=b.dataset.t===id;b.setAttribute('aria-selected',on);document.getElementById(b.dataset.t).hidden=!on}};
for(const b of tabs)b.addEventListener('click',()=>{show(b.dataset.t);history.replaceState(null,'','#'+b.dataset.t)});
const h=location.hash.slice(1);if(tabs.length)show(tabs.some(b=>b.dataset.t===h)?h:tabs[0].dataset.t);
for(const c of document.querySelectorAll('.stack td:not([data-l])')){let i=0,p=c;while(p=p.previousElementSibling)i+=p.colSpan;c.dataset.l=c.closest('table').rows[0].cells[i]?.textContent||''}
}
try{
const f=document.querySelector('.falcon'),say=document.querySelector('.say'),hero=document.querySelector('.hero');
if(f&&say){f.addEventListener('click',()=>{say.classList.add('on');clearTimeout(f._t);f._t=setTimeout(()=>say.classList.remove('on'),4000)})}
const still=matchMedia('(prefers-reduced-motion: reduce)').matches;
if(f&&hero){
 const hunt=hero.classList.contains('hunt'),per=hunt?15000:13000;
 const pos=(u,W,H)=>{
  if(!hunt){const a=u*2*Math.PI,rx=Math.min(W*.2,170),ry=H*.2;return [W-rx-40+rx*Math.cos(a),H*.42+ry*Math.sin(a)]}
  const d=Math.exp(-Math.pow((u-.55)/.06,2));
  return [-90+u*(W+180),H*.4+Math.sin(u*Math.PI*2)*H*.08+d*H*.3]};
 const place=u=>{const W=hero.clientWidth,H=hero.clientHeight,s=f.offsetWidth/2;const [x,y]=pos(u,W,H),[x2,y2]=pos((u+.003)%1,W,H);
  f.style.transform=`translate(${x-s}px,${y-s}px) rotate(${Math.atan2(y2-y,x2-x)}rad)`};
 const u0=hunt?.3:.1;place(u0);
 if(!still){const t0=performance.now()-u0*per;const fr=tm=>{place(((tm-t0)%per)/per);requestAnimationFrame(fr)};requestAnimationFrame(fr)}}
}catch(e){}"""


def _fav():
    return quote(LOGO.replace(' aria-hidden="true"', ' xmlns="http://www.w3.org/2000/svg"'))


def _num_ev(x):
    return "—" if x is None else f"{x:g}"


def _market_pane(b):
    mac = b.get("macro") or {}
    rg = mac.get("regime") or {}
    en = _LANG == "en"
    idx = "".join(f"<span><b>{E(i['ticker'])}</b> {_pct(i['day'])} {t('сегодня', 'today')} · {_pct(i['ret5'])} {t('за 5 дн.', 'in 5d')}</span>" for i in mac.get("index", []))
    facts = []
    if rg.get("vix") is not None:
        facts.append(f"VIX {rg['vix']:.1f}" + (f" ({_pct(rg['vix_chg'])} {t('за день', 'today')})" if rg.get("vix_chg") is not None else ""))
    if rg.get("breadth") is not None:
        facts.append(t(f"выше SMA20: {rg['breadth'] * 100:.0f}% бумаг", f"above SMA20: {rg['breadth'] * 100:.0f}% of stocks"))
    label = rg.get("label_en" if en else "label", "—")
    note = rg.get("note_en" if en else "note", "")
    reg = (f"<div class='reg'><p class='sub'>{t('Режим рынка', 'Market regime')}</p><h3>{E(label)}</h3><p>{E(note)}</p>"
           f"<p class='sub'>{E(' · '.join(facts))}</p>{_summary(mac.get('summary'))}</div>")
    ev_html, last = "", None
    for e in mac.get("events", []):
        day = e.get("day_ny", e["day"]) if en else e["day"]
        if day != last:
            ev_html += f"<p class='day'>{E(_long_day(day))}</p>"
            last = day
        fc = " · ".join(x for x in (f"{t('прогноз', 'forecast')} {_num_ev(e['expected'])}" if e["expected"] is not None else "",
                                    f"{t('было', 'prior')} {_num_ev(e['last'])}" if e["last"] is not None else "",
                                    f"<b>{t('факт', 'actual')} {_num_ev(e['actual'])}</b>" if e["actual"] is not None else "") if x)
        main, second = (e["ny"], f"{e['mad']} {t('Мадрид', 'Madrid')}") if en else (e["mad"], f"{e['ny']} NY")
        ev_html += (f"<div class='ev'><b>{main}</b><small class='ny'>{second}</small>"
                    f"<span>{E(e['name'])}{(' <small>' + E(e['period']) + '</small>') if e['period'] else ''}<br><small>{fc}</small></span>"
                    f"<span class='imp {e['imp']}'>{t('ВАЖНО', 'HIGH') if e['imp'] == 'high' else t('средне', 'medium')}</span></div>")
    if not ev_html:
        ev_html = f"<p class='empty'>{t('Календарь сейчас недоступен.', 'The calendar is unavailable right now.') if mac.get('events_error') else t('На неделе нет важных событий.', 'No major events this week.')}</p>"
    earn = "".join(f"<div class='ev'><b>{_exp(x['date'])}</b><small class='ny'></small><span><b>{E(x['ticker'])}</b> {t('отчёт', 'earnings')}</span>"
                   f"<span class='imp {'high' if x['days'] <= 7 else 'medium'}'>{t('через', 'in')} {x['days']} {t('дн.', 'd')}</span></div>" for x in mac.get("earnings", []))
    tz = t("Время по Мадриду (и Нью-Йорку).", "Times in New York (and Madrid).")
    return (f"{reg}<div class='two'><div><h2>{t('Календарь событий США', 'US economic calendar')}</h2><p class='sub'>{tz} {t('Важные и средние события на 7 дней.', 'High and medium impact, next 7 days.')}</p>{ev_html}</div>"
            f"<div><h2>{t('Отчёты по вотчлисту', 'Watchlist earnings')}</h2><p class='sub'>{t('На 3 недели вперёд. Перед отчётом IV растёт, после — падает.', 'Next 3 weeks. IV rises into earnings and drops after.')}</p>"
            f"{earn or '<p class=empty>' + t('Отчётов в ближайшие 3 недели нет.', 'No earnings in the next 3 weeks.') + '</p>'}</div></div>")


def _summary(sm):
    """A short story of yesterday and today (Claude or a template, see scout/story.py) plus headlines."""
    if not sm:
        return ""
    st = sm.get("story") or {}
    text = st.get(_LANG) or ""
    news = "".join(f"<li><a href='{E(n['url'])}' target='_blank' rel='noopener'>{E(n['title'])}</a> <small>{E(n['source'])}</small></li>"
                   for n in sm.get("news", []))
    return ((f"<p class='sub' style='margin-top:12px'>{t('Вчера и сегодня', 'Yesterday and today')}</p><p class='sum story'>{E(text)}</p>" if text else "")
            + (f"<p class='sub' style='margin-top:12px'>{t('Заголовки', 'Headlines')}</p><ul class='news'>{news}</ul>" if news else ""))


def _scanner(b):
    rows = [r for r in b["scanner"] if max(r.get("option_score", 0), r["s"]["stock_score"]) >= 15][:10]
    u = b.get("universe") or {}
    funnel = (t(f"Проверено {u['checked']} бумаг → ликвидных {u['passed']} (цена от $30, оборот от $300 млн в день, живые опционы) → полный разбор {u['deep']}. ",
                f"Checked {u['checked']} stocks → {u['passed']} liquid (price ≥ $30, ≥ $300M traded a day, active options) → {u['deep']} fully analysed. ")
              if u.get("checked") else "")
    items = "".join(_scan_item(r) for r in rows) or f"<p class='empty'>{t('Ни у одного тикера нет заметного сигнала.', 'No ticker shows a noticeable signal.')}</p>"
    return (f"<h2>{t('Топ-10 по силе сигнала', 'Top 10 by signal strength')}</h2><p class='sub'>{funnel}"
            f"{t('▲ на рост, ▼ на падение, ★ — ваш вотчлист. Нажмите на строку, чтобы увидеть данные.', '▲ long, ▼ short, ★ your watchlist. Tap a row for details.')}</p>"
            f"<div class='shead'><span>{t('Тикер', 'Ticker')}</span><span></span><span>{t('Сила сигнала', 'Signal strength')}</span><span></span>"
            f"<span class='num'>{t('Цена', 'Price')}</span><span class='num'>{t('День', 'Day')}</span></div><div>{items}</div>")


def _bot_link(b, lang):
    bot = b.get("bot") or "option_scout_bot"
    return f"https://t.me/{bot}?start={lang}"


def render_html(b: dict, lang: str = "ru") -> str:
    _set(lang)
    en = _LANG == "en"
    demo, test, as_of = b["provider"] == "demo", b.get("test"), b["as_of"]
    st, st30 = b["stats_all"]["all"], b["stats_30"]["all"]
    rg = (b.get("macro") or {}).get("regime") or {}
    reg_label = rg.get("label_en" if en else "label", "—")
    pos = [o["pnl"] for o in b["open"] if o.get("pnl") is not None]
    n_ideas = len(b["options"]) + len(b["stocks"])
    closed30 = (t(f"{st30['n']} закрыто, {st30['win'] * 100:.0f}% в плюсе", f"{st30['n']} closed, {st30['win'] * 100:.0f}% winners")
                if st30["n"] else t("пока нет закрытых", "none closed yet"))
    kpis = (f"<div class='kpi reg-{rg.get('key', '')}'><small>{t('Рынок', 'Market')}</small><b>{E(reg_label)}</b>"
            f"<span>{'VIX ' + format(rg['vix'], '.1f') if rg.get('vix') is not None else ''}</span></div>"
            f"<div class='kpi'><small>{t('Цели сегодня', 'Targets today')}</small><b>{n_ideas}</b>"
            f"<span>{len(b['options'])} {t('опц.', 'options')} + {len(b['stocks'])} {t('акц.', 'stocks')}</span></div>"
            f"<div class='kpi'><small>{t('В работе', 'Open')}</small><b>{len(b['open'])}</b>"
            f"<span>{t(f'в плюсе {sum(1 for x in pos if x > 0)}', f'{sum(1 for x in pos if x > 0)} in profit') if pos else t('открытых идей', 'open ideas')}</span></div>"
            f"<div class='kpi'><small>{t('Итог 30 дней', '30-day result')}</small><b>{_pct(st30['avg_r']) if st30['n'] else '—'}</b><span>{closed30}</span></div>")
    title = _targets(n_ideas) if n_ideas else t("Целей нет", "No targets")
    mode = "hunt" if n_ideas else "circle"
    best = max(b["options"] + b["stocks"], key=lambda r: max(r.get("option_score", 0), r["s"]["stock_score"]), default=None)
    if best:
        speech = t(f"Самая яркая цель — {best['ticker']}: {_why(best)}. Рынок: {reg_label.lower()}.",
                   f"Brightest target: {best['ticker']} — {_why(best)}. Market: {reg_label.lower()}.")
    else:
        near = b.get("near") or []
        speech = t("Сильных целей нет, лучше не торговать.", "No strong targets — better not to trade today.") + (
            t(f" Ближе всех к порогу {near[0]['ticker']}.", f" Closest to the bar: {near[0]['ticker']}.") if near else "")
    near = ", ".join(f"{E(r['ticker'])} {max(r.get('option_score', 0), r['s']['stock_score']):.0f}" for r in b.get("near", []))
    near_p = t(f" Ближе всех к порогу: {near}.", f" Closest to the bar: {near}.") if near else ""
    ms = b.get("min_score", 55)
    mso = b.get("min_score_options", 70)
    short = [r for r in b["options"] if r.get("mode", "short") == "short"]
    longs = [r for r in b["options"] if r.get("mode") == "long"]
    long_cards = "".join(_option_card(r, as_of) for r in longs) or (
        f"<p class='empty'>{t('Сегодня нет идей с экспирацией через 2–5 недель, прошедших фильтры.', 'No ideas with 2–5 week expirations passed the filters today.')}</p>")
    cards = "".join(_option_card(r, as_of) for r in short) or (
        f"<p class='empty'>{t(f'Сильных опционных идей нет: сила ниже {mso} или контракты не прошли фильтры (до $100, безубыток в пределах ожидаемого движения, ликвидность).', f'No strong option ideas: strength below {mso} or no contract passed the filters (≤ $100, break-even within the expected move, liquidity).')}{near_p}</p>")
    stocks = "".join(_stock_card(r, as_of) for r in b["stocks"]) or (
        f"<p class='empty'>{t(f'Сильных идей по акциям нет: ни одна бумага не набрала силу {ms}.', f'No strong stock ideas: nothing reached strength {ms}.')}{near_p}</p>")
    avoid = "".join(f"<li><b>{E(a['ticker'])}</b> — {E(a.get('why_en', a['why']) if en else a['why'])}</li>" for a in b["avoid"])
    opn = "".join(_open_row(r) for r in b["open"])
    cls = "".join(_closed_row(r) for r in b["recent_closed"])
    drv = "".join(f"<tr><td>{E((NAMES_EN if en else NAMES).get(k, k))}</td><td class='num'>{v['n']}</td><td class='num'>{v['win'] * 100:.0f}%</td><td class='num'>{_pct(v['avg_r'])}</td></tr>"
                  for k, v in sorted(b["stats_all"]["driver"].items(), key=lambda kv: -kv[1]["n"]) if v["n"])
    alltime = t(f" · за всё время {st['n']}", f" · all time {st['n']}") if st["n"] != st30["n"] else ""
    slab = (f"<div class='slab'><div class='big'>{_pct(st30['avg_r'])}</div><p>{t('средний итог закрытых идей за 30 дней', 'average result of ideas closed in 30 days')} · {closed30}{alltime}</p></div>"
            if st30["n"] else f"<div class='slab'><div class='big'>{t('0 закрытых', '0 closed')}</div><p>{t('результаты появятся, когда закроются первые идеи', 'results appear once the first ideas close')}</p></div>")
    errs = "".join(f"<li>{E(e['ticker'])}: {E(e['error'])}</li>" for e in b["errors"])
    badge = (f'<span class="badge">{t("демо-данные", "demo data")}</span>' if demo else '') + (f'<span class="badge">{t("тест", "test")}</span>' if test else '')
    tab = lambda tid, name, n=None: f"<button role='tab' data-t='{tid}'>{name}{f'<i>{n}</i>' if n is not None else ''}</button>"
    other = ("../", "RU") if en else ("en/", "EN")
    bot = _bot_link(b, _LANG)
    when = t("по будням в 21:35 по Мадриду, днём — алерты о сильных идеях, по пятницам — итоги недели",
             "on weekdays at 3:35 pm New York time, plus intraday alerts on strong ideas and a Friday recap")
    page = f"""<!DOCTYPE html><html lang="{_LANG}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Falco Scout — {t('бриф', 'daily brief')}</title><meta name="theme-color" content="#0b1020"><link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&family=Unbounded:wght@500;600&display=swap" rel="stylesheet">
<link rel="icon" href="data:image/svg+xml,@@FAV@@"><style>{CSS}</style></head><body><main class="wrap">
<div class="top"><div class="brand">{LOGO}<b>Falco Scout</b></div>
<a class="lang" href="{other[0]}" hreflang="{'ru' if en else 'en'}">{other[1]}</a>
<a class="sub-btn" href="{bot}" target="_blank" rel="noopener">{TG_ICON}<span class="lg">{t('Подписаться в Telegram', 'Get it in Telegram')}</span><span class="sm">{t('Подписаться', 'Subscribe')}</span></a></div>
<div class="hero {mode}"><p class="sub2">{E(_long_day(as_of))}{badge}{(' · ' + t('утренний бриф, не в журнале', 'pre-open brief, not recorded')) if b.get('preopen') else (' · ' + t('вне сессии', 'off-hours')) if b.get('off_hours') else ''}</p><h1>{E(title)}</h1>
<svg class="ridge" viewBox="0 0 400 40" preserveAspectRatio="none" aria-hidden="true"><path d="M0 40 L0 26 L40 18 L70 24 L110 10 L150 22 L190 14 L240 26 L280 16 L330 24 L370 12 L400 20 L400 40Z" fill="#0b1020"/></svg>
<div class="falcon" role="button" aria-label="{t('Что видит сокол', 'What the falcon sees')}">{BIRD}</div><div class="say" aria-live="polite">{E(speech)}</div></div>
<div class="kpis">{kpis}</div>
<nav class="tabs" role="tablist">{tab('mkt', t('Рынок', 'Market'))}{tab('opt', t('Опционы', 'Options'), len(b['options']) + len(b.get('rebounds', [])))}{tab('stk', t('Акции', 'Stocks'), len(b['stocks']))}{tab('jr', t('Журнал', 'Track record'), len(b['open']) or None)}</nav>
<section class="pane" id="mkt">{_market_pane(b)}<div style="margin-top:28px">{_scanner(b)}</div></section>
<section class="pane" id="opt" hidden>{_panic_note(b)}<h2>{t("Короткие · до 2 недель", "Short · up to 2 weeks")}</h2><p class="sub">{t('Лучшая идея в каждой ценовой категории: до $100, $100–200 и $200–500 (только с вероятностью прибыли от 40%). Цена — за 1 контракт (100 акций), она же максимальный убыток.', 'The best idea in each price tier: under $100, $100–200 and $200–500 (only with at least a 40% chance of profit). Price is per contract (100 shares) and is also the maximum loss.')}</p>
<div class="cards">{cards}</div>
<h2 style="margin-top:28px">{t("Длинные · 2–5 недель", "Long · 2–5 weeks")}</h2>
<p class="sub">{t("Те же сигналы, но экспирация через 2–5 недель: дороже контракт, зато меньше теряется на времени и спреде. Журнал считает короткие и длинные отдельно — через 3 месяца сравним.", "The same signals with 2–5 week expirations: a pricier contract, but less lost to time decay and the spread. The track record counts short and long separately; we compare them after 3 months.")}</p>
<div class="cards">{long_cards}</div>
<h2 style="margin-top:28px">{t("На отскок · эксперимент", "Snap-back · experimental")}</h2>
<p class="sub">{t("Колл после обвала — против тренда, когда падение ушло слишком далеко (RSI и движение за 5 дней сильно за нормой). По одной идее на каждый срок. Гипотеза: журнал считает эти идеи отдельно.", "A call after a crash — against the trend, when the drop has run too far (RSI and the 5-day move well past normal). One idea per expiration mode. A hypothesis: the track record counts these separately.")}</p>
<div class="cards">{"".join(_option_card(r, as_of) for r in b.get("rebounds", [])) or "<p class='empty'>" + t("Сейчас нет перерастянутых движений с подходящими опционами.", "No overstretched moves with suitable options right now.") + "</p>"}</div>
{f'<h2 style="margin-top:24px">{t("Не покупать опционы", "Avoid buying options")}</h2><ul class="avoid">{avoid}</ul>' if avoid else ''}</section>
<section class="pane" id="stk" hidden>{_panic_note(b)}<p class="sub">{t('Идея на одну акцию, сколько брать — решаете вы. Цель — ожидаемое движение за 10 торговых дней, стоп — половина пути, но не ближе дневного шума.', 'One-share ideas: position size is up to you. Target is the expected move over 10 trading days; the stop is half of that, but never inside daily noise.')}</p>
<div class="cards">{stocks}</div></section>
<section class="pane" id="jr" hidden>{slab}
<div class="two"><div><h2>{t('Открытые', 'Open')}</h2>
{f'<table class="stack"><thead><tr><th>{t("Дата", "Date")}</th><th>{t("Идея", "Idea")}</th><th class="num">{t("Сейчас", "Now")}</th><th class="num">{t("Итог", "Result")}</th><th>{t("План", "Plan")}</th></tr></thead><tbody>{opn}</tbody></table>' if opn else f'<p class="empty">{t("Нет открытых идей.", "No open ideas.")}</p>'}
</div><div><h2>{t('Закрытые', 'Closed')}</h2>
{f'<table class="stack"><thead><tr><th>{t("Даты", "Dates")}</th><th>{t("Идея", "Idea")}</th><th class="num">{t("Выход", "Exit")}</th><th>{t("Причина", "Reason")}</th><th class="num">{t("Итог", "Result")}</th></tr></thead><tbody>{cls}</tbody></table>' if cls else f'<p class="empty">{t("Пока ни одна идея не закрыта.", "No idea has closed yet.")}</p>'}
{f'<h2 style="margin-top:20px">{t("Какие сигналы работают", "Which signals work")}</h2><table><thead><tr><th>{t("Главный сигнал", "Main signal")}</th><th class="num">{t("Идей", "Ideas")}</th><th class="num">{t("В плюсе", "Winners")}</th><th class="num">{t("Средний итог", "Avg result")}</th></tr></thead><tbody>{drv}</tbody></table>' if drv else ''}
</div></div><p class="note">{t('Итог: для опционов — изменение премии, для акций — движение цены в сторону идеи. Идеи закрываются по тейку, стопу или дате выхода.', 'Result: for options, the change in premium; for stocks, the price move in the idea’s direction. Ideas close at take-profit, stop or their exit date.')}</p></section>
<div class="join"><p><b>{t('Бриф в Telegram', 'The brief in Telegram')}</b><br>{t('Бот присылает его', 'The bot sends it')} {when}. {t('Бесплатно, отписка — /stop.', 'Free; unsubscribe with /stop.')}</p>
<a class="sub-btn" href="{bot}" target="_blank" rel="noopener">{TG_ICON}<span>{t('Подписаться', 'Subscribe')}</span></a></div>
<details class="more legend" style="margin-top:24px"><summary>{t('Как читать бриф', 'How to read the brief')}</summary>
<p><b>{t('Сила сигнала, 0–100', 'Signal strength, 0–100')}</b>{t('Насколько согласны тренд, приток денег в опционы, необычный объём и вчерашний поток, закрепившийся в OI. Акции попадают в бриф от 55, опционы — только от 70 (максимальная уверенность), дневной алерт — от 65. Сила снижается вдвое, если идея идёт против силы бумаги к рынку (шорт бумаги сильнее рынка) или догоняет уже ушедшее движение: шорт после обвала, лонг после взлёта («риск отскока»).', 'How well the trend, money flowing into options, unusual volume and yesterday’s flow that stuck as open interest agree. Stocks enter the brief from 55, options only from 70 (highest conviction), intraday alerts from 65. Strength is halved when an idea fights relative strength (a short on a stock stronger than the market) or chases a move that already ran far: a short after a crash, a long after a spike (“snap-back risk”).')}</p>
<p><b>{t('Цель и стоп по акциям', 'Stock target and stop')}</b>{t('Цель — ожидаемое движение за горизонт идеи по большей из волатильностей: подразумеваемой (IV30) и фактической за 20 дней. Стоп — половина пути, но не ближе 1 ATR. От 60% годовой волатильности идея помечена ⚠.', 'The target is the expected move over the idea’s horizon, using the higher of implied (IV30) and 20-day realized volatility. The stop is half of that, but never closer than 1 ATR. Ideas above 60% annual volatility are flagged ⚠.')}</p>
<p><b>{t('Опционы', 'Options')}</b>{t('Тейк +100% к премии, стоп −50%, выход не позже дня перед экспирацией. Вероятность прибыли — шанс оказаться за безубытком к экспирации по Блэку — Шоулзу.', 'Take-profit +100% of premium, stop −50%, exit no later than the day before expiry. Chance of profit is the Black–Scholes probability of finishing beyond break-even.')}</p>
<p><b>{t('Чего сигналы не знают', 'What the signals cannot know')}</b>{t('Рост OI не показывает, кто купил, а кто продал. Верить стоит статистике журнала после 50–100 закрытых идей. Аналитика, не инвестиционный совет.', 'Rising open interest does not show who bought and who sold. Trust the track record only after 50–100 closed ideas. Analytics, not investment advice.')}</p>
</details>
{f'<details class="more"><summary>{t("Ошибки загрузки", "Data errors")} ({len(b["errors"])})</summary><ul class="note">{errs}</ul></details>' if errs else ''}
<p class="note">{t('Сгенерировано', 'Generated')} {E(b['generated'])} UTC · {E(b['provider'])}</p></main>
<script>{JS}</script>{_counter(b)}</body></html>"""
    return page.replace("@@FAV@@", _fav())


def _counter(b):
    """Visit counter (GoatCounter: no cookies, no consent banner). Only when a code is configured."""
    code = b.get("goatcounter")
    if not code or not code.replace("-", "").isalnum():
        return ""
    return (f'<script data-goatcounter="https://{code}.goatcounter.com/count" '
            'async src="//gc.zgo.at/count.js"></script>')


# ---------------- Telegram (parse_mode=HTML), two lines per idea

def _tg_option(r, as_of):
    p, s = r["option"], r["s"]
    r_ = _right(p)
    k = f"{p['strike']:g}/{p['short_strike']:g}" if p["type"] == "spread" else f"{p['strike']:g}"
    kind = f"{r_}{t('-спред', ' spread')}" if p["type"] == "spread" else r_
    rep = " ↺" if r.get("option_open_since") else ""
    sec = f" · {E(_sec(r))}" if _sec(r) else ""
    tier = f" · <i>{E(_tier(r))}</i>" if _tier(r) and r.get("tier") != "rebound" else ""
    return (f"{'🟢' if s['side'] == 'bull' else '🔴'} <b>{E(r['ticker'])}</b>{sec}{tier}\n{kind} {k} {t('до', 'exp.')} {_exp(p['exp'])} · ${p['cost_usd']:,.0f}\n"
            f"<i>{E(_why(r))}</i> · {t('б/у', 'b/e')} {_pct(_be(p))}{(' · ' + t('потенциал', 'upside') + f" +{p['payoff_em'] * 100:.0f}%") if p.get('payoff_em') is not None else ''} · {t('сила', 'strength')} {r['option_score']:.0f}{rep}")


def _tg_stock(r, as_of):
    p, s = r["stock"], r["s"]
    bull = s["side"] == "bull"
    rep = " ↺" if r.get("stock_open_since") else ""
    sec = f" · {E(_sec(r))}" if _sec(r) else ""
    return (f"{'🟢' if bull else '🔴'} <b>{E(r['ticker'])}</b>{sec}\n{t('лонг', 'long') if bull else t('шорт', 'short')} ${p['entry']:,.2f} → "
            f"🎯 {t('цель', 'target')} ${p['target']:,.2f} ({_pct(p['target_pct'] * (1 if bull else -1), 0)}) · 🛑 {t('стоп', 'stop')} ${p['stop']:,.2f}\n"
            f"<i>{E(_why(r))}</i> · {t('сила', 'strength')} {s['stock_score']:.0f} · {t('до', 'until')} {_date(p['exit_by'])}"
            f"{' ⚠️' if p.get('high_vol') else ''}{rep}")


def _tg_closed(c):
    r = c["result_r"]
    return f"{'✅' if r > 0 else '❌'} {E(c['ticker'])} {_pct(r)} · {E(_exit_reason(c['exit_reason']))}"


def _tg_head(b, title):
    tag = t(" · ДЕМО", " · DEMO") if b["provider"] == "demo" else ""
    tag += t(" · ТЕСТ", " · TEST") if b.get("test") else ""
    return f"{title} · {_date(b['as_of'])}{tag}"


def _tg_today_events(b):
    evs = [e for e in (b.get("macro") or {}).get("events", []) if e["day"] == b["as_of"] and e["imp"] == "high"]
    if not evs:
        return None
    return "📅 " + ", ".join(f"{e['ny'] + ' ET' if _LANG == 'en' else e['mad']} {E(e['name'])}" for e in evs[:3])


def render_text(b: dict, weekly: bool = False, lang: str = "ru") -> str:
    _set(lang)
    as_of = b["as_of"]
    rg = (b.get("macro") or {}).get("regime") or {}
    n = len(b["options"]) + len(b["stocks"])
    head = f"🦅 <b>{_tg_head(b, 'Falco Scout' + (t(' · утро', ' · pre-open') if b.get('preopen') else ''))}</b>\n" + (_targets(n) if n else t("Целей нет", "No targets"))
    label = rg.get("label_en" if _LANG == "en" else "label")
    if label:
        head += f" · {t('рынок', 'market')}: {E(label.lower())}" + (f", VIX {rg['vix']:.1f}" if rg.get("vix") is not None else "")
    L = [head]
    if b.get("preopen"):
        L.append(t("🌅 <i>Утренний бриф до открытия: цены вчерашнего закрытия, опционы ещё не котируются. "
                   "В журнал не записывается — журнал ведёт только бриф перед закрытием.</i>",
                   "🌅 <i>Pre-open brief: prices are yesterday's close and options aren't quoted yet. "
                   "Not recorded — the track record uses only the pre-close brief.</i>"))
    elif b.get("off_hours"):
        L.append(t("⚠️ <i>Запуск вне торговой сессии: цены и котировки опционов Yahoo могут отличаться от вечернего брифа.</i>",
                   "⚠️ <i>Run outside market hours: Yahoo prices and option quotes may differ from the evening brief.</i>"))
    ev = _tg_today_events(b)
    if ev:
        L.append(ev)
    if _panic_note(b, False):
        L.append(_panic_note(b, False))
    for mode, title in (("short", t("ОПЦИОНЫ · ДО 2 НЕДЕЛЬ", "OPTIONS · UP TO 2 WEEKS")), ("long", t("ОПЦИОНЫ · 2–5 НЕДЕЛЬ", "OPTIONS · 2–5 WEEKS"))):
        lst = [r for r in b["options"] if r.get("mode", "short") == mode]
        if lst:
            L += ["", f"<b>{title}</b>"]
            for r in lst:
                L += ["", _tg_option(r, as_of)]
    if b.get("rebounds"):
        L += ["", f"<b>{t('НА ОТСКОК', 'SNAP-BACK')}</b> <i>{t('эксперимент, против тренда', 'experimental, counter-trend')}</i>"]
        for r in b["rebounds"]:
            L += ["", _tg_option(r, as_of)]
    if b["stocks"]:
        L += ["", f"<b>{t('АКЦИИ', 'STOCKS')}</b>"]
        for r in b["stocks"]:
            L += ["", _tg_stock(r, as_of)]
    if not n:
        ms = b.get("min_score", 55)
        L += ["", t(f"Ни одна бумага не набрала силу {ms}: лучше не торговать.", f"Nothing reached strength {ms}: better not to trade today.")]
        if b.get("near"):
            L.append(t("Ближе всех: ", "Closest: ") + ", ".join(
                f"{E(r['ticker'])} {'▲' if r['s']['side'] == 'bull' else '▼'} {max(r.get('option_score', 0), r['s']['stock_score']):.0f}"
                for r in b["near"]))
    res = [_tg_closed(c) for c in b["closed_today"]]
    if b["open"]:
        pos = [o["pnl"] for o in b["open"] if o.get("pnl") is not None]
        res.append(t(f"⏳ в работе {len(b['open'])}", f"⏳ {len(b['open'])} open")
                   + (t(f", в плюсе {sum(1 for x in pos if x > 0)}", f", {sum(1 for x in pos if x > 0)} in profit") if pos else ""))
    if res:
        L += ["", f"<b>{t('Итоги', 'Results')}</b>"] + res
    if weekly:
        L += ["", render_weekly(b, _LANG)]
    return "\n".join(L)


def render_weekly(b: dict, lang: str | None = None) -> str:
    if lang:
        _set(lang)
    wk = b.get("week_closed") or []
    title = t("Охота за неделю", "Week's hunt")
    if not wk:
        return f"🗓 <b>{title}</b>: " + t("ни одна идея не закрылась.", "no idea closed.")
    rs = [c["result_r"] for c in wk]
    best, worst = max(wk, key=lambda c: c["result_r"]), min(wk, key=lambda c: c["result_r"])
    return (f"🗓 <b>{title}</b>: " + t(f"закрыто {len(wk)}, в плюсе {sum(1 for x in rs if x > 0)}, средний {_pct(sum(rs) / len(rs))}",
                                      f"{len(wk)} closed, {sum(1 for x in rs if x > 0)} winners, average {_pct(sum(rs) / len(rs))}")
            + "\n" + t(f"лучшая {E(best['ticker'])} {_pct(best['result_r'])} · худшая {E(worst['ticker'])} {_pct(worst['result_r'])}",
                       f"best {E(best['ticker'])} {_pct(best['result_r'])} · worst {E(worst['ticker'])} {_pct(worst['result_r'])}"))


def render_alert(b: dict, ny_time: str, lang: str = "ru") -> str | None:
    """Intraday: only what changed — new strong ideas and closed ones."""
    _set(lang)
    new = b.get("new_ideas") or []
    if not new and not b["closed_today"]:
        return None
    L = [f"🦅 <b>{_tg_head(b, t('Пикирую', 'Diving in'))} · {ny_time} NY</b>"]
    for x in new:
        L += ["", _tg_stock(x["row"], "") if x["kind"] == "stock" else _tg_option(x["row"], "")]
    if b["closed_today"]:
        L += ["", f"<b>{t('Закрылись', 'Closed')}</b>"] + [_tg_closed(c) for c in b["closed_today"]]
    return "\n".join(L)
