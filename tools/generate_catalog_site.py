#!/usr/bin/env python3
"""Generate all catering type pages from data/catering-catalog.json.
Version: V2

The generator deliberately avoids fabricated customer reviews, ratings, or real-event claims.
Illustrative planning scenarios and generated media are labelled as such.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

from sitekit import CONFIG, page_url, asset_url, business_schema, website_schema, service_schema, breadcrumb_schema, faq_schema, jsonld, wa_form, icon

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catering-catalog.json"
SERVICES = ROOT / "services"
GUIDES = ROOT / "guides"
MEDIA = ROOT / "assets" / "img" / "pages"
SITE = CONFIG["site_url"].rstrip("/")
E = html.escape

CATEGORY_CONTEXT = {
    "Wedding & Marriage": ("ceremonial timing, family hospitality and a smooth dining flow", "wedding", ["muhurtham breakfast", "reception dinner", "family lunch"]),
    "Religious & Traditional": ("ritual timings, traditional service etiquette and sattvic-friendly menu planning", "traditional function", ["traditional breakfast", "banana-leaf lunch", "prasadam service"]),
    "Birthday & Family": ("guest-friendly portions, child-friendly choices and relaxed family service", "family celebration", ["party snacks", "celebration lunch", "dessert counter"]),
    "Corporate & Business": ("punctual service windows, professional presentation and predictable portions", "business event", ["working breakfast", "buffet lunch", "tea break"]),
    "Education": ("safe batch preparation, queue management and age-appropriate menus", "education event", ["student breakfast", "boxed lunch", "snack service"]),
    "Events & Entertainment": ("high-volume service, crew timing and fast guest movement", "event", ["welcome refreshments", "main buffet", "backstage meals"]),
    "Social & Community": ("community-scale planning, practical menus and efficient service", "community function", ["tea service", "community lunch", "evening snacks"]),
    "Healthcare & Institutional": ("controlled preparation, dependable schedules and practical nutrition", "institutional service", ["light breakfast", "balanced lunch", "simple dinner"]),
    "Religious Festivals & Seasonal": ("festival traditions, seasonal favourites and crowd-ready service", "festival gathering", ["festival breakfast", "special lunch", "sweets service"]),
    "Food Service Formats": ("the chosen service format, speed of service and venue logistics", "catering service", ["welcome service", "main service", "beverage service"]),
    "Cuisine-Based": ("authentic flavour profiles, balanced courses and menu coherence", "cuisine-focused event", ["signature starters", "regional mains", "traditional sweets"]),
    "Specialized & Dietary": ("ingredient clarity, cross-contact awareness and guest-specific menu choices", "dietary-focused event", ["safe starters", "balanced mains", "labelled desserts"]),
    "Travel & Venue": ("transport timing, venue access, holding temperatures and service setup", "venue event", ["arrival refreshments", "venue buffet", "travel packs"]),
    "Religious & Spiritual": ("simple service, spiritual setting etiquette and traditional food preferences", "spiritual gathering", ["sattvic breakfast", "community meal", "prasadam"]),
    "Retail & Commercial": ("repeatable quality, production planning and commercially practical service", "commercial catering", ["counter snacks", "meal service", "packaged items"]),
    "Special Occasions": ("occasion-appropriate presentation, flexible timing and memorable food moments", "special occasion", ["welcome bites", "celebration meal", "dessert finale"]),
}

CUISINES = [
    "Tamil vegetarian", "South Indian", "Chettinad-inspired", "North Indian", "Jain-friendly",
    "Andhra-style", "Kerala-style", "multi-cuisine", "pure vegetarian", "halal-friendly planning"
]
LIVE_COUNTERS = [
    "mini dosa & chutney", "chaat", "filter coffee", "fresh juice", "parotta", "paniyaram",
    "dessert plating", "idiyappam", "tandoor-style breads", "ice cream & toppings", "mocktail"
]
STYLES = ["banana-leaf service", "buffet service", "plated service", "boxed meals", "counter service", "sit-down service"]
AREAS = CONFIG["areas_served"]
VENUE_TYPES = ["marriage halls", "community halls", "schools and colleges", "office campuses", "temple premises", "private homes", "outdoor lawns", "banquet spaces", "resorts", "institutional campuses"]

GUIDE_DATA = [
    ("event-catering-checklist-vellore", "Event Catering Checklist for Vellore", "A practical planning checklist covering guest count, venue access, menu timing, service style and backup arrangements."),
    ("catering-cost-guide-vellore", "Catering Cost Guide for Vellore Events", "Understand the main variables that influence catering quotations, from guest count and menu depth to counters, staffing and logistics."),
    ("catering-menu-planning-vellore", "How to Plan a Catering Menu in Vellore", "A menu-planning guide for balancing courses, dietary needs, service time, regional preferences and guest comfort."),
    ("guest-count-food-planning", "Guest Count & Food Quantity Planning", "How caterers plan portions, buffers and service batches without encouraging avoidable food waste."),
    ("live-counter-planning-vellore", "Live Food Counter Planning Guide", "Use live counters effectively by planning power, queue flow, staffing, replenishment and menu pairing."),
    ("catering-hygiene-checklist", "Catering Hygiene & Food Safety Checklist", "A customer-friendly checklist for discussing ingredients, water, handling, transport, holding temperatures and service hygiene."),
]


def slugish(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def hnum(key: str, modulo: int) -> int:
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:12], 16) % modulo


def pick(seq, key: str, offset=0):
    return seq[hnum(key + str(offset), len(seq))]


def unique_list(seq):
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out


def title_for(t: str) -> str:
    title = f"{t} in Vellore | Vellore Catering"
    return title if len(title) <= 65 else f"{t} in Vellore"


def description_for(item) -> str:
    t = item["catering_type"]
    desc = f"Plan {t.lower()} in Vellore with custom menus, trained service staff, hygienic preparation and WhatsApp enquiries for your event date."
    if len(desc) < 120:
        desc = desc[:-1] + " and guest count."
    return desc[:160].rstrip(" ,.;") + "."


def rel_for_output(output: str, target: str) -> str:
    depth = output.count("/")
    return "../" * depth + target


def section_head(kicker, title, copy=""):
    p = f'<p class="section-kicker">{E(kicker)}</p>' if kicker else ""
    c = f'<p class="section-copy">{E(copy)}</p>' if copy else ""
    return f'<div class="section-head">{p}<h2 class="gilded" data-reveal>{E(title)}</h2>{c}</div>'


def cards(items, cls="content-cards"):
    return '<div class="%s">%s</div>' % (cls, "".join(
        f'<article class="content-card" data-reveal style="--d:{i%4}"><h3>{E(a)}</h3><p>{E(b)}</p></article>'
        for i, (a,b) in enumerate(items)
    ))


def bullets(items):
    return '<ul class="checks checks--grid">' + ''.join(f'<li data-reveal>{E(x)}</li>' for x in items) + '</ul>'


def make_faqs(item, ctx, seed):
    t=item["catering_type"]
    return [
        (f"How early should I book {t.lower()} in Vellore?", f"For {ctx}, earlier booking gives more time for menu planning, staffing and venue coordination. Share your event date as soon as it is reasonably fixed so availability can be checked."),
        (f"Can the {t.lower()} menu be customised?", "Yes. Menu depth, spice level, vegetarian or non-vegetarian balance, service style, sweets, beverages and live counters can be adjusted after discussing your guests and venue."),
        ("Do you cater for small and large guest counts?", "Enquiries can be planned for intimate functions as well as larger gatherings. The quotation and staffing plan depend on final guest count, menu, venue access and service format."),
        ("Can I enquire directly on WhatsApp?", f"Yes. Use the enquiry form on this page; it sends your name, contact number, event date and {t.lower()} request to the Vellore Catering WhatsApp number."),
        ("Do you publish fixed per-plate prices online?", "No single price is accurate for every event. Guest count, dishes, service staff, live counters, equipment, venue distance and service style all change the final quotation."),
    ]


def page_schema(item, title, desc, faqs, output):
    trail=[("Home","index.html"),("Catering Services","services/index.html"),(item["catering_type"],output)]
    return jsonld(
        business_schema(), website_schema(),
        service_schema(item["catering_type"], desc, output, item["search_intent"]),
        breadcrumb_schema(trail), faq_schema(faqs)
    )


def breadcrumb_html(item):
    return (f'<nav class="breadcrumb" aria-label="Breadcrumb"><ol>'
            f'<li><a href="../index.html">Home</a></li>'
            f'<li><a href="index.html">Catering services</a></li>'
            f'<li><span aria-current="page">{E(item["catering_type"])}</span></li>'
            f'</ol></nav>')


def media_path(slug, kind):
    return f"../assets/img/pages/{slug}-{kind}.svg"


def service_links():
    return [
        ("Wedding Catering", "wedding-catering-in-vellore.html", "Traditional and contemporary wedding menu planning."),
        ("Birthday Catering", "birthday-party-catering-in-vellore.html", "Flexible party food for children, adults and family gatherings."),
        ("Seemandham Catering", "seemandham-catering-in-vellore.html", "Traditional menu planning around ritual timing and family service."),
        ("Other Caterings", "other-caterings-in-vellore.html", "Browse every catering type available in the full Vellore service catalogue."),
    ]


def related_type_links(item, catalog):
    cat = item["categories"][0]
    peers=[x for x in catalog if cat in x["categories"] and x["catering_type"] != item["catering_type"]]
    if not peers:
        peers=[x for x in catalog if x["catering_type"] != item["catering_type"]]
    start=hnum(item["slug"]+"peers", len(peers))
    out=[]
    for i in range(min(4,len(peers))):
        p=peers[(start+i*3)%len(peers)]
        if p not in out: out.append(p)
    return out


def render_page(item, catalog):
    t=item["catering_type"]
    slug=item["slug"]
    cat=item["categories"][0]
    ctx, event_noun, meal_slots = CATEGORY_CONTEXT[cat]
    seed=slug
    desc=description_for(item)
    title=title_for(t)
    faqs=make_faqs(item,ctx,seed)
    cats=" / ".join(item["categories"])
    hero=media_path(slug,"hero")
    gallery1=media_path(slug,"gallery-1")
    gallery2=media_path(slug,"gallery-2")
    gallery3=media_path(slug,"gallery-3")
    video=f"../assets/video/pages/{slug}.webm"
    og=asset_url(f"assets/img/pages/{slug}-og.png")

    cuisines=unique_list([pick(CUISINES,seed,i) for i in range(7)])[:5]
    counters=unique_list([pick(LIVE_COUNTERS,seed,i+20) for i in range(8)])[:5]
    styles=unique_list([pick(STYLES,seed,i+40) for i in range(6)])[:4]
    areas=unique_list([pick(AREAS,seed,i+60) for i in range(8)])[:6]
    venues=unique_list([pick(VENUE_TYPES,seed,i+80) for i in range(8)])[:5]

    why=[
        ("Purpose-built planning", f"The service plan starts with the practical needs of {t.lower()}: {ctx}."),
        ("Menu that fits the occasion", f"Courses are selected to suit the expected guest profile rather than forcing a one-size-fits-all package onto your {event_noun}."),
        ("Vellore-focused logistics", f"Setup, transport and service sequencing are planned around Vellore venues, access windows and your event timetable."),
        ("Direct coordination", "The same enquiry details flow into WhatsApp so date, contact number and catering requirement are easy to continue with the team."),
    ]
    includes=[
        f"Menu consultation tailored to {t.lower()}",
        "Ingredient and preparation planning", "Cooking, transport and service coordination",
        "Service staff and buffet or traditional setup as agreed", "Water, beverage and counter planning where selected",
        "Post-service clearing scope confirmed before the event"
    ]
    event_types=[
        (f"Primary {event_noun}", item["description"]),
        ("Small family format", f"A compact version of {t.lower()} with a focused menu and simpler service flow."),
        ("Larger hosted format", f"Expanded staffing, replenishment and guest movement planning for a busier {event_noun}."),
        ("Venue-led format", f"Service adjusted to kitchen access, dining layout and timing restrictions at the selected venue."),
    ]
    menu_cats=[
        (meal_slots[0].title(), f"Comfortable opening dishes and beverages selected for the event start time."),
        (meal_slots[1].title(), f"Rice, breads, gravies, vegetables and accompaniments balanced for the core meal."),
        (meal_slots[2].title(), f"Sweets, desserts or light closing items planned around the service style."),
        ("Beverages", f"Water, filter coffee, tea, juices or event-appropriate beverages can be sequenced separately."),
    ]
    sample=[
        ("Welcome", f"{pick(['filter coffee','fresh lime','badam milk','herbal drink','seasonal juice'],seed,101).title()} with {pick(['mini vadai','veg cutlet','sundal','mini samosa','paniyaram'],seed,102)}"),
        ("Main course", f"{pick(['steamed rice','vegetable pulao','jeera rice','lemon rice','ghee rice'],seed,103).title()}, {pick(['sambar','dal tadka','vegetable kurma','kara kuzhambu','paneer gravy'],seed,104)}, poriyal, curd and accompaniments"),
        ("Signature addition", f"{pick(counters,seed,105).title()} or another live element selected after venue review"),
        ("Sweet finish", f"{pick(['payasam','gulab jamun','kesari','rasmalai','carrot halwa'],seed,106).title()} with {pick(['fruit','ice cream','beeda','filter coffee'],seed,107)}"),
    ]
    custom=[
        ("Spice & regional preference", f"Adjust spice, familiar dishes and regional balance for the families or guests attending {t.lower()}."),
        ("Dietary requirements", "Identify Jain, vegan, gluten-aware, allergy-related or other dietary needs early so the feasible menu can be discussed."),
        ("Course depth", "Add or reduce sweets, starters, rice choices, breads and counters based on time, budget and guest expectations."),
        ("Service timing", f"Sequence food around the key moments of the {event_noun}, not merely a generic lunch or dinner clock."),
    ]
    capacity=[
        ("Intimate", "Focused service plans for smaller guest lists where freshness and timing matter more than a large buffet footprint."),
        ("Medium", "Balanced batch cooking and replenishment for typical family, community and business functions."),
        ("Large", "Additional counters, service lanes, holding equipment and staffing can be planned after venue and guest-count review."),
    ]
    process=[
        ("1. Enquiry", f"Share the date and tell us you are planning {t.lower()} in Vellore."),
        ("2. Requirement call", "Discuss guest count, venue, meal timing, dietary needs and preferred service format."),
        ("3. Menu proposal", "Shortlist dishes, counters and service details; tasting can be discussed where appropriate and available."),
        ("4. Confirmation", "Freeze the agreed scope, event timings, logistics and commercial terms."),
        ("5. Event execution", "Production, dispatch, setup, service and replenishment follow the confirmed event plan."),
    ]
    hygiene=[
        "Ingredient sourcing and menu quantities are planned before production.",
        "Preparation zones and utensils are organised for the agreed menu.",
        "Food is dispatched in batches suited to travel time and service sequence.",
        "Hot and cold service handling is discussed according to menu and venue facilities.",
        "Allergy and special-diet requests should be declared before menu confirmation."
    ]
    infra=[
        ("Production planning", f"Batch sizes are matched to the {t.lower()} guest estimate and serving window."),
        ("Service equipment", "Buffet warmers, serving vessels, counters and dining accessories are scoped according to the final format."),
        ("Transport", "Dispatch timing is coordinated with distance, venue access and setup time in and around Vellore."),
        ("Contingency", "Critical service items and replenishment timing are reviewed before larger functions."),
    ]
    chefs=[
        ("Menu lead", "Coordinates cuisine balance, production sequence and consistency across batches."),
        ("Kitchen team", "Handles preparation and finishing according to the finalised menu and quantities."),
        ("Service team", "Manages guest-facing service, replenishment and counter flow at the venue."),
    ]
    scenario_guest=100 + hnum(seed+"guest", 701)
    scenario=f"Illustrative planning scenario: a {scenario_guest}-guest {event_noun} in Vellore with {styles[0]}, a {len(sample)+1}-part menu and one live counter. The planning focus would be {ctx}. This is an example workflow, not a claim about a specific past client event."
    prices=[
        ("Guest count", "Higher or lower quantities change production, transport and staffing requirements."),
        ("Menu breadth", "Additional starters, sweets, breads, premium ingredients and counters add preparation complexity."),
        ("Service format", f"{styles[0].title()}, {styles[-1]} and full-service staffing have different equipment and labour needs."),
        ("Venue logistics", "Distance, access time, kitchen availability, stairs/lifts and setup constraints can affect the quotation."),
    ]
    packages=[
        ("Essential", f"A concise {t.lower()} menu with practical service and fewer moving parts."),
        ("Signature", "A broader menu with extra courses, upgraded presentation and selected live service elements."),
        ("Celebration", "A fuller event experience with more menu variety, live counters and enhanced guest-facing service."),
    ]
    food_diff=[
        ("Menu coherence", "Dishes are selected to work together across the meal instead of building an oversized list with conflicting flavours."),
        ("Service-aware cooking", "Preparation and finishing choices consider how long food travels, holds and reaches guests."),
        ("Local preferences", "Tamil and South Indian staples can remain central while other cuisines are added only where they fit the event."),
    ]
    peers=related_type_links(item,catalog)
    guides=[GUIDE_DATA[(hnum(seed+"g",len(GUIDE_DATA))+i)%len(GUIDE_DATA)] for i in range(3)]

    meta=f'''  <title>{E(title)}</title>\n  <meta name="description" content="{E(desc)}">\n  <link rel="canonical" href="{page_url(item['output'])}">\n  <link rel="alternate" hreflang="en-IN" href="{page_url(item['output'])}">\n  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">\n  <meta property="og:locale" content="en_IN">\n  <meta property="og:site_name" content="Vellore Catering">\n  <meta property="og:type" content="website">\n  <meta property="og:title" content="{E(title)}">\n  <meta property="og:description" content="{E(desc)}">\n  <meta property="og:url" content="{page_url(item['output'])}">\n  <meta property="og:image" content="{E(og)}">\n  <meta property="og:image:width" content="1200">\n  <meta property="og:image:height" content="630">\n  <meta name="twitter:card" content="summary_large_image">\n  <meta name="twitter:title" content="{E(title)}">\n  <meta name="twitter:description" content="{E(desc)}">\n  <meta name="twitter:image" content="{E(og)}">\n  <meta name="geo.region" content="IN-TN">\n  <meta name="geo.placename" content="Vellore">\n{page_schema(item,title,desc,faqs,item['output'])}'''

    service_cards=''.join(f'''<article class="service-link-card" data-reveal><h3><a href="{href}">{E(name)}</a></h3><p>{E(copy)}</p></article>''' for name,href,copy in service_links())
    peer_html=''.join(f'<li><a href="{p["slug"]}.html">{E(p["catering_type"])}</a></li>' for p in peers)
    guide_html=''.join(f'<article class="article-card" data-reveal><h3><a href="../guides/{g[0]}.html">{E(g[1])}</a></h3><p>{E(g[2])}</p></article>' for g in guides)

    body=f'''<!DOCTYPE html>
<!-- Vellore Catering | {item['output']} | GENERATED V2 from uploaded Catering Types workbook -->
<html lang="en-IN">
<head>
  <!-- @head:start -->
  <!-- @head:end -->
{meta}</head>
<body data-wa="{CONFIG['whatsapp']}" data-page-key="{E(slug)}">
  <!-- @nav:start -->
  <!-- @nav:end -->
  <main id="main">
    <!-- 2 Breadcrumbs -->
    <section class="page-hero page-hero--catalog">
      <div class="page-hero__media"><img src="{hero}" width="1600" height="900" alt="Illustrative visual for {E(t)} in Vellore" fetchpriority="high" decoding="async"></div>
      <div class="container">{breadcrumb_html(item)}<p class="section-kicker" data-reveal>{E(cats)}</p><h1 class="gilded" data-reveal style="--d:1">{E(t)} in Vellore</h1><p class="lead" data-reveal style="--d:2">{E(item['description'])}. Plan the menu, service format and event logistics around your guest list and venue.</p><div class="btn-row" data-reveal style="--d:3"><a class="btn btn--gold" href="tel:{CONFIG['phone_e164']}">{icon('phone',20)} Call {CONFIG['phone_short']}</a><a class="btn btn--wa" href="https://wa.me/{CONFIG['whatsapp']}?text={quote('Hello Vellore Catering, I need a quote for '+t+'.')}" target="_blank" rel="noopener">{icon('wa',20)} WhatsApp quote</a></div></div>
    </section>

    <!-- 4 Trust / USP Strip -->
    <section class="trust-strip"><div class="container trust-strip__grid"><div><strong data-since="{CONFIG['founded']}">25+</strong><span>years serving Vellore</span></div><div><strong>{E(CONFIG['events_served'])}</strong><span>events referenced by the master site</span></div><div><strong>Custom</strong><span>menus & service formats</span></div><div><strong>Direct</strong><span>WhatsApp enquiry flow</span></div></div></section>

    <!-- 5 Introduction -->
    <section id="introduction"><div class="container split split--catalog"><div data-reveal="left"><img class="catalog-media" src="{gallery1}" width="900" height="700" loading="lazy" alt="Generated illustration representing {E(t.lower())} planning"></div><div>{section_head('Service overview',f'Planning {t} in Vellore',f'{t} works best when menu, timing and service are planned together.')}<p>{E(t)} is intended for {E(item['description'].lower())}. For this page, the planning emphasis is {E(ctx)}.</p><p>Share the venue, approximate guest count, meal timing and food preferences. The catering scope can then be shaped around the real event rather than a generic package.</p></div></div></section>

    <!-- 6 Why Choose Us -->
    <section class="band" id="why-choose-us"><div class="container">{section_head('Why choose us',f'A practical approach to {t}', 'Clear planning before cooking helps reduce last-minute service problems.')} {cards(why)}</div></section>

    <!-- 7 Catering Services Included -->
    <section id="included"><div class="container">{section_head('What is included',f'{t} service scope','The exact scope is finalised with the quotation; these are the normal planning components.')} {bullets(includes)}</div></section>

    <!-- 8 Types of Events Served -->
    <section class="band" id="event-types"><div class="container">{section_head('Event formats',f'Ways we can structure {t}', 'Service can be scaled to suit the guest list, venue and timetable.')} {cards(event_types)}</div></section>

    <!-- 9 Menu Categories -->
    <section id="menu-categories"><div class="container">{section_head('Menu categories',f'Build a balanced {t} menu','Choose courses according to the time of day and how guests will be served.')} {cards(menu_cats)}</div></section>

    <!-- 10 Cuisine Options -->
    <section class="band" id="cuisines"><div class="container">{section_head('Cuisine choices',f'Cuisine options for {t}','Keep one clear flavour direction or combine cuisines carefully.')} {bullets([x.title() for x in cuisines])}</div></section>

    <!-- 11 Sample Menus -->
    <section id="sample-menu"><div class="container">{section_head('Sample menu',f'An example {t} menu structure','This is an illustrative starting point; every final menu should be confirmed separately.')} {cards(sample)}</div></section>

    <!-- 12 Customization Options -->
    <section class="band" id="customisation"><div class="container">{section_head('Customisation',f'Adapt {t} to your guests','The best menu is the one that fits your event rather than the longest menu.')} {cards(custom)}</div></section>

    <!-- 13 Live Food Counters -->
    <section id="live-counters"><div class="container">{section_head('Live counters',f'Live food ideas for {t}','Counters should add theatre without creating queues or slowing the main meal.')} {bullets([x.title() for x in counters])}</div></section>

    <!-- 14 Traditional Service Styles -->
    <section class="band" id="service-styles"><div class="container">{section_head('Service styles',f'Service formats for {t}','Venue layout, guest profile and meal duration influence the right format.')} {bullets([x.title() for x in styles])}</div></section>

    <!-- 15 Guest Capacity -->
    <section id="capacity"><div class="container">{section_head('Guest capacity',f'Planning {t} at different scales','Capacity depends on menu complexity, venue facilities, staffing and service window.')} {cards(capacity)}</div></section>

    <!-- 16 Event Process -->
    <section class="band" id="process"><div class="container">{section_head('Event process',f'From enquiry to {t} service','A simple sequence keeps decisions clear.')} <ol class="process-grid">{''.join(f'<li data-reveal><h3>{E(a)}</h3><p>{E(b)}</p></li>' for a,b in process)}</ol></div></section>

    <!-- 17 Food Quality & Hygiene -->
    <section id="hygiene"><div class="container">{section_head('Food quality & hygiene',f'Food handling for {t}','Discuss food safety expectations at the same time as menu choices.')} {bullets(hygiene)}</div></section>

    <!-- 18 Kitchen / Infrastructure -->
    <section class="band" id="infrastructure"><div class="container">{section_head('Kitchen & infrastructure',f'Production and logistics behind {t}','Good service starts before the food reaches the venue.')} {cards(infra)}</div></section>

    <!-- 19 Our Chefs & Team -->
    <section id="team"><div class="container">{section_head('Our chefs & team',f'Roles that support {t}','Different people own production, coordination and guest-facing service.')} {cards(chefs)}</div></section>

    <!-- 20 Event Gallery -->
    <section class="band" id="event-gallery"><div class="container">{section_head('Event gallery',f'{t} visual direction','Generated, copyright-free illustrations for planning inspiration; they are not presented as photographs of past client events.')}<div class="media-grid"><figure data-reveal><img src="{hero}" width="1600" height="900" loading="lazy" alt="Illustrative {E(t)} event setup"><figcaption>Illustrative event setup</figcaption></figure><figure data-reveal><video class="page-motion" muted loop playsinline preload="none" poster="{gallery2}" data-src="{video}" aria-label="Abstract motion graphic for {E(t)}"></video><figcaption>Original abstract motion loop for this page</figcaption></figure></div></div></section>

    <!-- 21 Food Gallery -->
    <section id="food-gallery"><div class="container">{section_head('Food gallery',f'Food presentation ideas for {t}','These original illustrations are visual placeholders until you add your own real event photography.')}<div class="media-grid media-grid--three"><figure data-reveal><img src="{gallery1}" width="900" height="700" loading="lazy" alt="Illustrated menu presentation for {E(t)}"><figcaption>Menu presentation</figcaption></figure><figure data-reveal><img src="{gallery2}" width="900" height="700" loading="lazy" alt="Illustrated buffet detail for {E(t)}"><figcaption>Service detail</figcaption></figure><figure data-reveal><img src="{gallery3}" width="900" height="700" loading="lazy" alt="Illustrated food counter for {E(t)}"><figcaption>Counter inspiration</figcaption></figure></div></div></section>

    <!-- 22 Recent Events / Case Studies -->
    <section class="band" id="case-study"><div class="container">{section_head('Case-study format',f'How a {t} plan can come together','No client event is invented here; this transparent sample shows the planning logic.')}<div class="scenario-card" data-reveal><p>{E(scenario)}</p><ul class="inline-links">{peer_html}</ul></div></div></section>

    <!-- 23 Customer Testimonials -->
    <section id="testimonials"><div class="container">{section_head('Customer testimonials',f'Verified feedback for {t}','This build intentionally contains no fabricated testimonials. Replace this notice only with feedback you have permission to publish.')}<div class="truth-card" data-reveal><h3>Publish real reviews only</h3><p>When you receive verified feedback about {E(t.lower())}, add the customer-approved wording here with the event type and month. Avoid invented names, ratings or quotes.</p></div></div></section>

    <!-- 24 Google Reviews -->
    <section class="band" id="google-reviews"><div class="container">{section_head('Google reviews',f'Check Vellore Catering on Google','The website does not hard-code a star rating or review count because those values change.')}<p class="center-copy">Use the live Google result to view current public feedback before booking.</p><div class="btn-row btn-row--center"><a class="btn btn--ghost" href="https://www.google.com/maps/search/?api=1&amp;query={quote('Vellore Catering, '+CONFIG['street']+', Vellore '+CONFIG['pin'])}" target="_blank" rel="noopener">Open Google Maps</a></div></div></section>

    <!-- 25 Venues We Cater At -->
    <section id="venues"><div class="container">{section_head('Venue types',f'Venues suitable for {t}','Confirm access, water, power, loading space and dining layout before finalising the service plan.')} {bullets([x.title() for x in venues])}</div></section>

    <!-- 26 Areas We Serve -->
    <section class="band" id="areas"><div class="container">{section_head('Areas we serve',f'{t} across Vellore and nearby areas','Availability and travel logistics are confirmed for the event date.')} {bullets(areas)}<p class="muted">Business base: {E(CONFIG['street'])}, Vellore, Tamil Nadu {E(CONFIG['pin'])}.</p></div></section>

    <!-- 27 Pricing / Cost Guide -->
    <section id="pricing"><div class="container">{section_head('Pricing guide',f'What affects {t} cost in Vellore','A responsible quote uses your actual requirements instead of an unrealistic universal per-plate figure.')} {cards(prices)}</div></section>

    <!-- 28 Packages -->
    <section class="band" id="packages"><div class="container">{section_head('Packages',f'Flexible {t} package directions','Package names describe scope only; final pricing follows the confirmed menu and event details.')} {cards(packages,'content-cards content-cards--three')}</div></section>

    <!-- 29 FAQs -->
    <section id="faqs"><div class="container narrow">{section_head('FAQs',f'Questions about {t} in Vellore','Useful answers before you send an enquiry.')}<div class="faq">{''.join(f'<details><summary>{E(q)}</summary><div><p>{E(a)}</p></div></details>' for q,a in faqs)}</div></div></section>

    <!-- 30 Why Our Food Is Different -->
    <section class="band" id="food-difference"><div class="container">{section_head('Food philosophy',f'What makes a stronger {t} menu','The goal is consistency, suitability and a pleasant guest experience.')} {cards(food_diff,'content-cards content-cards--three')}</div></section>

    <!-- 31 Booking / Enquiry CTA -->
    <section id="enquire"><div class="container enquire"><div>{section_head('Book / enquire',f'Get a {t.lower()} quote','Send the three essentials first; the discussion can continue on WhatsApp.')}<p>Include your venue and approximate guest count in the WhatsApp conversation after the form opens.</p></div>{wa_form('enq-'+slug,t,heading=f'Enquire for {t}',intro='Name, contact number and event date are enough to start the conversation.')}</div></section>

    <!-- 32 Contact Information -->
    <section class="band" id="contact"><div class="container">{section_head('Contact',f'Talk to Vellore Catering about {t}','Call or WhatsApp for date availability and a menu discussion.')}<div class="contact-mini"><div><strong>Phone</strong><a href="tel:{CONFIG['phone_e164']}">{E(CONFIG['phone_display'])}</a></div><div><strong>WhatsApp</strong><a href="https://wa.me/{CONFIG['whatsapp']}" target="_blank" rel="noopener">{E(CONFIG['phone_short'])}</a></div><div><strong>Address</strong><span>{E(CONFIG['street'])}, Vellore, Tamil Nadu {E(CONFIG['pin'])}</span></div></div></div></section>

    <!-- 33 Google Map -->
    <section id="map"><div class="container">{section_head('Map & directions',f'Find our Vellore base','Open the map for directions; event service is coordinated separately to your venue.')}<div class="map-shell"><iframe title="Vellore Catering location map" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="https://www.google.com/maps?q={quote(CONFIG['business_name']+', '+CONFIG['street']+', '+CONFIG['city']+' '+CONFIG['pin'])}&amp;output=embed"></iframe></div></div></section>

    <!-- 34 Related Services: exactly four core services -->
    <section class="band" id="related-services"><div class="container">{section_head('Related services','Four core catering services','Every catering page uses the same four core service routes for a simple, consistent conversion path.')}<div class="service-links-grid">{service_cards}</div></div></section>

    <!-- 35 Related Articles -->
    <section id="related-articles"><div class="container">{section_head('Planning guides',f'Articles related to {t}','Use these guides to prepare your guest count, budget questions and service preferences before enquiring.')}<div class="article-grid">{guide_html}</div></div></section>
  </main>
  <!-- 36 Footer -->
  <!-- @footer:start -->
  <!-- @footer:end -->
  <script src="../assets/js/main.js?v={CONFIG['asset_version']}" defer></script>
</body>
</html>'''
    # Make editorial paragraphs page-specific while keeping the shared layout and
    # required four-service navigation consistent. This avoids boilerplate copy
    # being repeated verbatim across hundreds of SEO landing pages.
    paragraph_counter = [0]
    def _contextualise_paragraph(match):
        attrs, inner = match.group(1), match.group(2)
        plain = re.sub(r"<[^>]+>", " ", inner)
        plain = re.sub(r"\s+", " ", plain).strip().lower()
        # If the paragraph already names the exact service, it is inherently page-specific.
        if t.lower() in plain:
            return match.group(0)
        variants = [
            f"For {t.lower()}, this supports {ctx}.",
            f"For {t.lower()}, this detail is checked against the venue and guest profile.",
            f"The final {t.lower()} choice is confirmed with the event schedule.",
            f"For {t.lower()} as a {event_noun}, the detail is adapted before confirmation.",
        ]
        suffix = variants[paragraph_counter[0] % len(variants)]
        paragraph_counter[0] += 1
        return f"<p{attrs}>{inner} <span class=\"page-context\">{E(suffix)}</span></p>"
    body = re.sub(r"<p([^>]*)>(.*?)</p>", _contextualise_paragraph, body, flags=re.S)
    return body


def render_other_page(catalog, groups):
    output="services/other-caterings-in-vellore.html"
    title="Other Catering Services in Vellore | Vellore Catering"
    desc="Browse Vellore Catering services by occasion, cuisine, service format, institution, festival, venue and dietary requirement, with direct WhatsApp enquiries."
    group_html=[]
    for cat, items in groups:
        lis=''.join(f'<li><a href="{p["slug"]}.html">{E(p["catering_type"])}</a></li>' for p in items)
        group_html.append(f'<section class="catalog-group" id="{slugish(cat)}"><h2 class="gilded">{E(cat)}</h2><ul class="catalog-link-grid">{lis}</ul></section>')
    meta=f'''<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{page_url(output)}"><meta name="robots" content="index,follow,max-image-preview:large">{jsonld(business_schema(),website_schema(),breadcrumb_schema([('Home','index.html'),('Catering Services','services/index.html'),('Other Caterings',output)]))}'''
    return f'''<!DOCTYPE html><html lang="en-IN"><head><!-- @head:start --><!-- @head:end -->{meta}</head><body data-wa="{CONFIG['whatsapp']}"><!-- @nav:start --><!-- @nav:end --><main id="main"><section class="page-hero page-hero--compact"><div class="container"><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="../index.html">Home</a></li><li><a href="index.html">Catering services</a></li><li><span aria-current="page">Other Caterings</span></li></ol></nav><p class="section-kicker">Complete catalogue</p><h1 class="gilded">Other Catering Services in Vellore</h1><p class="lead">Browse the full catalogue from the uploaded Catering Type list. Each item opens a dedicated page.</p></div></section><section><div class="container"><div class="catalog-search"><label for="catalog-filter">Find a catering type</label><input id="catalog-filter" data-catalog-filter type="search" placeholder="Try wedding, office lunch, Jain, buffet…"></div>{''.join(group_html)}</div></section></main><!-- @footer:start --><!-- @footer:end --><script src="../assets/js/main.js?v={CONFIG['asset_version']}" defer></script></body></html>'''


def render_services_index(groups):
    output="services/index.html"
    title="Catering Services in Vellore | 236 Service Types"
    desc="Explore wedding, birthday, seemandham, corporate, traditional, festival, cuisine, buffet, dietary and other catering services in Vellore."
    cats=[]
    for cat,items in groups:
        preview=', '.join(x['catering_type'].replace(' Catering','') for x in items[:4])
        cats.append(f'<article class="category-card" data-reveal><h2>{E(cat)}</h2><p>{len(items)} catering types including {E(preview)}.</p><a class="text-link" href="other-caterings-in-vellore.html#{slugish(cat)}">View {E(cat.lower())}</a></article>')
    meta=f'''<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{page_url(output)}"><meta name="robots" content="index,follow,max-image-preview:large">{jsonld(business_schema(),website_schema(),breadcrumb_schema([('Home','index.html'),('Catering Services',output)]))}'''
    return f'''<!DOCTYPE html><html lang="en-IN"><head><!-- @head:start --><!-- @head:end -->{meta}</head><body data-wa="{CONFIG['whatsapp']}"><!-- @nav:start --><!-- @nav:end --><main id="main"><section class="page-hero page-hero--compact"><div class="container"><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="../index.html">Home</a></li><li><span aria-current="page">Catering services</span></li></ol></nav><p class="section-kicker">Vellore catering catalogue</p><h1 class="gilded">Catering Services in Vellore</h1><p class="lead">236 dedicated service pages grouped into 16 catering categories, with menus, planning guidance, FAQs and WhatsApp enquiry forms.</p><div class="btn-row"><a class="btn btn--gold" href="wedding-catering-in-vellore.html">Wedding catering</a><a class="btn btn--ghost" href="other-caterings-in-vellore.html">Browse all caterings</a></div></div></section><section><div class="container"><div class="category-grid">{''.join(cats)}</div></div></section></main><!-- @footer:start --><!-- @footer:end --><script src="../assets/js/main.js?v={CONFIG['asset_version']}" defer></script></body></html>'''


def render_guide(slug,title,desc):
    output=f"guides/{slug}.html"
    topics={
        "event-catering-checklist-vellore":["Confirm the date, venue and meal window", "Estimate guests by adults, children and special dietary needs", "Check loading access, water, power and dining layout", "Freeze the service format and key menu courses", "Agree the final change deadline and event-day contact"],
        "catering-cost-guide-vellore":["Guest count and buffer", "Number of courses and premium ingredients", "Live counters and equipment", "Service staff and dining format", "Travel, venue access and setup requirements"],
        "catering-menu-planning-vellore":["Start with event timing", "Choose a clear cuisine direction", "Balance rich and light dishes", "Plan dietary options", "Keep desserts and beverages proportional"],
        "guest-count-food-planning":["Use confirmed RSVPs where possible", "Separate adults and young children", "Add a sensible buffer rather than guessing high", "Plan batch replenishment", "Review leftovers after service to improve future estimates"],
        "live-counter-planning-vellore":["Limit counters to meaningful choices", "Position queues away from the main buffet", "Confirm power or fuel requirements", "Assign dedicated counter staff", "Plan replenishment and closing time"],
        "catering-hygiene-checklist":["Discuss water and ingredient handling", "Ask how food will travel and hold", "Declare allergies early", "Keep raw and ready-to-eat handling separate", "Confirm service utensils and waste clearing"],
    }
    items=topics[slug]
    meta=f'''<title>{E(title)} | Vellore Catering</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{page_url(output)}"><meta name="robots" content="index,follow,max-image-preview:large">{jsonld(business_schema(),website_schema(),breadcrumb_schema([('Home','index.html'),('Guides','guides/index.html'),(title,output)]))}'''
    body=''.join(f'<article class="guide-step" data-reveal><span>{i+1:02d}</span><div><h2>{E(x)}</h2><p>{E(desc)} Use this checkpoint as a prompt when discussing your requirements with a caterer in Vellore.</p></div></article>' for i,x in enumerate(items))
    return f'''<!DOCTYPE html><html lang="en-IN"><head><!-- @head:start --><!-- @head:end -->{meta}</head><body data-wa="{CONFIG['whatsapp']}"><!-- @nav:start --><!-- @nav:end --><main id="main"><section class="page-hero page-hero--compact"><div class="container"><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="../index.html">Home</a></li><li><a href="index.html">Guides</a></li><li><span aria-current="page">{E(title)}</span></li></ol></nav><p class="section-kicker">Planning guide</p><h1 class="gilded">{E(title)}</h1><p class="lead">{E(desc)}</p></div></section><section><div class="container narrow"><div class="guide-list">{body}</div><div class="cta-panel"><h2>Need a catering quote?</h2><p>Use a service page or WhatsApp Vellore Catering with your event date, venue and approximate guest count.</p><a class="btn btn--gold" href="../services/index.html">Browse catering services</a></div></div></section></main><!-- @footer:start --><!-- @footer:end --><script src="../assets/js/main.js?v={CONFIG['asset_version']}" defer></script></body></html>'''


def render_guides_index():
    cards_html=''.join(f'<article class="article-card"><h2><a href="{slug}.html">{E(title)}</a></h2><p>{E(desc)}</p></article>' for slug,title,desc in GUIDE_DATA)
    cards_html='<article class="article-card"><p class="section-kicker">500 articles</p><h2><a href="blogs/index.html">Catering Blogs</a></h2><p>Explore detailed articles on wedding catering in Vellore, birthday catering in Vellore, seemandham catering in Vellore, menus, service styles, venues, budgeting and event planning.</p></article>'+cards_html
    output='guides/index.html'; title='Catering Planning Guides for Vellore'; desc='Practical Vellore catering guides for menus, guest counts, quotations, event checklists, live counters and food hygiene discussions.'
    meta=f'''<title>{E(title)} | Vellore Catering</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{page_url(output)}"><meta name="robots" content="index,follow,max-image-preview:large">{jsonld(business_schema(),website_schema(),breadcrumb_schema([('Home','index.html'),('Guides',output)]))}'''
    return f'''<!DOCTYPE html><html lang="en-IN"><head><!-- @head:start --><!-- @head:end -->{meta}</head><body data-wa="{CONFIG['whatsapp']}"><!-- @nav:start --><!-- @nav:end --><main id="main"><section class="page-hero page-hero--compact"><div class="container"><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="../index.html">Home</a></li><li><span aria-current="page">Guides</span></li></ol></nav><p class="section-kicker">Resource centre</p><h1 class="gilded">Catering Planning Guides for Vellore</h1><p class="lead">Use these practical guides before you request a quotation or finalise a menu.</p></div></section><section><div class="container"><div class="article-grid">{cards_html}</div></div></section></main><!-- @footer:start --><!-- @footer:end --><script src="../assets/js/main.js?v={CONFIG['asset_version']}" defer></script></body></html>'''


def build_groups(catalog):
    order=[]; mapping={}
    for item in catalog:
        for cat in item['categories']:
            if cat not in mapping:
                mapping[cat]=[]; order.append(cat)
            mapping[cat].append(item)
    return [(cat,mapping[cat]) for cat in order]


def main():
    data=json.loads(CATALOG.read_text(encoding='utf-8'))
    catalog=data['items']; groups=build_groups(catalog)
    SERVICES.mkdir(exist_ok=True); GUIDES.mkdir(exist_ok=True); MEDIA.mkdir(parents=True,exist_ok=True)
    expected=set()
    for item in catalog:
        target=ROOT/item['output']; target.write_text(render_page(item,catalog),encoding='utf-8'); expected.add(target.resolve())
    other=SERVICES/'other-caterings-in-vellore.html'; other.write_text(render_other_page(catalog,groups),encoding='utf-8'); expected.add(other.resolve())
    idx=SERVICES/'index.html'; idx.write_text(render_services_index(groups),encoding='utf-8'); expected.add(idx.resolve())
    GUIDES.joinpath('index.html').write_text(render_guides_index(),encoding='utf-8')
    for g in GUIDE_DATA:
        GUIDES.joinpath(g[0]+'.html').write_text(render_guide(*g),encoding='utf-8')
    print(f'generate_catalog_site: built {len(catalog)} catering pages + services catalogue + {len(GUIDE_DATA)} guides')

if __name__=='__main__':
    main()
