#!/usr/bin/env python3
"""
sitekit.py — shared helpers for the Vellore Catering World site tools.   Version: V1

Imported by generate_pages.py (bulk pages) and build_sitemap.py.
Keeps every generated page consistent: same meta tags, same image markup,
same WhatsApp form, same schema.
"""
import html
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "tools" / "site_config.json").read_text(encoding="utf-8"))

esc = html.escape


# ---------------------------------------------------------------- URLs
def page_url(rel_path: str) -> str:
    """Absolute canonical URL for a page path like 'services/index.html'."""
    rel = rel_path.replace("\\", "/")
    if rel == "index.html":
        rel = ""
    elif rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]
    return CONFIG["site_url"].rstrip("/") + "/" + rel


def asset_url(rel: str) -> str:
    return CONFIG["site_url"].rstrip("/") + "/" + rel.lstrip("/")


def depth_prefix(rel_path: str) -> str:
    return "../" * rel_path.replace("\\", "/").count("/")


def wa_link(text: str) -> str:
    return f"https://wa.me/{CONFIG['whatsapp']}?text={quote(text)}"


# ---------------------------------------------------------------- images
# Photos are free-licence Pexels images (https://www.pexels.com/license/).
# tools/localize_media.py downloads them into assets/img/photos/ for self-hosting.
def px(photo_id, w, h=None, ext="jpeg"):
    u = f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.{ext}?auto=compress&cs=tinysrgb&w={w}"
    if h:
        u += f"&h={h}&fit=crop"
    return u


def img(photo_id, alt, w, h, widths=(480, 800, 1200), sizes="100vw",
        lazy=True, cls="", ext="jpeg", attrs=""):
    ratio = h / w
    widths = sorted(set(x for x in widths if x <= max(w, 480)) | {w})
    srcset = ", ".join(f"{px(photo_id, x, round(x * ratio), ext)} {x}w" for x in widths)
    parts = [
        f'<img src="{esc(px(photo_id, w, h, ext))}"',
        f'srcset="{esc(srcset)}"',
        f'sizes="{sizes}"',
        f'width="{w}" height="{h}"',
        f'alt="{esc(alt)}"',
        'decoding="async"',
    ]
    parts.append('loading="lazy"' if lazy else 'fetchpriority="high"')
    if cls:
        parts.append(f'class="{cls}"')
    if attrs:
        parts.append(attrs)
    return " ".join(parts) + ">"


# ---------------------------------------------------------------- icons
ICONS = {
    "phone": '<path d="M6.6 10.8a15.2 15.2 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z" fill="currentColor"/>',
    "wa": '<path fill="currentColor" d="M12 2.2a9.8 9.8 0 0 0-8.4 14.8L2.2 21.8l4.9-1.3A9.8 9.8 0 1 0 12 2.2zm0 17.9a8.1 8.1 0 0 1-4.1-1.1l-.3-.2-2.9.8.8-2.8-.2-.3A8.1 8.1 0 1 1 12 20.1zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.6.8-.8 1-.3.2-.5.1a6.6 6.6 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3a.4.4 0 0 0 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6a2.7 2.7 0 0 0 1.8-1.2 2.2 2.2 0 0 0 .1-1.2c0-.1-.2-.2-.4-.3z"/>',
    "pin": '<path d="M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="10" r="2.6" fill="none" stroke="currentColor" stroke-width="1.6"/>',
    "leaf": '<path d="M4 20C4 10 10 4 20 4c0 10-6 16-16 16zM4 20l9-9" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
    "clock": '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M12 7v5l3 2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
    "pot": '<path d="M4 10h16M6 10v6a4 4 0 0 0 4 4h4a4 4 0 0 0 4-4v-6M9 6c0-1 1-1.5 1-2.5M13 6c0-1 1-1.5 1-2.5M2.5 12H4M20 12h1.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
    "shield": '<path d="M12 3l7 3v5c0 5-3.2 8.6-7 10-3.8-1.4-7-5-7-10V6z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M8.8 12.2l2.2 2.2 4.3-4.6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
    "users": '<circle cx="9" cy="8" r="3.2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M3 20c.6-3.6 3-5.5 6-5.5s5.4 1.9 6 5.5M15.5 5.2a3 3 0 0 1 0 5.8M17.5 14.8c2 .6 3.2 2.3 3.5 5.2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
    "menu": '<path d="M6 3h12v18H6zM9 8h6M9 12h6M9 16h4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
    "chev-l": '<path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    "chev-r": '<path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    "up": '<path d="M5 15l7-7 7 7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
}


