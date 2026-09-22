#!/usr/bin/env python3
"""generate_area_blog_site.py — servicing-area and blog pages.   Version: V2

V2: skips writing the generated SVG artwork when data/media-library.json exists,
because tools/stock_media.py replaces those slots with real photos.
"""
from __future__ import annotations
import csv, hashlib, html, json, re
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import quote
import openpyxl
from sitekit import CONFIG, asset_url, breadcrumb_schema, business_schema, faq_schema, head_meta, jsonld, page_shell, page_url, wa_form, website_schema

ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT/'data/source/Vellore_and_Nearby_500_Areas.xlsx'
CAT=ROOT/'data/catering-catalog.json'
AREA_DIR=ROOT/'servicing-areas'; BLOG_DIR=ROOT/'guides/blogs'
AREA_MEDIA=ROOT/'assets/img/areas'; BLOG_MEDIA=ROOT/'assets/img/blogs'
E=html.escape; SITE=CONFIG['site_url'].rstrip('/'); TODAY=date.today().isoformat(); BLOG_COUNT=500

CORE=[
 ('Wedding Catering','services/wedding-catering-in-vellore.html','Wedding menus, service timing, staffing and guest-flow planning.'),
 ('Birthday Catering','services/birthday-party-catering-in-vellore.html','Birthday menus for children, adults and family celebrations.'),
 ('Seemandham Catering','services/seemandham-catering-in-vellore.html','Traditional seemandham menu planning around ritual and family timings.'),
 ('Other Caterings','services/other-caterings-in-vellore.html','Browse the complete Vellore catering service catalogue.'),
]
CUISINES=['Tamil vegetarian','South Indian','Chettinad-inspired','North Indian','Andhra-style','Kerala-style','Jain-friendly','multi-cuisine','traditional tiffin','biryani-led non-vegetarian']
COUNTERS=['mini dosa and chutney','chaat','filter coffee','fresh juice','paniyaram','parotta','idiyappam','dessert plating','mocktails','ice cream and toppings','fresh fruit','soup and starters']
STYLES=['banana-leaf service','buffet service','plated dining','counter service','boxed meals','sit-down family service']
STARTERS=['mini idli with podi','vegetable cutlet','paneer pepper fry','chilli baby corn','mushroom pepper fry','chicken 65','veg spring roll','medhu vadai']
MAINS=['sambar rice with poriyal','vegetable biryani with kurma','traditional meals with rasam','ghee rice with vegetable kurma','chicken biryani with onion raita','mini tiffin combination','lemon rice with potato roast','chapati with paneer gravy']
SWEETS=['badam halwa','gulab jamun','paal payasam','kesari','jangiri','carrot halwa','rasmalai','elaneer payasam']
DRINKS=['filter coffee','masala tea','fresh lime','rose milk','badam milk','buttermilk','fresh juice','welcome mocktail']
AREA_CTX={
 'Town / Administrative area':('town traffic, venue loading windows and guest arrival peaks',['marriage halls','hotels','community halls','office spaces','private residences']),
 'Locality / Village':('last-mile access, service-equipment movement and meal timing around local functions',['homes','marriage halls','temple premises','community spaces','outdoor compounds']),
 'Road / Junction / Landmark':('parking, loading access, junction traffic and the exact venue entrance',['function halls','commercial venues','homes','institutions','event spaces']),
 'Forest / Census locality':('route confirmation, travel time, safe food transport and an agreed service setup point',['private properties','community spaces','outdoor venues','institutional premises','family event locations']),
}
CAT_CTX={
 'Wedding & Marriage':'ceremonial timing, guest hospitality and multi-course service',
 'Religious & Traditional':'ritual timing, traditional preferences and orderly service',
 'Birthday & Family':'age-mixed guests, easy-to-serve favourites and flexible timing',
 'Corporate & Business':'punctual service windows, professional presentation and predictable portions',
 'Education':'queue flow, batch service, safety and age-appropriate menu planning',
 'Events & Entertainment':'high-volume movement, backstage timing and quick replenishment',
 'Social & Community':'community-scale portions, practical menus and efficient distribution',
 'Healthcare & Institutional':'controlled preparation, dependable timing and practical nutrition',
 'Religious Festivals & Seasonal':'festival traditions, seasonal favourites and crowd-ready service',
 'Food Service Formats':'service speed, holding time, transport and setup',
 'Cuisine-Based':'authentic flavour balance, course sequence and menu coherence',
 'Specialized & Dietary':'ingredient clarity, dietary communication and careful menu choices',
 'Travel & Venue':'travel timing, venue access, holding temperature and service setup',
 'Religious & Spiritual':'simple service, spiritual-setting etiquette and traditional preferences',
 'Retail & Commercial':'repeatable production, service consistency and practical packaging',
 'Special Occasions':'occasion-led presentation, flexible timing and memorable food moments',
}
FORMATS=['Planning Guide','Menu Guide','Guest-Count Guide','Service Guide','Checklist','Mistakes to Avoid','Food Counter Guide','Budget Planning Guide','Timing Guide','Venue Coordination Guide']
ANGLES=['menu balance','guest comfort','service timing','food quantity planning','live counters','traditional service','buffet flow','family preferences','dietary requests','venue logistics','morning functions','evening functions','summer events','monsoon planning','large guest counts','small gatherings','vegetarian menus','mixed menus','dessert planning','beverage planning']


def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def hnum(k,m): return int(hashlib.sha256(k.encode()).hexdigest()[:14],16)%m
def pick(seq,k,o=0): return seq[hnum(f'{k}|{o}',len(seq))]
def picks(seq,k,n,start=0):
 out=[]; i=start
 while len(out)<n:
  v=pick(seq,k,i); i+=1
  if v not in out: out.append(v)
 return out

def shead(k,t,c=''):
 return f'<div class="section-head"><p class="section-kicker">{E(k)}</p><h2 class="gilded" data-reveal>{E(t)}</h2>{f"<p class=\"section-copy\">{E(c)}</p>" if c else ""}</div>'
