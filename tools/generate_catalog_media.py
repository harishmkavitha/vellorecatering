#!/usr/bin/env python3
"""Generate original local SVG illustrations, OG images and tiny WebM motion loops.
All visuals are procedural and created for this site; no stock-photo dependency.
"""
from __future__ import annotations
import hashlib, html, json, math, shutil, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
ITEMS=json.loads((ROOT/'data/catering-catalog.json').read_text(encoding='utf-8'))['items']
IMG=ROOT/'assets/img/pages'; VID=ROOT/'assets/video/pages'
IMG.mkdir(parents=True,exist_ok=True); VID.mkdir(parents=True,exist_ok=True)

PALETTE=['#7A231D','#5C3424','#3F4A2C','#5B274F','#2B4A45','#6E5123','#57313D','#3B3F5B']
GOLD='#D6AD52'; GOLD2='#F1D38B'; BLACK='#080704'; IVORY='#F7EFD7'

def n(seed, i=0): return int(hashlib.sha256((seed+str(i)).encode()).hexdigest()[:8],16)
def esc(t): return html.escape(t,quote=True)

def svg(item,kind,w,h):
    seed=item['slug']+kind; accent=PALETTE[n(seed)%len(PALETTE)]
    title=item['catering_type']; short=title.replace(' Catering','')
    circles=[]
    for i in range(10):
        x=40+n(seed,i+2)%(w-80); y=40+n(seed,i+20)%(h-80); r=20+n(seed,i+40)%90
        circles.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{GOLD}" stroke-opacity="{0.05+(i%4)*0.025}" stroke-width="2"/>')
    # abstract banana-leaf / plate / serving geometry, clearly illustrative rather than a fake photo
    if kind=='hero':
        art=f'''<ellipse cx="{w*.76:.0f}" cy="{h*.50:.0f}" rx="{w*.20:.0f}" ry="{h*.31:.0f}" fill="{accent}" opacity=".55"/><circle cx="{w*.76:.0f}" cy="{h*.50:.0f}" r="{min(w,h)*.22:.0f}" fill="{BLACK}" stroke="{GOLD}" stroke-width="4"/><circle cx="{w*.76:.0f}" cy="{h*.50:.0f}" r="{min(w,h)*.14:.0f}" fill="{GOLD}" opacity=".10"/><path d="M{w*.66:.0f},{h*.63:.0f} C{w*.76:.0f},{h*.32:.0f} {w*.85:.0f},{h*.35:.0f} {w*.89:.0f},{h*.63:.0f}" fill="none" stroke="{GOLD2}" stroke-width="8" stroke-linecap="round" opacity=".9"/>'''
        tx=w*.08; ty=h*.40; fs=max(36,int(w*.038))
    else:
        shift=(n(seed,77)%140)-70
        art=f'''<rect x="{w*.12:.0f}" y="{h*.20:.0f}" width="{w*.76:.0f}" height="{h*.58:.0f}" rx="44" fill="{accent}" opacity=".32"/><ellipse cx="{w*.50+shift:.0f}" cy="{h*.48:.0f}" rx="{w*.25:.0f}" ry="{h*.22:.0f}" fill="{BLACK}" stroke="{GOLD}" stroke-width="3"/><path d="M{w*.30:.0f},{h*.57:.0f} Q{w*.50:.0f},{h*.25:.0f} {w*.70:.0f},{h*.57:.0f}" fill="none" stroke="{GOLD2}" stroke-width="6" opacity=".9"/><circle cx="{w*.42:.0f}" cy="{h*.48:.0f}" r="{h*.06:.0f}" fill="{GOLD}" opacity=".34"/><circle cx="{w*.58:.0f}" cy="{h*.48:.0f}" r="{h*.08:.0f}" fill="{GOLD}" opacity=".18"/>'''
        tx=w*.08; ty=h*.88; fs=max(28,int(w*.035))
    label='Original illustration • Vellore Catering'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d"><title id="t">{esc(title)} illustration</title><desc id="d">Original abstract catering illustration created for the {esc(title)} page.</desc><defs><linearGradient id="bg" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#030303"/><stop offset=".55" stop-color="{BLACK}"/><stop offset="1" stop-color="{accent}" stop-opacity=".72"/></linearGradient><radialGradient id="glow"><stop stop-color="{GOLD}" stop-opacity=".23"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient></defs><rect width="100%" height="100%" fill="url(#bg)"/><circle cx="82%" cy="20%" r="34%" fill="url(#glow)"/>{''.join(circles)}{art}<text x="{tx:.0f}" y="{ty:.0f}" fill="{IVORY}" font-family="Georgia,serif" font-size="{fs}" font-weight="700">{esc(short[:34])}</text><text x="{tx:.0f}" y="{ty+fs*1.25:.0f}" fill="{GOLD2}" font-family="Arial,sans-serif" font-size="{max(18,int(fs*.42))}" letter-spacing="3">IN VELLORE</text><text x="{w*.08:.0f}" y="{h*.94:.0f}" fill="{IVORY}" opacity=".62" font-family="Arial,sans-serif" font-size="{max(14,int(w*.013))}">{esc(label)}</text></svg>'''

def write_og(item):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return False
    W,H=1200,630; seed=item['slug']; accent=PALETTE[n(seed)%len(PALETTE)]
    im=Image.new('RGB',(W,H),(8,7,4)); d=ImageDraw.Draw(im)
    # simple gradient
    import PIL.ImageColor
    ac=PIL.ImageColor.getrgb(accent)
    for y in range(H):
        mix=y/(H-1); base=(8,7,4)
        c=tuple(int(base[i]*(1-mix*.35)+ac[i]*(mix*.35)) for i in range(3))
        d.line((0,y,W,y),fill=c)
    for i in range(12):
        x=700+n(seed,i)%480; y=30+n(seed,i+20)%560; r=20+n(seed,i+40)%90
        d.ellipse((x-r,y-r,x+r,y+r),outline=(214,173,82),width=2)
    font_paths=['/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf','/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf']
    fp=next((x for x in font_paths if Path(x).exists()),None)
    sans='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    f1=ImageFont.truetype(fp,54) if fp else ImageFont.load_default()
    f2=ImageFont.truetype(sans,24) if Path(sans).exists() else ImageFont.load_default()
    title=item['catering_type'].replace(' Catering','')
    # basic two-line wrap
    words=title.split(); lines=[]; cur=''
    for word in words:
        test=(cur+' '+word).strip()
        if d.textlength(test,font=f1)>600 and cur: lines.append(cur); cur=word
        else: cur=test
    if cur: lines.append(cur)
    y=180
    for line in lines[:2]: d.text((75,y),line,font=f1,fill=(247,239,215)); y+=68
    d.text((75,y+10),'CATERING IN VELLORE',font=f2,fill=(241,211,139))
    d.text((75,540),'Vellore Catering  •  99404 66250',font=f2,fill=(220,215,198))
    im.save(IMG/f"{item['slug']}-og.png",optimize=True)
    return True

def write_video(item):
    ff=shutil.which('ffmpeg')
    if not ff: return False
    out=VID/f"{item['slug']}.webm"
    seed=item['slug']; a=PALETTE[n(seed)%len(PALETTE)].lstrip('#'); speed=60+n(seed,5)%90; speed2=45+n(seed,7)%70
    vf=(f"color=c=0x080704:s=480x270:r=12:d=2.6," 
        f"drawbox=x='mod(t*{speed}\\,600)-120':y=25:w=140:h=220:color=0xd6ad52@0.20:t=fill," 
        f"drawbox=x='480-mod(t*{speed2}\\,560)':y=0:w=90:h=270:color=0x{a}@0.22:t=fill," 
        f"drawbox=x=55:y=72:w=370:h=126:color=0xf1d38b@0.05:t=fill")
    cmd=[ff,'-loglevel','error','-y','-f','lavfi','-i',vf,'-an','-c:v','libvpx-vp9','-crf','47','-b:v','0','-row-mt','1',str(out)]
    subprocess.run(cmd,check=True)
    return True

def main():
    for i,item in enumerate(ITEMS,1):
        for kind,w,h in [('hero',1600,900),('gallery-1',900,700),('gallery-2',900,700),('gallery-3',900,700)]:
            sp=IMG/f"{item['slug']}-{kind}.svg"
            if not sp.exists(): sp.write_text(svg(item,kind,w,h),encoding='utf-8')
        og=IMG/f"{item['slug']}-og.png"
        if not og.exists(): write_og(item)
        vv=VID/f"{item['slug']}.webm"
        if not vv.exists(): write_video(item)
        if i%40==0: print(f'  media {i}/{len(ITEMS)}')
    print(f'generate_catalog_media: created original media for {len(ITEMS)} pages')

if __name__=='__main__': main()
