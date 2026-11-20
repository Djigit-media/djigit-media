import cv2,numpy as np,sys,json
clip=sys.argv[1]; objs=json.loads(sys.argv[2]);GG=json.loads(sys.argv[3]) if len(sys.argv)>3 else []  # [[frame,[obj box],[logo box],smin],...]
cap=cv2.VideoCapture(clip+'.mp4');F=[]
while True:
    ok,f=cap.read()
    if not ok:break
    F.append(f)
N=len(F);H,W=F[0].shape[:2]
def track(k,box):
    res={k:tuple(box)};x0,y0,x1,y1=box
    for rng in (range(k+1,N),range(k-1,-1,-1)):
        t=cv2.TrackerCSRT_create();t.init(F[k],(x0,y0,x1-x0,y1-y0))
        for i in rng:
            ok,b=t.update(F[i])
            if not ok:break
            x,y,w,h=b;res[i]=(x,y,x+w,y+h)
    return res
def logo_at(ob0,lb,ob):
    sx=(ob[2]-ob[0])/(ob0[2]-ob0[0]);sy=(ob[3]-ob[1])/(ob0[3]-ob0[1])
    return [int(ob[0]+(lb[0]-ob0[0])*sx),int(ob[1]+(lb[1]-ob0[1])*sy),int(ob[0]+(lb[2]-ob0[0])*sx),int(ob[1]+(lb[3]-ob0[1])*sy)]
def fix(img,lb,smin,mk,mode='y',wfr=0.45,m=8,strict=False):
    x0,y0,x1,y1=max(0,lb[0]-m),max(0,lb[1]-m),min(W,lb[2]+m),min(H,lb[3]+m)
    if x1-x0<8 or y1-y0<8:return
    r=img[y0:y1,x0:x1];hsv=cv2.cvtColor(r,cv2.COLOR_BGR2HSV);h,s,v=[c.astype(int) for c in cv2.split(hsv)]
    if mode=='y':
        yel=((h>=8)&(h<=24)&(s>=smin)&(v>=130)).astype(np.uint8)
        mm=cv2.dilate(yel,np.ones((7,7),np.uint8))
        if mm.any(): img[y0:y1,x0:x1]=cv2.inpaint(r,mm*255,7,cv2.INPAINT_TELEA);mk[y0:y1,x0:x1]|=mm
        return
    if mode=='c':
        cap=(((h<=4)|(h>=172))&(s>=200)&(v>=110)).astype(np.uint8)
        n,lab,st,_=cv2.connectedComponentsWithStats(cap,8)
        if n<2: return
        j=1+int(np.argmax(st[1:,4]));cap=(lab==j).astype(np.uint8)
        cl=cv2.morphologyEx(cap,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(wfr,wfr)))
        clp=np.pad(cl,1);hh,ww=clp.shape;msk=np.zeros((hh+2,ww+2),np.uint8)
        inv=(1-clp).astype(np.uint8);cv2.floodFill(inv,msk,(0,0),2)
        filled=((inv==1)|(clp==1)).astype(np.uint8)[1:-1,1:-1]
        ys,xs=np.nonzero(cap);top,bot=ys.min(),ys.max()
        yy=np.arange(cap.shape[0])[:,None]
        inner=cv2.erode(filled,np.ones((9,9),np.uint8))
        hole=((inner==1)&(cap==0)&(yy<top+0.68*(bot-top))).astype(np.uint8)
        n2,lab2,st2,_=cv2.connectedComponentsWithStats(hole,8);keep=np.zeros_like(hole)
        for q in range(1,n2):
            if st2[q,4]>=25: keep[lab2==q]=1
        capd=cv2.dilate(cap,np.ones((15,15),np.uint8))
        frc=cv2.blur(cap.astype(np.float32),(31,31))
        xx=np.arange(cap.shape[1])[None,:];lft,rgt=xs.min(),xs.max()
        lg=((h>=11)&(h<=35)&(v>=130)&(s>=40)&(capd>0)&(frc>=0.12)&(yy<top+0.68*(bot-top))&((xx<lft+0.6*(rgt-lft)) if strict else True)).astype(np.uint8)
        n3,lab3,st3,_=cv2.connectedComponentsWithStats(lg,8)
        for q in range(1,n3):
            if st3[q,4]>=15: keep[lab3==q]=1
        mm=cv2.dilate(keep,np.ones((9,9),np.uint8))&cv2.dilate(filled,np.ones((13,13),np.uint8))
        if not mm.any(): return
        src=(cap*(1-mm))[...,None].astype(np.float32)
        k=(81,81);num=cv2.blur(r.astype(np.float32)*src,k);den=cv2.blur(src[...,0],k)[...,None]
        fill=num/np.maximum(den,1e-4)
        al=cv2.GaussianBlur(mm.astype(np.float32),(5,5),0)[...,None];al=np.clip(al*1.5,0,1)*(den>0.05)
        img[y0:y1,x0:x1]=(r*(1-al)+fill*al).clip(0,255).astype(np.uint8);mk[y0:y1,x0:x1]|=mm
        return
    red=(((h<=5)|(h>=168))&(s>=110)).astype(np.float32)
    fr=cv2.blur(red,(31,31))
    if mode=='w': yel=((s<=110)&(v>=150)&(fr>=wfr))
    else:
        rb=red>0;ab=np.zeros_like(rb);bl=np.zeros_like(rb);lf=np.zeros_like(rb);rt=np.zeros_like(rb)
        for d in range(3,22,3):
            ab[d:]|=rb[:-d];bl[:-d]|=rb[d:];lf[:,d:]|=rb[:,:-d];rt[:,:-d]|=rb[:,d:]
        yel=((h>=6)&(h<=35)&(v>=smin)&(fr>=wfr)&ab&bl&lf&rt)
    yel=yel.astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(yel,8)
    keep=np.zeros_like(yel)
    for i in range(1,n):
        if st[i,4]>=8: keep[lab==i]=1
    mm=cv2.dilate(keep,np.ones((11,11),np.uint8))
    if not mm.any(): return
    src=(red*(1-mm))[...,None].astype(np.float32)
    k=(41,41);num=cv2.blur(r.astype(np.float32)*src,k);den=cv2.blur(src[...,0],k)[...,None]
    fill=num/np.maximum(den,1e-4)
    al=cv2.GaussianBlur(mm.astype(np.float32),(9,9),0)[...,None]
    al=np.clip(al*1.6,0,1)*(den>0.05)
    img[y0:y1,x0:x1]=(r*(1-al)+fill*al).clip(0,255).astype(np.uint8);mk[y0:y1,x0:x1]|=mm
