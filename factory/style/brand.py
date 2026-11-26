import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage as ndi
R='/home/claude/djigit-media/'; P='/home/claude/work/prev/'
def font(ch,w,sz):
    n='cyrillic' if ('Ѐ'<=ch<='ӿ') else 'latin'
    return ImageFont.truetype(P+f'mont_{n}_{w}.ttf',sz)
def runs(t):
    out=[];cur='';cf=None
    for ch in t:
        k='c' if ('Ѐ'<=ch<='ӿ') else ('l' if ch not in ' ' else cf)
        if cf is None: cf=k if k else 'l'
        if k!=cf and ch!=' ' : out.append((cur,cf));cur='';cf=k
        cur+=ch
    out.append((cur,cf or 'l'));return out
def width(t,w,sz):
    return sum(font('я' if k=='c' else 'a',w,sz).getlength(s) for s,k in runs(t))
def draw_text(img,cx,y,t,w,sz,fill,gold=False,anchor='m'):
    tw=width(t,w,sz);x=cx-tw/2 if anchor=='m' else cx
    m=Image.new('L',img.size,0);d=ImageDraw.Draw(m)
    for s,k in runs(t):
        f=font('я' if k=='c' else 'a',w,sz);d.text((x,y),s,font=f,fill=255);x+=f.getlength(s)
    if gold:
        bb=m.getbbox();a=np.zeros((img.size[1],img.size[0],3),np.uint8)
        for yy in range(bb[1],bb[3]+1):
            k=(yy-bb[1])/max(1,bb[3]-bb[1]);a[yy,:]=np.array([214,183,124])*(1-k)+np.array([162,124,64])*k
        col=Image.fromarray(a).convert('RGBA')
    else: col=Image.new('RGBA',img.size,fill)
    img.paste(col,(0,0),m)
def logo_img(h):
    src=Image.open(R+'ref/logo2.png').convert('RGB');a=np.array(src).astype(float)
    nonwhite=(765-a.sum(2))>60
    sil=ndi.binary_closing(nonwhite,structure=np.ones((3,3)),iterations=16)
    sil=ndi.binary_fill_holes(sil)
    ys,xs=np.where(sil);y0,y1,x0,x1=ys.min(),ys.max(),xs.min(),xs.max()
    sil=ndi.binary_dilation(sil,structure=np.ones((3,3)),iterations=11)
    rgba=np.zeros(a.shape[:2]+(4,),np.uint8);rgba[...,:3]=a.astype(np.uint8);rgba[...,3]=(sil*255)
    im=Image.fromarray(rgba).crop((x0,y0,x1+1,y1+1))
    w=int(im.width*h/im.height);return im.resize((w,h),Image.LANCZOS)
def shadow(base,layer,blur,op):
    a=layer.split()[3].filter(ImageFilter.GaussianBlur(blur)).point(lambda v:v*op//255)
    sh=Image.new('RGBA',layer.size,(0,0,0,0));sh.putalpha(a);base.alpha_composite(sh)
def logo_block(size=(1080,1920)):
    L=Image.new('RGBA',size,(0,0,0,0));lg=logo_img(205);L.alpha_composite(lg,(200-lg.width//2,95))
    draw_text(L,200,303,'DJIGIT',900,70,None,gold=True)
    draw_text(L,198,383,'СОВРЕМЕННАЯ ГРУЗИНСКАЯ КУХНЯ',700,15,(255,255,255,255))
    return L
def plate(pw,ph,r,alpha=250):
    p=Image.new('RGBA',(pw,ph),(0,0,0,0));d=ImageDraw.Draw(p)
    d.rounded_rectangle((0,0,pw-1,ph-1),r,fill=(5,5,5,alpha),outline=(184,150,92,255),width=2);return p
