import asyncio, os, json, re, subprocess, certifi
certifi.where = lambda: '/root/.ccr/ca-bundle.crt'
import edge_tts
NEW = {
 1: "Супер акция для первых трёх партнёров! Франшиза Хинкали Хаус в твоём городе!",
 3: "Чистая прибыль в месяц: киоск от трёх тысяч евро, фасадное помещение от десяти тысяч евро.",
 5: "Для наших гостей всё и сразу. Красиво, вкусно, быстро и по доступным ценам.",
 8: "Формат фаст ка́жуал. Быстрая подача, вкусно, доступные цены. Это большой поток гостей.",
 10: "Два формата: киоск от десяти квадратных метров или фасадное помещение от восьмидесяти.",
 11: "Небольшие вложения: киоск от двадцати тысяч евро под ключ, фасадное помещение от сорока пяти тысяч евро под ключ. И быстрая окупаемость, до одного года.",
}
async def gen(t, p):
    for k in range(30):
        try:
            await edge_tts.Communicate(t, 'ru-RU-DmitryNeural', proxy=os.environ.get('HTTPS_PROXY')).save(p)
            if os.path.getsize(p) > 3000: return
        except Exception as e:
            print('retry', k, flush=True); await asyncio.sleep(8 + 3 * min(k, 6))
    raise SystemExit('fail ' + t)
async def one(i, t):
    out = f'vo5/s{i:02d}.mp3'
    if os.path.exists(out) and os.path.getsize(out) > 3000: return
    parts = [x.strip() for x in re.split(r'(?<=[.!])\s+', t) if x.strip()]
    fs = []
    for j, x in enumerate(parts):
        p = f'/tmp/v5_{i}_{j}.mp3'
        if not (os.path.exists(p) and os.path.getsize(p) > 3000): await gen(x, p); await asyncio.sleep(1)
        fs.append(p)
    ins = []; fl = []
    for j, p in enumerate(fs): ins += ['-i', p]; fl.append(f'[{j}:a]apad=pad_dur=0.22[a{j}]')
    fl.append(''.join(f'[a{j}]' for j in range(len(fs))) + f'concat=n={len(fs)}:v=0:a=1[o]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + ins + ['-filter_complex', ';'.join(fl), '-map', '[o]', '-b:a', '128k', out], check=True)
async def main():
    for i, t in NEW.items(): await one(i, t)
    print('DONE', flush=True)
asyncio.run(main())