def cards(items,cls='content-cards'):
 return f'<div class="{cls}">'+''.join(f'<article class="content-card" data-reveal><h3>{E(a)}</h3><p>{E(b)}</p></article>' for a,b in items)+'</div>'
def bullets(items): return '<ul class="checks checks--grid">'+''.join(f'<li data-reveal>{E(x)}</li>' for x in items)+'</ul>'
def section(num,name,body,band=False,id=''):
 return f'<section class="section{" band" if band else ""}" data-section="{num}" data-section-name="{E(name)}"{f" id=\"{id}\"" if id else ""}><div class="container">{body}</div></section>'

def read_areas():
 wb=openpyxl.load_workbook(SRC,data_only=True,read_only=True); ws=wb[wb.sheetnames[0]]; rows=list(ws.iter_rows(values_only=True)); hdr=list(rows[0]); out=[]; used=set()
 for r in rows[1:]:
  d=dict(zip(hdr,r)); name=str(d['Area / Locality']).strip(); base=slug(name); s=base; i=2
  while s in used: s=f'{base}-{i}'; i+=1
  used.add(s); out.append({'sno':int(d['S.No']),'name':name,'search_phrase':str(d['Search Phrase']).strip(),'region':str(d['Region']).strip(),'area_type':str(d['Area Type']).strip(),'slug':s,'output':f'servicing-areas/{s}-catering.html'})
 return out

def catalog(): return json.loads(CAT.read_text(encoding='utf-8'))['items']

