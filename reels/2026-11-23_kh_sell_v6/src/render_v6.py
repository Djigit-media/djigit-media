# Продающий KHINKALI HOUSE v6 (23.11.2026). Фирменный стиль: brand.py + tpl.py (как Чашушули v2 / Карп v6 / KH v5).
# Каждое фото один раз. Фото 4:5 идут «карточкой» в нормальном размере на размытом фоне с плавным наездом, 9:16 на весь экран.
import sys, os, json, math, subprocess, numpy as np, cv2
sys.path.insert(0, '/home/claude/work/prev'); sys.path.insert(0, '/home/claude/work/tpl'); sys.path.insert(0, os.path.dirname(__file__))
import brand, tpl
from beats import BEATS
from PIL import Image, ImageDraw, ImageFilter
W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); OLD = os.path.join(ROOT, '..', '2026-11-22_kh_sell')
OUT = os.environ.get('OUT', os.path.join(ROOT, 'KH_sell_v6_noaudio.mp4'))

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
WHITE = (255, 255, 255, 255)

# ---------- фото ----------
SRC = {
 'hook': ('ph2/IMG_3685.jpeg', None), 'p1': ('ph/p1.png', None), 'menu': ('ph2/IMG_3203.jpeg', None),
 'kiosk': ('ph3/kiosk_logo.png', None), 'facade': ('ph3/facade_logo.png', None),
 'black': ('ph2/IMG_3688.jpeg', None), 'green': ('ph2/IMG_3690.jpeg', None), 'classic': ('ph2/IMG_3691.jpeg', None),
 'cherry': ('ph2/IMG_3693.jpeg', None), 'blue': ('ph2/IMG_3684.jpeg', None), 'rasp': ('ph2/IMG_3692.jpeg', None),
 'sphere': ('ph/n2.png', None), 'cheb': ('ph3/chebureki.png', None), 'don': ('ph3/doner.png', None),
 'khach': ('ph/p5_fix.png', None), 'queue': ('ph/p4.png', None), 'film': ('ph/p10_fix.png', None),
 'kitchen': ('ph2/IMG_3268.jpeg', (0, 0, 928, 1020)), 'courier': ('ph/p3.png', None), 'frozen': ('ph/p2.png', None),
 'hand': ('ph/p7.png', None),
 # только размытым фоном под текстовыми сценами
 'b_mall': ('ph2/IMG_3266.jpeg', None), 'b_terr': ('ph2/IMG_3273.jpeg', None), 'b_cafe': ('ph2/IMG_3259.jpeg', None), 'b_don2': ('ph3/doner2.png', None),
}
def path(p): return os.path.join(ROOT, p) if p.startswith('ph3') else os.path.join(OLD, p)
RAW = {}
for k, (p, crop) in SRC.items():
    im = Image.open(path(p)).convert('RGB')
    if crop: im = im.crop(crop)
    RAW[k] = im
def cover(im, sc_extra=1.0):
    sc = max(W * sc_extra / im.width, H * sc_extra / im.height)
    return im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
FULL = {k: im for k, im in RAW.items() if im.width / im.height < 0.62}   # 9:16, на весь экран
FULLC = {k: cover(im, 1.25) for k, im in FULL.items()}
CARD = {k: im for k, im in RAW.items() if k not in FULL and not k.startswith('b_')}
CARDBIG = {k: A(im.resize((int(W * 1.1), int(W * 1.1 * im.height / im.width)), Image.LANCZOS)) for k, im in CARD.items()}
def blurbg(im, k=0.42, r=48): return A(cover(im).crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(r))) * k
BLUR = {k: blurbg(im) for k, im in RAW.items() if k not in FULL}
for k in FULL: BLUR[k] = blurbg(FULL[k])

def full_bg(key, p, z0=1.0, z1=1.08, fx=0.5, fy=0.5, dx=0.0, dy=0.0):
    im = FULLC[key]; z = z0 + (z1 - z0) * eio(p)
    cw = im.width / 1.25 / z; ch = im.height / 1.25 / z
    cx = im.width * (fx + dx * p); cy = im.height * (fy + dy * p)
    x0 = min(max(cx - cw / 2, 0), im.width - cw); y0 = min(max(cy - ch / 2, 0), im.height - ch)
    return np.array(im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))).astype(np.float32)
