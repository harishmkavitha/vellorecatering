#!/usr/bin/env python3
"""
localize_media.py — self-host every Pexels photo/video the site uses.   Version: V2

V2: now a thin wrapper around tools/stock_media.py, which owns the media
library, file naming (assets/img/stock/<key>-<w>x<h>.webp) and page rewriting.
Kept so older notes and habits still work.

    python tools/localize_media.py              # = stock_media.py download
    python tools/localize_media.py --skip-video
    python tools/localize_media.py --dry-run    # = stock_media.py check (tests URLs only)

Needs internet access. Optional: Pillow (WebP), FFmpeg (video trimming),
PEXELS_API_KEY (category-specific videos). See the docstring in stock_media.py.
"""
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "stock_media.py"


def main():
    args = sys.argv[1:]
    if "--dry-run" in args:
        cmd = ["check"]
    else:
        cmd = ["download"] + (["--skip-video"] if "--skip-video" in args else [])
    sys.exit(subprocess.call([sys.executable, str(TOOL), *cmd]))


if __name__ == "__main__":
    main()
