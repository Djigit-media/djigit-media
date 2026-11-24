# ГЕЙТ КАЧЕСТВА DJIGIT (инструкция проекта, блок ГЕЙТ). Ролик Валу и наружу только при всех PASS.
# Запуск: python3 tools/gate.py --video V.mp4 --ref REF.mp4 --script src/render_vNN.py --ref-script src/render_vMM.py --zone-log zone_log.json
#   --ref: утверждённая прошлая версия (битрейт не ниже, звук сверяется), --script/--ref-script: тексты на экране слово в слово.
# Зона (Пульт 0001): x 65..960 (выше 1100 px до 1015), y 270..1500 для текста, плашек, цифр и логотипов.
import argparse, json, re, ast, subprocess, hashlib, sys, numpy as np, cv2
ZONE = (65, 270, 960, 1500)   # Meta Reels: 6% сбоку, 14% сверху; низ 1500 (обычный пост). Выше 1100 справа можно до 1015 (кнопок там нет)
ZONE_R_TOP = (1015, 1100)
CONTACTS = {'djigit.biz', 'djigit.com.ua', 'partners@djigit.biz', 'info@djigit.com.ua', '+49 174 760 55 42', '+38 067 460 00 04'}
STOP_MUSIC = ['kochari']
def probe(p):
    o = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', p], capture_output=True, text=True).stdout)
    v = [s for s in o['streams'] if s['codec_type'] == 'video'][0]; a = [s for s in o['streams'] if s['codec_type'] == 'audio']
    return v, (a[0] if a else None), o['format']
