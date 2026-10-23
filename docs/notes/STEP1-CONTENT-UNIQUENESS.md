# Step 1 — Text Content Uniqueness Completion

## Scope completed

All 1,262 public website HTML pages were included in the content-uniqueness audit. Internal HTML used only as partials/templates/tools and the media inventory utility are not treated as public website pages.

The rewrite covers generated service pages, servicing-area pages, guide/blog pages, the main guides, and the home/menu pages that were closest in wording.

## Tracking mechanism

The project now includes `tools/audit_text_uniqueness.py`.

The audit extracts visible editorial text from each page's `<main>` element and excludes shared navigation, forms, scripts, styles and footer chrome. It then calculates TF-IDF cosine similarity using normalized word 2-grams and 3-grams.

- `similarity_percent` = similarity to the closest other public page.
- `difference_percent` = 100 - similarity_percent.
- PASS requirement = difference_percent >= 50.00%.

This is a phrase-level duplication metric, so generic words such as “catering” alone do not determine the score; repeated multi-word wording and sentence patterns have much more influence.

## Final result

- Public pages audited: **1,262**
- Pages passed: **1,262**
- Pages failed: **0**
- Minimum page-to-page difference: **50.83%**
- Maximum nearest-page similarity: **49.17%**
- Median page-to-page difference: **71.06%**

Detailed evidence is available in:

- `content-uniqueness-audit.html`
- `content-uniqueness-audit.csv`
- `content-uniqueness-audit-summary.json`

## Step 2 status

Step 2 has **not** been performed. Existing image/video references remain unchanged. A source-reference comparison found **14,274 media references before and 14,274 after**, with an identical reference multiset: **0 added and 0 removed**.

The existing `media-replacement-inventory.html` remains in the project for Step 2.
