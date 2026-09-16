#!/usr/bin/env python3
"""Replace remote Pexels media in legacy master pages with original local procedural assets."""
from __future__ import annotations
import hashlib, html, re, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
IMG=ROOT/'assets/img/master-generated'; VID=ROOT/'assets/video/master-generated'
IMG.mkdir(parents=True,exist_ok=True); VID.mkdir(parents=True,exist_ok=True)
SKIP={'partials','tools','templates','data','assets','.git','node_modules'}
PEX_IMG=re.compile(r'https://images\.pexels\.com/[^\s"\'<>]+')
PEX_VID=re.compile(r'https://videos\.pexels\.com/[^\s"\'<>]+')
IMG_TAG=re.compile(r'<img\b[^>]*>',re.I)
VIDEO_TAG=re.compile(r'<video\b[^>]*>',re.I)

def attr(tag,name):
    m=re.search(rf'\b{name}="([^"]*)"',tag,re.I); return html.unescape(m.group(1)) if m else ''
def dim(tag,name,default):
    try:return max(1,int(attr(tag,name) or default))
    except:return default

def svg(path,w,h,label,seed):
    colors=['#7A231D','#5C3424','#3F4A2C','#5B274F','#2B4A45','#6E5123']
    n=int(hashlib.sha256(seed.encode()).hexdigest()[:8],16); ac=colors[n%len(colors)]
    safe=html.escape(label[:54] or 'Vellore Catering')
    fs=max(20,min(52,int(w/18)))
    art=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>{safe}</title><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#070604"/><stop offset="1" stop-color="{ac}"/></linearGradient><radialGradient id="r"><stop stop-color="#D6AD52" stop-opacity=".28"/><stop offset="1" stop-color="#D6AD52" stop-opacity="0"/></radialGradient></defs><rect width="100%" height="100%" fill="url(#g)"/><circle cx="78%" cy="28%" r="35%" fill="url(#r)"/><ellipse cx="70%" cy="58%" rx="23%" ry="26%" fill="#080704" stroke="#D6AD52" stroke-width="3"/><path d="M52% 65% Q70% 32% 88% 65%" fill="none" stroke="#F1D38B" stroke-width="6" stroke-linecap="round"/><circle cx="66%" cy="57%" r="7%" fill="#D6AD52" opacity=".22"/><circle cx="76%" cy="57%" r="5%" fill="#D6AD52" opacity=".35"/><text x="8%" y="48%" fill="#F7EFD7" font-family="Georgia,serif" font-size="{fs}" font-weight="700">{safe}</text><text x="8%" y="56%" fill="#F1D38B" font-family="Arial,sans-serif" font-size="{max(14,int(fs*.38))}" letter-spacing="2">ORIGINAL SITE ILLUSTRATION</text></svg>'''
    path.write_text(art,encoding='utf-8')

def localize_img_tag(tag,page,index):
    if not PEX_IMG.search(tag): return tag
    alt=attr(tag,'alt') or 'Vellore Catering visual'; w=dim(tag,'width',1000); h=dim(tag,'height',700)
    key=f'{page.relative_to(ROOT)}|{index}|{alt}|{w}x{h}'; name=hashlib.sha1(key.encode()).hexdigest()[:14]+'.svg'; path=IMG/name
    if not path.exists(): svg(path,w,h,alt,key)
    prefix='../'*((page.relative_to(ROOT).as_posix()).count('/'))
    loc=prefix+'assets/img/master-generated/'+name
    tag=re.sub(r'\bsrc="[^"]*"',f'src="{loc}"',tag,count=1)
    tag=re.sub(r'\s+srcset="[^"]*"','',tag)
    tag=re.sub(r'\s+sizes="[^"]*"','',tag)
    return tag

def make_video(path,seed):
    ff=shutil.which('ffmpeg')
    if not ff: return
    n=int(hashlib.sha256(seed.encode()).hexdigest()[:8],16); ac=['7A231D','5C3424','3F4A2C','5B274F','2B4A45','6E5123'][n%6]
    sp=70+n%80
    vf=f"color=c=0x080704:s=640x360:r=12:d=3,drawbox=x='mod(t*{sp}\\,780)-160':y=30:w=180:h=300:color=0xd6ad52@0.18:t=fill,drawbox=x='640-mod(t*65\\,720)':y=0:w=120:h=360:color=0x{ac}@0.18:t=fill"
    subprocess.run([ff,'-loglevel','error','-y','-f','lavfi','-i',vf,'-an','-c:v','libvpx-vp9','-crf','47','-b:v','0',str(path)],check=True)

def localize_video_tag(tag,page,index):
    if not PEX_VID.search(tag): return tag
    key=f'{page.relative_to(ROOT)}|video|{index}'; name=hashlib.sha1(key.encode()).hexdigest()[:14]+'.webm'; path=VID/name
    if not path.exists(): make_video(path,key)
    prefix='../'*((page.relative_to(ROOT).as_posix()).count('/'))
    loc=prefix+'assets/video/master-generated/'+name
    tag=PEX_VID.sub(loc,tag)
    return tag

def main():
    pages=[p for p in ROOT.rglob('*.html') if p.relative_to(ROOT).parts[0] not in SKIP]
    changed=0
    for page in pages:
        text=page.read_text(encoding='utf-8')
        i=[0]
        def ri(m): i[0]+=1; return localize_img_tag(m.group(0),page,i[0])
        text2=IMG_TAG.sub(ri,text)
        v=[0]
        def rv(m): v[0]+=1; return localize_video_tag(m.group(0),page,v[0])
        text2=VIDEO_TAG.sub(rv,text2)
        text2=text2.replace('<link rel="preconnect" href="https://images.pexels.com" crossorigin>\n','')
        if text2!=text: page.write_text(text2,encoding='utf-8'); changed+=1
    print(f'replace_remote_media: rewrote {changed} pages; generated {len(list(IMG.glob("*.svg")))} image assets and {len(list(VID.glob("*.webm")))} video assets')
if __name__=='__main__': main()
