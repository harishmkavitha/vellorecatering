#!/usr/bin/env python3
"""Rewrite generated page copy so each public page has materially distinct editorial text.

The script keeps navigation, links, forms, media and layout intact. It rewrites the main
editorial headings/paragraphs/list copy on service, servicing-area and generated blog pages,
then updates per-page meta descriptions. Output is deterministic from the page path.
"""
from __future__ import annotations

import hashlib, json, re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

CAT_FOCUS = {
    "Wedding & Marriage": ["ceremony transitions", "family hospitality", "muhurtham timing", "reception guest flow", "elder-friendly dining", "multi-meal sequencing"],
    "Religious & Traditional": ["ritual timing", "traditional service etiquette", "sattvic choices", "banana-leaf sequencing", "prayer-to-meal transition", "family customs"],
    "Birthday & Family": ["mixed-age portions", "child-friendly choices", "cake-and-meal timing", "informal service", "family seating", "snack-to-dinner flow"],
    "Corporate & Business": ["punctual service windows", "meeting schedules", "professional presentation", "portion consistency", "short breaks", "workspace logistics"],
    "Education": ["student queue movement", "age-appropriate portions", "batch service", "campus access", "short meal windows", "safe replenishment"],
    "Events & Entertainment": ["high-volume movement", "crew meals", "backstage timing", "public counters", "fast replenishment", "programme schedules"],
    "Social & Community": ["community-scale portions", "inclusive menus", "efficient queues", "shared dining", "budget discipline", "volunteer coordination"],
    "Healthcare & Institutional": ["scheduled meal delivery", "simple nutrition", "controlled preparation", "clear labelling", "repeatable portions", "institutional access"],
    "Religious Festivals & Seasonal": ["festival timing", "seasonal dishes", "crowd service", "traditional sweets", "fast replenishment", "special-day demand"],
    "Food Service Formats": ["service speed", "counter placement", "plate movement", "holding time", "staff deployment", "venue layout"],
    "Cuisine-Based": ["regional flavour", "course balance", "authentic accompaniments", "spice calibration", "menu coherence", "dessert pairing"],
    "Specialized & Dietary": ["ingredient clarity", "dietary separation", "guest labelling", "cross-contact awareness", "balanced alternatives", "advance requirement capture"],
    "Travel & Venue": ["arrival timing", "loading access", "food holding", "portable service", "venue restrictions", "transport sequence"],
    "Religious & Spiritual": ["quiet service", "sattvic preference", "spiritual etiquette", "community meal flow", "simple presentation", "prayer schedules"],
    "Retail & Commercial": ["repeatable production", "counter throughput", "commercial portions", "packaging flow", "peak-hour demand", "stock planning"],
    "Special Occasions": ["occasion styling", "guest comfort", "flexible timing", "signature dishes", "presentation moments", "host priorities"],
}

AREA_FOCUS = {
    "Town / Administrative area": ["town traffic", "venue access windows", "guest arrival peaks", "parking coordination", "local hall schedules", "delivery routing"],
    "Locality / Village": ["street access", "family venues", "neighbourhood timing", "local hall layout", "home-function setup", "last-mile delivery"],
    "Road / Junction / Landmark": ["junction traffic", "exact entrance identification", "loading space", "roadside parking", "signage for crews", "time-sensitive unloading"],
}

