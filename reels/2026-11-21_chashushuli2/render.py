# Рилс-рецепт «Чашушули» v2 (новое видео Вала 21.11, 720p). Широкий крючок (правило №5), надпись с кадра 0 (правило №4).
# Кадры с парнем (3.7-5.8 и 39.63-44.7) заменены кадрами блюда из того же видео, голос целиком.
import sys,os,subprocess,numpy as np,cv2
sys.path.insert(0,'/home/claude/work/prev');sys.path.insert(0,'/home/claude/work/tpl')
import brand,tpl
tpl.BTN_TEXT='ОТКРОЙ СВОЙ DJIGIT'
from PIL import Image,ImageDraw,ImageFilter
D=os.path.dirname(os.path.abspath(__file__))
SRC=D+'/src/src.mp4';OUT=os.environ.get('OUT','/home/claude/work/r2/chashushuli2_v1.mp4')
W,H,FPS=1080,1920,30
L1,L2,L3='ЕСТЬ ГОВЯДИНА?','ГОТОВЬ ТОЛЬКО ТАК','грузинское чашушули'
TITLE_END=3.0;LOGO_IN=3.0
PY,PH=255,470
STEPS=[(5.8,13.22,'ШАГ 1','ОБЖАРИВАЕМ ГОВЯДИНУ'),(13.27,15.65,'ШАГ 2','МНОГО ЛУКА'),(15.7,21.35,'ШАГ 3','ПОМИДОРЫ БЕЗ КОЖИЦЫ'),
 (21.4,27.85,'ШАГ 4','СПЕЦИИ И ТОМАТНАЯ ПАСТА'),(27.9,32.05,'ШАГ 5','ПЕРЕЦ И 2 ЧАСА ТУШИМ'),(32.1,37.18,'ШАГ 6','КИНЗА И ЧЕСНОК'),
 (37.23,42.05,'ГОТОВО','СО СВЕЖЕЙ ЛЕПЁШКОЙ')]
# (start_frame,end_frame,speed) исходника 30 к/с; итог 1263 кадра = 42.1 с
CUTS=[(0,111,1),(1016,1079,1),(174,1189,1),(90,111,1),(1117,1143,29/26),(46,70,1)]
NV=1263;AUDIO_END=44.715
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
T1=A(tlayer(L1,900,118,gold=True,maxw=900));T2=A(tlayer(L2,900,118,gold=True,maxw=900))
T3=A(tlayer(L3.upper(),700,44,fill=(255,255,255,255),maxw=900))
TY=[PY+40,PY+185,PY+345]
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
    z=1.0+(0.06*(1-ease(tl/0.35)) if pp>0 else 0)+0.02*((t%6)/6)
    cw,ch=int(W/z),int(H/z);x0=(W-cw)//2;y0=(H-ch)//2
    g=cv2.resize(f[y0:y0+ch,x0:x0+cw],(W,H),interpolation=cv2.INTER_LINEAR)
    fr=g.astype(np.float32)
    for ft in FLASH_T:
        if 0<=t-ft<0.38:
            q=(t-ft)/0.38;c=-300+q*(W+H*0.55+600);band=np.clip(1-np.abs(DIAG-c)/260,0,1)[...,None]*0.35*(1-q*0.5)
            fr=fr+(np.array([255,214,150],np.float32)-fr)*band
    if t<TITLE_END:  # ПРАВИЛО №4: плашка и надпись полностью видны с кадра 0
        a=1.0 if t<TITLE_END-0.25 else 1-ease((t-(TITLE_END-0.25))/0.25)
        comp(fr,PLATE,45,PY,a)
        spp=min(max((t-0.6)/1.1,0),1)
        for L,yy in ((T1,TY[0]),(T2,TY[1]),(T3,TY[2])):
            comp(fr,shimmer(L,spp) if (0<spp<1 and L is not T3) else L,540-L.shape[1]//2,yy,a)
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
def mkbg(last):
    return A(Image.eval(Image.fromarray(last).filter(ImageFilter.GaussianBlur(28)),lambda v:int(v*0.5)))
CLEAN=os.environ.get('CLEAN','/home/claude/work/r2/clean.mp4')  # собирается из CUTS отдельными ffmpeg (см. README)
cmd=['ffmpeg','-v','error','-i',CLEAN,'-vf',f'fps={FPS},scale={W}:{H}:flags=lanczos,unsharp=5:5:0.6','-f','rawvideo','-pix_fmt','rgb24','-']
PREV=os.environ.get('PREVIEW')
p=subprocess.Popen(cmd,stdout=subprocess.PIPE)
if PREV:
    want={int(round(float(x)*FPS)) for x in PREV.split(',')};i=0
    while i<NV:
        b=p.stdout.read(W*H*3)
        if len(b)<W*H*3: break
        if i in want: Image.fromarray(np.clip(frame(np.frombuffer(b,np.uint8).reshape(H,W,3),i/FPS),0,255).astype(np.uint8)).save(f'/home/claude/work/r2/p_{i/FPS:.2f}.jpg',quality=88)
        last=np.frombuffer(b,np.uint8).reshape(H,W,3).copy();i+=1
    Image.fromarray(np.clip(endframe(last,mkbg(last),2.0),0,255).astype(np.uint8)).save('/home/claude/work/r2/p_end.jpg',quality=88)
    p.kill();sys.exit()
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',SRC,
 '-map','0:v','-map','1:a','-c:v','libx264','-preset','slow','-crf','13','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',OUT],stdin=subprocess.PIPE)
last=None;i=0
while i<NV:
    b=p.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    f=np.frombuffer(b,np.uint8).reshape(H,W,3);last=f
    enc.stdin.write(np.clip(frame(f,i/FPS),0,255).astype(np.uint8).tobytes());i+=1
    if i%150==0: print('frame',i,flush=True)
BG=mkbg(last);NE=int(np.ceil((AUDIO_END-i/FPS)*FPS))+3
for j in range(NE): enc.stdin.write(np.clip(endframe(last,BG,j/FPS),0,255).astype(np.uint8).tobytes())
enc.stdin.close();enc.wait();print('done',i,NE)
