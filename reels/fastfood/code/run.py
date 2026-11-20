import cv2,numpy as np,sys,json
clip=sys.argv[1]; objs=json.loads(sys.argv[2])  # [[frame,x0,y0,x1,y1,kind],...]
cap=cv2.VideoCapture(clip+'.mp4');F=[]
while True:
    ok,f=cap.read()
    if not ok:break
    F.append(f)
N=len(F)
def track(k,box,idx):
    res={}
    x0,y0,x1,y1=box;res[k]=box
    for rng in (range(k+1,N),range(k-1,-1,-1)):
        t=cv2.TrackerCSRT_create();t.init(F[k],(x0,y0,x1-x0,y1-y0))
        for i in rng:
            ok,b=t.update(F[i])
            if not ok:break
            x,y,w,h=[int(v) for v in b];res[i]=(x,y,x+w,y+h)
    return res
def fixroi(img,box,kind,mk):
    H,W=img.shape[:2];m=12
    x0,y0,x1,y1=box;x0,y0=max(0,x0-m),max(0,y0-m);x1,y1=min(W,x1+m),min(H,y1+m)
    if x1-x0<10 or y1-y0<10:return
    r=img[y0:y1,x0:x1]
    hsv=cv2.cvtColor(r,cv2.COLOR_BGR2HSV);h,s,v=[c.astype(np.int32) for c in cv2.split(hsv)]
    smin=150 if kind=='cap' else 110
    yel=((h>=9)&(h<=26)&(s>=smin)&(v>=150)).astype(np.float32)
    if kind=='white': base=((s<=60)&(v>=150)).astype(np.float32)
    else: base=(((h<=7)|(h>=170))&(s>=120)&(v>=60)).astype(np.float32)
    frac=cv2.blur(base,(21,21))
    core=((yel>0)&(frac>0.42)).astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(core,8)
    keep=np.zeros_like(core)
    for i in range(1,n):
        if st[i,4]>=6: keep[lab==i]=1
    mm=cv2.dilate(keep,np.ones((5,5),np.uint8))
    if mm.any():
        img[y0:y1,x0:x1]=cv2.inpaint(r,mm*255,6,cv2.INPAINT_TELEA)
        mk[y0:y1,x0:x1]|=mm
tracks=[(track(o[0],o[1:5],j),o[5]) for j,o in enumerate(objs)]
out=cv2.VideoWriter(f'/tmp/{clip}_fx.avi',cv2.VideoWriter_fourcc(*'MJPG'),24,(F[0].shape[1],F[0].shape[0]))
MK=[]
for i in range(N):
    img=F[i].copy();mk=np.zeros(img.shape[:2],np.uint8)
    for tr,kind in tracks:
        if i in tr: fixroi(img,tr[i],kind,mk)
    out.write(img);MK.append((mk.sum(),[tr.get(i) for tr,_ in tracks]))
    F[i]=img
out.release()
json.dump([[int(a),b] for a,b in MK],open(f'/tmp/{clip}_trk.json','w'))
print(clip,N)
