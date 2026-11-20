import sys;sys.path.insert(0,'pro')
from clean import K,rd,HSV,comps,cc,put,hfill
from signs import shift,sstep
import cv2,numpy as np,json,subprocess,time
def LAB(f):
    L=cv2.cvtColor(f,cv2.COLOR_BGR2LAB).astype(np.int16);return L[...,0],L[...,1]-128,L[...,2]-128
def fillholes(m):
    p=np.pad(m,1);inv=(1-p).astype(np.uint8);msk=np.zeros((p.shape[0]+2,p.shape[1]+2),np.uint8);cv2.floodFill(inv,msk,(0,0),2)
    return ((inv==1)|(p==1)).astype(np.uint8)[1:-1,1:-1]
SEED={'s2':(84,950,640),'s3a':(0,930,640),'F_A':(50,950,680),'F_B':(0,820,740),'F_T':(0,825,740),'F_C':(0,825,745)}
def cap_track(F,name):
    """follow the red cap from a seed frame; returns per-frame cap mask bbox or None"""
    T=len(F);H,W=F[0].shape[:2];t0,sx,sy=SEED[name];out=[None]*T
    def comp_at(f,prevbb,prevarea):
        L,a,b=LAB(f);C=((a>=45)&(L>=40)).astype(np.uint8);n,l,st,ce=comps(C);best=None
        for i in range(1,n):
            x,y,w,hh,ar=st[i]
            if ar<400:continue
            if prevbb is None:
                if ar<3000 or not(x-30<=sx<=x+w+30 and y-30<=sy<=y+hh+30) or w>470 or hh>360:continue
                sc=ar
            else:
                px0,py0,px1,py1=prevbb;iw=min(x+w,px1)-max(x,px0);ih=min(y+hh,py1)-max(y,py0)
                if iw<=0 or ih<=0:continue
                edge=(x+w>=W-2) or (px1>=W-2)
                if not edge and not(0.5<=ar/float(prevarea)<=2.0):continue
                if w>470 or hh>360:continue
                sc=iw*ih
            if best is None or sc>best[0]:best=(sc,i)
        if best is None:return None
        i=best[1];x,y,w,hh,ar=st[i];return (int(x),int(y),int(x+w),int(y+hh)),int(ar)
    r=comp_at(F[t0],None,None)
    if r is None:return out
    out[t0]=r
    for rng in(range(t0+1,T),range(t0-1,-1,-1)):
        prev=out[t0]
        for t in rng:
            r=comp_at(F[t],prev[0],prev[1])
            if r is None:break
            out[t]=r;prev=r
    return out
