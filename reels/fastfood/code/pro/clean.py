import cv2,numpy as np,sys,json,subprocess,os,time
import scipy.sparse as sp,scipy.sparse.linalg as spl
def K(n):return cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(n,n))
def rd(p):
    c=cv2.VideoCapture(p);F=[]
    while True:
        ok,f=c.read()
        if not ok:break
        F.append(f)
    return F
def HSV(f):
    h,s,v=cv2.split(cv2.cvtColor(f,cv2.COLOR_BGR2HSV));return h.astype(np.int16),s.astype(np.int16),v.astype(np.int16)
def comps(m,conn=8):return cv2.connectedComponentsWithStats(m,connectivity=conn)
def cc(l,i,st,pad,H,W):
    x,y,w,h,a=st[i];x0,y0,x1,y1=max(0,x-pad),max(0,y-pad),min(W,x+w+pad),min(H,y+h+pad)
    return (l[y0:y1,x0:x1]==i).astype(np.uint8),(x0,y0,x1,y1)
def ring(c,test,r):
    rg=cv2.dilate(c,K(2*r+1))-c;return float((rg&test).sum())/max(1,int(rg.sum()))
def put(dst,l,i,st):
    x,y,w,h,a=st[i];dst[y:y+h,x:x+w][l[y:y+h,x:x+w]==i]=1
def hfill(img,mask,src,sig=1.5,const=None):
    """harmonic (Laplace) interpolation of mask from src pixels; everything else is a no-flux border"""
    H,W=mask.shape;out=img.astype(np.float32)
    if not mask.any():return out
    srcb=(src>0)&(mask==0);sf=srcb.astype(np.float32)
    num=cv2.GaussianBlur(out*sf[...,None],(0,0),sig);den=cv2.GaussianBlur(sf,(0,0),sig)
    sm=num/np.maximum(den,1e-4)[...,None]
    n,lab,st,_=cv2.connectedComponentsWithStats(mask,connectivity=4)
    for i in range(1,n):
        x,y,w,h,a=st[i]
        M=np.zeros((h+2,w+2),bool);S=np.zeros((h+2,w+2),bool);V=np.zeros((h+2,w+2,3),np.float32)
        M[1:-1,1:-1]=lab[y:y+h,x:x+w]==i
        ya,yb,xa,xb=max(y-1,0),min(y+h+1,H),max(x-1,0),min(x+w+1,W)
        S[ya-(y-1):yb-(y-1),xa-(x-1):xb-(x-1)]=srcb[ya:yb,xa:xb]
        V[ya-(y-1):yb-(y-1),xa-(x-1):xb-(x-1)]=sm[ya:yb,xa:xb]
        ys,xs=np.nonzero(M);N=len(ys);idx=np.full(M.shape,-1,np.int64);idx[ys,xs]=np.arange(N)
        diag=np.zeros(N);b=np.zeros((N,3));rows=[];cols=[];hasd=False
        for dy,dx in((1,0),(-1,0),(0,1),(0,-1)):
            ny,nx=ys+dy,xs+dx;mm=M[ny,nx];ss=S[ny,nx]
            rows.append(np.nonzero(mm)[0]);cols.append(idx[ny[mm],nx[mm]])
            diag+=mm;diag+=ss
            if ss.any():hasd=True;b[ss]+=V[ny[ss],nx[ss]]
        if not hasd:
            if const is not None:out[y-1+ys,x-1+xs]=const
            continue
        r=np.concatenate([np.arange(N)]+rows);c=np.concatenate([np.arange(N)]+cols)
        d=np.concatenate([diag]+[-np.ones(len(q)) for q in rows])
        A=sp.csc_matrix((d,(r,c)),shape=(N,N))
        sol=np.linalg.solve(A.toarray(),b) if N<=4 else spl.splu(A).solve(b)
        out[y-1+ys,x-1+xs]=sol
    return out