def icon(name, size=22):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" aria-hidden="true" '
            f'focusable="false">{ICONS[name]}</svg>')


def pulli():
    return '<span class="pulli" aria-hidden="true"><i></i><i></i><i></i></span>'


# ---------------------------------------------------------------- head meta
def head_meta(rel_path, title, description, image=None, og_type="website", extra=""):
    """Per-page metadata block (sits OUTSIDE the @head sync markers)."""
    url = page_url(rel_path)
    image = image or asset_url(CONFIG["og_image"])
    return f"""  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{url}">
  <link rel="alternate" hreflang="en-IN" href="{url}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <meta property="og:locale" content="en_IN">
  <meta property="og:site_name" content="{esc(CONFIG['business_name'])}">
  <meta property="og:type" content="{og_type}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{esc(image)}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{esc(image)}">
  <meta name="geo.region" content="IN-{CONFIG['region_code']}">
  <meta name="geo.placename" content="{CONFIG['city']}">
{extra}"""


# ---------------------------------------------------------------- schema
def business_ref():
    return {"@id": CONFIG["site_url"].rstrip("/") + "/#business"}


def business_schema():
    c = CONFIG
    return {
        "@type": ["FoodEstablishment", "LocalBusiness"],
        "@id": c["site_url"].rstrip("/") + "/#business",
        "name": c["business_name"],
        "description": "Wedding, engagement, birthday and seemandham caterers in Vellore, Tamil Nadu, serving traditional South Indian vegetarian and non-vegetarian menus since 2000.",
        "url": c["site_url"].rstrip("/") + "/",
        "telephone": c["phone_e164"],
        "image": asset_url(c["og_image"]),
        "logo": asset_url("assets/img/logo.svg"),
        "foundingDate": str(c["founded"]),
        "servesCuisine": ["South Indian", "Tamil", "Chettinad", "Biryani", "North Indian"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": c["street"],
            "addressLocality": c["city"],
            "addressRegion": c["region_code"],
            "postalCode": c["pin"],
            "addressCountry": c["country"],
        },
        "hasMap": "https://www.google.com/maps/search/?api=1&query=" + quote(f"{c['business_name']}, {c['street']}, {c['city']} {c['pin']}"),
        "areaServed": [{"@type": "City", "name": a} for a in c["areas_served"]],
        "contactPoint": {
            "@type": "ContactPoint",
            "telephone": c["phone_e164"],
            "contactType": "customer service",
            "areaServed": "IN",
            "availableLanguage": ["en", "ta"],
        },
        "sameAs": [],
    }


def website_schema():
    return {
        "@type": "WebSite",
        "@id": CONFIG["site_url"].rstrip("/") + "/#website",
        "url": CONFIG["site_url"].rstrip("/") + "/",
        "name": CONFIG["business_name"],
        "inLanguage": "en-IN",
        "publisher": business_ref(),
    }


def breadcrumb_schema(trail):
    """trail: list of (name, rel_path)"""
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": page_url(p)}
            for i, (n, p) in enumerate(trail)
        ],
    }


def faq_schema(faqs):
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs
        ],
    }


def service_schema(name, description, rel_path, service_type):
    return {
        "@type": "Service",
        "name": name,
        "serviceType": service_type,
        "description": description,
        "url": page_url(rel_path),
        "provider": business_ref(),
        "areaServed": {"@type": "City", "name": CONFIG["city"]},
    }


