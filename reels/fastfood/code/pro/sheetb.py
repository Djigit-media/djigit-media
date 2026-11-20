import sys;sys.path.insert(0,'pro')
from roto import *
def capsheet(n,frames,out,key='B',per=7,zoom=1.5,cw=260,ch=200):
    G=rd(f'pro/{key}_{n}.mkv') if key in('A','B') else rd(n+'.mp4');L=json.load(open(f'pro/B_{n}.json'));H,W=G[0].shape[:2];tiles=[];last=(820,720)
    for t in frames:
        cb=L[t].get('cap')
        if cb:last=((cb[0]+cb[2])//2,cb[1]+int(0.38*(cb[3]-cb[1])))
        cx,cy=last;x0=int(min(max(cx-cw//2,0),W-cw));y0=int(min(max(cy-ch//2,0),H-ch))
        tl=cv2.resize(G[t][y0:y0+ch,x0:x0+cw],(int(cw*zoom),int(ch*zoom)),interpolation=cv2.INTER_CUBIC)
        cv2.putText(tl,f'{n} {t}'+('' if L[t].get('capfill') else ' -'),(5,20),0,0.6,(255,255,255),2);tiles.append(tl)
    while len(tiles)%per:tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(out,np.vstack([np.hstack(tiles[k:k+per]) for k in range(0,len(tiles),per)]))
if __name__=='__main__':
    capsheet('s2',list(range(64,97,2)),'/tmp/sb_s2.png')
    capsheet('s3a',list(range(0,88,3)),'/tmp/sb_s3a.png')
    capsheet('F_A',list(range(16,73,3)),'/tmp/sb_FA.png')
    capsheet('F_B',list(range(0,121,9)),'/tmp/sb_FB.png')
    capsheet('F_T',list(range(0,97,7)),'/tmp/sb_FT.png')
    capsheet('F_C',list(range(0,84,3)),'/tmp/sb_FC.png')
