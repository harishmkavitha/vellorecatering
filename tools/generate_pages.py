#!/usr/bin/env python3
"""
generate_pages.py — build landing pages from data/pages/*.json.   Version: V1

This is how the site grows from 10 pages to 500+ without copy-paste:

    1. Copy data/pages/_example-area-page.json to a new file, e.g.
       data/pages/catering-in-katpadi.json, and write its content.
    2. Set "publish": true and an "output" path, e.g.
       "areas/catering-in-katpadi.html".
    3. Run:  python tools/build.py
       (generate → sync nav/footer → rebuild sitemap.xml)

Rules
  - Files whose name starts with "_" are ignored (drafts/examples).
  - "publish": false keeps a page out of the build.
  - Every page MUST have a unique title, description and h1. The script stops
    if it finds duplicates, because duplicate metadata is the most common SEO
    fault on large sites.
  - Hand-edits to generated HTML are overwritten. Edit the JSON or the
    template (templates/landing-page.html) instead.
"""
import argparse
import json
import sys
from string import Template

from sitekit import (ROOT, CONFIG, esc, img, icon, pulli, head_meta, jsonld,
                     business_schema, breadcrumb, breadcrumb_schema, faq_schema,
                     service_schema, wa_form, faq_block, depth_prefix, wa_link)

DATA = ROOT / "data" / "pages"
TEMPLATE = ROOT / "templates" / "landing-page.html"


def load_pages():
    pages = []
    for path in sorted(DATA.glob("*.json")):
        if path.name.startswith("_"):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_file"] = path.name
        if data.get("publish", False):
            pages.append(data)
    return pages


def check_unique(pages):
    problems = []
    for key in ("output", "title", "description", "h1"):
        seen = {}
        for p in pages:
            v = p.get(key, "").strip().lower()
            if not v:
                problems.append(f"{p['_file']}: missing '{key}'")
            elif v in seen:
                problems.append(f"{p['_file']}: duplicate {key} (also in {seen[v]})")
            else:
                seen[v] = p["_file"]
        for p in pages:
            d = p.get("description", "")
            if key == "description" and not (110 <= len(d) <= 165):
                problems.append(f"{p['_file']}: description is {len(d)} chars (aim for 120-160)")
    return problems


def link(pre, href):
    return href if href.startswith(("http", "tel:", "mailto:", "#")) else pre + href


