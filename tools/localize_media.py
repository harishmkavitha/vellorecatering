#!/usr/bin/env python3
"""
localize_media.py — download every hot-linked Pexels photo/video into the repo
and rewrite the HTML to use the local copies.   Version: V1

Why: the site ships with free-licence Pexels images linked from Pexels' CDN so
it looks complete immediately. Run this once on your computer to self-host
everything on GitHub (faster, no third-party dependency).

    python tools/localize_media.py             # download + rewrite
    python tools/localize_media.py --dry-run   # list what would change
    python tools/localize_media.py --skip-video

Needs internet access. Uses Pillow (pip install pillow) to save photos as WebP
when available; otherwise keeps JPEG. Safe to run again: existing files are
reused. Run it again after adding new pages that use Pexels images.
"""
import argparse
import html
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"partials", "tools", "templates", "data", ".git", "node_modules", "assets"}
PHOTO_DIR = ROOT / "assets" / "img" / "photos"
VIDEO_DIR = ROOT / "assets" / "video"
URL_RE = re.compile(r'https://(?:images|videos)\.pexels\.com/[^\s"\'<>,]+')
UA = {"User-Agent": "Mozilla/5.0 (VelloreCatering site tools)"}

try:
    from PIL import Image
except ImportError:
    Image = None


def local_name(url):
    raw = html.unescape(url)
    p = urlparse(raw)
    q = parse_qs(p.query)
    if "videos.pexels.com" in p.netloc:
        return VIDEO_DIR / Path(p.path).name
    m = re.search(r"/(?:photos|videos)/(\d+)/", p.path)
    pid = m.group(1) if m else re.sub(r"\W", "", p.path)[-12:]
    w = q.get("w", ["orig"])[0]
    h = q.get("h", [""])[0]
    kind = "vposter-" if p.path.startswith("/videos/") else ""
    ext = ".webp" if Image else ".jpg"
    return PHOTO_DIR / f"{kind}{pid}-{w}{'x' + h if h else ''}{ext}"


def download(url, target):
    if target.exists() and target.stat().st_size > 0:
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(html.unescape(url), headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except Exception as e:  # noqa
        print(f"  ! failed: {url} ({e})")
        return False
    if target.suffix == ".webp":
        from io import BytesIO
        im = Image.open(BytesIO(data)).convert("RGB")
        im.save(target, "WEBP", quality=80, method=6)
    else:
        target.write_bytes(data)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-video", action="store_true")
    args = ap.parse_args()

    pages = [p for p in sorted(ROOT.rglob("*.html"))
             if p.relative_to(ROOT).parts[0] not in SKIP_DIRS]
    urls = set()
    for page in pages:
        urls.update(URL_RE.findall(page.read_text(encoding="utf-8")))
    if args.skip_video:
        urls = {u for u in urls if "videos.pexels.com" not in u}
    print(f"localize_media: {len(urls)} remote files referenced in {len(pages)} pages")
    if args.dry_run:
        for u in sorted(urls):
            print(f"  {u}\n    -> {local_name(u).relative_to(ROOT)}")
        return

    ok = {}
    for i, u in enumerate(sorted(urls), 1):
        target = local_name(u)
        print(f"  [{i}/{len(urls)}] {target.name}")
        if download(u, target):
            ok[u] = target

    changed = 0
    for page in pages:
        text = page.read_text(encoding="utf-8")
        depth = len(page.relative_to(ROOT).parts) - 1
        prefix = "../" * depth
        # exact, whole-URL replacement (some URLs are prefixes of others)
        new = URL_RE.sub(
            lambda m: prefix + ok[m.group(0)].relative_to(ROOT).as_posix() if m.group(0) in ok else m.group(0),
            text)
        new = new.replace('<link rel="preconnect" href="https://images.pexels.com" crossorigin>\n', "")
        if new != text:
            page.write_text(new, encoding="utf-8")
            changed += 1
    failed = len(urls) - len(ok)
    print(f"localize_media: {len(ok)} downloaded, {failed} failed, {changed} pages rewritten")
    if failed:
        print("  Failed URLs stay hot-linked (the site shows a gold placeholder if one is broken).")
        sys.exit(1)


if __name__ == "__main__":
    main()