# ---------------- wall signs ----------------
def basic(h,s,v):
    red=(((h<=8)|(h>=170))&(s>=170)&(v>=60)).astype(np.uint8)
    ys=((h>=10)&(h<=36)&(s>=165)&(v>=160)).astype(np.uint8)      # sign face
    yl=((h>=9)&(h<=40)&(s>=150)&(v>=90)).astype(np.uint8)        # face + dark gold sides
    return red,ys,yl
def sign_cands(h,s,v):
    """every bright-yellow blob in the top of the frame with red wall around it"""
    H,W=h.shape;red,ys,yl=basic(h,s,v);n,l,st,ce=comps(ys);out=[]
    for i in range(1,n):
        x,y,w,hh,a=st[i];edge=(x<=1 or x+w>=W-1)
        if a<300 or a>90000 or y+hh>0.31*H:continue
        c,(x0,y0,x1,y1)=cc(l,i,st,30,H,W);band=cv2.dilate(c,K(57))-cv2.dilate(c,K(27))
        fr=float((band&red[y0:y1,x0:x1]).sum())/max(1,int(band.sum()));ext=a/float(w*hh)
        if fr<0.4:continue
        strict=(not edge) and fr>=0.7 and a>=1500 and 0.3<=ext<=0.8 and hh>=0.9*w
        out.append({'bb':[int(x),int(y),int(x+w),int(y+hh)],'strict':bool(strict),'id':i})
    return out,(l,st),red,ys,yl
