import cv2,numpy as np,sys,json
clip,step=sys.argv[1],int(sys.argv[2])
a=cv2.VideoCapture(clip+'.mp4');b=cv2.VideoCapture(f'/tmp/{clip}_fx.avi');trk=json.load(open(f'/tmp/{clip}_trk.json'))
i=0;rows=[]
while True:
    ok1,f1=a.read();ok2,f2=b.read()
    if not(ok1 and ok2):break
    if i%step==0:
        g=f2.copy()
        for bx in trk[i][1]:
            if bx: cv2.rectangle(g,tuple(bx[:2]),tuple(bx[2:]),(0,255,0),3)
        cv2.putText(g,f'f{i}',(30,1880),0,3,(255,0,255),6)
        rows.append(np.hstack([cv2.resize(f1[400:1500],(400,407)),cv2.resize(g[400:1500],(400,407))]))
    i+=1
while len(rows)%3: rows.append(np.zeros_like(rows[0]))
cv2.imwrite(f'/tmp/chk_{clip}.png',np.vstack([np.hstack(rows[k:k+3]) for k in range(0,len(rows),3)]))
