# Рилс «3 бизнеса на еде без опыта» (продажа через широкую тему, правило 0021). Картинки Вала из GPT 27.11 (3 шт., 941x1672).
# Без голоса; музыка Mixkit «Gimme that Groove!» (id 872, Mixkit Stock Music Free License: коммерция и соцсети, без указания автора).
# Стиль: копия эталона reels/2026-11-26_khachapuri/render.py.
import sys, os, subprocess, json, numpy as np, cv2
sys.path.insert(0, '/home/claude/work/prev'); sys.path.insert(0, '/home/claude/work/tpl'); sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../factory/style'))
import brand, tpl
from PIL import Image, ImageDraw, ImageFilter
D = os.path.dirname(os.path.abspath(__file__)); WK = '/home/claude/work/biz'
OUT = os.environ.get('OUT', WK + '/biz3_v1.mp4'); MUS = D + '/src/music_mixkit_872_gimme_that_groove.mp3'
W, H, FPS = 1080, 1920, 30
ZX0, ZY0, ZX1, ZY1 = 65, 270, 960, 1500
L1, L2, L3 = '3 БИЗНЕСА', 'на еде без опыта', 'первое место тебя удивит'
HOOK_END = 2.6; LOGO_IN = 2.6; END_T = 17.0   # сцены-цифры сжаты до 2,8 с: меньше размытого фона, выше досмотр
STEPS = [(9.6, 12.0, 'ПОЧЕМУ ПЕРВОЕ МЕСТО', 'ФОРМАТ КИОСКА'), (12.0, 14.4, 'ПОЧЕМУ ПЕРВОЕ МЕСТО', 'ГОСТИ САМИ СНИМАЮТ'),
         (14.4, 17.0, 'ПОЧЕМУ ПЕРВОЕ МЕСТО', 'БИЗНЕС-ПЛАН И СОПРОВОЖДЕНИЕ')]
NUMS = [(2.6, 5.4, '3', 'КОФЕЙНЯ', 'кофейня уже на каждом углу', 'kiosk'), (5.4, 8.2, '2', 'ШАУРМА', 'все умеют, поэтому все и открыли', 'hand'),
        (8.2, 9.6, '1', 'KHINKALI HOUSE', 'и вот почему', 'box')]
NV = int(20.5 * FPS)
# проверка шрифта: каждый символ всех надписей есть в Montserrat (27.11: «№» рисовался квадратом)
from fontTools.ttLib import TTFont
import glob as _g
_cm = set()
for _f in _g.glob('/home/claude/work/prev/mont_*_900.ttf'): _cm |= set(TTFont(_f).getBestCmap())
_txt = [L1, L2, L3, 'ПИШИ «ХОЧУ ОТКРЫТЬ» В ДИРЕКТ', 'Хочешь такой ресторан', 'в своём городе?'] + [x for st in STEPS for x in st[2:]] + [x for n in NUMS for x in n[2:5]]
_miss = sorted({c for tx in _txt for c in tx if c != ' ' and ord(c) not in _cm})
assert not _miss, f'нет глифов в шрифте: {_miss}'

