from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, sys
F='/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf'
def font(sz,w=800):
    f=ImageFont.truetype(F,sz)
    try: f.set_variation_by_axes([w])
    except Exception as e: print(e)
    return f
def make_print(W,col=(207,160,81)):
    lg=Image.open('logo_gold.png').convert('RGBA')
    lh=int(W*0.62); lg=lg.resize((int(lg.width*lh/lg.height),lh),Image.LANCZOS)
    f1=font(int(W*0.30),800); f2=font(int(W*0.085),600)
    d=ImageDraw.Draw(Image.new('RGBA',(10,10)))
    t1='DJIGIT'; t2='KHINKALI HOUSE'
    b1=d.textbbox((0,0),t1,font=f1); b2=d.textbbox((0,0),t2,font=f2)
    H=lh+int(W*0.06)+(b1[3]-b1[1])+int(W*0.05)+(b2[3]-b2[1])
    img=Image.new('RGBA',(W,H),(0,0,0,0)); dr=ImageDraw.Draw(img)
    img.paste(lg,((W-lg.width)//2,0),lg)
    y=lh+int(W*0.06)
    dr.text(((W-(b1[2]-b1[0]))//2-b1[0],y-b1[1]),t1,font=f1,fill=col+(255,))
    y+= (b1[3]-b1[1])+int(W*0.05)
    dr.text(((W-(b2[2]-b2[0]))//2-b2[0],y-b2[1]),t2,font=f2,fill=col+(255,))
    return img
def apply(src,dst,cx,top,W,shear=0.0):
    P=Image.open(src).convert('RGB'); pr=make_print(W)
    if shear: pr=pr.transform(pr.size,Image.AFFINE,(1,0,0,shear,1,-shear*pr.width/2),Image.BICUBIC)
    pr=pr.filter(ImageFilter.GaussianBlur(0.5))
    x=cx-pr.width//2
    reg=np.array(P.crop((x,top,x+pr.width,top+pr.height))).astype(float)
    lum=reg.mean(2); shade=np.clip(lum/ max(np.median(lum),1),0.6,1.5)
    pa=np.array(pr).astype(float); rgb=pa[...,:3]*shade[...,None]*0.92; al=pa[...,3:]/255*0.95
    out=reg*(1-al)+rgb*al
    P.paste(Image.fromarray(np.clip(out,0,255).astype(np.uint8)),(x,top))
    P.save(dst)
if __name__=='__main__':
    apply('ph/p5.png','ph/p5_fix.png',cx=660,top=505,W=300,shear=0.0)
    apply('ph/p6.png','ph/p6_fix.png',cx=600,top=470,W=270,shear=0.0)
