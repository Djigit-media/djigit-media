# Завод DJIGIT: автоконтроль финального ролика. Ролик показывать Валу ТОЛЬКО при всех PASS.
# Запуск: python3 control.py --video V.mp4 --beats beats.py --timeline timeline.json [--music-seg seg.wav]
# 1) ЗВУК: длина аудио = длине видео; по окнам 1 с нет тишины/обрыва до последней секунды.
# 2) ГОЛОС: Whisper по каждому биту финального ролика против утверждённого текста, по словам (нечёткое совпадение).
# 3) УДАРЕНИЯ: stress_ru.check по тексту (запрещённые знаки, опасные слова).
import argparse, json, os, re, subprocess, sys, difflib, importlib.util, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stress_ru import check
from num2words import num2words
def audio(path, ss=None, t=None):
    cmd = ['ffmpeg', '-v', 'error'] + (['-ss', str(ss)] if ss is not None else []) + (['-t', str(t)] if t is not None else []) + ['-i', path, '-vn', '-ac', '1', '-ar', '16000', '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32)
def dur(path, sel):
    o = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', sel, '-show_entries', 'stream=duration', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip()
    return float(o.split('\n')[0])
def norm(s):
    s = s.lower().replace('ё', 'е').replace('́', '')
    s = re.sub(r'(\d)\s+(\d{3})', r'\1\2', s)
    s = re.sub(r'\d+', lambda m: ' ' + num2words(int(m.group(0)), lang='ru') + ' ', s)
    s = s.replace('%', ' процентов ')
    return re.findall(r'[а-я]+', s)
def sim(a, b): return difflib.SequenceMatcher(None, a, b).ratio()
def word_check(ref, hyp):
    # каждое слово эталона должно найтись по порядку в услышанном (нечётко, >=0.6), числа сверяются по корню
    miss = []; j = 0
    for w in ref:
        best = None
        for k in range(j, min(len(hyp), j + 6)):
            if sim(w, hyp[k]) >= 0.6 or (len(w) > 4 and hyp[k].startswith(w[:4])): best = k; break
        if best is None: miss.append(w)
        else: j = best + 1
    return miss
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--video'); ap.add_argument('--beats'); ap.add_argument('--timeline'); ap.add_argument('--music-seg', default='/tmp/kochari_45_80.wav'); a = ap.parse_args()
    res = []
    # 1 звук
    dv, da = dur(a.video, 'v:0'), dur(a.video, 'a:0')
    au = audio(a.video); win = 16000
    lv = [20 * np.log10(np.sqrt(np.mean(au[i:i + win] ** 2)) + 1e-9) for i in range(0, len(au) - win // 2, win)]
    quiet = [i for i, l in enumerate(lv) if l < -40]
    res.append(('ЗВУК', abs(dv - da) < 0.15 and not quiet, f'видео {dv:.2f} c, аудио {da:.2f} c, мин {min(lv):.1f} dB, тихие секунды {quiet}'))
    # 1б музыка: огибающая баса финала совпадает с нужным куском, повторённым по кругу (ловит обрыв, не тот кусок, тишину)
    def env(x, hop=800, n=2048):
        fr = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hanning(n); S = np.abs(np.fft.rfft(fr, axis=1))
        f = np.fft.rfftfreq(n, 1 / 16000); bnd = (f >= 40) & (f <= 250); return np.log(S[:, bnd].sum(1) + 1e-6)
    seg = audio(a.music_seg); stem = np.tile(seg, len(au) // len(seg) + 1)[:len(au)]
    E1, E2 = env(au), env(stem); w = 80
    cs = [np.corrcoef(E1[i:i + w], E2[i:i + w])[0, 1] for i in range(0, len(E1) - w, w)]
    badw = [c < 0.3 for c in cs]; run = mx = 0
    for x in badw: run = run + 1 if x else 0; mx = max(mx, run)
    res.append(('МУЗЫКА', mx <= 2 and cs[-1] >= 0.3, f'кусок по кругу до конца: подряд плохих окон по 4 с {mx}, последнее окно {cs[-1]:.2f}'))
    # 2 голос
    sp = importlib.util.spec_from_file_location('b', a.beats); b = importlib.util.module_from_spec(sp); sp.loader.exec_module(b)
    tl = json.load(open(a.timeline)); from faster_whisper import WhisperModel
    m = WhisperModel('small', device='cpu', compute_type='int8'); bad = []
    for (k, text), st, d in zip(b.BEATS, tl['starts'], tl['durs']):
        x = audio(a.video, max(0, st - 0.05), d + 0.25)
        segs, _ = m.transcribe(x, language='ru', initial_prompt=text); heard = ' '.join(s.text for s in segs)
        miss = word_check(norm(text), norm(heard))
        if miss: bad.append(f'{k}: нет слов {miss} | слышно: {heard.strip()}')
    res.append(('ГОЛОС', not bad, '; '.join(bad) or 'все слова на месте'))
    # 3 ударения
    st = [f'{k}: {x}' for k, t in b.BEATS for x in check(t)]
    res.append(('УДАРЕНИЯ', not st, '; '.join(st) or 'запрещённых знаков и опасных слов нет'))
    for n, ok, info in res: print(f"{'PASS' if ok else 'FAIL'} {n}: {info}")
    print('ИТОГ:', 'ВСЁ PASS' if all(r[1] for r in res) else 'ЕСТЬ FAIL')
