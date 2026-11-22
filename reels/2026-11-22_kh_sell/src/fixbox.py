import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
F='/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf'
GOLD=(214,176,106)
def fnt(sz,w=800):
    f=ImageFont.truetype(F,sz); f.set_variation_by_axes([w]); return f
def flat(kind,W,H,S=6):
    im=Image.new('RGBA',(W*S,H*S),(0,0,0,0)); d=ImageDraw.Draw(im)
    lg=Image.open('/home/claude/djigit-media/ref/logo.png').convert('RGBA'); lg=lg.crop(lg.split()[3].point(lambda v:255 if v>8 else 0).getbbox())
    def text_fit(t,wpx,y,w=800):
        sz=100
        for _ in range(8):
            f=fnt(sz,w); bb=d.textbbox((0,0),t,font=f); cur=bb[2]-bb[0]; sz=sz*wpx*S/cur
        f=fnt(int(sz),w); bb=d.textbbox((0,0),t,font=f); return f,bb
    if kind=='L':   # horse top center, text below
        hh=int(H*0.52*S); hw=int(lg.width*hh/lg.height); im.alpha_composite(lg.resize((hw,hh),Image.LANCZOS),((W*S-hw)//2,0))
        f,bb=text_fit('DJIGIT',W*0.78,0); d.text(((W*S-(bb[2]-bb[0]))//2-bb[0],int(H*0.58*S)-bb[1]),'DJIGIT',font=f,fill=GOLD+(255,))
        f2,bb2=text_fit('KHINKALI HOUSE',W*0.66,0,600); d.text(((W*S-(bb2[2]-bb2[0]))//2-bb2[0],int(H*0.88*S)-bb2[1]),'KHINKALI HOUSE',font=f2,fill=GOLD+(255,))
    else:           # horse left, text right
        hh=int(H*0.92*S); hw=int(lg.width*hh/lg.height); im.alpha_composite(lg.resize((hw,hh),Image.LANCZOS),(0,int(H*0.04*S)))
        x0=hw+int(W*0.07*S); avail=W*S-x0
        f,bb=text_fit('DJIGIT',avail/S,0); d.text((x0-bb[0],int(H*0.10*S)-bb[1]),'DJIGIT',font=f,fill=GOLD+(255,))
        f2,bb2=text_fit('KHINKALI HOUSE',avail*0.92/S,0,700); d.text((x0-bb2[0],int(H*0.60*S)-bb2[1]),'KHINKALI HOUSE',font=f2,fill=GOLD+(255,))
    return im
def c2f(p): return (470+p[0]/2, 820+p[1]/2)
img=cv2.imread('ph/p10.png'); H0,W0=img.shape[:2]
faces=[('L',200,115,[(100,520),(280,615),(280,730),(100,635)],[(92,512),(290,618),(290,742),(92,648)]),
       ('R',190,85,[(570,527),(760,447),(760,532),(570,612)],[(562,520),(766,436),(766,540),(562,620)])]
mask=np.zeros((H0,W0),np.uint8)
for k,w,h,q,m in faces:
    cv2.fillPoly(mask,[np.array([c2f(p) for p in m],np.int32)],255)
mask=cv2.dilate(mask,np.ones((3,3),np.uint8))
inp=cv2.inpaint(img,mask,4,cv2.INPAINT_TELEA)
fm=cv2.GaussianBlur(mask,(0,0),2.5).astype(np.float32)[...,None]/255
out=(inp.astype(np.float32)*fm+img.astype(np.float32)*(1-fm)).astype(np.uint8)
for k,w,h,q,m in faces:
    S=6; fl=np.array(flat(k,w,h,S)); src=np.float32([[0,0],[w*S,0],[w*S,h*S],[0,h*S]]); dst=np.float32([c2f(p) for p in q])
    M=cv2.getPerspectiveTransform(src,dst)
    wr=cv2.warpPerspective(fl,M,(W0,H0),flags=cv2.INTER_AREA if False else cv2.INTER_LINEAR)
    wr=cv2.GaussianBlur(wr,(0,0),0.5)
    al=wr[...,3:4].astype(np.float32)/255*0.97; rgb=wr[...,:3][...,::-1].astype(np.float32)
    # shade by local luminance of inpainted face
    lum=cv2.cvtColor(out,cv2.COLOR_BGR2GRAY).astype(np.float32)[...,None]
    out=(out.astype(np.float32)*(1-al)+rgb*al*0.95).clip(0,255).astype(np.uint8)
cv2.imwrite('ph/p10_fix.png',out)
cv2.imwrite('/tmp/box_fix.jpg',out[820:1300,470:941][::1,::1])
c=cv2.imread('/tmp/box_fix.jpg'); cv2.imwrite('/tmp/box_fix.jpg',cv2.resize(c,(942,960),interpolation=cv2.INTER_LANCZOS4),[cv2.IMWRITE_JPEG_QUALITY,92])
