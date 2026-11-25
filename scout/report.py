"""Daily brief rendering: self-contained HTML page + short text for Telegram."""
from __future__ import annotations

import html
import json

from .ideas import NAMES

E = html.escape
SIDE = {"bull": "рост", "bear": "падение"}


def _p(x, d=1):
    return "—" if x is None else f"{x * 100:.{d}f}%"


def _n(x, d=2):
    return "—" if x is None else f"{x:,.{d}f}"


def _usd(x):
    if x is None:
        return "—"
    return f"${x / 1e6:.1f}M" if abs(x) >= 1e6 else f"${x / 1e3:.0f}K" if abs(x) >= 1e3 else f"${x:,.0f}"


def _exp(e):
    return f"{e[8:10]}.{e[5:7]}"


def _pct(x, d=1, sign=True):
    if x is None:
        return "—"
    return (f"{x * 100:+.{d}f}%" if sign else f"{x * 100:.{d}f}%").replace("-", "−")


def _date(iso):
    return f"{iso[8:10]}.{iso[5:7]}"


def structure(p: dict, ticker: str) -> str:
    r = "колл" if p["right"] == "call" else "пут"
    if p["type"] == "spread":
        return f"{ticker} {r}-спред {p['strike']:g}/{p['short_strike']:g}, экспирация {_exp(p['exp'])}"
    return f"{ticker} {r} {p['strike']:g}, экспирация {_exp(p['exp'])}"


def idea_label(rec: dict) -> str:
    p, t = rec["plan"], rec["ticker"]
    if p["type"] == "stock":
        return f"{'Покупка' if p['side'] == 'bull' else 'Шорт'} {t} от ${p['entry']:,.2f}"
    return f"{structure(p, t)} за ${p['entry']:.2f}"


def _since_note(since, as_of):
    if not since:
        return ""
    return "повтор: идея из дневного алерта" if since == as_of else f"повтор: идея открыта {_date(since)}"


def _be(p):
    """Move needed to break even, signed in the direction of the trade (puts need a fall)."""
    return p["req_move_pct"] * (1 if p["right"] == "call" else -1)


def _option_card(r, as_of):
    p, s, m = r["option"], r["s"], r["m"]
    em_w = min(100, p["em_pct"] / max(p["em_pct"], p["req_move_pct"], 1e-9) * 100)
    be_w = min(100, max(0, p["req_move_pct"]) / max(p["em_pct"], p["req_move_pct"], 1e-9) * 100)
    r_ = "колл" if p["right"] == "call" else "пут"
    what = (f"Купить {r_}-спред {p['strike']:g}/{p['short_strike']:g}" if p["type"] == "spread"
            else f"Купить {r_} {p['strike']:g}")
    extra = (f"<div><dt>Макс. прибыль</dt><dd>${p['max_profit_usd']:,.0f}</dd></div>" if p["type"] == "spread" else "")
    reasons = "".join(f"<li>{E(x)}</li>" for x in s["reasons"])
    since = _since_note(r.get("option_open_since"), as_of)
    return f"""<article class="card">
<header><h3>{E(r['ticker'])}</h3><span class="tag {s['side']}">{SIDE[s['side']]}</span>
<span class="score" title="Сила сигнала 0–100">сила <b>{r['option_score']:.0f}</b></span></header>
<p class="why1">{E(r.get('why', ''))}</p>
<p class="trade">{E(what)}, экспирация {_exp(p['exp'])}</p>
<p class="cost">${p['entry']:.2f} за опцион, ${p['cost_usd']:,.0f} за контракт. Это максимальный убыток.{(' · ' + E(since)) if since else ''}</p>
<div class="move"><div class="lbl">Нужно до безубытка <b>{_pct(_be(p))}</b> · ожидаемое движение <b>±{_pct(p['em_pct'], sign=False)}</b></div>
<div class="bar"><i class="em" style="width:{em_w:.0f}%"></i><i class="be" style="left:{be_w:.0f}%"></i></div></div>
<dl class="kv">
<div><dt>Цена акции</dt><dd>${m['price']:,.2f}</dd></div>
<div><dt>Безубыток</dt><dd>${p['breakeven']:,.2f}</dd></div>
<div><dt>Тейк</dt><dd>${p['target']:.2f} (+{(p['target'] / p['entry'] - 1) * 100:.0f}%)</dd></div>
<div><dt>Стоп</dt><dd>${p['stop']:.2f} (−{(1 - p['stop'] / p['entry']) * 100:.0f}%)</dd></div>
<div><dt>Вероятность прибыли</dt><dd>{_pct(p['pop'], 0, sign=False)}</dd></div>
<div><dt>Выход</dt><dd>до {_exp(p['exp'])}</dd></div>{extra}
</dl>
<details><summary>Все сигналы</summary><ul class="why">{reasons}</ul></details>
</article>"""


