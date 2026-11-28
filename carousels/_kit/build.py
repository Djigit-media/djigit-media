#!/usr/bin/env python3
"""Сборщик каруселей DJIGIT (агент 05). Уровень @dashi_agent, стиль DJIGIT.
python3 build.py <папка карусели>  ->  <папка>/slides/NN.png 1080x1350 + preview.jpg
В папке: slides.json = {"steps": ["01 Зал", ...], "cta": "...", "slides": [{bg, section, tag, title, text, card, step, final}]}
"""
import json, sys, os, re, html
from playwright.sync_api import sync_playwright
K = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(os.path.dirname(K))
NB = re.compile(r'(?<![\wА-Яа-яЁё])(в|на|и|с|к|по|от|до|за|не|а|о|у|из|для|без|под|при|про|что|как|это|ты|мы|я)\s', re.I)
def nb(t): return NB.sub(lambda m: m.group(1) + ' ', html.escape(t))   # 0 висячих предлогов
CSS = f"""
@font-face{{font-family:Mont;src:url(file://{K}/fonts/mont_cyrillic_900.ttf);font-weight:900;unicode-range:U+0400-04FF}}
@font-face{{font-family:Mont;src:url(file://{K}/fonts/mont_latin_900.ttf);font-weight:900}}
""" + ''.join(f"@font-face{{font-family:Man;src:url(file://{K}/fonts/manrope-{s}-{w}-normal.woff2);font-weight:{w}}}" for s in ('cyrillic', 'latin') for w in (400, 500, 700, 800)) + """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;overflow:hidden;font-family:Man;color:#fff;background:#000}
.bg{position:absolute;inset:0;background-size:cover;background-position:center}
.sh{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.55) 0%,rgba(0,0,0,.25) 35%,rgba(0,0,0,.55) 70%,rgba(0,0,0,.85) 100%)}
.hd{position:absolute;left:80px;right:80px;top:70px;height:56px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,.28);padding-bottom:18px;height:74px}
.pill{display:flex;align-items:center;gap:10px;border:2px solid rgba(255,255,255,.85);border-radius:30px;padding:6px 18px 6px 8px;font-weight:800;font-size:22px;letter-spacing:.5px}
.pill img{height:40px}
.sec{font-weight:800;font-size:22px;letter-spacing:1px}
.tag{display:inline-block;background:#CDA96B;color:#14100a;font-weight:800;font-size:22px;padding:6px 18px;border-radius:30px;letter-spacing:.5px}
h1{font-family:Mont;font-weight:900;font-size:92px;line-height:.98;text-transform:uppercase;margin:18px 0 18px;letter-spacing:-1px}
.tx{font-size:32px;line-height:1.3;font-weight:500;color:rgba(255,255,255,.92)}
.glass{background:rgba(18,18,22,.42);backdrop-filter:blur(26px);-webkit-backdrop-filter:blur(26px);border:1px solid rgba(255,255,255,.18);border-radius:28px;padding:26px 28px;box-shadow:0 20px 60px rgba(0,0,0,.35)}
.ct{font-size:22px;font-weight:700;color:rgba(255,255,255,.85);display:flex;align-items:center;gap:10px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,.12);margin-bottom:14px}
.ct b{color:#CDA96B;font-size:26px}
.row{margin:14px 0}.rl{display:flex;justify-content:space-between;font-size:24px;font-weight:700}.rl span{color:#CDA96B;font-weight:700;font-size:21px}
.bar{height:10px;border-radius:6px;background:rgba(255,255,255,.14);margin-top:9px}.bar i{display:block;height:100%;border-radius:6px;background:rgba(255,255,255,.75)}
.bar.hl i{background:#CDA96B}
.note{margin-top:16px;border:1px solid rgba(255,255,255,.14);border-radius:18px;padding:14px 18px;font-size:22px;line-height:1.35;color:rgba(255,255,255,.88)}
.note em{font-style:normal;color:#CDA96B;font-weight:700;font-size:18px;letter-spacing:1px;display:block;margin-bottom:4px}
.pg{position:absolute;left:80px;right:80px;top:1148px;display:flex;gap:12px}
.pg div{flex:1;border-top:2px solid rgba(255,255,255,.3);padding-top:10px;font-size:20px;color:rgba(255,255,255,.55)}
.pg div.on{border-top:5px solid #CDA96B;color:#CDA96B;font-weight:800;padding-top:7px}
.ft{position:absolute;left:80px;right:80px;top:1218px;border-top:1px solid rgba(255,255,255,.28);padding-top:18px;font-size:28px;font-weight:500}
.ft b{color:#CDA96B}
.fin{position:absolute;left:80px;right:80px;top:470px}
.fin h2{font-family:Mont;font-weight:900;font-size:76px;line-height:1.02;text-transform:uppercase}
.fin .k{font-family:Mont;font-weight:900;font-size:132px;color:#CDA96B;line-height:1;margin-top:60px;letter-spacing:-2px;text-shadow:0 8px 40px rgba(0,0,0,.6)}
.fin .s{font-size:34px;font-weight:700;margin-top:14px;text-align:right}
"""
def slide_html(c, s, i):
    bg = s['bg'] if s['bg'].startswith('/') else os.path.join(R, s['bg'])
    out = [f"<div class=bg style=\"background-image:url('file://{bg}');{s.get('bgcss','')}\"></div><div class=sh></div>",
           f"<div class=hd><div class=pill><img src='file://{R}/ref/logo.png'>DJIGIT</div><div class=sec>{html.escape(s.get('section',''))}</div></div>"]
    if s.get('final'):
        out.append(f"<div class=fin><h2>{nb(s['title'])}</h2><div class=k>«{html.escape(c['key'])}»</div><div class=s>{nb(s.get('text',''))}</div></div>")
    else:
        top = s.get('top', 200)
        body = f"<div style='position:absolute;left:80px;width:{s.get('w',920)}px;top:{top}px'>"
        if s.get('tag'): body += f"<div class=tag>{html.escape(s['tag'])}</div>"
        body += f"<h1>{nb(s['title'])}</h1>" + (f"<div class=tx>{nb(s['text'])}</div>" if s.get('text') else '') + "</div>"
        out.append(body)
        cd = s.get('card')
        if cd:
            rows = ''.join(f"<div class=row><div class=rl>{nb(r['l'])}<span>{nb(r.get('v',''))}</span></div><div class='bar{' hl' if r.get('hl') else ''}'><i style='width:{r.get('w',60)}%'></i></div></div>" for r in cd.get('rows', []))
            notes = ''.join(f"<div class=note><em>{html.escape(n.get('h',''))}</em>{nb(n['t'])}</div>" for n in cd.get('notes', []))
            out.append(f"<div class=glass style='position:absolute;{cd['pos']}'><div class=ct><b>✳</b>{nb(cd.get('title',''))}</div>{rows}{notes}</div>")
    if c.get('steps') and not s.get('final'):
        out.append('<div class=pg>' + ''.join(f"<div class='{'on' if k + 1 == s.get('step') else ''}'>{html.escape(t)}</div>" for k, t in enumerate(c['steps'])) + '</div>')
    if not s.get('final') and not s.get('cover'):
        out.append(f"<div class=ft>{c['cta_html']}</div>")
    return f"<html><head><meta charset=utf-8><style>{CSS}</style></head><body>{''.join(out)}</body></html>"