_CL={}
def cap_logo(f,capbb,key=None,pad=60):
    """cap fabric mask, logo core and the thin non-red strokes that may be painted, on a padded crop"""
    if key is not None and key in _CL:return _CL[key]
    H,W=f.shape[:2];x0,y0,x1,y1=capbb;X0,Y0,X1,Y1=max(0,x0-pad),max(0,y0-pad),min(W,x1+pad),min(H,y1+pad)
    crop=f[Y0:Y1,X0:X1];L,a,b=LAB(crop);C=((a>=45)&(L>=40)).astype(np.uint8)
    n,l,st,_=comps(C);keep=np.zeros_like(C);bx0,by0,bx1,by1=x0-X0,y0-Y0,x1-X0,y1-Y0
    for i in range(1,n):
        x,y,w,hh,ar=st[i]
        if ar>=200 and not(x>bx1 or x+w<bx0 or y>by1 or y+hh<by0):put(keep,l,i,st)
    C=keep
    Ssm=cv2.morphologyEx(C,cv2.MORPH_CLOSE,K(45))|C          # closes the notch a logo cuts into the outline
    Cfill=fillholes(cv2.morphologyEx(C,cv2.MORPH_CLOSE,K(5)))
    Lf=float(np.median(L[C>0])) if C.any() else 120.0
    yel=(b>=38)&(a<40)&(L>=Lf+18);whi=(np.abs(a)<=18)&(b<=30)&(L>=max(190,Lf+60))
    loose=(L>=Lf+10)&(a<45)&((b>=30)|(L>=185))
    LC=(loose&(C==0)).astype(np.uint8);thick=cv2.morphologyEx(LC,cv2.MORPH_OPEN,K(21))
    thd=cv2.dilate(thick,K(7)) if thick.any() else thick
    Cf=C.astype(np.float32);den=cv2.GaussianBlur(Cf,(0,0),12)+1e-3
    aloc=cv2.GaussianBlur(a.astype(np.float32)*Cf,(0,0),12)/den;bloc=cv2.GaussianBlur(b.astype(np.float32)*Cf,(0,0),12)/den;Lloc=cv2.GaussianBlur(L.astype(np.float32)*Cf,(0,0),12)/den
    rel=((aloc-a)>=10)&((b-bloc)>=4)&(L>=Lloc-5)&(den>0.15)
    core=((Ssm|Cfill)&(1-thd)&((((1-C)>0)&(yel|whi))|rel)).astype(np.uint8)
    ext=((C==0)&(Ssm>0)&(thick==0)).astype(np.uint8)
    anc=None
    if C.any():
        xs=np.nonzero(C.any(0))[0];xm=int(xs.min());ys=np.nonzero(C[:,xm:xm+3].any(1))[0];anc=(X0+xm,Y0+float(ys.mean()))
    d=dict(C=C,Cfill=Cfill,core=core,ext=ext,org=(X0,Y0),Lf=Lf,anc=anc,sel=None)
    if key is not None:_CL[key]=d
    return d
def rrect(H,W,bb,m,rad=0.3):
    x0,y0,x1,y1=[int(round(q)) for q in (bb[0]-m,bb[1]-m,bb[2]+m,bb[3]+m)];o=np.zeros((H,W),np.uint8)
    r=int(max(2,rad*min(x1-x0,y1-y0)));cv2.rectangle(o,(x0+r,y0),(x1-r,y1),1,-1);cv2.rectangle(o,(x0,y0+r),(x1,y1-r),1,-1)
    for cx,cy in((x0+r,y0+r),(x1-r,y0+r),(x0+r,y1-r),(x1-r,y1-r)):cv2.circle(o,(cx,cy),r,1,-1)
    return o
def logo_track(F,caps,t0):
    """per-frame logo bbox: the bright non-red cluster on the crown, followed outwards from the seed frame"""
    T=len(F);raw=[None]*T;info=[None]*T
    def pick(t,prevc):
        d=cap_logo(F[t],caps[t][0],key=t);X0,Y0=d['org'];core=d['core']
        if core.sum()<20:return None
        n,l,st,ce=comps(cv2.dilate(core,K(13)));best=None;cb=caps[t][0]
        for i in range(1,n):
            cm=(l==i)&(core>0);ar=int(cm.sum())
            if ar<20:continue
            ys,xs=np.nonzero(cm);bb=(X0+xs.min(),Y0+ys.min(),X0+xs.max()+1,Y0+ys.max()+1)
            if (bb[1]+bb[3])/2.0>cb[1]+0.72*(cb[3]-cb[1]):continue
            if bb[2]-bb[0]>150 or bb[3]-bb[1]>150:continue
            if prevc is None:sc=ar
            else:
                dist=np.hypot((bb[0]+bb[2])/2.0-prevc[0],(bb[1]+bb[3])/2.0-prevc[1])
                if dist>70:continue
                sc=ar-4.0*dist
            if best is None or sc>best[0]:best=(sc,bb,ar,cm.astype(np.uint8))
        if best is not None:d['sel']=best[3]
        return best
    if caps[t0] is None:return raw,info
    b0=pick(t0,None)
    if b0 is None:return raw,info
    raw[t0]=[int(q) for q in b0[1]];info[t0]=b0[2];c0=((b0[1][0]+b0[1][2])/2.0,(b0[1][1]+b0[1][3])/2.0)
    for rng in(range(t0+1,T),range(t0-1,-1,-1)):
        prevc=c0;miss=0
        for t in rng:
            if caps[t] is None:break
            b=pick(t,prevc)
            if b is None:
                miss+=1
                if miss>12:break
                continue
            miss=0;raw[t]=[int(q) for q in b[1]];info[t]=b[2];prevc=((b[1][0]+b[1][2])/2.0,(b[1][1]+b[1][3])/2.0)
    return raw,info
