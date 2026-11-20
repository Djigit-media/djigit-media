import sys,subprocess,numpy as np,cv2
sys.path.insert(0,'/home/claude/work/tpl')
import tpl
from PIL import Image,ImageDraw,ImageFilter
LANG=sys.argv[1]  # ru | en
OUT=f'/home/claude/kl/djigit_mcd_{LANG}.mp4'
W,H,FPS=1080,1920,30
CLIPS=sys.argv[2].split(',')
def dur(f): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]).decode())
D=[dur(c) for c in CLIPS];STARTS=list(np.cumsum([0]+D[:-1]));TOTAL=sum(D)
END_LEN=3.0
# --- video: normalize and concat
inp=[];fl=[]
for k,c in enumerate(CLIPS):
    inp+=['-i',c];fl.append(f'[{k}:v]scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},setsar=1,format=rgb24[v{k}]')
fl.append(''.join(f'[v{k}]' for k in range(len(CLIPS)))+f'concat=n={len(CLIPS)}:v=1:a=0[o]')
p=subprocess.Popen(['ffmpeg','-v','error']+inp+['-filter_complex',';'.join(fl),'-map','[o]','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
def ease(t): t=min(max(t,0),1); return 1-(1-t)**3
def A(im): return np.array(im).astype(np.float32)
def comp(fr,lay,x,y,a=1.0):
    h,w=lay.shape[:2];x0,y0=max(x,0),max(y,0);x1,y1=min(x+w,W),min(y+h,H)
    if x1<=x0 or y1<=y0 or a<=0.003: return
    l=lay[y0-y:y1-y,x0-x:x1-x];al=l[...,3:4]/255*a
    fr[y0:y1,x0:x1]=fr[y0:y1,x0:x1]*(1-al)+l[...,:3]*al
def scaled(L,s):
    if abs(s-1)<0.004: return L
    return cv2.resize(L,(max(1,int(L.shape[1]*s)),max(1,int(L.shape[0]*s))),interpolation=cv2.INTER_LINEAR)
def shimmer(lay,p,width=90):
    h,w=lay.shape[:2];o=lay.copy();xx=np.arange(w)[None,:]+np.arange(h)[:,None]*0.6
    c=-width+p*(w+h*0.6+2*width);b=np.clip(1-np.abs(xx-c)/width,0,1)[...,None]
    o[...,:3]=o[...,:3]+(255-o[...,:3])*b*0.55;return o
CORNER=A(tpl.corner_layer(subt='СОВРЕМЕННАЯ ГРУЗИНСКАЯ КУХНЯ' if LANG=='ru' else 'MODERN GEORGIAN CUISINE').crop((0,0,460,480)))
HB=tpl.CORNER['horse'];HXY=(HB[0]-12,HB[1]-12,HB[2]+13,HB[3]+13)
LOGO_IN=0.6;SWEEPS=[LOGO_IN+0.5+6*k for k in range(10)]
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
 '-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','/tmp/vid_'+LANG+'.mp4'],stdin=subprocess.PIPE)
i=0;last=None
while True:
    b=p.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    f=np.frombuffer(b,np.uint8).reshape(H,W,3);t=i/FPS;last=f;fr=f.astype(np.float32)
    q=ease((t-LOGO_IN)/0.35);CL=CORNER
    for st in SWEEPS:
        if st<=t<st+1.0:
            CL=CORNER.copy();x0_,y0_,x1_,y1_=HXY;CL[y0_:y1_,x0_:x1_]=shimmer(CORNER[y0_:y1_,x0_:x1_],(t-st)/1.0,45);break
    comp(fr,CL,0,0,q)
    enc.stdin.write(np.clip(fr,0,255).astype(np.uint8).tobytes());i+=1
NV=i
if LANG=='ru': EL=tpl.end_layers()
else:
    EL=tpl.end_layers('Want this restaurant','in your city?','DM «FRANCHISE»','MODERN GEORGIAN CUISINE');EL.pop('site')
bgs=Image.fromarray(last).filter(ImageFilter.GaussianBlur(28));BG=A(Image.eval(bgs,lambda v:int(v*0.5)))
glow=Image.new('RGBA',(W,H),(0,0,0,0));ImageDraw.Draw(glow).ellipse((290,380,790,880),fill=(214,170,100,90));GLOW=A(glow.filter(ImageFilter.GaussianBlur(90)))
L={k:(A(im),xy) for k,(im,xy) in EL.items()}
order=[o for o in [('dj',0.25),('sub',0.4),('q1',0.55),('q2',0.62),('btn',0.78),('site',0.92)] if o[0] in L]
for j in range(int(END_LEN*FPS)):
    t=j/FPS;m=ease(t/0.25);fr=BG*m+last.astype(np.float32)*(1-m)
    comp(fr,GLOW,0,0,ease(t/0.6))
    hl,(hx,hy)=L['horse'];hs=shimmer(hl,(t-0.9)/1.0,70) if 0.9<t<1.9 else hl
    comp(fr,hs,hx,hy,ease(t/0.35))
    for k,d in order:
        lay,(x,y)=L[k];aa=ease((t-d)/0.35);dy=int(35*(1-aa))
        if k=='dj' and 0.6<t<1.5: lay=shimmer(lay,(t-0.6)/0.9)
        if k=='btn' and t>1.4:
            s2=1+0.025*np.sin((t-1.4)*2*np.pi/1.2);l2=scaled(lay,s2);comp(fr,l2,x-(l2.shape[1]-lay.shape[1])//2,y-(l2.shape[0]-lay.shape[0])//2,aa);continue
        comp(fr,lay,x,y+dy,aa)
    enc.stdin.write(np.clip(fr,0,255).astype(np.uint8).tobytes())
enc.stdin.close();enc.wait()
VT=NV/FPS;TT=VT+END_LEN
# --- audio
ai=[];af=[]
for k,c in enumerate(CLIPS):
    ai+=['-i',c];af.append(f'[{k}:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{D[k]:.3f},asetpts=PTS-STARTPTS[a{k}]')
af.append(''.join(f'[a{k}]' for k in range(len(CLIPS)))+f'concat=n={len(CLIPS)}:v=0:a=1[kl]')
n=len(CLIPS)
ai+=['-ss','45','-i','/mnt/user-data/uploads/7e355929-New_Age_Armenia_-_Kochari_Armenian_Folk_Dance.mp3'];mus=n
af.append('[kl]anull[voc]')
af.append(f'[voc]apad,atrim=0:{TT:.3f}[vocp]')
af.append(f"[{mus}:a]atrim=0:{TT:.3f},aresample=48000,aformat=channel_layouts=stereo,volume='if(lt(t,{VT:.2f}),0.28,0.28+0.55*min(1,(t-{VT:.2f})/0.6))':eval=frame,afade=t=out:st={TT-0.6:.2f}:d=0.6[mu]")
af.append('[vocp][mu]amix=inputs=2:normalize=0,alimiter=limit=0.95[aout]')
subprocess.run(['ffmpeg','-v','error','-y']+ai+['-i','/tmp/vid_'+LANG+'.mp4','-filter_complex',';'.join(af),
 '-map',f'{n+1}:v','-map','[aout]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest',OUT],check=True)
print('done',OUT,round(TT,2),[round(s,2) for s in STARTS])
