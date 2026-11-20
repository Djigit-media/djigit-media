import sys;sys.path.insert(0,'pro')
from clean import *
O=rd('s2.mp4');B=rd('pro/B_s2.mkv');H,W=O[0].shape[:2];out=[]
for t,(o,b) in enumerate(zip(O,B)):
    if t<=34:
        h,s,v=HSV(o);dk=cv2.morphologyEx((v<=70).astype(np.uint8),cv2.MORPH_OPEN,K(5));dk[480:]=0;dk[:,500:]=0
        n,l,st,_=comps(dk);hull=np.zeros((H,W),np.uint8)
        for i in range(1,n):
            x,y,w,hh,a=st[i]
            if a>=2500 and w<=320 and hh<=260:cv2.fillConvexPoly(hull,cv2.convexHull(cv2.findNonZero((l==i).astype(np.uint8))),1)
        if hull.any():
            br=((v>=225)).astype(np.uint8);n,l,st,_=comps(br);hd=cv2.dilate(hull,K(5));lamp=hull.copy()
            for i in range(1,n):
                x,y,w,hh,a=st[i]
                if hd[y:y+hh,x:x+w].any() and hh<=60:put(lamp,l,i,st)
            al=cv2.GaussianBlur(cv2.dilate(lamp,K(5)).astype(np.float32),(0,0),1.2)[...,None]
            b=np.clip(b*(1-al)+o*al,0,255).astype(np.uint8)
    out.append(b)
p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','24','-i','-','-c:v','ffv1','-pix_fmt','bgr0','pro/B_s2.mkv'],stdin=subprocess.PIPE)
for g in out:p.stdin.write(g.tobytes())
p.stdin.close();p.wait()
tiles=[cv2.resize(out[t][200:700,0:420],(336,400)) for t in (0,4,12,18,24,30)]
cv2.imwrite('/tmp/lamp.png',np.hstack(tiles))
B=rd('pro/B_F_C.mkv');cv2.imwrite('/tmp/hug.png',np.hstack([cv2.resize(B[t][40:640,420:1020],(330,330)) for t in (124,130,134,138,142,144)]))
