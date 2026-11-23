# Продающий KHINKALI HOUSE v6 (23.11.2026). Фирменный стиль: brand.py + tpl.py (как Чашушули v2 / Карп v6 / KH v5).
# Каждое фото один раз. Фото 4:5 идут «карточкой» в нормальном размере на размытом фоне с плавным наездом, 9:16 на весь экран.
import sys, os, json, math, subprocess, numpy as np, cv2
sys.path.insert(0, '/home/claude/work/prev'); sys.path.insert(0, '/home/claude/work/tpl'); sys.path.insert(0, os.path.dirname(__file__))
import brand, tpl
from beats10 import BEATS
from PIL import Image, ImageDraw, ImageFilter
W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); OLD = os.path.join(ROOT, '..', '2026-11-22_kh_sell')
OUT = os.environ.get('OUT', os.path.join(ROOT, 'KH_sell_v10_noaudio.mp4'))

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
 'hook': ('ph4/IMG_5796.jpeg', (0, 330, 1080, 1350)), 'p1': ('ph/p1.png', None), 'straw': ('ph2/IMG_3685.jpeg', None),
 'kiosk': ('ph3/kiosk_eve.png', None), 'facade': ('ph3/facade_eve.png', None), 'phone': ('ph2/IMG_3259.jpeg', None),
 'black': ('ph2/IMG_3688.jpeg', None), 'green': ('ph2/IMG_3690.jpeg', None), 'classic': ('ph2/IMG_3691.jpeg', None),
 'cherry': ('ph2/IMG_3693.jpeg', None), 'blue': ('ph2/IMG_3684.jpeg', None), 'rasp': ('ph2/IMG_3692.jpeg', None),
 'sphere': ('ph/n2.png', None), 'sphere2': ('ph2/IMG_3678.jpeg', None), 'don': ('ph3/doner.png', None),
 'khach': ('ph/p5_fix.png', None), 'queue': ('ph/p4.png', None), 'film': ('ph/p10_fix.png', None),
 'courier': ('ph/p3.png', None), 'frozen': ('ph/p2.png', None), 'hand': ('ph/p7.png', None), 'board': ('ph2/IMG_2959.jpeg', None), 'kiosk2': ('ph4/62272163.png', None), 'terrace': ('ph4/3890A620.png', None),
 'ice': ('ph4/IMG_3353.png', None), 'freezer': ('ph4/FE83307F.png', None), 'girls': ('ph4/5DF26AA2.png', None), 'chef': ('ph4/F6703FE5.png', None),
 # только размытым фоном под текстовыми сценами (тёплая серия)
 'b_n1': ('ph/n1.png', None), 'b_p5': ('ph/p5.png', None), 'b_p10': ('ph/p10.png', None), 'b_p6': ('ph/p6.png', None),
}
def path(p): return os.path.join(ROOT, p) if p.startswith(('ph3', 'ph4')) else os.path.join(OLD, p)
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
PANBIG = {}
def pan_frame(key, p, d=1, cy=935, h=930):
    if key not in PANBIG:
        im = RAW[key]; hh = int(h * 1.04); PANBIG[key] = A(im.resize((int(im.width * hh / im.height), hh), Image.LANCZOS))
    big = PANBIG[key]; fr = BLUR[key].copy(); q = eio(p); z = 1.0 + 0.04 * q
    bh = int(big.shape[0] / 1.04 * z); bw = int(big.shape[1] / 1.04 * z)
    L = cv2.resize(big, (bw, bh), interpolation=cv2.INTER_AREA)
    span = max(0, bw - W); x0 = int(span * (q if d > 0 else 1 - q)); y = int(cy - bh / 2)
    sh = CARD_SHADOW.get(('pan', key))
    if sh is None:
        m = np.zeros((H, W), np.float32); m[max(0, y + 18):min(H, y + 18 + bh), :] = 1
        sh = cv2.GaussianBlur(m, (0, 0), 30)[..., None] * 0.55; CARD_SHADOW[('pan', key)] = sh
    fr = fr * (1 - sh)
    y0, y1 = max(y, 0), min(y + bh, H); fr[y0:y1] = L[y0 - y:y1 - y, x0:x0 + W]
    return fr
def shot_img(key, p, z0, z1, fx, fy, dx, dy, cy=900):
    if key in FULL: return full_bg(key, p, z0, z1, fx, fy, dx, dy)
    if RAW[key].width / RAW[key].height > 1.3: return pan_frame(key, p, 1 if z1 >= z0 else -1)
    return card_frame(key, p, z0, z1, cy, dy * 300)

# ---------- таймлайн по голосу ----------
VO = os.path.join(ROOT, 'vo10')
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
json.dump({'v': 10, 'keys': KEYS, 'starts': starts, 'durs': durs, 'total': TOTAL, 'end_start': END_START}, open(os.path.join(ROOT, 'timeline_v10.json'), 'w'), ensure_ascii=False)
def BL(i): return starts[i + 1] - starts[i]

# ---------- фирменные слои ----------
CORNER = A(tpl.corner_layer().crop((0, 0, 460, 480)))
HB = tpl.CORNER['horse']; HXY = (HB[0] - 12, HB[1] - 12, HB[2] + 13, HB[3] + 13)
LOGO_IN = starts[1]
SWEEPS = [LOGO_IN + 0.5 + 6 * k for k in range(40)]
PY, PH_ = 90, 545
PLATE = A(brand.plate(990, PH_, 34))
HT1 = A(tlayer('СУПЕР АКЦИЯ', 900, 92, gold=True, maxw=900))
HT2 = A(tlayer('ДЛЯ ПЕРВЫХ 3 ФРАНЧАЙЗИ', 900, 56, gold=True, maxw=900))
HT3a = A(tlayer('ФРАНШИЗА', 800, 40, fill=WHITE, maxw=900))
HT3 = A(tlayer('DJIGIT', 900, 120, gold=True, maxw=900))
def mixrow():
    a = tlayer('ФОРМАТ', 800, 36, fill=WHITE); b = tlayer('KHINKALI HOUSE', 900, 66, gold=True, maxw=760)
    Wd = a.width + b.width - 20; Hd = b.height; L = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0))
    L.alpha_composite(b, (a.width - 20, 0)); L.alpha_composite(a, (0, int(66 * 0.78 - 36 * 0.78) + 4)); return A(L)