CARD_SHADOW = {}
def card_frame(key, p, z0, z1, cy=900, dy=0):
    fr = BLUR[key].copy(); big = CARDBIG[key]; z = z0 + (z1 - z0) * eio(p)
    cw = int(W * z); ch = int(big.shape[0] * cw / big.shape[1])
    L = cv2.resize(big, (cw, ch), interpolation=cv2.INTER_AREA)
    y = int(cy + dy * p - ch / 2); x = (W - cw) // 2
    # мягкая тень под карточкой
    sh = CARD_SHADOW.get((key, cw // 8))
    if sh is None:
        m = np.zeros((H, W), np.float32); y0c = max(0, int(cy - ch / 2) + 18); m[y0c:min(H, y0c + ch), max(0, x):min(W, x + cw)] = 1
        sh = cv2.GaussianBlur(m, (0, 0), 30)[..., None] * 0.55; CARD_SHADOW[(key, cw // 8)] = sh
    fr = fr * (1 - sh)
    y0, y1 = max(y, 0), min(y + ch, H); x0, x1 = max(x, 0), min(x + cw, W)
    fr[y0:y1, x0:x1] = L[y0 - y:y1 - y, x0 - x:x1 - x]
    return fr
def shot_img(key, p, z0, z1, fx, fy, dx, dy, cy=900):
    if key in FULL: return full_bg(key, p, z0, z1, fx, fy, dx, dy)
    return card_frame(key, p, z0, z1, cy, dy * 300)

# ---------- таймлайн по голосу ----------
VO = os.path.join(ROOT, 'vo')
KEYS = [k for k, _ in BEATS]
def dur(f): return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout)
durs = [dur(f'{VO}/{i:02d}_{k}.wav') for i, k in enumerate(KEYS)]
GAP = 0.22
starts = []; t = 0.0
MINL = {'slot': 2.3, 'end': 0}
for k_, d in zip(KEYS, durs): starts.append(t); t += max(d + GAP, MINL.get(k_, 2.3))
B = {k: i for i, k in enumerate(KEYS)}
END_START = starts[B['end']]
TOTAL = starts[-1] + durs[-1] + 1.6
json.dump({'keys': KEYS, 'starts': starts, 'durs': durs, 'total': TOTAL, 'end_start': END_START}, open(os.path.join(ROOT, 'timeline_v6.json'), 'w'), ensure_ascii=False)
def BL(i): return starts[i + 1] - starts[i]

# ---------- фирменные слои ----------
CORNER = A(tpl.corner_layer().crop((0, 0, 460, 480)))
HB = tpl.CORNER['horse']; HXY = (HB[0] - 12, HB[1] - 12, HB[2] + 13, HB[3] + 13)
LOGO_IN = starts[1]
SWEEPS = [LOGO_IN + 0.5 + 6 * k for k in range(40)]
PY, PH_ = 255, 600
PLATE = A(brand.plate(990, PH_, 34))
HT1 = A(tlayer('СУПЕР АКЦИЯ', 900, 108, gold=True, maxw=900))
HT2 = A(tlayer('ДЛЯ ПЕРВЫХ 3 ПАРТНЁРОВ', 900, 108, gold=True, maxw=900))
HT3 = A(tlayer('ФРАНШИЗА', 900, 124, gold=True, maxw=900))
HT4 = A(tlayer('KHINKALI HOUSE В ТВОЁМ ГОРОДЕ', 800, 52, fill=WHITE, maxw=900))
TY = [PY + 26, PY + 150, PY + 285, PY + 470]
yy_ = np.arange(H); grad = np.zeros((H, W, 1), np.float32)
grad[:, :, 0] = np.maximum(np.clip((yy_ - 1050) / 600, 0, 1) ** 1.2 * 0.75, np.clip(1 - yy_ / 560, 0, 1) ** 1.5 * 0.45)[:, None]
CAPY_A, CAPY_B, LINE_H = 1395, 1477, 88
def fit_sz(texts, sz=70):
    while max(brand.width(t, 900, sz) for t in texts) > 1000: sz -= 2
    return sz
def words_layer(text, sz=70):
    words = text.split(' '); sp = brand.width(' ', 900, sz); tot = brand.width(text, 900, sz); x = 540 - tot / 2; WL = []
    for wd in words:
        L = tlayer(wd, 900, sz, fill=WHITE); ww = brand.width(wd, 900, sz)
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

def SH(f, key, a, b, fx=.5, fy=.5, dx=0, dy=0, cy=900): return (f, key, a, b, fx, fy, dx, dy, cy)
# у каждого блока своё движение: наезд / отъезд / сдвиг
SHOTS = {
 'what': [SH(0, 'p1', .94, 1.04, .5, .62)],
 'all': [SH(0, 'menu', 1.0, 1.07)],
 'k1': [SH(0, 'kiosk', 1.07, 1.0, cy=1060)],
 'k2': [SH(0, 'facade', 1.0, 1.07, cy=1060)],
 's1': [SH(0, 'black', 1.0, 1.08)],
 's2': [SH(0, 'green', 1.08, 1.0)],
 's3': [SH(0, 'classic', 1.0, 1.08, dy=.08)],
 'd1': [SH(0, 'cherry', 1.0, 1.07), SH(.5, 'blue', 1.07, 1.0)],
 'd2': [SH(0, 'rasp', 1.0, 1.09)],
 'sph': [SH(0, 'sphere', 1.12, 1.2, .5, .8)],
 'cheb': [SH(0, 'cheb', 1.08, 1.0)],
 'don': [SH(0, 'don', 1.0, 1.08)],
 'kha': [SH(0, 'khach', .96, 1.04, .5, .66, 0, -.04)],
 'gst': [SH(0, 'queue', 1.03, .95, .45, .55)],
 'wow': [SH(0, 'film', .94, 1.03, .45, .45)],
 'prt': [SH(0, 'kitchen', 1.0, 1.07)],
 'src1': [SH(0, 'courier', .95, 1.03, .45, .5), SH(.52, 'frozen', 1.03, .95, .5, .5)],
 'net': [SH(0, 'hand', 1.14, 1.22, .5, .78)],
}
CAPS = {
 'what': ('KHINKALI HOUSE', 'СТРИТФУД СОВРЕМЕННОЙ', 'ГРУЗИНСКОЙ КУХНИ'),
 'all': ('ДЛЯ ВСЕХ', 'КРАСИВО • ВКУСНО', 'БЫСТРО • НЕДОРОГО'),
 'k1': ('ФОРМАТ 1', 'КИОСК ОТ 10 М²', 'НА УЛИЦЕ ИЛИ В ТОРГОВОМ ЦЕНТРЕ'),
 'k2': ('ФОРМАТ 2', 'ФАСАДНОЕ ПОМЕЩЕНИЕ ОТ 80 М²', 'ЗАЛ И ЛЕТНЯЯ ПЛОЩАДКА'),
 's1': ('СОЛЁНЫЕ ХИНКАЛИ', 'ЧЁРНЫЕ НА ЧЕРНИЛАХ КАРАКАТИЦЫ', 'С МОРЕПРОДУКТАМИ'),
 's2': ('СОЛЁНЫЕ ХИНКАЛИ', 'ЗЕЛЁНЫЕ', 'СО ШПИНАТОМ И СЫРОМ'),
 's3': ('СОЛЁНЫЕ ХИНКАЛИ', 'КЛАССИЧЕСКИЕ', 'С МЯСОМ И БУЛЬОНОМ'),
 'd1': ('СЛАДКИЕ ХИНКАЛИ', 'КЛУБНИКА • ВИШНЯ', 'ЧЕРНИКА • МАЛИНА'),
 'd2': ('СЛАДКИЕ ХИНКАЛИ', 'ВНУТРИ НАСТОЯЩИЕ ЯГОДЫ', 'НАТУРАЛЬНЫЕ КРАСИТЕЛИ'),
 'sph': ('ВАУ-БЛЮДО', 'ЧЕБУРЕК-СФЕРА', 'ГОСТЬ СЖИМАЕТ ЕЁ В РОЛЛ'),
 'cheb': ('ЧЕБУРЕКИ', 'С ТЕЛЯТИНОЙ • С БАРАНИНОЙ', 'С СУЛУГУНИ'),
 'don': ('ДОНЕРЫ', 'СОЛЁНЫЕ', 'И СЛАДКИЕ'),
 'kha': ('А ЕЩЁ', 'ХАЧАПУРИ', 'И СВЕЖИЕ САЛАТЫ'),
 'gst': ('ЧТО ПОЛУЧАЕТ ГОСТЬ', 'НЕОБЫЧНО • ВКУСНО • НЕДОРОГО', 'ВЫДАЧА ЗА 3–5 МИНУТ'),
 'wow': ('ВАУ-ЭФФЕКТ', 'ГОСТИ САМИ СНИМАЮТ', 'И РЕКЛАМИРУЮТ ТВОЮ ТОЧКУ'),
 'prt': ('ЧТО ПОЛУЧАЕТ ПАРТНЁР', 'ЕДА НУЖНА ВСЕГДА', 'ГРУЗИНСКУЮ КУХНЮ ОСОБЕННО ЛЮБЯТ'),
 'src1': ('5 ИСТОЧНИКОВ ДОХОДА', 'ЗАЛ • ДОСТАВКА', 'ЛЕТНЯЯ ПЛОЩАДКА • ЗАМОРОЗКА ДОМОЙ'),
 'net': ('ПРИСОЕДИНЯЙСЯ К НАШЕЙ СЕТИ', 'СИЛЬНЫЕ ЛЮДИ ВМЕСТЕ', 'ДОСТИГАЮТ БОЛЬШИХ ВЫСОТ'),
}
for c in CAPS.values(): mkcap(c)

def shot_of(key, lt, L):
    sh = SHOTS[key]; f = lt / L; i = max(j for j, s in enumerate(sh) if f >= s[0] - 1e-9)
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

# ---------- переходы ----------
def whip(fr, q):
    k = 1 + 2 * int(70 * (1 - q) / 2); sh = int(W * 0.22 * (1 - ease(q)))
    return cv2.blur(np.roll(fr, sh, axis=1), (k, 1)) if k > 1 else fr
def vflash(fr, q, k):
    c = -200 + q * (H + 400); band = np.clip(1 - np.abs(YY - c) / 200, 0, 1)[..., None] * 0.35 * k * (1 - q * 0.5)
    return fr + (np.array([255, 214, 150], np.float32) - fr) * band
def punch(fr, q, amt):
    z = 1.0 + amt * (1 - ease(q)); cw, ch = int(W / z), int(H / z); x0 = (W - cw) // 2; y0 = (H - ch) // 2
    return cv2.resize(fr[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR)
def flash(fr, q, k):
    c = -300 + q * (W + H * 0.55 + 600); band = np.clip(1 - np.abs(DIAG - c) / 260, 0, 1)[..., None] * 0.35 * k * (1 - q * 0.5)
    return fr + (np.array([255, 214, 150], np.float32) - fr) * band
def trans(fr, st, kind, k):
    q = st / 0.38
    if kind == 0: return flash(punch(fr, st / 0.35, 0.06 * k) if st < 0.35 else fr, q, k)
    if kind == 1: fr = punch(fr, st / 0.35, 0.08 * k) if st < 0.35 else fr; return fr + (255 - fr) * (0.3 * k * (1 - q))
    if kind == 2: return whip(fr, q)
    return vflash(punch(fr, st / 0.35, 0.05 * k) if st < 0.35 else fr, q, k)

def brand_dark(fr, t):
    m = min(1, ease((t - LOGO_IN) / 0.3))
    return fr * (1 - grad * m) * (1 - (1 - CDARK) * m * 0.6)
def corner(fr, t):
    q = ease((t - LOGO_IN) / 0.35); CL = CORNER
    for stt in SWEEPS:
        if stt <= t < stt + 1.0:
            CL = CORNER.copy(); x0_, y0_, x1_, y1_ = HXY; CL[y0_:y1_, x0_:x1_] = shimmer(CORNER[y0_:y1_, x0_:x1_], (t - stt) / 1.0, 45); break
    comp(fr, CL, 0, 0, q)

# ---------- сцена «два формата: деньги» ----------
TB_PL = A(brand.plate(990, 1010, 34))
TB_K = A(tlayer('КИОСК', 900, 64, gold=True)); TB_F = A(tlayer('ФАСАДНОЕ', 900, 64, gold=True, maxw=440))
TB_KS = A(tlayer('от 10 м²', 700, 40, fill=WHITE)); TB_FS = A(tlayer('от 80 м²', 700, 40, fill=WHITE))
TB_R1 = A(tlayer('ВЛОЖЕНИЯ ПОД КЛЮЧ', 800, 40, fill=WHITE))
TB_R1K = A(tlayer('20 000 €', 900, 84, gold=True, maxw=430)); TB_R1F = A(tlayer('45 000 €', 900, 84, gold=True, maxw=430))
TB_R2 = A(tlayer('ЧИСТАЯ ПРИБЫЛЬ В МЕСЯЦ', 800, 40, fill=WHITE))
TB_R2K = A(tlayer('3 000 €', 900, 104, gold=True, maxw=440)); TB_R2F = A(tlayer('10 000 €', 900, 104, gold=True, maxw=440))
TB_PAY = A(tlayer('ОКУПАЕМОСТЬ ДО 1 ГОДА', 900, 56, fill=WHITE, maxw=860))
def pill(w, h):
    p = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(p).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=(184, 146, 82, 255)); return A(p)
TB_PILL = pill(880, 120)
TB_PAYD = A(tlayer('ОКУПАЕМОСТЬ ДО 1 ГОДА', 900, 56, fill=(20, 15, 8, 255), maxw=820, shadow=0))
def pop(fr, L, cx, cy, q, shim_t=None, big=1.6):
    if q <= 0: return
    sc = big - (big - 1) * eback(min(1, q), 2.2); Ln = scaled(L, sc)
    if shim_t is not None and 0 < shim_t < 1: Ln = shimmer(Ln, shim_t, 120)
    comp(fr, Ln, cx - Ln.shape[1] // 2, cy - Ln.shape[0] // 2, min(1, q * 3))
def table_scene(fr, t):
    t0 = starts[B['inv']]; t1 = starts[B['prof']]; lt = t - t0; Lall = starts[B['prof'] + 1] - t0
    out = 1 - ease((lt - (Lall - 0.22)) / 0.22) if lt > Lall - 0.22 else 1
    a = ease(lt / 0.3) * out; Y0 = 470
    comp(fr, TB_PL, 45, Y0, a)
    for L, cx, y in ((TB_K, 300, Y0 + 40), (TB_F, 780, Y0 + 40)): comp(fr, L, cx - L.shape[1] // 2, y + int(20 * (1 - ease(lt / .35))), a)
    for L, cx, y in ((TB_KS, 300, Y0 + 132), (TB_FS, 780, Y0 + 132)): comp(fr, L, cx - L.shape[1] // 2, y, ease((lt - .2) / .35) * out)
    vl = int(820 * ease((lt - .15) / .5)); ln = np.zeros((max(vl, 1), 3, 4), np.float32); ln[..., :3] = (200, 165, 100); ln[..., 3] = 200
    if vl > 2: comp(fr, ln, 539, Y0 + 40, out)
    for y in (Y0 + 215, Y0 + 520):
        hl = int(900 * ease((lt - .25) / .5)); h2 = np.zeros((2, max(hl, 1), 4), np.float32); h2[..., :3] = (200, 165, 100); h2[..., 3] = 160
        if hl > 2: comp(fr, h2, 540 - hl // 2, y, out)
    # строка 1: вложения (с голосом «вложения под ключ»)
    q1 = (lt - 0.35) / 0.35
    if q1 > 0: comp(fr, TB_R1, 540 - TB_R1.shape[1] // 2, Y0 + 238, ease(q1) * out)
    dk = durs[B['inv']]
    for L, cx, tt in ((TB_R1K, 300, .38 * dk), (TB_R1F, 780, .72 * dk)):
        q = (lt - tt) / 0.45
        if q > 0: pop(fr, L, cx, Y0 + 395, q, (lt - tt - .45) / 1.0)
    # строка 2: прибыль
    lt2 = t - t1; dp = durs[B['prof']]
    if lt2 > 0:
        comp(fr, TB_R2, 540 - TB_R2.shape[1] // 2, Y0 + 545, ease(lt2 / .35) * out)
        for L, cx, tt in ((TB_R2K, 300, .22 * dp), (TB_R2F, 780, .5 * dp)):
            q = (lt2 - tt) / 0.45
            if q > 0:
                pop(fr, L, cx, Y0 + 715, q, (lt2 - tt - .45) / 1.0, 1.7)
                if lt2 - tt < 0.15: fr[:] = fr + (255 - fr) * (0.3 * (1 - (lt2 - tt) / 0.15))
        qp = (lt2 - .76 * dp) / 0.4
        if qp > 0:
            s = 0.7 + 0.3 * eback(min(1, qp)); P = scaled(TB_PILL, s); D = scaled(TB_PAYD, s)
            comp(fr, P, 540 - P.shape[1] // 2, Y0 + 875 + (120 - P.shape[0]) // 2, ease(qp) * out)
            if 0.4 < lt2 - .76 * dp < 1.4: D = shimmer(D, (lt2 - .76 * dp - .4), 100)
            comp(fr, D, 540 - D.shape[1] // 2, Y0 + 875 + (120 - D.shape[0]) // 2 - 4, ease(qp) * out)
    return fr

# ---------- сцена «30%» ----------
P30_PL = A(brand.plate(990, 760, 34))
P30_T = A(tlayer('5-Й ИСТОЧНИК ДОХОДА', 900, 58, gold=True, maxw=900))
P30_N = A(tlayer('30%', 900, 260, gold=True, maxw=900))
P30_A = A(tlayer('ВЗНОСА ЗА КАЖДОГО', 800, 56, fill=WHITE, maxw=900)); P30_B = A(tlayer('ПРИВЕДЁННОГО ПАРТНЁРА', 800, 56, fill=WHITE, maxw=900))
def p30_scene(fr, lt, L):
    out = 1 - ease((lt - (L - 0.22)) / 0.22) if lt > L - 0.22 else 1; Y0 = 480
    comp(fr, P30_PL, 45, Y0, ease(lt / .3) * out)
    comp(fr, P30_T, 540 - P30_T.shape[1] // 2, Y0 + 45 + int(20 * (1 - ease(lt / .35))), ease(lt / .35) * out)
    q = (lt - .55) / .45
    if q > 0:
        pop(fr, P30_N, 540, Y0 + 320, q, (lt - 1.0) / 1.0, 1.8)
        if lt - .55 < .15: fr[:] = fr + (255 - fr) * (0.35 * (1 - (lt - .55) / .15))
    for j, Lr in enumerate((P30_A, P30_B)):
        qq = (lt - 1.0 - .15 * j) / .35
        if qq > 0: comp(fr, Lr, 540 - Lr.shape[1] // 2, Y0 + 520 + 80 * j + int(20 * (1 - ease(qq))), ease(qq) * out)
    return fr

# ---------- сцена «защита + Германия» ----------
LQ_PA = A(brand.plate(990, 380, 34)); LQ_PB = A(brand.plate(990, 420, 34))
LQ = [A(tlayer('ЗАЩИТА ВЛОЖЕНИЙ', 900, 54, gold=True)), A(tlayer('ЛИКВИДНЫЙ АКТИВ', 900, 92, fill=WHITE, maxw=900)), A(tlayer('ГОТОВУЮ ТОЧКУ ВСЕГДА МОЖНО ПРОДАТЬ', 700, 38, fill=(225, 225, 225, 255), maxw=900))]
DE = [A(tlayer('ГЕРМАНИЯ', 900, 54, gold=True)), A(tlayer('ГОСПОДДЕРЖКА', 900, 92, fill=WHITE, maxw=900)), A(tlayer('ЧЕРЕЗ АККРЕДИТОВАННЫХ', 700, 38, fill=(225, 225, 225, 255), maxw=900)), A(tlayer('ФИНАНСОВЫХ КОНСУЛЬТАНТОВ', 700, 38, fill=(225, 225, 225, 255), maxw=900))]
def liq_scene(fr, t):
    t0 = starts[B['liq']]; t1 = starts[B['de']]; lt = t - t0; Lall = starts[B['de'] + 1] - t0
    out = 1 - ease((lt - (Lall - 0.22)) / 0.22) if lt > Lall - 0.22 else 1; Y0 = 480
    comp(fr, LQ_PA, 45, Y0, ease(lt / .3) * out)
    if t >= t1 - 0.05: comp(fr, LQ_PB, 45, Y0 + 420, ease((t - t1 + .05) / .3) * out)
    for j, (Lr, y) in enumerate(zip(LQ, (Y0 + 50, Y0 + 140, Y0 + 270))):
        q = (lt - .1 - .25 * j) / .35
        if q > 0:
            L2 = shimmer(Lr, (lt - .9) / 1.0) if (j == 1 and 0.9 < lt < 1.9) else Lr
            comp(fr, L2, 540 - Lr.shape[1] // 2, y + int(25 * (1 - ease(q))), ease(q) * out)
    hl = int(800 * ease((t - t1 + .2) / .4)); h2 = np.zeros((2, max(hl, 1), 4), np.float32); h2[..., :3] = (200, 165, 100); h2[..., 3] = 180
    
    lt2 = t - t1
    for j, (Lr, y) in enumerate(zip(DE, (Y0 + 465, Y0 + 555, Y0 + 685, Y0 + 740))):
        q = (lt2 - .1 - .25 * j) / .35
        if q > 0:
            L2 = shimmer(Lr, (lt2 - .9) / 1.0) if (j == 1 and 0.9 < lt2 < 1.9) else Lr
            comp(fr, L2, 540 - Lr.shape[1] // 2, y + int(25 * (1 - ease(q))), ease(q) * out)
    return fr

# ---------- оффер (из v5) ----------
OF_T = A(tlayer('ТОЛЬКО ДЛЯ ПЕРВЫХ ТРЁХ', 900, 64, gold=True, maxw=900))
OF_K = A(tlayer('КИОСК', 800, 40, gold=True)); OF_F = A(tlayer('ФАСАДНОЕ', 800, 40, gold=True))
OF_O1 = A(tlayer('7 000 €', 800, 86, fill=(215, 215, 215, 255))); OF_O2 = A(tlayer('9 000 €', 800, 86, fill=(215, 215, 215, 255)))
OF_N = A(tlayer('5 000 €', 900, 210, gold=True, maxw=950)); OF_NL = A(tlayer('ВЗНОС', 800, 46, fill=WHITE))
OF_C = [A(tlayer(s, 900, 56, fill=WHITE)) for s in ('0% РОЯЛТИ 3 МЕСЯЦА', 'ДИЗАЙН-ПРОЕКТ В ПОДАРОК')]
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
SL_B = A(tlayer('ЗАЙМИ СВОЁ МЕСТО', 900, 70, fill=WHITE, maxw=950))
def offer_scene(fr, lt, L):
    out = 1 - ease((lt - (L - 0.22)) / 0.22) if lt > L - 0.22 else 1
    comp(fr, OF_PLATE, 45, 470, ease(lt / 0.3) * out)
    comp(fr, OF_T, 540 - OF_T.shape[1] // 2, 515 + int(25 * (1 - ease(lt / 0.35))), ease(lt / 0.35) * out)
    qo = ease((lt - 0.4) / 0.35)
    comp(fr, OF_K, 300 - OF_K.shape[1] // 2, 595, qo * out); comp(fr, OF_F, 780 - OF_F.shape[1] // 2, 595, qo * out)
    comp(fr, OF_O1, 300 - OF_O1.shape[1] // 2, 640, qo * out); comp(fr, OF_O2, 780 - OF_O2.shape[1] // 2, 640, qo * out)
    N0 = 0.2 * L; qn = (lt - N0) / 0.45
    if qn > 0:
        comp(fr, OF_NL, 540 - OF_NL.shape[1] // 2, 810, ease(qn) * out)
        sc = 1.7 - 0.7 * eback(min(1, qn), 2.2); Ln = scaled(OF_N, sc)
        if 0.45 < (lt - N0) < 1.45: Ln = shimmer(Ln, ((lt - N0) - 0.45) / 1.0, 120)
        shake = int(10 * math.sin(lt * 60) * max(0, 1 - (lt - N0) / 0.35)) if qn > 0.6 else 0
        comp(fr, Ln, 540 - Ln.shape[1] // 2 + shake, 1000 - Ln.shape[0] // 2, min(1, qn * 3) * out)
        if lt - N0 < 0.15: fr[:] = fr + (255 - fr) * (0.45 * (1 - (lt - N0) / 0.15))
    st = ease((lt - 0.36 * L) / 0.35)
    if st > 0:
        for cx in (300, 780):
            ln = np.zeros((12, int(300 * st) + 1, 4), np.float32); ln[..., :3] = (225, 45, 45); ln[..., 3] = 255
            comp(fr, ln, cx - 150, 718, out)
    for j, Lc in enumerate(OF_C):
        qc = (lt - (0.55 + 0.17 * j) * L) / 0.35
        if qc > 0: Ls = scaled(Lc, 0.7 + 0.3 * eback(min(1, qc))); comp(fr, Ls, 540 - Ls.shape[1] // 2, 1170 + j * 95 + (Lc.shape[0] - Ls.shape[0]) // 2, ease(qc) * out)
    for k in range(3):
        qk = (lt - 0.9 - 0.18 * k) / 0.3
        if qk > 0:
            pul = 1 + 0.06 * math.sin(lt * 5 - k * 0.9); Ls = scaled(TOK[k], (0.6 + 0.4 * eback(min(1, qk))) * pul)
            cx = 540 + (k - 1) * 190; comp(fr, Ls, cx - Ls.shape[1] // 2, 1375 + (TOK[k].shape[0] - Ls.shape[0]) // 2, ease(qk) * out)
    qs = (lt - 1.2) / 0.35
    if qs > 0: comp(fr, OF_S, 540 - OF_S.shape[1] // 2, 1515, ease(qs) * out)
    return fr
def slots_scene(fr, lt, L):
    for k in range(3):
        qk = (lt - 0.05 - 0.2 * k) / 0.3
        if qk > 0:
            pul = 1 + 0.05 * math.sin(lt * 6 - k); Ls = scaled(TOKB[k], (0.6 + 0.4 * eback(min(1, qk))) * pul)
            cx = 540 + (k - 1) * 300; comp(fr, Ls, cx - Ls.shape[1] // 2, 830 + (TOKB[k].shape[0] - Ls.shape[0]) // 2, ease(qk))
    comp(fr, SL_A, 540 - SL_A.shape[1] // 2, 600 + int(25 * (1 - ease(lt / 0.3))), ease(lt / 0.3))
    q = ease((lt - 0.7) / 0.3); comp(fr, SL_B, 540 - SL_B.shape[1] // 2, 1130 + int(25 * (1 - q)), q)
    return fr

# ---------- заставка (утверждённая) ----------
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

# ---------- кадр ----------
TEXTBG = {'inv': 'b_mall', 'prof': 'b_mall', 'src2': 'frozen', 'liq': 'b_terr', 'de': 'b_terr', 'off': 'b_cafe', 'slot': 'b_don2'}
def drift(bgimg, lt, s=0.04):
    z = 1 + s * min(lt / 6, 1); cw, ch = int(W / z), int(H / z); x0 = (W - cw) // 2; y0 = (H - ch) // 2
    return cv2.resize(bgimg[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR)
def frame(fi):
    t = fi / FPS
    i = max(j for j, s in enumerate(starts) if t >= s - 1e-9); key = KEYS[i]; lt = t - starts[i]
    if key == 'end': return None
    L = BL(i)
    if key == 'hook':
        fr = card_frame('hook', lt / L, 1.0, 1.07, cy=1150)
        a = 1.0 if lt < L - 0.25 else 1 - ease((lt - (L - 0.25)) / 0.25)
        comp(fr, PLATE, 45, PY, a)
        spp = min(max((lt - 0.6) / 1.1, 0), 1)
        for Lr, yy in ((HT1, TY[0]), (HT2, TY[1]), (HT3, TY[2])):
            comp(fr, shimmer(Lr, spp) if 0 < spp < 1 else Lr, 540 - Lr.shape[1] // 2, yy, a)
        comp(fr, HT4, 540 - HT4.shape[1] // 2, TY[3], a)
        return fr
    if key in SHOTS:
        si, st, sl, (f, k2, z0, z1, fx, fy, dx, dy, cy) = shot_of(key, lt, L)
        fr = shot_img(k2, st / sl, z0, z1, fx, fy, dx, dy, cy)
        if st < 0.38: fr = trans(fr, st, (i * 3 + si) % 4, 1.0 if si == 0 else 0.7)
        fr = brand_dark(fr, t); corner(fr, t)
        if key in CAPS: draw_caps(fr, mkcap(CAPS[key]), lt, L)
        return fr
    # текстовые сцены на размытом фоне
    first = key in ('inv', 'liq') or key not in ('prof', 'de')
    t_sc = starts[B['inv']] if key in ('inv', 'prof') else (starts[B['liq']] if key in ('liq', 'de') else starts[i])
    fr = drift(BLUR[TEXTBG[key]], t - t_sc)
    if t - t_sc < 0.38: fr = punch(fr, (t - t_sc) / 0.35, 0.06) if t - t_sc < 0.35 else fr; fr = flash(fr, (t - t_sc) / 0.38, 1.0)
    fr = brand_dark(fr, t); corner(fr, t)
    if key in ('inv', 'prof'): return table_scene(fr, t)
    if key in ('liq', 'de'): return liq_scene(fr, t)
    if key == 'src2': return p30_scene(fr, lt, L)
    if key == 'off': return offer_scene(fr, lt, L)
    if key == 'slot': return slots_scene(fr, lt, L)
    return fr

def end_bg(last): return A(Image.fromarray(np.clip(last, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28))) * 0.5

if __name__ == '__main__':
    NF = int(math.ceil(TOTAL * FPS)); EF = int(math.ceil(END_START * FPS))
    if len(sys.argv) > 1 and sys.argv[1].startswith('frames:'):
        os.makedirs(os.path.join(ROOT, 'prev'), exist_ok=True)
        for x in sys.argv[1][7:].split(','):
            fi = int(float(x) * FPS)
            img = endframe(frame(EF - 1), end_bg(frame(EF - 1)), (fi - EF) / FPS) if fi >= EF else frame(fi)
            Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(ROOT, 'prev', f'f_{float(x):06.2f}.jpg'), quality=92)
        print(json.dumps(dict(zip(KEYS, [round(s, 2) for s in starts])), ensure_ascii=False), END_START, TOTAL); sys.exit()
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'slow', '-crf', '13', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    last = None
    for fi in range(EF):
        f = frame(fi); last = f; enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
        if fi % 300 == 0: print(fi, '/', NF, flush=True)
    BG = end_bg(last)
    for j in range(NF - EF): enc.stdin.write(np.clip(endframe(last, BG, j / FPS), 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait(); print('done', NF, flush=True)
