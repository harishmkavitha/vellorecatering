#!/usr/bin/env python3
"""Generate a page-wise inventory of externally hosted visual media.

Requires beautifulsoup4. Output: media-replacement-inventory.html
"""
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from fractions import Fraction
import html, re, json
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'media-replacement-inventory.html'
EXCLUDE_PREFIXES = ('tools/', 'templates/', 'partials/')


def esc(v):
    return html.escape(str(v or ''), quote=True)


def is_remote(u):
    return isinstance(u, str) and u.startswith(('https://', 'http://'))


def parse_srcset(value):
    out=[]
    for part in (value or '').split(','):
        part=part.strip()
        if not part: continue
        bits=part.split()
        u=bits[0]
        descriptor=bits[1] if len(bits)>1 else ''
        if is_remote(u): out.append((u,descriptor))
    return out


def url_dims(u):
    if not u: return (None,None)
    try:
        q=parse_qs(urlparse(u).query)
        w=int(q['w'][0]) if q.get('w') and q['w'][0].isdigit() else None
        h=int(q['h'][0]) if q.get('h') and q['h'][0].isdigit() else None
        if w and h: return w,h
    except Exception: pass
    # Pexels video names often include 1920_1080
    m=re.search(r'[_-](\d{3,5})_(\d{3,5})(?:_|\D|$)', u)
    if m:
        a,b=map(int,m.groups())
        if 200 <= a <= 10000 and 200 <= b <= 10000: return a,b
    return (None,None)


def ratio_text(w,h):
    if not w or not h: return '—'
    f=Fraction(w,h).limit_denominator(50)
    return f'{f.numerator}:{f.denominator}'


def fmt_dims(w,h):
    return f'{w} × {h} px' if w and h else 'Not specified'


def nearest_context(tag):
    section=tag.find_parent('section')
    container=section or tag.find_parent(['header','main','footer','article'])
    sec_name=''
    heading=''
    if section:
        sec_name=section.get('data-section-name') or section.get('id') or ''
    if container:
        hd=container.find(['h1','h2','h3'])
        if hd: heading=' '.join(hd.stripped_strings)
    fig=tag.find_parent('figure')
    caption=''
    if fig:
        fc=fig.find('figcaption')
        if fc: caption=' '.join(fc.stripped_strings)
    return sec_name, heading, caption


def master_dims(tag, primary, srcset):
    # Prefer the largest explicit responsive crop; otherwise the element's declared dimensions; otherwise URL dimensions.
    candidates=[]
    for u,d in srcset:
        w,h=url_dims(u)
        if w and h: candidates.append((w*h,w,h))
    aw=tag.get('width'); ah=tag.get('height')
    try:
        aw=int(str(aw)); ah=int(str(ah))
        candidates.append((aw*ah,aw,ah))
    except Exception: pass
    w,h=url_dims(primary)
    if w and h: candidates.append((w*h,w,h))
    if candidates:
        _,w,h=max(candidates)
        return w,h
    return None,None


def suggestion(page, kind, idx, slot=''):
    slug=Path(page).with_suffix('').as_posix().replace('/','-')
    slug=re.sub(r'[^a-zA-Z0-9_-]+','-',slug).strip('-').lower() or 'home'
    slot_slug=re.sub(r'[^a-zA-Z0-9_-]+','-',slot).strip('-').lower()
    stem=f'{slug}-{slot_slug}' if slot_slug and slot_slug not in slug else f'{slug}-{kind}-{idx:02d}'
    ext='mp4' if kind=='Video' else 'webp'
    return f'assets/media/replacements/{stem}.{ext}'


def asset_from_image(img, page, idx):
    primary=img.get('src','')
    srcset=parse_srcset(img.get('srcset',''))
    remote_primary=primary if is_remote(primary) else (srcset[-1][0] if srcset else '')
    if not remote_primary: return None
    sec,heading,caption=nearest_context(img)
    htmlw=img.get('width'); htmlh=img.get('height')
    try: htmlw=int(str(htmlw)); htmlh=int(str(htmlh))
    except: htmlw=htmlh=None
    sw,sh=url_dims(primary)
    mw,mh=master_dims(img,primary,srcset)
    alt=img.get('alt','').strip()
    slot=img.get('data-slot','')
    media=img.get('data-media','')
    context=caption or alt or heading or media or 'Image'
    responsive=', '.join(d for _,d in srcset if d) or '—'
    return dict(kind='Image',url=remote_primary,poster='',host=urlparse(remote_primary).netloc,
                section=sec,heading=heading,caption=caption,context=context,alt=alt,slot=slot,media=media,
                html_dims=fmt_dims(htmlw,htmlh),source_dims=fmt_dims(sw,sh),master_dims=fmt_dims(mw,mh),
                ratio=ratio_text(mw or htmlw or sw,mh or htmlh or sh),responsive=responsive,
                suggested=suggestion(page,'image',idx,slot), css_note='')