HT4 = mixrow()
HT5 = A(tlayer('В ТВОЁМ ГОРОДЕ', 800, 36, fill=WHITE, maxw=900))
TY = [PY + 10, PY + 110, PY + 180, PY + 222, PY + 388, PY + 472]
HB_PILL = None
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
 'what': [SH(0, 'queue', .95, 1.04, .45, .55)],
 'all': [SH(0, 'board', 1.0, 1.05)],
 'k1': [SH(0, 'kiosk2', 1.05, 1.0)],
 'k2': [SH(0, 'terrace', 1.0, 1.05)],
 's1': [SH(0, 'black', 1.0, 1.08)],
 's2': [SH(0, 'green', 1.08, 1.0)],
 's3': [SH(0, 'classic', 1.0, 1.08, dy=.08)],
 'sph': [SH(0, 'sphere', 1.12, 1.2, .5, .8), SH(.5, 'sphere2', 1.07, 1.0)],
 'don': [SH(0, 'don', 1.0, 1.08)],
 'kha': [SH(0, 'khach', .96, 1.04, .5, .66, 0, -.04)],
 'ice': [SH(0, 'ice', 1.05, 1.0)],
 'g1': [SH(0, 'film', .95, 1.04, .45, .5)],
 'g2': [SH(0, 'freezer', 1.0, 1.05)],
 'g3': [SH(0, 'girls', 1.0, 1.08)],
 'w0': [SH(0, 'chef', 1.05, 1.0)],
 'wow': [SH(0, 'phone', 1.0, 1.08)],
 'prt': [SH(0, 'hand', .95, 1.04, .5, .62)],
 'src1': [SH(0, 'courier', .95, 1.03, .45, .5), SH(.52, 'frozen', 1.03, .95, .5, .5)],
}
CAPS = {
 'what': ('ФОРМАТ KHINKALI HOUSE', 'СТРИТФУД СОВРЕМЕННОЙ', 'ГРУЗИНСКОЙ КУХНИ'),
 'all': ('САМЫЕ ХОДОВЫЕ БЛЮДА', 'ХИНКАЛИ • ЧЕБУРЕКИ', 'ДОНЕРЫ • ХАЧАПУРИ'),
 'ice': ('А ЕЩЁ МОРОЖЕНОЕ-ШОУ', 'В ГОРЯЧЕМ НАТУРАЛЬНОМ ШОКОЛАДЕ', 'И ОРЕХАХ'),
 'g1': ('ПОЧЕМУ ГОСТИ ЛЮБЯТ KHINKALI HOUSE', 'КРАСИВО • ВКУСНО', 'БЫСТРО • ДОСТУПНЫЕ ЦЕНЫ'),
 'g2': ('МОЖНО ПОЕСТЬ СРАЗУ', 'ИЛИ КУПИТЬ ДОМОЙ', 'ДОМАШНИЕ ПОЛУФАБРИКАТЫ'),
 'g3': ('ВАУ-ЭФФЕКТ', 'ГОСТИ САМИ СНИМАЮТ', 'И РЕКЛАМИРУЮТ ТВОЮ ТОЧКУ'),
 'w0': ('ДЛЯ ПАРТНЁРА', 'ПОЧЕМУ СТОИТ КУПИТЬ', 'ЭТУ ФРАНШИЗУ'),
 'k1': ('ФОРМАТ 1', 'КИОСК ОТ 10 М²', 'НА УЛИЦЕ ИЛИ В ТОРГОВОМ ЦЕНТРЕ'),
 'k2': ('ФОРМАТ 2', 'ФАСАДНОЕ ПОМЕЩЕНИЕ ОТ 80 М²', 'ЗАЛ И ЛЕТНЯЯ ПЛОЩАДКА'),
 's1': ('СОЛЁНЫЕ ХИНКАЛИ', 'ЧЁРНЫЕ НА ЧЕРНИЛАХ КАРАКАТИЦЫ', 'С МОРЕПРОДУКТАМИ'),
 's2': ('СОЛЁНЫЕ ХИНКАЛИ', 'ЗЕЛЁНЫЕ', 'ШПИНАТ И СЫР'),
 's3': ('СОЛЁНЫЕ ХИНКАЛИ', 'КЛАССИЧЕСКИЕ', 'С МЯСОМ И БУЛЬОНОМ'),

 'sph': ('БОЛЬШИЕ ЧЕБУРЕКИ-СФЕРЫ', 'ТЕЛЯТИНА • БАРАНИНА • СУЛУГУНИ', 'НЕОБЫЧНО НА ВИД И ОЧЕНЬ ВКУСНО'),
 'don': ('ДОНЕРЫ', 'СОЛЁНЫЕ', 'И СЛАДКИЕ'),
 'kha': ('А ЕЩЁ', 'ХАЧАПУРИ', 'И СВЕЖИЕ САЛАТЫ'),
 'gst': ('ЧТО ПОЛУЧАЕТ ГОСТЬ', 'НЕОБЫЧНО • ВКУСНО • НЕДОРОГО', 'ВЫДАЧА ЗА 3–5 МИНУТ'),
 'wow': ('ВАУ-ЭФФЕКТ', 'ГОСТИ САМИ СНИМАЮТ', 'И РЕКЛАМИРУЮТ ТВОЮ ТОЧКУ'),
 'prt': ('ЧТО ПОЛУЧАЕТ ПАРТНЁР', 'ЕДА НУЖНА ВСЕГДА', 'ГРУЗИНСКУЮ КУХНЮ ОСОБЕННО ЛЮБЯТ'),
 'src1': ('5 ИСТОЧНИКОВ ДОХОДА', 'ЗАЛ • ДОСТАВКА • ЛЕТНЯЯ ПЛОЩАДКА', 'ВКУСНЫЕ ДОМАШНИЕ ПРОДУКТЫ ДОМОЙ'),
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
TB_R1K = A(tlayer('от 20 000 €', 900, 74, gold=True, maxw=430)); TB_R1F = A(tlayer('от 45 000 €', 900, 74, gold=True, maxw=430))
TB_R2 = A(tlayer('ЧИСТАЯ ПРИБЫЛЬ В МЕСЯЦ', 800, 40, fill=WHITE))
TB_R2K = A(tlayer('от 3 000 €', 900, 90, gold=True, maxw=430)); TB_R2F = A(tlayer('от 10 000 €', 900, 90, gold=True, maxw=430))
TB_PAY = A(tlayer('ОКУПАЕМОСТЬ ДО 1 ГОДА', 900, 56, fill=WHITE, maxw=860))
def pill(w, h):
    p = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(p).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=(184, 146, 82, 255)); return A(p)