def jsonld(*nodes):
    data = {"@context": "https://schema.org", "@graph": list(nodes)}
    return ('  <script type="application/ld+json">\n'
            + json.dumps(data, ensure_ascii=False, indent=2)
            + "\n  </script>\n")


# ---------------------------------------------------------------- shared blocks
def breadcrumb(trail):
    """Visible breadcrumb. trail: list of (name, href or None for current)."""
    items = []
    for name, href in trail:
        if href:
            items.append(f'<li><a href="{href}">{esc(name)}</a></li>')
        else:
            items.append(f'<li><span aria-current="page">{esc(name)}</span></li>')
    return f'<nav class="breadcrumb" aria-label="Breadcrumb"><ol>{"".join(items)}</ol></nav>'


def wa_form(form_id, event_label, heading="Get a quote on WhatsApp",
            intro="Share three details and WhatsApp opens with your enquiry ready to send.",
            heading_tag="h2"):
    c = CONFIG
    fid = form_id
    return f"""<div class="form-card" data-reveal="right">
  <{heading_tag}>{esc(heading)}</{heading_tag}>
  <p>{esc(intro)}</p>
  <form class="form" data-wa-form data-event="{esc(event_label)}" action="https://wa.me/{c['whatsapp']}" method="get" novalidate>
    <div class="field">
      <label for="{fid}-name">Your name</label>
      <input id="{fid}-name" name="name" type="text" autocomplete="name" required minlength="2" placeholder="e.g. Lakshmi Narayanan" aria-describedby="{fid}-name-error">
      <span class="field__error" id="{fid}-name-error" aria-live="polite"></span>
    </div>
    <div class="field">
      <label for="{fid}-phone">Contact number</label>
      <input id="{fid}-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" required placeholder="10-digit mobile number" aria-describedby="{fid}-phone-error">
      <span class="field__error" id="{fid}-phone-error" aria-live="polite"></span>
    </div>
    <div class="field">
      <label for="{fid}-date">Event date</label>
      <input id="{fid}-date" name="event_date" type="date" required aria-describedby="{fid}-date-error">
      <span class="field__error" id="{fid}-date-error" aria-live="polite"></span>
    </div>
    <button class="btn btn--wa btn--block" type="submit">{icon('wa', 20)} Send enquiry on WhatsApp</button>
    <p class="form-status" role="status" aria-live="polite"></p>
    <p class="form__note">Your details go straight to our WhatsApp and are not stored on this website. Prefer to talk? Call <a href="tel:{c['phone_e164']}">{c['phone_short']}</a>.</p>
  </form>
</div>"""


def faq_block(faqs):
    items = "\n".join(
        f'<details><summary>{esc(q)}</summary><div><p>{esc(a)}</p></div></details>'
        for q, a in faqs
    )
    return f'<div class="faq">\n{items}\n</div>'


def page_shell(rel_path, meta_block, main_html, body_class=""):
    """Full HTML page with sync markers. Nav/footer are filled by sync_partials.py."""
    name = rel_path
    cls = f' class="{body_class}"' if body_class else ""
    pre = depth_prefix(rel_path)
    return f"""<!DOCTYPE html>
<!-- Vellore Catering World | {name} | Version: V1 -->
<html lang="en-IN">
<head>
  <!-- @head:start -->
  <!-- @head:end -->

  <!-- per-page metadata: never synced, always unique -->
{meta_block}</head>
<body{cls} data-wa="{CONFIG['whatsapp']}">

  <!-- @nav:start -->
  <!-- @nav:end -->

  <main id="main">
{main_html}
  </main>

  <!-- @footer:start -->
  <!-- @footer:end -->

  <script src="{pre}assets/js/main.js?v={CONFIG['asset_version']}" defer></script>
</body>
</html>
"""
