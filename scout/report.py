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


def _scan_row(r):
    m, s = r["m"], r["s"]
    ch = m["price"] / m["prev_close"] - 1 if m.get("prev_close") else None
    em = next(iter(m["em"].values()), None) if m.get("em") else None
    earn = f"{_exp(m['earnings'])} ({m['earnings_days']} дн.)" if m.get("earnings") and m["earnings_days"] is not None and m["earnings_days"] >= 0 else "—"
    flow = f"{_usd(m['new_call_prem'])} / {_usd(m['new_put_prem'])}" if m["has_prev"] else "нет вчерашних данных"
    return f"""<tr><td><b>{E(r['ticker'])}</b></td><td class="num">${m['price']:,.2f}</td>
<td class="num {'up' if (ch or 0) >= 0 else 'dn'}">{'—' if ch is None else _pct(ch)}</td>
<td class="num {'up' if s['direction'] >= 0 else 'dn'}">{s['direction']:+.2f}</td>
<td class="num">{max(r.get('option_score', 0), s['stock_score']):.0f}</td>
<td class="num">{_p(m['iv30'], 0)}</td><td class="num">{_n(m['iv_rank'], 0) if m['iv_rank'] is not None else '—'}</td>
<td class="num">{_n(m['iv_hv'])}</td><td class="num">{_p(em)}</td><td class="num">{_n(m['pcr_oi'])}</td>
<td class="num">{flow}</td><td class="num">{_usd(m['unusual_premium'])}</td>
<td class="num">{_n(m['put_wall'], 1)} / {_n(m['call_wall'], 1)}</td><td>{earn}</td></tr>"""


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


