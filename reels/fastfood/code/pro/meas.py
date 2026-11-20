import cv2,numpy as np
def rd(n):
    c=cv2.VideoCapture(n+'.mp4');F=[]
    while True:
        ok,f=c.read()
        if not ok:break
        F.append(f)
    return F
def hsv(f):
    h,s,v=cv2.split(cv2.cvtColor(f,cv2.COLOR_BGR2HSV));return h.astype(np.int16),s.astype(np.int16),v.astype(np.int16)
def blobs(f,amin=1200,top=0.5):
    H,W=f.shape[:2];h,s,v=hsv(f)
    red=(((h<=7)|(h>=171))&(s>=180)&(v>=70)).astype(np.uint8)
    yel=((h>=13)&(h<=36)&(s>=140)&(v>=150)).astype(np.uint8);yel[int(H*top):]=0
    n,l,st,_=cv2.connectedComponentsWithStats(yel,8);o=[]
    for i in range(1,n):
        if st[i,4]>=amin:
            x,y,w,hh,a=st[i];x0,y0,x1,y1=max(0,x-20),max(0,y-20),min(W,x+w+20),min(H,y+hh+20)
            c=(l[y0:y1,x0:x1]==i).astype(np.uint8);ring=cv2.dilate(c,np.ones((31,31),np.uint8))-c
            fr=(ring&red[y0:y1,x0:x1]).sum()/max(1,ring.sum())
            if fr>=0.4:o.append((int(x),int(y),int(x+w),int(y+hh),int(a),round(float(fr),2)))
    return o
if __name__=='__main__':
    S={}
    for n in ['s2','s3a','F_A','F_B','F_T','F_C']:
        F=rd(n);S[n]=F;print(n,len(F))
        for k in range(0,len(F),8 if n in('F_B','F_T') else 6):print('  ',k,blobs(F[k]))
    f=S['s3a'][40];a=f[150:750,560:1080];b=f[950:1400,380:1080]
    cv2.imwrite('/tmp/c1.png',np.hstack([a,cv2.copyMakeBorder(b,0,150,0,0,cv2.BORDER_CONSTANT)]))
    f=S['F_C'][136];g=S['F_A'][58];h_=S['s2'][6]
    a=f[60:700,480:1080];b=cv2.resize(g[1380:1916,0:1080],(756,375));c=h_[60:500,0:420]
    cv2.imwrite('/tmp/c2.png',np.hstack([a,cv2.copyMakeBorder(b,0,265,0,0,cv2.BORDER_CONSTANT),cv2.copyMakeBorder(c,0,200,0,0,cv2.BORDER_CONSTANT)]))
