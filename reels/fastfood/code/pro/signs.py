import sys;sys.path.insert(0,'pro')
from clean import K,rd,HSV,comps,cc,put,hfill
import cv2,numpy as np,json,subprocess,time
def basic(h,s,v):
    red=(((h<=8)|(h>=170))&(s>=170)&(v>=60)).astype(np.uint8)
    ys=((h>=10)&(h<=36)&(s>=165)&(v>=160)).astype(np.uint8)
    return red,ys
def sign_cands(h,s,v):
    H,W=h.shape;red,ys=basic(h,s,v);n,l,st,ce=comps(ys);out=[]
    for i in range(1,n):
        x,y,w,hh,a=st[i];edge=(x<=1 or x+w>=W-1)
        if a<(60 if edge else 300) or a>90000 or y+hh>0.31*H:continue
        c,(x0,y0,x1,y1)=cc(l,i,st,30,H,W);band=cv2.dilate(c,K(57))-cv2.dilate(c,K(27))
        fr=float((band&red[y0:y1,x0:x1]).sum())/max(1,int(band.sum()));ext=a/float(w*hh)
        if fr<0.4:continue
        strict=(not edge) and fr>=0.7 and a>=1500 and 0.3<=ext<=0.8 and hh>=0.9*w
        out.append({'bb':[int(x),int(y),int(x+w),int(y+hh)],'strict':bool(strict),'id':i})
    return out,(l,st),red,ys
def contain(c,q,m=10):
    iw=min(c[2],q[2]+m)-max(c[0],q[0]-m);ih=min(c[3],q[3]+m)-max(c[1],q[1]-m)
    if iw<=0 or ih<=0:return 0.0
    return iw*ih/float(max(1,(c[2]-c[0])*(c[3]-c[1])))
def track_signs(C):
    T=len(C);ACC=[[c['bb'] for c in C[t] if c['strict']] for t in range(T)]
    for it in range(80):
        ch=False
        for order in(range(T),range(T-1,-1,-1)):
            for t in order:
                near=(ACC[t-1] if t>0 else [])+(ACC[t+1] if t<T-1 else [])
                for c in C[t]:
                    if c['bb'] in ACC[t]:continue
                    if any(contain(c['bb'],q)>=0.6 for q in near):ACC[t].append(c['bb']);ch=True
        if not ch:break
    OK=[]
    for t in range(T):
        nb=(ACC[t-1] if t>0 else [])+(ACC[t+1] if t<T-1 else [])
        OK.append([b for b in ACC[t] if any(contain(b,q)>=0.3 or contain(q,b)>=0.3 for q in nb)])
    return OK
def sign_geom(H,W,l,st,ids):
    m=np.zeros((H,W),np.uint8)
    for i in ids:put(m,l,i,st)
    n,gl,gst,_=comps(cv2.dilate(m,K(41)));R=np.zeros((H,W),np.uint8);inner=np.zeros((H,W),np.uint8)
    for g in range(1,n):
        pts=cv2.findNonZero(m&(gl==g).astype(np.uint8))
        if pts is None:continue
        hm=np.zeros((H,W),np.uint8);cv2.fillConvexPoly(hm,cv2.convexHull(pts),1)
        x,y,w,hh=cv2.boundingRect(pts);mg=int(np.clip(0.09*max(w,hh),8,22))
        Rg=cv2.dilate(hm,K(2*mg+1));R|=Rg|shift(Rg,5,14);inner|=cv2.dilate(hm,K(9))
    return R,inner,m
def sign_mask(h,s,v,R,inner,m,ys):
    H,W=h.shape
    redl=(((h<=10)|(h>=166))&(s>=110)&(v>=30)).astype(np.uint8)
    signc=((h>=8)&(h<=42)&(s>=110)&(v>=35)).astype(np.uint8)
    okc=redl|signc
    n,l,st,_=comps(ys&(1-m));prot=np.zeros((H,W),np.uint8)
    for i in range(1,n):
        x,y,w,hh,a=st[i]
        if a>=300 and R[y:y+hh,x:x+w].any():
            c=l[y:y+hh,x:x+w]==i
            if inner[y:y+hh,x:x+w][c].mean()<0.5:put(prot,l,i,st)
    if prot.any():prot=cv2.dilate(prot,K(9))
    non=inner&(1-okc);thick=cv2.morphologyEx(non,cv2.MORPH_OPEN,K(9))
    fgo=cv2.dilate(thick,K(7)) if thick.any() else thick
    mask=((R&okc)|inner)&(1-fgo)&(1-prot)
    redsrc=(((h<=13)|(h>=166))&(s>=130)&(v>=30)&(v<=245)).astype(np.uint8)
    src=cv2.erode(redsrc,K(5))&(1-R)&(1-fgo)
    glow=cv2.morphologyEx(((v>=230)&(s<=95)).astype(np.uint8),cv2.MORPH_OPEN,K(3));n,l,st,_=comps(glow);gl=np.zeros((H,W),np.uint8);Rd=cv2.dilate(R,K(9));md=cv2.dilate(m,K(5))
    for i in range(1,n):
        x,y,w,hh,a=st[i]
        if a>=150 and Rd[y:y+hh,x:x+w].any():
            c=l[y:y+hh,x:x+w]==i
            if md[y:y+hh,x:x+w][c].mean()<0.3:put(gl,l,i,st)
    dk=((v<=70)).astype(np.uint8);n,l,st,_=comps(cv2.morphologyEx(dk,cv2.MORPH_OPEN,K(5)));Rd2=cv2.dilate(R,K(41))
    for i in range(1,n):
        x,y,w,hh,a=st[i]
        if a>=2500 and w<=320 and hh<=260 and Rd2[y:y+hh,x:x+w].any():
            hm=np.zeros((H,W),np.uint8);cv2.fillConvexPoly(hm,cv2.convexHull(cv2.findNonZero((l==i).astype(np.uint8))),1)
            hm=cv2.dilate(hm,np.ones((19,25),np.uint8),anchor=(12,2));gl|=hm
    if gl.any():mask&=1-cv2.dilate(gl,K(3));src&=1-cv2.dilate(gl,K(11))
    return mask,src,gl