def clean_track(raw,ancs,T,maxgap=22,ext=14):
    """logo boxes relative to the cap's brim tip: reject outliers, interpolate gaps, extend a little at the ends"""
    rel=[None]*T
    for t in range(T):
        if raw[t] is not None and ancs[t] is not None:rel[t]=np.array(raw[t],float)-np.array([ancs[t][0],ancs[t][1]]*2,float)
    for t in range(T):
        if rel[t] is None:continue
        nb=[rel[u] for u in range(max(0,t-3),min(T,t+4)) if u!=t and rel[u] is not None]
        if len(nb)>=2:
            med=np.median(np.array(nb),axis=0)
            if np.hypot(*(((rel[t][:2]+rel[t][2:])-(med[:2]+med[2:]))/2))>25:rel[t]=None
    out=list(rel);idx=[t for t in range(T) if rel[t] is not None]
    for a,b in zip(idx[:-1],idx[1:]):
        if 1<b-a<=maxgap:
            for t in range(a+1,b):
                w=(t-a)/float(b-a);out[t]=rel[a]*(1-w)+rel[b]*w
    if idx:
        for t in range(idx[0]-1,max(-1,idx[0]-1-ext),-1):
            if ancs[t] is None:break
            out[t]=rel[idx[0]]
        for t in range(idx[-1]+1,min(T,idx[-1]+1+ext)):
            if ancs[t] is None:break
            out[t]=rel[idx[-1]]
    res=[None]*T;kind=['']*T
    for t in range(T):
        if out[t] is not None and ancs[t] is not None:
            res[t]=out[t]+np.array([ancs[t][0],ancs[t][1]]*2,float);kind[t]='d' if rel[t] is not None else 'i'
    return res,kind

def ring(c,test,r):
    rg=cv2.dilate(c,K(2*r+1))-c;return float((rg&test).sum())/max(1,int(rg.sum()))
def table_cands(crop):
    """logos on red fries cartons and on white cups inside the table zone"""
    h,w=crop.shape[:2];L,a,b=LAB(crop)
    C=((a>=45)&(L>=40)).astype(np.uint8);S=fillholes(cv2.morphologyEx(C,cv2.MORPH_CLOSE,K(9)))
    yel=((b>=38)&(a<=40)&(L>=140)).astype(np.uint8);Cd=cv2.dilate(C,K(3))
    Sr=np.zeros((h,w),np.uint8);Lr=np.zeros((h,w),np.uint8);n,l,st,_=comps(S&(1-C)&yel)
    for i in range(1,n):
        x,y,ww,hh,ar=st[i]
        if ar<30 or ar>2500 or ww>80 or hh>80:continue
        q,(a0,b0,a1,b1)=cc(l,i,st,8,h,w);fr=ring(q,Cd[b0:b1,a0:a1],5)
        if fr>=0.6:Lr[b0:b1,a0:a1]|=q
        if fr>=0.8:Sr[b0:b1,a0:a1]|=q
    wh=((L>=150)&(np.abs(a)<=16)&(b<=38)).astype(np.uint8)
    yc=((b>=45)&(a<=38)&(a>=-10)&(L>=150)).astype(np.uint8)
    Sw=np.zeros((h,w),np.uint8);Lw=np.zeros((h,w),np.uint8);n,l,st,_=comps(yc)
    for i in range(1,n):
        x,y,ww,hh,ar=st[i]
        if ar<150 or ar>7000:continue
        q,(a0,b0,a1,b1)=cc(l,i,st,12,h,w);fr=ring(q,wh[b0:b1,a0:a1],8)
        if fr>=0.4:Lw[b0:b1,a0:a1]|=q
        if fr>=0.55 and ar>=700 and hh>=40:Sw[b0:b1,a0:a1]|=q
    return Sr,Lr,Sw,Lw
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
    res=[]
    for t in range(T):                       # extend with the neighbours' masks right next to this frame's mask
        m=out[t]
        if m.any():
            nb=np.zeros_like(m)
            if t>0:nb|=out[t-1]
            if t<T-1:nb|=out[t+1]
            m=m|(cv2.dilate(m,K(7))&nb)
        res.append(m)
    return res