def build_page(p, index, template):
    out = p["output"]
    pre = depth_prefix(out)

    # breadcrumb
    trail = [("Home", "index.html")]
    if p.get("breadcrumb_parent"):
        trail.append(tuple(p["breadcrumb_parent"]))
    trail_visible = [(n, link(pre, h)) for n, h in trail] + [(p["nav_label"], None)]
    trail_schema = trail + [(p["nav_label"], out)]

    faqs = [tuple(x) for x in p.get("faqs", [])]
    schema_nodes = [
        business_schema(),
        service_schema(p["h1"], p["description"], out, p.get("service_type", p["nav_label"])),
        breadcrumb_schema(trail_schema),
    ]
    if faqs:
        schema_nodes.append(faq_schema(faqs))

    meta = head_meta(out, p["title"], p["description"],
                     og_type="article") + jsonld(*schema_nodes)

    hero = p["hero_image"]
    intro_img = p.get("intro_image", hero)

    intro_html = "\n".join(f"<p>{esc(t)}</p>" for t in p.get("intro", []))
    includes_html = "\n".join(f"<li>{esc(t)}</li>" for t in p.get("includes", []))

    # menu columns
    menu_cols = []
    for course in p.get("menu", []):
        lis = "".join(
            f'<li><span class="mark{" mark--nonveg" if kind == "nonveg" else ""}" '
            f'aria-label="{"Non-vegetarian" if kind == "nonveg" else "Vegetarian"}"></span>{esc(name)}</li>'
            for name, kind in course["items"]
        )
        menu_cols.append(f'<div class="course" data-reveal><h3>{esc(course["title"])}</h3>'
                         f'<ul class="dish-list dish-list--single">{lis}</ul></div>')
    menu_html = "\n".join(menu_cols)
    ml = p.get("menu_link")
    menu_link_html = (f'<a class="btn btn--ghost" href="{link(pre, ml["href"])}">{esc(ml["text"])}</a>'
                      if ml else "")
    share_text = f"Hello Vellore Catering World, please share the {p['event_label'].lower()} menu and a quote."
    menu_share = (f'<a class="btn btn--wa" href="{wa_link(share_text)}" target="_blank" rel="noopener">'
                  f'{icon("wa", 20)} Ask for this menu on WhatsApp</a>')

    why_html = "\n".join(
        f'<div class="feature" data-reveal style="--d:{i}"><span class="feature__icon">{icon(w.get("icon", "leaf"), 24)}</span>'
        f'<div><h3>{esc(w["title"])}</h3><p>{esc(w["text"])}</p></div></div>'
        for i, w in enumerate(p.get("why", []))
    )

    gallery_html = "\n".join(
        f'<figure data-reveal="zoom" style="--d:{i}">{img(g["id"], g["alt"], 800, 600, widths=(480, 800), sizes="(max-width: 860px) 50vw, 25vw")}'
        f'<figcaption>{esc(g["alt"])}</figcaption></figure>'
        for i, g in enumerate(p.get("gallery", []))
    )

    related_cards = []
    for i, rel in enumerate(p.get("related", [])):
        r = index.get(rel)
        if not r:
            print(f"  ! {p['_file']}: related page '{rel}' not found — skipped")
            continue
        card = r.get("card", {})
        related_cards.append(
            f'<article class="tile" data-reveal style="--d:{i}">'
            f'{img(r["hero_image"]["id"], r["hero_image"]["alt"], 600, 860, widths=(400, 600), sizes="(max-width: 600px) 100vw, (max-width: 1079px) 50vw, 25vw")}'
            f'<div class="tile__body"><h3 class="gilded">{esc(r["nav_label"])}</h3>'
            f'<p>{esc(card.get("text", r["lead"]))}</p>'
            f'<a class="text-link tile__link" href="{link(pre, rel)}">View {esc(r["nav_label"].lower())}</a></div></article>'
        )
    related_html = "\n".join(related_cards)

    values = {
        "page_path": out,
        "asset_prefix": pre,
        "asset_version": CONFIG["asset_version"],
        "wa_number": CONFIG["whatsapp"],
        "meta": meta,
        "breadcrumb": breadcrumb(trail_visible),
        "hero_img": img(hero["id"], hero["alt"], 1600, 900, widths=(640, 1000, 1600), lazy=False),
        "kolam_src": pre + "assets/img/kolam.svg",
        "h1": esc(p["h1"]),
        "lead": esc(p["lead"]),
        "tamil": esc(p.get("tamil", "")),
        "tamil_meaning": esc(p.get("tamil_meaning", "")),
        "phone_e164": CONFIG["phone_e164"],
        "phone_short": CONFIG["phone_short"],
        "wa_hero": wa_link(f"Hello Vellore Catering World, I would like a quote for {p['event_label'].lower()}."),
        "intro_heading": esc(p.get("intro_heading", "")),
        "intro_html": intro_html,
        "intro_img": img(intro_img["id"], intro_img["alt"], 800, 1000, widths=(480, 800), sizes="(max-width: 860px) 100vw, 45vw"),
        "includes_heading": esc(p.get("includes_heading", "What is included")),
        "includes_html": includes_html,
        "menu_heading": esc(p.get("menu_heading", "Sample menu")),
        "menu_intro": esc(p.get("menu_intro", "")),
        "menu_html": menu_html,
        "menu_link": menu_link_html,
        "menu_share": menu_share,
        "why_heading": esc(p.get("why_heading", "Why families choose us")),
        "why_html": why_html,
        "gallery_heading": esc(p.get("gallery_heading", "Spreads we serve")),
        "gallery_html": gallery_html,
        "gallery_link": pre + "gallery.html",
        "faq_heading": esc(p.get("faq_heading", "Questions families ask")),
        "faq_html": faq_block(faqs),
        "related_heading": esc(p.get("related_heading", "Other functions we cater")),
        "related_html": related_html,
        "form_html": wa_form("enq", p["event_label"], heading=f"Get a {p['event_label'].lower()} quote"),
        "contact_href": pre + "contact.html",
        "pulli": pulli(),
        "icon_phone": icon("phone", 20),
        "icon_wa": icon("wa", 20),
    }
    html_out = Template(template).substitute(values)
    target = ROOT / out
    target.parent.mkdir(parents=True, exist_ok=True)

    # keep already-synced nav/footer so a rebuild without sync is still valid
    if target.exists():
        import re
        old = target.read_text(encoding="utf-8")
        for name in ("head", "nav", "footer"):
            pat = re.compile(rf"<!--\s*@{name}:start\s*-->.*?<!--\s*@{name}:end\s*-->", re.DOTALL)
            m_old, m_new = pat.search(old), pat.search(html_out)
            if m_old and m_new:
                html_out = html_out[:m_new.start()] + m_old.group(0) + html_out[m_new.end():]
    target.write_text(html_out, encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="build just one output path, e.g. services/wedding-catering-in-vellore.html")
    args = ap.parse_args()

    pages = load_pages()
    problems = check_unique(pages)
    if problems:
        print("generate_pages: fix these first:")
        for pr in problems:
            print("  ! " + pr)
        sys.exit(1)

    template = TEMPLATE.read_text(encoding="utf-8")
    index = {p["output"]: p for p in pages}
    built = []
    for p in pages:
        if args.only and p["output"] != args.only:
            continue
        built.append(build_page(p, index, template))
    print(f"generate_pages: built {len(built)} page(s)")
    for b in built:
        print(f"  + {b}")


if __name__ == "__main__":
    main()
