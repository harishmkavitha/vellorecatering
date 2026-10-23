#!/usr/bin/env python3
"""
add_analytics.py - insert the Google Analytics 4 tag into every public page.
Version: V1

Run from the project root:

    python tools/add_analytics.py            # insert / update the tag
    python tools/add_analytics.py --check     # report what would change
    python tools/add_analytics.py --remove    # take the tag out again

The Measurement ID is read from tools/site_config.json ("ga4_measurement_id").

WHY THIS EXISTS INSTEAD OF sync_partials.py
-------------------------------------------
The GA4 tag lives in partials/head.html, so in principle sync_partials.py
would push it everywhere. In practice the published pages have since been run
through an HTML prettifier (alphabetised attributes, self-closing tags), so
re-syncing the raw partial would rewrite all 1,262 pages cosmetically and bury
the real change in a 20,000-line diff.

This script inserts just the tag, in the prettified style the pages already
use, immediately before the <!-- @head:end --> marker - which is inside the
head block, so a future sync_partials.py run regenerates it from the partial
rather than leaving a duplicate.

It is idempotent: running it twice changes nothing. If the Measurement ID in
site_config.json changes, running it again rewrites the existing tag.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "tools" / "site_config.json"
SKIP_DIRS = {"partials", "tools", "templates", "data", "docs", ".git", "node_modules", "assets"}

HEAD_END = "<!-- @head:end -->"
# sync_partials.py indents the end marker by two spaces; hand-edited and
# prettified pages have it at other indents. Capture whatever is there so the
# inserted block lines up with it and the script stays idempotent.
HEAD_END_RE = re.compile(r"(?P<indent>[ \t]*)" + re.escape(HEAD_END))
# Matches the whole inserted block, whatever Measurement ID it carries, so the
# script can replace or remove it cleanly.
BLOCK_RE = re.compile(
    r"[ \t]*<!-- Google Analytics 4 \(gtag\.js\).*?-->\n"
    r"[ \t]*<script async=\"\" src=\"https://www\.googletagmanager\.com/gtag/js\?id=[^\"]*\"></script>\n"
    r"[ \t]*<script>window\.dataLayer=.*?</script>\n",
    re.DOTALL,
)
# Any other gtag/GTM tag already on the page - we must not add a second one.
FOREIGN_TAG_RE = re.compile(r"googletagmanager\.com/(?:gtag/js|gtm\.js)")


def block_for(measurement_id: str) -> str:
    return (
        '<!-- Google Analytics 4 (gtag.js) | id: {mid} | inserted by tools/add_analytics.py -->\n'
        '<script async="" src="https://www.googletagmanager.com/gtag/js?id={mid}"></script>\n'
        "<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}"
        "gtag('js',new Date());gtag('config','{mid}');</script>\n"
    ).format(mid=measurement_id)


def indent_block(block: str, indent: str) -> str:
    """Re-indent every line of the block to sit level with the end marker."""
    return "".join(indent + line + "\n" for line in block.rstrip("\n").split("\n"))


def same_block(found: str, block: str) -> bool:
    """Compare ignoring indentation, so a re-indent alone is not a change."""
    norm = lambda s: "\n".join(ln.strip() for ln in s.strip().split("\n"))
    return norm(found) == norm(block)


def measurement_id() -> str:
    if not CONFIG.exists():
        sys.exit(f"Config not found: {CONFIG}")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    mid = (cfg.get("ga4_measurement_id") or "").strip()
    if not mid:
        sys.exit(
            'No "ga4_measurement_id" in tools/site_config.json.\n'
            'Add it, e.g. "ga4_measurement_id": "G-XXXXXXXXXX", then run this again.'
        )
    if not re.fullmatch(r"G-[A-Z0-9]{6,}", mid):
        sys.exit(f'"{mid}" does not look like a GA4 Measurement ID (expected G-XXXXXXXXXX).')
    return mid


def html_files():
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS:
            continue
        yield path


def run(check_only=False, remove=False, quiet=False):
    mid = measurement_id()
    block = block_for(mid)

    added, updated, removed, current, no_marker, foreign = [], [], [], [], [], []

    for page in html_files():
        original = page.read_text(encoding="utf-8")
        rel = page.relative_to(ROOT).as_posix()
        existing = BLOCK_RE.search(original)

        marker = HEAD_END_RE.search(original)
        indent = marker.group("indent") if marker else ""

        if remove:
            if not existing:
                continue
            text = BLOCK_RE.sub("", original)
            removed.append(rel)
        else:
            if existing:
                if same_block(existing.group(0), block):
                    current.append(rel)
                    continue
                text = BLOCK_RE.sub(indent_block(block, indent), original, count=1)
                updated.append(rel)
            else:
                # Guard: never stack a second Google tag on a page that has one.
                if FOREIGN_TAG_RE.search(original):
                    foreign.append(rel)
                    continue
                if not marker:
                    no_marker.append(rel)
                    continue
                text = (
                    original[: marker.start()]
                    + indent_block(block, indent)
                    + indent
                    + HEAD_END
                    + original[marker.end() :]
                )
                added.append(rel)

        if not check_only and text != original:
            page.write_text(text, encoding="utf-8")

    print(f"add_analytics ({mid}):")
    for label, group in (("added", added), ("updated", updated), ("removed", removed)):
        if group:
            print(f"  {len(group):5d} {'would be ' + label if check_only else label}")
    if current:
        print(f"  {len(current):5d} already current")
    if not quiet:
        for rel in (added + updated + removed)[:10]:
            print(f"    ~ {rel}")
        shown = len(added + updated + removed)
        if shown > 10:
            print(f"    … and {shown - 10} more")
    for rel in no_marker:
        print(f"  ! no {HEAD_END} marker, skipped: {rel}")
    for rel in foreign:
        print(f"  ! another Google tag already present, skipped: {rel}")

    if (no_marker or foreign) and not check_only:
        print("\nSome pages were skipped. Fix them by hand or they will not report.")
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--check", action="store_true", help="report without writing")
    parser.add_argument("--remove", action="store_true", help="take the tag out of every page")
    parser.add_argument("--quiet", action="store_true", help="do not list affected files")
    args = parser.parse_args()
    sys.exit(run(check_only=args.check, remove=args.remove, quiet=args.quiet))
