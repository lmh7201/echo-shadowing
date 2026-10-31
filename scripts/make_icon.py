"""Draw the Echo PC icon and write pc/icons/icon.png, icon.ico (Windows) and icon.icns (macOS).
Usage: py -3.12 scripts/make_icon.py  (needs Pillow and an italic Georgia; the outputs are committed, so CI never runs this)"""
from pathlib import Path
import sys
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'pc'/'icons'
GREEN=(55,108,76);DEEP=(34,66,46);CREAM=(246,245,240);LEAF=(217,231,173)
FONTS=['C:/Windows/Fonts/georgiai.ttf','/Library/Fonts/Georgia Italic.ttf','/System/Library/Fonts/Supplemental/Georgia Italic.ttf',
       '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf']


def font(size):
    for path in FONTS:
        try:return ImageFont.truetype(path,size)
        except OSError:continue
    sys.exit('No italic serif font found; add one to FONTS.')


def master(size,inset):
    """The web logo's green rounded square with an italic e, plus two echo arcs; drawn 4x and downsampled."""
    s=size*4;m=round(s*inset);box=s-2*m;img=Image.new('RGBA',(s,s),(0,0,0,0))
    gradient=Image.new('RGBA',(1,box))
    for y in range(box):
        t=y/(box-1);gradient.putpixel((0,y),tuple(round(GREEN[i]*(1-t)+DEEP[i]*t) for i in range(3))+(255,))
    tile=gradient.resize((box,box))
    mask=Image.new('L',(s,s),0);ImageDraw.Draw(mask).rounded_rectangle((m,m,s-m-1,s-m-1),radius=round(box*0.225),fill=255)
    img.paste(tile,(m,m),mask.crop((m,m,s-m,s-m)))
    draw=ImageDraw.Draw(img)
    cx=m+box*0.43;cy=m+box*0.5
    for radius,alpha in ((0.335,210),(0.455,120)):
        r=box*radius;w=round(box*0.042)
        draw.arc((cx-r,cy-r,cx+r,cy+r),start=-38,end=38,fill=LEAF+(alpha,),width=w)
    draw.text((cx,cy-box*0.02),'e',font=font(round(box*0.72)),fill=CREAM,anchor='mm')
    return img.resize((size,size),Image.LANCZOS)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    square={n:master(n,0) for n in (16,24,32,48,64,128,256,512,1024)}
    square[256].save(OUT/'icon.png')
    square[256].save(OUT/'icon.ico',append_images=[square[n] for n in (16,24,32,48,64,128)],sizes=[(n,n) for n in (16,24,32,48,64,128,256)])
    # macOS icons leave a transparent margin around the shape, like Apple's own.
    padded={n:master(n,0.09) for n in (16,32,64,128,256,512,1024)}
    padded[1024].save(OUT/'icon.icns',append_images=[padded[n] for n in (16,32,64,128,256,512)])
    print('\n'.join(str(p) for p in sorted(OUT.iterdir())))


if __name__=='__main__':main()
