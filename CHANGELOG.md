# Changelog
<!-- CHANGELOG.md | Version: V4 -->

## V6 — 23 October 2026 — Google Analytics 4

Measures three things the business actually asked for: how many people land on the
site, how many tap a **Call** button, and how many tap a **WhatsApp** button.

GA4 property "Vellore Catering World", web stream `vellorecatering.in`,
Measurement ID **`G-SP3B9FK19N`** (recorded in `tools/site_config.json`).

**Page views** are automatic — `page_view` on all 1,262 pages, plus scrolls, outbound
clicks and site search from GA4's Enhanced measurement.

**Call and WhatsApp taps** are two custom events, emitted from `assets/js/main.js`:

| Event | Fires on |
|---|---|
| `call_click` | any `tel:` link — ~6 per page |
| `whatsapp_click` | any `wa.me` link (~5 per page) **and** the enquiry form's WhatsApp hand-off |

Each event carries three parameters:

- `location` — `floating_button`, `header`, `footer`, `hero`, `enquiry_form`,
  `enquiry_form_submit`, the enclosing `section` id (`contact`, `pricing`, `enquire` …),
  or `page_body`. Anything with `data-track-location` overrides all of these.
- `page_type` — `home`, `service`, `area`, `blog`, `contact` or `other`, read from the
  body class the generators already set. This separates calls from the 236 service
  pages, the 507 locality pages and the ~500 blog articles.
- `link_text` — the visible label, trimmed to 60 characters, or `icon only`.

One delegated listener on `document` handles all ~13,800 links sitewide rather than
binding thousands of handlers. It runs in the capture phase so the event is queued
before navigation begins; gtag sends via `navigator.sendBeacon`, which survives the
page going away. **No click is ever cancelled or delayed to record an event**, and if
`gtag` is missing — blocked, offline, not yet loaded — the click proceeds untouched.

**Why a new script instead of `sync_partials.py`.** The tag belongs in
`partials/head.html`, and it is there. But the published pages have since been run
through an HTML prettifier (alphabetised attributes, self-closing tags), so the partial
no longer matches them byte-for-byte: re-syncing would rewrite all 1,262 pages
cosmetically and bury the real change in a ~20,000-line diff. `tools/add_analytics.py`
inserts only the tag, in the style the pages already use, immediately before the
`<!-- @head:end -->` marker — inside the head block, so a future `sync_partials.py` run
regenerates it from the partial rather than leaving a duplicate. It is idempotent, it
refuses to stack a second Google tag on a page that already has one, and
`--remove` reverses it.

**Cache busting.** `main.js?v=1` → `?v=2` on all 1,262 pages (`asset_version` in
`site_config.json` bumped to match), otherwise returning visitors would keep the old
file and never report a click. `main.css` is unchanged and stays at `?v=15`.

**Privacy policy.** `privacy.html` claimed the site set no analytics cookies, which
stopped being true. It now names Google Analytics, the `_ga` cookies and what is
recorded, states that enquiry details are never sent to Google, confirms no advertising
or remarketing use, and links Google's opt-out add-on. "Who receives your data" names
Google. No consent banner was added — see the note below.

**Verified in Chromium** against the real pages, not in theory: on the home, service,
locality and contact pages, `call_click` and `whatsapp_click` both reach `dataLayer`
with the right `page_type`; `location` resolves to `floating_button`, `header`,
`footer`, `hero`, `enquiry_form` and section ids; submitting the enquiry form emits
`whatsapp_click` / `enquiry_form_submit`; an ordinary link emits nothing; and no page
throws a JavaScript error. The CI media audit still passes unchanged.

**Still to do by hand in GA4:** mark `call_click` and `whatsapp_click` as key events.
GA4 only offers an event for marking once it has been seen at least once, so this
cannot be done until real traffic arrives.

**No consent banner.** GA4's cookies are first-party and analytics-only, and a banner
defaulting to "off" would suppress most of the data the business wants. Under the DPDP
Act the honest disclosure now in `privacy.html` is the baseline; a consent gate is a
business decision, not a technical gap. Adding one later means wrapping the `gtag`
call in `assets/js/main.js` and the tag in `partials/head.html` behind a stored choice.

### Files in V6

| File | Version | Change |
|---|---|---|
| `tools/add_analytics.py` | V1 | new — idempotent GA4 tag injector, with `--check` and `--remove` |
| `partials/head.html` | V2 | gtag.js snippet (source of truth for future syncs) |
| `assets/js/main.js` | V3 | section 12 click tracker; `whatsapp_click` on form submit |
| `privacy.html` | V3 | analytics and cookies disclosed accurately; date updated |
| `tools/site_config.json` | V4 | `ga4_measurement_id`; `asset_version` → `2` |
| `tools/sync_partials.py` | V2 | skips `docs/` (it was reporting the moved reports as marker-less) |
| 1,262 `.html` pages | unchanged | gtag.js block added; `main.js?v=1` → `?v=2` |
| `README.md` | V5 | analytics section |
| `CHANGELOG.md` | V4 | this entry |

## V5 — 23 October 2026 — live domain canonicals, and internal files taken off the public site

