import sys;sys.path.insert(0,'pro')
from roto import *
OBJ={'s3a':[(0,(560,1053,660,1140),'w'),(0,(934,1083,1015,1172),'w'),(0,(510,1152,562,1200),'r'),(0,(774,1176,828,1222),'r')],
     's2':[(96,(552,1056,660,1132),'w'),(96,(936,1086,1016,1170),'w'),(96,(514,1156,558,1200),'r'),(96,(776,1182,816,1220),'r'),(80,(638,1062,700,1140),'w'),(80,(980,1094,1062,1178),'w'),(80,(554,1162,600,1204),'r'),(80,(824,1190,858,1228),'r'),(70,(764,1078,826,1156),'w'),(70,(970,1104,1008,1130),'w'),(70,(676,1180,712,1218),'r'),(70,(956,1180,998,1204),'r')],
     'F_A':[(0,(798,1312,880,1420),'w'),(0,(684,1450,748,1510),'r'),(0,(1040,1488,1080,1546),'r'),(10,(982,1390,1048,1460),'r')]}
def track(O,ref,bb,pad=36,win=40):
    T=len(O);x0,y0,x1,y1=bb;tx0,ty0,tx1,ty1=x0-pad,y0-pad,x1+pad,y1+pad;H,W=O[0].shape[:2]
    tx0,ty0,tx1,ty1=max(0,tx0),max(0,ty0),min(W,tx1),min(H,ty1)
    tpl=cv2.cvtColor(O[ref][ty0:ty1,tx0:tx1],cv2.COLOR_BGR2GRAY);th,tw=tpl.shape
    pos={ref:(0.0,0.0,1.0)}
    for rng in (range(ref+1,T),range(ref-1,-1,-1)):
        dx,dy=0.0,0.0
        for t in rng:
            g=cv2.cvtColor(O[t],cv2.COLOR_BGR2GRAY);sx0=int(max(0,tx0+dx-win));sy0=int(max(0,ty0+dy-win));sx1=int(min(W,tx1+dx+win));sy1=int(min(H,ty1+dy+win))
            S=g[sy0:sy1,sx0:sx1]
            if S.shape[0]<th or S.shape[1]<tw:break
            r=cv2.matchTemplate(S,tpl,cv2.TM_CCOEFF_NORMED);_,mv,_,ml=cv2.minMaxLoc(r)
            if mv<0.55:break
            dx,dy=sx0+ml[0]-tx0,sy0+ml[1]-ty0;pos[t]=(float(dx),float(dy),float(mv))
    ks=sorted(pos);arr=np.array([pos[k][:2] for k in ks])
    sm={}
    for i,k in enumerate(ks):
        lo,hi=max(0,i-2),min(len(ks),i+3);sm[k]=arr[lo:hi].mean(0)
    return sm
def run(name,dbg=()):
    O=rd(name+'.mp4');G=rd(f'pro/B_{name}.mkv');T=len(G);H,W=G[0].shape[:2];out=[g.copy() for g in G];cnt=np.zeros(T,int);P=24
    for ref,bb,kind in OBJ[name]:
        sm=track(O,ref,bb);x0,y0,x1,y1=bb;bw,bh=x1-x0+2*P,y1-y0+2*P
        rel={}
        for t,(dx,dy) in sm.items():
            X0,Y0=int(round(x0+dx))-P,int(round(y0+dy))-P
            if X0<0 or Y0<0 or X0+bw>W or Y0+bh>H:continue
            c=out[t][Y0:Y0+bh,X0:X0+bw];L,a,b=LAB(c)
            obj=(((a>=45)&(L>=40)) if kind=='r' else ((L>=160)&(np.abs(a)<=18)&(b<=26))).astype(np.uint8)
            if obj.sum()<200:continue
            hm=np.zeros_like(obj);cv2.fillConvexPoly(hm,cv2.convexHull(cv2.findNonZero(cv2.morphologyEx(obj,cv2.MORPH_OPEN,K(5)) if cv2.morphologyEx(obj,cv2.MORPH_OPEN,K(5)).any() else obj)),1)
            inner=np.zeros_like(obj);inner[P-6:bh-P+6,P-6:bw-P+6]=1
            if kind=='r':lg=((b>=22)&(a<=44)&(L>=90)).astype(np.uint8)
            else:lg=((b>=16)&(L>=100)&(a<=40)).astype(np.uint8)
            lg&=hm&inner&(1-obj)
            rel[t]=(X0,Y0,lg,hm,obj)
        for t,(X0,Y0,lg,hm,obj) in rel.items():
            U=lg.copy()
            for u in (t-2,t-1,t+1,t+2):
                if u in rel:U|=rel[u][2]
            m=cv2.dilate(U,K(7))&hm
            if kind=='w':m&=(LAB(out[t][Y0:Y0+bh,X0:X0+bw])[0]>=120).astype(np.uint8)
            if m.sum()<15:continue
            Y0e,X0e=max(0,Y0-16),max(0,X0-16);Y1e,X1e=min(H,Y0+bh+16),min(W,X0+bw+16)
            ce=out[t][Y0e:Y1e,X0e:X1e];Le,ae,be=LAB(ce)
            srce=(((ae>=45)&(Le>=40)) if kind=='r' else ((Le>=160)&(np.abs(ae)<=18)&(be<=26))).astype(np.uint8)
            me=np.zeros(Le.shape,np.uint8);me[Y0-Y0e:Y0-Y0e+bh,X0-X0e:X0-X0e+bw]=m
            o=np.clip(hfill(ce,me,srce&(1-me)),0,255).astype(np.uint8)
            bl=cv2.GaussianBlur(o,(0,0),0.7);edge=cv2.dilate(me,K(3))&(1-cv2.erode(me,K(3)));o[edge>0]=bl[edge>0]
            out[t][Y0e:Y1e,X0e:X1e]=o;cnt[t]+=1
    print(name,'objects per frame:',''.join(str(min(c,9)) for c in cnt))
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','24','-i','-','-c:v','ffv1','-pix_fmt','bgr0',f'pro/C_{name}.mkv'],stdin=subprocess.PIPE)
    for o in out:p.stdin.write(o.tobytes())
    p.stdin.close();p.wait()
if __name__=='__main__':
    for n in sys.argv[1].split(','):run(n)
