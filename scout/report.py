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


def structure(p: dict, ticker: str) -> str:
    r = "колл" if p["right"] == "call" else "пут"
    if p["type"] == "spread":
        return (f"Купить {p['contracts']}× дебетовый {r}-спред {ticker} {p['strike']:g}/{p['short_strike']:g}, "
                f"эксп. {_exp(p['exp'])}, за ${p['entry']:.2f}")
    return f"Купить {p['contracts']}× {ticker} {p['strike']:g} {r}, эксп. {_exp(p['exp'])}, по ${p['entry']:.2f}"


def _option_card(r):
    p, s, m = r["option"], r["s"], r["m"]
    em_w = min(100, p["em_pct"] / max(p["em_pct"], p["req_move_pct"], 1e-9) * 100)
    be_w = min(100, max(0, p["req_move_pct"]) / max(p["em_pct"], p["req_move_pct"], 1e-9) * 100)
    extra = (f"<div><dt>Макс. прибыль</dt><dd>${p['max_profit_usd']:,.0f}</dd></div>" if p["type"] == "spread" else "")
    reasons = "".join(f"<li>{E(x)}</li>" for x in s["reasons"])
    return f"""<article class="card">
<header><h3>{E(r['ticker'])}</h3><span class="tag {s['side']}">{SIDE[s['side']]}</span>
<span class="score"><b>{r['option_score']:.0f}</b>/100</span></header>
<p class="trade">{E(structure(p, r['ticker']))}</p>
<p class="cost">Стоимость ${p['cost_usd'] * p['contracts']:,.0f} — это и есть максимальный убыток</p>
<div class="move"><div class="lbl">Нужно до безубытка <b>{_p(p['req_move_pct'])}</b> · ожидаемое движение рынка <b>{_p(p['em_pct'])}</b></div>
<div class="bar"><i class="em" style="width:{em_w:.0f}%"></i><i class="be" style="left:{be_w:.0f}%"></i></div></div>
<dl class="kv">
<div><dt>Цена акции</dt><dd>${m['price']:,.2f}</dd></div>
<div><dt>Безубыток</dt><dd>${p['breakeven']:,.2f}</dd></div>
<div><dt>Вероятность прибыли</dt><dd>{_p(p['pop'], 0)}</dd></div>
<div><dt>Дельта</dt><dd>{p['delta']:+.2f}</dd></div>
<div><dt>Тейк / стоп</dt><dd>${p['target']:.2f} / ${p['stop']:.2f}</dd></div>
<div><dt>До экспирации</dt><dd>{p['dte']} дн.</dd></div>{extra}
</dl>
<ul class="why">{reasons}</ul>
<p class="drv">Главный сигнал: {E(s['driver_name'])}</p>
</article>"""


def _stock_row(r):
    p, s, m = r["stock"], r["s"], r["m"]
    act = "Купить" if s["side"] == "bull" else "Шорт"
    return f"""<tr><td><b>{E(r['ticker'])}</b> <span class="tag {s['side']}">{SIDE[s['side']]}</span></td>
<td class="num">{s['stock_score']:.0f}</td><td>{act} {p['shares']} шт. по ${p['entry']:,.2f}</td>
<td class="num">${p['stop']:,.2f}</td><td class="num">${p['target']:,.2f}</td><td class="num">${p['risk_usd']:,.0f}</td>
<td>{E(s['reasons'][0] if s['reasons'] else '')}</td></tr>"""


def _scan_row(r):
    m, s = r["m"], r["s"]
    ch = m["price"] / m["prev_close"] - 1 if m.get("prev_close") else None
    em = next(iter(m["em"].values()), None) if m.get("em") else None
    earn = f"{_exp(m['earnings'])} ({m['earnings_days']} дн.)" if m.get("earnings") and m["earnings_days"] is not None and m["earnings_days"] >= 0 else "—"
    flow = f"{_usd(m['new_call_prem'])} / {_usd(m['new_put_prem'])}" if m["has_prev"] else "нет вчерашних данных"
    return f"""<tr><td><b>{E(r['ticker'])}</b></td><td class="num">${m['price']:,.2f}</td>
<td class="num {'up' if (ch or 0) >= 0 else 'dn'}">{'—' if ch is None else f'{ch:+.1%}'}</td>
<td class="num {'up' if s['direction'] >= 0 else 'dn'}">{s['direction']:+.2f}</td>
<td class="num">{r.get('option_score', 0):.0f}</td><td class="num">{s['stock_score']:.0f}</td>
<td class="num">{_p(m['iv30'], 0)}</td><td class="num">{_n(m['iv_rank'], 0) if m['iv_rank'] is not None else '—'}</td>
<td class="num">{_n(m['iv_hv'])}</td><td class="num">{_p(em)}</td><td class="num">{_n(m['pcr_oi'])}</td>
<td class="num">{flow}</td><td class="num">{_usd(m['unusual_premium'])}</td>
<td class="num">{_n(m['put_wall'], 1)} / {_n(m['call_wall'], 1)}</td><td>{earn}</td></tr>"""


