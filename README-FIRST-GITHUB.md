# Vellore Catering World — GitHub Ready Website

This ZIP is the current full source-of-truth website build with **Batches 01–37 integrated**.

## Business details
- Business name: **Vellore Catering World**
- Contact number: **9445978140**

## Media status
- All 37 planned production batches are complete and integrated.
- Batches 01–27 from v13 are retained.
- Batches 28–37 are merged into their actual website pages.
- Completed Batch 01–37 pages contain **0 Pexels/Unsplash media references**.
- Built-in full-site local-media audit: **4269 references checked, 0 broken references**.

See `MEDIA-INTEGRATION-VALIDATION-01-37.txt` and `FULL-SITE-MEDIA-AUDIT.txt` for the detailed audit.

## Important scope note
The website has more than 1,200 HTML pages. The 37 planned business-critical/support pages now use the completed local media. Many lower-priority long-tail pages still use online stock references by design and can be migrated later in controlled batches.

## GitHub upload
1. Back up the current repository if needed.
2. Extract this ZIP.
3. Open the `vellorecatering-main` folder.
4. Copy/replace its contents into your existing repository working folder.
5. Run:

```powershell
git add .
git commit -m "Integrate Vellore Catering World media batches 01 to 37"
git push origin main
```

After GitHub Pages deploys, test the Homepage, Services Index, Menus, Gallery, Contact and Batches 28–32 on desktop and mobile.

Future website work should use this package as the new source of truth, not v13 or older ZIPs.
