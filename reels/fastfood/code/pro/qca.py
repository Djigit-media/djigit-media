import sys;sys.path.insert(0,'pro')
from clean import *
def wall_sheet(names,out,key='A'):
    rows=[]
    for n in names:
        G=rd(f'pro/A_{n}.mkv') if key=='A' else rd(f'pro/{n}.mp4');L=json.load(open(f'pro/A_{n}.json'));T=len(G);H,W=G[0].shape[:2]
        fr=list(np.linspace(0,T-1,12).astype(int));tiles=[];last=(700,320)
        for t in fr:
            sg=L[t]['sign']
            if sg:
                b=max(sg,key=lambda q:(q[2]-q[0])*(q[3]-q[1]));last=((b[0]+b[2])//2,(b[1]+b[3])//2)
            cx,cy=last;x0=int(min(max(cx-200,0),W-400));y0=int(min(max(cy-230,0),H-460))
            tl=cv2.resize(G[t][y0:y0+460,x0:x0+400],(220,253),interpolation=cv2.INTER_AREA);cv2.putText(tl,f'{n} {t}',(4,16),0,0.5,(255,255,255),1);tiles.append(tl)
        rows.append(np.hstack(tiles));del G
    cv2.imwrite(out,np.vstack(rows))
if __name__=='__main__':
    wall_sheet(['s2','s3a','F_A'],'/tmp/w1.png');wall_sheet(['F_B','F_T','F_C'],'/tmp/w2.png')