THEMES = {
    "menu": ["course balance", "portion rhythm", "regional pairing", "spice level", "meal progression", "guest familiarity", "seasonal suitability", "service temperature"],
    "guest": ["arrival pattern", "age mix", "elder comfort", "child portions", "dietary notes", "queue behaviour", "seating turnover", "late arrivals"],
    "venue": ["kitchen access", "loading route", "serving space", "power points", "water access", "waste route", "dining layout", "parking window"],
    "timing": ["setup lead time", "first-service target", "ritual pauses", "programme delays", "replenishment interval", "closing time", "dispatch window", "cleanup sequence"],
    "staff": ["service stations", "counter ownership", "supervisor hand-off", "replenishment roles", "clearing zones", "guest assistance", "back-of-house movement", "shift timing"],
    "counter": ["queue footprint", "utility access", "made-to-order speed", "batch size", "garnish station", "plate pickup", "counter signage", "waste control"],
    "diet": ["ingredient disclosure", "separate utensils", "clear labels", "vegetarian separation", "allergy notes", "Jain-friendly planning", "lighter alternatives", "special portions"],
    "hygiene": ["covered transport", "clean water", "hand-wash access", "hot holding", "cold holding", "surface hygiene", "batch freshness", "safe clearing"],
    "price": ["guest count", "course depth", "staffing", "equipment", "distance", "live counters", "service duration", "special ingredients"],
    "breakfast": ["tiffin sequence", "filter coffee timing", "hot-item batches", "chutney replenishment", "early setup", "quick seating", "light sweets", "morning beverages"],
    "lunch": ["rice service", "gravy sequence", "poriyal balance", "curd finish", "sweet timing", "banana-leaf order", "second servings", "water circulation"],
    "dinner": ["starter pacing", "main-course flow", "breads and gravies", "dessert finish", "late guest arrivals", "lighting around counters", "beverage service", "closing batches"],
    "beverage": ["welcome drinks", "water stations", "filter coffee", "tea service", "fresh juice", "refill frequency", "cup disposal", "temperature control"],
    "booking": ["date confirmation", "venue details", "guest estimate", "menu discussion", "service format", "advance requirements", "final headcount", "event-day contact"],
    "local": ["venue identification", "route planning", "local timing", "service access", "guest movement", "parking constraints", "delivery sequence", "setup footprint"],
    "general": ["event priorities", "practical coordination", "guest comfort", "service clarity", "menu fit", "venue readiness", "timing discipline", "host communication"],
}

OPENERS = [
    "A useful way to plan {subject} is to begin with {focus}",
    "For {subject}, {focus} deserves attention before the menu is locked",
    "The strongest plan for {subject} connects {focus} with the actual event schedule",
    "Instead of treating {subject} as a standard package, start by checking {focus}",
    "One practical decision for {subject} is how {focus} will work at the venue",
    "When organising {subject}, the early discussion should make {focus} explicit",
    "A page-specific priority for {subject} is {focus}, because it affects service on the day",
    "Planning {subject} becomes clearer once {focus} is agreed with the host",
    "For this {subject} requirement, {focus} is more useful than adding dishes without a service plan",
    "The operating plan behind {subject} should translate {focus} into a clear action for the team",
    "In {subject}, {focus} is best decided alongside guest count and venue conditions",
    "A sensible brief for {subject} records {focus} before quantities and staffing are finalised",
]

FOLLOWUPS = [
    "That choice influences {detail}, so it should be confirmed before production quantities are set.",
    "It also changes how the team handles {detail} during setup and service.",
    "From there, {detail} can be adjusted without forcing the event into a generic format.",
    "This keeps {detail} aligned with the host's priorities rather than with a fixed template.",
    "The same decision gives the kitchen and service crew a clearer reference for {detail}.",
    "When this is settled early, {detail} is easier to coordinate and explain to everyone involved.",
    "That creates a practical basis for choosing {detail} with fewer last-minute changes.",
    "It is then easier to match {detail} to the real pace of the function.",
    "The benefit is a more deliberate approach to {detail}, especially when the venue has constraints.",
    "This detail should appear in the final event brief together with {detail}.",
    "Used well, that decision prevents {detail} from becoming an afterthought on the event day.",
    "The host can then review {detail} against budget, timing and guest expectations.",
]

LEAD_PATTERNS = [
    "{subject} is planned around {descriptor}. This page focuses on {focus}, with the menu and service format shaped around the actual venue and guest profile.",
    "Use this {subject} page to plan {descriptor}. The emphasis here is {focus}, so timing, portions and service choices can be discussed as one coordinated brief.",
    "For {subject}, the relevant starting point is {descriptor}. Particular attention is given to {focus} instead of relying on a standard event package.",
    "This guide to {subject} covers {descriptor}. Its planning angle is {focus}, helping the host connect food choices with how the event will really run.",
    "{subject} can vary considerably from one function to another. Here, {descriptor} is considered through the lens of {focus}, guest comfort and venue practicality.",
    "The purpose of this {subject} page is to make {descriptor} easier to organise. It prioritises {focus} and a service sequence that fits the function.",
]

