# Сведение: голос по таймлайну + Kochari 0:45-1:20 по кругу (0.28 под голосом, после голоса громче), лимитер.
import json, glob, subprocess, os
R = os.path.join(os.path.dirname(__file__), '..'); tl = json.load(open(f'{R}/timeline_v10.json'))
M = f'{R}/../fastfood/kochari.mp3'; T = tl['total']; E = tl['end_start']
SEG = '/tmp/kochari_45_80.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '45', '-t', '35', '-i', M, '-ar', '48000', '-ac', '2', SEG], check=True)
# кусок 0:45-1:20 по кругу до конца ролика (раньше -t 35 на входе обрезал музыку на 35 с)
ins = ['-stream_loop', '-1', '-i', SEG]; fl = []; lab = []
for i, (k, s) in enumerate(zip(tl['keys'], tl['starts'])):
    f = glob.glob(f'{R}/vo10/{i:02d}_{k}.wav')[0]; ins += ['-i', f]
    fl.append(f'[{i+1}:a]aresample=48000,adelay={int(s*1000)}:all=1[v{i}]'); lab.append(f'[v{i}]')
fl.append(f"[0:a]aresample=48000,atrim=0:{T:.3f},volume='if(lt(t,{E:.2f}),0.22,0.22+0.3*min(1,(t-{E:.2f})/0.8))':eval=frame,afade=t=out:st={T-1.2:.2f}:d=1.2[m]")
fl.append(''.join(lab) + f'amix=inputs={len(lab)}:normalize=0[vv]')
fl.append('[vv][m]amix=inputs=2:normalize=0,alimiter=limit=0.95,aformat=channel_layouts=stereo[o]')
subprocess.run(['ffmpeg', '-v', 'error', '-y'] + ins + ['-filter_complex', ';'.join(fl), '-map', '[o]', '-t', f'{T:.3f}', '-c:a', 'aac', '-b:a', '256k', f'{R}/audio_v10.m4a'], check=True)
# проверка: музыка звучит на всём ролике (окна по 5 с, уровень музыки отдельно)
import numpy as np
raw = subprocess.run(['ffmpeg', '-v', 'error', '-stream_loop', '-1', '-i', SEG, '-t', f'{T:.3f}', '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout
m = np.frombuffer(raw, np.float32); win = 16000 * 5
lv = [20 * np.log10(np.sqrt(np.mean(m[i:i + win] ** 2)) + 1e-9) for i in range(0, len(m) - win // 2, win)]
assert len(m) / 16000 >= T - 0.5 and min(lv) > -40, f'МУЗЫКА НЕ НА ВСЁМ РОЛИКЕ: {len(m)/16000:.1f}s из {T:.1f}s, мин {min(lv):.1f} dB'
print('ok, музыка', round(len(m) / 16000, 1), 'с из', round(T, 1), 'мин уровень', round(min(lv), 1), 'dB')
