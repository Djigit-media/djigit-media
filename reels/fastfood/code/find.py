import cv2,numpy as np,sys,json
clip,fi=sys.argv[1],int(sys.argv[2]);boxes=json.loads(sys.argv[3])
cap=cv2.VideoCapture(clip+'.mp4');cap.set(cv2.CAP_PROP_POS_FRAMES,fi);ok,f=cap.read()
hsv=cv2.cvtColor(f,cv2.COLOR_BGR2HSV);h,s,v=[c.astype(int) for c in cv2.split(hsv)]
yel=((h>=8)&(h<=22)&(s>=140)&(v>=170)).astype(np.uint8)
vis=f.copy()
for k,(x0,y0,x1,y1) in enumerate(boxes):
    n,lab,st,_=cv2.connectedComponentsWithStats(cv2.dilate(yel[y0:y1,x0:x1],np.ones((5,5),np.uint8)),8)
    big=sorted([st[i] for i in range(1,n)],key=lambda r:-r[4])[:3]
    print(k,[(int(r[0]+x0),int(r[1]+y0),int(r[0]+x0+r[2]),int(r[1]+y0+r[3]),int(r[4])) for r in big])
    cv2.rectangle(vis,(x0,y0),(x1,y1),(0,255,0),2)
    for j,r in enumerate(big): cv2.rectangle(vis,(r[0]+x0,r[1]+y0),(r[0]+x0+r[2],r[1]+y0+r[3]),[(255,0,255),(255,255,0),(0,255,255)][j],2)
cv2.imwrite('/tmp/find.png',cv2.resize(vis,(540,958)))