CSS = """
/* VOICE: audit desk — sober, figure-first, nothing decorative
   IDEA: a morning trading sheet a desk head prints before the bell
   PICTURE: signal map — every ticker placed by direction and score
   COLOUR and TYPE: white, ink, one yellow slab on the track record; Manrope
   LAYOUT: map + key figures first, then ideas, then the full scan and journal */
:root{color-scheme:light dark;--bg:light-dark(#fff,#101418);--ink:light-dark(#101418,#e9edf1);--mut:light-dark(#5b6672,#97a3ae);
--line:light-dark(#e3e7eb,#262d34);--card:light-dark(#f6f8f9,#161c22);--y:#ffd84a;--up:light-dark(#0f7a47,#4cc38a);--dn:light-dark(#c2321f,#ff7a66)}
:root[data-theme=light]{color-scheme:light}:root[data-theme=dark]{color-scheme:dark}
*{box-sizing:border-box;min-width:0}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 Manrope,system-ui,sans-serif;overflow-x:clip}
.band{padding:clamp(22px,4vw,56px) max(5vw,16px);max-width:1240px;margin:0 auto}
h1{font-size:clamp(30px,4.6vw,48px);line-height:1.05;margin:0 0 10px;text-wrap:balance;font-weight:700}
h2{font-size:24px;margin:0 0 6px}h3{font-size:22px;margin:0}
.sub{color:var(--mut);margin:0}.demo{display:inline-block;background:var(--ink);color:var(--bg);padding:2px 10px;border-radius:4px;font-size:13px;font-weight:700}
.top{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:28px;margin-top:22px}
.fig{position:relative;min-height:360px;border:1px solid var(--line);border-radius:10px}.fig>svg{position:absolute;inset:0;width:100%;height:100%}
.slab{background:var(--y);color:#101418;border-radius:10px;padding:20px 22px}
.big{font-size:clamp(40px,6vw,56px);font-weight:700;line-height:1}.slab p{margin:6px 0 0}
.mk{margin-top:16px;border-top:1px solid var(--line)}.mk div{display:flex;justify-content:space-between;gap:10px;padding:10px 0;border-bottom:1px solid var(--line)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,360px),1fr));gap:18px;margin-top:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px}
.card header{display:flex;align-items:center;gap:10px}.score{margin-left:auto;color:var(--mut)}.score b{font-size:22px;color:var(--ink)}
.tag{font-size:13px;font-weight:700;padding:2px 8px;border-radius:4px;white-space:nowrap}.tag.bull{background:color-mix(in srgb,var(--up) 18%,transparent);color:var(--up)}
.tag.bear{background:color-mix(in srgb,var(--dn) 18%,transparent);color:var(--dn)}
.trade{font-weight:700;font-size:17px;margin:12px 0 2px}.cost{color:var(--mut);margin:0 0 12px;font-size:14px}
.move .lbl{font-size:14px}.bar{position:relative;height:10px;border-radius:5px;background:var(--line);margin:6px 0 12px}
.bar .em{position:absolute;inset:0 auto 0 0;background:color-mix(in srgb,var(--up) 45%,transparent);border-radius:5px}
.bar .be{position:absolute;top:-4px;width:3px;height:18px;background:var(--ink);transform:translateX(-1px)}
.kv{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px 16px;margin:0}.kv dt{font-size:13px;color:var(--mut)}.kv dd{margin:0;font-weight:700;white-space:nowrap}
.why{margin:8px 0 0;padding-left:18px;font-size:14px}.why1{margin:8px 0 0;font-size:15px;color:var(--mut)}
details{margin-top:12px;font-size:14px}summary{cursor:pointer;color:var(--mut)}
.legend{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,280px),1fr));gap:14px 28px;margin-top:12px}.legend b{display:block}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:13px;color:var(--mut);font-weight:600;white-space:nowrap}.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.nw{white-space:nowrap}.warn{font-size:14px;margin:12px 0 0;padding:8px 10px;border-radius:6px;background:color-mix(in srgb,var(--y) 30%,transparent)}.up{color:var(--up)}.dn{color:var(--dn)}.scroll{overflow-x:auto}
.avoid li{margin:4px 0}.note{font-size:13px;color:var(--mut)}.empty{color:var(--mut);padding:14px 0}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:28px}
@media(max-width:820px){.top,.two{grid-template-columns:minmax(0,1fr)}}
@media(max-width:600px){table{font-size:13px}.stack thead{display:none}.stack tr{display:grid;padding-block:10px}
.stack td{display:flow-root;border:0;padding:3px 0;padding-inline-start:8em;text-align:start}
.stack td::before{content:attr(data-l);float:inline-start;width:7.5em;margin-inline-start:-8em;white-space:normal;color:var(--mut)}.stack td:empty{display:none}}
"""

