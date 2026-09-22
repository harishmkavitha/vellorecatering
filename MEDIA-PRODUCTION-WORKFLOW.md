# Vellore Catering World — Controlled Media Production Workflow

## Why this structure exists

The website contains thousands of media references because the same stock images are repeated in multiple page positions and responsive `srcset` sizes. That does **not** mean thousands of original photographs are required.

The new system uses **page-exclusive core media** for important commercial pages. A standard service page needs only:

- 1 hero image
- 3 supporting/gallery images
- 1 short video
- 1 video poster generated automatically from the video

The same page may display its hero or gallery image more than once. That is intentional and does not require another original file.

## Priority model

### P0 — Produce first

The complete Wedding & Marriage service cluster plus the homepage. The recommended order starts with Wedding Catering and Reception Catering. The homepage is P0 but has more visual slots, so it can be produced over several days and activated only when its full set is ready.

### P1 — Produce second

Other commercially important services such as Valaikappu, Seemandham, Birthday, Housewarming, Corporate, Office Lunch, South Indian, Banana Leaf, Vegetarian, Non-Vegetarian, Buffet and Live Counter Catering.

### P2 — Produce after P0/P1

Supporting conversion pages such as Services index, Menus, Gallery and Contact.

Later, servicing-area pages and blog/guide pages can use a controlled thematic library rather than every page receiving a completely new photo set.

## Folder structure

Important service pages use one folder per page:

```text
assets/images/services/wedding-catering-in-vellore/
assets/videos/services/wedding-catering-in-vellore/

assets/images/services/reception-catering-in-vellore/
assets/videos/services/reception-catering-in-vellore/
```

The exact filenames, dimensions and prompts are listed in:

```text
tools/media-production-dashboard.html
```

Do not invent or rename filenames after activation. Use the exact planned path.

## Safe daily process

### 1. Pick one or two pages

Run:

```bash
python tools/media_workflow.py next 5
```

This shows the next unfinished pages in the production order.

### 2. Create only the listed files

Open:

```text
tools/media-production-dashboard.html
```

For the selected page, copy the prompt for each required media item and save the finished file at the exact path shown.

For a normal service page:

- Hero image: 1920×1080 WebP
- Gallery image 1: 1800×1400 WebP
- Gallery image 2: 1800×1400 WebP
- Gallery image 3: 1800×1400 WebP
- Video: 1920×1080 MP4, recommended 12–15 seconds

The activation tool creates the 1200×750 video poster automatically.

### 3. Validate before changing HTML

Example:

```bash
python tools/media_workflow.py validate wedding-catering-in-vellore
```

If a file is missing, has the wrong dimensions, is not a real WebP, or the video is invalid, validation fails and **the webpage is not changed**.

### 4. Activate the complete page atomically

Only after validation passes:

```bash
python tools/media_workflow.py activate wedding-catering-in-vellore
```

Activation switches every planned media slot on that page to the local files in one operation. Until activation, the page continues using its existing working stock media, so there is no broken-image period while production is incomplete.

### 5. Run the site-wide media integrity check

```bash
python tools/media_workflow.py audit-site
```

This checks local image/video URLs across the public site and fails if a local reference points to a missing file.

### 6. Commit and push to GitHub

Commit these together:

- new files under `assets/images/...`
- new files under `assets/videos/...`
- changed webpage HTML
- `data/media-replacement-plan.json`
- regenerated video poster, when applicable

A GitHub Action at `.github/workflows/validate-media.yml` automatically runs the local media-link audit on every push and pull request.

## Important safeguards

1. **Never manually replace a Pexels/Unsplash URL in the HTML.** Use the activation tool.
2. **Never activate a half-complete page.** The script refuses to do so.
3. **Do not reuse P0/P1 image/video files on another P0/P1 page.** Each important page gets its own folder and own visual story.
4. **Same-page reuse is allowed.** If the hero appears twice on the Wedding page, both placements intentionally point to the same Wedding hero image.
5. **If media must be rolled back**, run:

```bash
python tools/media_workflow.py deactivate wedding-catering-in-vellore
```

The page returns to its stored online fallback media.
6. `tools/build.py` now runs `media_workflow.py reapply-active` after generated/stock media work, so already activated local page media is restored after a rebuild.

## Tracking files

- `data/media-replacement-plan.json` — source of truth for priority, filenames, dimensions, prompts and activation status.
- `tools/media-production-dashboard.html` — human-friendly production dashboard.
- `tools/media_workflow.py` — validation, activation, rollback and integrity tool.
- `.github/workflows/validate-media.yml` — push-time broken-local-media guard.

## Recommended first production sequence

1. Wedding Catering
2. Reception Catering
3. Engagement Catering
4. Nichayathartham Catering
5. Marriage Hall Catering
6. Hindu Wedding Catering
7. Muslim Wedding Catering
8. Christian Wedding Catering
9. Mehendi Catering
10. Sangeet Catering
11. Haldi Catering
12. Bridal Shower Catering
13. Groom / Bridal Welcome Catering
14. Destination Wedding Catering
15. Pre-Wedding Function Catering
16. Post-Wedding Catering
17. Homepage media set

After P0, continue with P1 from the dashboard.