def iou(a,b):
    iw=min(a[2],b[2])-max(a[0],b[0]);ih=min(a[3],b[3])-max(a[1],b[1])
    if iw<=0 or ih<=0:return 0.0
    i=iw*ih;return i/float((a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-i)
def track_signs(C):
    T=len(C);ACC=[[c['bb'] for c in C[t] if c['strict']] for t in range(T)]
    for it in range(60):
        ch=False
        for order in(range(T),range(T-1,-1,-1)):
            for t in order:
                near=(ACC[t-1] if t>0 else [])+(ACC[t+1] if t<T-1 else [])
                for c in C[t]:
                    if c['bb'] in ACC[t]:continue
                    if any(iou(c['bb'],q)>=0.3 for q in near):ACC[t].append(c['bb']);ch=True
        if not ch:break
    OK=[]
    for t in range(T):
        nb=(ACC[t-1] if t>0 else [])+(ACC[t+1] if t<T-1 else [])
        OK.append([b for b in ACC[t] if any(iou(b,q)>=0.3 for q in nb)])
    return OK
def sign_region(H,W,l,st,ids):
    R=np.zeros((H,W),np.uint8);m=np.zeros((H,W),np.uint8)
    for i in ids:
        c=np.zeros((H,W),np.uint8);put(c,l,i,st);m|=c
        hm=np.zeros((H,W),np.uint8);cv2.fillConvexPoly(hm,cv2.convexHull(cv2.findNonZero(c)),1)
        mg=int(np.clip(0.09*max(st[i,2],st[i,3]),8,22));R|=cv2.dilate(hm,K(2*mg+1))
    return R,m
def sign_mask(h,s,v,R,m,red,ys,yl,fg=None):
    H,W=h.shape;n,l,st,_=comps(ys&(1-m));big=np.zeros((H,W),np.uint8)
    for i in range(1,n):
        x,y,w,hh,a=st[i]
        if a>=300 and R[y:y+hh,x:x+w].any():
            c=l[y:y+hh,x:x+w]==i
            if (R[y:y+hh,x:x+w][c]).mean()<0.6:put(big,l,i,st)
    prot=cv2.dilate(big,K(9))
    panel=cv2.morphologyEx(red|cv2.dilate(m,K(25)),cv2.MORPH_CLOSE,K(15))
    redl=(((h<=9)|(h>=168))&(s>=130)&(v>=45)).astype(np.uint8)
    base=R&panel&(1-prot)
    if fg is None:mask=base&(redl|yl)
    else:
        sy=((h>=11)&(h<=40)&(s>=185)&(v>=150)).astype(np.uint8)
        mask=(base&(redl|yl)&(1-fg))|(base&sy)
    non=base&(1-mask)
    if fg is not None:non&=1-fg
    n,l,st,_=comps(non);bigno=np.zeros((H,W),np.uint8)
    for i in range(1,n):
        if st[i,4]<150:put(mask,l,i,st)
        else:put(bigno,l,i,st)
    mask&=1-(cv2.dilate(bigno,K(5))&(1-ys))
    src=red&(1-R)
    if fg is not None:src&=1-fg
    return mask,src
# ---------------- small logos ----------------
def cap_hull(h,s,v):
    H,W=h.shape;redc=(((h<=6)|(h>=171))&(s>=175)&(v>=90)).astype(np.uint8);n,l,st,ce=comps(redc);best=None
    for i in range(1,n):
        x,y,w,hh,a=st[i];edge=x+w>=W-2
        if not((3000<=a<=90000) or (edge and 500<=a<3000)):continue
        if w>430 or hh>320 or y<430:continue
        if not(0.2*H<=ce[i][1]<=0.5*H) or x+w<0.55*W:continue
        if best is None or a>st[best,4]:best=i
    if best is None:return None
    bx,by,bw,bh,ba=st[best];m=np.zeros((H,W),np.uint8)
    for i in range(1,n):
        x,y,w,hh,a=st[i]
        if a>=300 and w<=430 and hh<=320 and not(x>bx+bw+60 or x+w<bx-60 or y>by+bh+40 or y+hh<by-60):put(m,l,i,st)
    hm=np.zeros((H,W),np.uint8);cv2.fillConvexPoly(hm,cv2.convexHull(cv2.findNonZero(m)),1)
    return hm
def cap_cands(h,s,v,white=False):
    """thin bright warm (or white) strokes inside the cap outline, enclosed by red: the cap logo"""
    H,W=h.shape;S=np.zeros((H,W),np.uint8);L=np.zeros((H,W),np.uint8);hm=cap_hull(h,s,v)
    if hm is None:return S,L,0
    hd=cv2.dilate(hm,K(5))
    rf=(((h<=9)|(h>=168))&(s>=120)&(v>=50)).astype(np.uint8)
    kinds=[('y',((h>=10)&(h<=40)&(s>=110)&(v>=160)).astype(np.uint8),30,4000)]
    if white:kinds.append(('p',((s<=110)&(v>=170)).astype(np.uint8),150,8000))
    for kind,cm,amin,amax in kinds:
        n,l,st,ce=comps(cm&hd)
        for i in range(1,n):
            x,y,w,hh,a=st[i]
            if a<amin or a>amax:continue
            q,(a0,b0,a1,b1)=cc(l,i,st,8,H,W)
            if cv2.erode(q,K(17)).any():continue
            fr=ring(q,rf[b0:b1,a0:a1],6)
            if fr<0.45:continue
            L[b0:b1,a0:a1]|=q;qb=q.astype(bool)
            if fr>=0.8 or (kind=='y' and fr>=0.5 and 40<=a<=1500 and np.median(s[b0:b1,a0:a1][qb])>=170 and np.median(v[b0:b1,a0:a1][qb])>=180):S[b0:b1,a0:a1]|=q
    return S,L,1
def red_cands(h,s,v,zone,excl):
    H,W=h.shape;x0,y0,x1,y1=zone
    red=(((h<=8)|(h>=170))&(s>=150)&(v>=70)).astype(np.uint8)
    yel=((h>=7)&(h<=40)&(s>=165)&(v>=165)).astype(np.uint8)&(1-excl)
    S=np.zeros((H,W),np.uint8);L=np.zeros((H,W),np.uint8);n,l,st,_=comps(yel[y0:y1,x0:x1])
    for i in range(1,n):
        a=st[i,4]
        if a<10 or a>2500:continue
        q,(a0,b0,a1,b1)=cc(l,i,st,8,y1-y0,x1-x0);fr=ring(q,red[y0+b0:y0+b1,x0+a0:x0+a1],5)
        if fr>=0.6:L[y0+b0:y0+b1,x0+a0:x0+a1]|=q
        if fr>=0.75:S[y0+b0:y0+b1,x0+a0:x0+a1]|=q
    return S,L
def cup_cands(h,s,v,zone):
    H,W=h.shape;x0,y0,x1,y1=zone
    wh=((s<=110)&(v>=170)).astype(np.uint8)
    yel=((h>=9)&(h<=30)&(s>=140)&(v>=180)).astype(np.uint8)
    S=np.zeros((H,W),np.uint8);L=np.zeros((H,W),np.uint8);n,l,st,_=comps(yel[y0:y1,x0:x1])
    for i in range(1,n):
        a=st[i,4]
        if a<150 or a>6000:continue
        q,(a0,b0,a1,b1)=cc(l,i,st,12,y1-y0,x1-x0);sl=(slice(y0+b0,y0+b1),slice(x0+a0,x0+a1));qb=q.astype(bool)
        if not(14<=np.median(h[sl][qb])<=22 and np.median(s[sl][qb])>=185):continue
        fr=ring(q,wh[sl],8)
        if fr>=0.4:L[sl]|=q
        if fr>=0.55 and a>=800 and st[i,3]>=40:S[sl]|=q
    return S,L
def track(Ss,Ls,r=21,iters=3):
    T=len(Ss);F=[q.copy() for q in Ss]
    for it in range(iters):
        ch=False
        for order in(range(T),range(T-1,-1,-1)):
            for t in order:
                if not Ls[t].any():continue
                near=F[t].copy()
                if t>0:near|=F[t-1]
                if t<T-1:near|=F[t+1]
                if not near.any():continue
                near=cv2.dilate(near,K(r));n,l,st,_=comps(Ls[t])
                for i in range(1,n):
                    x,y,w,hh,a=st[i];c=l[y:y+hh,x:x+w]==i
                    if near[y:y+hh,x:x+w][c].any() and not F[t][y:y+hh,x:x+w][c].all():F[t][y:y+hh,x:x+w][c]=1;ch=True
        if not ch:break
    out=[]
    for t in range(T):
        nb=np.zeros_like(F[t])
        if t>0:nb|=F[t-1]
        if t<T-1:nb|=F[t+1]
        nb=cv2.dilate(nb,K(r));n,l,st,_=comps(F[t]);keep=np.zeros_like(F[t])
        for i in range(1,n):
            x,y,w,hh,a=st[i];c=l[y:y+hh,x:x+w]==i
            if nb[y:y+hh,x:x+w][c].any():keep[y:y+hh,x:x+w][c]=1
        out.append(keep)
    return out
def fill_red(f,blob,k=9):
    h,s,v=HSV(f)
    redl=(((h<=9)|(h>=168))&(s>=115)&(v>=50)).astype(np.uint8)
    d=cv2.dilate(blob,K(k));mask=blob|(d&redl);mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,K(3))&d
    src=(((h<=8)|(h>=170))&(s>=125)&(v>=60)).astype(np.uint8)
    return np.clip(hfill(f,mask,src),0,255).astype(np.uint8),mask