def audio_md5(p):
    return hashlib.md5(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-map', '0:a:0', '-c', 'copy', '-f', 'data', '-'], capture_output=True).stdout).hexdigest()
def pcm(p):
    return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-vn', '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
def strings(path):
    t = ast.parse(open(path, encoding='utf-8').read()); out = set()
    for n in ast.walk(t):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and re.search('[А-ЯЁA-Z]{3,}|€|%|м²|djigit', n.value) and not re.search(r'[/\\]|\.(py|png|jpe?g|mp4|wav|json|m4a)|^[a-z_]+$|^[A-Z_]+$', n.value):
            out.add(n.value)
    return out
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    for k in ('video', 'ref', 'script', 'ref_script', 'zone_log', 'music', 'timeline', 'extra_src'): ap.add_argument('--' + k.replace('_', '-'), dest=k, default='')
    ap.add_argument('--music-waiver', default='')
    ap.add_argument('--text-approved', default='', help='строки, изменённые по слову Вала: «новая|старая|кто когда»')
    a = ap.parse_args(); res = []
    v, au, fm = probe(a.video); rv, rau, rfm = probe(a.ref)
    vb, rb = int(v.get('bit_rate', 0)), int(rv.get('bit_rate', 0))
    ok = v['width'] == 1080 and v['height'] == 1920 and v['codec_name'] == 'h264' and v['r_frame_rate'] == '30/1' and vb >= rb
    res.append(('1 ФОРМАТ', ok, f"{v['width']}x{v['height']} {v['codec_name']} {v['r_frame_rate']} fps, видео {vb/1e6:.2f} Мбит/с (эталон {rb/1e6:.2f})"))
    # 2 безопасная зона: рамка слоя надписей каждого кадра после раскладки + угловой логотип
    zl = json.load(open(a.zone_log)); x0, y0, x1, y1 = ZONE; bad = []
    lb = zl['logo']
    if not (lb[0] >= x0 and lb[1] >= y0 and lb[2] <= x1 and lb[3] <= y1): bad.append(f'логотип {lb}')
    for i, f in enumerate(zl['frames']):
        g, bx0, by0, bx1, by1 = f[:5]; xl = f[5] if len(f) > 5 else (bx1 if by1 >= ZONE_R_TOP[1] else -1)   # xl: правый край надписей ниже 1100 px
        if bx0 < x0 or by0 < y0 or by1 > y1 or bx1 > ZONE_R_TOP[0] or xl > x1: bad.append(f'кадр {i} ({g}) {bx0},{by0}..{bx1},{by1}')
    ext = np.array([f[1:5] for f in zl['frames']]); span = f'надписи по всем кадрам x {ext[:,0].min()}..{ext[:,2].max()}, y {ext[:,1].min()}..{ext[:,3].max()}; логотип {lb}'
    ph = zl.get('photo', []); cut = [f'{g} {r}' for g, r in ph if r < 0.995]
    if not ph: cut = ['нет лога фото-слоёв']
    bad += [f'фото-слой обрезан: {c}' for c in cut[:5]]
    res.append(('2 ЗОНА', not bad and len(zl['frames']) > 0, (span if not bad else '; '.join(bad[:8])) + f'; кадров проверено {len(zl["frames"])}, фото-слои целиком в кадре: {len(ph)} кадров'))
    # 3 первый кадр
    cap = cv2.VideoCapture(a.video); okf, f0 = cap.read(); g0 = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
    sharp = cv2.Laplacian(g0, cv2.CV_64F).var(); res.append(('3 КАДР 0', okf and g0.mean() > 25 and g0.std() > 20 and sharp > 50, f'яркость {g0.mean():.0f}, контраст {g0.std():.0f}, резкость {sharp:.0f}'))
    # 4 звук: длина = видео, нет тишины в конце, нет щелчков; звук тот же, что в эталоне
    dv, da = float(v['duration']), float(au['duration']); x = pcm(a.video); win = 16000
    lv = [20 * np.log10(np.sqrt(np.mean(x[i:i + win] ** 2)) + 1e-9) for i in range(0, len(x) - win // 2, win)]
    tail = 20 * np.log10(np.sqrt(np.mean(x[-2 * win:] ** 2)) + 1e-9)
    # щелчки на склейках: всплеск ВЧ-энергии в 5 мс у границы бита против соседних 200 мс
    hp = np.abs(np.diff(x, 2)); clk = []
    for st in (json.load(open(a.timeline))['starts'] if a.timeline else []):
        i = int(st * 16000); w0 = hp[max(0, i - 3200):i + 3200]; c = hp[max(0, i - 80):i + 80]
        if len(c) and len(w0) and c.max() > 8 * (np.percentile(w0, 99) + 1e-6): clk.append(round(st, 2))
    clk = len(clk)
    same = audio_md5(a.video) == audio_md5(a.ref)
    res.append(('4 ЗВУК', abs(dv - da) < 0.15 and min(lv) > -40 and tail > -40 and clk == 0 and same,
                f'видео {dv:.2f} c, аудио {da:.2f} c, мин {min(lv):.1f} dB, последние 2 с {tail:.1f} dB, щелчков {clk}, дорожка байт в байт как в эталоне: {same}'))
    # 5 текст на экране слово в слово с утверждённой версией
    s1, s0 = strings(a.script), strings(a.ref_script); add, rem = s1 - s0, s0 - s1
    ok_new, ok_old = set(), set()
    for item in filter(None, a.text_approved.split(';')):
        n_, o_, who = item.split('|'); ok_new.add(n_); ok_old.add(o_)
    add, rem = add - ok_new, rem - ok_old
    res.append(('5 ТЕКСТ', not add and not rem, f'строк {len(s1)}' + (f'; новые {sorted(add)}; пропали {sorted(rem)}' if add or rem else ', совпадают с утверждённой' + (f' (изменено по слову Вала: {a.text_approved})' if a.text_approved else ''))))
    # 6 контакты
    src = open(a.script, encoding='utf-8').read() + ''.join(open(p, encoding='utf-8').read() for p in a.extra_src.split(',') if p); found = set(re.findall(r'[\w.]*djigit\.[a-z.]+|\+\d[\d ]{8,}\d', src))
    badc = {c for c in found if c not in CONTACTS and not c.startswith('/')}
    res.append(('6 КОНТАКТЫ', not badc and 'djigit.biz' in src, f'на экране: {sorted(found & CONTACTS)}' + (f'; чужие {sorted(badc)}' if badc else '')))
    # 7 музыка
    mus = a.music.lower(); stop = any(w in mus for w in STOP_MUSIC)
    if stop and a.music_waiver: res.append(('7 МУЗЫКА', True, f'{a.music}: оставлена по решению Вала ({a.music_waiver})'))
    else: res.append(('7 МУЗЫКА', not stop, a.music or 'не указана'))
    for n, ok, info in res: print(f"{'PASS' if ok else 'FAIL'} {n}: {info}")
    print('ИТОГ:', 'ВСЁ PASS' if all(r[1] for r in res) else 'ЕСТЬ FAIL')
    sys.exit(0 if all(r[1] for r in res) else 1)
