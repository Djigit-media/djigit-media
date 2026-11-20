import sys;sys.path.insert(0,'pro')
from clean import *
name=sys.argv[1];F=rd(name+'.mp4');H,W=F[0].shape[:2]
for t in [int(x) for x in sys.argv[2].split(',')]:
    f=F[t];h,s,v=HSV(f);print('== frame',t)
    red=(((h<=8)|(h>=170))&(s>=170)&(v>=60)).astype(np.uint8)
    yl=((h>=9)&(h<=40)&(s>=125)&(v>=90)).astype(np.uint8)
    n,l,st,ce=comps(yl)
    for i in range(1,n):
        x,y,w,hh,a=st[i]
        if a>=600 and y+hh<0.45*H:
            c,(x0,y0,x1,y1)=cc(l,i,st,24,H,W);print(' SIGN? bb',(x,y,x+w,y+hh),'a',a,'ext',round(a/(w*hh),2),'ring',round(ring(c,red[y0:y1,x0:x1],15),2))
    # cap
    redc=(((h<=6)|(h>=171))&(s>=175)&(v>=90)).astype(np.uint8)
    n,l,st,ce=comps(redc)
    for i in range(1,n):
        x,y,w,hh,a=st[i]
        if 3000<=a<=90000 and w<=430 and hh<=320 and 0.2*H<ce[i][1]<0.6*H and x+w>0.45*W:
            print(' CAP comp bb',(x,y,x+w,y+hh),'a',a)
            c,(x0,y0,x1,y1)=cc(l,i,st,6,H,W);hm=np.zeros_like(c);cv2.fillConvexPoly(hm,cv2.convexHull(cv2.findNonZero(c)),1)
            non=hm&(1-c);n2,l2,s2,_=comps(non)
            for j in range(1,n2):
                if s2[j,4]>=12:
                    q=(l2==j);hh_,ss_,vv_=h[y0:y1,x0:x1][q],s[y0:y1,x0:x1][q],v[y0:y1,x0:x1][q]
                    qq,(a0,b0,a1,b1)=cc(l2,j,s2,8,y1-y0,x1-x0)
                    print('    hole a',s2[j,4],'bb',(x0+s2[j,0],y0+s2[j,1]),'H',np.percentile(hh_,[10,50,90]).astype(int),'S',np.percentile(ss_,[10,50,90]).astype(int),'V',np.percentile(vv_,[10,50,90]).astype(int),'ring',round(ring(qq,cv2.dilate(c,K(3))[b0:b1,a0:a1],6),2))
    # table yellow comps
    if len(sys.argv)>3:
        x0,y0,x1,y1=[int(q) for q in sys.argv[3].split(',')]
        ye=((h>=10)&(h<=38)&(s>=100)&(v>=130)).astype(np.uint8)[y0:y1,x0:x1]
        n,l,st,_=comps(ye)
        for i in range(1,n):
            if st[i,4]>=150:
                q,(a0,b0,a1,b1)=cc(l,i,st,12,y1-y0,x1-x0);rg=(cv2.dilate(q,K(17))-q).astype(bool)
                hs,ss_,vs=h[y0+b0:y0+b1,x0+a0:x0+a1],s[y0+b0:y0+b1,x0+a0:x0+a1],v[y0+b0:y0+b1,x0+a0:x0+a1]
                qb=q.astype(bool)
                print('  Y bb',(x0+st[i,0],y0+st[i,1],st[i,2],st[i,3]),'a',st[i,4],'Hm',int(np.median(hs[qb])),'Sm',int(np.median(ss_[qb])),'Vm',int(np.median(vs[qb])),
                  '| ring S',np.percentile(ss_[rg],[25,50,75]).astype(int),'V',np.percentile(vs[rg],[25,50,75]).astype(int),'redfrac',round(float(red[y0+b0:y0+b1,x0+a0:x0+a1][rg].mean()),2))
