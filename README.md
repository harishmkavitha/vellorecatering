# Vellore Catering Website — V2 Multi-page Catalogue

A GitHub Pages-ready static website for **Vellore Catering**, built from the supplied master design and the uploaded Catering Type spreadsheet.

## What is included

- **236 unique Catering Type pages** generated from 237 spreadsheet rows. `Marriage Hall Catering` appeared twice in the source sheet, so it uses one canonical page linked under both source categories.
- **16 Catering Categories** displayed inside the fixed floating mega-menu, with desktop search and mobile accordion behaviour.
- Every Catering Type page follows the supplied section specification: breadcrumbs, hero, trust strip, introduction, why choose us, service scope, event types, menu categories, cuisines, sample menu, customisation, live counters, service styles, capacity, process, hygiene, infrastructure, team, galleries, case-study format, testimonials policy, Google reviews link, venues, areas, pricing guide, packages, FAQs, food differentiation, booking form, contact, map, related services, related articles and footer.
- The **Related Services** section on every Catering Type page contains only these four services: Wedding Catering, Birthday Catering, Seemandham Catering and Other Caterings.
- WhatsApp enquiry form fields: **Name, Contact Number, Event Date**. Submission opens WhatsApp with those details and the current catering type.
- Floating Call and WhatsApp buttons are available sitewide.
- Responsive layout for desktop, laptop, tablet and mobile breakpoints.
- CSS reveal effects, hover transitions, fixed glass navigation, scroll effects and lazy page motion.

## Original/local media

The live HTML has **no Pexels image or video hotlinks**. New page artwork and motion loops are procedurally generated and stored locally:

- `assets/img/pages/` — unique SVG page illustrations + unique OG PNGs
- `assets/video/pages/` — one unique WebM loop per Catering Type page
- `assets/img/master-generated/` — local original replacements for remote media in the supplied master pages
- `assets/video/master-generated/` — local original motion replacements for the supplied master pages

These generated visuals are illustrative placeholders, not claims of real customer events. Replace them with your own real event photography/video when available; authentic local media is normally better for trust and local SEO.

## Main structure

```text
vellore-catering/
├── index.html
├── about.html
├── menus.html
├── gallery.html
├── contact.html
├── services/
│   ├── index.html
│   ├── other-caterings-in-vellore.html
│   └── 236 Catering Type pages
├── guides/
│   ├── index.html
│   └── 6 planning guides
├── assets/
│   ├── css/main.css
│   ├── js/main.js
│   ├── fonts/
│   ├── img/
│   └── video/
├── data/catering-catalog.json
├── partials/
├── tools/
├── sitemap.xml
├── robots.txt
└── .nojekyll
```

## Rebuild after edits

Run from the project root:

```bash
python tools/build.py
```

That rebuilds the mega-menu and Catering Type pages, syncs shared partials, rebuilds `sitemap.xml`, and runs duplicate/broken-link checks.

If you change the spreadsheet-derived catalogue, update `data/catering-catalog.json` and rebuild. `tools/generate_catalog_media.py` can regenerate missing original media assets when FFmpeg and Pillow are installed.

## GitHub Pages deployment

1. Create a GitHub repository and upload the **contents of this folder**.
2. Keep `.nojekyll` in the repository root.
3. In GitHub: **Settings → Pages → Deploy from a branch → main / root**.
4. The current canonical base URL is configured in `tools/site_config.json` as:
   `https://harishmkavitha.github.io/vellore-catering`
5. For a custom domain, run:

```bash
python tools/set_domain.py https://www.yourdomain.com
python tools/build.py
```

Then configure the domain in GitHub Pages and enforce HTTPS.

## SEO implementation

The generated service pages include unique titles, meta descriptions, H1s, canonical URLs, Open Graph/Twitter metadata, LocalBusiness/Service/Breadcrumb/FAQ JSON-LD, semantic headings, descriptive alt text, internal links, local-area references, related-service links, planning guides, `robots.txt`, and an XML sitemap.

No website can guarantee a #1 Google position. Ranking also depends on Google Business Profile quality, genuine reviews, real local photos, citations/backlinks, page experience, competition, domain authority, and ongoing content/technical maintenance. After launch, connect Google Search Console, submit `sitemap.xml`, keep NAP details consistent, and publish only genuine reviews/event case studies.

## Content integrity

The generated site deliberately does **not** fabricate customer testimonials, star ratings or real-event case studies. Those sections transparently request verified business data or show an explicitly labelled planning scenario. Replace them only with real, permissioned material.

## V3 locality + blog expansion

This package now includes:

- `servicing-areas/index.html` plus 506 individual locality pages from the supplied area workbook.
- `guides/blogs/index.html` plus 500 long-form catering articles.
- `data/servicing-area-page-map.csv` and `data/blog-page-map.csv` for URL/content management.
- `EXPANSION-SEO-NOTES.md` for the expansion audit and publishing cautions.

Top-navigation structure intentionally keeps only one child under **Services** (`Servicing Areas`) and one child under **Guides** (`Blogs`), while hub pages provide crawlable access to the large page libraries.