JS = """{
const pts=JSON.parse(document.getElementById('pts').textContent);const s=document.getElementById('map');
const esc=t=>String(t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const draw=()=>{const W=s.clientWidth,H=s.clientHeight,p={l:34,r:14,t:30,b:44};const iw=W-p.l-p.r,ih=H-p.t-p.b;
const X=d=>p.l+(d+1)/2*iw,Y=v=>p.t+(1-v/100)*ih;let g='';
g+=`<rect x="${X(0)}" y="${p.t}" width="${iw/2}" height="${ih}" fill="var(--up)" opacity=".06"/><rect x="${p.l}" y="${p.t}" width="${iw/2}" height="${ih}" fill="var(--dn)" opacity=".06"/>`;
for(const v of [0,40,70,100]){g+=`<line x1="${p.l}" x2="${W-p.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text x="${p.l-6}" y="${Y(v)+4}" text-anchor="end" font-size="12" fill="var(--mut)">${v}</text>`}
g+=`<line x1="${X(0)}" x2="${X(0)}" y1="${p.t}" y2="${H-p.b}" stroke="var(--mut)" stroke-dasharray="3 3"/>`;
g+=`<text x="${p.l+4}" y="18" font-size="13" fill="var(--dn)" font-weight="700">← на падение</text><text x="${W-p.r-4}" y="18" text-anchor="end" font-size="13" fill="var(--up)" font-weight="700">на рост →</text>`;
g+=`<text x="${X(0)}" y="${H-8}" text-anchor="middle" font-size="12" fill="var(--mut)">направление сигнала; по вертикали — сила сигнала</text>`;
const used=pts.map(q=>{const x=X(q.d),y=Y(q.v);return [x-6,y-6,x+6,y+6]});for(const q of [...pts].sort((a,b)=>b.pick-a.pick||b.v-a.v)){const x=X(q.d),y=Y(q.v);const pick=q.pick;
g+=`<circle cx="${x}" cy="${y}" r="${pick?7:5}" fill="${q.d>=0?'var(--up)':'var(--dn)'}" ${pick?'stroke="var(--ink)" stroke-width="2"':'opacity=".55"'}/>`;
const w=q.t.length*7.5+4;const opts=[[x,y-11,'middle'],[x,y+19,'middle'],[x+10,y+4,'start'],[x-10,y+4,'end'],[x,y-25,'middle'],[x,y+33,'middle']];
const box=o=>{const x0=o[2]==='middle'?o[0]-w/2:o[2]==='start'?o[0]:o[0]-w;return [x0,o[1]-11,x0+w,o[1]+2]};
const hit=b=>used.some(u=>b[0]<u[2]&&b[2]>u[0]&&b[1]<u[3]&&b[3]>u[1])||b[0]<p.l||b[2]>W-p.r;
const o=opts.find(o=>!hit(box(o)));
if(o&&(W>360||pick)){used.push(box(o));g+=`<text x="${o[0]}" y="${o[1]}" text-anchor="${o[2]}" font-size="12" font-weight="${pick?700:500}" fill="var(--ink)">${esc(q.t)}</text>`}}
s.innerHTML=g};const ro=new ResizeObserver(draw);ro.observe(s);
for(const c of document.querySelectorAll('.stack td:not([data-l])')){let i=0,p=c;while(p=p.previousElementSibling)i+=p.colSpan;c.dataset.l=c.closest('table').rows[0].cells[i]?.textContent||''}
}"""


