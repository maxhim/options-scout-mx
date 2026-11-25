"""Owner-only admin page, published at /admin/ but encrypted with ADMIN_PASSWORD.

GitHub Pages is public and static, so the page ships only ciphertext (AES-256-GCM, key from the
password via PBKDF2-SHA256, 600k iterations); the browser decrypts it after the password is typed.
A weak password can be brute-forced offline: use a long one.
"""
from __future__ import annotations

import base64
import datetime as dt
import html
import os
from zoneinfo import ZoneInfo

from . import journal, sectors

E = html.escape
ITER = 600_000
MAD = ZoneInfo("Europe/Madrid")


def encrypt(plain: str, password: str) -> dict:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(password.encode())
    ct = AESGCM(key).encrypt(iv, plain.encode(), None)
    b64 = lambda x: base64.b64encode(x).decode()
    return {"salt": b64(salt), "iv": b64(iv), "ct": b64(ct), "iter": ITER}


def _pct(x):
    return "—" if x is None else f"{x * 100:+.1f}%".replace("-", "−")


def _local(ts):
    try:
        return dt.datetime.fromisoformat(ts).astimezone(MAD).strftime("%d.%m %H:%M")
    except Exception:
        return ts


def vix_s(r):
    return f", VIX {r['vix']:.1f}" if r.get("vix") else ""


def body(store, subs: dict | None, owner: str | None, links: dict) -> str:
    subs = (subs or {}).get("subs", {})
    others = {c: s for c, s in subs.items() if c != str(owner)}
    today = dt.date.today()
    new7 = sum(1 for s in others.values() if s.get("since", "") >= (today - dt.timedelta(days=7)).isoformat())
    by_lang = {lg: sum(1 for s in others.values() if s["lang"] == lg) for lg in ("ru", "en")}
    runs = store.runs(60)
    closed, opened = store.closed_recs(), store.open_recs()
    st_all, st30 = journal.stats(closed), journal.stats(closed, (today - dt.timedelta(days=30)).isoformat())

    by_sector: dict = {}
    for c in closed:
        g = sectors.label(sectors.group(c["ticker"])) or "Другое"
        d = by_sector.setdefault(g, [])
        d.append(c["result_r"])
    sector_rows = "".join(
        f"<tr><td>{E(g)}</td><td class=n>{len(v)}</td><td class=n>{sum(1 for x in v if x > 0) / len(v) * 100:.0f}%</td><td class=n>{_pct(sum(v) / len(v))}</td></tr>"
        for g, v in sorted(by_sector.items(), key=lambda kv: -len(kv[1])))
    driver_rows = "".join(
        f"<tr><td>{E(k)}</td><td class=n>{v['n']}</td><td class=n>{v['win'] * 100:.0f}%</td><td class=n>{_pct(v['avg_r'])}</td></tr>"
        for k, v in st_all["driver"].items() if v["n"] and v.get("win") is not None)
    sub_rows = "".join(f"<tr><td>{E(s.get('who') or '— (подписался до учёта имён)')}</td><td>{s['lang']}</td><td>{E(s.get('since', ''))}</td></tr>"
                       for s in sorted(others.values(), key=lambda s: s.get("since", ""), reverse=True))
    growth, cum = [], 0
    for d in sorted({s.get("since", "") for s in others.values()}):
        cum += sum(1 for s in others.values() if s.get("since") == d)
        growth.append(f"<tr><td>{E(d)}</td><td class=n>{cum}</td></tr>")
    run_rows = "".join(
        f"<tr><td>{_local(r['ts'])}</td><td>{E(r['mode'])}</td><td class=n>{r['options']} + {r['stocks']}</td>"
        f"<td class=n>{r['checked']}→{r['liquid']}→{r['deep']}</td><td class=n>{r['errors']}</td>"
        f"<td class=n>{'—' if r['delivered'] is None else r['delivered']}</td><td>{E(r['regime'] or '')}{vix_s(r)}</td></tr>"
        for r in runs)
    lk = " · ".join(f'<a href="{E(u)}" target="_blank" rel="noopener">{E(n)}</a>' for n, u in links.items() if u)
    return f"""<h1>Falco Scout · админка</h1><p class=m>Обновлено {dt.datetime.now(MAD):%d.%m.%Y %H:%M} (Мадрид) · {lk}</p>
<div class=k><div><small>Подписчики</small><b>{len(others)}</b><span>ru {by_lang['ru']} · en {by_lang['en']} · +{new7} за 7 дней</span></div>
<div><small>Запусков записано</small><b>{len(runs)}</b><span>последний {(_local(runs[0]['ts']) if runs else '—')}</span></div>
<div><small>Идеи в журнале</small><b>{len(opened)} / {len(closed)}</b><span>открыто / закрыто</span></div>
<div><small>Итог 30 дней</small><b>{_pct(st30['all']['avg_r']) if st30['all']['n'] else '—'}</b><span>{st30['all']['n']} закрыто{f", {st30['all']['win'] * 100:.0f}% в плюсе" if st30['all']['n'] else ''}</span></div></div>
<h2>Подписчики</h2>{f'<div class=t><table><tr><th>Кто</th><th>Язык</th><th>С</th></tr>{sub_rows}</table></div>' if sub_rows else '<p class=m>Пока никого, кроме тебя.</p>'}
{f'<h2>Рост подписчиков</h2><div class=t><table><tr><th>Дата</th><th class=n>Всего</th></tr>{"".join(growth)}</table></div>' if growth else ''}
<h2>Запуски</h2><p class=m>Режим: brief — вечерний или ручной бриф, alert — дневной алерт. Отбор: проверено → ликвидных → полный разбор.</p>
{f'<div class=t><table><tr><th>Когда</th><th>Режим</th><th class=n>Идеи о+а</th><th class=n>Отбор</th><th class=n>Ошибки</th><th class=n>Доставлено</th><th>Рынок</th></tr>{run_rows}</table></div>' if run_rows else '<p class=m>Запусков ещё не было.</p>'}
<h2>Журнал по секторам</h2>{f'<div class=t><table><tr><th>Сектор</th><th class=n>Идей</th><th class=n>В плюсе</th><th class=n>Средний</th></tr>{sector_rows}</table></div>' if sector_rows else '<p class=m>Пока нет закрытых идей.</p>'}
{f'<h2>Журнал по сигналам</h2><div class=t><table><tr><th>Сигнал</th><th class=n>Идей</th><th class=n>В плюсе</th><th class=n>Средний</th></tr>{driver_rows}</table></div>' if driver_rows else ''}"""


