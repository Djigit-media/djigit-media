import asyncio, os, re, subprocess, sys, json, certifi
certifi.where = lambda: '/root/.ccr/ca-bundle.crt'
import edge_tts
sys.path.insert(0, os.path.dirname(__file__)); from beats import BEATS
OUT = os.path.join(os.path.dirname(__file__), '..', 'vo')
async def gen(t, p):
    for k in range(30):
        try:
            await edge_tts.Communicate(t, 'ru-RU-DmitryNeural', proxy=os.environ.get('HTTPS_PROXY')).save(p)
            if os.path.getsize(p) > 3000: return
        except Exception as e:
            print('retry', k, repr(e)[:80], flush=True); await asyncio.sleep(6 + 3 * min(k, 6))
    raise SystemExit('fail ' + t)
async def one(i, key, t):
    out = f'{OUT}/{i:02d}_{key}.wav'
    if os.path.exists(out) and os.path.getsize(out) > 3000: return
    parts = [x.strip() for x in re.split(r'(?<=[.!?:])\s+', t) if x.strip()]
    fs = []
    for j, x in enumerate(parts):
        p = f'/tmp/v6_{i}_{j}.mp3'
        if not (os.path.exists(p) and os.path.getsize(p) > 3000): await gen(x, p); await asyncio.sleep(0.5)
        fs.append(p)
    ins = []; fl = []
    for j, p in enumerate(fs):
        ins += ['-i', p]
        fl.append(f'[{j}:a]silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo=1.08,apad=pad_dur={0.18 if j < len(fs)-1 else 0}[a{j}]')
    fl.append(''.join(f'[a{j}]' for j in range(len(fs))) + f'concat=n={len(fs)}:v=0:a=1[o]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + ins + ['-filter_complex', ';'.join(fl), '-map', '[o]', '-ar', '48000', '-ac', '1', out], check=True)
async def main():
    idx = [int(a) for a in sys.argv[1:]] or list(range(len(BEATS)))
    for i in idx: await one(i, *BEATS[i])
    print('DONE', flush=True)
asyncio.run(main())
