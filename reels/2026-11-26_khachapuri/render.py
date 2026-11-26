# Рилс-рецепт «Хачапури по-мегрельски» (видео Вала 26.11, 624x848, 26.4 с, голос оригинала байт в байт).
# Монтаж: 0-3.0 с тянущийся сыр (исходник 23.4-26.4) под крючком; 3.0-23.4 исходник 1:1 (синхрон с голосом);
# 23.4-конец финальная карточка поверх размытого разреза (исходник 0-3). Угловой логотип 0.8 от стандарта (Вал 26.11).
import sys, os, subprocess, json, numpy as np, cv2
sys.path.insert(0, '/home/claude/work/prev'); sys.path.insert(0, '/home/claude/work/tpl')
import brand, tpl
from PIL import Image, ImageDraw, ImageFilter
D = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('SRC', D + '/src/src.mov'); OUT = os.environ.get('OUT', '/home/claude/work/kh/khachapuri_v1.mp4')
W, H, FPS = 1080, 1920, 30
ZX0, ZY0, ZX1, ZY1 = 65, 270, 960, 1500
L1, L2, L3 = 'ДИЕТА ПОДОЖДЁТ', 'СЫР ВНУТРИ И СВЕРХУ', 'хачапури по-мегрельски'
HOOK_END = 3.0; LOGO_IN = 3.0; END_T = 23.4
STEPS = [(3.0, 8.0, 'ШАГ 1', 'ЗАМЕШИВАЕМ ТЕСТО'), (8.0, 10.8, 'ШАГ 2', 'ТЕСТО ОТДЫХАЕТ'),
         (10.8, 15.1, 'ШАГ 3', 'СЫР ВНУТРЬ, ЗАЩИПЫВАЕМ'), (15.1, 18.3, 'ШАГ 4', 'СМАЗЫВАЕМ, СЫР СВЕРХУ'),
         (18.3, 23.4, 'ШАГ 5', '15 МИНУТ ПРИ 200°')]
NV = 793
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
def shimmer(lay, p, width=90):
    h, w = lay.shape[:2]; o = lay.copy(); xx = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.6
    c = -width + p * (w + h * 0.6 + 2 * width); b = np.clip(1 - np.abs(xx - c) / width, 0, 1)[..., None]
    o[..., :3] = o[..., :3] + (255 - o[..., :3]) * b * 0.55; return o