T=[(track(o[0],o[1]),o) for o in objs]
out=cv2.VideoWriter(f'/tmp/{clip}_fx.avi',cv2.VideoWriter_fourcc(*'MJPG'),24,(W,H))
info=[]
for i in range(N):
    img=F[i].copy();mk=np.zeros((H,W),np.uint8);boxes=[]
    for tr,o in T:
        if i in tr and i<=(o[5] if len(o)>5 else 10**6) and i>=(o[9] if len(o)>9 else 0):
            lb=logo_at(o[1],o[2],tr[i]);fix(img,lb,o[3],mk,o[4] if len(o)>4 else 'y',o[6] if len(o)>6 else 0.45,o[7] if len(o)>7 else 8,bool(o[8]) if len(o)>8 else False);boxes.append(lb)
    for G in GG:
        if G['f0']<=i<=G['f1']:
            x0,y0,x1,y1=G['box'];r=img[y0:y1,x0:x1];hsv=cv2.cvtColor(r,cv2.COLOR_BGR2HSV);h,s,v=[c.astype(int) for c in cv2.split(hsv)]
            yl=((h>=G.get("h0",8))&(h<=G.get("h1",26))&(s>=G.get("s",70))&(v>=G.get("v",110)))
            red=(((h<=G.get("rh",7))|(h>=168))&(s>=110)&(v>=50)).astype(np.float32)
            mm=(yl&(cv2.blur(red,(31,31))>=G.get('fr',0.45))).astype(np.uint8)
            mm=cv2.dilate(mm,np.ones((G.get('d',5),G.get('d',5)),np.uint8))
            if mm.any(): img[y0:y1,x0:x1]=cv2.inpaint(r,mm*255,7,cv2.INPAINT_TELEA);mk[y0:y1,x0:x1]|=mm
    out.write(img);info.append([int(mk.sum()),boxes])
out.release();json.dump(info,open(f'/tmp/{clip}_trk.json','w'));print(clip,N)
