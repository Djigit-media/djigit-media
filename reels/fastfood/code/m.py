import cv2,numpy as np,sys
def mask(img):
    hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    h,s,v=cv2.split(hsv)
    yel=((h>=10)&(h<=24)&(s>=85)&(v>=165)).astype(np.uint8)
    red=(((h<=8)|(h>=170))&(s>=120)&(v>=70)).astype(np.uint8)
    wht=((s<=55)&(v>=140)).astype(np.uint8)
    yd=cv2.dilate(yel,np.ones((3,3),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(yd,8)
    out=np.zeros_like(yel)
    H=img.shape[0]
    for i in range(1,n):
        x,y,w,hh,a=st[i]
        if a<15 or a>0.004*img.size/3: continue
        comp=(lab[y:y+hh,x:x+w]==i).astype(np.uint8)
        pad=max(4,int(0.35*max(w,hh)))
        x0,y0=max(0,x-pad),max(0,y-pad);x1,y1=min(img.shape[1],x+w+pad),min(H,y+hh+pad)
        full=np.zeros((y1-y0,x1-x0),np.uint8);full[y-y0:y-y0+hh,x-x0:x-x0+w]=comp
        ring=cv2.dilate(full,np.ones((2*pad+1,2*pad+1),np.uint8))-full
        rn=ring.sum()
        if rn==0: continue
        fr=(red[y0:y1,x0:x1]*ring).sum()/rn
        fw=(wht[y0:y1,x0:x1]*ring).sum()/rn
        if fr>0.55 or fw>0.6:
            out[y0:y1,x0:x1]|=full
    return out
def fix(img):
    m=mask(img)
    m=cv2.dilate(m,np.ones((5,5),np.uint8))
    return cv2.inpaint(img,m*255,5,cv2.INPAINT_TELEA),m
if __name__=='__main__':
    img=cv2.imread(sys.argv[1]);r,m=fix(img)
    vis=img.copy();vis[m>0]=(255,0,255)
    cv2.imwrite(sys.argv[2],np.hstack([cv2.resize(vis,(540,960)),cv2.resize(r,(540,960))]))