PAGE = """<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Falco Scout · админка</title><style>
:root{color-scheme:dark}body{margin:0;background:#0b1020;color:#e8ecf4;font:15px/1.5 system-ui,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 48px}h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:26px 0 8px}
.m{color:#8b95ad;margin:0 0 8px}a{color:#7c8cff}
.k{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-top:14px}
.k div{background:#121a2e;border:1px solid #222c45;border-radius:12px;padding:12px}.k small{display:block;color:#8b95ad;font-size:12px;text-transform:uppercase}
.k b{display:block;font-size:24px}.k span{color:#8b95ad;font-size:13px}
.t{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:6px 8px;border-bottom:1px solid #222c45;text-align:left}th{color:#8b95ad;font-weight:600}
.n{text-align:right;white-space:nowrap}form{display:flex;gap:8px;margin-top:30vh;justify-content:center}
input,button{font:inherit;padding:10px 12px;border-radius:10px;border:1px solid #222c45;background:#121a2e;color:#e8ecf4}
button{background:#f5a524;color:#141006;border:0;font-weight:700;cursor:pointer}#err{color:#f87171;text-align:center}
</style></head><body><main id="app"><form id="f"><input id="p" type="password" placeholder="Пароль" autocomplete="current-password" autofocus>
<button>Открыть</button></form><p id="err"></p></main>
<script>
const D=@@DATA@@;
const b64=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
document.getElementById('f').addEventListener('submit',async e=>{e.preventDefault();
 const err=document.getElementById('err');err.textContent='Проверяю…';
 try{const enc=new TextEncoder();
  const base=await crypto.subtle.importKey('raw',enc.encode(document.getElementById('p').value),'PBKDF2',false,['deriveKey']);
  const key=await crypto.subtle.deriveKey({name:'PBKDF2',salt:b64(D.salt),iterations:D.iter,hash:'SHA-256'},base,{name:'AES-GCM',length:256},false,['decrypt']);
  const pt=await crypto.subtle.decrypt({name:'AES-GCM',iv:b64(D.iv)},key,b64(D.ct));
  document.getElementById('app').innerHTML=new TextDecoder().decode(pt);
 }catch(x){err.textContent='Неверный пароль'}});
</script></body></html>"""


def write(out_dir, store, subs: dict | None, owner: str | None, links: dict) -> bool:
    password = os.environ.get("ADMIN_PASSWORD")
    if not password:
        return False
    import json
    data = encrypt(body(store, subs, owner, links), password)
    (out_dir / "admin").mkdir(parents=True, exist_ok=True)
    (out_dir / "admin" / "index.html").write_text(PAGE.replace("@@DATA@@", json.dumps(data)), encoding="utf-8")
    return True