def render_html(b: dict) -> str:
    demo, test, as_of = b["provider"] == "demo", b.get("test"), b["as_of"]
    picks = {r["ticker"] for r in b["options"]} | {r["ticker"] for r in b["stocks"]}
    pts = [{"t": r["ticker"], "d": round(r["s"]["direction"], 3),
            "v": round(max(r.get("option_score", 0), r["s"]["stock_score"]), 1), "pick": r["ticker"] in picks}
           for r in b["scanner"]]
    st, st30 = b["stats_all"]["all"], b["stats_30"]["all"]
    if st30["n"]:
        slab = (f"<div class='big'>{_pct(st30['avg_r'])}</div><p>средний результат закрытых идей за 30 дней "
                f"· {st30['n']} идей · {st30['win'] * 100:.0f}% в плюсе</p>")
    else:
        slab = "<div class='big'>0 закрытых</div><p>результаты появятся, когда закроются первые идеи</p>"
    if b["open"]:
        pos = [o["pnl"] for o in b["open"] if o.get("pnl") is not None]
        slab += f"<p>Открыто {len(b['open'])} идей" + (f", в плюсе {sum(1 for x in pos if x > 0)}" if pos else "") + "</p>"
    mk = "".join(
        f"<div><span><b>{E(r['ticker'])}</b> {'тренд вверх' if r['m']['trend'] > 0.2 else 'тренд вниз' if r['m']['trend'] < -0.2 else 'без тренда'}</span>"
        f"<span class='num'>IV {_p(r['m']['iv30'], 0)} · 5 дн. {_pct(r['m']['ret5'])}</span></div>" for r in b["market"])
    title = (f"{len(b['options'])} опционных и {len(b['stocks'])} акционных идей по вотчлисту"
             if b["options"] or b["stocks"] else "Сегодня сильных сигналов нет: лучшая сделка — не торговать")
    cards = "".join(_option_card(r, as_of) for r in b["options"]) or "<p class='empty'>Нет опционов, прошедших фильтры: цена до $100, безубыток в пределах ожидаемого движения, ликвидность.</p>"
    stocks = "".join(_stock_card(r, as_of) for r in b["stocks"]) or "<p class='empty'>Нет акций выше порога.</p>"
    avoid = "".join(f"<li><b>{E(a['ticker'])}</b> — {E(a['why'])}</li>" for a in b["avoid"]) or "<li>Нет</li>"
    scan = "".join(_scan_row(r) for r in b["scanner"])
    opn = "".join(_open_row(r) for r in b["open"])
    cls = "".join(_closed_row(r) for r in b["recent_closed"])
    drv = "".join(f"<tr><td>{E(NAMES.get(k, k))}</td><td class='num'>{v['n']}</td><td class='num'>{v['win'] * 100:.0f}%</td><td class='num'>{_pct(v['avg_r'])}</td></tr>"
                  for k, v in sorted(b["stats_all"]["driver"].items(), key=lambda kv: -kv[1]["n"]) if v["n"])
    errs = "".join(f"<li>{E(e['ticker'])}: {E(e['error'])}</li>" for e in b["errors"])
    pts_json = json.dumps(pts).replace("<", "\\u003c")
    badge = ('<span class="demo">демо-данные, не рыночные</span>' if demo else '') + \
            ('<span class="demo">тестовый запуск, в журнал не записан</span>' if test else '')
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Options Scout: бриф</title><link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&display=swap" rel="stylesheet"><style>{CSS}</style></head><body>
<section class="band">
<p class="sub">Options Scout · данные на {E(as_of)} · источник: {E(b['provider'])} {badge}</p>
<h1>{E(title)}</h1>
<div class="top"><div class="fig"><svg id="map" role="img" aria-label="Карта сигналов по тикерам"></svg></div>
<div><div class="slab">{slab}</div><div class="mk">{mk}</div></div></div>
</section>
<section class="band"><h2>Опционы</h2><p class="sub">Дешёвые недельные контракты, где безубыток не дальше ожидаемого движения. Цена указана за 1 контракт (100 акций).</p>
<div class="cards">{cards}</div></section>
<section class="band"><h2>Акции</h2><p class="sub">Идея на одну акцию: сколько брать, решаете вы. Цель — ожидаемое движение за горизонт идеи, стоп — половина этого пути, но не ближе дневного шума.</p>
<div class="cards">{stocks}</div>
<h3 style="margin-top:28px;font-size:18px">Не покупать опционы</h3><ul class="avoid">{avoid}</ul></section>
<section class="band"><h2>Как отработали прошлые идеи</h2><p class="sub">Каждая идея записывается автоматически и закрывается по тейку, стопу или дате выхода. Результат: для опционов — изменение премии, для акций — движение цены в сторону идеи.</p>
<div class="two" style="margin-top:14px"><div><h3 style="font-size:18px">Открытые</h3>
{f'<div class="scroll"><table class="stack"><thead><tr><th>Дата</th><th>Идея</th><th class="num">Сейчас</th><th class="num">Итог</th><th>План</th></tr></thead><tbody>{opn}</tbody></table></div>' if opn else '<p class="empty">Нет открытых идей.</p>'}
</div><div><h3 style="font-size:18px">Закрытые</h3>
{f'<div class="scroll"><table class="stack"><thead><tr><th>Даты</th><th>Идея</th><th class="num">Выход</th><th>Причина</th><th class="num">Итог</th></tr></thead><tbody>{cls}</tbody></table></div>' if cls else '<p class="empty">Пока ни одна идея не закрыта.</p>'}
{f'<h3 style="margin-top:20px;font-size:18px">Какие сигналы работают</h3><div class="scroll"><table><thead><tr><th>Главный сигнал</th><th class="num">Идей</th><th class="num">В плюсе</th><th class="num">Средний итог</th></tr></thead><tbody>{drv}</tbody></table></div>' if drv else ''}
</div></div></section>
<section class="band"><h2>Сканер вотчлиста</h2><p class="sub">Направление от −1 (на падение) до +1 (на рост). Новый OI: прирост открытого интереса к прошлой сессии, в долларах премии, колы / путы.</p>
<div class="scroll"><table><thead><tr><th>Тикер</th><th class="num">Цена</th><th class="num">День</th><th class="num">Напр.</th><th class="num">Сила</th>
<th class="num">IV30</th><th class="num">IV Rank</th><th class="num">IV/HV</th><th class="num">Ожид. движ.</th><th class="num">P/C OI</th><th class="num">Новый OI К/П</th><th class="num">Необычн.</th><th class="num">Путы / колы, стены</th><th>Отчёт</th></tr></thead>
<tbody>{scan}</tbody></table></div></section>
<section class="band"><h2>Как читать</h2><div class="legend">
<p><b>Сила сигнала, 0–100</b>Насколько согласны между собой тренд, приток денег в опционы, необычный объём и вчерашний поток, закрепившийся в OI. От 40 идея попадает в бриф, от 55 приходит дневным алертом, от 70 сигнал сильный.</p>
<p><b>Цель и стоп по акциям</b>Цель — ожидаемое движение за горизонт идеи по волатильности: берётся большая из подразумеваемой (IV30) и фактической за 20 дней. Стоп — половина пути до цели, но не ближе 1 ATR, чтобы его не выбило обычным дневным шумом. У бумаг с волатильностью от 60% годовых стоп получается широким, такие идеи помечены ⚠.</p>
<p><b>Опционы</b>Тейк +100% к премии, стоп −50%, выход не позже дня перед экспирацией. Вероятность прибыли — шанс оказаться за безубытком к экспирации по модели Блэка — Шоулза.</p>
<p><b>Чего сигналы не знают</b>Рост OI не показывает, кто купил, а кто продал: это вероятность, а не факт. Верить стоит статистике журнала после 50–100 закрытых идей. Аналитика, не инвестиционный совет.</p>
</div>
{f'<p class="note">Ошибки загрузки:</p><ul class="note">{errs}</ul>' if errs else ''}<p class="note">Сгенерировано {E(b['generated'])} UTC.</p></section>
<script type="application/json" id="pts">{pts_json}</script><script>{JS}</script></body></html>"""


# ---------------- Telegram (parse_mode=HTML)

def _tg_option(r, as_of):
    p, s = r["option"], r["s"]
    r_ = "колл" if p["right"] == "call" else "пут"
    k = f"{p['strike']:g}/{p['short_strike']:g}" if p["type"] == "spread" else f"{p['strike']:g}"
    kind = f"{r_}-спред" if p["type"] == "spread" else r_
    since = _since_note(r.get("option_open_since"), as_of)
    return (f"{'🟢' if s['side'] == 'bull' else '🔴'} <b>{E(r['ticker'])}</b> {kind} {k} до {_exp(p['exp'])} · "
            f"<b>${p['cost_usd']:,.0f}</b> за контракт\n"
            f"    <i>{E(r.get('why', ''))}</i>\n"
            f"    безубыток {_pct(_be(p))} при ожидаемом ±{_pct(p['em_pct'], sign=False)} · сила {r['option_score']:.0f}"
            + (f"\n    ↺ {since}" if since else ""))


def _tg_stock(r, as_of):
    p, s = r["stock"], r["s"]
    bull = s["side"] == "bull"
    since = _since_note(r.get("stock_open_since"), as_of)
    return (f"{'🟢' if bull else '🔴'} <b>{E(r['ticker'])}</b> {'покупка' if bull else 'шорт'} от ${p['entry']:,.2f} · до {_date(p['exit_by'])}\n"
            f"    цель ${p['target']:,.2f} ({_pct(p['target_pct'] * (1 if bull else -1))}) · "
            f"стоп ${p['stop']:,.2f} ({_pct(p['stop_pct'] * (-1 if bull else 1))})\n"
            f"    <i>{E(r.get('why', ''))}</i> · сила {s['stock_score']:.0f}"
            + (f"\n    ⚠️ высокая волатильность ({p['vol'] * 100:.0f}% год.): стоп широкий" if p.get("high_vol") else "")
            + (f"\n    ↺ {since}" if since else ""))


def _tg_closed(c):
    r = c["result_r"]
    return f"{'✅' if r > 0 else '❌'} {E(idea_label(c))} (с {_date(c['as_of'])}): <b>{_pct(r)}</b>, {E(c['exit_reason'])}"


def _tg_head(b, title):
    tag = " · ДЕМО" if b["provider"] == "demo" else ""
    tag += " · ТЕСТ, не в журнале" if b.get("test") else ""
    return f"{title} · {_date(b['as_of'])}{tag}"


LEGEND = "<i>Сила 0–100: насколько согласны тренд, поток опционов и объём. 40+ в брифе, 55+ дневной алерт, 70+ сильный сигнал.</i>"


def render_text(b: dict, weekly: bool = False) -> str:
    as_of = b["as_of"]
    L = [f"📊 <b>{_tg_head(b, 'Options Scout')}</b>"]
    if b["options"]:
        L += ["", "<b>ОПЦИОНЫ</b>"] + [_tg_option(r, as_of) for r in b["options"]]
    if b["stocks"]:
        L += ["", "<b>АКЦИИ</b> (идея на 1 акцию)"] + [_tg_stock(r, as_of) for r in b["stocks"]]
    if not b["options"] and not b["stocks"]:
        L += ["", "Сильных сигналов нет: лучшая сделка сегодня — не торговать."]
    res = [_tg_closed(c) for c in b["closed_today"]]
    if b["open"]:
        pos = [o["pnl"] for o in b["open"] if o.get("pnl") is not None]
        line = f"⏳ В работе {len(b['open'])} идей"
        if pos:
            line += f": в плюсе {sum(1 for x in pos if x > 0)}, средний итог {_pct(sum(pos) / len(pos))}"
        res.append(line)
    if res:
        L += ["", "<b>ИТОГИ ИДЕЙ</b>"] + res
    st = b["stats_30"]["all"]
    if st["n"]:
        L.append(f"За 30 дней: {st['n']} закрыто, {st['win'] * 100:.0f}% в плюсе, средний итог {_pct(st['avg_r'])}")
    if weekly:
        L += ["", render_weekly(b)]
    L += ["", LEGEND]
    return "\n".join(L)


def render_weekly(b: dict) -> str:
    wk = b.get("week_closed") or []
    L = ["🗓 <b>ИТОГИ НЕДЕЛИ</b>"]
    if not wk:
        L.append("За неделю ни одна идея не закрылась.")
        return "\n".join(L)
    rs = [c["result_r"] for c in wk]
    L.append(f"Закрыто {len(wk)}: в плюсе {sum(1 for x in rs if x > 0)}, средний итог {_pct(sum(rs) / len(rs))}")
    best, worst = max(wk, key=lambda c: c["result_r"]), min(wk, key=lambda c: c["result_r"])
    L.append(f"Лучшая: {E(idea_label(best))} {_pct(best['result_r'])}")
    if worst is not best:
        L.append(f"Худшая: {E(idea_label(worst))} {_pct(worst['result_r'])}")
    return "\n".join(L)


def render_alert(b: dict, ny_time: str) -> str | None:
    """Intraday: only what changed — new strong ideas and closed ones."""
    as_of = b["as_of"]
    new = b.get("new_ideas") or []
    if not new and not b["closed_today"]:
        return None
    L = [f"⚡ <b>{_tg_head(b, 'Дневной алерт')} · {ny_time} NY</b>"]
    if new:
        L += ["", "<b>НОВЫЕ ИДЕИ</b>"]
        L += [_tg_option(x["row"], "") if x["kind"] == "option" else _tg_stock(x["row"], "") for x in new]
    if b["closed_today"]:
        L += ["", "<b>ЗАКРЫЛИСЬ</b>"] + [_tg_closed(c) for c in b["closed_today"]]
    L += ["", LEGEND]
    return "\n".join(L)
