import cv2,numpy as np,sys,json
clip,fi,boxes=sys.argv[1],int(sys.argv[2]),json.loads(sys.argv[3])
cap=cv2.VideoCapture(clip+'.mp4');cap.set(cv2.CAP_PROP_POS_FRAMES,fi);ok,f=cap.read()
outs=[]
for x0,y0,x1,y1 in boxes:
    outs.append(cv2.resize(f[y0:y1,x0:x1],(240,240)))
cv2.imwrite('/tmp/show.png',np.hstack(outs))