def asset_from_video(v, page, idx):
    candidates=[v.get('data-src'),v.get('src')]
    for s in v.find_all('source'):
        candidates += [s.get('data-src'),s.get('src')]
    primary=next((u for u in candidates if is_remote(u)), '')
    poster=v.get('poster','') if is_remote(v.get('poster')) else ''
    if not primary and not poster: return None
    sec,heading,caption=nearest_context(v)
    htmlw=v.get('width'); htmlh=v.get('height')
    try: htmlw=int(str(htmlw)); htmlh=int(str(htmlh))
    except: htmlw=htmlh=None
    sw,sh=url_dims(primary)
    pw,ph=url_dims(poster)
    mw,mh=(sw,sh) if sw and sh else ((htmlw,htmlh) if htmlw and htmlh else (pw,ph))
    aria=v.get('aria-label','').replace('Video:','').strip()
    slot=v.get('data-slot','')
    media=v.get('data-media','')
    context=caption or aria or heading or media or 'Video'
    classes=set(v.get('class') or [])
    parent_classes=set()
    for par in v.parents:
        if getattr(par,'attrs',None): parent_classes |= set(par.get('class') or [])
    css_note=''
    if 'media-grid' in parent_classes:
        css_note='Displayed/cropped by CSS at 16:10 (media-grid).'
    elif 'reel' in parent_classes:
        css_note='Displayed by CSS at 16:9 (reel).'
    elif 'hero__media' in parent_classes:
        css_note='Full-bleed hero; object-fit: cover, so edges may crop by screen size.'
    return dict(kind='Video',url=primary or poster,poster=poster,host=urlparse(primary or poster).netloc,
                section=sec,heading=heading,caption=caption,context=context,alt=aria,slot=slot,media=media,
                html_dims=fmt_dims(htmlw,htmlh),source_dims=fmt_dims(sw,sh),master_dims=fmt_dims(mw,mh),
                ratio=ratio_text(mw,mh),responsive='—',suggested=suggestion(page,'video',idx,slot),css_note=css_note,
                poster_dims=fmt_dims(pw,ph))


def collect():
    records=[]
    html_files=[]
    for p in sorted(ROOT.rglob('*.html')):
        rel=p.relative_to(ROOT).as_posix()
        if rel == OUT.name or rel.startswith(EXCLUDE_PREFIXES):
            continue
        html_files.append((p,rel))
    for p,rel in html_files:
        soup=BeautifulSoup(p.read_text(encoding='utf-8',errors='ignore'),'html.parser')
        title=' '.join((soup.title.stripped_strings if soup.title else []))
        h1=soup.find('h1')
        h1text=' '.join(h1.stripped_strings) if h1 else ''
        assets=[]
        idx=0
        for tag in soup.find_all(['img','video']):
            if tag.name=='img':
                has_remote=is_remote(tag.get('src')) or any(is_remote(u) for u,_ in parse_srcset(tag.get('srcset','')))
                if not has_remote: continue
                idx+=1; a=asset_from_image(tag,rel,idx)
            else:
                urls=[tag.get('src'),tag.get('data-src'),tag.get('poster')]
                for s in tag.find_all('source'): urls += [s.get('src'),s.get('data-src')]
                if not any(is_remote(u) for u in urls): continue
                idx+=1; a=asset_from_video(tag,rel,idx)
            if a: assets.append(a)
        records.append(dict(page=rel,title=title,h1=h1text,assets=assets))
    return records


