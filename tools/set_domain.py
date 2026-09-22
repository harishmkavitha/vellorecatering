#!/usr/bin/env python3
"""
set_domain.py — switch the site's canonical domain in one go.   Version: V1

    python tools/set_domain.py https://www.vellorecatering.in

Updates tools/site_config.json, every page's canonical/OG/schema URLs,
404.html <base>, robots.txt and sitemap.xml. For a custom domain it also writes
the CNAME file GitHub Pages needs.
"""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "tools" / "site_config.json"
SKIP_DIRS = {".git", "node_modules", "assets"}


def main():
    if len(sys.argv) != 2 or not sys.argv[1].startswith("https://"):
        sys.exit("usage: python tools/set_domain.py https://your-domain.in")
    new = sys.argv[1].rstrip("/")
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    old = cfg["site_url"].rstrip("/")
    if old == new:
        sys.exit("Domain is already set to " + new)
    cfg["site_url"] = new
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    changed = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in {".html", ".xml", ".txt", ".webmanifest", ".json"}:
            continue
        if path.relative_to(ROOT).parts[0] in SKIP_DIRS or path == CFG:
            continue
        text = path.read_text(encoding="utf-8")
        if old in text:
            path.write_text(text.replace(old, new), encoding="utf-8")
            changed += 1

    host = urlparse(new).netloc
    cname = ROOT / "CNAME"
    if host.endswith("github.io"):
        if cname.exists():
            cname.unlink()
    else:
        cname.write_text(host + "\n", encoding="utf-8")
    print(f"set_domain: {old} -> {new} in {changed} files" + ("" if host.endswith("github.io") else f"; CNAME = {host}"))


if __name__ == "__main__":
    main()
