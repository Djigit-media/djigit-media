import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
F='/home/claude/work/prev/'
LOGO='/home/claude/djigit-media/ref/logo.png'
GOLD_TOP=(214,183,124);GOLD_BOT=(162,124,64)
CORNER={'horse':(128,96,305,318),'dj':(81,329,358,386),'sub':(52,423,381,433)}
END={'horse':(395,432,684,789),'dj':(337,838,749,923),'sub':(203,963,875,986),
     'q1':(196,1070,880,1118),'q2':(221,1128,823,1196),'site':(458,1416,621,1450),
     'btn':(160,1222,919,1352)}
def _font(t,w,sz):
    cyr=any('Ѐ'<=ch<='ӿ' for ch in t)
    return ImageFont.truetype(F+f"mont_{'cyrillic' if cyr else 'latin'}_{w}.ttf",sz)
def _ink(t,w,sz,mixed=True):
    big=Image.new('L',(int(sz*len(t)*1.2)+50,int(sz*2)),0);d=ImageDraw.Draw(big);x=10
    for ch in t:
        f=_font(ch if ch.strip() else 'a',w,sz);d.text((x,int(sz*0.3)),ch,font=f,fill=255);x+=f.getlength(ch)
    return big.crop(big.getbbox())
def fit_text(t,w,bbox,by='width'):
    x0,y0,x1,y1=bbox;tw=x1-x0+1;th=y1-y0+1;sz=40
    for _ in range(30):
        m=_ink(t,w,sz);cur=m.width if by=='width' else m.height;tgt=tw if by=='width' else th
        if abs(cur-tgt)<=1: break
        sz=max(6,sz*tgt/cur)
    return _ink(t,w,sz)
def logo_fit(bbox):
    im=Image.open(LOGO).convert('RGBA');im=im.crop(im.split()[3].point(lambda v:255 if v>8 else 0).getbbox())
    x0,y0,x1,y1=bbox;return im.resize((x1-x0+1,y1-y0+1),Image.LANCZOS)
def colorize(mask,rgb=None,grad=False):
    a=np.array(mask);h,w=a.shape;o=np.zeros((h,w,4),np.uint8)
    if grad:
        k=np.linspace(0,1,h)[:,None,None];o[...,:3]=(np.array(GOLD_TOP)*(1-k)+np.array(GOLD_BOT)*k).astype(np.uint8)
    else: o[...,:3]=rgb
    o[...,3]=a;return Image.fromarray(o)
def corner_layer(size=(1080,1920),shadow=True,subt='СОВРЕМЕННАЯ ГРУЗИНСКАЯ КУХНЯ'):
    L=Image.new('RGBA',size,(0,0,0,0))
    L.alpha_composite(logo_fit(CORNER['horse']),CORNER['horse'][:2])
    L.alpha_composite(colorize(fit_text('DJIGIT',900,CORNER['dj']),grad=True),CORNER['dj'][:2])
    L.alpha_composite(colorize(fit_text(subt,600,CORNER['sub']),(255,255,255)),CORNER['sub'][:2])
    if not shadow: return L
    sh=Image.new('RGBA',size,(0,0,0,0));sh.putalpha(L.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda v:v*130//255))
    out=Image.new('RGBA',size,(0,0,0,0));out.alpha_composite(sh);out.alpha_composite(L);return out
def _sz_of(mask,t,w):
    sz=40
    for _ in range(30):
        m=_ink(t,w,sz)
        if abs(m.width-mask.width)<=1: return sz
        sz=sz*mask.width/m.width
    return sz
def end_layers(q1t='Хочешь такой ресторан',q2t='в своём городе?',btnt='ПИШИ «ФРАНШИЗА» В ДИРЕКТ',subt='СОВРЕМЕННАЯ ГРУЗИНСКАЯ КУХНЯ'):
    E=END;Ls={}
    Ls['horse']=(logo_fit(E['horse']),E['horse'][:2])
    Ls['dj']=(colorize(fit_text('DJIGIT',900,E['dj']),grad=True),E['dj'][:2])
    Ls['sub']=(colorize(fit_text(subt,600,E['sub']),(255,255,255)),E['sub'][:2])
    q1=fit_text(q1t,800,E['q1']);q2=_ink(q2t,800,int(round(_sz_of(q1,q1t,800))))
    Ls['q1']=(colorize(q1,(255,255,255)),E['q1'][:2]);Ls['q2']=(colorize(q2,(255,255,255)),(540-q2.width//2,E['q2'][1]))
    x0,y0,x1,y1=E['btn'];b=Image.new('RGBA',(x1-x0+1,y1-y0+1),(0,0,0,0))
    ImageDraw.Draw(b).rounded_rectangle((0,0,b.width-1,b.height-1),34,fill=(184,146,82,255))
    t=_ink(btnt,900,40);b.alpha_composite(colorize(t,(20,15,8)),((b.width-t.width)//2,(b.height-t.height)//2))
    Ls['btn']=(b,(x0,y0))
    Ls['site']=(colorize(fit_text('djigit.biz',600,E['site']),(214,183,124)),E['site'][:2])
    return Ls
