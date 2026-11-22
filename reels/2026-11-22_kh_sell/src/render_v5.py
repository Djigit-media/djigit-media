# Продающий KHINKALI HOUSE v2. Фирменный стиль: brand.py + tpl.py (как Чашушули v2 / Карп v6).
import sys, os, json, math, subprocess, numpy as np, cv2
sys.path.insert(0, '/home/claude/work/prev'); sys.path.insert(0, '/home/claude/work/tpl')
import brand, tpl
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
W, H, FPS = 1080, 1920, 30
VO = os.environ.get('VO', 'vo5t')
OUT = os.environ.get('OUT', 'KH_sell_v5_noaudio.mp4')

def ease(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3
def eio(t): t = min(max(t, 0), 1); return 3 * t * t - 2 * t * t * t
def eback(t, s=1.7): t = min(max(t, 0), 1); return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2
def A(im): return np.array(im).astype(np.float32)
def comp(fr, lay, x, y, a=1.0):
    h, w = lay.shape[:2]; x, y = int(x), int(y); x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0 or a <= 0.003: return
    l = lay[y0 - y:y1 - y, x0 - x:x1 - x]; al = l[..., 3:4] / 255 * a
    fr[y0:y1, x0:x1] = fr[y0:y1, x0:x1] * (1 - al) + l[..., :3] * al
def scaled(L, s):
    if abs(s - 1) < 0.004: return L
    return cv2.resize(L, (max(1, int(L.shape[1] * s)), max(1, int(L.shape[0] * s))), interpolation=cv2.INTER_LINEAR)
def shimmer(lay, p, width=90):
    h, w = lay.shape[:2]; o = lay.copy(); xx = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.6
    c = -width + p * (w + h * 0.6 + 2 * width); b = np.clip(1 - np.abs(xx - c) / width, 0, 1)[..., None]
    o[..., :3] = o[..., :3] + (255 - o[..., :3]) * b * 0.55; return o
def tlayer(t, w8, sz, fill=None, gold=False, maxw=1000, shadow=235):
    while brand.width(t, w8, sz) > maxw: sz -= 2
    tw = int(brand.width(t, w8, sz)) + 40; L = Image.new('RGBA', (tw, int(sz * 1.5)), (0, 0, 0, 0))
    brand.draw_text(L, tw // 2, 0, t, w8, sz, fill, gold=gold)
    sh = Image.new('RGBA', L.size, (0, 0, 0, 0)); sh.putalpha(L.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda v: min(255, v * shadow // 255)))
    out = Image.new('RGBA', (tw + 30, L.height + 30), (0, 0, 0, 0)); out.alpha_composite(sh, (15, 19)); out.alpha_composite(L, (15, 15))
    return out

# ---------- photos ----------
def load(p):
    im = Image.open(p).convert('RGB'); sc = max(W * 1.25 / im.width, H * 1.25 / im.height)
    return im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
PHN = {'p1': 'ph/p1.png', 'p2': 'ph/p2.png', 'p3': 'ph/p3.png', 'p4': 'ph/p4.png', 'p5': 'ph/p5_fix.png', 'p6': 'ph/p6_fix.png',
       'p7': 'ph/p7.png', 'p8': 'ph/n2.png', 'p9': 'ph/n1.png', 'p10': 'ph/p10_fix.png'}
PH = {k: load(v) for k, v in PHN.items()}
def bg(key, p, z0=1.0, z1=1.08, fx=0.5, fy=0.5, dx=0.0, dy=0.0):
    im = PH[key]; z = z0 + (z1 - z0) * eio(p)
    cw = im.width / 1.25 / z; ch = im.height / 1.25 / z
    cx = im.width * (fx + dx * p); cy = im.height * (fy + dy * p)
    x0 = min(max(cx - cw / 2, 0), im.width - cw); y0 = min(max(cy - ch / 2, 0), im.height - ch)
    return np.array(im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))).astype(np.float32)


# ---------- timeline ----------
meta = json.load(open(VO + '/meta.json')); durs = meta['d']; GAP = 0.2
starts = []; t = 0.0
for d in durs: starts.append(t); t += d + GAP
SLOTS_LEN = 2.0
END_START = starts[-1] + SLOTS_LEN
TOTAL = starts[-1] + durs[-1] + 0.8
json.dump({'starts': starts, 'total': TOTAL, 'end_start': END_START, 'gap': GAP, 'durs': durs}, open('timeline_v5.json', 'w'))
NB = len(starts) - 1
SL = lambda s: starts[s + 1] - starts[s] if s < NB else SLOTS_LEN

# ---------- brand layers ----------
CORNER = A(tpl.corner_layer().crop((0, 0, 460, 480)))
HB = tpl.CORNER['horse']; HXY = (HB[0] - 12, HB[1] - 12, HB[2] + 13, HB[3] + 13)
LOGO_IN = starts[1]
SWEEPS = [LOGO_IN + 0.5 + 6 * k for k in range(20)]
PY, PH_ = 255, 600
PLATE = A(brand.plate(990, PH_, 34))
HT1 = A(tlayer('СУПЕР АКЦИЯ', 900, 108, gold=True, maxw=900))
HT2 = A(tlayer('ДЛЯ ПЕРВЫХ 3 ПАРТНЁРОВ', 900, 108, gold=True, maxw=900))
HT3 = A(tlayer('ФРАНШИЗА', 900, 124, gold=True, maxw=900))
HT4 = A(tlayer('KHINKALI HOUSE В ТВОЁМ ГОРОДЕ', 800, 52, fill=(255, 255, 255, 255), maxw=900))
TY = [PY + 26, PY + 150, PY + 285, PY + 470]
grad = np.zeros((H, W, 1), np.float32); yy_ = np.arange(H); grad[:, :, 0] = np.maximum(np.clip((yy_ - 1000) / 650, 0, 1) ** 1.2 * 0.72, np.clip(1 - yy_ / 620, 0, 1) ** 1.5 * 0.5)[:, None]
CAPY_A, CAPY_B, LINE_H = 1290, 1372, 88
def fit_sz(texts, sz=70):
    while max(brand.width(t, 900, sz) for t in texts) > 1000: sz -= 2
    return sz
def words_layer(text, sz=70):
    words = text.split(' '); sp = brand.width(' ', 900, sz); tot = brand.width(text, 900, sz); x = 540 - tot / 2; WL = []
    for wd in words:
        L = tlayer(wd, 900, sz, fill=(255, 255, 255, 255)); ww = brand.width(wd, 900, sz)
        WL.append(([A(L.filter(ImageFilter.GaussianBlur(r))) for r in (0, 3, 7)], int(x + ww / 2))); x += ww + sp
    return WL, tot
_cc = {}
def mkcap(c):
    if c in _cc: return _cc[c]
    la, l1, l2 = c; LA = A(tlayer(la, 900, 58, gold=True)); sz = fit_sz([l1, l2])
    _cc[c] = (LA, words_layer(l1, sz), words_layer(l2, sz)); return _cc[c]
def wordfx(blurs, tt):
    p = min(max(tt / 0.32, 0), 1); i = 0 if p > 0.75 else (1 if p > 0.4 else 2)
    return blurs[i], 0.7 + 0.3 * eback(p), ease(p)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32); DIAG = XX + YY * 0.55
CDARK = (1 - 0.72 * np.clip(1 - np.sqrt((XX / 560) ** 2 + (YY / 520) ** 2), 0, 1) ** 0.8)[..., None].astype(np.float32)

C = {
 'a1': ('KHINKALI HOUSE', 'ПРЕМИУМ-СТРИТФУД', 'СОВРЕМЕННОЙ ГРУЗИНСКОЙ КУХНИ'),
 'b': ('ВСЕ ФЛАГМАНЫ В ОДНОМ МЕСТЕ', 'ЦВЕТНЫЕ ХИНКАЛИ • ЧЕБУРЕК-СФЕРА', 'ХАЧАПУРИ • ДОНЕР • САЛАТЫ'),
 'c': ('ДЛЯ НАШИХ ГОСТЕЙ: ВСЁ И СРАЗУ', 'КРАСИВО • ВКУСНО • БЫСТРО', 'И ПО ДОСТУПНЫМ ЦЕНАМ'),
 'd': ('БЛЮДА С ВАУ-ЭФФЕКТОМ', 'ГОСТИ СНИМАЮТ ИХ', 'И САМИ РЕКЛАМИРУЮТ ТВОЁ ЗАВЕДЕНИЕ'),
 'e': ('ПАРТНЁРУ: СУПЕР БИЗНЕС', 'ПИЩЕВАЯ НИША, ВОСТРЕБОВАННАЯ ВСЕГДА', 'ГРУЗИНСКУЮ КУХНЮ ОСОБЕННО ЛЮБЯТ'),
 'f': ('ФОРМАТ FAST CASUAL', 'БЫСТРАЯ ПОДАЧА, ВКУСНО, ДОСТУПНЫЕ ЦЕНЫ', '= БОЛЬШОЙ ПОТОК ГОСТЕЙ'),
 'g': ('ДВА ПОТОКА ГОСТЕЙ СРАЗУ', 'ПОЕСТЬ СЕЙЧАС', '+ КУПИТЬ ЗАМОРОЗКУ ДОМОЙ'),
 'h': ('ДВА ФОРМАТА', 'КИОСК ОТ 10 М²', 'ФАСАДНОЕ ПОМЕЩЕНИЕ ОТ 80 М²'),
 'i1': ('НЕБОЛЬШИЕ ВЛОЖЕНИЯ', 'КИОСК ОТ 20 000 € ПОД КЛЮЧ', 'ФАСАДНОЕ ОТ 45 000 € ПОД КЛЮЧ'),
 'i2': ('БЫСТРАЯ ОКУПАЕМОСТЬ', 'ДО 1 ГОДА', 'ПО ОРИЕНТИРАМ СЕТИ'),
 'j': ('ГОСПОДДЕРЖКА В ГЕРМАНИИ', 'АККРЕДИТОВАННЫЕ ФИНКОНСУЛЬТАНТЫ', 'ПОМОГАЮТ С ПРОГРАММАМИ ГОСПОДДЕРЖКИ'),
 'k1': ('5 ИСТОЧНИКОВ ДОХОДА', 'ЗАЛ • ДОСТАВКА', 'ЛЕТНЯЯ ПЛОЩАДКА • ЗАМОРОЗКА ДОМОЙ'),
 'k2': ('5-Й ИСТОЧНИК: ПАРТНЁРСКАЯ ПРОГРАММА', 'ПРИВЁЛ НОВОГО ФРАНЧАЙЗИ', 'ПОЛУЧИЛ 30% ЕГО ВЗНОСА'),
 'l': ('ЗАЩИТА ВЛОЖЕНИЙ', 'ЛИКВИДНЫЙ АКТИВ', 'КОТОРЫЙ ВСЕГДА В ЦЕНЕ'),
 'n': ('ПРИСОЕДИНЯЙСЯ К НАШЕЙ СЕТИ', 'СИЛЬНЫЕ ЛЮДИ ВМЕСТЕ', 'ДОСТИГАЮТ БОЛЬШИХ ВЫСОТ'),
}
def SH(f, key, a, b, fx=.5, fy=.5, dx=0, dy=0): return (f, key, a, b, fx, fy, dx, dy)
SHOTS = {
 0: [SH(0, 'p4', .94, 1.02, .5, 1), SH(.55, 'p1', .9, .82)],
 1: [SH(0, 'p9', .94, 1.02, .45, 1, .06)],
 3: [SH(0, 'p1', .82, .9), SH(.3, 'p8', .8, .86), SH(.64, 'p5', .9, .82)],
 4: [SH(0, 'p3', .94, 1.02, .4, 1, .1)],
 5: [SH(0, 'p10', .84, .92), SH(.5, 'p6', .9, .82)],
 6: [SH(0, 'p7', .94, 1.02, .5, 1)],
 7: [SH(0, 'p4', .96, 1.02, .3, 1, .15), SH(.5, 'p8', .82, .9)],
 8: [SH(0, 'p9', .94, 1.02, .3, 1, .08), SH(.5, 'p2', .84, .92)],
 9: [SH(0, 'p4', 1.02, .94, .5, 1), SH(.5, 'p9', .94, 1.02, .65, 1, -.06)],
 10: [SH(0, 'p6', .84, .92), SH(.6, 'p5', .92, .84)],
 11: [SH(0, 'p9', .94, 1.02, .7, 1, -.06)],
 12: [SH(0, 'p9', .94, 1.02, .5, 1), SH(.2, 'p3', 1.02, .94, .6, 1), SH(.4, 'p9', 1.02, .94, .3, 1, .06), SH(.6, 'p2', .84, .92), SH(.78, 'p7', .94, 1.02, .5, 1)],
 13: [SH(0, 'p9', 1.02, .94, .5, 1)],
 15: [SH(0, 'p2', .84, .92, .5, .6)],
}
CAPW = {1: [(0, 1, 'a1')], 3: [(0, 1, 'b')], 4: [(0, 1, 'c')], 5: [(0, 1, 'd')], 6: [(0, 1, 'e')], 7: [(0, 1, 'f')], 8: [(0, 1, 'g')],
        9: [(0, 1, 'h')], 10: [(0, .62, 'i1'), (.66, 1, 'i2')], 11: [(0, 1, 'j')], 12: [(0, .56, 'k1'), (.6, 1, 'k2')], 13: [(0, 1, 'l')], 15: [(0, 1, 'n')]}
for v in CAPW.values():
    for _, _, k in v: mkcap(C[k])

def shot_of(seg, lt, L):
    sh = SHOTS[seg]; f = lt / L; i = max(j for j, s in enumerate(sh) if f >= s[0] - 1e-9)
    f0 = sh[i][0]; f1 = sh[i + 1][0] if i + 1 < len(sh) else 1.0
    return i, (lt - f0 * L), (f1 - f0) * L, sh[i]

def draw_caps(fr, cap, lt, wl):
    LA, (W1, tot1), (W2, tot2) = cap
    out = 1 - ease((lt - (wl - 0.22)) / 0.22) if lt > wl - 0.22 else 1
    aa = ease(lt / 0.3) * out; dy = int(30 * (1 - ease(lt / 0.3)))
    LAs = shimmer(LA, min(max((lt - 0.3) / 0.9, 0), 1)) if 0.3 < lt < 1.2 else LA
    comp(fr, LAs, 540 - LA.shape[1] // 2, CAPY_A + dy, aa)
    d2 = 0.12 + 0.08 * len(W1) + 0.25
    for row, (WL, delay, yb) in enumerate(((W1, 0.12, CAPY_B), (W2, d2, CAPY_B + LINE_H))):
        for k, (blurs, cx) in enumerate(WL):
            Lw, s, al = wordfx(blurs, lt - delay - 0.08 * k); Ls = scaled(Lw, s)
            comp(fr, Ls, cx - Ls.shape[1] // 2, yb + (Lw.shape[0] - Ls.shape[0]) // 2, al * out)
    tot = max(tot1, tot2); lw = int(tot * ease((lt - 0.35 - d2) / 0.4))
    if lw > 2:
        ln = np.zeros((5, lw, 4), np.float32); ln[..., :3] = (200, 165, 100); ln[..., 3] = 230
        comp(fr, ln, 540 - lw // 2, CAPY_B + LINE_H + 116, out)

# offer scene layers
OF_T = A(tlayer('ТОЛЬКО ДЛЯ ПЕРВЫХ ТРЁХ', 900, 64, gold=True, maxw=900))
OF_K = A(tlayer('КИОСК', 800, 40, gold=True)); OF_F = A(tlayer('ФАСАДНОЕ', 800, 40, gold=True))
OF_O1 = A(tlayer('7 000 €', 800, 86, fill=(215, 215, 215, 255)))
OF_O2 = A(tlayer('9 000 €', 800, 86, fill=(215, 215, 215, 255)))
OF_N = A(tlayer('5 000 €', 900, 210, gold=True, maxw=950))
OF_NL = A(tlayer('ВЗНОС', 800, 46, fill=(255, 255, 255, 255)))
OF_C = [A(tlayer(s, 900, 56, fill=(255, 255, 255, 255))) for s in ('0% РОЯЛТИ 3 МЕСЯЦА', 'ДИЗАЙН-ПРОЕКТ В ПОДАРОК')]
OF_S = A(tlayer('ВСЕГО 3 МЕСТА', 900, 58, gold=True))
OF_PLATE = A(brand.plate(990, 1180, 34))
def token(n, d=120):
    S = int(d * 1.5); im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); o = (S - d) // 2
    dr.ellipse((o - 5, o - 5, o + d + 5, o + d + 5), fill=(255, 226, 160, 255)); dr.ellipse((o, o, o + d, o + d), fill=(214, 176, 106, 255))
    brand.draw_text(im, S // 2, int(o + d * 0.13), str(n), 900, int(d * 0.62), (24, 16, 6, 255))
    sh = Image.new('RGBA', (S, S), (0, 0, 0, 0)); sh.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(8)).point(lambda v: v * 200 // 255))
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0)); out.alpha_composite(sh, (0, 6)); out.alpha_composite(im); return A(out)
TOK = [token(i) for i in (1, 2, 3)]; TOKB = [token(i, 200) for i in (1, 2, 3)]
SL_A = A(tlayer('МЕСТ ВСЕГО ТРИ', 900, 96, gold=True, maxw=950))
SL_B = A(tlayer('ЗАЙМИ СВОЁ МЕСТО', 900, 70, fill=(255, 255, 255, 255), maxw=950))

# end card
_E = dict(tpl.END)
for k in ('q1', 'q2', 'btn', 'site'):
    a, b, c, d = _E[k]; _E[k] = (a, b + 34, c, d + 34)
tpl.END.update(_E)
EL = tpl.end_layers(q1t='Хочешь такой стритфуд', q2t='в своём городе?', btnt='ЗАЙМИ СВОЁ МЕСТО'); Lend = {k: (A(im), xy) for k, (im, xy) in EL.items()}
_ben = tlayer('КРАСИВО • БЫСТРО • ВКУСНО • ДОСТУПНО ПО ЦЕНЕ', 800, 34, gold=True, maxw=960); Lend['ben'] = (A(_ben), (540 - _ben.width // 2, 1018))
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((290, 380, 790, 880), fill=(214, 170, 100, 90)); GLOW = A(glow.filter(ImageFilter.GaussianBlur(90)))
order = [('dj', 0.25), ('sub', 0.4), ('ben', 0.5), ('q1', 0.62), ('q2', 0.7), ('btn', 0.85), ('site', 1.0)]
def endframe(last, BG, t):
    m = ease(t / 0.25); fr = BG * m + last * (1 - m)
    comp(fr, GLOW, 0, 0, ease(t / 0.6))
    hl, (hx, hy) = Lend['horse']; hs = shimmer(hl, (t - 0.9) / 1.0, 70) if 0.9 < t < 1.9 else hl
    comp(fr, hs, hx, hy, ease(t / 0.35))
    for k, d in order:
        lay, (x, y) = Lend[k]; aa = ease((t - d) / 0.35); dy = int(35 * (1 - aa))
        if k == 'dj' and 0.6 < t < 1.5: lay = shimmer(lay, (t - 0.6) / 0.9)
        if k == 'ben' and 1.2 < t < 2.2: lay = shimmer(lay, (t - 1.2) / 1.0, 120)
        if k == 'btn' and t > 1.5:
            s2 = 1 + 0.025 * np.sin((t - 1.5) * 2 * np.pi / 1.2); l2 = scaled(lay, s2)
            comp(fr, l2, x - (l2.shape[1] - lay.shape[1]) // 2, y - (l2.shape[0] - lay.shape[0]) // 2, aa); continue
        comp(fr, lay, x, y + dy, aa)
    return fr

# ---------- backgrounds ----------
def seg_bg(seg, lt, L):
    if seg in SHOTS:
        i, st, sl, (f, key, z0, z1, fx, fy, dx, dy) = shot_of(seg, lt, L)
        return bg(key, st / sl, z0, z1, fx, fy, dx, dy)
    p = lt / L
    if seg == 2: return cv2.GaussianBlur(bg('p4', p, .9, .98, .5, 1.0), (0, 0), 16) * 0.4
    if seg == 14: return cv2.GaussianBlur(bg('p1', p, 1.15, 1.25, 0.5, 0.5), (0, 0), 14) * 0.45
    return cv2.GaussianBlur(bg('p10', min(p, 1), 1.08, 1.0, 0.55, 0.42), (0, 0), 16) * 0.42

def whip(fr, q):
    k = 1 + 2 * int(70 * (1 - q) / 2); sh = int(W * 0.22 * (1 - ease(q)))
    return cv2.blur(np.roll(fr, sh, axis=1), (k, 1)) if k > 1 else fr
def vflash(fr, q, k):
    c = -200 + q * (H + 400); band = np.clip(1 - np.abs(YY - c) / 200, 0, 1)[..., None] * 0.35 * k * (1 - q * 0.5)
    return fr + (np.array([255, 214, 150], np.float32) - fr) * band
def trans(fr, st, kind, k):
    q = st / 0.38
    if kind == 0: return flash(punch(fr, st / 0.35, 0.06 * k) if st < 0.35 else fr, q, k)
    if kind == 1: fr = punch(fr, st / 0.35, 0.08 * k) if st < 0.35 else fr; return fr + (255 - fr) * (0.3 * k * (1 - q))
    if kind == 2: return whip(fr, q)
    return vflash(punch(fr, st / 0.35, 0.05 * k) if st < 0.35 else fr, q, k)
def punch(fr, q, amt):
    z = 1.0 + amt * (1 - ease(q)); cw, ch = int(W / z), int(H / z); x0 = (W - cw) // 2; y0 = (H - ch) // 2
    return cv2.resize(fr[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR)
def flash(fr, q, k):
    c = -300 + q * (W + H * 0.55 + 600); band = np.clip(1 - np.abs(DIAG - c) / 260, 0, 1)[..., None] * 0.35 * k * (1 - q * 0.5)
    return fr + (np.array([255, 214, 150], np.float32) - fr) * band

def frame(fi):
    t = fi / FPS
    seg = max(i for i, s in enumerate(starts) if t >= s - 1e-9)
    s0 = starts[seg]; L = SL(seg); lt = t - s0
    if seg == NB and t >= END_START: return None
    fr = seg_bg(seg, lt, L)
    if seg in SHOTS:
        i, st, sl, _ = shot_of(seg, lt, L)
        if not (seg == 0 and i == 0) and st < 0.38:
            k = 1.0 if i == 0 else 0.7
            fr = trans(fr, st, (seg * 3 + i) % 4, k)
    elif seg in (2, 14, 16) and lt < 0.38:
        fr = punch(fr, lt / 0.35, 0.06) if lt < 0.35 else fr; fr = flash(fr, lt / 0.38, 1.0)
    if seg == 0:
        a = 1.0 if lt < L - 0.25 else 1 - ease((lt - (L - 0.25)) / 0.25)
        comp(fr, PLATE, 45, PY, a)
        spp = min(max((lt - 0.6) / 1.1, 0), 1)
        for Lr, yy in ((HT1, TY[0]), (HT2, TY[1]), (HT3, TY[2])):
            comp(fr, shimmer(Lr, spp) if 0 < spp < 1 else Lr, 540 - Lr.shape[1] // 2, yy, a)
        comp(fr, HT4, 540 - HT4.shape[1] // 2, TY[3], a)
        return fr
    if seg == 2: return profit_scene(fr, lt, L, t)
    if seg in SHOTS:
        fr = fr * (1 - grad * min(1, ease((t - LOGO_IN) / 0.3))) * (1 - (1 - CDARK) * min(1, ease((t - LOGO_IN) / 0.3)))
        q = ease((t - LOGO_IN) / 0.35); CL = CORNER
        for stt in SWEEPS:
            if stt <= t < stt + 1.0:
                CL = CORNER.copy(); x0_, y0_, x1_, y1_ = HXY; CL[y0_:y1_, x0_:x1_] = shimmer(CORNER[y0_:y1_, x0_:x1_], (t - stt) / 1.0, 45); break
        comp(fr, CL, 0, 0, q)
        for f0, f1, ck in CAPW.get(seg, []):
            if f0 * L <= lt < f1 * L + 0.001: draw_caps(fr, mkcap(C[ck]), lt - f0 * L, (f1 - f0) * L)
        return fr
    out = 1 - ease((lt - (L - 0.22)) / 0.22) if (seg == 14 and lt > L - 0.22) else 1
    if seg == 14:
        comp(fr, OF_PLATE, 45, 300, ease(lt / 0.3) * out)
        comp(fr, OF_T, 540 - OF_T.shape[1] // 2, 345 + int(25 * (1 - ease(lt / 0.35))), ease(lt / 0.35) * out)
        qo = ease((lt - 0.4) / 0.35)
        comp(fr, OF_K, 300 - OF_K.shape[1] // 2, 425, qo * out); comp(fr, OF_F, 780 - OF_F.shape[1] // 2, 425, qo * out)
        comp(fr, OF_O1, 300 - OF_O1.shape[1] // 2, 470, qo * out); comp(fr, OF_O2, 780 - OF_O2.shape[1] // 2, 470, qo * out)
        N0 = 0.12 * L; qn = (lt - N0) / 0.45
        if qn > 0:
            comp(fr, OF_NL, 540 - OF_NL.shape[1] // 2, 640, ease(qn) * out)
            sc = 1.7 - 0.7 * eback(min(1, qn), 2.2); Ln = scaled(OF_N, sc)
            if 0.45 < (lt - N0) < 1.45: Ln = shimmer(Ln, ((lt - N0) - 0.45) / 1.0, 120)
            shake = int(10 * math.sin(lt * 60) * max(0, 1 - (lt - N0) / 0.35)) if qn > 0.6 else 0
            comp(fr, Ln, 540 - Ln.shape[1] // 2 + shake, 830 - Ln.shape[0] // 2, min(1, qn * 3) * out)
            if lt - N0 < 0.15: fr = fr + (255 - fr) * (0.45 * (1 - (lt - N0) / 0.15))
        st = ease((lt - 0.42 * L) / 0.35)
        if st > 0:
            for cx in (300, 780):
                ln = np.zeros((12, int(300 * st) + 1, 4), np.float32); ln[..., :3] = (225, 45, 45); ln[..., 3] = 255
                comp(fr, ln, cx - 150, 548, out)
        for j, Lc in enumerate(OF_C):
            qc = (lt - (0.6 + 0.18 * j) * L) / 0.35
            if qc > 0: Ls = scaled(Lc, 0.7 + 0.3 * eback(min(1, qc))); comp(fr, Ls, 540 - Ls.shape[1] // 2, 1000 + j * 95 + (Lc.shape[0] - Ls.shape[0]) // 2, ease(qc) * out)
        for k in range(3):
            qk = (lt - 0.9 - 0.18 * k) / 0.3
            if qk > 0:
                pul = 1 + 0.06 * math.sin(lt * 5 - k * 0.9); Ls = scaled(TOK[k], (0.6 + 0.4 * eback(min(1, qk))) * pul)
                cx = 540 + (k - 1) * 190; comp(fr, Ls, cx - Ls.shape[1] // 2, 1205 + (TOK[k].shape[0] - Ls.shape[0]) // 2, ease(qk) * out)
        qs = (lt - 1.2) / 0.35
        if qs > 0: comp(fr, OF_S, 540 - OF_S.shape[1] // 2, 1345, ease(qs) * out)
        return fr
    # slots scene
    for k in range(3):
        qk = (lt - 0.05 - 0.2 * k) / 0.3
        if qk > 0:
            pul = 1 + 0.05 * math.sin(lt * 6 - k); Ls = scaled(TOKB[k], (0.6 + 0.4 * eback(min(1, qk))) * pul)
            cx = 540 + (k - 1) * 300; comp(fr, Ls, cx - Ls.shape[1] // 2, 830 + (TOKB[k].shape[0] - Ls.shape[0]) // 2, ease(qk))
    comp(fr, SL_A, 540 - SL_A.shape[1] // 2, 600 + int(25 * (1 - ease(lt / 0.3))), ease(lt / 0.3))
    q = ease((lt - 0.7) / 0.3); comp(fr, SL_B, 540 - SL_B.shape[1] // 2, 1130 + int(25 * (1 - q)), q)
    if lt > L - 0.2: pass
    return fr

PF_PL = A(brand.plate(990, 900, 34))
PF_T = A(tlayer('ЧИСТАЯ ПРИБЫЛЬ В МЕСЯЦ', 900, 62, gold=True, maxw=900))
PF_K = A(tlayer('КИОСК ОТ', 900, 56, fill=(255, 255, 255, 255)))
PF_KN = A(tlayer('3 000 €', 900, 190, gold=True, maxw=900))
PF_F = A(tlayer('ФАСАДНОЕ ПОМЕЩЕНИЕ ОТ', 900, 50, fill=(255, 255, 255, 255), maxw=900))
PF_FN = A(tlayer('10 000 €', 900, 190, gold=True, maxw=900))
def profit_scene(fr, lt, L, t):
    fr = fr * (1 - grad * min(1, ease((t - LOGO_IN) / 0.3))) * (1 - (1 - CDARK) * min(1, ease((t - LOGO_IN) / 0.3))); q = ease((t - LOGO_IN) / 0.35)
    comp(fr, CORNER, 0, 0, q)
    out = 1 - ease((lt - (L - 0.22)) / 0.22) if lt > L - 0.22 else 1
    comp(fr, PF_PL, 45, 480, ease(lt / 0.3) * out)
    comp(fr, PF_T, 540 - PF_T.shape[1] // 2, 520 + int(25 * (1 - ease(lt / 0.35))), ease(lt / 0.35) * out)
    for (lab, num, t0, y) in ((PF_K, PF_KN, 0.3 * L, 650), (PF_F, PF_FN, 0.62 * L, 1000)):
        qq = (lt - t0) / 0.45
        if qq > 0:
            comp(fr, lab, 540 - lab.shape[1] // 2, y - 5, ease(qq) * out)
            sc = 1.6 - 0.6 * eback(min(1, qq), 2.2); Ln = scaled(num, sc)
            if 0.45 < lt - t0 < 1.45: Ln = shimmer(Ln, (lt - t0 - 0.45) / 1.0, 120)
            comp(fr, Ln, 540 - Ln.shape[1] // 2, y + 75 + (num.shape[0] - Ln.shape[0]) // 2, min(1, qq * 3) * out)
            if lt - t0 < 0.15: fr = fr + (255 - fr) * (0.35 * (1 - (lt - t0) / 0.15))
    ln = np.zeros((4, 700, 4), np.float32); ln[..., :3] = (200, 165, 100); ln[..., 3] = 220
    comp(fr, ln, 190, 960, ease((lt - 0.5 * L) / 0.4) * out)
    return fr

def end_bg(): return cv2.GaussianBlur(seg_bg(NB, SLOTS_LEN, SLOTS_LEN), (0, 0), 20) * 0.6

if __name__ == '__main__':
    NF = int(math.ceil(TOTAL * FPS)); EF = int(END_START * FPS)
    if len(sys.argv) > 1 and sys.argv[1].startswith('frames:'):
        for x in sys.argv[1][7:].split(','):
            fi = int(float(x) * FPS)
            if fi >= EF: img = endframe(frame(EF - 1), end_bg(), (fi - EF) / FPS)
            else: img = frame(fi)
            Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(f'v5_{x}.jpg', quality=90)
        print(starts, END_START, TOTAL); sys.exit()
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'slow', '-crf', '13', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    last = None
    for fi in range(EF):
        f = frame(fi); last = f; enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
        if fi % 300 == 0: print(fi, '/', NF, flush=True)
    BG = end_bg()
    for j in range(NF - EF): enc.stdin.write(np.clip(endframe(last, BG, j / FPS), 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait(); print('done', NF)