The site has been served from **https://vellorecatering.in** since the custom domain was
mapped, but every page still declared `https://harishmkavitha.github.io/vellorecatering`
as its canonical address. Search engines were being told the GitHub copy was the real
version, which splits ranking signals between two addresses.

**Fixed** (`python tools/set_domain.py https://vellorecatering.in`, 1,265 files)
- `<link rel="canonical">` and the `hreflang="en-IN"` alternate on all 1,262 pages.
- `og:url` and the `url`, `@id`, `image` and `logo` fields in the LocalBusiness,
  WebSite, Service, Breadcrumb and FAQ JSON-LD blocks.
- All 1,260 `<loc>` entries in `sitemap.xml`, and the `Sitemap:` line in `robots.txt`.
- The `<base href>` in `404.html`, two files under `data/`, and `tools/site_config.json`.
- `CNAME` rewritten with the same value, `vellorecatering.in` (now with a trailing newline).
- `README.md` deployment section updated: it still described the GitHub Pages URL as canonical.

**Deliberately not changed**
- No rebuild was run. The page content, media, business name (Vellore Catering World)
  and phone number (94459 78140) are byte-for-byte unchanged apart from the URL string.
- Version markers on generated pages and their data files were left as they were: their
  content did not change, only the domain they point to. This release is recorded here instead.

### Internal files were being published

The repository root is the website root on GitHub Pages, so 22 working files were
publicly readable at `vellorecatering.in/<filename>` — including `SEO-AUDIT.md`,
`STEP1-CONTENT-UNIQUENESS.md`, the `MEDIA-*` batch logs, `content-uniqueness-audit.csv`
and two HTML audit reports that carried **no robots meta at all**, so they were indexable.
Nothing linked to them and they were not in the sitemap, but anyone could open them.

**Moved** (22 files, no content changed)
- 16 working notes and batch logs → `docs/notes/`
- 6 audit outputs → `docs/reports/`
- `robots.txt` now disallows `/docs/`. `tools/media_workflow.py` already skipped `docs`,
  so the CI media audit still scans the same 1,262 public pages and passes.

**Stopped them coming back.** The audit scripts wrote to the repository root, so the files
would have reappeared on the next run. They now write to `docs/reports/` and create it if needed.

**`noindex, nofollow`** added to the four internal HTML reports and to the dashboard
template that generates one of them, so regenerating keeps the tag.

Note that `Disallow` prevents crawling, not indexing: a disallowed URL can still be listed
if something links to it. The `noindex` tags are the reliable protection, which is why both are used.

### Files in V5

| File | Version | Change |
|---|---|---|
| `tools/site_config.json` | V3 | `site_url` → `https://vellorecatering.in` |
| `CNAME` | — | `vellorecatering.in` (rewritten, same value) |
| 1,262 `.html` pages, `sitemap.xml`, 2 `data/*.json` | unchanged | URL string only |
| `robots.txt` | V3 | live sitemap URL + `Disallow: /docs/` |
| `tools/audit_text_uniqueness.py` | V2 | output → `docs/reports/`; skips `docs`; report tagged `noindex` |
| `tools/audit_business_page_distinctness.py` | V2 | output → `docs/reports/` |
| `tools/generate_media_replacement_inventory.py` | V2 | output → `docs/reports/`; skips `docs/`; report tagged `noindex` |
| `tools/media_workflow.py` | V2 | generated dashboard tagged `noindex` |
| `tools/media-day-01-wedding-reception.html` | — | `noindex` added |
| `tools/media-production-dashboard.html` | — | `noindex` added |
| `docs/notes/*` (16 files) | — | moved from the repository root |
| `docs/reports/*` (6 files) | — | moved from the repository root; HTML reports tagged `noindex` |
| `README.md` | V4 | live domain, `servicing-areas/`, and the `docs/` rule |
| `CHANGELOG.md` | V3 | this entry |

## V4 — 16 September 2026 — real photos & videos

**Media**
- Replaced every generated SVG placeholder (5,003 image slots on 1,247 pages) and
  every abstract WebM loop with real Pexels photos/videos of South Indian food,
  catering, weddings and rituals — 61 photos and 10 videos in `data/media-library.json`.
- Photos are chosen per page theme (wedding, pooja, corporate, biryani, haldi,
  funeral …); vegetarian-only on wedding, pooja and funeral pages; no people or
  sweets on funeral pages; no photo repeats within a page.
- Alt text, figure captions, gallery lightbox labels, Open Graph/Twitter images
  and JSON-LD images now describe the real photo. Area and blog pages previously
  used SVG `og:image` files, which social apps cannot display.
- Page wording that called the visuals "illustrations" now says "representative
  stock photographs", keeping the honest disclosure.
- New `credits.html` (noindex) with a footer link; new `tools/media-review.html` contact sheet.
- Deleted 3,487 unused placeholder SVG/PNG/WebM files (13.4 MB).

**Fixes**
- Canonical, Open Graph, schema, robots and sitemap URLs pointed to
  `/vellore-catering/`; corrected to the live `/vellorecatering/` path (1,263 files).
