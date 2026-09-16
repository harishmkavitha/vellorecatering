#!/usr/bin/env python3
"""
build.py — one command to rebuild the site after any change.   Version: V1

    python tools/build.py

Steps:
  1. build_catalog_nav.py — build category mega-menu from catalog
  2. generate_catalog_site.py — build every Catering Type page
  3. sync_partials.py   — push head/nav/footer into every page
  4. build_sitemap.py   — rewrite sitemap.xml from canonical URLs
  5. quick checks       — duplicate titles/descriptions, missing alt, broken internal links
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
SKIP_DIRS = {"partials", "tools", "templates", "data", ".git", "node_modules", "assets"}


def run(script, *args):
    r = subprocess.run([sys.executable, str(TOOLS / script), *args], cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"build: {script} failed")


def checks():
    pages = [p for p in sorted(ROOT.rglob("*.html")) if p.relative_to(ROOT).parts[0] not in SKIP_DIRS]
    titles, descs, problems = {}, {}, []
    for p in pages:
        rel = p.relative_to(ROOT).as_posix()
        t = p.read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", t, re.S)
        desc = re.search(r'<meta name="description" content="([^"]*)"', t)
        for store, m, label in ((titles, title, "title"), (descs, desc, "description")):
            if not m:
                problems.append(f"{rel}: missing {label}")
                continue
            v = m.group(1).strip()
            if v in store:
                problems.append(f"{rel}: duplicate {label} with {store[v]}")
            store[v] = rel
        if len(re.findall(r"<h1[\s>]", t)) != 1:
            problems.append(f"{rel}: should have exactly one <h1>")
        for tag in re.findall(r"<img\b[^>]*>", t):
            if " alt=" not in tag:
                problems.append(f"{rel}: <img> without alt")
        for href in re.findall(r'href="([^"#:?]+\.(?:html|xml))(?:[#?][^"]*)?"', t):
            target = (p.parent / href).resolve()
            if not target.exists():
                problems.append(f"{rel}: broken link -> {href}")
    print(f"checks: {len(pages)} pages scanned, {len(problems)} problem(s)")
    for pr in problems:
        print("  ! " + pr)
    return not problems


if __name__ == "__main__":
    run("build_catalog_nav.py")
    run("generate_catalog_site.py")
    run("generate_area_blog_site.py")
    run("sync_partials.py", "--quiet")
    run("build_sitemap.py")
    sys.exit(0 if checks() else 1)