def render(records):
    asset_total=sum(len(r['assets']) for r in records)
    image_total=sum(a['kind']=='Image' for r in records for a in r['assets'])
    video_total=sum(a['kind']=='Video' for r in records for a in r['assets'])
    pages_with=sum(bool(r['assets']) for r in records)
    unique_urls={a['url'] for r in records for a in r['assets'] if a['url']}
    hosts=Counter(a['host'] for r in records for a in r['assets'])

    chunks=[]
    for r in records:
        group=r['page'].split('/')[0] if '/' in r['page'] else 'root'
        count=len(r['assets'])
        page_label=r['h1'] or r['title'] or r['page']
        rows=[]
        if not r['assets']:
            rows.append('<div class="empty">No externally hosted visual image/video elements found on this page.</div>')
        for i,a in enumerate(r['assets'],1):
            thumb=a['poster'] if a['kind']=='Video' and a['poster'] else a['url']
            preview=(f'<img src="{esc(thumb)}" alt="" loading="lazy">' if thumb else '<div class="no-preview">VIDEO</div>')
            poster_line=''
            if a['kind']=='Video' and a.get('poster'):
                poster_line=f'<div><b>Poster:</b> <a href="{esc(a["poster"])}" target="_blank" rel="noopener">open poster</a> · {esc(a.get("poster_dims",""))}</div>'
            css_line=f'<div><b>Display note:</b> {esc(a["css_note"])}</div>' if a.get('css_note') else ''
            rows.append(f'''<article class="asset" data-kind="{a['kind'].lower()}">
              <div class="preview">{preview}<span class="badge">{esc(a['kind'])}</span></div>
              <div class="asset-main">
                <h3>{i}. {esc(a['context'])}</h3>
                <div class="meta-grid">
                  <div><b>Section:</b> {esc(a['section'] or '—')}</div>
                  <div><b>Section heading:</b> {esc(a['heading'] or '—')}</div>
                  <div><b>HTML dimensions:</b> {esc(a['html_dims'])}</div>
                  <div><b>Current source crop:</b> {esc(a['source_dims'])}</div>
                  <div><b>Recommended master:</b> <strong>{esc(a['master_dims'])}</strong></div>
                  <div><b>Aspect ratio:</b> {esc(a['ratio'])}</div>
                  <div><b>Responsive variants:</b> {esc(a['responsive'])}</div>
                  <div><b>Media key:</b> <code>{esc(a['media'] or '—')}</code></div>
                  <div class="wide"><b>data-slot:</b> <code>{esc(a['slot'] or '—')}</code></div>
                  <div class="wide"><b>Alt / context:</b> {esc(a['alt'] or a['caption'] or '—')}</div>
                  {poster_line}{css_line}
                  <div class="wide"><b>Suggested replacement file:</b> <code>{esc(a['suggested'])}</code></div>
                  <div class="wide source"><b>Current online source:</b> <a href="{esc(a['url'])}" target="_blank" rel="noopener">{esc(a['url'])}</a></div>
                </div>
              </div>
            </article>''')
        chunks.append(f'''<details class="page-card" data-group="{esc(group)}" data-page="{esc((r['page']+' '+page_label).lower())}" {'open' if r['page']=='index.html' else ''}>
          <summary><span class="page-path">{esc(r['page'])}</span><span class="page-name">{esc(page_label)}</span><span class="count">{count} media</span></summary>
          <div class="page-body">{''.join(rows)}</div>
        </details>''')

    host_text=', '.join(f'{h}: {n}' for h,n in hosts.most_common()) or 'None'
    return f'''<!DOCTYPE html>
<html lang="en-IN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Media Replacement Inventory | Vellore Catering World</title>
<style>
:root{{--bg:#0f1115;--panel:#171a20;--soft:#222630;--text:#f5f7fb;--muted:#aeb6c5;--line:#303642;--accent:#e0b85b;--green:#77d69b}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.45}}
a{{color:#9fc4ff}} code{{white-space:normal;overflow-wrap:anywhere;color:#f1d58e}}
.wrap{{max-width:1500px;margin:auto;padding:28px}} h1{{margin:.1em 0;font-size:clamp(2rem,4vw,3.6rem)}} .lead{{max-width:1100px;color:var(--muted)}}
.stats{{display:grid;grid-template-columns:repeat(5,minmax(130px,1fr));gap:12px;margin:24px 0}} .stat{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}} .stat b{{display:block;font-size:1.6rem;color:var(--accent)}} .stat span{{color:var(--muted);font-size:.9rem}}
.note{{background:#172019;border:1px solid #31543c;border-radius:12px;padding:14px 16px;margin:18px 0;color:#dff5e6}}
.controls{{position:sticky;top:0;z-index:20;background:rgba(15,17,21,.96);backdrop-filter:blur(10px);padding:14px 0;border-bottom:1px solid var(--line);display:flex;gap:10px;flex-wrap:wrap}}
.controls input,.controls select,.controls button{{background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:10px;padding:11px 13px;font:inherit}} .controls input{{flex:1;min-width:260px}} .controls button{{cursor:pointer}}
.page-card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;margin:14px 0;overflow:hidden}} summary{{cursor:pointer;display:grid;grid-template-columns:minmax(260px,1.1fr) 2fr auto;gap:14px;align-items:center;padding:15px 18px;background:#191d24}} summary:hover{{background:#1e232b}} .page-path{{font-weight:700;color:var(--accent);overflow-wrap:anywhere}} .page-name{{color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .count{{background:var(--soft);padding:5px 9px;border-radius:999px;font-size:.82rem}}
.page-body{{padding:14px}} .asset{{display:grid;grid-template-columns:200px 1fr;gap:16px;border-top:1px solid var(--line);padding:16px 0}} .asset:first-child{{border-top:0}} .preview{{height:135px;background:#0b0c0f;border-radius:10px;overflow:hidden;position:relative}} .preview img{{width:100%;height:100%;object-fit:cover}} .badge{{position:absolute;left:8px;top:8px;background:rgba(0,0,0,.78);padding:4px 7px;border-radius:7px;font-size:.75rem}} .asset h3{{margin:0 0 10px;font-size:1.08rem}}
.meta-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px 18px;color:#dce1e9;font-size:.9rem}} .wide{{grid-column:1/-1}} .source a{{display:inline-block;max-width:100%;overflow-wrap:anywhere}} .empty{{padding:18px;color:var(--muted);font-style:italic}}
.hidden{{display:none!important}} .legend{{color:var(--muted);font-size:.9rem;margin:9px 0 20px}} footer{{color:var(--muted);padding:28px 0}}
@media(max-width:800px){{.wrap{{padding:18px}}.stats{{grid-template-columns:repeat(2,1fr)}} summary{{grid-template-columns:1fr auto}}.page-name{{display:none}}.asset{{grid-template-columns:1fr}}.preview{{height:210px}}.meta-grid{{grid-template-columns:1fr}}.wide{{grid-column:auto}}}}
</style></head><body><div class="wrap">
<header><p style="color:var(--accent);font-weight:700;letter-spacing:.08em;text-transform:uppercase">Vellore Catering World</p><h1>Page-wise Media Replacement Inventory</h1>
<p class="lead">Use this file to prepare your own images and videos before replacing the current externally hosted media. It inventories visual <code>&lt;img&gt;</code> and <code>&lt;video&gt;</code> elements page-by-page, with context, current dimensions, responsive sizes, and suggested local filenames.</p></header>
<div class="stats"><div class="stat"><b>{len(records)}</b><span>Website HTML pages scanned</span></div><div class="stat"><b>{pages_with}</b><span>Pages using online visual media</span></div><div class="stat"><b>{asset_total}</b><span>Media placements</span></div><div class="stat"><b>{image_total}</b><span>Image placements</span></div><div class="stat"><b>{video_total}</b><span>Video placements</span></div></div>
<div class="note"><b>How to use dimensions:</b> create at least the <b>Recommended master</b> size. “HTML dimensions” are the declared intrinsic dimensions in the current markup; “Current source crop” is the remote URL crop. Responsive pages may request multiple smaller versions automatically. Video display notes identify CSS cropping such as 16:10.</div>
<p class="legend"><b>Unique primary online assets:</b> {len(unique_urls)}. <b>Hosts:</b> {esc(host_text)}. This inventory intentionally excludes local logos/icons and non-visual external iframes such as map embeds.</p>
<div class="controls"><input id="q" type="search" placeholder="Search page, service, context, asset..."><select id="group"><option value="">All page groups</option></select><select id="kind"><option value="">Images + videos</option><option value="image">Images only</option><option value="video">Videos only</option></select><button id="openAll" type="button">Open visible</button><button id="closeAll" type="button">Close all</button></div>
<main id="pages">{''.join(chunks)}</main>
<footer>Generated from the current Vellore Catering World project. Re-run <code>python tools/generate_media_replacement_inventory.py</code> after major HTML/media changes.</footer>
</div><script>
const cards=[...document.querySelectorAll('.page-card')], q=document.getElementById('q'), group=document.getElementById('group'), kind=document.getElementById('kind');
[...new Set(cards.map(c=>c.dataset.group))].sort().forEach(g=>{{let o=document.createElement('option');o.value=g;o.textContent=g;group.appendChild(o)}});
function filter(){{const s=q.value.trim().toLowerCase(),g=group.value,k=kind.value;cards.forEach(c=>{{let pageOK=(!s||c.textContent.toLowerCase().includes(s))&&(!g||c.dataset.group===g);let assets=[...c.querySelectorAll('.asset')], any=false;assets.forEach(a=>{{let ok=pageOK&&(!k||a.dataset.kind===k)&&(!s||a.textContent.toLowerCase().includes(s)||c.dataset.page.includes(s));a.classList.toggle('hidden',!ok);if(ok)any=true}});let empty=c.querySelector('.empty');let show=pageOK&&(assets.length?any:!k);c.classList.toggle('hidden',!show)}})}}
q.addEventListener('input',filter);group.addEventListener('change',filter);kind.addEventListener('change',filter);document.getElementById('openAll').onclick=()=>cards.filter(c=>!c.classList.contains('hidden')).forEach(c=>c.open=true);document.getElementById('closeAll').onclick=()=>cards.forEach(c=>c.open=false);
</script></body></html>'''

if __name__=='__main__':
    records=collect()
    OUT.write_text(render(records),encoding='utf-8')
    print(f'Wrote {OUT} with {len(records)} pages and {sum(len(r["assets"]) for r in records)} media placements.')