HEADING_PATTERNS = [
    "{subject}: a plan built around {focus}",
    "How {focus} shapes {subject}",
    "Practical decisions for {subject}",
    "A clearer service brief for {subject}",
    "Planning {subject} beyond a standard package",
    "What to settle first for {subject}",
    "Service details that matter for {subject}",
    "Building the right flow for {subject}",
    "From menu idea to service plan: {subject}",
    "Making {subject} work at the actual venue",
    "Guest experience priorities for {subject}",
    "Coordinating food, timing and setup for {subject}",
]

SUBHEAD_PATTERNS = [
    "Focus on {focus}", "Plan {focus} early", "A decision about {focus}", "Check {focus} at the venue",
    "Coordinate {focus}", "Keep {focus} practical", "Confirm {focus} with the host", "Match {focus} to the event",
    "Use {focus} as a planning checkpoint", "Review {focus} before service", "Make {focus} measurable", "Agree the approach to {focus}",
]

BULLET_PATTERNS = [
    "Confirm {focus} for {subject} before the final event brief is closed.",
    "Match {focus} to the guest count, venue and timing for {subject}.",
    "Record the decision on {focus} so the {subject} team has one clear instruction.",
    "Review {focus} with the host when finalising {subject} quantities and service flow.",
    "Keep {focus} practical for the available setup space during {subject}.",
    "Use {focus} to guide staffing and replenishment choices for {subject}.",
    "Check whether {focus} needs a separate service station for {subject}.",
    "Discuss {focus} early if it can affect cost, timing or equipment for {subject}.",
    "Link {focus} to the serving sequence rather than treating it as an isolated menu choice.",
    "Include {focus} in the event-day checklist for {subject}.",
]

CATEGORY_WORDS = {
    "Wedding & Marriage": "wedding function",
    "Religious & Traditional": "traditional function",
    "Birthday & Family": "family celebration",
    "Corporate & Business": "business event",
    "Education": "campus event",
    "Events & Entertainment": "public event",
    "Social & Community": "community gathering",
    "Healthcare & Institutional": "institutional meal service",
    "Religious Festivals & Seasonal": "festival gathering",
    "Food Service Formats": "catering format",
    "Cuisine-Based": "cuisine-led event",
    "Specialized & Dietary": "special-diet event",
    "Travel & Venue": "venue-led event",
    "Religious & Spiritual": "spiritual gathering",
    "Retail & Commercial": "commercial food service",
    "Special Occasions": "special occasion",
}


def hnum(key: str, modulo: int) -> int:
    return int(hashlib.sha256(key.encode('utf-8')).hexdigest()[:16], 16) % modulo

def pick(seq, key: str):
    return seq[hnum(key, len(seq))]

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def clean_descriptor(s: str, subject: str) -> str:
    s = norm(s).strip(' .')
    if not s:
        return f"the food, timing and guest experience required for {subject.lower()}"
    s = re.sub(r"\bFor [^.;]{0,100}(?:\.|$)", "", s, flags=re.I)
    s = re.sub(r"\bThe final [^.;]{0,120}(?:\.|$)", "", s, flags=re.I)
    s = norm(s).strip(' .')
    if len(s) > 180:
        s = s[:180].rsplit(' ',1)[0]
    return s[0].lower()+s[1:] if s and s[0].isupper() else s

def theme_for(text: str) -> str:
    x=text.lower()
    checks=[
        ('breakfast',['breakfast','tiffin','morning']),('lunch',['lunch','meals','banana-leaf','banana leaf']),('dinner',['dinner','reception','evening']),
        ('beverage',['beverage','coffee','tea','juice','water']),('diet',['diet','jain','allerg','vegan','vegetarian','non-vegetarian']),
        ('counter',['counter','live station','queue']),('venue',['venue','hall','access','parking','kitchen','setup']),('timing',['timing','schedule','time','muhurtham','ritual']),
        ('staff',['staff','service crew','server','replenish','clearing']),('hygiene',['hygiene','safe','clean','temperature','handling']),
        ('price',['price','cost','quote','quotation','budget']),('booking',['book','enquiry','whatsapp','confirm']),('guest',['guest','children','elder','family','crowd']),
        ('menu',['menu','course','dish','cuisine','sweet','starter','rice','gravy']),('local',['local','area','road','junction','town','village']),
    ]
    for k,words in checks:
        if any(w in x for w in words): return k
    return 'general'