def _open_row(rec):
    p = rec["plan"]
    cur = rec.get("current")
    if p["type"] == "stock":
        what = f"{'Лонг' if p['side'] == 'bull' else 'Шорт'} {p['shares']} шт."
        chg = None if cur is None else (cur - p["entry"]) / abs(p["entry"] - p["stop"]) * (1 if p["side"] == "bull" else -1)
    else:
        what = structure(p, rec["ticker"])
        chg = None if cur is None else (cur - p["entry"]) / p["entry"]
    cls = "" if chg is None else ("up" if chg >= 0 else "dn")
    return (f"<tr><td>{E(rec['as_of'][5:])}</td><td><b>{E(rec['ticker'])}</b></td><td>{E(what)}</td>"
            f"<td class='num'>{_n(p['entry'])}</td><td class='num'>{_n(cur)}</td>"
            f"<td class='num {cls}'>{'—' if chg is None else f'{chg:+.2f}R'}</td></tr>")


def _closed_row(rec):
    r = rec["result_r"]
    return (f"<tr><td>{E(rec['exit_date'][5:])}</td><td><b>{E(rec['ticker'])}</b></td>"
            f"<td>{'акция' if rec['kind'] == 'stock' else 'опцион'}, {SIDE[rec['side']]}</td>"
            f"<td>{E(rec['exit_reason'])}</td><td class='num {'up' if r > 0 else 'dn'}'>{r:+.2f}R</td></tr>")


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
.why{margin:12px 0 6px;padding-left:18px;font-size:14px}.drv{font-size:13px;color:var(--mut);margin:0}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:13px;color:var(--mut);font-weight:600;white-space:nowrap}.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.up{color:var(--up)}.dn{color:var(--dn)}.scroll{overflow-x:auto}
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
g+=`<text x="${X(0)}" y="${H-8}" text-anchor="middle" font-size="12" fill="var(--mut)">направление сигнала; по вертикали — лучший скор</text>`;
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
    demo = b["provider"] == "demo"
    picks = {r["ticker"] for r in b["options"]} | {r["ticker"] for r in b["stocks"]}
    pts = [{"t": r["ticker"], "d": round(r["s"]["direction"], 3),
            "v": round(max(r.get("option_score", 0), r["s"]["stock_score"]), 1), "pick": r["ticker"] in picks}
           for r in b["scanner"]]
    st, st30 = b["stats_all"]["all"], b["stats_30"]["all"]
    if st30["n"]:
        slab = (f"<div class='big'>{st30['avg_r']:+.2f}R</div><p>средний результат закрытых идей за 30 дней "
                f"· {st30['n']} сделок · {st30['win'] * 100:.0f}% в плюсе</p>")
    else:
        slab = "<div class='big'>0 сделок</div><p>трек-рекорд появится, когда закроются первые идеи</p>"
    if st["n"]:
        slab += f"<p>За всё время: {st['n']} сделок, сумма {st['sum_r']:+.1f}R</p>"
    mk = "".join(
        f"<div><span><b>{E(r['ticker'])}</b> {'тренд вверх' if r['m']['trend'] > 0.2 else 'тренд вниз' if r['m']['trend'] < -0.2 else 'без тренда'}</span>"
        f"<span class='num'>IV {_p(r['m']['iv30'], 0)} · 5д {r['m']['ret5']:+.1%}</span></div>" for r in b["market"])
    title = (f"{len(b['options'])} опционных и {len(b['stocks'])} акционных идей по вотчлисту"
             if b["options"] or b["stocks"] else "Сегодня сильных сигналов нет: лучшая сделка — не торговать")
    cards = "".join(_option_card(r) for r in b["options"]) or "<p class='empty'>Нет опционов, прошедших фильтры: цена до $100, безубыток в пределах ожидаемого движения, ликвидность.</p>"
    stocks = "".join(_stock_row(r) for r in b["stocks"])
    avoid = "".join(f"<li><b>{E(a['ticker'])}</b> — {E(a['why'])}</li>" for a in b["avoid"]) or "<li>Нет</li>"
    scan = "".join(_scan_row(r) for r in b["scanner"])
    opn = "".join(_open_row(r) for r in b["open"])
    cls = "".join(_closed_row(r) for r in b["recent_closed"])
    drv = "".join(f"<tr><td>{E(NAMES.get(k, k))}</td><td class='num'>{v['n']}</td><td class='num'>{v['win'] * 100:.0f}%</td><td class='num'>{v['avg_r']:+.2f}R</td></tr>"
                  for k, v in sorted(b["stats_all"]["driver"].items(), key=lambda kv: -kv[1]["n"]) if v["n"])
    errs = "".join(f"<li>{E(e['ticker'])}: {E(e['error'])}</li>" for e in b["errors"])
    pts_json = json.dumps(pts).replace("<", "\\u003c")
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Options Scout: бриф</title><link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&display=swap" rel="stylesheet"><style>{CSS}</style></head><body>
<section class="band">
<p class="sub">Options Scout · данные на {E(b['as_of'])} · источник: {E(b['provider'])} {'<span class="demo">демо-данные, не рыночные</span>' if demo else ''}</p>
<h1>{E(title)}</h1>
<div class="top"><div class="fig"><svg id="map" role="img" aria-label="Карта сигналов по тикерам"></svg></div>
<div><div class="slab">{slab}</div><div class="mk">{mk}</div></div></div>
</section>
<section class="band"><h2>Опционы: лучшие идеи</h2><p class="sub">Дешёвые недельные контракты, где безубыток не дальше ожидаемого движения. Убыток ограничен ценой контракта.</p>
<div class="cards">{cards}</div></section>
<section class="band two"><div><h2>Акции</h2>
{f'<div class="scroll"><table class="stack"><thead><tr><th>Тикер</th><th class="num">Скор</th><th>Действие</th><th class="num">Стоп</th><th class="num">Цель</th><th class="num">Риск</th><th>Почему</th></tr></thead><tbody>{stocks}</tbody></table></div>' if stocks else '<p class="empty">Нет акций выше порога.</p>'}
</div><div><h2>Не покупать опционы</h2><ul class="avoid">{avoid}</ul></div></section>
<section class="band"><h2>Сканер вотчлиста</h2><p class="sub">Направление от −1 (на падение) до +1 (на рост). Новый OI: прирост открытого интереса к прошлой сессии, в долларах премии, колы / путы.</p>
<div class="scroll"><table><thead><tr><th>Тикер</th><th class="num">Цена</th><th class="num">День</th><th class="num">Напр.</th><th class="num">Скор опц.</th><th class="num">Скор акц.</th>
<th class="num">IV30</th><th class="num">IV Rank</th><th class="num">IV/HV</th><th class="num">Ожид. движ.</th><th class="num">P/C OI</th><th class="num">Новый OI К/П</th><th class="num">Необычн.</th><th class="num">Путы / колы, стены</th><th>Отчёт</th></tr></thead>
<tbody>{scan}</tbody></table></div></section>
<section class="band two"><div><h2>Открытые идеи</h2>
{f'<div class="scroll"><table class="stack"><thead><tr><th>Дата</th><th>Тикер</th><th>Позиция</th><th class="num">Вход</th><th class="num">Сейчас</th><th class="num">Итог</th></tr></thead><tbody>{opn}</tbody></table></div>' if opn else '<p class="empty">Нет открытых идей.</p>'}
</div><div><h2>Закрытые</h2>
{f'<div class="scroll"><table class="stack"><thead><tr><th>Дата</th><th>Тикер</th><th>Тип</th><th>Выход</th><th class="num">Итог</th></tr></thead><tbody>{cls}</tbody></table></div>' if cls else '<p class="empty">Пока ни одна идея не закрыта.</p>'}
{f'<h3 style="margin-top:20px;font-size:18px">Какие сигналы работают</h3><div class="scroll"><table><thead><tr><th>Главный сигнал</th><th class="num">Сделок</th><th class="num">В плюсе</th><th class="num">Средний R</th></tr></thead><tbody>{drv}</tbody></table></div>' if drv else ''}
</div></section>
<section class="band note"><p>R для опционов: результат в долях уплаченной премии (−1R = контракт сгорел). Для акций: в долях риска до стопа.
Рост OI не показывает, кто купил, а кто продал: подтверждённый поток — это вероятность, а не факт. Аналитика и сигналы, не инвестиционный совет.</p>
{f'<p>Ошибки загрузки:</p><ul>{errs}</ul>' if errs else ''}<p>Сгенерировано {E(b['generated'])} UTC.</p></section>
<script type="application/json" id="pts">{pts_json}</script><script>{JS}</script></body></html>"""


def render_text(b: dict) -> str:
    lines = [f"Options Scout · {b['as_of']}" + (" (ДЕМО)" if b["provider"] == "demo" else "")]
    for r in b["options"]:
        p = r["option"]
        lines.append(f"• {r['ticker']} [{r['option_score']:.0f}] {structure(p, r['ticker'])}. "
                     f"Безубыток {_p(p['req_move_pct'])} при ожидаемом {_p(p['em_pct'])}, вероятность прибыли {_p(p['pop'], 0)}.")
    for r in b["stocks"]:
        p = r["stock"]
        lines.append(f"• {r['ticker']} акция [{r['s']['stock_score']:.0f}] {SIDE[r['s']['side']]}: вход {p['entry']:.2f}, стоп {p['stop']:.2f}, цель {p['target']:.2f}")
    if not b["options"] and not b["stocks"]:
        lines.append("Сильных сигналов нет.")
    for c in b["closed_today"]:
        lines.append(f"Закрыто: {c['ticker']} {c['exit_reason']} {c['result_r']:+.2f}R")
    st = b["stats_30"]["all"]
    if st["n"]:
        lines.append(f"30 дней: {st['n']} сделок, {st['win'] * 100:.0f}% в плюсе, средний {st['avg_r']:+.2f}R")
    return "\n".join(lines)