def shift(a,dx,dy):
    o=np.zeros_like(a);h,w=a.shape[:2]
    xs0,xs1=max(0,-dx),min(w,w-dx);ys0,ys1=max(0,-dy),min(h,h-dy)
    o[ys0+dy:ys1+dy,xs0+dx:xs1+dx]=a[ys0:ys1,xs0:xs1];return o
def sstep(x,a,b):
    t=np.clip((x-a)/float(b-a),0,1);return t*t*(3-2*t)
CFGA={'F_C':{'ref':94}}
def process(name,dbg=()):
    F=rd(name+'.mp4');T=len(F);H,W=F[0].shape[:2];t00=time.time()
    OK=track_signs([sign_cands(*HSV(f))[0] for f in F])
    ref=CFGA.get(name,{}).get('ref');t0=ref+1 if ref is not None else T
    log=[];A=[None]*T;geo={}
    for t in range(t0):
        f=F[t];h,s,v=HSV(f);cs,(l,st),red,ys=sign_cands(h,s,v);ids=[c['id'] for c in cs if c['bb'] in OK[t]]
        rec={'t':t,'sign':[c['bb'] for c in cs if c['bb'] in OK[t]],'mode':'fill'}
        if ids:
            R,inner,m=sign_geom(H,W,l,st,ids);mask,src,gl=sign_mask(h,s,v,R,inner,m,ys)
            near=src&cv2.dilate(R,K(61));const=np.median(f[near>0],axis=0) if near.any() else None
            g=hfill(f,mask,src,const=const)
            if gl.any():
                al=cv2.GaussianBlur(cv2.dilate(gl,K(5)).astype(np.float32),(0,0),1.5)[...,None];g=g*(1-al)+f.astype(np.float32)*al
            A[t]=np.clip(g,0,255).astype(np.uint8);rec['mask']=int(mask.sum())
            if t==ref:geo=dict(m=m)
            if t in dbg:
                vis=f.copy()
                for mk,col in((R,(0,255,0)),(mask,(255,255,0)),(src&cv2.dilate(R,K(9)),(255,0,255))):
                    cn,_=cv2.findContours(mk,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE);cv2.drawContours(vis,cn,-1,col,1)
                cv2.imwrite(f'/tmp/dbgA_{name}_{t}.png',vis)
        else:A[t]=f.copy()
        log.append(rec)
    if ref is not None:
        ts=[];bbs=[]
        for t in range(max(0,ref-16),min(T,ref+18)):
            q=[b for b in OK[t] if b[2]-b[0]>120]
            if q:ts.append(t);bbs.append(q[0])
        bbs=np.array(bbs,float);co=[np.polyfit(ts,bbs[:,k],1) for k in range(4)]
        pred=lambda t:[float(np.polyval(co[k],t)) for k in range(4)]
        REF=F[ref];REFc=A[ref];Mref=geo['m'];br=[b for b in OK[ref] if b[2]-b[0]>120][0]
        CH=(np.abs(REF.astype(np.int16)-REFc.astype(np.int16)).max(2)>10).astype(np.uint8)
        hh_,ss_,vv_=HSV(REF);mm=Mref>0;print(name,'sign face HSV median',int(np.median(hh_[mm])),int(np.median(ss_[mm])),int(np.median(vv_[mm])),flush=True)
        prev=None;cxr,cyr=(br[0]+br[2])/2.0,(br[1]+br[3])/2.0
        for t in range(t0,T):
            f=F[t];bb=pred(t);sx0=(bb[2]-bb[0])/float(br[2]-br[0]);sy0=(bb[3]-bb[1])/float(br[3]-br[1]);cx,cy=(bb[0]+bb[2])/2.0,(bb[1]+bb[3])/2.0
            def mk(ds,dx=0,dy=0):
                sx,sy=sx0*(1+ds),sy0*(1+ds);return np.float32([[sx,0,cx-sx*cxr+dx],[0,sy,cy-sy*cyr+dy]])
            h,s,v=HSV(f);red,ys=basic(h,s,v)
            if prev is None:cand=[(float(ds),range(-8,9),range(-8,9)) for ds in np.arange(-0.03,0.0301,0.005)]
            else:cand=[(prev[0]+dd,range(prev[1]-2,prev[1]+3),range(prev[2]-2,prev[2]+3)) for dd in (-0.004,-0.002,0.0,0.002,0.004)]
            best=(-1e18,0.0,0,0);vis_px=0
            for ds,rx,ry in cand:
                Mw=cv2.warpAffine(Mref,mk(ds),(W,H),flags=cv2.INTER_NEAREST)
                yy,xx=np.nonzero(Mw)
                if len(yy)==0:continue
                x0=max(0,xx.min()-48);x1=min(W,xx.max()+49);y0=max(0,yy.min()-48);y1=min(H,yy.max()+49)
                SY=ys[y0:y1,x0:x1].astype(np.float32);RD=red[y0:y1,x0:x1].astype(np.float32);Mc=Mw[y0:y1,x0:x1]
                Min=cv2.dilate(Mc,K(3)).astype(np.float32);Mout=((1-cv2.dilate(Mc,K(7)))&cv2.dilate(Mc,K(61))).astype(np.float32);Mco=cv2.erode(Mc,K(5)).astype(np.float32)
                vis_px=max(vis_px,float((SY*cv2.dilate(Mc,K(25))).sum()))
                for dy in ry:
                    for dx in rx:
                        sc=float((SY*shift(Min,dx,dy)).sum()-3*(SY*shift(Mout,dx,dy)).sum()-1.5*(RD*shift(Mco,dx,dy)).sum())
                        if prev is not None:sc-=1.0*((dx-prev[1])**2+(dy-prev[2])**2)+2e5*(ds-prev[0])**2
                        if sc>best[0]:best=(sc,ds,dx,dy)
            if prev is not None and vis_px<400:best=(0,)+prev
            _,ds,dx,dy=best;prev=(ds,dx,dy);Ma=mk(ds,dx,dy);Mw=cv2.warpAffine(Mref,Ma,(W,H),flags=cv2.INTER_NEAREST)
            RW=cv2.warpAffine(REF,Ma,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
            PL=cv2.warpAffine(REFc,Ma,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
            Z=cv2.dilate(cv2.warpAffine(CH,Ma,(W,H),flags=cv2.INTER_NEAREST),K(31))
            yy,xx=np.nonzero(Z);x0=max(3,xx.min()-8);x1=min(W-3,xx.max()+9);y0=max(3,yy.min()-8);y1=min(H-3,yy.max()+9)
            fc=f[y0:y1,x0:x1].astype(np.int16);d=np.full(fc.shape[:2],999,np.int16)
            for ddy in range(-2,3):
                for ddx in range(-2,3):d=np.minimum(d,np.abs(fc-RW[y0+ddy:y1+ddy,x0+ddx:x1+ddx].astype(np.int16)).max(2))
            hc=h[y0:y1,x0:x1].astype(np.float32);sc_=s[y0:y1,x0:x1].astype(np.float32);vc=v[y0:y1,x0:x1].astype(np.float32)
            y1m=sstep(hc,15,19)*(hc<=42)*sstep(sc_,130,175)*sstep(vc,50,95)
            Md=cv2.dilate(Mw,K(15))[y0:y1,x0:x1].astype(np.float32);y1m=np.maximum(y1m,Md*sstep(hc,15,17)*(hc<=42)*sstep(sc_,110,140)*sstep(vc,90,120))
            beta=np.maximum(y1m,1-sstep(d.astype(np.float32),12,26))
            g=(beta*cv2.GaussianBlur(Z[y0:y1,x0:x1].astype(np.float32),(0,0),1.2))[...,None]
            o=f.copy();o[y0:y1,x0:x1]=np.clip(f[y0:y1,x0:x1]*(1-g)+PL[y0:y1,x0:x1]*g,0,255).astype(np.uint8)
            A[t]=o;log.append({'t':t,'sign':[[round(q) for q in bb]],'mode':'plate','shift':[round(float(ds),4),int(dx),int(dy)],'vis':int(vis_px)})
            if t in dbg:
                vis=f.copy();cn,_=cv2.findContours(Z,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE);cv2.drawContours(vis,cn,-1,(0,255,0),1)
                cn,_=cv2.findContours(Mw,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE);cv2.drawContours(vis,cn,-1,(255,0,255),1)
                cv2.imwrite(f'/tmp/dbgA_{name}_{t}.png',vis)
    del F
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','24','-i','-','-c:v','ffv1','-pix_fmt','bgr0',f'pro/A_{name}.mkv'],stdin=subprocess.PIPE)
    for g in A:p.stdin.write(g.tobytes())
    p.stdin.close();p.wait();json.dump(log,open(f'pro/A_{name}.json','w'))
    print(name,'signs done',round(time.time()-t00,1),'s',flush=True)
if __name__=='__main__':
    for nm in sys.argv[1].split(','):process(nm,tuple(int(x) for x in sys.argv[2].split(',')) if len(sys.argv)>2 else ())
