import sys;sys.path.insert(0,'pro')
from roto import *
def boxlogo(f,zone):
    x0,y0,x1,y1=zone;c=f[y0:y1,x0:x1];h,s,v=HSV(c);L,a,b=LAB(c);M=np.zeros(h.shape,np.uint8)
    R=((a>=45)&(L>=40)).astype(np.uint8);R=cv2.morphologyEx(R,cv2.MORPH_OPEN,K(3))
    n,l,st,_=comps(R)
    for i in range(1,n):
        x,y,w,hh,ar=st[i]
        if ar<2500 or ar>90000 or hh<45:continue
        comp=(l==i).astype(np.uint8);hm=np.zeros_like(comp);cv2.fillConvexPoly(hm,cv2.convexHull(cv2.findNonZero(comp)),1)
        hm[:y+int(0.28*hh)]=0;hm=cv2.erode(hm,K(5))
        dev=((h>=7)&(h<=38)&(s>=70)&(v>=90)).astype(np.uint8)
        cand=hm&(1-comp)&dev
        cand|=hm&dev&(cv2.blur(comp.astype(np.float32),(15,15))>0.5).astype(np.uint8)&((b-a)>-5).astype(np.uint8)
        n2,l2,s2,_=comps(cand)
        for j in range(1,n2):
            if s2[j,4]>=6 and s2[j,4]<=0.25*ar:M[l2==j]=1
    return M
def run(name):
    ts,zone=TABLE[name];G=rd(f'pro/C_{name}.mkv');T=len(G);H,W=G[0].shape[:2];x0,y0,x1,y1=zone
    Ms=[boxlogo(G[t],zone) if t>=ts else None for t in range(T)];out=list(G);cnt=[]
    for t in range(ts,T):
        U=np.zeros_like(Ms[t])
        for u in range(max(ts,t-2),min(T,t+3)):U|=cv2.dilate(Ms[u],K(5))
        crop=G[t][y0:y1,x0:x1];L,a,b=LAB(crop);R=((a>=45)&(L>=40)).astype(np.uint8)
        m=cv2.dilate(U,K(5))&cv2.dilate(R,K(9))&((R|((a>=15)&(L>=60))).astype(np.uint8))
        cnt.append(int(m.sum()))
        if not m.any():continue
        o=np.clip(hfill(crop,m,R&(1-m)),0,255).astype(np.uint8)
        bl=cv2.GaussianBlur(o,(0,0),0.7);e=cv2.dilate(m,K(3))&(1-cv2.erode(m,K(3)));o[e>0]=bl[e>0]
        g=G[t].copy();g[y0:y1,x0:x1]=o;out[t]=g
    print(name,cnt[::4])
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','24','-i','-','-c:v','ffv1','-pix_fmt','bgr0',f'pro/D_{name}.mkv'],stdin=subprocess.PIPE)
    for o in out:p.stdin.write(o.tobytes())
    p.stdin.close();p.wait()
if __name__=='__main__':
    for n in sys.argv[1].split(','):run(n)