- Page video clips now load only on tablet/desktop without data saver (`main.js`).
- `build.py` re-applies media after regenerating pages, so a rebuild no longer
  brings placeholders back, and it now flags any leftover placeholder reference.
- Removed a stray `{partials,tools,templates,data` folder and `tools/__pycache__`.

**Retired**
- `tools/replace_remote_media.py` (it converted Pexels photos back into SVGs) and
  `tools/generate_catalog_media.py` (placeholder generator).

### Files in V4

| File | Version | Change |
|---|---|---|
| `tools/stock_media.py` | V1 | new — apply / check / download / review / prune |
| `data/media-library.json` | V1 | new — curated Pexels photos & videos |
| `credits.html` | V1 | new — generated by `stock_media.py` |
| `tools/media-review.html` | V1 | new — generated by `stock_media.py review` |
| `tools/build.py` | V2 | media step + placeholder check |
| `tools/localize_media.py` | V2 | now a wrapper for `stock_media.py download` |
| `tools/generate_area_blog_site.py` | V2 | stops writing placeholder SVGs |
| `tools/site_config.json` | V2 | `site_url` corrected |
| `assets/js/main.js` | V2 | page-video loading guard |
| `partials/footer.html` | V2 | "Photo credits" link |
| `robots.txt` | V2 | sitemap URL corrected |
| `index.html`, `about.html`, `menus.html`, `gallery.html`, `contact.html` | V2 | real photos |
| `privacy.html`, `terms.html`, `404.html` | V2 | URL fix + footer link |
| `servicing-areas/*.html`, `guides/blogs/*.html` | V2 | real photos (set by `stock_media.py`) |
| `services/*.html` (catering types) | GENERATED V3 | real photos (set by `stock_media.py`) |
| `README.md` | V3 | media workflow |
| `CREDITS.md` | V3 | Pexels licence notes |
| `CHANGELOG.md` | V2 | this entry |

Unchanged: `assets/css/main.css` V1, `partials/head.html` V1, `partials/nav.html` V2,
`tools/sync_partials.py` V1, `tools/build_sitemap.py` V1, `tools/set_domain.py` V1,
`tools/sitekit.py` V1, `tools/generate_pages.py` V1, `tools/generate_catalog_site.py` V2,
`tools/build_catalog_nav.py` V2.

## V1 — 16 September 2026

First release.

- 6 main pages (Home, About us, Services, Menus, Gallery, Contact us) + 4 SEO service pages
  (wedding, engagement, birthday, seemandham catering in Vellore) + privacy, terms, 404
- Black and gold design, animated kolam hero, fixed floating menu with mobile overlay and services dropdown
- Floating Call and WhatsApp buttons; enquiry forms (name, contact number, event date) that open WhatsApp
- XML sitemap, robots.txt, JSON-LD schema, Open Graph image, web manifest, icons
- Python tooling for 500+ pages: JSON-driven generator, partial sync, sitemap builder, media localiser, domain switcher

### File versions (as of V1 — see the V4 table above for current versions)

When you change a file, bump its `Version:` marker (V1 → V2) and add a line here.

| File | Version |
|---|---|
| `404.html` | V1 |
| `CREDITS.md` | V1 |
| `README.md` | V1 |
| `about.html` | V1 |
| `assets/css/main.css` | V1 |
| `assets/img/fallback.svg` | V1 |
| `assets/img/favicon.svg` | V1 |
| `assets/img/kolam.svg` | V1 |
| `assets/img/logo-mark.svg` | V1 |
| `assets/img/logo.svg` | V1 |
| `assets/js/main.js` | V1 |
| `contact.html` | V1 |
| `data/pages/_example-area-page.json` | V1 |
| `data/pages/birthday-party-catering-in-vellore.json` | V1 |
| `data/pages/engagement-catering-in-vellore.json` | V1 |
| `data/pages/seemandham-catering-in-vellore.json` | V1 |
| `data/pages/wedding-catering-in-vellore.json` | V1 |
| `gallery.html` | V1 |
| `index.html` | V1 |
| `menus.html` | V1 |
| `partials/footer.html` | V1 |
| `partials/head.html` | V1 |
| `partials/nav.html` | V1 |
| `privacy.html` | V1 |
| `robots.txt` | V1 |
| `services/birthday-party-catering-in-vellore.html` | V1 |
| `services/engagement-catering-in-vellore.html` | V1 |
| `services/index.html` | V1 |
| `services/seemandham-catering-in-vellore.html` | V1 |
| `services/wedding-catering-in-vellore.html` | V1 |
| `site.webmanifest` | V1 |
| `sitemap.xml` | V1 |
| `templates/landing-page.html` | V1 |
| `terms.html` | V1 |
| `tools/build.py` | V1 |
| `tools/build_sitemap.py` | V1 |
| `tools/generate_pages.py` | V1 |
| `tools/localize_media.py` | V1 |
| `tools/set_domain.py` | V1 |
| `tools/site_config.json` | V1 |
| `tools/sitekit.py` | V1 |
| `tools/sync_partials.py` | V1 |