TB_PILL = pill(880, 120)
TB_PAYD = A(tlayer('ОКУПАЕМОСТЬ ДО 1 ГОДА', 900, 56, fill=(20, 15, 8, 255), maxw=820, shadow=0))
HB_PILL = pill(480, 96); HB_T = A(tlayer('МЕСТ ВСЕГО 3', 900, 54, fill=(20, 15, 8, 255), maxw=440, shadow=0))
SB_PILL = pill(820, 120)
# ---------- хук v11: два формата, взнос и прибыль с первого кадра (Вал 23.11 17:43) ----------
def old_price(t, sz=30):
    w0 = brand.width('вместо', 700, sz) + 16; w1 = brand.width(t, 700, sz); tw = int(w0 + w1) + 40
    L = Image.new('RGBA', (tw + 30, int(sz * 1.5) + 30), (0, 0, 0, 0)); dr = ImageDraw.Draw(L)
    x0 = 15 + 20 + (w0 + w1) / 2
    brand.draw_text(L, int(15 + 20 + (w0 - 16) / 2), 15, 'вместо', 700, sz, (225, 225, 225, 255))
    brand.draw_text(L, int(15 + 20 + w0 + w1 / 2), 15, t, 700, sz, (200, 200, 200, 255))
    yy = 15 + int(sz * 0.58); dr.line((15 + 20 + w0 - 4, yy, 15 + 20 + w0 + w1 + 4, yy), fill=(220, 50, 40, 255), width=4)
    return A(L)
HK_X = (45, 545); HK_Y = 650; HK_W, HK_H = 490, 206
HK_PL = A(brand.plate(HK_W, HK_H, 26))
HK_ROWS = []
for nm, old, prof in (('КИОСК', '7 000 €', 'от 3 000 €'), ('ФАСАДНОЕ', '9 000 €', 'от 10 000 €')):
    HK_ROWS.append((A(tlayer(nm, 900, 40, gold=True, maxw=440)), A(tlayer('ВЗНОС 5 000 €', 900, 40, fill=WHITE, maxw=440)),
                    old_price(old, 27), A(tlayer('ПРИБЫЛЬ ' + prof.upper() + '/МЕС', 900, 28, gold=True, maxw=450))))
