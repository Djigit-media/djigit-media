import cv2,numpy as np,sys
clip=sys.argv[1];fr=[int(x) for x in sys.argv[2].split(',')];y0,y1=int(sys.argv[3]),int(sys.argv[4])
b=cv2.VideoCapture(f'/tmp/{clip}_fx.avi');i=0;out=[]
while True:
    ok,f=b.read()
    if not ok:break
    if i in fr: out.append(cv2.resize(f[y0:y1,300:1080],(520,int(520*(y1-y0)/780))))
    i+=1
cv2.imwrite('/tmp/zoom.png',np.vstack([np.hstack(out[k:k+3]) for k in range(0,len(out),3)]))