def make_context(path: Path, soup: BeautifulSoup, catalog_map, area_map):
    rel=path.relative_to(ROOT).as_posix()
    h1=soup.find('h1')
    title=norm(h1.get_text(' ',strip=True) if h1 else (soup.title.get_text(' ',strip=True) if soup.title else path.stem))
    if rel.startswith('services/') and path.name!='index.html':
        item=catalog_map.get(path.stem,{})
        subject=item.get('catering_type') or re.sub(r'-in-vellore$','',path.stem).replace('-',' ').title()
        cat=(item.get('categories') or ['Special Occasions'])[0]
        descriptor=item.get('description') or f"the specific requirements of {subject.lower()}"
        focuses=CAT_FOCUS.get(cat,CAT_FOCUS['Special Occasions'])
        return {'kind':'service','subject':subject,'title':title,'descriptor':clean_descriptor(descriptor,subject),'focuses':focuses,'category':cat,'rel':rel}
    if rel.startswith('servicing-areas/') and path.name!='index.html':
        row=area_map.get(path.stem,{})
        area=row.get('area') or title.replace('Catering in ','')
        atype=row.get('type') or 'Locality / Village'
        subject=f"catering in {area}"
        descriptor=f"functions hosted around {area}, with the exact venue and service window confirmed before the menu is finalised"
        return {'kind':'area','subject':subject,'title':title,'descriptor':descriptor,'focuses':AREA_FOCUS.get(atype,AREA_FOCUS['Locality / Village']),'category':atype,'area':area,'rel':rel}
    if rel.startswith('guides/blogs/'):
        subject=title.split('|')[0].strip()
        first=soup.find('p')
        desc=clean_descriptor(first.get_text(' ',strip=True) if first else '',subject)
        # derive unique topical focuses from title + generic operational themes
        words=[w for w in re.findall(r"[A-Za-z][A-Za-z-]{3,}", subject.lower()) if w not in {'vellore','catering','guide','practical','decisions','events','event'}]
        topical=[]
        for w in words[:4]: topical.append(w.replace('-',' ')+' planning')
        topical += ['decision sequence','host checklist','service trade-offs','venue fit','guest communication','final confirmation']
        return {'kind':'blog','subject':subject,'title':title,'descriptor':desc or f"practical decisions connected with {subject.lower()}",'focuses':topical[:8],'category':'Guide article','rel':rel}
    return None

def focus(ctx, idx, extra=''):
    base=ctx['focuses']
    f=pick(base, ctx['rel']+f'|focus|{idx}|{extra}')
    return f

def detail_for(text, ctx, idx):
    theme=theme_for(text)
    vals=THEMES[theme]
    return pick(vals,ctx['rel']+f'|detail|{idx}|{theme}|{text[:30]}')

def rewrite_text(original: str, ctx, idx: int, kind: str) -> str:
    subject=ctx['subject']
    foc=focus(ctx,idx,original[:30])
    det=detail_for(original,ctx,idx)
    if kind=='lead':
        return pick(LEAD_PATTERNS,ctx['rel']+f'|lead|{idx}').format(subject=subject,descriptor=ctx['descriptor'],focus=foc)
    if kind=='kicker':
        labels=['Planning note','Service focus','Page-specific guidance','Event detail','Practical checkpoint','Host brief','Operational focus','Local planning note']
        return f"{pick(labels,ctx['rel']+f'|kick|{idx}')} · {foc.title()}"
    if kind=='sectioncopy':
        return f"For {subject}, this section concentrates on {foc}; the recommendation should be checked against {det}, guest count and the actual venue before confirmation."
    if kind=='h2':
        return pick(HEADING_PATTERNS,ctx['rel']+f'|h2|{idx}').format(subject=subject.title() if ctx['kind']=='area' else subject,focus=foc)
    if kind=='h3':
        return pick(SUBHEAD_PATTERNS,ctx['rel']+f'|h3|{idx}').format(focus=foc.title())
    if kind=='li':
        return pick(BULLET_PATTERNS,ctx['rel']+f'|li|{idx}').format(subject=subject,focus=foc)
    if kind=='summary':
        qs=[
            "What should be confirmed first for {subject}?","How should {focus} be handled for {subject}?","Can {subject} be adjusted around {focus}?",
            "What venue detail matters most for {subject}?","How is the final plan for {subject} confirmed?","When should {focus} be discussed for {subject}?"
        ]
        return pick(qs,ctx['rel']+f'|sum|{idx}').format(subject=subject,focus=foc)
    # paragraph: use semantic clue from the original while removing obvious repeated suffixes
    core=clean_descriptor(original,subject)
    op=pick(OPENERS,ctx['rel']+f'|p1|{idx}|{original[:20]}').format(subject=subject,focus=foc)
    fu=pick(FOLLOWUPS,ctx['rel']+f'|p2|{idx}|{original[-20:]}').format(detail=det)
    # every third paragraph retains one concise fact from the source when useful
    if core and len(core.split())>=4 and idx%3==0:
        fact=core.rstrip('.')
        if len(fact)>140: fact=fact[:140].rsplit(' ',1)[0]
        return f"{op}. In this context, {fact}. {fu}"
    return f"{op}. {fu}"