HK_T = {'fee': 7.8, 'prof': (12.3, 14.0)}   # whisper по vo10/00_hook.wav: «взнос» 7.82, «киоск» 12.28, «фасадное» 14.02
def hook_chips(fr, lt, a):
    for j, x in enumerate(HK_X):
        comp(fr, HK_PL, x, HK_Y, a); cx = x + HK_W // 2; nm, fee, old, prof = HK_ROWS[j]
        tp = HK_T['prof'][j]; hf = 0 <= lt - HK_T['fee'] < 1.4; hp = 0 <= lt - tp < 1.4
        Lf = shimmer(fee, (lt - HK_T['fee']) / 1.2, 90) if hf else fee
        Lp = shimmer(prof, (lt - tp) / 1.2, 90) if hp else prof
        if hf: Lf = scaled(Lf, 1 + 0.08 * math.sin(min(1, (lt - HK_T['fee']) / 0.5) * math.pi))
        if hp: Lp = scaled(Lp, 1 + 0.05 * math.sin(min(1, (lt - tp) / 0.5) * math.pi))
        for Lr, yy in ((nm, 0), (Lf, 48), (old, 96), (Lp, 136)):
            comp(fr, Lr, cx - Lr.shape[1] // 2, HK_Y + yy - (Lr.shape[0] - fee.shape[0]) // 2 * (Lr is Lf or Lr is Lp), a)
def pop(fr, L, cx, cy, q, shim_t=None, big=1.6, out=1.0):
    if q <= 0: return
    sc = big - (big - 1) * eback(min(1, q), 2.2); Ln = scaled(L, sc)
    if shim_t is not None and 0 < shim_t < 1: Ln = shimmer(Ln, shim_t, 120)
    comp(fr, Ln, cx - Ln.shape[1] // 2, cy - Ln.shape[0] // 2, min(1, q * 3) * out)
def table_scene(fr, t):
    t0 = starts[B['inv']]; t1 = starts[B['prof']]; lt = t - t0; Lall = starts[B['prof'] + 1] - t0
    out = 1 - ease((lt - (Lall - 0.22)) / 0.22) if lt > Lall - 0.22 else 1
    a = ease(lt / 0.3) * out; Y0 = 470
    comp(fr, TB_PL, 45, Y0, a)
    for L, cx, y in ((TB_K, 300, Y0 + 40), (TB_F, 780, Y0 + 40)): comp(fr, L, cx - L.shape[1] // 2, y + int(20 * (1 - ease(lt / .35))), a)
    for L, cx, y in ((TB_KS, 300, Y0 + 132), (TB_FS, 780, Y0 + 132)): comp(fr, L, cx - L.shape[1] // 2, y, ease((lt - .2) / .35) * out)
    for ya, yb in ((Y0 + 40, Y0 + 200), (Y0 + 315, Y0 + 480), (Y0 + 625, Y0 + 805)):
        vl = int((yb - ya) * ease((lt - .15) / .5)); ln = np.zeros((max(vl, 1), 3, 4), np.float32); ln[..., :3] = (200, 165, 100); ln[..., 3] = 200
        if vl > 2: comp(fr, ln, 539, ya, out)
    for y in (Y0 + 215, Y0 + 520):
        hl = int(900 * ease((lt - .25) / .5)); h2 = np.zeros((2, max(hl, 1), 4), np.float32); h2[..., :3] = (200, 165, 100); h2[..., 3] = 160
        if hl > 2: comp(fr, h2, 540 - hl // 2, y, out)
    # строка 1: вложения (с голосом «вложения под ключ»)
    q1 = (lt - 0.35) / 0.35
    if q1 > 0: comp(fr, TB_R1, 540 - TB_R1.shape[1] // 2, Y0 + 238, ease(q1) * out)
    dk = durs[B['inv']]
    for L, cx, tt in ((TB_R1K, 300, .38 * dk), (TB_R1F, 780, .72 * dk)):
        q = (lt - tt) / 0.45
        if q > 0: pop(fr, L, cx, Y0 + 395, q, (lt - tt - .45) / 1.0, out=out)
    # строка 2: прибыль
    lt2 = t - t1; dp = durs[B['prof']]
    if lt2 > 0:
        comp(fr, TB_R2, 540 - TB_R2.shape[1] // 2, Y0 + 545, ease(lt2 / .35) * out)
        for L, cx, tt in ((TB_R2K, 300, .22 * dp), (TB_R2F, 780, .5 * dp)):
            q = (lt2 - tt) / 0.45
            if q > 0:
                pop(fr, L, cx, Y0 + 715, q, (lt2 - tt - .45) / 1.0, 1.7, out=out)
                if lt2 - tt < 0.15: fr[:] = fr + (255 - fr) * (0.3 * (1 - (lt2 - tt) / 0.15))
        qp = (lt2 - .76 * dp) / 0.4
        if qp > 0:
            s = 0.7 + 0.3 * eback(min(1, qp)); P = scaled(TB_PILL, s); D = scaled(TB_PAYD, s)
            comp(fr, P, 540 - P.shape[1] // 2, Y0 + 875 + (120 - P.shape[0]) // 2, ease(qp) * out)
            if 0.4 < lt2 - .76 * dp < 1.4: D = shimmer(D, (lt2 - .76 * dp - .4), 100)
            comp(fr, D, 540 - D.shape[1] // 2, Y0 + 875 + (120 - D.shape[0]) // 2 - 4, ease(qp) * out)
    return fr

# ---------- сцена «30%» ----------
P30_PL = A(brand.plate(990, 800, 34))
P30_T = A(tlayer('5-Й ИСТОЧНИК ДОХОДА', 900, 58, gold=True, maxw=900)); P30_S = A(tlayer('ТЫ ОФИЦИАЛЬНЫЙ ПРЕДСТАВИТЕЛЬ DJIGIT', 800, 42, fill=WHITE, maxw=900))
P30_N = A(tlayer('30%', 900, 260, gold=True, maxw=900))
P30_A = A(tlayer('ОТ ПАУШАЛЬНОГО ВЗНОСА', 800, 54, fill=WHITE, maxw=900)); P30_B = A(tlayer('КАЖДОГО ПАРТНЁРА, КОТОРОГО ПРИВЁЛ', 800, 46, fill=WHITE, maxw=900))
def p30_scene(fr, lt, L):
    out = 1 - ease((lt - (L - 0.22)) / 0.22) if lt > L - 0.22 else 1; Y0 = 480
    comp(fr, P30_PL, 45, Y0, ease(lt / .3) * out)
    comp(fr, P30_T, 540 - P30_T.shape[1] // 2, Y0 + 40 + int(20 * (1 - ease(lt / .35))), ease(lt / .35) * out)
    comp(fr, P30_S, 540 - P30_S.shape[1] // 2, Y0 + 115, ease((lt - .3) / .35) * out)
    q = (lt - .55) / .45
    if q > 0:
        pop(fr, P30_N, 540, Y0 + 370, q, (lt - 1.0) / 1.0, 1.8, out=out)
        if lt - .55 < .15: fr[:] = fr + (255 - fr) * (0.35 * (1 - (lt - .55) / .15))
    for j, Lr in enumerate((P30_A, P30_B)):
        qq = (lt - 1.0 - .15 * j) / .35
        if qq > 0: comp(fr, Lr, 540 - Lr.shape[1] // 2, Y0 + 560 + 80 * j + int(20 * (1 - ease(qq))), ease(qq) * out)
    return fr

# ---------- сцена «защита + Германия» ----------
LQ_PA = A(brand.plate(990, 380, 34)); LQ_PB = A(brand.plate(990, 420, 34))
LQ = [A(tlayer('ЗАЩИТА ВЛОЖЕНИЙ', 900, 54, gold=True)), A(tlayer('ГОТОВАЯ ТОЧКА', 900, 92, fill=WHITE, maxw=900)), A(tlayer('ЛИКВИДНЫЙ И СТАБИЛЬНЫЙ АКТИВ', 800, 44, fill=(225, 225, 225, 255), maxw=900))]
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


# ---------- почему стоит купить: 6 причин, каждая вспыхивает с голосом ----------
WHY = [('ПИЩЕВАЯ НИША ВОСТРЕБОВАНА ВСЕГДА', 'хлеба и зрелищ: мы даём и то, и другое'),
       ('ГРУЗИНСКУЮ КУХНЮ ЛЮБЯТ ВСЕ', 'цветные хинкали и другие вау-блюда'),
       ('ДОСТУПНЫЙ СТРИТФУД ДЛЯ ВСЕХ', 'гостей всегда много'),
       ('НЕБОЛЬШИЕ ВЛОЖЕНИЯ', 'окупаемость до 1 года'),
       ('ЛИКВИДНЫЙ АКТИВ', 'который всегда в цене'),
       ('5 ИСТОЧНИКОВ ДОХОДА', 'зал, доставка, площадка, продукты, партнёры')]
def ltext(t, w8, sz, fill=None, gold=False, maxw=800):
    while brand.width(t, w8, sz) > maxw: sz -= 1
    tw = int(brand.width(t, w8, sz)) + 10; L = Image.new('RGBA', (tw + 20, int(sz * 1.45) + 20), (0, 0, 0, 0))
    brand.draw_text(L, 10, 6, t, w8, sz, fill, gold=gold, anchor='l'); return A(L)
WM = [(ltext(a, 900, 50, fill=WHITE, maxw=820), ltext(a, 900, 50, gold=True, maxw=820), ltext(b, 700, 40, fill=(225, 225, 225, 255), maxw=820)) for a, b in WHY]
WT = A(tlayer('ПОЧЕМУ СТОИТ КУПИТЬ', 900, 62, gold=True, maxw=900))
_WPC = {}
def WPL_h(h):
    h = int(round(h / 8.0) * 8)
    if h not in _WPC: _WPC[h] = A(brand.plate(990, h, 34))
    return _WPC[h]
def checkmark(d=64):
    S = d + 20; im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.ellipse((10, 10, 10 + d, 10 + d), fill=(214, 176, 106, 255))
    dr.line([(10 + d * .27, 10 + d * .52), (10 + d * .44, 10 + d * .69), (10 + d * .74, 10 + d * .33)], fill=(20, 15, 8, 255), width=8, joint='curve')
    return A(im)
CHK = checkmark()
def why_scene(fr, t):
    t0 = starts[B['w1']]; lt = t - t0; Lall = starts[B['w6'] + 1] - t0
    out = 1 - ease((lt - (Lall - 0.22)) / 0.22) if lt > Lall - 0.22 else 1; Y0 = 455
    nrev = sum(ease(max(0, min(1, (lt - (starts[B[f'w{j + 1}']] - t0)) / 0.35))) for j in range(6))
    comp(fr, WPL_h(150 + 185 * nrev + 25), 45, Y0, ease(lt / .3) * out)
    comp(fr, WT, 540 - WT.shape[1] // 2, Y0 + 28 + int(20 * (1 - ease(lt / .35))), ease(lt / .35) * out)
    for j in range(6):
        tj = starts[B[f'w{j + 1}']] - t0; q = (lt - tj) / 0.35
        if q <= 0: continue
        y = Y0 + 150 + j * 185; a = ease(q) * out; dx = int(40 * (1 - ease(q)))
        cs = scaled(CHK, 0.6 + 0.4 * eback(min(1, q), 2.4)); comp(fr, cs, 120 - cs.shape[1] // 2, y + 36 - cs.shape[0] // 2, a)
        nxt = starts[B[f'w{j + 2}']] - t0 if j < 5 else Lall
        active = tj <= lt < nxt
        Wm, Wg, Ws = WM[j]; Lm = Wg if active else Wm
        if active and 0.3 < lt - tj < 1.3: Lm = shimmer(Lm, lt - tj - 0.3, 90)
        comp(fr, Lm, 165 + dx, y - 4, a); comp(fr, Ws, 165 + dx, y + 70, a)
    return fr
def de_scene(fr, lt, L):
    out = 1 - ease((lt - (L - 0.22)) / 0.22) if lt > L - 0.22 else 1; Y0 = 620
    comp(fr, LQ_PB, 45, Y0, ease(lt / .3) * out)
    for j, (Lr, y) in enumerate(zip(DE, (Y0 + 45, Y0 + 135, Y0 + 265, Y0 + 320))):
        q = (lt - .1 - .25 * j) / .35
        if q > 0:
            L2 = shimmer(Lr, (lt - .9) / 1.0) if (j == 1 and 0.9 < lt < 1.9) else Lr
            comp(fr, L2, 540 - Lr.shape[1] // 2, y + int(25 * (1 - ease(q))), ease(q) * out)
    return fr

# ---------- оффер (из v5) ----------
OF_T = A(tlayer('ТОЛЬКО ДЛЯ ПЕРВЫХ 3 ФРАНЧАЙЗИ', 900, 60, gold=True, maxw=900))
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
SL_B = A(tlayer('ЗАЙМИ СВОЁ МЕСТО', 900, 62, fill=(20, 15, 8, 255), maxw=820, shadow=0))
SL_C = [A(tlayer('АКЦИЯ ДЕЙСТВУЕТ,', 800, 60, fill=WHITE, maxw=950)), A(tlayer('ПОКА СВОБОДНЫ 3 МЕСТА', 800, 60, fill=WHITE, maxw=950))]
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
            cx = 540 + (k - 1) * 300; comp(fr, Ls, cx - Ls.shape[1] // 2, 955 + (TOKB[k].shape[0] - Ls.shape[0]) // 2, ease(qk))
    F = fire(starts[B['slot']] + lt, 820, 260); comp(fr, F, 540 - F.shape[1] // 2, 480, ease(lt / 0.3))
    comp(fr, SL_A, 540 - SL_A.shape[1] // 2, 725 + int(25 * (1 - ease(lt / 0.3))), ease(lt / 0.3))
    for j, Lc in enumerate(SL_C):
        q = ease((lt - 0.5 - 0.2 * j) / 0.3); comp(fr, Lc, 540 - Lc.shape[1] // 2, 1235 + 80 * j + int(25 * (1 - q)), q)
    q = (lt - 1.2) / 0.35
    if q > 0:
        s = (0.7 + 0.3 * eback(min(1, q))) * (1 + 0.025 * math.sin(max(0, lt - 1.6) * 2 * math.pi / 1.2)); P = scaled(SB_PILL, s); D = scaled(SL_B, s)
        comp(fr, P, 540 - P.shape[1] // 2, 1545 - P.shape[0] // 2, ease(q)); comp(fr, D, 540 - D.shape[1] // 2, 1541 - D.shape[0] // 2, ease(q))
    return fr

# ---------- заставка (утверждённая) ----------
_E = dict(tpl.END)
for k in ('q1', 'q2', 'btn', 'site'):
    a, b, c, d = _E[k]; o = 150 if k == 'site' else 34; _E[k] = (a, b + o, c, d + o)
tpl.END.update(_E)
EL = tpl.end_layers(q1t='Хочешь такой стритфуд', q2t='в своём городе?', btnt='ЗАЙМИ СВОЁ МЕСТО'); Lend = {k: (A(im), xy) for k, (im, xy) in EL.items()}
_ben = tlayer('КРАСИВО • БЫСТРО • ВКУСНО • ДОСТУПНО ПО ЦЕНЕ', 800, 34, gold=True, maxw=960); Lend['ben'] = (A(_ben), (540 - _ben.width // 2, 1018))
_mag = tlayer('БЕСПЛАТНО ПОСЧИТАЕМ ЭКОНОМИКУ', 900, 46, gold=True, maxw=980); Lend['mag'] = (A(_mag), (540 - _mag.width // 2, 1392))
_mag2 = tlayer('ПОД ТВОЙ ГОРОД', 900, 46, gold=True, maxw=980); Lend['mag2'] = (A(_mag2), (540 - _mag2.width // 2, 1452))
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((290, 380, 790, 880), fill=(214, 170, 100, 90)); GLOW = A(glow.filter(ImageFilter.GaussianBlur(90)))
order = [('dj', 0.25), ('sub', 0.4), ('ben', 0.5), ('q1', 0.62), ('q2', 0.7), ('btn', 0.85), ('mag', 1.0), ('mag2', 1.05), ('site', 1.15)]
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



# ---------- огонь (срочность): процедурное пламя, поднимается вверх ----------
_rng = np.random.default_rng(7)
_NZ = [cv2.GaussianBlur(_rng.random((1400, 900)).astype(np.float32), (0, 0), sg) for sg in (22, 9)]
_NZ = [(n - n.mean()) / n.std() * 0.11 + 0.5 for n in _NZ]
_FC = {}
def fire(t, w, h):
    key = (w, h)
    if key not in _FC:
        yy = np.linspace(0, 1, h)[:, None]; xx = np.linspace(-1, 1, w)[None, :]
        bot = np.clip((1 - yy) / 0.10, 0, 1)
        _FC[key] = (np.broadcast_to(yy, (h, w)).copy(), np.clip(1 - np.abs(xx) ** 3, 0, 1) * bot)
    yy, hm = _FC[key]
    hh = h // 2 + 1
    o1 = 700 - int(t * 170) % 700; o2 = 700 - int(t * 260) % 700
    n1 = cv2.resize(_NZ[0][o1:o1 + hh, 60:60 + w], (w, h)); n2 = cv2.resize(_NZ[1][o2:o2 + hh, 30:30 + w], (w, h))
    z = (0.65 * n1 + 0.35 * n2 - 0.5) / 0.11
    I = np.clip(yy * 1.9 - 0.75 + 0.42 * z, 0, 1) * hm
    c1 = np.array([255, 250, 215]); c2 = np.array([255, 155, 25]); c3 = np.array([185, 30, 5])
    col = np.where(I[..., None] > .5, c2 + (c1 - c2) * ((I[..., None] - .5) / .5), c3 + (c2 - c3) * (I[..., None] / .5))
    a = np.clip(I * 1.7, 0, 1)
    out = np.zeros((h, w, 4), np.float32); out[..., :3] = col; out[..., 3] = a * 255
    return out


# ---------- хук v13: хинкали на общем фоне (без карточки), огонь из хвостика (Вал 23.11 19:37) ----------
HK_KNOT = 1080; HK_PILL_Y = 925   # верх хвостика хинкали на экране; центр плашки «МЕСТ ВСЕГО 3»
_HKB = {}
def hook_bg(lt, L):
    if not _HKB:
        im = cv2.cvtColor(cv2.imread(os.path.join(ROOT, 'ph4/IMG_5796.jpeg')), cv2.COLOR_BGR2RGB).astype(np.float32)
        crop = im[300:1340, 30:1050]          # без верхней надписи и без золотой рамки по краям
        k = H / crop.shape[0]; bg = cv2.resize(crop, (int(crop.shape[1] * k), H)); x = (bg.shape[1] - W) // 2
        bg = cv2.GaussianBlur(bg[:, x:x + W], (0, 0), 38) * 0.42
        g = np.linspace(0.75, 1.0, H)[:, None, None]; _HKB['bg'] = bg * g
        h, w = crop.shape[:2]; m = np.ones((h, w), np.float32); f = 130
        ramp = lambda n: np.clip(np.arange(n) / f, 0, 1)
        m *= np.minimum(ramp(w), ramp(w)[::-1])[None, :]; m *= np.minimum(ramp(h), ramp(h)[::-1])[:, None]
        m = cv2.GaussianBlur(m, (0, 0), 25) ** 1.4
        _HKB['fg'] = np.dstack([crop, m * 255])
        # силуэт хинкали поверх огня (огонь горит изнутри: виден в отверстии хвостика и над ним)
        hsv = cv2.cvtColor(crop.astype(np.uint8), cv2.COLOR_RGB2HSV); hh_, ss_, vv_ = cv2.split(hsv)
        red = (((hh_ < 12) | (hh_ > 165)) & (ss_ > 110) & (vv_ > 70)).astype(np.uint8)
        red = cv2.morphologyEx(red, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
        n_, lab, st_, _ = cv2.connectedComponentsWithStats(red); kk = 1 + np.argmax(st_[1:, 4]); km = (lab == kk).astype(np.uint8)
        ff = km.copy(); fm = np.zeros((km.shape[0] + 2, km.shape[1] + 2), np.uint8); cv2.floodFill(ff, fm, (0, 0), 1); km = km | (1 - ff)
        cv2.ellipse(km, (545, 118), (92, 30), 0, 0, 360, 0, -1)      # отверстие хвостика: там виден огонь
        km = cv2.GaussianBlur(km.astype(np.float32), (0, 0), 2.5); km[620:] = 0   # нижняя часть не нужна (огня там нет)
        _HKB['ov'] = np.dstack([crop, km * 255])
    fr = _HKB['bg'].copy(); S = 0.80 + 0.04 * eio(min(lt / L, 1))
    fg = _HKB['fg']; L2 = cv2.resize(fg, (int(fg.shape[1] * S), int(fg.shape[0] * S)), interpolation=cv2.INTER_AREA)
    comp(fr, L2, 540 - 510 * S, HK_KNOT - 70 * S)
    return fr
def hook_over(fr, lt, L):
    S = 0.80 + 0.04 * eio(min(lt / L, 1)); ov = _HKB['ov']
    L2 = cv2.resize(ov, (int(ov.shape[1] * S), int(ov.shape[0] * S)), interpolation=cv2.INTER_AREA)
    comp(fr, L2, 540 - 510 * S, HK_KNOT - 70 * S)
    return 540 + 35 * S, HK_KNOT + 62 * S      # центр отверстия хвостика на экране (x, низ огня)
_FN = {}
def flame2(t, Wf=560, Hf=320):
    """Один язык пламени из хвостика: узкий у основания, шире к середине, рваный верх, движется вверх."""
    if not _FN:
        rng = np.random.default_rng(11)
        a = cv2.GaussianBlur(rng.random((Hf * 6, Wf)).astype(np.float32), (0, 0), sigmaX=9, sigmaY=22)
        b = cv2.GaussianBlur(rng.random((Hf * 6, Wf)).astype(np.float32), (0, 0), sigmaX=5, sigmaY=12)
        _FN['a'] = (a - a.mean()) / a.std(); _FN['b'] = (b - b.mean()) / b.std()
        _FN['yy'] = np.linspace(1, 0, Hf)[:, None].astype(np.float32); _FN['xx'] = np.linspace(-1, 1, Wf)[None, :].astype(np.float32)
    a, b, yy, xx = _FN['a'], _FN['b'], _FN['yy'], _FN['xx']; N = Hf * 5
    o1 = int(t * 170) % N; o2 = int(t * 330) % N
    n1 = a[N - o1:N - o1 + Hf] if o1 else a[N:N + Hf]; n2 = b[N - o2:N - o2 + Hf] if o2 else b[N:N + Hf]
    sway = 0.10 * yy * np.sin(t * 5.3 + yy * 6.0) + 0.16 * yy * n1[:, Wf // 2:Wf // 2 + 1]
    wp = np.where(yy < 0.68, 0.22 + 0.78 * np.sin(np.clip(yy / 0.68, 0, 1) * np.pi / 2) ** 1.6, np.clip(1 - (yy - 0.68) / 0.32, 0, 1) ** 0.8)
    shape = np.clip(1 - (np.abs(xx - sway) / (wp + 1e-3)) ** 2, 0, 1)
    tong = np.clip(0.5 + 0.5 * np.sin(xx * 9.0 + n1 * 1.6 + t * 2.0), 0, 1)
    I = shape * (0.95 - 0.55 * yy) * (0.65 + 0.35 * tong) + 0.18 * n2 * shape - np.clip(yy - 0.3, 0, 1) * (0.7 + 0.5 * n1) * (1.1 - tong * 0.4)
    I = np.clip(I, 0, 1) * np.clip(yy / 0.06, 0, 1) ** 0.5
    stops = np.array([0, 0.2, 0.45, 0.7, 0.9, 1.0]); cols = np.array([[110, 8, 0], [190, 30, 0], [250, 90, 8], [255, 160, 30], [255, 215, 110], [255, 240, 190]], np.float32)
    rgb = np.stack([np.interp(I, stops, cols[:, c]) for c in range(3)], -1)
    al = np.clip((I - 0.06) * 2.4, 0, 1)
    glow = cv2.GaussianBlur(I, (0, 0), 18) * 0.4
    A_ = np.maximum(al, glow * 0.6); rgb = rgb * (al / np.maximum(A_, 1e-3))[..., None] + np.array([255, 120, 20], np.float32) * (1 - al / np.maximum(A_, 1e-3))[..., None]
    out = np.zeros((Hf, Wf, 4), np.float32); out[..., :3] = rgb; out[..., 3] = A_ * 255
    return out

# ---------- сладкая линейка: сетка 2х2, подсвечивается то, что называет голос ----------
GRID_K = ['straw', 'cherry', 'blue', 'rasp']; GRID_N = ['КЛУБНИКА', 'ВИШНЯ', 'ЧЕРНИКА', 'МАЛИНА']
GRID_T = [1.18, 1.94, 2.64, 3.46]   # по словам в голосе (whisper)
CW_, CH_, GG = 488, 610, 14; GX0 = (W - 2 * CW_ - GG) // 2; GY0 = 470
def cellimg(k):
    im = RAW[k]; sc = max(CW_ / im.width, CH_ / im.height); im2 = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
    x = (im2.width - CW_) // 2; y = (im2.height - CH_) // 2; return A(im2.crop((x, y, x + CW_, y + CH_)))
GCELL = {k: cellimg(k) for k in GRID_K}
GLAB = [A(tlayer(n, 900, 40, gold=True)) for n in GRID_N]
GTITLE = A(tlayer('СЛАДКИЕ ХИНКАЛИ', 900, 64, gold=True))
def grid_frame(t, all_lit=False):
    t0 = starts[B['d1']]; lt = t - t0
    fr = BLUR['straw'].copy()
    for j, k in enumerate(GRID_K):
        cx = GX0 + (j % 2) * (CW_ + GG); cy = GY0 + (j // 2) * (CH_ + GG)
        qa = ease((lt - 0.08 * j) / 0.35)
        lit = all_lit or lt >= GRID_T[j] - 0.05
        ql = 1.0 if all_lit else ease((lt - GRID_T[j] + 0.05) / 0.25)
        bright = 0.6 + 0.4 * (ql if lit else 0)
        s = 1 + 0.05 * (1 - ease((lt - GRID_T[j] + 0.05) / 0.4)) if (lit and not all_lit and lt - GRID_T[j] < 0.4) else 1
        C = GCELL[k] * bright
        if s != 1: C = scaled(C, s)
        Cl = np.dstack([C, np.full(C.shape[:2] + (1,), 255, np.float32)])
        comp(fr, Cl, cx + (CW_ - C.shape[1]) // 2, cy + (CH_ - C.shape[0]) // 2, qa)
        if lit and ql > 0:
            b = np.zeros((C.shape[0] + 10, C.shape[1] + 10, 4), np.float32); b[..., :3] = (214, 176, 106); b[..., 3] = 255; b[5:-5, 5:-5, 3] = 0
            comp(fr, b, cx + (CW_ - C.shape[1]) // 2 - 5, cy + (CH_ - C.shape[0]) // 2 - 5, ql * qa)
            Lb = GLAB[j]; band = np.zeros((70, C.shape[1], 4), np.float32); band[..., 3] = 170
            comp(fr, band, cx + (CW_ - C.shape[1]) // 2, cy + (CH_ + C.shape[0]) // 2 - 70, ql * qa)
            comp(fr, Lb, cx + CW_ // 2 - Lb.shape[1] // 2, cy + (CH_ + C.shape[0]) // 2 - 70 + (70 - Lb.shape[0]) // 2 + 2, ql * qa)
    return fr
def sweet_scene(t, key, lt, L):
    if key == 'd1':
        fr = grid_frame(t)
        if lt < 0.38: fr = trans(fr, lt, 0, 1.0)
        corner(fr, t); comp(fr, GTITLE, 540 - GTITLE.shape[1] // 2, 1715 + int(20 * (1 - ease(lt / .35))), ease(lt / .35))
        return fr
    # d2: наезд в клубничный хинкали
    card = card_frame('straw', lt / L, 1.0, 1.08)
    if lt < 0.5:
        g = grid_frame(t, True); q = ease(lt / 0.5); z = 1 + 1.25 * q
        ccx = GX0 + CW_ / 2; ccy = GY0 + CH_ / 2; cw, ch = W / z, H / z
        x0 = min(max(ccx - cw / 2, 0), W - cw); y0 = min(max(ccy - ch / 2, 0), H - ch)
        gz = cv2.resize(g[int(y0):int(y0 + ch), int(x0):int(x0 + cw)], (W, H), interpolation=cv2.INTER_LINEAR)
        fr = gz * (1 - q) + card * q
    else: fr = card
    fr = brand_dark(fr, t); corner(fr, t)
    draw_caps(fr, mkcap(('СЛАДКИЕ ХИНКАЛИ', 'НАСТОЯЩИЕ ЯГОДЫ ВНУТРИ', 'НАТУРАЛЬНЫЕ КРАСИТЕЛИ')), lt, L)
    return fr

# ---------- кадр ----------
TEXTBG = {'inv': 'b_n1', 'prof': 'b_n1', 'src2': 'frozen', 'de': 'b_p5', 'off': 'b_p10', 'slot': 'b_p6', **{f'w{j}': 'chef' for j in range(1, 7)}}
def drift(bgimg, lt, s=0.04):
    z = 1 + s * min(lt / 6, 1); cw, ch = int(W / z), int(H / z); x0 = (W - cw) // 2; y0 = (H - ch) // 2
    return cv2.resize(bgimg[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR)
def frame(fi):
    t = fi / FPS
    i = max(j for j, s in enumerate(starts) if t >= s - 1e-9); key = KEYS[i]; lt = t - starts[i]
    if key == 'end': return None
    L = BL(i)
    if key == 'hook':
        fr = hook_bg(lt, L)
        a = 1.0 if lt < L - 0.25 else 1 - ease((lt - (L - 0.25)) / 0.25)
        comp(fr, PLATE, 45, PY, a)
        spp = min(max((lt - 0.6) / 1.1, 0), 1)
        for Lr, yy in ((HT1, TY[0]), (HT2, TY[1]), (HT3, TY[3]), (HT4, TY[4])):
            comp(fr, shimmer(Lr, spp) if 0 < spp < 1 else Lr, 540 - Lr.shape[1] // 2, yy, a)
        comp(fr, HT3a, 540 - HT3a.shape[1] // 2, TY[2], a); comp(fr, HT5, 540 - HT5.shape[1] // 2, TY[5], a)
        bp = 1 + 0.03 * math.sin(lt * 2 * math.pi / 1.1); BY = HK_PILL_Y
        F = flame2(t); S_ = 0.80 + 0.04 * eio(min(lt / L, 1)); fx_, fy_ = 540 + 35 * S_, HK_KNOT + 62 * S_
        comp(fr, F, fx_ - F.shape[1] // 2, fy_ - F.shape[0], a); hook_over(fr, lt, L)
        hook_chips(fr, lt, a)
        Pb = scaled(HB_PILL, bp); Tb = scaled(HB_T, bp)
        comp(fr, Pb, 540 - Pb.shape[1] // 2, BY - Pb.shape[0] // 2, a)
        comp(fr, Tb, 540 - Tb.shape[1] // 2, BY - Tb.shape[0] // 2 - 4, a)
        return fr
    if key in ('d1', 'd2'): return sweet_scene(t, key, lt, L)
    if key in SHOTS:
        si, st, sl, (f, k2, z0, z1, fx, fy, dx, dy, cy) = shot_of(key, lt, L)
        fr = shot_img(k2, st / sl, z0, z1, fx, fy, dx, dy, cy)
        if st < 0.38: fr = trans(fr, st, (i * 3 + si) % 4, 1.0 if si == 0 else 0.7)
        fr = brand_dark(fr, t); corner(fr, t)
        if key in CAPS: draw_caps(fr, mkcap(CAPS[key]), lt, L)
        return fr
    # текстовые сцены на размытом фоне
    first = key in ('inv', 'liq') or key not in ('prof', 'de')
    t_sc = starts[B['inv']] if key in ('inv', 'prof') else (starts[B['w1']] if key.startswith('w') else starts[i])
    fr = drift(BLUR[TEXTBG[key]], t - t_sc)
    if t - t_sc < 0.38: fr = punch(fr, (t - t_sc) / 0.35, 0.06) if t - t_sc < 0.35 else fr; fr = flash(fr, (t - t_sc) / 0.38, 1.0)
    fr = brand_dark(fr, t); corner(fr, t)
    if key in ('inv', 'prof'): return table_scene(fr, t)
    if key.startswith('w'): return why_scene(fr, t)
    if key == 'de': return de_scene(fr, lt, L)
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
