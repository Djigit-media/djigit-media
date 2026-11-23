# Автопроверка рилса DJIGIT перед показом Валу. Запуск:
#   python3 qa_reel.py --video V.mp4 --beats beats.py --vo VO_DIR --photos p1.png p2.jpg ... --out QA_DIR
# Выдаёт отчёт qa.md и лист кадров sheet.jpg (смотреть ГЛАЗАМИ весь лист, это обязательный шаг).
import argparse, os, re, json, subprocess, difflib, importlib.util, numpy as np, cv2
from PIL import Image, ImageDraw
def probe(v):
    j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,width,height,r_frame_rate,bit_rate:format=duration,size', '-of', 'json', v], capture_output=True, text=True).stdout)
    return j
def norm(t): return re.sub(r'[^а-яёa-z0-9 ]', ' ', t.lower().replace('́', '').replace('ё', 'е')).split()
def voice_check(beats, vo):
    from faster_whisper import WhisperModel
    m = WhisperModel('small', device='cpu', compute_type='int8'); rows = []
    for i, (k, t) in enumerate(beats):
        f = os.path.join(vo, f'{i:02d}_{k}.wav')
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
        a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
        segs, _ = m.transcribe(a, language='ru'); heard = ' '.join(s.text for s in segs)
        r = difflib.SequenceMatcher(None, norm(t), norm(heard)).ratio(); rows.append((k, round(r, 2), t, heard))
    return rows
def dhash(p, n=12):
    g = np.array(Image.open(p).convert('L').resize((n + 1, n), Image.LANCZOS), np.int16); return (g[:, 1:] > g[:, :-1]).flatten()
def dup_check(photos):
    hs = {p: dhash(p) for p in photos}; out = []
    ps = list(hs)
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            d = int((hs[ps[i]] != hs[ps[j]]).sum())
            if d < 30: out.append((os.path.basename(ps[i]), os.path.basename(ps[j]), d))
    return out
def style_stats(photos):
    rows = []
    for p in photos:
        L = cv2.cvtColor(np.array(Image.open(p).convert('RGB')), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
        rows.append((os.path.basename(p), *[round(float(x), 1) for x in L.mean(0)], round(float(L[:, 0].std()), 1)))
    return rows
def sheet(v, out, step=2.0):
    d = float(probe(v)['format']['duration']); ts = np.arange(0, d, step); w, h = 216, 384; cols = 12
    S = Image.new('RGB', (w * cols, (h + 18) * int(np.ceil(len(ts) / cols))), 'white'); dr = ImageDraw.Draw(S)
    for i, t in enumerate(ts):
        f = f'/tmp/qa_{i}.jpg'; subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', v, '-frames:v', '1', '-vf', f'scale={w}:{h}', f])
        x, y = (i % cols) * w, (i // cols) * (h + 18); S.paste(Image.open(f), (x, y)); dr.text((x + 3, y + h + 3), f'{t:.0f}s', fill='black')
    S.save(out, quality=88); return len(ts)
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--video'); ap.add_argument('--beats'); ap.add_argument('--vo'); ap.add_argument('--photos', nargs='*', default=[]); ap.add_argument('--out', default='qa')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); R = ['# QA рилса', '']
    j = probe(a.video); v = [s for s in j['streams'] if s['codec_name'] == 'h264'][0]
    ok = v['width'] == 1080 and v['height'] == 1920 and v['r_frame_rate'] == '30/1'
    R += [f"## Техника: {'OK' if ok else 'ОШИБКА'} {v['width']}x{v['height']} {v['r_frame_rate']} {float(j['format']['duration']):.1f}s {int(j['format']['size'])/1e6:.0f} МБ", '']
    if a.beats and a.vo:
        sp = importlib.util.spec_from_file_location('b', a.beats); b = importlib.util.module_from_spec(sp); sp.loader.exec_module(b)
        R += ['## Голос против сценария (ниже 0.80 = переслушать и переделать)']
        for k, r, t, h in voice_check(b.BEATS, a.vo): R.append(f"- {'!! ' if r < .8 else ''}{k}: {r} | слышно: {h.strip()}")
        R.append('')
    if a.photos:
        dd = dup_check(a.photos); R += ['## Повторы и почти-дубли фото', *(f'- {x} ~ {y} (dist {d})' for x, y, d in dd)] if dd else ['## Повторы фото: нет']
        R += ['', '## Цвет фото (L, a, b, контраст): все места должны быть близки друг к другу, все блюда друг к другу', *(f'- {r}' for r in style_stats(a.photos)), '']
    n = sheet(a.video, os.path.join(a.out, 'sheet.jpg')); R += [f'## Лист кадров: {a.out}/sheet.jpg ({n} кадров, каждые 2 с). ПОСМОТРЕТЬ ЦЕЛИКОМ.']
    open(os.path.join(a.out, 'qa.md'), 'w').write('\n'.join(R)); print('\n'.join(R))
