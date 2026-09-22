#!/usr/bin/env python3
"""
media_workflow.py — safe staged replacement of online stock media with page-local media.

The site keeps its currently working online media until a complete local media set for a
page exists and passes validation. Activation is atomic per page, so half-finished pages
never contain broken local references.

Typical daily workflow
----------------------
1. Open tools/media-production-dashboard.html and choose the next P0/P1 page.
2. Create files exactly at the listed paths/dimensions.
3. Run:  python tools/media_workflow.py validate <page-or-slug>
4. Run:  python tools/media_workflow.py activate <page-or-slug>
5. Run:  python tools/media_workflow.py audit-site
6. Commit/push the page + media + data/media-replacement-plan.json.

Commands
--------
  status [page]          Show planned/ready/active status.
  validate <page>        Validate required image/video files and dimensions.
  activate <page>        Validate, generate video poster if needed, then switch page atomically.
  deactivate <page>      Restore that page's stored online fallback media.
  reapply-active         Re-apply all active local media after a site rebuild.
  audit-site             Verify every local image/video URL in public HTML resolves to a file.
  dashboard              Rebuild media-production-dashboard.html.
  next [N]               Show the next N unfinished pages in production order.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "data" / "media-replacement-plan.json"
DASHBOARD = ROOT / "tools" / "media-production-dashboard.html"
CFG_PATH = ROOT / "tools" / "site_config.json"
SKIP_DIRS = {"partials", "tools", "templates", "data", ".git", "node_modules", "assets", "docs"}

IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
VIDEO_RE = re.compile(r"<video\b[^>]*>.*?</video>", re.I | re.S)
PRELOAD_RE = re.compile(r'<link\b[^>]*rel="preload"[^>]*>', re.I)
SOURCE_RE = re.compile(r"<source\b[^>]*>", re.I)
ATTR_RE_CACHE: dict[str, re.Pattern] = {}


def load_plan():
    if not PLAN_PATH.exists():
        sys.exit(f"Missing {PLAN_PATH.relative_to(ROOT)}")
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def save_plan(plan):
    PLAN_PATH.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def attr(tag: str, name: str):
    pat = ATTR_RE_CACHE.get(name)
    if pat is None:
        pat = re.compile(r"\s" + re.escape(name) + r'="([^"]*)"', re.I)
        ATTR_RE_CACHE[name] = pat
    m = pat.search(tag)
    return html.unescape(m.group(1)) if m else None


def set_attr(tag: str, name: str, value: str):
    val = html.escape(str(value), quote=True)
    pat = re.compile(r"(\s" + re.escape(name) + r'=\")[^\"]*(\")', re.I)
    if pat.search(tag):
        return pat.sub(lambda m: m.group(1) + val + m.group(2), tag, count=1)
    pos = tag.rfind("/>")
    if pos < 0:
        pos = tag.rfind(">")
    return tag[:pos] + f' {name}="{val}"' + tag[pos:]


def del_attr(tag: str, name: str):
    return re.sub(r"\s" + re.escape(name) + r'="[^"]*"', "", tag, count=1, flags=re.I)


def rel_url(page_path: Path, asset_path: str):
    return os.path.relpath(ROOT / asset_path, page_path.parent).replace(os.sep, "/")


def page_candidates(plan):
    return plan["pages"]


def resolve_page(plan, query: str):
    q = query.strip().lower().replace("\\", "/")
    matches = []
    for p in page_candidates(plan):
        rel = p["page"].lower()
        stem = Path(rel).stem.lower()
        label = p["label"].lower()
        if q in {rel, stem, label} or q == stem.replace("-in-vellore", ""):
            return p
        if q in rel or q in label:
            matches.append(p)
    if len(matches) == 1:
        return matches[0]
    if matches:
        names = ", ".join(x["page"] for x in matches[:8])
        sys.exit(f"Ambiguous page '{query}'. Matches: {names}")
    sys.exit(f"Page not found in media plan: {query}")


def image_info(path: Path):
    try:
        from PIL import Image
    except ImportError:
        return None, "Pillow is not installed; cannot validate image dimensions."
    try:
        with Image.open(path) as im:
            return (int(im.width), int(im.height), im.format), None
    except Exception as exc:
        return None, f"cannot open image: {exc}"


def video_info(path: Path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None, "ffprobe is not installed; cannot validate video dimensions."
    cmd = [
        ffprobe, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name:format=duration",
        "-of", "json", str(path),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(r.stdout)
        stream = data.get("streams", [{}])[0]
        fmt = data.get("format", {})
        return (
            int(stream.get("width", 0)), int(stream.get("height", 0)),
            stream.get("codec_name", ""), float(fmt.get("duration", 0) or 0)
        ), None
    except Exception as exc:
        return None, f"cannot inspect video: {exc}"


def validate_page(page, generate_posters=False, quiet=False):
    problems = []
    details = []
    for a in page["assets"]:
        f = ROOT / a["file"]
        if not f.exists():
            problems.append(f"MISSING: {a['file']}")
            continue
        if a["type"] == "image":
            info, err = image_info(f)
            if err:
                problems.append(f"{a['file']}: {err}")
                continue
            w, h, fmt = info
            ew, eh = int(a["create_width"]), int(a["create_height"])
            if (w, h) != (ew, eh):
                problems.append(f"DIMENSION: {a['file']} is {w}x{h}; expected exactly {ew}x{eh}")
            if f.suffix.lower() == ".webp" and str(fmt).upper() != "WEBP":
                problems.append(f"FORMAT: {a['file']} has .webp extension but is {fmt}")
            details.append(f"OK image {a['file']} {w}x{h} {fmt}")
        else:
            info, err = video_info(f)
            if err:
                problems.append(f"{a['file']}: {err}")
                continue
            w, h, codec, duration = info
            ew, eh = int(a["create_width"]), int(a["create_height"])
            if (w, h) != (ew, eh):
                problems.append(f"DIMENSION: {a['file']} is {w}x{h}; expected exactly {ew}x{eh}")
            if duration < 6 or duration > 25:
                problems.append(f"DURATION: {a['file']} is {duration:.1f}s; expected 6–25s (recommended 12–15s)")
            details.append(f"OK video {a['file']} {w}x{h} {codec} {duration:.1f}s")
            poster = ROOT / a["poster_file"]
            if not poster.exists() and generate_posters and not problems:
                ok, msg = generate_poster(f, poster, int(a["poster_width"]), int(a["poster_height"]))
                if not ok:
                    problems.append(msg)
                else:
                    details.append(msg)
            if poster.exists():
                pinfo, perr = image_info(poster)
                if perr:
                    problems.append(f"{a['poster_file']}: {perr}")
                else:
                    pw, ph, pfmt = pinfo
                    ewp, ehp = int(a["poster_width"]), int(a["poster_height"])
                    if (pw, ph) != (ewp, ehp):
                        problems.append(f"POSTER DIMENSION: {a['poster_file']} is {pw}x{ph}; expected {ewp}x{ehp}")
                    details.append(f"OK poster {a['poster_file']} {pw}x{ph} {pfmt}")
            elif not generate_posters:
                details.append(f"Poster will be generated automatically at activation: {a['poster_file']}")
    if not quiet:
        print(f"validate: {page['page']}")
        for d in details:
            print("  + " + d)
        for p in problems:
            print("  ! " + p)
        print("PASS" if not problems else f"FAIL ({len(problems)} problem(s))")
    return problems


def generate_poster(video: Path, poster: Path, w: int, h: int):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False, f"Cannot create {poster.relative_to(ROOT)}: ffmpeg is not installed"
    poster.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg, "-y", "-ss", "1", "-i", str(video), "-frames:v", "1",
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
        "-c:v", "libwebp", "-quality", "82", str(poster),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return False, f"Poster generation failed for {video.relative_to(ROOT)}: {r.stderr[-500:]}"
    return True, f"Generated poster {poster.relative_to(ROOT)}"


def patch_img_tag(tag: str, page_path: Path, a: dict, active: bool):
    if attr(tag, "data-slot") != a["slot"]:
        return tag
    if active:
        u = rel_url(page_path, a["file"])
        tag = set_attr(tag, "src", u)
        tag = del_attr(tag, "srcset")
        tag = set_attr(tag, "data-media", "local")
        if attr(tag, "data-full") is not None:
            tag = set_attr(tag, "data-full", u)
        return tag
    tag = set_attr(tag, "src", a.get("fallback_src", ""))
    if a.get("fallback_srcset"):
        tag = set_attr(tag, "srcset", a["fallback_srcset"])
    else:
        tag = del_attr(tag, "srcset")
    if a.get("fallback_sizes"):
        tag = set_attr(tag, "sizes", a["fallback_sizes"])
    if a.get("fallback_data_media"):
        tag = set_attr(tag, "data-media", a["fallback_data_media"])
    else:
        tag = del_attr(tag, "data-media")
    return tag


def patch_video_block(block: str, page_path: Path, a: dict, active: bool):
    open_tag_m = re.match(r"<video\b[^>]*>", block, re.I)
    if not open_tag_m:
        return block
    open_tag = open_tag_m.group(0)
    if attr(open_tag, "data-slot") != a["slot"]:
        return block
    if active:
        vu = rel_url(page_path, a["file"])
        pu = rel_url(page_path, a["poster_file"])
        new_open = set_attr(open_tag, "data-src", vu)
        new_open = set_attr(new_open, "poster", pu)
        new_open = set_attr(new_open, "data-media", "local")
        out = block.replace(open_tag, new_open, 1)
        if SOURCE_RE.search(out):
            out = SOURCE_RE.sub(lambda m: set_attr(m.group(0), "src", vu), out, count=1)
        return out
    fallback = a.get("fallback_data_src", "")
    new_open = set_attr(open_tag, "data-src", fallback)
    if a.get("fallback_poster"):
        new_open = set_attr(new_open, "poster", a["fallback_poster"])
    if a.get("fallback_data_media"):
        new_open = set_attr(new_open, "data-media", a["fallback_data_media"])
    else:
        new_open = del_attr(new_open, "data-media")
    out = block.replace(open_tag, new_open, 1)
    if SOURCE_RE.search(out) and fallback:
        out = SOURCE_RE.sub(lambda m: set_attr(m.group(0), "src", fallback), out, count=1)
    return out


def patch_preload(tag: str, page_path: Path, image_assets: dict, active: bool):
    slot = attr(tag, "data-slot")
    if not slot or slot not in image_assets:
        return tag
    a = image_assets[slot]
    if active:
        u = rel_url(page_path, a["file"])
        tag = set_attr(tag, "href", u)
        tag = del_attr(tag, "imagesrcset")
        tag = del_attr(tag, "imagesizes")
    else:
        tag = set_attr(tag, "href", a.get("fallback_src", ""))
        if a.get("fallback_srcset"):
            tag = set_attr(tag, "imagesrcset", a["fallback_srcset"])
        else:
            tag = del_attr(tag, "imagesrcset")
    return tag


def update_og(text: str, page: dict, active: bool):
    if active:
        hero = next((a for a in page["assets"] if a["type"] == "image" and "hero" in a.get("role", "")), None)
        if not hero:
            hero = next((a for a in page["assets"] if a["type"] == "image"), None)
        if not hero:
            return text
        site = json.loads(CFG_PATH.read_text(encoding="utf-8"))["site_url"].rstrip("/")
        url = site + "/" + hero["file"]
    else:
        url = page.get("original_og_image", "")
        if not url:
            return text
    esc = html.escape(url, quote=True)
    text = re.sub(r'(<meta property="og:image" content=")[^"]*(")', rf'\g<1>{esc}\2', text, count=1)
    tw = page.get("original_twitter_image", "") if not active else url
    if tw:
        twesc = html.escape(tw, quote=True)
        text = re.sub(r'(<meta name="twitter:image" content=")[^"]*(")', rf'\g<1>{twesc}\2', text, count=1)
    return text


def patch_page(page: dict, active: bool):
    path = ROOT / page["page"]
    if not path.exists():
        raise RuntimeError(f"Missing page {page['page']}")
    text = path.read_text(encoding="utf-8")
    before = text
    img_assets = {a["slot"]: a for a in page["assets"] if a["type"] == "image"}
    vid_assets = {a["slot"]: a for a in page["assets"] if a["type"] == "video"}
    text = IMG_RE.sub(lambda m: patch_img_tag(m.group(0), path, img_assets.get(attr(m.group(0), "data-slot"), {}), active)
                      if attr(m.group(0), "data-slot") in img_assets else m.group(0), text)
    text = PRELOAD_RE.sub(lambda m: patch_preload(m.group(0), path, img_assets, active), text)
    text = VIDEO_RE.sub(lambda m: patch_video_block(m.group(0), path, vid_assets.get(attr(re.match(r"<video\b[^>]*>", m.group(0), re.I).group(0), "data-slot"), {}), active)
                        if re.match(r"<video\b[^>]*>", m.group(0), re.I) and attr(re.match(r"<video\b[^>]*>", m.group(0), re.I).group(0), "data-slot") in vid_assets else m.group(0), text)
    text = update_og(text, page, active)
    if text != before:
        path.write_text(text, encoding="utf-8")
    return text != before


def activate(plan, page):
    # First inspect media. Posters are generated only after core assets are valid.
    problems = validate_page(page, generate_posters=False, quiet=False)
    core_problems = [p for p in problems if not p.startswith("MISSING: ") or "video-poster" not in p]
    if core_problems:
        sys.exit("Activation stopped. Fix the validation problems above; the page still uses its working online media.")
    # Generate any missing posters and validate once more.
    for a in page["assets"]:
        if a["type"] == "video":
            poster = ROOT / a["poster_file"]
            if not poster.exists():
                ok, msg = generate_poster(ROOT / a["file"], poster, int(a["poster_width"]), int(a["poster_height"]))
                print(("  + " if ok else "  ! ") + msg)
                if not ok:
                    sys.exit("Activation stopped; no page changes were made.")
    problems = validate_page(page, generate_posters=False, quiet=True)
    if problems:
        for p in problems:
            print("  ! " + p)
        sys.exit("Activation stopped; no page changes were made.")
    changed = patch_page(page, True)
    page["active"] = True
    page["production_status"] = "activated"
    save_plan(plan)
    build_dashboard(plan)
    print(f"ACTIVATED: {page['page']} ({'HTML updated' if changed else 'already using local media'})")


def deactivate(plan, page):
    changed = patch_page(page, False)
    page["active"] = False
    page["production_status"] = "pending"
    save_plan(plan)
    build_dashboard(plan)
    print(f"DEACTIVATED: {page['page']} ({'fallback media restored' if changed else 'already on fallback'})")


def reapply_active(plan):
    active = [p for p in plan["pages"] if p.get("active")]
    if not active:
        print("media_workflow: no activated local-media pages to reapply")
        return 0
    failed = 0
    for p in active:
        probs = validate_page(p, generate_posters=False, quiet=True)
        if probs:
            failed += 1
            print(f"! {p['page']}: local media invalid/missing")
            for x in probs:
                print("    " + x)
            continue
        patch_page(p, True)
        print(f"+ reapplied {p['page']}")
    if failed:
        sys.exit(f"reapply-active failed for {failed} page(s); build stopped to prevent broken local media")
    return len(active)


def status_line(page):
    have = 0
    need = 0
    for a in page["assets"]:
        if not a.get("required", True):
            continue
        need += 1
        if (ROOT / a["file"]).exists():
            have += 1
    state = "ACTIVE" if page.get("active") else ("READY" if have == need and need else "PENDING")
    return state, have, need


def show_status(plan, page=None):
    pages = [page] if page else plan["pages"]
    for p in pages:
        state, have, need = status_line(p)
        print(f"{p['priority']:>2}  {state:<7} {have:>2}/{need:<2}  {p['page']} — {p['label']}")


def show_next(plan, n=5):
    unfinished = [p for p in plan["pages"] if not p.get("active")]
    unfinished.sort(key=lambda p: (p["priority"], int(p.get("order", 999))))
    for p in unfinished[:n]:
        state, have, need = status_line(p)
        print(f"{p['priority']} #{p['order']:02d}  {p['label']}  [{have}/{need} files]  {p['page']}")


def local_ref_target(page_path: Path, url: str):
    if not url or url.startswith(("http://", "https://", "data:", "#", "mailto:", "tel:", "//")):
        return None
    parsed = urlparse(html.unescape(url))
    path = parsed.path
    if not path or path.startswith("/"):
        return None
    return (page_path.parent / path).resolve()


def audit_site(plan=None):
    problems = []
    scanned = 0
    media_refs = 0
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if rel.parts and rel.parts[0] in SKIP_DIRS:
            continue
        if path.name in {DASHBOARD.name, "content-uniqueness-audit.html", "media-replacement-inventory.html"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        scanned += 1
        # Local media references only. srcset items are split separately.
        tags = IMG_RE.findall(text) + [m.group(0) for m in re.finditer(r"<video\b[^>]*>", text, re.I)] + SOURCE_RE.findall(text)
        for tag in tags:
            for name in ("src", "poster", "data-src", "data-full"):
                u = attr(tag, name)
                target = local_ref_target(path, u or "")
                if target:
                    media_refs += 1
                    if not target.exists():
                        problems.append(f"{rel.as_posix()}: broken {name} -> {u}")
            ss = attr(tag, "srcset")
            if ss:
                for item in ss.split(","):
                    u = item.strip().split()[0] if item.strip() else ""
                    target = local_ref_target(path, u)
                    if target:
                        media_refs += 1
                        if not target.exists():
                            problems.append(f"{rel.as_posix()}: broken srcset -> {u}")
    # Active pages must resolve every planned slot to local media.
    if plan:
        for p in plan["pages"]:
            if not p.get("active"):
                continue
            path = ROOT / p["page"]
            t = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
            for a in p["assets"]:
                if a["type"] == "image":
                    expected = rel_url(path, a["file"])
                    if f'data-slot="{a["slot"]}"' not in t or expected not in t:
                        problems.append(f"{p['page']}: active slot not pointing to local image {a['slot']}")
                else:
                    expected = rel_url(path, a["file"])
                    if f'data-slot="{a["slot"]}"' not in t or expected not in t:
                        problems.append(f"{p['page']}: active slot not pointing to local video {a['slot']}")
    print(f"audit-site: {scanned} public HTML pages, {media_refs} local media references checked, {len(problems)} problem(s)")
    for x in problems[:200]:
        print("  ! " + x)
    if len(problems) > 200:
        print(f"  ... {len(problems)-200} more")
    return not problems


def esc(s):
    return html.escape(str(s or ""), quote=True)


def build_dashboard(plan):
    rows = []
    totals = {"P0": 0, "P1": 0, "P2": 0}
    active = 0
    for p in plan["pages"]:
        totals[p["priority"]] = totals.get(p["priority"], 0) + 1
        if p.get("active"):
            active += 1
        state, have, need = status_line(p)
        asset_rows = []
        for a in p["assets"]:
            exists = (ROOT / a["file"]).exists()
            if a["type"] == "image":
                dim = f"Create {a['create_width']}×{a['create_height']} · displays {a.get('display_width','?')}×{a.get('display_height','?')}"
                extra = ""
            else:
                dim = f"Create {a['create_width']}×{a['create_height']} · {a.get('duration_seconds','12–15')} sec"
                extra = f"<div><b>Poster:</b> <code>{esc(a['poster_file'])}</code> — generated automatically at activation.</div>"
            asset_rows.append(f'''<div class="asset {'done' if exists else ''}">
              <div class="asset-head"><span class="kind">{esc(a['type'].upper())}</span><b>{esc(a.get('role'))}</b><span class="pill">{'FILE FOUND' if exists else 'TO CREATE'}</span></div>
              <div><b>Filename/path:</b> <code>{esc(a['file'])}</code></div>
              <div><b>Dimensions:</b> {esc(dim)}</div>
              <div><b>Section:</b> {esc(a.get('section_context') or 'Page media section')}</div>
              {extra}
              <details><summary>Copy creation prompt</summary><pre>{esc(a.get('prompt'))}</pre></details>
            </div>''')
        rows.append(f'''<section class="page-card" id="{esc(Path(p['page']).stem)}">
          <div class="page-head"><div><span class="priority {p['priority']}">{p['priority']}</span><h2>{esc(p['label'])}</h2><p><code>{esc(p['page'])}</code></p></div><div class="status {state.lower()}">{state}<br><small>{have}/{need} core files</small></div></div>
          <p class="reason"><b>Visual direction:</b> {esc(p['business_reason'])}</p>
          <p class="folder"><b>Rule:</b> Every core file on this page is page-exclusive. Do not reuse these exact images/videos on another P0/P1 page.</p>
          <details class="assets"><summary>Show {len(p['assets'])} required media items & prompts</summary>{''.join(asset_rows)}</details>
        </section>''')
    html_out = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Vellore Catering World — Media Production Dashboard</title>
<style>
:root{{--ink:#172019;--muted:#667067;--line:#ddd8cc;--paper:#fffdf8;--gold:#9c6b1d;--green:#1e6f48;--red:#a53b2e}}*{{box-sizing:border-box}}body{{margin:0;font:15px/1.55 system-ui,Segoe UI,sans-serif;background:#f5f2eb;color:var(--ink)}}header{{background:#172019;color:white;padding:32px 5vw}}header h1{{margin:.2rem 0;font-size:clamp(28px,4vw,46px)}}header p{{max-width:1050px;color:#e5e1d8}}main{{max-width:1180px;margin:auto;padding:28px 18px 60px}}.summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:22px}}.summary div{{background:white;border:1px solid var(--line);border-radius:14px;padding:16px}}.summary b{{font-size:24px;display:block}}.rules{{background:#fff7dd;border:1px solid #e6d28b;border-radius:14px;padding:18px;margin:18px 0 26px}}.page-card{{background:white;border:1px solid var(--line);border-radius:16px;padding:20px;margin:14px 0}}.page-head{{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}}h2{{margin:4px 0}}.priority{{font-weight:800;border-radius:999px;padding:4px 8px;font-size:12px}}.P0{{background:#2b3b31;color:#fff}}.P1{{background:#e5efe8;color:#214d35}}.P2{{background:#eee;color:#444}}.status{{min-width:96px;text-align:center;padding:9px;border-radius:10px;font-weight:800}}.status.active{{background:#d8f2e4;color:#145d38}}.status.ready{{background:#e4efff;color:#204d83}}.status.pending{{background:#f4e9e6;color:#7a392d}}code{{font-size:13px;overflow-wrap:anywhere}}.reason,.folder{{color:#4d564f}}details.assets>summary{{cursor:pointer;font-weight:700;padding:8px 0}}.asset{{border-top:1px solid var(--line);padding:15px 0}}.asset-head{{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-bottom:8px}}.kind,.pill{{font-size:11px;font-weight:800;border-radius:999px;padding:3px 7px;background:#eee}}.asset.done .pill{{background:#d8f2e4;color:#145d38}}pre{{white-space:pre-wrap;background:#f5f2eb;padding:14px;border-radius:10px;border:1px solid var(--line)}}summary{{cursor:pointer}}.sequence{{background:white;border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:20px}}footer{{text-align:center;color:var(--muted);padding:20px}}
</style></head><body><header><p>Vellore Catering World</p><h1>Media Production Dashboard</h1><p>Create and activate media page-by-page without broken links. P0 is the first phase: the homepage plus every Wedding &amp; Marriage service page. P1 follows with other high-commercial-intent services. P2 contains supporting conversion pages.</p></header><main>
<div class="summary"><div><b>{len(plan['pages'])}</b>planned important pages</div><div><b>{totals.get('P0',0)}</b>P0 first-phase pages</div><div><b>{totals.get('P1',0)}</b>P1 business pages</div><div><b>{active}</b>pages activated locally</div></div>
<div class="rules"><b>Safe daily rule:</b> Create every listed core asset for one page, place it at the exact path, validate, then activate the whole page. Until activation, that page keeps the existing online stock media. Service pages normally need only <b>4 unique images + 1 unique video</b>; the video poster is created automatically.</div>
<div class="sequence"><b>Recommended first sequence:</b> Wedding Catering → Reception Catering → Engagement → Nichayathartham → Marriage Hall → Hindu/Muslim/Christian Wedding → the remaining Wedding &amp; Marriage pages. The homepage is P0 too, but because it has many more assets it can be completed across several days before activation.</div>
{''.join(rows)}
</main><footer>Generated from <code>data/media-replacement-plan.json</code> by <code>tools/media_workflow.py dashboard</code>.</footer></body></html>'''
    DASHBOARD.write_text(html_out, encoding="utf-8")
    print(f"dashboard: wrote {DASHBOARD.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p_status = sp.add_parser("status"); p_status.add_argument("page", nargs="?")
    p_val = sp.add_parser("validate"); p_val.add_argument("page")
    p_act = sp.add_parser("activate"); p_act.add_argument("page")
    p_de = sp.add_parser("deactivate"); p_de.add_argument("page")
    sp.add_parser("reapply-active")
    sp.add_parser("audit-site")
    sp.add_parser("dashboard")
    p_next = sp.add_parser("next"); p_next.add_argument("count", nargs="?", type=int, default=5)
    args = ap.parse_args()
    plan = load_plan()
    if args.cmd == "status":
        show_status(plan, resolve_page(plan, args.page) if args.page else None)
    elif args.cmd == "validate":
        p = resolve_page(plan, args.page)
        sys.exit(0 if not validate_page(p) else 1)
    elif args.cmd == "activate":
        activate(plan, resolve_page(plan, args.page))
    elif args.cmd == "deactivate":
        deactivate(plan, resolve_page(plan, args.page))
    elif args.cmd == "reapply-active":
        reapply_active(plan)
    elif args.cmd == "audit-site":
        sys.exit(0 if audit_site(plan) else 1)
    elif args.cmd == "dashboard":
        build_dashboard(plan)
    elif args.cmd == "next":
        show_next(plan, args.count)


if __name__ == "__main__":
    main()
