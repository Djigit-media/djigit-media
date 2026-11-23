# Сведение: голос по таймлайну + Kochari 0:45-1:20 по кругу (0.28 под голосом, после голоса громче), лимитер.
import json, glob, subprocess, os
R = os.path.join(os.path.dirname(__file__), '..'); tl = json.load(open(f'{R}/timeline_v10.json'))
M = f'{R}/../fastfood/kochari.mp3'; T = tl['total']; E = tl['end_start']
ins = ['-stream_loop', '-1', '-ss', '45', '-t', '35', '-i', M]; fl = []; lab = []
for i, (k, s) in enumerate(zip(tl['keys'], tl['starts'])):
    f = glob.glob(f'{R}/vo10/{i:02d}_{k}.wav')[0]; ins += ['-i', f]
    fl.append(f'[{i+1}:a]aresample=48000,adelay={int(s*1000)}:all=1[v{i}]'); lab.append(f'[v{i}]')
fl.append(f"[0:a]aresample=48000,atrim=0:{T:.3f},volume='if(lt(t,{E:.2f}),0.28,0.28+0.42*min(1,(t-{E:.2f})/0.8))':eval=frame,afade=t=out:st={T-1.2:.2f}:d=1.2[m]")
fl.append(''.join(lab) + f'amix=inputs={len(lab)}:normalize=0[vv]')
fl.append('[vv][m]amix=inputs=2:normalize=0,alimiter=limit=0.95,aformat=channel_layouts=stereo[o]')
subprocess.run(['ffmpeg', '-v', 'error', '-y'] + ins + ['-filter_complex', ';'.join(fl), '-map', '[o]', '-t', f'{T:.3f}', '-c:a', 'aac', '-b:a', '256k', f'{R}/audio_v10.m4a'], check=True)
print('ok')