def svg(path,title,subtitle,key,kind='area'):
 if (ROOT/'data/media-library.json').exists(): return  # V2: real photos via stock_media.py
 hue=30+hnum(key,25); dots=''.join(f'<circle cx="{80+hnum(key+str(i)+"x",1040)}" cy="{60+hnum(key+str(i)+"y",510)}" r="{2+hnum(key+str(i)+"r",5)}" fill="#e0b65f" opacity=".{12+hnum(key+str(i)+"o",28)}"/>' for i in range(16))
 label='LOCAL SERVICE AREA' if kind=='area' else 'VELLORE CATERING GUIDE'
 text=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="{E(title)}"><defs><radialGradient id="g" cx="82%" cy="18%" r="80%"><stop offset="0" stop-color="hsl({hue} 45% 20%)"/><stop offset=".55" stop-color="#0b0906"/><stop offset="1" stop-color="#020202"/></radialGradient><linearGradient id="gold"><stop stop-color="#b98528"/><stop offset=".5" stop-color="#f2d17c"/><stop offset="1" stop-color="#a66f1e"/></linearGradient></defs><rect width="1200" height="630" fill="url(#g)"/>{dots}<rect x="70" y="66" width="1060" height="498" rx="30" fill="none" stroke="#d6ad52" opacity=".28"/><text x="90" y="125" fill="#d6ad52" font-size="20" font-family="Arial" letter-spacing="5">{label}</text><text x="90" y="280" fill="url(#gold)" font-size="54" font-family="Georgia" font-weight="700">{E(title[:55])}</text><text x="92" y="332" fill="#f2eadb" opacity=".86" font-size="23" font-family="Arial">{E(subtitle[:100])}</text><line x1="92" y1="385" x2="480" y2="385" stroke="#d6ad52" opacity=".5"/><text x="92" y="440" fill="#f2eadb" font-size="21" font-family="Arial">Wedding • Birthday • Seemandham • Other Caterings</text><text x="92" y="495" fill="#bfb5a6" font-size="18" font-family="Arial">Vellore Catering World · WhatsApp 94459 78140</text></svg>'''
 path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding='utf-8')

def related_areas(areas,idx,n=12):
 a=areas[idx]; out=[]
 for d in range(1,20):
  for j in (idx-d,idx+d):
   if 0<=j<len(areas) and areas[j] not in out: out.append(areas[j])
   if len(out)>=n: return out
 return out

def area_faq(a):
 n=a['name']; typ=a['area_type'].lower(); access=AREA_CTX.get(a['area_type'],AREA_CTX['Locality / Village'])[0]
 return [(f'Do you provide catering in {n}?',f'{n} is included in the supplied service-area workbook. Share the exact venue, date and guest count so {access} can be confirmed before the event.'),(f'Can I book wedding catering in {n}?',f'Wedding catering in {n} can be planned for breakfast, lunch or reception dining, with banana-leaf, buffet or other service styles depending on the venue.'),(f'Is birthday catering available in {n}?',f'Birthday catering in {n} can cover snacks, main meals, desserts, beverages and child-friendly choices for homes, halls or family venues.'),(f'Can you plan seemandham catering in {n}?',f'Seemandham catering in {n} can be aligned to ritual timing, vegetarian menu preferences, sweets, beverages and the family’s chosen serving style.'),(f'What details are needed for a {n} quote?',f'Send the event date, exact {n} venue, approximate guest count, meal timing and menu preference. For this {typ}, access and setup details are also useful.')]

def area_schema(a,faqs):
 srv={'@type':'Service','name':f'Catering in {a["name"]}','serviceType':'Event catering','description':f'Wedding, birthday, seemandham and event catering in {a["name"]}.','url':page_url(a['output']),'provider':{'@id':SITE+'/#business'},'areaServed':{'@type':'Place','name':a['search_phrase']}}
 return jsonld(business_schema(),website_schema(),srv,breadcrumb_schema([('Home','index.html'),('Servicing Areas','servicing-areas/index.html'),(a['name'],a['output'])]),faq_schema(faqs))

def area_page(a,idx,areas,blogs):
 n=a['name']; k=a['slug']; access,venues=AREA_CTX.get(a['area_type'],AREA_CTX['Locality / Village']); rel=related_areas(areas,idx); faqs=area_faq(a)
 cuisine=picks(CUISINES,k,5); counters=picks(COUNTERS,k,4); styles=picks(STYLES,k,3); starters=picks(STARTERS,k,2); mains=picks(MAINS,k,3); sweets=picks(SWEETS,k,2); drinks=picks(DRINKS,k,2)
 bg=[blogs[(idx*7+i*17)%len(blogs)] for i in range(6)]; g1=60+hnum(k+'g1',70); g2=150+hnum(k+'g2',160); g3=350+hnum(k+'g3',400); scenario=150+hnum(k+'sc',400)
 title=f'Catering in {n} | Vellore Catering World'; desc=f'Catering in {n} for weddings, birthdays, seemandham and family events. Plan menus, guest count, service style and WhatsApp enquiries with Vellore Catering World.'
 meta=head_meta(a['output'],title,desc,image=asset_url(f'assets/img/areas/{k}-hero.svg'))+area_schema(a,faqs)
 breadcrumb=f'<div class="container" data-section="2" data-section-name="Breadcrumbs"><nav class="breadcrumb"><ol><li><a href="../index.html">Home</a></li><li><a href="index.html">Servicing Areas</a></li><li><span aria-current="page">{E(n)}</span></li></ol></nav></div>'
 hero=f'<section class="page-hero page-hero--catalog" data-section="3" data-section-name="Hero Banner"><div class="page-hero__media"><img src="../assets/img/areas/{k}-hero.svg" width="1200" height="630" alt="Catering planning for {E(n)}, Vellore" fetchpriority="high"></div><div class="container page-hero__content"><p class="eyebrow">Servicing area · {E(a["area_type"])}</p><h1>Catering in {E(n)}</h1><p class="lead">Wedding catering, birthday catering, seemandham catering and other event menus for {E(n)} with direct WhatsApp enquiry.</p><div class="btn-row"><a class="btn btn--gold" href="#booking">Get a quote</a><a class="btn btn--ghost" href="https://wa.me/{CONFIG["whatsapp"]}?text={quote("Hello Vellore Catering World, I need catering in "+n)}">WhatsApp</a></div></div></section>'
 trust=f'<section class="trust-strip" data-section="4" data-section-name="Trust/USP Strip"><div class="container trust-strip__grid"><div><strong>Since 2000</strong><span>Established catering operations</span></div><div><strong>3,000+</strong><span>Events referenced by the master site</span></div><div><strong>{E(a["area_type"].split("/")[0].strip())}</strong><span>{E(n)} planning context</span></div><div><strong>WhatsApp</strong><span>Direct date enquiry</span></div></div></section>'
 s=[]
 s.append(section(5,'Introduction',shead('Local catering',f'Catering support for {n}',f'{n} appears in the supplied Vellore service-area list as a {a["area_type"].lower()} within {a["region"]}.')+f'<div class="split split--catalog"><div><p>For an event in <strong>{E(n)}</strong>, the useful starting point is the exact venue, meal timing and guest estimate. That allows wedding catering, birthday catering, seemandham catering and other services to be shaped around the real function rather than a generic package.</p><p>Because {E(n)} is listed as a {E(a["area_type"].lower())}, this page gives particular attention to {E(access)}.</p></div><img class="catalog-media" src="../assets/img/areas/{k}-hero.svg" alt="Illustrated catering guide for {E(n)}" width="1200" height="630" loading="lazy"></div>'))
 s.append(section(6,'Why Choose Us',shead('Planning strengths',f'Why the {n} enquiry is venue-first')+cards([('Venue-specific planning',f'The {n} enquiry begins with access, timing and serving space rather than assuming every venue works the same way.'),('Flexible menus',f'Menus for {n} can be adjusted around vegetarian, non-vegetarian, traditional, child-friendly and mixed-guest preferences.'),('Service coordination',f'Staffing, setup, replenishment and clearing for {n} are matched to the selected service format.'),('Direct communication',f'The {n} WhatsApp form captures the essential details without an account or online payment.')]),True))
 s.append(section(7,'Catering Services Included',shead('Four services',f'Core catering services for {n}')+'<div class="service-links-grid">'+''.join(f'<article class="service-link-card"><h3><a href="../{h}">{E(l)}</a></h3><p>{E(d)} For {E(n)}, the exact scope is confirmed after venue and guest-count discussion.</p></article>' for l,h,d in CORE)+'</div>'))
 s.append(section(8,'Types of Events Served',shead('Event formats',f'Functions that can be discussed for {n}')+bullets([f'Wedding breakfast, muhurtham lunch or reception dining in {n}',f'Birthday parties and milestone celebrations in {n}',f'Seemandham, valaikappu and other traditional family functions in {n}',f'Engagements, housewarmings, anniversaries and community meals in {n}',f'Corporate, school, institutional or group meals around {n}',f'Drop-off, buffet, banana-leaf or staffed full-service catering depending on the {n} venue'])))
 s.append(section(9,'Menu Categories',shead('Menu structure',f'Build a balanced menu for {n}')+cards([('Breakfast / tiffin',f'For {n}, idli, dosa, pongal, vadai, chutney and coffee can form a practical morning sequence.'),('Lunch / meals',f'A {n} lunch can combine rice, sambar, rasam, poriyal, kootu, appalam, pickle, sweet and curd.'),('Dinner / reception',f'Evening catering in {n} can use breads, rice or biryani, gravies, starters, desserts and beverages.'),('Counters / refreshments',f'{counters[0].title()} or {counters[1]} can be considered when the {n} venue has suitable utilities and queue space.')]),True))
 s.append(section(10,'Cuisine Options',shead('Cuisine choices',f'Cuisine directions for {n}')+bullets([f'{x} can be discussed for a {n} function, subject to the event format and final menu.' for x in cuisine])))
 s.append(section(11,'Sample Menus',shead('Illustrative menu',f'One planning example for {n}','This {n} menu is an illustration, not a fixed package or quotation.')+cards([('Welcome',f'{drinks[0].title()} with {starters[0]} for the {n} guest-arrival window.'),('Main course',f'{mains[0].capitalize()}, {mains[1]} and an appropriate side for the {n} service.'),('Sweet finish',f'{sweets[0].title()} with {sweets[1]} and {drinks[1]} for the {n} closing course.'),('Optional counter',f'{counters[2].title()} may suit {n} when the venue can support a safe counter footprint.')])))
 s.append(section(12,'Customization Options',shead('Customise',f'Adjust the {n} menu around the people attending')+bullets([f'Change spice, richness and course count for the age mix attending in {n}.',f'Choose vegetarian-only, non-vegetarian or clearly separated mixed menus for {n}.',f'Prioritise traditional dishes for a {n} ritual or contemporary dishes for a reception-style event.',f'Discuss Jain-friendly or other dietary requirements early for the {n} function.',f'Add or remove live counters based on power, water, queue space and duration at the {n} venue.']),True))
 s.append(section(13,'Live Food Counters',shead('Live service',f'Counter ideas for {n}')+cards([(x.title(),f'A {x} counter can add a made-to-order element in {n} when the venue supports safe queueing and replenishment.') for x in counters])))
 s.append(section(14,'Traditional Service Styles',shead('Serving formats',f'Service styles that can fit {n}')+cards([(x.title(),f'{x.title()} can work in {n} when seating, meal duration and staffing are planned around the guest count.') for x in styles],'content-cards content-cards--three'),True))
 s.append(section(15,'Guest Capacity',shead('Guest count',f'Scale the {n} service carefully')+cards([(f'Around {g1} guests',f'A smaller {n} function can use a compact menu and a single service zone.'),(f'Around {g2} guests',f'A medium-size {n} function benefits from clear buffet lanes or planned banana-leaf batches.'),(f'{g3}+ guests',f'A larger {n} gathering usually requires more holding capacity, service staff and staged replenishment.')],'content-cards content-cards--three')))
 s.append(section(16,'Wedding/Event Process',shead('Workflow',f'From {n} enquiry to service')+'<ol class="process-grid">'+''.join([f'<li><h3>Enquiry</h3><p>Share the {E(n)} venue, date, meal and guest estimate.</p></li>',f'<li><h3>Consultation</h3><p>Discuss the {E(n)} menu, dietary needs, service style and schedule.</p></li>',f'<li><h3>Menu confirmation</h3><p>Confirm dishes, counters, sweets and beverages for {E(n)}.</p></li>',f'<li><h3>Logistics</h3><p>Confirm {E(n)} access, utilities, equipment and staffing.</p></li>',f'<li><h3>Execution</h3><p>Prepare, transport and serve according to the confirmed {E(n)} plan.</p></li>'])+'</ol>',True))
 s.append(section(17,'Food Quality & Hygiene',shead('Food handling',f'Quality checks for {n}')+bullets([f'Confirm the preparation and dispatch timeline for food travelling to {n}.',f'Keep cooked food, raw ingredients and service utensils on separate practical workflows for {n}.',f'Discuss potable water and hand-washing arrangements at the {n} venue.',f'Use safe holding and batch replenishment during the {n} service.',f'Confirm {n} travel time so food is not dispatched unnecessarily early.'])))
 s.append(section(18,'Kitchen / Infrastructure',shead('Infrastructure',f'What a {n} event may need')+cards([('Preparation',f'Batch planning, ingredient staging and packing for {n} are organised before dispatch.'),('Transport',f'The {n} route and venue access determine how vessels, carriers and materials arrive.'),('Venue setup',f'Tables, buffet equipment or banana-leaf requirements are matched to the {n} venue.'),('Utilities',f'Any {n} live counter is confirmed against power, water, ventilation and protected cooking space.')]),True))
 s.append(section(19,'Our Chefs & Team',shead('People',f'Team planning for {n}')+f'<div class="truth-card"><p>For {E(n)}, staffing is planned across production, packing, transport, setup, serving, replenishment and clearing. The exact cook and service-team requirement depends on the confirmed menu and guest count. This page does not invent individual chef biographies that were not supplied in the project material.</p></div>'))
 s.append(section(20,'Wedding Gallery',shead('Wedding gallery',f'{n} wedding-planning visual','Illustrative artwork is used until verified real-event photographs are supplied.')+f'<div class="media-grid"><figure><img src="../assets/img/areas/{k}-wedding.svg" width="1200" height="630" alt="Illustrative wedding catering planning for {E(n)}" loading="lazy"><figcaption>Illustrative planning artwork for {E(n)}.</figcaption></figure><figure><a href="../gallery.html"><img src="../assets/img/areas/{k}-hero.svg" width="1200" height="630" alt="Open the Vellore Catering World gallery from {E(n)}" loading="lazy"></a><figcaption>Use the main gallery for verified business photography.</figcaption></figure></div>',True))
 s.append(section(21,'Food Gallery',shead('Food gallery',f'{n} menu-planning visual','The visual is illustrative and is not presented as a photograph of a completed client event.')+f'<div class="media-grid"><figure><img src="../assets/img/areas/{k}-food.svg" width="1200" height="630" alt="Illustrative menu planning for {E(n)}" loading="lazy"><figcaption>Menu-planning artwork for {E(n)}.</figcaption></figure><figure><a href="../menus.html"><img src="../assets/img/areas/{k}-wedding.svg" width="1200" height="630" alt="Explore catering menus for {E(n)}" loading="lazy"></a><figcaption>Compare breakfast, lunch, dinner and event-menu ideas.</figcaption></figure></div>'))
 s.append(section(22,'Recent Events / Case Studies',shead('Planning example',f'Illustrative {n} event scenario','No unverified customer event is represented as a real case study.')+f'<article class="scenario-card"><h3>{scenario}-guest {E(n)} planning example</h3><p>An illustrative {scenario}-guest function in {E(n)} could use {E(styles[0])}, a menu led by {E(mains[2])}, {E(sweets[0])} and {E(drinks[0])}, with {E(counters[3])} as an optional counter. The scenario demonstrates how the {E(n)} venue, menu and staffing decisions connect; it is not a claim about a completed client event.</p></article>',True))
 s.append(section(23,'Customer Testimonials',shead('Testimonials',f'Verified feedback for {n}')+f'<div class="truth-card"><p>Generated or invented testimonials are not inserted for {E(n)}. A real customer quote can be added here when the business provides permission, event context and the approved wording.</p></div>'))
 s.append(section(24,'Google Reviews',shead('Public feedback',f'Check current reviews before a {n} booking')+f'<div class="cta-panel"><p>Ratings and review counts change over time, so the {E(n)} page does not hard-code a score. Use Google Maps to verify current public feedback.</p><a class="btn btn--ghost" href="https://www.google.com/maps/search/?api=1&amp;query={quote(CONFIG["business_name"]+", "+CONFIG["city"])}">Search Google Maps</a></div>',True))
 s.append(section(25,'Venues We Cater At',shead('Venue types',f'Venue planning around {n}')+cards([(v.title(),f'For a {v} in {n}, access, serving space and utilities should be confirmed before the final menu.') for v in venues[:4]])))
 s.append(section(26,'Areas We Serve',shead('Nearby areas',f'Continue from {n} to related service pages','Every workbook locality is linked from the Servicing Areas hub.')+'<ul class="area-link-cloud">'+''.join(f'<li><a href="{E(x["slug"])}-catering.html">Catering in {E(x["name"])}</a></li>' for x in rel)+'</ul><p class="center-copy"><a class="text-link" href="index.html">Browse all 506 servicing areas</a></p>',True))
 s.append(section(27,'Pricing / Cost Guide',shead('Cost factors',f'What changes a {n} catering quotation')+bullets([f'Final guest count and agreed buffer for the {n} event.',f'Number of dishes, premium ingredients, sweets and beverages selected for {n}.',f'Service style, number of staff, equipment and duration required in {n}.',f'Transport, access and setup requirements for the exact {n} venue.',f'Live counters, dietary preparation and serving materials requested for {n}.'])))
 s.append(section(28,'Packages',shead('Planning scopes',f'Three ways to scope a {n} enquiry','These are service-scope examples rather than fixed-price packages.')+cards([('Essential',f'A focused {n} menu with core dishes and straightforward setup.'),('Celebration',f'A broader {n} menu with extra starters, sweets or beverages and more service support.'),('Signature',f'A multi-course {n} event with selected live counters and enhanced presentation.')],'content-cards content-cards--three'),True))
 s.append(section(29,'FAQs',shead('Questions',f'Frequently asked questions about catering in {n}')+'<div class="faq">'+''.join(f'<details><summary>{E(q)}</summary><div><p>{E(ans)}</p></div></details>' for q,ans in faqs)+'</div>'))
 s.append(section(30,'Why Our Food Is Different',shead('Food-first planning',f'A practical menu approach for {n}')+cards([('Coherent menus',f'Dishes for {n} are selected to work together rather than making the menu long for its own sake.'),('Service-aware choices',f'Food that travels and serves well is prioritised for the actual {n} route and timing.'),('Guest-aware planning',f'Traditional favourites, spice balance and dietary requests can be discussed for the {n} guest mix.'),('Waste-conscious portions',f'Guest estimates and batch replenishment help avoid unnecessary display quantities in {n}.')]),True))
 s.append(section(31,'Booking / Enquiry CTA',shead('Book',f'Check your {n} event date')+f'<div class="split split--catalog" id="booking"><div><h3>Send the essentials first</h3><p>For a useful {E(n)} response, include the exact venue, approximate guest count, meal timing and whether the enquiry is for wedding catering, birthday catering, seemandham catering or another service.</p></div>{wa_form("area-"+k,"Catering in "+n,heading="Enquire for catering in "+n,heading_tag="h3")}</div>'))
 s.append(section(32,'Contact Information',shead('Contact',f'Reach Vellore Catering World for {n}')+f'<div class="contact-mini"><div><strong>Call</strong><a href="tel:{CONFIG["phone_e164"]}">{E(CONFIG["phone_display"])}</a></div><div><strong>WhatsApp</strong><a href="https://wa.me/{CONFIG["whatsapp"]}">{E(CONFIG["phone_short"])}</a></div><div><strong>Kitchen / office</strong><span>{E(CONFIG["street"])}, {E(CONFIG["city"])} {E(CONFIG["pin"])}</span></div></div>',True))
 s.append(section(33,'Google Map',shead('Map',f'Find {n}, Vellore')+f'<div class="map-shell"><iframe title="Map search for {E(n)}, Vellore" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="https://www.google.com/maps?q={quote(a["search_phrase"])}&amp;output=embed"></iframe></div>'))
 s.append(section(34,'Related Services',shead('Related catering',f'Useful service pages from the {n} guide')+'<div class="service-links-grid">'+''.join(f'<article class="service-link-card"><h3><a href="../{h}">{E(l)} in Vellore</a></h3><p>{E(d)} Use this from the {E(n)} page when it matches the function.</p></article>' for l,h,d in CORE)+'</div>',True))
 s.append(section(35,'Related Articles',shead('Guides',f'Continue planning your {n} event')+'<div class="article-grid">'+''.join(f'<article class="article-card"><h3><a href="../guides/blogs/{E(b["slug"])}.html">{E(b["title"])}</a></h3><p>{E(b["summary"])}</p></article>' for b in bg)+'</div>'))
 return page_shell(a['output'],meta,breadcrumb+hero+trust+''.join(s),body_class='area-page')

def area_index(areas):
 groups=defaultdict(list)
 for a in areas: groups[a['region']].append(a)
 htmls=[]
 for rg in sorted(groups):
  links=''.join(f'<li><a href="{E(a["slug"])}-catering.html">{E(a["name"])}</a><span>{E(a["area_type"])}</span></li>' for a in groups[rg])
  htmls.append(f'<section class="catalog-group"><h2>{E(rg)}</h2><ul class="catalog-link-grid area-index-grid">{links}</ul></section>')
 out='servicing-areas/index.html'; desc='Browse all 506 Vellore and nearby catering service areas with individual wedding, birthday, seemandham and event catering pages.'
 meta=head_meta(out,'Servicing Areas | Catering in Vellore & Nearby',desc)+jsonld(business_schema(),website_schema(),breadcrumb_schema([('Home','index.html'),('Servicing Areas',out)]))
 main=f'<section class="page-hero page-hero--compact"><div class="container"><p class="eyebrow">Services · Local coverage</p><h1>Servicing Areas</h1><p class="lead">Browse {len(areas)} localities from the supplied Vellore-area workbook. Each locality has a full catering planning page.</p></div></section><div class="container"><nav class="breadcrumb"><ol><li><a href="../index.html">Home</a></li><li><span>Servicing Areas</span></li></ol></nav></div><section class="section"><div class="container"><div class="catalog-search"><label for="area-search">Search servicing areas</label><input id="area-search" type="search" placeholder="Type an area or locality…" data-catalog-filter></div>{"".join(htmls)}</div></section>'
 return page_shell(out,meta,main,body_class='area-index')

def topics(cat,areas):
 out=[]; seen=set()
 for i,it in enumerate(cat):
  fmt=FORMATS[i%len(FORMATS)]; angle=ANGLES[(i*3)%len(ANGLES)]; title=f'{it["catering_type"]} in Vellore: {fmt} for {angle.title()}'; s=slug(title); seen.add(s); out.append({'title':title,'slug':s,'service':it,'category':it['categories'][0],'format':fmt,'angle':angle})
 subjects=['Wedding Catering in Vellore','Birthday Catering in Vellore','Seemandham Catering in Vellore','South Indian Wedding Menus','Tamil Vegetarian Catering','Non-Vegetarian Catering','Banana Leaf Service','Buffet Catering','Live Food Counters','Breakfast Catering','Lunch Catering','Reception Dinner Catering','Engagement Catering','Housewarming Catering','Corporate Catering','School Event Catering','Temple Function Catering','Annadhanam Catering','Biryani Catering','Dessert Counters','Filter Coffee Service','Guest Count Planning','Catering Budget Planning','Venue Coordination','Food Hygiene','Catering Service Staff']
 j=0
 while len(out)<BLOG_COUNT:
  sub=subjects[j%len(subjects)]; angle=ANGLES[(j*5+2)%len(ANGLES)]; fmt=FORMATS[(j*7+1)%len(FORMATS)]; area=areas[(j*37)%len(areas)]
  if j%3==0: title=f'{sub}: {fmt} for {angle.title()} around {area["name"]}'
  elif j%3==1: title=f'How to Improve {angle.title()} for {sub}: Vellore {fmt}'
  else: title=f'{sub} {fmt}: Practical Decisions for {angle.title()}'
  s=slug(title)
  if s in seen: s+=f'-{len(out)+1}'; title+=f' — Article {len(out)+1}'
  seen.add(s); it=cat[hnum(title,len(cat))]; out.append({'title':title,'slug':s,'service':it,'category':it['categories'][0],'format':fmt,'angle':angle}); j+=1
 for i,b in enumerate(out):
  b['index']=i; b['output']=f'guides/blogs/{b["slug"]}.html'; b['summary']=f'Practical notes for {b["title"]}, covering menu choices, guest planning, service coordination and {b["angle"]}.'
 return out

def blog_faq(b):
 s=b['service']['catering_type']; a=b['angle']; f=b['format'].lower()
 return [(f'What should I decide first for {s.lower()}?',f'For this {f} on {s.lower()}, start with the event date, venue, guest estimate and meal timing. Those details shape the menu and service plan when the focus is {a}.'),(f'How does {a} affect catering planning?',f'For {s.lower()}, {a} affects dishes, portions, counters, staffing and guest flow. This {f} treats it as a planning input rather than an afterthought.'),('Should I choose the menu before confirming guest count?',f'For {s.lower()}, a draft menu can be discussed early, but final quantities and staffing are more reliable after the guest estimate and service format are reasonably stable.'),('Can I ask for vegetarian and non-vegetarian options?',f'Yes. For {s.lower()}, discuss separation, labels, counter placement and guest preferences so a mixed menu remains clear and comfortable.'),('How do I request a quote?',f'Use the WhatsApp enquiry form for {s.lower()} and send your name, contact number, date, venue, guest count and any {a} priorities.')]

def blog_page(b,blogs,areas):
 s=b['service']['catering_type']; k=b['slug']; angle=b['angle']; fmt=b['format']; cat=b['category']; ctx=CAT_CTX.get(cat,'practical menu and service coordination'); idx=b['index']; local=areas[(idx*37)%len(areas)]; al=[areas[(idx*37+i*71)%len(areas)] for i in range(4)]
 cuisines=picks(CUISINES,k,4); counters=picks(COUNTERS,k,3); styles=picks(STYLES,k,3); mains=picks(MAINS,k,3); sweets=picks(SWEETS,k,2); faqs=blog_faq(b); related=[blogs[(idx+x)%len(blogs)] for x in (7,19,41,67,101,131)]
 title=b['title']; desc=f'{title}. {b["summary"]} Covers menus, guest counts, timing, venue logistics and booking decisions for Vellore events.'
 article={'@type':'BlogPosting','headline':title,'description':b['summary'],'mainEntityOfPage':page_url(b['output']),'image':asset_url(f'assets/img/blogs/{k}.svg'),'author':{'@type':'Organization','name':CONFIG['business_name']},'publisher':{'@id':SITE+'/#business'},'datePublished':TODAY,'dateModified':TODAY,'inLanguage':'en-IN','about':[s,'Catering in Vellore',angle]}
 meta=head_meta(b['output'],title,desc,image=asset_url(f'assets/img/blogs/{k}.svg'),og_type='article')+jsonld(business_schema(),website_schema(),article,breadcrumb_schema([('Home','index.html'),('Guides','guides/index.html'),('Blogs','guides/blogs/index.html'),(title,b['output'])]),faq_schema(faqs))
 p1=f'Good {s.lower()} is not simply a longer dish list. This {fmt.lower()} connects {angle}, the venue, guest expectations and the service window. For readers comparing catering in Vellore, wedding caterers in Vellore, birthday catering in Vellore or seemandham catering in Vellore, the useful question is how the plan will work on the actual event day.'
 p2=f'Within {cat.lower()}, {ctx} matter because food moves through preparation, transport, setup, guest arrival, service, replenishment and clearing. The {local["name"]} locality page is one practical local reference for applying the same decisions.'
 main=f'''<article class="blog-article"><section class="page-hero page-hero--catalog blog-hero"><div class="page-hero__media"><img src="../../assets/img/blogs/{k}.svg" width="1200" height="630" alt="{E(title)}" fetchpriority="high"></div><div class="container page-hero__content"><p class="eyebrow">Guides · Blogs · {E(cat)}</p><h1>{E(title)}</h1><p class="lead">{E(b['summary'])}</p><div class="blog-meta"><span>Published by Vellore Catering World</span><span>Updated {TODAY}</span><span>{E(fmt)}</span></div></div></section><div class="container"><nav class="breadcrumb"><ol><li><a href="../../index.html">Home</a></li><li><a href="../index.html">Guides</a></li><li><a href="index.html">Blogs</a></li><li><span>{E(title)}</span></li></ol></nav></div><section class="section"><div class="container blog-layout"><div class="blog-content"><p>{E(p1)}</p><p>{E(p2)}</p>