def ease(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3
def eback(t, s=1.7): t = min(max(t, 0), 1); return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2
def A(im): return np.array(im).astype(np.float32)
ZLOG = []; _box = [None]
def comp(fr, lay, x, y, a=1.0, log=True):
    h, w = lay.shape[:2]; x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0 or a <= 0.003: return
    l = lay[y0 - y:y1 - y, x0 - x:x1 - x]; al = l[..., 3:4] / 255 * a
    fr[y0:y1, x0:x1] = fr[y0:y1, x0:x1] * (1 - al) + l[..., :3] * al
    if log:
        m = (l[..., 3] * a) > 20
        if m.any():
            ys, xs = np.where(m.any(1))[0], np.where(m.any(0))[0]; b = [x0 + xs[0], y0 + ys[0], x0 + xs[-1], y0 + ys[-1]]
            o = _box[0]; _box[0] = b if o is None else [min(o[0], b[0]), min(o[1], b[1]), max(o[2], b[2]), max(o[3], b[3])]
def scaled(L, s):
    if abs(s - 1) < 0.004: return L
    return cv2.resize(L, (max(1, int(L.shape[1] * s)), max(1, int(L.shape[0] * s))), interpolation=cv2.INTER_LINEAR)
def comp_c(fr, L, cx, cy, sc=1.0, a=1.0, log=True):
    Ls = scaled(L, sc); comp(fr, Ls, int(cx - Ls.shape[1] / 2), int(cy - Ls.shape[0] / 2), a, log)
def shimmer(lay, p, width=90):
    h, w = lay.shape[:2]; o = lay.copy(); xx = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.6
    c = -width + p * (w + h * 0.6 + 2 * width); b = np.clip(1 - np.abs(xx - c) / width, 0, 1)[..., None]
    o[..., :3] = o[..., :3] + (255 - o[..., :3]) * b * 0.55; return o
def tlayer(t, w8, sz, fill=None, gold=False, maxw=800, shadow=235):
    while brand.width(t, w8, sz) > maxw: sz -= 2
    tw = int(brand.width(t, w8, sz)) + 40; L = Image.new('RGBA', (tw, int(sz * 1.5)), (0, 0, 0, 0))
    brand.draw_text(L, tw // 2, 0, t, w8, sz, fill, gold=gold)
    out = Image.new('RGBA', (tw + 30, L.height + 30), (0, 0, 0, 0))
    if shadow:   # двойная мягкая тень вместо подложки: читается на светлом, не закрывает кадр
        for bl, op, dy in ((14, 0.55), (3, 0.9)) and ((14, 0.55, 6), (3, 0.9, 3)):
            sh = Image.new('RGBA', L.size, (0, 0, 0, 0)); sh.putalpha(L.split()[3].filter(ImageFilter.GaussianBlur(bl)).point(lambda v, o=op: min(255, int(v * 2.2 * o * shadow / 255))))
            out.alpha_composite(sh, (15, 15 + dy))
    out.alpha_composite(L, (15, 15))
    return out
# угловой логотип: стандарт tpl, масштаб 0.8, левый-верхний угол там же, где в KH v16d (Вал 26.11: «немножко уменьшить»)
tpl.CORNER['sub'] = (52, 400, 381, 410)
C0 = A(tpl.corner_layer().crop((0, 0, 460, 480))); _m = C0[..., 3] > 0.5
_cy, _cx = np.where(_m.any(1))[0], np.where(_m.any(0))[0]; REF_TL = (5 + _cx[0], 156 + _cy[0])
CS = 0.84; CORNER = scaled(C0, CS); _m = CORNER[..., 3] > 0.5
_cy, _cx = np.where(_m.any(1))[0], np.where(_m.any(0))[0]
LDX, LDY = int(25 - _cx[0]), int(190 - _cy[0])   # Вал 26.11 23:45: место то же (25,190), размер чуть больше (0.84)
CORNER_BOX = [int(LDX + _cx[0]), int(LDY + _cy[0]), int(LDX + _cx[-1]), int(LDY + _cy[-1])]
HB = [int(v * CS) for v in tpl.CORNER['horse']]; HXY = (HB[0] - 10, HB[1] - 10, HB[2] + 10, HB[3] + 10)
SWEEPS = [LOGO_IN + 0.5 + 6 * k for k in range(5)]
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
CDARK = (1 - 0.6 * np.clip(1 - np.sqrt(((XX - LDX) / 520) ** 2 + ((YY - LDY) / 520) ** 2), 0, 1) ** 0.8)[..., None]
# крючок: СТАНДАРТ ПЛАШКИ = «КУБДАРИ» (замер кадра kubdari_v1 0.5 с): плашка 984x389, центр 540, золото плоское (205,169,107),
# название Montserrat 900 высота букв 110, подзаголовок белый строчными 600, третья строка золотом строчными. Вал 26.11 23:40.
GOLD = (205, 169, 107, 255)
STYLE = os.environ.get('STYLE', 'A')
TOPG = np.zeros((H, W, 1), np.float32); _yy = np.arange(H); TOPG[:, :, 0] = (0.78 * np.clip(1 - np.abs(_yy - 470) / 420, 0, 1) ** 0.7)[:, None]
PX, PY, PW, PH = 65, 270, 950, 389   # 65..1015: выше 1100 px справа можно до 1015 (гейт ZONE_R_TOP)
PLATE = A(brand.plate(PW, PH, 34, alpha=240))
def ink_layer(t, w8, sz, fill):
    L = tlayer(t, w8, sz, fill=fill, maxw=880, shadow=(235 if STYLE == 'B' else 0)); a = np.array(L)[..., 3]; ys = np.where(a.max(1) > 30)[0]
    return A(L), int(ys[0])
T1, T1o = ink_layer(L1, 900, 158, GOLD); T2, T2o = ink_layer(L2, 600, 54, (255, 255, 255, 255)); T3, T3o = ink_layer(L3, 600, 38, GOLD)
TY = [PY + 82 - T1o, PY + 225 - T2o, PY + 311 - T3o]
RING = (PLATE[..., 0] > 100) & (PLATE[..., 3] > 200); _ry, _rx = np.mgrid[0:PH, 0:PW]
RANG = (np.arctan2((_ry - PH / 2) / PH, (_rx - PW / 2) / PW) / (2 * np.pi)) % 1.0
def hook_group(t):
    G = PLATE.copy() if STYLE != 'B' else np.zeros_like(PLATE)
    if STYLE != 'B':   # две золотые искры бегут по рамке плашки
        p = (t / 2.2) % 1.0; d = np.minimum(np.abs(RANG - p), 1 - np.abs(RANG - p)); d2 = np.minimum(np.abs(RANG - (p + .5) % 1), 1 - np.abs(RANG - (p + .5) % 1))
        k = (np.clip(1 - np.minimum(d, d2) / 0.06, 0, 1) ** 2) * RING
        glow = cv2.GaussianBlur(k.astype(np.float32), (0, 0), 7) * 2.2
        add = np.clip(np.maximum(k, glow), 0, 1)[..., None]
        G[..., :3] = G[..., :3] * (1 - add) + np.array([255, 236, 190], np.float32) * add; G[..., 3] = np.maximum(G[..., 3], add[..., 0] * 255)
    spp = min(max((t - 0.5) / 1.1, 0), 1)
    for L, yy in ((T1, TY[0]), (T2, TY[1]), (T3, TY[2])):
        LL = shimmer(L, spp) if (0 < spp < 1 and L is T1) else L; x = PW // 2 - LL.shape[1] // 2; y = yy - PY
        h, w = LL.shape[:2]; x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + w, PW), min(y + h, PH)
        l = LL[y0 - y:y1 - y, x0 - x:x1 - x]; al = l[..., 3:4] / 255
        G[y0:y1, x0:x1, :3] = G[y0:y1, x0:x1, :3] * (1 - al) + l[..., :3] * al; G[y0:y1, x0:x1, 3] = np.maximum(G[y0:y1, x0:x1, 3], l[..., 3])
    return G
grad = np.zeros((H, W, 1), np.float32); grad[:, :, 0] = (np.clip((np.arange(H) - 950) / 600, 0, 1) ** 1.2 * 0.7)[:, None]
CAPY_A, CAPY_B = 1302, 1374   # Вал 27.11 00:03: шаги почти внизу, низ черты 1490 (зона Reels до 1500)
caps = []
for s0, s1, a, b in STEPS:
    LA = A(tlayer(a, 900, 56, gold=True)); szb = 68
    while brand.width(b, 900, szb) > 820: szb -= 2
    words = b.split(' '); sp = brand.width(' ', 900, szb); tot = brand.width(b, 900, szb); x = 512 - tot / 2; WL = []
    for wd in words:
        L = tlayer(wd, 900, szb, fill=(255, 255, 255, 255)); ww = brand.width(wd, 900, szb)
        WL.append(([A(L.filter(ImageFilter.GaussianBlur(r))) for r in (0, 3, 7)], int(x + ww / 2))); x += ww + sp
    bw = int(min(max(tot, LA.shape[1]) + 140, ZX1 - ZX0 - 60)); bh = 250
    bd = Image.new('RGBA', (bw + 80, bh + 80), (0, 0, 0, 0)); ImageDraw.Draw(bd).rounded_rectangle((40, 40, 40 + bw, 40 + bh), 60, fill=(0, 0, 0, 150))
    BD = A(bd.filter(ImageFilter.GaussianBlur(22)))
    caps.append((s0, s1, LA, WL, tot, BD))
DIAG = XX + YY * 0.55
FLASH_T = [2.6, 5.4, 8.2, 9.6, 12.0, 14.4]; PUNCH = [0] + FLASH_T
# прогресс 5 шагов: золотые точки над подписью
DOT_Y = CAPY_A - 34
def wordfx(blurs, tt):
    p = min(max(tt / 0.32, 0), 1); i = 0 if p > 0.75 else (1 if p > 0.4 else 2)
    return blurs[i], 0.7 + 0.3 * eback(p), ease(p)
def dots(fr, t):
    k = max(i for i, s in enumerate(STEPS) if s[0] <= t + 1e-6); n = len(STEPS); gap = 34; x0 = 512 - gap * (n - 1) / 2
    for i in range(n):
        r = 9 if i == k else 6; col = (214, 183, 124) if i <= k else (255, 255, 255)
        a = 1.0 if i <= k else 0.45
        if i == k: r = int(6 + 5 * eback(min((t - STEPS[k][0]) / 0.3, 1)))
        d = np.zeros((2 * r + 6, 2 * r + 6, 4), np.float32); cy = cx = r + 3
        m = ((np.arange(2 * r + 6)[:, None] - cy) ** 2 + (np.arange(2 * r + 6)[None, :] - cx) ** 2) <= r * r
        d[m, :3] = col; d[m, 3] = 255
        comp(fr, d, int(x0 + gap * i - cx), DOT_Y - cy, a)
def corner(fr, t):
    q = ease((t - LOGO_IN) / 0.35) * (1 - ease((t - 9.45) / 0.2) + ease((t - 11.9) / 0.3) if 9.45 <= t < 12.2 else 1)   # на кадре киоска логотип уходит: там вывеска DJIGIT, угловой не налезает на неё
    CL = CORNER
    for st in SWEEPS:
        if st <= t < st + 1.0:
            CL = CORNER.copy(); x0_, y0_, x1_, y1_ = HXY; CL[y0_:y1_, x0_:x1_] = shimmer(CORNER[y0_:y1_, x0_:x1_], (t - st) / 1.0, 40); break
    sc = 0.7 + 0.3 * eback((t - LOGO_IN) / 0.45) if t < LOGO_IN + 0.45 else 1.0
    comp_c(fr, CL, LDX + CL.shape[1] / 2, LDY + CL.shape[0] / 2, sc, q, log=False)
NL = []
for s0, s1, n, ti, jk, bgk in NUMS:
    NLn = A(tlayer(n, 900, 340, gold=True, maxw=800)); NT = tlayer(ti, 900, 120 if len(ti) < 10 else 100, fill=(255, 255, 255, 255) if n != '1' else None, gold=(n == '1'), maxw=820)
    NTb = [A(NT.filter(ImageFilter.GaussianBlur(r))) for r in (0, 4, 9)]; NJ = A(tlayer(jk, 600, 54, fill=(255, 255, 255, 255), maxw=820))
    NL.append((s0, s1, NLn, NTb, NJ))
def numscene(fr, t):
    for s0, s1, NLn, NTb, NJ in NL:
        if s0 <= t < s1:
            tt = t - s0; T = s1 - s0; out = 1 - ease((tt - (T - 0.25)) / 0.25) if tt > T - 0.25 else 1
            so = 1 + 0.08 * (1 - out)
            Ln = shimmer(NLn, (tt - 0.45) / 0.8) if 0.45 < tt < 1.25 else NLn
            comp_c(fr, Ln, 512, 600, (0.55 + 0.45 * eback(tt / 0.4)) * so, out)   # цифра видна с первого кадра сцены (без пустого кадра)
            L, s, al = wordfx(NTb, tt - 0.3); comp_c(fr, L, 512, 850, s * so, al * out)
            lw = int(min(NTb[0].shape[1] - 60, 700) * ease((tt - 0.55) / 0.4))
            if lw > 2:
                ln = np.zeros((5, lw, 4), np.float32); ln[..., :3] = (200, 165, 100); ln[..., 3] = 230; comp(fr, ln, 512 - lw // 2, 935, out)
            ja = ease((tt - 0.8) / 0.35) * out; comp_c(fr, NJ, 512, 1010 + int(25 * (1 - ease((tt - 0.8) / 0.35))), so, ja)
IMG = {}
for k, fn in (('kiosk', 'kiosk.webp'), ('box', 'box.jpg'), ('hand', 'hand.webp')):
    im = Image.open(D + '/src/' + fn).convert('RGB').resize((int(W * 1.2), int(H * 1.2)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
    IMG[k] = np.array(im); IMG[k + '_bl'] = (np.array(im.filter(ImageFilter.GaussianBlur(22))).astype(np.float32) * 0.42).astype(np.uint8)
def kb(img, z, cx, cy):   # кен бёрнс: кроп 1/z от кадра 1.2x вокруг (cx,cy)
    h, w = img.shape[:2]; cw, ch = int(W * 1.2 / z), int(H * 1.2 / z); cw, ch = min(cw, w), min(ch, h)
    x0 = int(np.clip(cx * w - cw / 2, 0, w - cw)); y0 = int(np.clip(cy * h - ch / 2, 0, h - ch))
    return cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_AREA)
def bg(t):
    if t < HOOK_END: return kb(IMG['box'], 1.2 + 0.08 * ease(t / HOOK_END), 0.42, 0.62)
    for s0, s1, n, ti, jk, bgk in NUMS:
        if s0 <= t < s1: return kb(IMG[bgk + '_bl'], 1.2 + 0.05 * (t - s0) / (s1 - s0), 0.5, 0.5)
    if t < 12.0: q = (t - 9.6) / 2.4; return kb(IMG['kiosk'], 1.2 + 0.1 * q, 0.5, 0.45 + 0.05 * q)
    if t < 14.4: q = (t - 12.0) / 2.4; return kb(IMG['box'], 1.2 + 0.12 * q, 0.45 + 0.1 * q, 0.55)
    q = (t - 14.4) / 2.6; return kb(IMG['hand'], 1.2 + 0.1 * q, 0.5, 0.5)
def frame(f, t):
    pp = max(k for k in PUNCH if k <= t + 1e-6); tl = t - pp
    z = 1.0 + (0.06 * (1 - ease(tl / 0.35)) if pp > 0 else 0.04 * ease(t / 3.0)) + 0.015 * ((t % 5) / 5)
    cw, ch = int(W / z), int(H / z); x0 = (W - cw) // 2; y0 = (H - ch) // 2
    fr = cv2.resize(f[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    for ft in FLASH_T:   # радиальный зум-блюр на склейке шагов
        if 0 <= t - ft < 0.2:
            k = 1 - (t - ft) / 0.2; acc = fr.copy(); n = 1
            for zz in (1.025, 1.05, 1.075):
                z2 = 1 + (zz - 1) * k; c2w, c2h = int(W / z2), int(H / z2); xa, ya = (W - c2w) // 2, (H - c2h) // 2
                acc += cv2.resize(fr[ya:ya + c2h, xa:xa + c2w], (W, H), interpolation=cv2.INTER_LINEAR); n += 1
            fr = acc / n
    for ft in FLASH_T:
        if 0 <= t - ft < 0.38:
            q = (t - ft) / 0.38; c = -300 + q * (W + H * 0.55 + 600); band = np.clip(1 - np.abs(DIAG - c) / 260, 0, 1)[..., None] * 0.35 * (1 - q * 0.5)
            fr = fr + (np.array([255, 214, 150], np.float32) - fr) * band
    if t < HOOK_END:  # правило №4: крючок полностью виден с кадра 0
        a = 1.0 if t < HOOK_END - 0.25 else 1 - ease((t - (HOOK_END - 0.25)) / 0.25)
        if STYLE == 'B': fr = fr * (1 - TOPG * a)
        sc = 0.97 + 0.03 * ease(t / 0.6) if t < HOOK_END - 0.25 else 1 - 0.06 * ease((t - (HOOK_END - 0.25)) / 0.25)   # кадр 0 читается, плашка «садится», уходит вглубь
        G = hook_group(t)
        if t > HOOK_END - 0.25: G = A(Image.fromarray(np.clip(G, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6 * ease((t - (HOOK_END - 0.25)) / 0.25))))
        comp_c(fr, G, PX + PW / 2, PY + PH / 2, sc, a)
    if t >= LOGO_IN:
        g = min(1, ease((t - LOGO_IN) / 0.3)); fr = fr * (CDARK * g + (1 - g)); corner(fr, t)   # Вал 27.11: без затемнения под шагами
    numscene(fr, t)
    for s0, s1, LA, WL, tot, BD in caps:
        if s0 <= t < s1:
            tt = t - s0; T = s1 - s0; out = 1 - ease((tt - (T - 0.22)) / 0.22) if tt > T - 0.22 else 1
            aa = ease(tt / 0.3) * out; dy = int(30 * (1 - ease(tt / 0.3)))
            LAs = shimmer(LA, min(max((tt - 0.3) / 0.9, 0), 1)) if 0.3 < tt < 1.2 else LA
            comp_c(fr, LAs, 512, CAPY_A + dy + LA.shape[0] / 2, 0.6 + 0.4 * eback(tt / 0.35), aa)
            for k, (blurs, cx) in enumerate(WL):
                L, s, al = wordfx(blurs, tt - 0.12 - 0.08 * k); Ls = scaled(L, s)
                comp(fr, Ls, cx - Ls.shape[1] // 2, CAPY_B + (L.shape[0] - Ls.shape[0]) // 2, al * out)
            lw = int(tot * ease((tt - 0.35) / 0.4))
            if lw > 2:
                ln = np.zeros((5, lw, 4), np.float32); ln[..., :3] = (200, 165, 100); ln[..., 3] = 230
                comp(fr, ln, 512 - lw // 2, CAPY_B + 112, out)
            dots(fr, t)
    return fr
BTN = 'ПИШИ «ХОЧУ ОТКРЫТЬ» В ДИРЕКТ'
EL = tpl.end_layers(btnt=BTN)
_b, _bxy = EL['btn']; _b = Image.new('RGBA', _b.size, (0, 0, 0, 0)); ImageDraw.Draw(_b).rounded_rectangle((0, 0, _b.width - 1, _b.height - 1), 34, fill=(184, 146, 82, 255))
_sz = 40
while True:
    _t = tpl._ink(BTN, 900, _sz)
    if _t.width <= _b.width - 70: break
    _sz -= 1
_b.alpha_composite(tpl.colorize(_t, (20, 15, 8)), ((_b.width - _t.width) // 2, (_b.height - _t.height) // 2)); EL['btn'] = (_b, _bxy)
Lend = {k: (A(im), xy) for k, (im, xy) in EL.items()}
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((290, 380, 790, 880), fill=(214, 170, 100, 90)); GLOW = A(glow.filter(ImageFilter.GaussianBlur(90)))
order = [('dj', 0.25), ('sub', 0.4), ('q1', 0.55), ('q2', 0.62), ('btn', 0.78), ('site', 0.92)]
def endframe(src, t, last=None):
    bg = A(Image.eval(Image.fromarray(src).filter(ImageFilter.GaussianBlur(28)), lambda v: int(v * 0.5)))
    m = ease(t / 0.3); fr = bg * m + (last.astype(np.float32) * (1 - m) if last is not None else 0); pulse = 0.85 + 0.15 * np.sin(t * 2 * np.pi / 1.6)
    comp(fr, GLOW, 0, 0, ease(t / 0.6) * pulse, log=False)
    hl, (hx, hy) = Lend['horse']; hs = shimmer(hl, (t - 0.9) / 1.0, 70) if 0.9 < t < 1.9 else hl
    comp_c(fr, hs, hx + hl.shape[1] / 2, hy + hl.shape[0] / 2, 0.8 + 0.2 * eback(t / 0.5), ease(t / 0.35))
    for k, d in order:
        lay, (x, y) = Lend[k]; aa = ease((t - d) / 0.35); dy = int(35 * (1 - aa))
        if k == 'dj':   # DJIGIT открывается шторкой слева направо
            if 0.6 < t < 1.5: lay = shimmer(lay, (t - 0.6) / 0.9)
            wv = int(lay.shape[1] * ease((t - d) / 0.45))
            if wv > 2: comp(fr, lay[:, :wv], x, y, 1.0)
            continue
        if k == 'btn':   # кнопка: поп с отскоком, блик раз в 1.6 с, волна-обводка
            if t < d: continue
            sc = 0.5 + 0.5 * eback((t - d) / 0.4) if t < d + 0.4 else 1 + 0.02 * np.sin((t - d - 0.4) * 2 * np.pi / 1.2)
            ph = ((t - d - 0.5) % 1.6) / 0.7
            L2 = shimmer(lay, ph, 60) if (t > d + 0.5 and ph < 1) else lay
            comp_c(fr, L2, x + lay.shape[1] / 2, y + lay.shape[0] / 2, sc, aa)
            for r0 in (d + 0.5, d + 1.7):
                q = (t - r0) / 0.9
                if 0 < q < 1:
                    gx = int(36 * ease(q)); bw, bh = lay.shape[1] + 2 * gx, lay.shape[0] + 2 * gx
                    ring = Image.new('RGBA', (bw + 8, bh + 8), (0, 0, 0, 0)); ImageDraw.Draw(ring).rounded_rectangle((4, 4, bw + 3, bh + 3), 34 + gx, outline=(214, 183, 124, 255), width=3)
                    comp(fr, A(ring), x - gx - 4, y - gx - 4, (1 - q) * 0.9)
            continue
        comp(fr, lay, x, y + dy, aa)
    return fr
if __name__ == '__main__':
    PREV = os.environ.get('PREVIEW'); LAST = bg(END_T - 0.01); ENDBG = kb(IMG['hand'], 1.2, 0.5, 0.5)
    def render(i):
        _box[0] = None; t = i / FPS
        fr = frame(bg(t), t) if t < END_T else endframe(ENDBG, t - END_T, frame(LAST, END_T - 0.01))
        return np.clip(fr, 0, 255).astype(np.uint8)
    if PREV:
        for x in PREV.split(','):
            i = int(round(float(x) * FPS)); Image.fromarray(render(i)).save(f'{WK}/p_{float(x):05.2f}.jpg', quality=90)
        sys.exit()
    dur = NV / FPS
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-ss', '12', '-t', f'{dur:.3f}', '-i', MUS,
                            '-map', '0:v', '-map', '1:a', '-af', f'afade=t=in:d=0.15,afade=t=out:st={dur - 0.7:.2f}:d=0.7',
                            '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
                            '-map_metadata', '-1', '-fflags', '+bitexact', '-flags:v', '+bitexact', '-flags:a', '+bitexact', '-shortest',
                            '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    for i in range(NV):
        enc.stdin.write(render(i).tobytes())
        b = _box[0]
        if b: ZLOG.append(['f%d' % i] + [int(v) for v in b])
    enc.stdin.close(); enc.wait()
    json.dump({'zone': [ZX0, ZY0, ZX1, ZY1], 'logo': CORNER_BOX, 'frames': ZLOG, 'photo': [('src', 1.0)]}, open(WK + '/zone_log.json', 'w'))
    print('done', NV, 'logo', CORNER_BOX)