def _stock_card(r, as_of):
    p, s = r["stock"], r["s"]
    bull = s["side"] == "bull"
    reasons = "".join(f"<li>{E(x)}</li>" for x in s["reasons"])
    since = _since_note(r.get("stock_open_since"), as_of)
    return f"""<article class="card">
<header><h3>{E(r['ticker'])}</h3><span class="tag {s['side']}">{SIDE[s['side']]}</span>
<span class="score" title="Сила сигнала 0–100">сила <b>{s['stock_score']:.0f}</b></span></header>
<p class="why1">{E(r.get('why', ''))}</p>
<p class="trade">{'Покупка' if bull else 'Шорт'} от ${p['entry']:,.2f}</p>
<p class="cost">Держать до {_date(p['exit_by'])}{(' · ' + E(since)) if since else ''}</p>
<dl class="kv">
<div><dt>Цель</dt><dd class="up">${p['target']:,.2f} ({_pct(p['target_pct'] * (1 if bull else -1))})</dd></div>
<div><dt>Стоп</dt><dd class="dn">${p['stop']:,.2f} ({_pct(p['stop_pct'] * (-1 if bull else 1))})</dd></div>
<div><dt>Потенциал : риск</dt><dd>{p['rr']:.1f} : 1</dd></div>
<div><dt>Ожид. движение</dt><dd>±{_pct(p['target_pct'], sign=False)} за {p['max_hold_days']} дн.</dd></div>
</dl>
{f'<p class="warn">⚠ Высокая волатильность ({p["vol"] * 100:.0f}% годовых): цель и стоп шире обычного, цена может пройти стоп за один день. Риск точнее ограничить опционом.</p>' if p.get('high_vol') else ''}
<details><summary>Все сигналы</summary><ul class="why">{reasons}</ul></details>
</article>"""


def _scan_item(r):
    """One watchlist row: compact summary, details on tap."""
    m, s = r["m"], r["s"]
    ch = m["price"] / m["prev_close"] - 1 if m.get("prev_close") else None
    em = next(iter(m["em"].values()), None) if m.get("em") else None
    v = max(r.get("option_score", 0), s["stock_score"])
    side = "bull" if s["direction"] >= 0 else "bear"
    earn = f"{_exp(m['earnings'])}, через {m['earnings_days']} дн." if m.get("earnings") and m["earnings_days"] is not None and m["earnings_days"] >= 0 else "—"
    flow = f"{_usd(m['new_call_prem'])} / {_usd(m['new_put_prem'])}" if m["has_prev"] else "нет вчерашних данных"
    reasons = "".join(f"<li>{E(x)}</li>" for x in s["reasons"])
    return f"""<details class="srow"><summary>
<b class="tk">{E(r['ticker'])}{'<small>★</small>' if r.get('watch') else ''}</b><span class="arr {side}">{'▲' if side == 'bull' else '▼'}</span>
<span class="sbar"><i class="{side}" style="width:{v:.0f}%"></i></span><b class="sv">{v:.0f}</b>
<span class="num px">${m['price']:,.2f}</span><span class="num chg {'up' if (ch or 0) >= 0 else 'dn'}">{'—' if ch is None else _pct(ch)}</span>
</summary><div class="sdet"><p class="why1">{E(r.get('why', ''))}</p><dl class="kv3">
<div><dt>IV30</dt><dd>{_p(m['iv30'], 0)}</dd></div><div><dt>IV Rank</dt><dd>{_n(m['iv_rank'], 0) if m['iv_rank'] is not None else '—'}</dd></div>
<div><dt>IV/HV</dt><dd>{_n(m['iv_hv'])}</dd></div><div><dt>Ожид. движение</dt><dd>{_p(em)}</dd></div>
<div><dt>Put/Call по OI</dt><dd>{_n(m['pcr_oi'])}</dd></div><div><dt>Новый OI колы / путы</dt><dd>{flow}</dd></div>
<div><dt>Необычный объём</dt><dd>{_usd(m['unusual_premium'])}</dd></div><div><dt>Стены OI путы / колы</dt><dd>{_n(m['put_wall'], 1)} / {_n(m['call_wall'], 1)}</dd></div>
<div><dt>Отчёт</dt><dd>{earn}</dd></div></dl><ul class="why">{reasons}</ul></div></details>"""


def _open_row(rec):
    p, chg = rec["plan"], rec.get("pnl")
    cls = "" if chg is None else ("up" if chg >= 0 else "dn")
    return (f"<tr><td>{_date(rec['as_of'])}</td><td>{E(idea_label(rec))}</td>"
            f"<td class='num'>{_n(rec.get('current'))}</td><td class='num {cls}'>{_pct(chg)}</td>"
            f"<td class='nw'>до {_date(p.get('exit_by') or p.get('exp') or rec['as_of'])}</td></tr>")