<h2>1. Define the constraints for {E(s.lower())}</h2><p>For {E(title)}, write down the event date, exact venue, meal start time, guest estimate, service duration and any fixed ritual or programme timing before finalising dishes. That keeps {E(angle)} connected to a real operating window.</p><p>If the {E(s.lower())} function has a tight serving window, use dishes that replenish cleanly in batches. If guests arrive gradually, holding and replenishment matter more. A {E(fmt.lower())} should therefore examine the guest journey, not just the menu length.</p>
<h2>2. Build the menu around a clear purpose</h2><p>For this {E(s.lower())} topic, one direction is {E(cuisines[0])} with {E(mains[0])}, supported by {E(mains[1])}. Another is {E(cuisines[1])}. The right direction depends on family preference, event tradition and how strongly {E(angle)} shapes the function.</p><p>Desserts such as {E(sweets[0])} and {E(sweets[1])} can create variety without making the sweet course disproportionately large. In {E(title)}, the menu is treated as a sequence rather than a catalogue.</p>
<h2>3. Match service style to {E(angle)}</h2><p>{E(styles[0].title())}, {E(styles[1])} and {E(styles[2])} each create a different guest rhythm. For {E(s.lower())}, choose the format that fits the venue, event timing and expected guest movement.</p><p>Ask how many service points are needed, where guests will queue, how elders and children will be accommodated, and whether the serving line supports the {E(angle)} objective described in this {E(fmt.lower())}.</p>
<h2>4. Use live counters only when they add value</h2><p>For {E(title)}, options such as {E(counters[0])}, {E(counters[1])} or {E(counters[2])} should earn their place. Each counter adds staff, equipment, ingredients, utilities and a queue, so popularity alone is not enough reason to include it.</p><p>Place counters where waiting guests do not block the main meal service. For {E(s.lower())}, power, water, ventilation and replenishment should be confirmed before the counter becomes part of the final quotation.</p>
<h2>5. Plan guest quantities with a sensible buffer</h2><p>Guest count is rarely exact for {E(s.lower())}, but quantities should still be planned rather than guessed. Start with the host’s best estimate, separate adults and children where useful, consider whether the meal is the main attraction, and discuss a sensible buffer.</p><p>Wedding catering in Vellore can receive guests in waves around ceremony timing; birthday catering in Vellore may have a shorter service window; seemandham catering in Vellore may be tied to ritual timing. {E(title)} applies that distinction to {E(angle)}.</p>
<h2>6. Treat venue logistics as part of the menu</h2><p>A menu that looks ideal on paper still has to work at a real venue. Limited loading space, distant service access or no safe place for a live counter can change the plan. For the {E(local['name'])} example, confirm the exact entrance, unloading point, holding area, service start and cleaning expectations.</p><p>Browse related local pages for {', '.join(f'<a href="../../servicing-areas/{a["slug"]}-catering.html">{E(a["name"])}</a>' for a in al)}. These links connect the article to the service-area directory without requiring hundreds of links on every page.</p>
<h2>7. Keep dietary requirements explicit</h2><p>Vegetarian, non-vegetarian, Jain-friendly and allergy-related requests should be discussed as stated requirements. In {E(s.lower())}, decide how foods will be labelled and placed, and clarify ingredient restrictions early when they affect {E(angle)}.</p><p>Clear dietary communication supports guest confidence and service speed. It also reduces last-minute substitutions that can make a carefully planned {E(fmt.lower())} less predictable.</p>
<h2>8. Create a shared event timing sheet</h2><p>For {E(title)}, a simple sheet can record kitchen dispatch, venue arrival, setup start, welcome beverage, first service, last service and clearing. Shared timing reduces ambiguity between the host, venue and catering team.</p><p>Map rituals, speeches, performances or photography blocks against the meal. Food quality is better protected when the service time is a firm operational milestone rather than a rough suggestion.</p>
<h2>9. Questions to ask before confirming {E(s.lower())}</h2><ul class="checks"><li>What is the realistic guest count and service window for this function?</li><li>Which dishes are essential to the family or event tradition?</li><li>What service style best supports {E(angle)}?</li><li>Which live counters genuinely improve the experience?</li><li>What utilities, access and holding facilities are available?</li><li>How will dietary requirements be communicated?</li><li>Who is the single point of contact on the event day?</li></ul>
<h2>10. A practical checklist for {E(title)}</h2><p>Before treating the plan as final, write down the date, venue, guest estimate, meal timing, menu scope, service style, staff requirement, counters, transport, setup, dietary notes and payment terms. For this {E(fmt.lower())}, the checklist turns {E(angle)} from a vague preference into a confirmable requirement.</p><p>Search terms can help people discover options, but the booking decision should come from whether the proposed menu and service plan fit the function. That is the purpose of this article and the linked service pages.</p>
<h2>Frequently asked questions</h2><div class="faq">{''.join(f'<details><summary>{E(q)}</summary><div><p>{E(a)}</p></div></details>' for q,a in faqs)}</div>
<h2>Related catering services</h2><div class="service-links-grid">{''.join(f'<article class="service-link-card"><h3><a href="../../{h}">{E(l)}</a></h3><p>{E(d)} This link is included because it is commonly compared with the subject of this article.</p></article>' for l,h,d in CORE)}</div>
<h2>Continue reading</h2><div class="article-grid">{''.join(f'<article class="article-card"><h3><a href="{E(r["slug"])}.html">{E(r["title"])}</a></h3><p>{E(r["summary"])}</p></article>' for r in related)}</div></div><aside class="blog-aside"><div class="blog-aside__card"><h2>Need a catering quote?</h2>{wa_form("blog-"+k,s,heading="WhatsApp enquiry",heading_tag="h3")}</div><div class="blog-aside__card"><h2>Primary topic</h2><p><a class="text-link" href="../../services/{E(b['service']['slug'])}.html">{E(s)} in Vellore</a></p><p>Focus: {E(angle)} · {E(cat)}</p></div></aside></div></section></article>'''
 return page_shell(b['output'],meta,main,body_class='blog-page')

def blog_index(blogs):
 groups=defaultdict(list)
 for b in blogs: groups[b['category']].append(b)
 parts=[]
 for cat in sorted(groups):
  c=''.join(f'<article class="article-card blog-index-card" data-blog-card><p class="section-kicker">{E(b["format"])}</p><h2><a href="{E(b["slug"])}.html">{E(b["title"])}</a></h2><p>{E(b["summary"])}</p></article>' for b in groups[cat])
  parts.append(f'<section class="blog-index-group"><div class="section-head"><p class="section-kicker">Topic group</p><h2 class="gilded">{E(cat)}</h2></div><div class="article-grid">{c}</div></section>')
 out='guides/blogs/index.html'; desc=f'Browse {len(blogs)} detailed Vellore catering articles covering weddings, birthdays, seemandham, menus, guest counts, service styles and event planning.'
 meta=head_meta(out,'Catering Blogs & Guides | Vellore Catering World',desc)+jsonld(business_schema(),website_schema(),breadcrumb_schema([('Home','index.html'),('Guides','guides/index.html'),('Blogs',out)]))
 main=f'<section class="page-hero page-hero--compact"><div class="container"><p class="eyebrow">Guides · Blogs</p><h1>Catering Blogs</h1><p class="lead">{len(blogs)} planning articles about catering in Vellore, wedding catering, birthday catering, seemandham catering, menus and service logistics.</p></div></section><div class="container"><nav class="breadcrumb"><ol><li><a href="../../index.html">Home</a></li><li><a href="../index.html">Guides</a></li><li><span>Blogs</span></li></ol></nav></div><section class="section"><div class="container"><div class="catalog-search"><label for="blog-search">Search {len(blogs)} articles</label><input id="blog-search" type="search" placeholder="Search wedding, birthday, menu…" data-blog-search></div>{"".join(parts)}</div></section>'
 return page_shell(out,meta,main,body_class='blog-index')

def write_data(areas,blogs):
 (ROOT/'data/servicing-areas.json').write_text(json.dumps({'count':len(areas),'items':areas},ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'data/blog-catalog.json').write_text(json.dumps({'count':len(blogs),'generated':TODAY,'items':[{**{k:v for k,v in b.items() if k!='service'},'service_name':b['service']['catering_type'],'service_slug':b['service']['slug']} for b in blogs]},ensure_ascii=False,indent=2),encoding='utf-8')
 with (ROOT/'data/servicing-area-page-map.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f); w.writerow(['S.No','Area / Locality','Search Phrase','Region','Area Type','URL']); [w.writerow([a['sno'],a['name'],a['search_phrase'],a['region'],a['area_type'],a['output']]) for a in areas]
 with (ROOT/'data/blog-page-map.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f); w.writerow(['No','Blog Title','Category','Focus','URL']); [w.writerow([i,b['title'],b['category'],b['angle'],b['output']]) for i,b in enumerate(blogs,1)]

def main():
 AREA_DIR.mkdir(exist_ok=True); BLOG_DIR.mkdir(parents=True,exist_ok=True); AREA_MEDIA.mkdir(parents=True,exist_ok=True); BLOG_MEDIA.mkdir(parents=True,exist_ok=True)
 areas=read_areas(); cat=catalog(); blogs=topics(cat,areas); write_data(areas,blogs)
 print(f'Generating {len(areas)} servicing-area pages…')
 for i,a in enumerate(areas):
  svg(AREA_MEDIA/f'{a["slug"]}-hero.svg',f'Catering in {a["name"]}',a['search_phrase'],a['slug']+'hero'); svg(AREA_MEDIA/f'{a["slug"]}-wedding.svg',f'{a["name"]} Wedding Planning','Illustrative event-service planning artwork',a['slug']+'wed'); svg(AREA_MEDIA/f'{a["slug"]}-food.svg',f'{a["name"]} Menu Planning','Illustrative food-service planning artwork',a['slug']+'food')
  (ROOT/a['output']).write_text(area_page(a,i,areas,blogs),encoding='utf-8')
 (AREA_DIR/'index.html').write_text(area_index(areas),encoding='utf-8')
 print(f'Generating {len(blogs)} blog pages…')
 for b in blogs:
  svg(BLOG_MEDIA/f'{b["slug"]}.svg',b['service']['catering_type'],b['angle'].title()+' · '+b['format'],b['slug'],kind='blog'); (ROOT/b['output']).write_text(blog_page(b,blogs,areas),encoding='utf-8')
 (BLOG_DIR/'index.html').write_text(blog_index(blogs),encoding='utf-8')
 print(f'generate_area_blog_site: {len(areas)} area pages + {len(blogs)} blogs + 2 hubs')
if __name__=='__main__': main()