def fill_white(f,blob,k=9):
    h,s,v=HSV(f)
    al=(((s<=120)&(v>=150))|((h>=5)&(h<=40)&(v>=150))).astype(np.uint8)
    d=cv2.dilate(blob,K(k));mask=blob|(d&al);mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,K(3))&d
    src=((s<=110)&(v>=160)).astype(np.uint8)
    return np.clip(hfill(f,mask,src),0,255).astype(np.uint8),mask
CFG={'s2':{'table':(52,(300,960,1080,1500))},'s3a':{'table':(0,(300,960,1080,1500))},
 'F_A':{'table':(0,(0,960,1080,1916)),'white':True},'F_B':{},'F_T':{},
 'F_C':{'hug':{'t0':98,'ref':94,'fit':(64,106)}}}
def process(name,dbg=(),write=True,stage='AB'):
    if stage=='B':return stageB(name,None,None,dbg,write)
    cfg=CFG[name];F=rd(name+'.mp4');T=len(F);H,W=F[0].shape[:2];log=[];A=[];t00=time.time()
    hug=cfg.get('hug');t0=hug['t0'] if hug else 10**9
    OK=track_signs([sign_cands(*HSV(f))[0] for f in F])
    def sel(t,f):
        h,s,v=HSV(f);cs,(l,st),red,ys,yl=sign_cands(h,s,v);ids=[c['id'] for c in cs if c['bb'] in OK[t]]
        return h,s,v,l,st,ids,red,ys,yl
    if hug:
        ts=[];bbs=[]
        for t in range(hug['fit'][0],hug['fit'][1]+1):
            q=[b for b in OK[t] if b[2]-b[0]>120]
            if q:ts.append(t);bbs.append(q[0])
        bbs=np.array(bbs,float);co=[np.polyfit(ts,bbs[:,k],1) for k in range(4)]
        pred=lambda t:[float(np.polyval(co[k],t)) for k in range(4)]
        h,s,v,l,st,ids,red,ys,yl=sel(hug['ref'],F[hug['ref']]);RREF,MREF=sign_region(H,W,l,st,ids);REF=F[hug['ref']];br=pred(hug['ref'])
    for t,f in enumerate(F):
        rec={'t':t};const=None;fg=None
        if t>=t0:
            h,s,v=HSV(f);red,ys,yl=basic(h,s,v)
            bb=pred(t);sx=(bb[2]-bb[0])/(br[2]-br[0]);sy=(bb[3]-bb[1])/(br[3]-br[1])
            Ma=np.float32([[sx,0,bb[0]-sx*br[0]],[0,sy,bb[1]-sy*br[1]]])
            E=cv2.warpAffine(REF,Ma,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
            R=cv2.warpAffine(RREF,Ma,(W,H),flags=cv2.INTER_NEAREST);m=cv2.warpAffine(MREF,Ma,(W,H),flags=cv2.INTER_NEAREST)
            ys_,xs_=np.nonzero(R);x0,y0,x1,y1=max(4,xs_.min()-6),max(4,ys_.min()-6),min(W-4,xs_.max()+7),min(H-4,ys_.max()+7)
            fc=f[y0:y1,x0:x1].astype(np.int16);d=np.full(fc.shape[:2],255,np.int16)
            for dy in range(-3,4):
                for dx in range(-3,4):d=np.minimum(d,np.abs(fc-E[y0+dy:y1+dy,x0+dx:x1+dx].astype(np.int16)).max(2))
            fgc=cv2.morphologyEx((d>30).astype(np.uint8),cv2.MORPH_OPEN,K(5));n,l,st,_=comps(fgc)
            for i in range(1,n):
                if st[i,4]<80:fgc[l==i]=0
            fgc=cv2.dilate(cv2.morphologyEx(fgc,cv2.MORPH_CLOSE,K(9)),K(5))
            fg=np.zeros((H,W),np.uint8);fg[y0:y1,x0:x1]=fgc
            mask,src=sign_mask(h,s,v,R,m,red,ys,yl,fg);rec['sign']=[[round(q) for q in bb]];rec['fg']=int(fg.sum())
            if src.any():const=f[src>0].mean(0)
        else:
            h,s,v,l,st,ids,red,ys,yl=sel(t,f);rec['sign']=[[int(q) for q in (st[i,0],st[i,1],st[i,0]+st[i,2],st[i,1]+st[i,3])] for i in ids]
            if ids:R,m=sign_region(H,W,l,st,ids);mask,src=sign_mask(h,s,v,R,m,red,ys,yl)
            else:R=mask=src=np.zeros((H,W),np.uint8)
        g=np.clip(hfill(f,mask,src,const=const),0,255).astype(np.uint8) if mask.any() else f.copy()
        A.append(g);log.append(rec)
        if t in dbg:
            vis=f.copy()
            for mk,col in((R,(0,255,0)),(mask,(255,255,0)))+(((fg,(255,0,255)),) if fg is not None else ()):
                cn,_=cv2.findContours(mk,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE);cv2.drawContours(vis,cn,-1,col,1)
            cv2.imwrite(f'/tmp/dbgA_{name}_{t}.png',vis)
    del F
    print(name,'signs done',round(time.time()-t00,1),'s',flush=True)
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','24','-i','-','-c:v','ffv1','-pix_fmt','bgr0',f'pro/A_{name}.mkv'],stdin=subprocess.PIPE)
    for g in A:p.stdin.write(g.tobytes())
    p.stdin.close();p.wait();json.dump(log,open(f'pro/A_{name}.json','w'))
    return stageB(name,A,log,dbg,write)
def stageB(name,A,log,dbg=(),write=True):
    cfg=CFG[name];t00=time.time()
    if A is None:A=rd(f'pro/A_{name}.mkv');log=json.load(open(f'pro/A_{name}.json'))
    H,W=A[0].shape[:2]
    Sc=[];Lc=[];Sr=[];Lr=[];Sw=[];Lw=[];Z=np.zeros((H,W),np.uint8)
    for t,g in enumerate(A):
        h,s,v=HSV(g);a,b,nz=cap_cands(h,s,v,cfg.get('white',False));Sc.append(a);Lc.append(b);log[t]['capz']=nz
        sr=lr=sw=lw=Z
        if 'table' in cfg and t>=cfg['table'][0]:
            sr,lr=red_cands(h,s,v,cfg['table'][1],cv2.dilate(b,K(15)));sw,lw=cup_cands(h,s,v,cfg['table'][1])
        Sr.append(sr);Lr.append(lr);Sw.append(sw);Lw.append(lw)
    Fc=track(Sc,Lc);Fr=track(Sr,Lr,r=15);Fw=track(Sw,Lw)
    del Sr,Lr,Sw,Lw
    p=None
    if write:
        p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','24','-i','-','-i',name+'.mp4','-map','0:v','-map','1:a',
          '-c:v','libx264','-preset','medium','-crf','8','-pix_fmt','yuv420p','-c:a','copy',f'pro/{name}.mp4'],stdin=subprocess.PIPE)
    for t,g in enumerate(A):
        o=g
        if Fc[t].any():o,_=fill_red(o,Fc[t],9)
        if Fr[t].any():o,_=fill_red(o,Fr[t],7)
        if Fw[t].any():o,_=fill_white(o,Fw[t],9)
        log[t].update(cap=int(Fc[t].sum()),capS=int(Sc[t].sum()),sred=int(Fr[t].sum()),cup=int(Fw[t].sum()))
        if p:p.stdin.write(o.tobytes())
        if t in dbg:
            vis=g.copy()
            for mk,col in((Lc[t],(120,0,120)),(Fc[t],(255,0,255)),(Fr[t],(0,255,255)),(Fw[t],(255,128,0))):
                cn,_=cv2.findContours(mk,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE);cv2.drawContours(vis,cn,-1,col,2)
            cv2.imwrite(f'/tmp/dbgB_{name}_{t}.png',vis)
    if p:p.stdin.close();p.wait()
    print(name,'all done',round(time.time()-t00,1),'s',flush=True)
    json.dump(log,open(f'pro/{name}.json','w'))
if __name__=='__main__':
    for nm in sys.argv[1].split(','):process(nm,tuple(int(x) for x in sys.argv[2].split(',')) if len(sys.argv)>2 else ())