def _closed_row(rec):
    r = rec["result_r"]
    return (f"<tr><td class='nw'>{_date(rec['as_of'])} → {_date(rec['exit_date'])}</td><td>{E(idea_label(rec))}</td>"
            f"<td class='num'>{_n(rec['exit_price'])}</td><td>{E(rec['exit_reason'])}</td>"
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


def _plural(n, one, few, many):
    n = abs(n) % 100
    if 11 <= n <= 14:
        return many
    return one if n % 10 == 1 else few if 2 <= n % 10 <= 4 else many


CSS = """
:root{color-scheme:light dark;--bg:light-dark(#f7f3ec,#0e1116);--ink:light-dark(#161b22,#ece6da);--mut:light-dark(#5e6772,#98a2ad);
--line:light-dark(#e4ddd0,#232a33);--card:light-dark(#fffdf8,#151a21);--y:#f2a93b;--slate:#4a5a6e;--up:light-dark(#0f7a47,#4cc38a);--dn:light-dark(#c2321f,#ff7a66);
--sky1:light-dark(#efe6d6,#141b24);--sky2:light-dark(#f7f3ec,#0e1116)}
h1,h2,.brand b,.kpi b,.big{font-family:Unbounded,Manrope,system-ui,sans-serif;font-weight:600;letter-spacing:-.01em}
.brand{display:flex;align-items:center;gap:10px}.brand svg{width:40px;height:40px;flex:none}.brand b{font-size:19px}.brand small{display:block;color:var(--mut);font-size:13px;font-family:Manrope,sans-serif;font-weight:400}
.hero{position:relative;height:150px;margin:14px 0 8px;border-radius:14px;overflow:hidden;background:linear-gradient(180deg,var(--sky1),var(--sky2));border:1px solid var(--line)}
.hero h1{position:absolute;left:18px;bottom:14px;margin:0;max-width:70%;z-index:1}.hero .sub2{position:absolute;left:18px;top:14px;margin:0;color:var(--mut);font-size:14px;z-index:1}
.hero .ridge{position:absolute;left:0;bottom:0;width:100%;height:38px;opacity:.5}
.falcon{position:absolute;left:0;top:0;width:64px;height:64px;color:var(--ink);cursor:pointer;z-index:2;will-change:transform;transform:translate(70%,30px)}
.falcon svg{width:100%;height:100%;display:block}
.falcon .w{transform-box:fill-box;animation:flap 1.1s ease-in-out infinite}.falcon .w1{transform-origin:50% 100%}.falcon .w2{transform-origin:50% 0}
@keyframes flap{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.55)}}
.say{position:absolute;right:14px;top:12px;max-width:min(60%,320px);background:var(--card);border:1px solid var(--line);border-radius:12px;padding:8px 12px;font-size:14px;
 opacity:0;transform:translateY(-6px);transition:.25s;z-index:3;pointer-events:none}.say.on{opacity:1;transform:none}
.sbar i{transform-origin:left;animation:grow .9s cubic-bezier(.2,.7,.2,1) both}@keyframes grow{from{transform:scaleX(0)}}
@media (prefers-reduced-motion:reduce){.falcon .w,.sbar i{animation:none}}
@media(max-width:600px){.falcon{width:50px;height:50px}.hero{height:170px}.hero h1{max-width:92%;font-size:24px}}
*{box-sizing:border-box;min-width:0}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 Manrope,system-ui,sans-serif;overflow-x:clip}
.wrap{max-width:1100px;margin:0 auto;padding:clamp(16px,3vw,40px) max(4vw,14px) 40px}
h1{font-size:clamp(26px,4vw,40px);line-height:1.1;margin:6px 0 16px;text-wrap:balance}
h2{font-size:21px;margin:0 0 4px}h3{font-size:20px;margin:0}
.sub{color:var(--mut);margin:0;font-size:14px}.badge{display:inline-block;background:var(--ink);color:var(--bg);padding:1px 8px;border-radius:4px;font-size:12px;font-weight:700;margin-left:6px}
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}.kpi small{display:block;color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.kpi b{display:block;font-size:22px;line-height:1.25}.kpi span{font-size:13px;color:var(--mut)}
.kpi.reg-stress b,.kpi.reg-nervous b{color:var(--dn)}.kpi.reg-calm_up b{color:var(--up)}
.tabs{display:flex;gap:4px;margin:22px 0 0;border-bottom:1px solid var(--line);overflow-x:auto;scrollbar-width:none;position:sticky;top:0;background:var(--bg);z-index:2}
.tabs button{font:inherit;font-weight:600;font-size:15px;color:var(--mut);background:none;border:0;border-bottom:3px solid transparent;padding:12px 12px 10px;cursor:pointer;white-space:nowrap}
.tabs button[aria-selected=true]{color:var(--ink);border-color:var(--y)}.tabs button i{font-style:normal;font-size:12px;background:var(--line);border-radius:9px;padding:0 6px;margin-left:4px}
.pane{padding-top:18px}.pane[hidden]{display:none}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,330px),1fr));gap:14px;margin-top:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}
.card header{display:flex;align-items:center;gap:8px}.score{margin-left:auto;color:var(--mut);font-size:14px}.score b{font-size:20px;color:var(--ink)}
.tag{font-size:12px;font-weight:700;padding:2px 8px;border-radius:4px;white-space:nowrap}.tag.bull{background:color-mix(in srgb,var(--up) 18%,transparent);color:var(--up)}
.tag.bear{background:color-mix(in srgb,var(--dn) 18%,transparent);color:var(--dn)}
.trade{font-weight:700;font-size:17px;margin:10px 0 2px}.cost{color:var(--mut);margin:0 0 10px;font-size:14px}
.move .lbl{font-size:14px}.bar{position:relative;height:8px;border-radius:4px;background:var(--line);margin:6px 0 12px}
.bar .em{position:absolute;inset:0 auto 0 0;background:color-mix(in srgb,var(--up) 45%,transparent);border-radius:4px}
.bar .be{position:absolute;top:-4px;width:3px;height:16px;background:var(--ink);transform:translateX(-1px)}
.kv{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px 14px;margin:0}.kv dt,.kv3 dt{font-size:12px;color:var(--mut)}.kv dd,.kv3 dd{margin:0;font-weight:700}
.kv3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px 14px;margin:8px 0}
.why{margin:8px 0 0;padding-left:18px;font-size:14px}.why1{margin:6px 0 0;font-size:14px;color:var(--mut)}
details>summary{cursor:pointer}details.more{margin-top:10px;font-size:14px}details.more summary{color:var(--mut)}
.warn{font-size:13px;margin:10px 0 0;padding:8px 10px;border-radius:6px;background:color-mix(in srgb,var(--y) 30%,transparent)}
.srow{border-bottom:1px solid var(--line)}.srow summary,.shead{display:grid;grid-template-columns:4.2em 1.2em minmax(40px,1fr) 2em 5.6em 4.4em;gap:8px;align-items:center;padding:10px 2px;list-style:none}
.shead{margin-top:10px;padding-block:6px;border-bottom:1px solid var(--line);font-size:12px;color:var(--mut);font-weight:600}.shead span:nth-child(3){grid-column:3/5}.shead span:nth-child(4){display:none}
.srow summary::-webkit-details-marker{display:none}.srow[open] summary{background:var(--card)}.sdet{padding:4px 2px 14px}
.arr.bull{color:var(--up)}.arr.bear{color:var(--dn)}.sbar{height:8px;background:var(--line);border-radius:4px;overflow:hidden}
.sbar i{display:block;height:100%}.sbar i.bull{background:var(--up)}.sbar i.bear{background:var(--dn)}.sv{text-align:right}
.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}.px,.chg{font-size:14px}
.up{color:var(--up)}.dn{color:var(--dn)}.nw{white-space:nowrap}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:12px;color:var(--mut);font-weight:600;white-space:nowrap}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:24px}
.slab{background:var(--y);color:#101418;border-radius:10px;padding:16px 18px;margin-bottom:18px}.slab .big{font-size:36px;font-weight:700;line-height:1}.slab p{margin:4px 0 0}
.reg{border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:18px}.reg h3{font-size:22px}.reg p{margin:6px 0 0}
.idx{display:flex;gap:18px;flex-wrap:wrap;margin-top:10px;font-size:14px}
.day{margin:16px 0 4px;font-size:13px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em;font-weight:700}
.ev{display:grid;grid-template-columns:3.4em 5.2em minmax(0,1fr) auto;gap:10px;align-items:baseline;padding:8px 0;border-bottom:1px solid var(--line);font-size:14px}
.imp{font-size:11px;font-weight:700;padding:1px 6px;border-radius:4px;text-align:center}.imp.high{background:color-mix(in srgb,var(--dn) 18%,transparent);color:var(--dn)}
.imp.medium{background:color-mix(in srgb,var(--y) 35%,transparent)}.ev small{color:var(--mut)}
.empty{color:var(--mut);padding:10px 0}.note{font-size:13px;color:var(--mut)}.avoid{padding-left:18px}.avoid li{margin:4px 0}
.legend p{margin:8px 0}.legend b{display:block}
@media(max-width:760px){.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.two{grid-template-columns:minmax(0,1fr)}.kv3{grid-template-columns:repeat(2,minmax(0,1fr))}
.ev{grid-template-columns:3.2em minmax(0,1fr) auto}.ev .ny{display:none}}
@media(max-width:600px){.stack thead{display:none}.stack tr{display:grid;padding-block:8px}
.stack td{display:flow-root;border:0;padding:2px 0;padding-inline-start:7em;text-align:start}
.stack td::before{content:attr(data-l);float:inline-start;width:6.5em;margin-inline-start:-7em;color:var(--mut)}.stack td:empty{display:none}}
"""

JS = """{
const f=document.querySelector('.falcon'),say=document.querySelector('.say');
if(f&&say){f.addEventListener('click',()=>{say.classList.add('on');clearTimeout(f._t);f._t=setTimeout(()=>say.classList.remove('on'),4000)})}
const still=matchMedia('(prefers-reduced-motion: reduce)').matches;
const hero=document.querySelector('.hero');
if(f&&hero){
 const hunt=hero.classList.contains('hunt'),per=hunt?15000:13000;
 const pos=(u,W,H)=>{
  if(!hunt){const a=u*2*Math.PI,rx=Math.min(W*.2,170),ry=H*.2;return [W-rx-40+rx*Math.cos(a),H*.42+ry*Math.sin(a)]}
  const d=Math.exp(-Math.pow((u-.55)/.06,2));   // the dive
  return [-90+u*(W+180),H*.4+Math.sin(u*Math.PI*2)*H*.08+d*H*.3]};
 const place=u=>{const W=hero.clientWidth,H=hero.clientHeight,s=f.offsetWidth/2;const [x,y]=pos(u,W,H),[x2,y2]=pos((u+.003)%1,W,H);
  f.style.transform=`translate(${x-s}px,${y-s}px) rotate(${Math.atan2(y2-y,x2-x)}rad)`};
 if(still){place(hunt?.3:.1)}else{place(hunt?.3:.1);const t0=performance.now()-(hunt?.3:.1)*per;const fr=t=>{place(((t-t0)%per)/per);requestAnimationFrame(fr)};requestAnimationFrame(fr)}}
;requestAnimationFrame(step)}
const tabs=[...document.querySelectorAll('.tabs button')];
const show=id=>{for(const b of tabs){const on=b.dataset.t===id;b.setAttribute('aria-selected',on);document.getElementById(b.dataset.t).hidden=!on}};
for(const b of tabs)b.onclick=()=>{show(b.dataset.t);history.replaceState(null,'','#'+b.dataset.t)};
const h=location.hash.slice(1);show(tabs.some(b=>b.dataset.t===h)?h:tabs[0].dataset.t);
for(const c of document.querySelectorAll('.stack td:not([data-l])')){let i=0,p=c;while(p=p.previousElementSibling)i+=p.colSpan;c.dataset.l=c.closest('table').rows[0].cells[i]?.textContent||''}
}"""

RU_DAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
RU_MON = ["", "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]


def _ru_day(iso):
    import datetime as _dt
    d = _dt.date.fromisoformat(iso)
    return f"{RU_DAYS[d.weekday()]}, {d.day} {RU_MON[d.month]}"


def _num_ev(x):
    return "—" if x is None else f"{x:g}"


def _market_pane(b):
    mac = b.get("macro") or {}
    rg = mac.get("regime") or {}
    idx = "".join(f"<span><b>{E(i['ticker'])}</b> {_pct(i['day'])} сегодня · {_pct(i['ret5'])} за 5 дн.</span>" for i in mac.get("index", []))
    facts = []
    if rg.get("vix") is not None:
        facts.append(f"VIX {rg['vix']:.1f}" + (f" ({_pct(rg['vix_chg'])} за день)" if rg.get("vix_chg") is not None else ""))
    if rg.get("breadth") is not None:
        facts.append(f"выше SMA20: {rg['breadth'] * 100:.0f}% вотчлиста")
    reg = (f"<div class='reg'><p class='sub'>Режим рынка</p><h3>{E(rg.get('label', '—'))}</h3><p>{E(rg.get('note', ''))}</p>"
           f"<p class='sub'>{E(' · '.join(facts))}</p><div class='idx'>{idx}</div></div>")
    ev_html, last = "", None
    for e in mac.get("events", []):
        if e["day"] != last:
            ev_html += f"<p class='day'>{E(_ru_day(e['day']))}</p>"
            last = e["day"]
        fc = " · ".join(x for x in (f"прогноз {_num_ev(e['expected'])}" if e["expected"] is not None else "",
                                    f"было {_num_ev(e['last'])}" if e["last"] is not None else "",
                                    f"<b>факт {_num_ev(e['actual'])}</b>" if e["actual"] is not None else "") if x)
        ev_html += (f"<div class='ev'><b>{e['mad']}</b><small class='ny'>{e['ny']} NY</small>"
                    f"<span>{E(e['name'])}{(' <small>' + E(e['period']) + '</small>') if e['period'] else ''}<br><small>{fc}</small></span>"
                    f"<span class='imp {e['imp']}'>{'ВАЖНО' if e['imp'] == 'high' else 'средне'}</span></div>")
    if not ev_html:
        ev_html = f"<p class='empty'>{'Календарь сейчас недоступен.' if mac.get('events_error') else 'На неделе нет важных событий.'}</p>"
    earn = "".join(f"<div class='ev'><b>{_exp(x['date'])}</b><small class='ny'></small><span><b>{E(x['ticker'])}</b> отчёт</span>"
                   f"<span class='imp {'high' if x['days'] <= 7 else 'medium'}'>через {x['days']} дн.</span></div>" for x in mac.get("earnings", []))
    return (f"{reg}<div class='two'><div><h2>Календарь событий США</h2><p class='sub'>Время по Мадриду (и Нью-Йорку). Только важные и средние события на 7 дней.</p>{ev_html}</div>"
            f"<div><h2>Отчёты по вотчлисту</h2><p class='sub'>На 3 недели вперёд. Перед отчётом IV растёт, после — падает.</p>"
            f"{earn or '<p class=empty>Отчётов в ближайшие 3 недели нет.</p>'}</div></div>")


def _scanner(b):
    rows = [r for r in b["scanner"] if max(r.get("option_score", 0), r["s"]["stock_score"]) >= 15][:10]
    u = b.get("universe") or {}
    funnel = (f"Проверено {u['checked']} бумаг → ликвидных {u['passed']} (цена от $30, оборот от $300 млн в день, живые опционы) → "
              f"полный разбор {u['deep']}. " if u.get("checked") else "")
    items = "".join(_scan_item(r) for r in rows) or "<p class='empty'>Ни у одного тикера нет заметного сигнала.</p>"
    return (f"<h2>Что видит сокол: топ-10</h2><p class='sub'>{funnel}▲ на рост, ▼ на падение, ★ — ваш вотчлист. "
            f"Нажмите на строку, чтобы увидеть данные.</p>"
            f"<div class='shead'><span>Тикер</span><span></span><span>Сила сигнала</span><span></span><span class='num'>Цена</span><span class='num'>День</span></div>"
            f"<div>{items}</div>")


def _fav():
    from urllib.parse import quote
    return quote(LOGO.replace(' aria-hidden="true"', ' xmlns="http://www.w3.org/2000/svg"'))


def render_html(b: dict) -> str:
    demo, test, as_of = b["provider"] == "demo", b.get("test"), b["as_of"]
    st, st30 = b["stats_all"]["all"], b["stats_30"]["all"]
    rg = (b.get("macro") or {}).get("regime") or {}
    pos = [o["pnl"] for o in b["open"] if o.get("pnl") is not None]
    closed30 = f"{st30['n']} закрыто, {st30['win'] * 100:.0f}% в плюсе" if st30["n"] else "пока нет закрытых"
    count30 = f" data-count='{st30['avg_r'] * 100:.1f}' data-dec='1' data-suf='%' data-sign='1'" if st30["n"] else ""
    alltime = f" · за всё время {st['n']}" if st["n"] != st30["n"] else ""
    kpis = (f"<div class='kpi reg-{rg.get('key', '')}'><small>Рынок</small><b>{E(rg.get('label', '—'))}</b>"
            f"<span>{'VIX ' + format(rg['vix'], '.1f') if rg.get('vix') is not None else ''}</span></div>"
            f"<div class='kpi'><small>Цели сегодня</small><b data-count='{len(b['options']) + len(b['stocks'])}'>{len(b['options']) + len(b['stocks'])}</b><span>{len(b['options'])} опц. + {len(b['stocks'])} акц.</span></div>"
            f"<div class='kpi'><small>В работе</small><b data-count='{len(b['open'])}'>{len(b['open'])}</b><span>{f'в плюсе {sum(1 for x in pos if x > 0)}' if pos else 'открытых идей'}</span></div>"
            f"<div class='kpi'><small>Итог 30 дней</small><b{count30}>{_pct(st30['avg_r']) if st30['n'] else '—'}</b>"
            f"<span>{closed30}</span></div>")
    n_ideas = len(b["options"]) + len(b["stocks"])
    title = (f"Вижу {n_ideas} {_plural(n_ideas, 'цель', 'цели', 'целей')}" if n_ideas else "Целей нет — кружу")
    mode = "hunt" if n_ideas else "circle"
    best = max(b["options"] + b["stocks"], key=lambda r: max(r.get("option_score", 0), r["s"]["stock_score"]), default=None)
    if best:
        speech = (f"Самая яркая цель — {best['ticker']}: {best.get('why', '')}. "
                  f"Рынок: {rg.get('label', '—').lower()}. Цель и стоп — в карточке.")
    else:
        near = b.get("near") or []
        speech = ("Сильных целей нет, лучше не торговать." + (f" Ближе всех к порогу {near[0]['ticker']}." if near else ""))
    near = ", ".join(f"{E(r['ticker'])} {max(r.get('option_score', 0), r['s']['stock_score']):.0f}" for r in b.get("near", []))
    near_p = f" Ближе всех к порогу: {near}." if near else ""
    ms = b.get("min_score", 55)
    cards = "".join(_option_card(r, as_of) for r in b["options"]) or f"<p class='empty'>Сильных опционных идей нет: сила ниже {ms} или контракты не прошли фильтры (до $100, безубыток в пределах ожидаемого движения, ликвидность).{near_p}</p>"
    stocks = "".join(_stock_card(r, as_of) for r in b["stocks"]) or f"<p class='empty'>Сильных идей по акциям нет: ни одна бумага не набрала силу {ms}.{near_p}</p>"
    avoid = "".join(f"<li><b>{E(a['ticker'])}</b> — {E(a['why'])}</li>" for a in b["avoid"])
    opn = "".join(_open_row(r) for r in b["open"])
    cls = "".join(_closed_row(r) for r in b["recent_closed"])
    drv = "".join(f"<tr><td>{E(NAMES.get(k, k))}</td><td class='num'>{v['n']}</td><td class='num'>{v['win'] * 100:.0f}%</td><td class='num'>{_pct(v['avg_r'])}</td></tr>"
                  for k, v in sorted(b["stats_all"]["driver"].items(), key=lambda kv: -kv[1]["n"]) if v["n"])
    slab = (f"<div class='slab'><div class='big'>{_pct(st30['avg_r'])}</div><p>средний итог закрытых идей за 30 дней · {st30['n']} идей · {st30['win'] * 100:.0f}% в плюсе"
            f"{alltime}</p></div>" if st30["n"] else
            "<div class='slab'><div class='big'>0 закрытых</div><p>результаты появятся, когда закроются первые идеи</p></div>")
    errs = "".join(f"<li>{E(e['ticker'])}: {E(e['error'])}</li>" for e in b["errors"])
    badge = ('<span class="badge">демо-данные</span>' if demo else '') + ('<span class="badge">тест, не в журнале</span>' if test else '')
    tab = lambda t, name, n=None: f"<button role='tab' data-t='{t}'>{name}{f'<i>{n}</i>' if n is not None else ''}</button>"
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Falco Scout — бриф</title><link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&family=Unbounded:wght@500;600&display=swap" rel="stylesheet">
<link rel="icon" href="data:image/svg+xml,{{FAV}}"><style>{CSS}</style></head><body><main class="wrap">
<header class="brand">{LOGO}<div><b>Falco Scout</b><small>опционы и акции · сокол видит рынок сверху</small></div></header>
<div class="hero {mode}"><p class="sub2">{E(_ru_day(as_of))} · {E(b['provider'])}{badge}</p><h1>{E(title)}</h1>
<svg class="ridge" viewBox="0 0 400 40" preserveAspectRatio="none" aria-hidden="true"><path d="M0 40 L0 26 L40 18 L70 24 L110 10 L150 22 L190 14 L240 26 L280 16 L330 24 L370 12 L400 20 L400 40Z" fill="var(--line)"/></svg>
<div class="falcon" role="button" aria-label="Что видит сокол">{BIRD}</div><div class="say" aria-live="polite">{E(speech)}</div></div>
<div class="kpis">{kpis}</div>
<nav class="tabs" role="tablist">{tab('opt', 'Опционы', len(b['options']))}{tab('stk', 'Акции', len(b['stocks']))}{tab('mkt', 'Рынок')}{tab('jr', 'Журнал', len(b['open']) or None)}</nav>
<section class="pane" id="opt"><p class="sub">Дешёвые недельные контракты, где безубыток не дальше ожидаемого движения. Цена — за 1 контракт (100 акций), она же максимальный убыток.</p>
<div class="cards">{cards}</div>
{f'<h2 style="margin-top:24px">Не покупать опционы</h2><ul class="avoid">{avoid}</ul>' if avoid else ''}</section>
<section class="pane" id="stk" hidden><p class="sub">Идея на одну акцию, сколько брать — решаете вы. Цель — ожидаемое движение за 10 торговых дней, стоп — половина пути, но не ближе дневного шума.</p>
<div class="cards">{stocks}</div></section>
<section class="pane" id="mkt" hidden>{_market_pane(b)}<div style="margin-top:28px">{_scanner(b)}</div></section>
<section class="pane" id="jr" hidden>{slab}
<div class="two"><div><h2>Открытые</h2>
{f'<table class="stack"><thead><tr><th>Дата</th><th>Идея</th><th class="num">Сейчас</th><th class="num">Итог</th><th>План</th></tr></thead><tbody>{opn}</tbody></table>' if opn else '<p class="empty">Нет открытых идей.</p>'}
</div><div><h2>Закрытые</h2>
{f'<table class="stack"><thead><tr><th>Даты</th><th>Идея</th><th class="num">Выход</th><th>Причина</th><th class="num">Итог</th></tr></thead><tbody>{cls}</tbody></table>' if cls else '<p class="empty">Пока ни одна идея не закрыта.</p>'}
{f'<h2 style="margin-top:20px">Какие сигналы работают</h2><table><thead><tr><th>Главный сигнал</th><th class="num">Идей</th><th class="num">В плюсе</th><th class="num">Средний итог</th></tr></thead><tbody>{drv}</tbody></table>' if drv else ''}
</div></div><p class="note">Итог: для опционов — изменение премии, для акций — движение цены в сторону идеи. Идеи закрываются по тейку, стопу или дате выхода.</p></section>
<details class="more legend" style="margin-top:32px"><summary>Как читать бриф</summary>
<p><b>Сила сигнала, 0–100</b>Насколько согласны тренд, приток денег в опционы, необычный объём и вчерашний поток, закрепившийся в OI. От 55 идея попадает в бриф, от 65 приходит дневным алертом, от 70 сигнал сильный. Если бумага сильнее рынка, а идея на падение (или наоборот), сила снижается вдвое: такая идея — ставка на рынок, а не на бумагу.</p>
<p><b>Цель и стоп по акциям</b>Цель — ожидаемое движение за горизонт идеи по большей из волатильностей: подразумеваемой (IV30) и фактической за 20 дней. Стоп — половина пути, но не ближе 1 ATR. От 60% годовой волатильности идея помечена ⚠.</p>
<p><b>Опционы</b>Тейк +100% к премии, стоп −50%, выход не позже дня перед экспирацией. Вероятность прибыли — шанс оказаться за безубытком к экспирации по Блэку — Шоулзу.</p>
<p><b>Чего сигналы не знают</b>Рост OI не показывает, кто купил, а кто продал. Верить стоит статистике журнала после 50–100 закрытых идей. Аналитика, не инвестиционный совет.</p>
</details>
{f'<details class="more"><summary>Ошибки загрузки ({len(b["errors"])})</summary><ul class="note">{errs}</ul></details>' if errs else ''}
<p class="note">Сгенерировано {E(b['generated'])} UTC.</p></main>
<script>{JS}</script></body></html>""".replace("{FAV}", _fav())


# ---------------- Telegram (parse_mode=HTML), kept short: 2 lines per idea

def _tg_option(r, as_of):
    p, s = r["option"], r["s"]
    r_ = "колл" if p["right"] == "call" else "пут"
    k = f"{p['strike']:g}/{p['short_strike']:g}" if p["type"] == "spread" else f"{p['strike']:g}"
    kind = f"{r_}-спред" if p["type"] == "spread" else r_
    rep = " ↺" if r.get("option_open_since") else ""
    return (f"{'🟢' if s['side'] == 'bull' else '🔴'} <b>{E(r['ticker'])}</b> {kind} {k} до {_exp(p['exp'])} · ${p['cost_usd']:,.0f}\n"
            f"<i>{E(r.get('why', ''))}</i> · б/у {_pct(_be(p))} · сила {r['option_score']:.0f}{rep}")


def _tg_stock(r, as_of):
    p, s = r["stock"], r["s"]
    bull = s["side"] == "bull"
    rep = " ↺" if r.get("stock_open_since") else ""
    return (f"{'🟢' if bull else '🔴'} <b>{E(r['ticker'])}</b> {'лонг' if bull else 'шорт'} ${p['entry']:,.2f} → "
            f"🎯 цель ${p['target']:,.2f} ({_pct(p['target_pct'] * (1 if bull else -1), 0)}) · 🛑 стоп ${p['stop']:,.2f}\n"
            f"<i>{E(r.get('why', ''))}</i> · сила {s['stock_score']:.0f} · до {_date(p['exit_by'])}"
            f"{' ⚠️' if p.get('high_vol') else ''}{rep}")


def _tg_closed(c):
    r = c["result_r"]
    return f"{'✅' if r > 0 else '❌'} {E(c['ticker'])} {_pct(r)} · {E(c['exit_reason'])}"


def _tg_head(b, title):
    tag = " · ДЕМО" if b["provider"] == "demo" else ""
    tag += " · ТЕСТ" if b.get("test") else ""
    return f"{title} · {_date(b['as_of'])}{tag}"


def _tg_today_events(b):
    evs = [e for e in (b.get("macro") or {}).get("events", []) if e["day"] == b["as_of"] and e["imp"] == "high"]
    return ("📅 " + ", ".join(f"{e['mad']} {E(e['name'])}" for e in evs[:3])) if evs else None


def render_text(b: dict, weekly: bool = False) -> str:
    as_of = b["as_of"]
    rg = (b.get("macro") or {}).get("regime") or {}
    n = len(b["options"]) + len(b["stocks"])
    head = f"🦅 <b>{_tg_head(b, 'Falco Scout')}</b>\n" + (f"Вижу {n} {_plural(n, 'цель', 'цели', 'целей')}" if n else "Целей нет — кружу")
    if rg.get("label"):
        head += f" · рынок: {E(rg['label'].lower())}" + (f", VIX {rg['vix']:.1f}" if rg.get("vix") is not None else "")
    L = [head]
    ev = _tg_today_events(b)
    if ev:
        L.append(ev)
    if b["options"]:
        L += ["", "<b>ОПЦИОНЫ</b>"]
        for r in b["options"]:
            L += ["", _tg_option(r, as_of)]
    if b["stocks"]:
        L += ["", "<b>АКЦИИ</b>"]
        for r in b["stocks"]:
            L += ["", _tg_stock(r, as_of)]
    if not b["options"] and not b["stocks"]:
        L += ["", f"Ни одна бумага не набрала силу {b.get('min_score', 55)}: лучше не торговать."]
        if b.get("near"):
            L.append("Ближе всех: " + ", ".join(
                f"{E(r['ticker'])} {'▲' if r['s']['side'] == 'bull' else '▼'} {max(r.get('option_score', 0), r['s']['stock_score']):.0f}"
                for r in b["near"]))
    res = [_tg_closed(c) for c in b["closed_today"]]
    if b["open"]:
        pos = [o["pnl"] for o in b["open"] if o.get("pnl") is not None]
        res.append(f"⏳ в работе {len(b['open'])}" + (f", в плюсе {sum(1 for x in pos if x > 0)}" if pos else ""))
    if res:
        L += ["", "<b>Итоги</b>"] + res
    if weekly:
        L += ["", render_weekly(b)]
    return "\n".join(L)


def render_weekly(b: dict) -> str:
    wk = b.get("week_closed") or []
    if not wk:
        return "🗓 <b>Охота за неделю</b>: ни одна идея не закрылась."
    rs = [c["result_r"] for c in wk]
    best, worst = max(wk, key=lambda c: c["result_r"]), min(wk, key=lambda c: c["result_r"])
    return (f"🗓 <b>Охота за неделю</b>: закрыто {len(wk)}, в плюсе {sum(1 for x in rs if x > 0)}, средний {_pct(sum(rs) / len(rs))}\n"
            f"лучшая {E(best['ticker'])} {_pct(best['result_r'])} · худшая {E(worst['ticker'])} {_pct(worst['result_r'])}")


def render_alert(b: dict, ny_time: str) -> str | None:
    """Intraday: only what changed — new strong ideas and closed ones."""
    new = b.get("new_ideas") or []
    if not new and not b["closed_today"]:
        return None
    L = [f"🦅 <b>{_tg_head(b, 'Пикирую')} · {ny_time} NY</b>"]
    for x in new:
        L += ["", _tg_option(x["row"], "") if x["kind"] == "option" else _tg_stock(x["row"], "")]
    if b["closed_today"]:
        L += ["", "<b>Закрылись</b>"] + [_tg_closed(c) for c in b["closed_today"]]
    return "\n".join(L)
