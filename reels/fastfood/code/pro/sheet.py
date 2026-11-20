import sys;sys.path.insert(0,'pro')
from clean import *
def capsheet(names,out,frames=None):
    rows=[]
    for n in names:
        F=rd(n+'.mp4');G=rd(f'pro/{n}.mp4');T=len(F);H,W=F[0].shape[:2];last=None;tiles=[]
        fr=frames[n] if frames and n in frames else list(np.linspace(0,T-1,16).astype(int))
        cent={}
        for t in range(T):
            if t in fr:
                hm=cap_hull(*HSV(F[t]))
                if hm is not None:
                    ys,xs=np.nonzero(hm);last=((xs.min()+xs.max())//2,(ys.min()+ys.max())//2)
                cent[t]=last
        for t in fr:
            c=cent[t] or (800,650);x0=min(max(c[0]-104,0),W-208);y0=max(c[1]-86,0)
            tl=cv2.resize(G[t][y0:y0+152,x0:x0+208],(333,243),interpolation=cv2.INTER_CUBIC);cv2.putText(tl,f'{n} {t}',(5,18),0,0.55,(255,255,255),2);tiles.append(tl)
        while len(tiles)%8:tiles.append(np.zeros_like(tiles[0]))
        rows+= [np.hstack(tiles[k:k+8]) for k in range(0,len(tiles),8)]
    cv2.imwrite(out,np.vstack(rows))
if __name__=='__main__':
    capsheet(['s2','s3a','F_A'],'/tmp/cap1.png',{'s2':list(range(66,97,2)),'F_A':list(range(20,73,3))[:16]+[72]})
    capsheet(['F_B','F_T','F_C'],'/tmp/cap2.png',{'F_C':list(range(0,96,6))})