STOP = ['хинкальн', 'fast casual', 'напиши франшиза', 'пиши «франшиза»', 'плевать']   # Ошибки и защита п.0в, 3а: придуманные названия и запрещённые слова
def stop_check(c):
    txt = json.dumps(c, ensure_ascii=False).lower(); bad = [w for w in STOP if w in txt]
    if bad: raise SystemExit('FAIL стоп-слова: ' + ', '.join(bad))
def main(d):
    c = json.load(open(os.path.join(d, 'slides.json'))); stop_check(c); os.makedirs(os.path.join(d, 'slides'), exist_ok=True); files = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome'); pg = b.new_page(viewport={'width': 1080, 'height': 1350})
        for i, s in enumerate(c['slides'], 1):
            h = os.path.join(d, 'slides', f'{i:02d}.html'); open(h, 'w').write(slide_html(c, s, i))
            pg.goto('file://' + h); pg.wait_for_timeout(600)
            over = pg.evaluate("[...document.querySelectorAll('h1,.tx,.rl,.note,.ft,.fin h2,.k')].filter(e=>e.scrollWidth>e.clientWidth+1||e.getBoundingClientRect().right>1000).map(e=>e.className||e.tagName)")
            if over: print('FAIL выход за поля', i, over)
            f = os.path.join(d, 'slides', f'{i:02d}.png'); pg.screenshot(path=f); files.append(f)
        b.close()
    print('ok', len(files))
if __name__ == '__main__': main(os.path.abspath(sys.argv[1]))