def tlayer(t, w8, sz, fill=None, gold=False, maxw=800, shadow=235):
    while brand.width(t, w8, sz) > maxw: sz -= 2
    tw = int(brand.width(t, w8, sz)) + 40; L = Image.new('RGBA', (tw, int(sz * 1.5)), (0, 0, 0, 0))
    brand.draw_text(L, tw // 2, 0, t, w8, sz, fill, gold=gold)
    sh = Image.new('RGBA', L.size, (0, 0, 0, 0)); sh.putalpha(L.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda v: min(255, v * shadow // 255)))
    out = Image.new('RGBA', (tw + 30, L.height + 30), (0, 0, 0, 0)); out.alpha_composite(sh, (15, 19)); out.alpha_composite(L, (15, 15))
    return out
# угловой логотип: стандарт tpl, масштаб 0.8, левый-верхний угол там же, где в KH v16d (Вал 26.11: «немножко уменьшить»)
tpl.CORNER['sub'] = (52, 400, 381, 410)
C0 = A(tpl.corner_layer().crop((0, 0, 460, 480))); _m = C0[..., 3] > 0.5
_cy, _cx = np.where(_m.any(1))[0], np.where(_m.any(0))[0]; REF_TL = (5 + _cx[0], 156 + _cy[0])
CS = 0.8; CORNER = scaled(C0, CS); _m = CORNER[..., 3] > 0.5
_cy, _cx = np.where(_m.any(1))[0], np.where(_m.any(0))[0]
LDX, LDY = int(ZX0 - _cx[0]), int(ZY0 - _cy[0])   # рамка логотипа с тенью ровно от угла зоны 65,270
CORNER_BOX = [int(LDX + _cx[0]), int(LDY + _cy[0]), int(LDX + _cx[-1]), int(LDY + _cy[-1])]
HB = [int(v * CS) for v in tpl.CORNER['horse']]; HXY = (HB[0] - 10, HB[1] - 10, HB[2] + 10, HB[3] + 10)
SWEEPS = [LOGO_IN + 0.5 + 6 * k for k in range(5)]
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
CDARK = (1 - 0.6 * np.clip(1 - np.sqrt(((XX - LDX) / 520) ** 2 + ((YY - LDY) / 520) ** 2), 0, 1) ** 0.8)[..., None]
# крючок: плашка на всю ширину зоны
PX, PY, PW, PH = ZX0, 300, ZX1 - ZX0, 440
PLATE = A(brand.plate(PW, PH, 34))
T1 = A(tlayer(L1, 900, 104, gold=True, maxw=800)); T2 = A(tlayer(L2, 900, 104, gold=True, maxw=800))
T3 = A(tlayer(L3.upper(), 700, 42, fill=(255, 255, 255, 255), maxw=780))
TY = [PY + 34, PY + 168, PY + 318]
grad = np.zeros((H, W, 1), np.float32); grad[:, :, 0] = (np.clip((np.arange(H) - 950) / 600, 0, 1) ** 1.2 * 0.7)[:, None]
CAPY_A, CAPY_B = 1250, 1325
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
FLASH_T = [s for s, _, _, _ in STEPS]; PUNCH = [0] + FLASH_T
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
    q = ease((t - LOGO_IN) / 0.35); CL = CORNER
    for st in SWEEPS:
        if st <= t < st + 1.0:
            CL = CORNER.copy(); x0_, y0_, x1_, y1_ = HXY; CL[y0_:y1_, x0_:x1_] = shimmer(CORNER[y0_:y1_, x0_:x1_], (t - st) / 1.0, 40); break
    comp(fr, CL, LDX, LDY, q, log=False)
def frame(f, t):
    pp = max(k for k in PUNCH if k <= t + 1e-6); tl = t - pp
    z = 1.0 + (0.06 * (1 - ease(tl / 0.35)) if pp > 0 else 0.04 * ease(t / 3.0)) + 0.015 * ((t % 5) / 5)
    cw, ch = int(W / z), int(H / z); x0 = (W - cw) // 2; y0 = (H - ch) // 2
    fr = cv2.resize(f[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    for ft in FLASH_T:
        if 0 <= t - ft < 0.38:
            q = (t - ft) / 0.38; c = -300 + q * (W + H * 0.55 + 600); band = np.clip(1 - np.abs(DIAG - c) / 260, 0, 1)[..., None] * 0.35 * (1 - q * 0.5)
            fr = fr + (np.array([255, 214, 150], np.float32) - fr) * band
    if t < HOOK_END:  # правило №4: крючок полностью виден с кадра 0
        a = 1.0 if t < HOOK_END - 0.25 else 1 - ease((t - (HOOK_END - 0.25)) / 0.25)
        comp(fr, PLATE, PX, PY, a)
        spp = min(max((t - 0.5) / 1.1, 0), 1)
        for L, yy in ((T1, TY[0]), (T2, TY[1]), (T3, TY[2])):
            comp(fr, shimmer(L, spp) if (0 < spp < 1 and L is not T3) else L, 512 - L.shape[1] // 2, yy, a)
    if t >= LOGO_IN:
        g = min(1, ease((t - LOGO_IN) / 0.3)); fr = fr * (1 - grad * g); fr = fr * (CDARK * g + (1 - g)); corner(fr, t)
        dots(fr, t)
    for s0, s1, LA, WL, tot, BD in caps:
        if s0 <= t < s1:
            tt = t - s0; T = s1 - s0; out = 1 - ease((tt - (T - 0.22)) / 0.22) if tt > T - 0.22 else 1
            aa = ease(tt / 0.3) * out; dy = int(30 * (1 - ease(tt / 0.3)))
            comp(fr, BD, 512 - BD.shape[1] // 2, DOT_Y - 70, aa)
            LAs = shimmer(LA, min(max((tt - 0.3) / 0.9, 0), 1)) if 0.3 < tt < 1.2 else LA
            comp(fr, LAs, 512 - LA.shape[1] // 2, CAPY_A + dy, aa)
            for k, (blurs, cx) in enumerate(WL):
                L, s, al = wordfx(blurs, tt - 0.12 - 0.08 * k); Ls = scaled(L, s)
                comp(fr, Ls, cx - Ls.shape[1] // 2, CAPY_B + (L.shape[0] - Ls.shape[0]) // 2, al * out)
            lw = int(tot * ease((tt - 0.35) / 0.4))
            if lw > 2:
                ln = np.zeros((5, lw, 4), np.float32); ln[..., :3] = (200, 165, 100); ln[..., 3] = 230
                comp(fr, ln, 512 - lw // 2, CAPY_B + 112, out)
            dots(fr, t)
    return fr
EL = tpl.end_layers(); Lend = {k: (A(im), xy) for k, (im, xy) in EL.items()}
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((290, 380, 790, 880), fill=(214, 170, 100, 90)); GLOW = A(glow.filter(ImageFilter.GaussianBlur(90)))
order = [('dj', 0.25), ('sub', 0.4), ('q1', 0.55), ('q2', 0.62), ('btn', 0.78), ('site', 0.92)]
def endframe(src, t):
    bg = A(Image.eval(Image.fromarray(src).filter(ImageFilter.GaussianBlur(28)), lambda v: int(v * 0.5)))
    fr = bg
    comp(fr, GLOW, 0, 0, ease(t / 0.6), log=False)
    hl, (hx, hy) = Lend['horse']; hs = shimmer(hl, (t - 0.9) / 1.0, 70) if 0.9 < t < 1.9 else hl
    comp(fr, hs, hx, hy, ease(t / 0.35))
    for k, d in order:
        lay, (x, y) = Lend[k]; aa = ease((t - d) / 0.35); dy = int(35 * (1 - aa))
        if k == 'dj' and 0.6 < t < 1.5: lay = shimmer(lay, (t - 0.6) / 0.9)
        if k == 'btn' and t > 1.4:
            s2 = 1 + 0.025 * np.sin((t - 1.4) * 2 * np.pi / 1.2); l2 = scaled(lay, s2)
            comp(fr, l2, x - (l2.shape[1] - lay.shape[1]) // 2, y - (l2.shape[0] - lay.shape[0]) // 2, aa); continue
        comp(fr, lay, x, y + dy, aa)
    return fr
# кадры исходника: обрезка по центру до 9:16 (477x848), апскейл lanczos + резкость
def src_frames():
    cmd = ['ffmpeg', '-v', 'error', '-i', SRC, '-vf', f'fps={FPS},crop=477:848:73:0,scale={W}:{H}:flags=lanczos,unsharp=5:5:0.7',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE); fs = []
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        fs.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
    return fs
def timeline(fs):  # индекс исходного кадра для каждого кадра итога
    n = len(fs); pull0 = int(END_T * FPS); out = []
    for i in range(NV):
        t = i / FPS
        if t < HOOK_END: out.append(('v', min(pull0 + i, n - 1)))
        elif t < END_T: out.append(('v', min(i, n - 1)))
        else: out.append(('e', min(i - pull0, n - 1)))
    return out
if __name__ == '__main__':
    fs = src_frames(); TL = timeline(fs); PREV = os.environ.get('PREVIEW')
    def render(i):
        _box[0] = None; k, j = TL[i]; t = i / FPS
        fr = frame(fs[j], t) if k == 'v' else endframe(fs[j], t - END_T)
        return np.clip(fr, 0, 255).astype(np.uint8)
    if PREV:
        for x in PREV.split(','):
            i = int(round(float(x) * FPS)); Image.fromarray(render(i)).save(f'/home/claude/work/kh/p_{float(x):05.2f}.jpg', quality=90)
        sys.exit()
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', SRC,
                            '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p',
                            '-c:a', 'copy', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    for i in range(NV):
        enc.stdin.write(render(i).tobytes())
        b = _box[0]
        if b and i % 1 == 0: ZLOG.append(['f%d' % i] + [int(v) for v in b])
    enc.stdin.close(); enc.wait()
    json.dump({'zone': [ZX0, ZY0, ZX1, ZY1], 'logo': CORNER_BOX, 'frames': ZLOG, 'photo': [('src', 1.0)]}, open('/home/claude/work/kh/zone_log.json', 'w'))
    print('done', NV, 'logo', CORNER_BOX)
