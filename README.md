# Vellore Catering World Website — V4 Real Photos & Videos
<!-- README.md | Version: V3 -->

A GitHub Pages-ready static website for **Vellore Catering World**, built from the supplied master design and the uploaded Catering Type spreadsheet.

## What is included

- **236 unique Catering Type pages** generated from 237 spreadsheet rows. `Marriage Hall Catering` appeared twice in the source sheet, so it uses one canonical page linked under both source categories.
- **16 Catering Categories** displayed inside the fixed floating mega-menu, with desktop search and mobile accordion behaviour.
- Every Catering Type page follows the supplied section specification: breadcrumbs, hero, trust strip, introduction, why choose us, service scope, event types, menu categories, cuisines, sample menu, customisation, live counters, service styles, capacity, process, hygiene, infrastructure, team, galleries, case-study format, testimonials policy, Google reviews link, venues, areas, pricing guide, packages, FAQs, food differentiation, booking form, contact, map, related services, related articles and footer.
- The **Related Services** section on every Catering Type page contains only these four services: Wedding Catering, Birthday Catering, Seemandham Catering and Other Caterings.
- WhatsApp enquiry form fields: **Name, Contact Number, Event Date**. Submission opens WhatsApp with those details and the current catering type.
- Floating Call and WhatsApp buttons are available sitewide.
- Responsive layout for desktop, laptop, tablet and mobile breakpoints.
- CSS reveal effects, hover transitions, fixed glass navigation, scroll effects and lazy page motion.

## Photos and videos (V4)

Every page now shows real South Indian food, catering and wedding photography
from **Pexels** (free for commercial use, no attribution required). The curated
list — 61 photos and 10 videos — lives in `data/media-library.json`, and
`tools/stock_media.py` places them on all 1,262 pages:

- each Catering Type page gets photos that suit its occasion (wedding, pooja,
  corporate, biryani, haldi, funeral and so on); wedding, pooja and funeral
  pages show vegetarian food only, and funeral pages show no people or sweets
- area and blog pages get a stable, varied mix, so a page never repeats a photo
- alt text, captions, Open Graph/Twitter images and JSON-LD images follow the photo
- `credits.html` (noindex, linked in the footer) lists every item in use

```bash
python tools/stock_media.py check      # 1. confirm every Pexels link works (needs internet)
python tools/stock_media.py review     # 2. open tools/media-review.html and eyeball the photos
python tools/stock_media.py download   # 3. optional: self-host everything, then commit
```

Out of the box, photos load from the Pexels CDN, already cropped to each slot,
so the site looks complete as soon as you push. Running `download` saves about
770 WebP/JPEG files to `assets/img/stock/` (roughly 80–100 MB) and short MP4
clips to `assets/video/stock/`, then rewrites the pages to use them.

For the category videos (biryani, filter coffee, curd rice, dosa counter …),
get a free key at https://www.pexels.com/api/ and run:

```bash
# Windows PowerShell:  $env:PEXELS_API_KEY="your-key"
# macOS / Linux:       export PEXELS_API_KEY=your-key
python tools/stock_media.py download
```

Without a key, every page uses the verified dosa clip. Install FFmpeg so clips
are trimmed to 12 seconds at 1280 px; `pip install pillow` for WebP output.

**Swapping a photo:** edit or remove its entry in `data/media-library.json`, then
run `python tools/stock_media.py apply`. **Adding your own event photos:** real
photos of your own functions build more trust than stock images — replace
library entries with your own files over time.

Stock photos are representative only. Do not caption them as your own events,
and do not suggest the people shown are your staff or customers.

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
│   ├── img/        (stock/ after download)
│   └── video/      (stock/ after download)
├── data/catering-catalog.json
├── data/media-library.json   (photo & video list)
├── credits.html
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

That rebuilds the mega-menu and Catering Type pages, re-applies the stock photos and videos, syncs shared partials, rebuilds `sitemap.xml`, and runs duplicate/broken-link/placeholder checks.

If you change the spreadsheet-derived catalogue, update `data/catering-catalog.json` and rebuild. New pages pick up photos automatically.

## GitHub Pages deployment

1. Create a GitHub repository and upload the **contents of this folder**.
2. Keep `.nojekyll` in the repository root.
3. In GitHub: **Settings → Pages → Deploy from a branch → main / root**.
4. The current canonical base URL is configured in `tools/site_config.json` as:
   `https://harishmkavitha.github.io/vellorecatering` (V4: corrected to match the live repository name)
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
