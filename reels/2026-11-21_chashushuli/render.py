# Рилс-рецепт «Чашушули» по эталону DJIGIT (карп v6). Звук оригинала.
import sys,os,subprocess,numpy as np,cv2
sys.path.insert(0,'/home/claude/work/prev');sys.path.insert(0,'/home/claude/work/tpl')
import brand,tpl
tpl.BTN_TEXT='ОТКРОЙ СВОЙ DJIGIT'
from PIL import Image,ImageDraw,ImageFilter
SRC='/home/claude/work/r/src.mp4';OUT='/home/claude/work/r/chashushuli_v1.mp4'
W,H,FPS=1080,1920,30
TITLE='ЧАШУШУЛИ';TITLE_END=2.4;LOGO_IN=2.4
PY,PH=500,410            # плашка накрывает надпись исходника (y 632-784)
SRC_TXT=(0,600,1080,820) # полоса с надписью исходника, размываем до 1.7 с
STEPS=[(13.4,21.5,'ШАГ 1','ОБЖАРИВАЕМ ГОВЯДИНУ'),(21.55,25.0,'ШАГ 2','ЛУК К МЯСУ'),(25.05,29.6,'ШАГ 3','БОЛГАРСКИЙ ПЕРЕЦ'),
 (29.65,36.9,'ШАГ 4','МАСЛО, ПОМИДОРЫ, СПЕЦИИ'),(36.95,40.0,'ШАГ 5','КИПЯТОК И 40 МИНУТ'),(40.05,44.7,'ШАГ 6','КИНЗА И ЧЕСНОК'),
 (44.75,49.4,'ГОТОВО','МЯСО ТАЕТ ВО РТУ')]