TABLE={'s2':(52,(300,960,1080,1500)),'s3a':(0,(300,960,1080,1500)),'F_A':(0,(0,960,1080,1916))}
HUG={'F_C':(96,(300,0,1080,960))}
def process(name,dbg=(),write=True):
    t00=time.time();A=rd(f'pro/A_{name}.mkv');T=len(A);H,W=A[0].shape[:2];log=[{'t':t} for t in range(T)]
    _CL.clear();caps=cap_track(A,name);raw,info=logo_track(A,caps,SEED[name][0])
    ancs=[None]*T
    for t in range(T):
        if caps[t] is not None:ancs[t]=cap_logo(A[t],caps[t][0],key=t)['anc']
    trk,kind=clean_track(raw,ancs,T)
    for t in range(T):
        log[t]['cap']=caps[t][0] if caps[t] else None;log[t]['raw']=raw[t];log[t]['area']=info[t];log[t]['kind']=kind[t]
        log[t]['logo']=None if trk[t] is None else [round(float(q),1) for q in trk[t]]
    out=[g for g in A]
    relb=[None]*T
    for t in range(T):
        if trk[t] is not None and ancs[t] is not None:relb[t]=trk[t]-np.array([ancs[t][0],ancs[t][1]]*2,float)
    for t in range(T):
        if relb[t] is None or caps[t] is None:continue
        bbs=[relb[u] for u in range(t-2,t+3) if 0<=u<T and relb[u] is not None]
        ax,ay=ancs[t];bb=[min(b[0] for b in bbs)+ax,min(b[1] for b in bbs)+ay,max(b[2] for b in bbs)+ax,max(b[3] for b in bbs)+ay]
        g=out[t];d=cap_logo(g,caps[t][0],key=t);X0,Y0=d['org'];C=d['C'];Cfill=d['Cfill'];hh,ww=C.shape
        R=rrect(H,W,bb,11 if kind[t]=='d' else 22)[Y0:Y0+hh,X0:X0+ww]
        mask=R&(Cfill|d['ext'])
        if not mask.any():continue
        crop=g[Y0:Y0+hh,X0:X0+ww];src=cv2.erode(C,K(3))&(1-mask)
        const=np.median(crop[C>0],axis=0) if C.any() else None
        o=np.clip(hfill(crop,mask,src,const=const),0,255).astype(np.uint8)
        outside=1-(Cfill|mask);band=cv2.dilate(mask,K(3))&cv2.dilate(outside,K(3))
        if band.any():
            bl=cv2.GaussianBlur(o,(0,0),0.8);o[band>0]=bl[band>0]
        g2=g.copy();g2[Y0:Y0+hh,X0:X0+ww]=o;out[t]=g2;log[t]['capfill']=int(mask.sum());log[t]['box']=[round(float(q)) for q in bb]
        if t in dbg:
            vis=A[t].copy();cn,_=cv2.findContours(mask,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
            for c in cn:c+=np.array([[X0,Y0]])
            cv2.drawContours(vis,cn,-1,(255,0,255),1);cv2.imwrite(f'/tmp/dbgC_{name}_{t}.png',vis)
    if name in TABLE:
        ts,(x0,y0,x1,y1)=TABLE[name];idx=list(range(ts,T));Sr=[];Lr=[];Sw=[];Lw=[]
        for t in idx:
            a,b,c,d=table_cands(out[t][y0:y1,x0:x1]);Sr.append(a);Lr.append(b);Sw.append(c);Lw.append(d)
        Fr=track(Sr,Lr,r=15);Fw=track(Sw,Lw);del Sr,Lr,Sw,Lw
        for k,t in enumerate(idx):
            crop=out[t][y0:y1,x0:x1];o=crop;L,a,b=LAB(crop)
            if Fr[k].any():
                C=((a>=45)&(L>=40)).astype(np.uint8)
                mask=cv2.dilate(Fr[k],K(7))&(cv2.dilate(C,K(3))|((b>=30)&(L>=120)).astype(np.uint8))
                o=np.clip(hfill(o,mask,cv2.erode(C,K(3))&(1-mask),const=np.median(crop[C>0],axis=0) if C.any() else None),0,255).astype(np.uint8)
            if Fw[k].any():
                wh=((L>=150)&(np.abs(a)<=16)&(b<=38)).astype(np.uint8)
                mask=cv2.dilate(Fw[k],K(9))&(wh|((b>=22)&(L>=120)&(a<=40)).astype(np.uint8))
                o=np.clip(hfill(o,mask,wh&(1-mask),const=np.median(crop[wh>0],axis=0) if wh.any() else None),0,255).astype(np.uint8)
            if o is not crop:
                g2=out[t].copy();g2[y0:y1,x0:x1]=o;out[t]=g2
            log[t]['fries']=int(Fr[k].sum());log[t]['cups']=int(Fw[k].sum())
    if name in HUG:
        ts,(x0,y0,x1,y1)=HUG[name];idx=list(range(ts,T));Sr=[];Lr=[]
        for t in idx:
            crop=out[t][y0:y1,x0:x1];L,a,b=LAB(crop);C=((a>=45)&(L>=40)).astype(np.uint8);Cd=cv2.dilate(C,K(3))
            yel=((b>=30)&(a<=42)&(L>=120)).astype(np.uint8);hh_,ww_=C.shape;S1=np.zeros_like(C);L1=np.zeros_like(C);n,l,st,_=comps(yel&(1-C))
            for i in range(1,n):
                x,y,w,h2,ar=st[i]
                if ar<8 or ar>3000 or w>90 or h2>140:continue
                q,(a0,b0,a1,b1)=cc(l,i,st,8,hh_,ww_);fr=ring(q,Cd[b0:b1,a0:a1],5)
                thin=h2>=3*w and w<=8
                if fr>=(0.3 if thin else 0.5):L1[b0:b1,a0:a1]|=q
                if fr>=(0.4 if thin else 0.7):S1[b0:b1,a0:a1]|=q
            Sr.append(S1);Lr.append(L1)
        Fr=track(Sr,Lr,r=15)
        for k,t in enumerate(idx):
            if not Fr[k].any():continue
            crop=out[t][y0:y1,x0:x1];L,a,b=LAB(crop);C=((a>=45)&(L>=40)).astype(np.uint8)
            mask=cv2.dilate(Fr[k],K(7))&(cv2.dilate(C,K(3))|((b>=24)&(L>=100)).astype(np.uint8))
            o=np.clip(hfill(crop,mask,cv2.erode(C,K(3))&(1-mask),const=np.median(crop[C>0],axis=0) if C.any() else None),0,255).astype(np.uint8)
            g2=out[t].copy();g2[y0:y1,x0:x1]=o;out[t]=g2;log[t]['hug']=int(mask.sum())
    json.dump(log,open(f'pro/B_{name}.json','w'))
    if write:
        p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','24','-i','-','-c:v','ffv1','-pix_fmt','bgr0',f'pro/B_{name}.mkv'],stdin=subprocess.PIPE)
        for o in out:p.stdin.write(o.tobytes())
        p.stdin.close();p.wait()
    print(name,'stage B done',round(time.time()-t00,1),'s',flush=True)
    return out
if __name__=='__main__':
    for nm in sys.argv[1].split(','):process(nm,tuple(int(x) for x in sys.argv[2].split(',')) if len(sys.argv)>2 else ())
