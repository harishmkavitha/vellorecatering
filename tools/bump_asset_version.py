#!/usr/bin/env python3
"""
bump_asset_version.py - point every page at the current assets/js/main.js version.
Version: V1

Run from the project root:

    python tools/bump_asset_version.py --check    # report what would change
    python tools/bump_asset_version.py            # rewrite the pages
    python tools/bump_asset_version.py --set 3    # also bump site_config.json first

WHY THIS MATTERS
----------------
Pages load the script as:

    <script defer src="assets/js/main.js?v=2"></script>

The "?v=" query is the cache buster. If you change assets/js/main.js but leave the
query alone, returning visitors keep the copy their browser already has - so a new
feature (analytics click tracking, say) silently never runs for them.

The number comes from "asset_version" in tools/site_config.json, which is what the
page generators use. This script makes the already-published pages agree with it,
without regenerating them.

So after any edit to main.js: bump asset_version, then run this.
It is idempotent, and it leaves main.css alone (that has its own version query).
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "tools" / "site_config.json"
SKIP_DIRS = {"partials", "tools", "templates", "data", "docs", ".git", "node_modules", "assets"}

# Matches main.js?v=<anything> but NOT the ${asset_version} template placeholder.
REF_RE = re.compile(r"(assets/js/main\.js\?v=)(\d+)")


def read_version() -> str:
    if not CONFIG.exists():
        sys.exit(f"Config not found: {CONFIG}")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    version = str(cfg.get("asset_version", "")).strip()
    if not version.isdigit():
        sys.exit(f'"asset_version" in site_config.json must be a number, found: {version!r}')
    return version


def write_version(version: str) -> None:
    text = CONFIG.read_text(encoding="utf-8")
    new, n = re.subn(r'("asset_version":\s*")[^"]*(")', rf"\g<1>{version}\g<2>", text, count=1)
    if n != 1:
        sys.exit('Could not find "asset_version" in site_config.json to update.')
    CONFIG.write_text(new, encoding="utf-8")
    print(f'site_config.json: asset_version -> "{version}"')


def html_files():
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS:
            continue
        yield path


def run(check_only=False, set_to=None):
    if set_to is not None:
        if not str(set_to).isdigit():
            sys.exit(f"--set needs a number, got {set_to!r}")
        if not check_only:
            write_version(str(set_to))

    version = str(set_to) if (set_to is not None and check_only) else read_version()

    changed, current, missing = [], [], []
    for page in html_files():
        original = page.read_text(encoding="utf-8")
        rel = page.relative_to(ROOT).as_posix()
        if not REF_RE.search(original):
            missing.append(rel)
            continue
        text = REF_RE.sub(lambda m: m.group(1) + version, original)
        if text == original:
            current.append(rel)
            continue
        changed.append(rel)
        if not check_only:
            page.write_text(text, encoding="utf-8")

    verb = "would be updated" if check_only else "updated"
    print(f"bump_asset_version (main.js?v={version}):")
    if changed:
        print(f"  {len(changed):5d} {verb}")
    if current:
        print(f"  {len(current):5d} already current")
    for rel in missing:
        print(f"  ! no main.js reference: {rel}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--check", action="store_true", help="report without writing")
    parser.add_argument("--set", metavar="N", help="set asset_version to N first")
    args = parser.parse_args()
    sys.exit(run(check_only=args.check, set_to=args.set))
