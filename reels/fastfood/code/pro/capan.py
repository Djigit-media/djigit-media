import sys;sys.path.insert(0,'pro')
from clean import K,rd,HSV,comps,cc,put
import cv2,numpy as np
def capcomp(h,s,v):
    H,W=h.shape;cr=(((h<=9)|(h>=168))&(s>=110)&(v>=60)).astype(np.uint8);cr[:430]=0
    n,l,st,ce=comps(cr);best=None
    for i in range(1,n):
        x,y,w,hh,a=st[i];edge=x+w>=W-2
        if not((3000<=a<=120000) or (edge and 400<=a<3000)):continue
        if w>460 or hh>340:continue
        if not(0.22*H<=ce[i][1]<=0.5*H) or x+w<0.5*W:continue
        if best is None or a>st[best,4]:best=i
    if best is None:return None,cr
    c=np.zeros((H,W),np.uint8);put(c,l,best,st);return c,cr
if __name__=='__main__':
    sel={'s2':[68,72,80,96],'s3a':[0,40,64,80],'F_A':[22,30,44,66],'F_B':[0,60],'F_T':[40,90],'F_C':[6,30,48,57,62,78]}
    tiles=[]
    for n,ts in sel.items():
        F=rd(n+'.mp4');H,W=F[0].shape[:2]
        for t in ts:
            f=F[t];h,s,v=HSV(f);c,cr=capcomp(h,s,v)
            if c is None:print(n,t,'NO CAP');continue
            lab=cv2.cvtColor(f,cv2.COLOR_BGR2LAB).astype(np.int16);Lc,ac,bc=lab[...,0],lab[...,1]-128,lab[...,2]-128
            cb=c.astype(bool);x,y,w,hh=cv2.boundingRect(cv2.findNonZero(c))
            closed=cv2.morphologyEx(c,cv2.MORPH_CLOSE,K(25));hole=(closed&(1-c)).astype(bool)
            print(n,t,'cap bb',(x,y,x+w,y+hh),'area',int(cb.sum()),'| fabric L',np.percentile(Lc[cb],[5,50,95]).astype(int),'a',np.percentile(ac[cb],[5,50,95]).astype(int),'b',np.percentile(bc[cb],[5,50,95]).astype(int),'S',np.percentile(s[cb],[5,50]).astype(int))
            if hole.sum()>20:
                br=hole&(Lc>=np.percentile(Lc[cb],50)-15)
                print('      holes px',int(hole.sum()),'bright',int(br.sum()),'| L',np.percentile(Lc[hole],[10,50,90]).astype(int),'a',np.percentile(ac[hole],[10,50,90]).astype(int),'b',np.percentile(bc[hole],[10,50,90]).astype(int),'H',np.percentile(h[hole],[10,50,90]).astype(int),'S',np.percentile(s[hole],[10,50,90]).astype(int),'V',np.percentile(v[hole],[10,50,90]).astype(int))
            x0=max(0,min(x-10,W-280));y0=max(0,y-20);crop=f[y0:y0+200,x0:x0+280]
            am=np.clip((ac[y0:y0+200,x0:x0+280]+20)*3,0,255).astype(np.uint8)
            t1=cv2.resize(crop,(560,400),interpolation=cv2.INTER_CUBIC);t2=cv2.cvtColor(cv2.resize(am,(560,400),interpolation=cv2.INTER_NEAREST),cv2.COLOR_GRAY2BGR)
            cv2.putText(t1,f'{n} {t}',(6,22),0,0.7,(255,255,255),2);tiles.append(np.hstack([t1,t2]))
    while len(tiles)%2:tiles.append(np.zeros_like(tiles[0]))
    half=len(tiles)//2
    cv2.imwrite('/tmp/ca1.png',np.vstack([np.hstack(tiles[k:k+2]) for k in range(0,half-half%2,2)]))
    cv2.imwrite('/tmp/ca2.png',np.vstack([np.hstack(tiles[k:k+2]) for k in range(half-half%2,len(tiles),2)]))