VEND=49.5;AUDIO_END=52.06
def ease(t): t=min(max(t,0),1); return 1-(1-t)**3
def eback(t,s=1.7): t=min(max(t,0),1); return 1+(s+1)*(t-1)**3+s*(t-1)**2
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
def tlayer(t,w8,sz,fill=None,gold=False,maxw=1000,shadow=235):
    while brand.width(t,w8,sz)>maxw: sz-=2
    tw=int(brand.width(t,w8,sz))+40;L=Image.new('RGBA',(tw,int(sz*1.5)),(0,0,0,0))
    brand.draw_text(L,tw//2,0,t,w8,sz,fill,gold=gold)
    sh=Image.new('RGBA',L.size,(0,0,0,0));sh.putalpha(L.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda v:min(255,v*shadow//255)))
    out=Image.new('RGBA',(tw+30,L.height+30),(0,0,0,0));out.alpha_composite(sh,(15,19));out.alpha_composite(L,(15,15))
    return out
CORNER=A(tpl.corner_layer().crop((0,0,460,480)))
HB=tpl.CORNER['horse'];HXY=(HB[0]-12,HB[1]-12,HB[2]+13,HB[3]+13)
SWEEPS=[LOGO_IN+0.5+6*k for k in range(10)]
PLATE=A(brand.plate(990,PH,34))
T1=A(tlayer(TITLE,900,150,gold=True,maxw=900))
grad=np.zeros((H,W,1),np.float32);grad[:,:,0]=(np.clip((np.arange(H)-1150)/700,0,1)**1.3*0.55)[:,None]
CAPY_A,CAPY_B=1375,1455
caps=[]
for s0,s1,a,b in STEPS:
    LA=A(tlayer(a,900,58,gold=True));szb=70
    while brand.width(b,900,szb)>1000: szb-=2
    words=b.split(' ');sp=brand.width(' ',900,szb);tot=brand.width(b,900,szb);x=540-tot/2;WL=[]
    for wd in words:
        L=tlayer(wd,900,szb,fill=(255,255,255,255));ww=brand.width(wd,900,szb)
        WL.append(([A(L.filter(ImageFilter.GaussianBlur(r))) for r in (0,3,7)],int(x+ww/2)));x+=ww+sp
    caps.append((s0,s1,LA,WL,tot))
YY,XX=np.mgrid[0:H,0:W].astype(np.float32);DIAG=XX+YY*0.55
FLASH_T=[s for s,_,_,_ in STEPS]
PUNCH=[0]+FLASH_T
def wordfx(blurs,tt):
    p=min(max(tt/0.32,0),1);i=0 if p>0.75 else (1 if p>0.4 else 2)
    return blurs[i],0.7+0.3*eback(p),ease(p)
def frame(f,t):
    pp=max(k for k in PUNCH if k<=t+1e-6);tl=t-pp
    z=1.0+0.06*(1-ease(tl/0.35))+0.02*((t%6)/6)
    cw,ch=int(W/z),int(H/z);x0=(W-cw)//2;y0=(H-ch)//2
    g=cv2.resize(f[y0:y0+ch,x0:x0+cw],(W,H),interpolation=cv2.INTER_LINEAR)
    if t<1.7:  # страховка: размыть надпись исходника под плашкой
        a0,b0,a1,b1=SRC_TXT;g[b0:b1]=cv2.GaussianBlur(g[b0:b1],(0,0),25)
    fr=g.astype(np.float32)
    for ft in FLASH_T:
        if 0<=t-ft<0.38:
            q=(t-ft)/0.38;c=-300+q*(W+H*0.55+600);band=np.clip(1-np.abs(DIAG-c)/260,0,1)[...,None]*0.35*(1-q*0.5)
            fr=fr+(np.array([255,214,150],np.float32)-fr)*band
    if t<TITLE_END:
        a=1.0 if t<TITLE_END-0.25 else 1-ease((t-(TITLE_END-0.25))/0.25)
        sc=1.0+0.04*(1-ease(t/0.35));P=scaled(PLATE,sc)
        comp(fr,P,540-P.shape[1]//2,PY+(PH-P.shape[0])//2,a)
        spp=min(max((t-0.45)/1.1,0),1)
        aa=ease((t-0.1)/0.35)*a;dy=int(25*(1-ease((t-0.1)/0.35)))
        comp(fr,shimmer(T1,spp) if 0<spp<1 else T1,540-T1.shape[1]//2,PY+(PH-T1.shape[0])//2+dy,aa)
    if t>=LOGO_IN:
        fr=fr*(1-grad*min(1,ease((t-LOGO_IN)/0.3)))
        q=ease((t-LOGO_IN)/0.35);CL=CORNER
        for st in SWEEPS:
            if st<=t<st+1.0:
                CL=CORNER.copy();x0_,y0_,x1_,y1_=HXY;CL[y0_:y1_,x0_:x1_]=shimmer(CORNER[y0_:y1_,x0_:x1_],(t-st)/1.0,45);break
        comp(fr,CL,0,0,q)
    for s0,s1,LA,WL,tot in caps:
        if s0<=t<s1:
            tt=t-s0;T=s1-s0;out=1-ease((tt-(T-0.22))/0.22) if tt>T-0.22 else 1
            aa=ease(tt/0.3)*out;dy=int(30*(1-ease(tt/0.3)))
            LAs=shimmer(LA,min(max((tt-0.3)/0.9,0),1)) if 0.3<tt<1.2 else LA
            comp(fr,LAs,540-LA.shape[1]//2,CAPY_A+dy,aa)
            for k,(blurs,cx) in enumerate(WL):
                L,s,al=wordfx(blurs,tt-0.12-0.08*k);Ls=scaled(L,s)
                comp(fr,Ls,cx-Ls.shape[1]//2,CAPY_B+(L.shape[0]-Ls.shape[0])//2,al*out)
            lw=int(tot*ease((tt-0.35)/0.4))
            if lw>2:
                ln=np.zeros((5,lw,4),np.float32);ln[...,:3]=(200,165,100);ln[...,3]=230
                comp(fr,ln,540-lw//2,CAPY_B+118,out)
    return fr
EL=tpl.end_layers();Lend={k:(A(im),xy) for k,(im,xy) in EL.items()}
glow=Image.new('RGBA',(W,H),(0,0,0,0));ImageDraw.Draw(glow).ellipse((290,380,790,880),fill=(214,170,100,90));GLOW=A(glow.filter(ImageFilter.GaussianBlur(90)))
order=[('dj',0.25),('sub',0.4),('q1',0.55),('q2',0.62),('btn',0.78),('site',0.92)]
def endframe(last,BG,t):
    m=ease(t/0.25);fr=BG*m+last.astype(np.float32)*(1-m)
    comp(fr,GLOW,0,0,ease(t/0.6))
    hl,(hx,hy)=Lend['horse'];hs=shimmer(hl,(t-0.9)/1.0,70) if 0.9<t<1.9 else hl
    comp(fr,hs,hx,hy,ease(t/0.35))
    for k,d in order:
        lay,(x,y)=Lend[k];aa=ease((t-d)/0.35);dy=int(35*(1-aa))
        if k=='dj' and 0.6<t<1.5: lay=shimmer(lay,(t-0.6)/0.9)
        if k=='btn' and t>1.4:
            s2=1+0.025*np.sin((t-1.4)*2*np.pi/1.2);l2=scaled(lay,s2);comp(fr,l2,x-(l2.shape[1]-lay.shape[1])//2,y-(l2.shape[0]-lay.shape[0])//2,aa);continue
        comp(fr,lay,x,y+dy,aa)
    return fr
def grab(t):
    b=subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',SRC,'-frames:v','1','-vf',f'scale={W}:{H}:flags=lanczos,unsharp=5:5:0.6','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
    return np.frombuffer(b,np.uint8).reshape(H,W,3)
def mkbg(last):
    return A(Image.eval(Image.fromarray(last).filter(ImageFilter.GaussianBlur(28)),lambda v:int(v*0.5)))
if os.environ.get('PREVIEW'):
    outs=[]
    for t in [float(x) for x in os.environ['PREVIEW'].split(',')]:
        if t<VEND: fr=frame(grab(t),t)
        else:
            last=grab(VEND-1/FPS);fr=endframe(last,mkbg(last),t-VEND)
        outs.append(np.clip(fr,0,255).astype(np.uint8))
    for k,o in enumerate(outs): Image.fromarray(o).save(f'/home/claude/work/r/prev_{k}.jpg',quality=90)
    sys.exit()
cmd=['ffmpeg','-v','error','-ss','0.12','-i',SRC,'-vf',f'fps={FPS},scale={W}:{H}:flags=lanczos,unsharp=5:5:0.6','-t',str(VEND),'-f','rawvideo','-pix_fmt','rgb24','-']
p=subprocess.Popen(cmd,stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',SRC,
 '-map','0:v','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest',OUT],stdin=subprocess.PIPE)
last=None;i=0;N=int(VEND*FPS)
while i<N:
    b=p.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    f=np.frombuffer(b,np.uint8).reshape(H,W,3);t=i/FPS;last=f
    enc.stdin.write(np.clip(frame(f,t),0,255).astype(np.uint8).tobytes());i+=1
BG=mkbg(last);NE=int(np.ceil((AUDIO_END-i/FPS)*FPS))+3
try:
    for j in range(NE): enc.stdin.write(np.clip(endframe(last,BG,j/FPS),0,255).astype(np.uint8).tobytes())
    enc.stdin.close()
except BrokenPipeError: pass
enc.wait();print('done',i+NE)