def replace_simple_text(tag, text):
    # Only replace tags whose content is plain text, to preserve anchors/icons/structured markup.
    if any(getattr(c,'name',None) for c in tag.children):
        return False
    tag.string=text
    return True

def update_meta(soup, ctx):
    desc = f"{ctx['title']}: page-specific guidance on {focus(ctx,901)}, {focus(ctx,902)} and practical event coordination for Vellore enquiries."
    desc=desc[:158].rstrip(' ,.;')+'.'
    m=soup.find('meta',attrs={'name':'description'})
    if m: m['content']=desc
    og=soup.find('meta',attrs={'property':'og:description'})
    if og: og['content']=desc
    tw=soup.find('meta',attrs={'name':'twitter:description'})
    if tw: tw['content']=desc

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument('--group', choices=['services','areas','blogs','all'], default='all')
    args=ap.parse_args()
    catalog=json.loads((ROOT/'data/catering-catalog.json').read_text(encoding='utf-8'))['items']
    catalog_map={x['slug']:x for x in catalog}
    df=pd.read_excel(ROOT/'data/source/Vellore_and_Nearby_500_Areas.xlsx')
    area_map={}
    for _,r in df.iterrows():
        area=str(r['Area / Locality']).strip()
        slug=re.sub(r'[^a-z0-9]+','-',area.lower()).strip('-')+'-catering'
        area_map[slug]={'area':area,'type':str(r['Area Type']).strip(),'region':str(r['Region']).strip()}

    targets=[]
    if args.group in ('services','all'):
        targets += [p for p in (ROOT/'services').glob('*.html') if p.name!='index.html']
    if args.group in ('areas','all'):
        targets += [p for p in (ROOT/'servicing-areas').glob('*.html') if p.name!='index.html']
    if args.group in ('blogs','all'):
        targets += list((ROOT/'guides'/'blogs').glob('*.html'))
    changed=0
    for path in targets:
        soup=BeautifulSoup(path.read_text(encoding='utf-8',errors='ignore'),'html.parser')
        ctx=make_context(path,soup,catalog_map,area_map)
        if not ctx: continue
        mainel=soup.find('main')
        if not mainel: continue
        idx=0
        for tag in mainel.find_all(['p','h2','h3','li','summary']):
            if tag.find_parent(['nav','form']): continue
            # do not rewrite CTA/link-only text or content with child elements
            original=norm(tag.get_text(' ',strip=True))
            if not original: continue
            idx+=1
            cls=set(tag.get('class') or [])
            if tag.name=='p' and 'lead' in cls: typ='lead'
            elif tag.name=='p' and ('section-kicker' in cls or 'eyebrow' in cls): typ='kicker'
            elif tag.name=='p' and 'section-copy' in cls: typ='sectioncopy'
            elif tag.name in {'h2','h3','li','summary'}: typ=tag.name
            else: typ='p'
            if not replace_simple_text(tag,rewrite_text(original,ctx,idx,typ)):
                # For a paragraph containing links, keep links intact and only add a unique aria-independent sentence before it.
                if tag.name=='p' and tag.find('a'):
                    prefix=rewrite_text(original,ctx,idx,'sectioncopy')+' '
                    tag.insert(0,NavigableString(prefix))
        update_meta(soup,ctx)
        path.write_text(str(soup),encoding='utf-8')
        changed+=1
    print(f"Rewrote {changed} generated public pages")

if __name__=='__main__': main()
