#!/usr/bin/env python3
"""
stock_media.py — real South Indian food, catering and wedding photos/videos
for every page of the site.                                      Version: V1

All media comes from Pexels (https://www.pexels.com/license/): free for
commercial use, no attribution required, may be modified. The curated list
lives in data/media-library.json; edit that file to add, remove or swap items.

    python tools/stock_media.py apply        # swap every placeholder for a library photo/video
    python tools/stock_media.py check        # confirm every Pexels URL answers (run on your PC)
    python tools/stock_media.py download     # self-host: save photos as WebP + videos as MP4, then apply
    python tools/stock_media.py download --skip-video
    python tools/stock_media.py review       # write tools/media-review.html (contact sheet to eyeball)
    python tools/stock_media.py prune        # list generated SVG/WebM placeholders no page uses
    python tools/stock_media.py prune --yes  # ...and delete them

How it works
  * Every generated placeholder (assets/img/pages|areas|blogs|master-generated,
    assets/video/pages|master-generated) is a "slot". Each slot gets a photo
    chosen by page theme (wedding, pooja, corporate, biryani ...) and a stable
    hash, so the same page always gets the same photos and a page never shows
    the same photo twice.
  * Rewritten tags keep data-slot="..." so re-running is safe, and
    tools/build.py re-applies media after it regenerates pages.
  * Until you run "download", photos load from the Pexels CDN (already cropped
    to each slot's shape). After "download", apply points at the local copies
    in assets/img/stock/ and assets/video/stock/ automatically.
  * Also writes credits.html (noindex) and swaps SVG og:images for real photos.

Optional
  PEXELS_API_KEY  free key from https://www.pexels.com/api/ — lets "download"
                  fetch the category-specific videos (cooking, biryani, coffee...).
                  Without it only the verified dosa clip is downloaded.
  Pillow          pip install pillow   (WebP conversion; JPEG kept otherwise)
  FFmpeg          on PATH              (trims videos to 12 s, 1280 px, no audio)
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB_PATH = ROOT / "data" / "media-library.json"
CFG_PATH = ROOT / "tools" / "site_config.json"
IMG_DIR = ROOT / "assets" / "img" / "stock"
VID_DIR = ROOT / "assets" / "video" / "stock"
REVIEW_PATH = ROOT / "tools" / "media-review.html"
CREDITS_PATH = ROOT / "credits.html"
SKIP_DIRS = {"partials", "tools", "templates", "data", ".git", "node_modules", "assets", "docs"}
GENERATED_DIRS = [ROOT / "assets/img/pages", ROOT / "assets/img/areas", ROOT / "assets/img/blogs",
                  ROOT / "assets/img/master-generated", ROOT / "assets/video/pages",
                  ROOT / "assets/video/master-generated"]
WIDTHS = (480, 800, 1200, 1600)
DEFAULT_VIDEO = "dosa-griddle"

CFG = json.loads(CFG_PATH.read_text(encoding="utf-8"))
SITE = CFG["site_url"].rstrip("/")
UA = f"Mozilla/5.0 (compatible; VelloreCateringMediaTool/1.0; +{SITE}/)"

# --------------------------------------------------------------------------
# Hand-picked photos for the master pages (home, about, menus, gallery,
# contact). keep=True keeps the page's existing alt text because the photo
# matches it; otherwise the photo's own description is used.
# --------------------------------------------------------------------------
MASTER = {
    # index.html
    "adde795c011ff9": ("feast-elaborate", True),
    "53ac256b571616": ("feast-sweets", True),
    "52e030f3b3908e": ("ritual-hands", False),
    "0b638224237be3": ("snacks-platter", False),
    "dfac94ddd6722d": ("henna-bangles", False),
    "2ea0f6934e6bc9": ("cook-traditional", False),
    "3e371b48a89137": ("vada-leaf", True),
    "73f32e44f147d7": ("sadya-kerala", False),
    "05d8ec6b5be593": ("tiffin-spread", True),
    "d7c47ea1d6a698": ("buffet-copper", True),
    "223c6f434e55f3": ("biryani-egg", True),
    "0e8f1ecf5f8481": ("dosa-banana-leaf", False),
    "849fc2d2a88275": ("buffet-greenery", True),
    "1458c99b8a6328": ("sweets-golden", True),
    "75ebc667c7459d": ("ritual-feet", False),
    "eab049ff51f4ec": ("vada-dark", True),
    "82adb56451535c": ("buffet-outdoor", False),
    # about.html
    "359b45fddf9881": ("cook-traditional", False),
    "a5241fbc224bde": ("buffet-copper", True),
    "75f5c13fabcebb": ("sweets-golden", True),
    # menus.html
    "7a89ad69124bd4": ("feast-elaborate", True),
    "7b4944d2a7f074": ("feast-sweets", True),
    "94959bb119939b": ("tiffin-spread", True),
    "1d1030f10d13ac": ("buffet-copper", True),
    "45f2aded26bdf9": ("biryani-egg", True),
    "4a52a6a51a8f40": ("sweets-golden", True),
    "187c3f4d0595e9": ("bangles-coconut", False),
    "1c41627a69ee9a": ("snacks-platter", True),
    "22efc54e63d949": ("samosa-tiered", True),
    # contact.html
    "26069e460def59": ("sadya-kerala", False),
    # gallery.html
    "98fd33f325cb46": ("appetiser-cups", True),
    "e4efa356b3212d": ("feast-sweets", True),
    "9939310f644bc3": ("buffet-greenery", True),
    "d5ba46b684ea5d": ("groom-family", False),
    "cbb90e46451545": ("vada-sambar-dark", True),
    "8feabcbc6ea066": ("buffet-copper", True),
    "3087d103bea139": ("sweets-golden", True),
    "72ff669e509927": ("couple-outdoor", False),
    "b721a7f6744434": ("tiffin-spread", True),
    "d6b0ffb7844bd1": ("snacks-platter", False),
    "98f18c4220ae72": ("biryani-egg", True),
    "16cb5d19c31539": ("buffet-outdoor", True),
    "f5303958e7fcdf": ("henna-bangles", True),
    "47f9c85b392b6a": ("breakfast-tea", False),
    "8e636411932f06": ("appetiser-cups", True),
    "2be6cb201f5641": ("rings-henna", False),
    "52de7c0d2fe8b3": ("cook-traditional", False),
    "43a263c4dec40e": ("sweets-silver", True),
    "12414b2458da8a": ("dosa-rustic", True),
    "7ef2b165409070": ("tandoori-chicken", True),
    "80c91adc6bb642": ("appetiser-tray", True),
}
# master videos: slot name -> (video key, poster master slot, poster w, poster h)
MASTER_VIDEO = {
    "04a06450cbab6f": (DEFAULT_VIDEO, "adde795c011ff9", 1600, 1000),
    "gallery-showcase": ("curry-rice", "98fd33f325cb46", 1600, 900),
}

# --------------------------------------------------------------------------
# Page themes: tag preferences for [hero, gallery-1, gallery-2, gallery-3, video]
# --------------------------------------------------------------------------
THEMES = {
    "wedding":       (["couple", "bride"], ["feast"], ["buffet", "sweets"], ["ritual", "family"], ["wedding"]),
    "engagement":    (["engagement", "ritual"], ["sweets"], ["feast", "buffet"], ["bride", "couple"], ["feast"]),
    "reception":     (["premium", "reception"], ["cocktail"], ["couple", "bride"], ["sweets"], ["buffet"]),
    "destination":   (["destination", "couple"], ["buffet", "outdoor"], ["feast"], ["sweets", "cocktail"], ["wedding"]),
    "prewedding":    (["haldi"], ["mehendi", "sweets"], ["snacks", "cocktail"], ["haldi", "prewedding"], ["snacks"]),
    "family_ritual": (["valaikappu"], ["feast"], ["sweets"], ["tiffin"], ["feast"]),
    "celebration":   (["sweets", "celebration"], ["snacks"], ["buffet"], ["feast", "tiffin"], ["festival"]),
    "traditional":   (["feast", "festival"], ["tiffin", "traditional"], ["sweets"], ["ritual", "pongal"], ["traditional"]),
    "solemn":        (["solemn"], ["solemn"], ["solemn"], ["solemn"], ["solemn"]),
    "biryani":       (["biryani"], ["nonveg"], ["buffet"], ["sweets", "biryani"], ["biryani"]),
    "kerala":        (["kerala"], ["feast"], ["tiffin"], ["sweets", "kerala"], ["feast"]),
    "northindian":   (["northindian"], ["buffet"], ["snacks", "fusion"], ["sweets", "nonveg"], ["northindian"]),
    "corporate":     (["corporate"], ["snacks", "hightea"], ["cocktail", "buffet"], ["tiffin", "feast"], ["corporate"]),
    "tiffin":        (["breakfast"], ["tiffin"], ["coffee", "hightea"], ["snacks"], ["coffee", "tiffin"]),
    "cocktail":      (["cocktail"], ["snacks"], ["premium", "buffet"], ["nonveg", "sweets"], ["snacks"]),
    "institutional": (["institutional", "feast"], ["tiffin"], ["buffet"], ["snacks", "sweets"], ["institutional", "feast"]),
    "healthy":       (["healthy"], ["veg"], ["feast"], ["healthy", "tiffin"], ["healthy"]),
    "everyday":      (["everyday"], ["tiffin"], ["biryani", "feast"], ["snacks"], ["everyday"]),
    "service":       (["hero", "buffet"], ["livecounter", "chef"], ["buffet"], ["feast", "tiffin"], ["livecounter"]),
    "sweets":        (["sweets"], ["sweets", "snacks"], ["snacks"], ["tiffin", "feast"], ["festival"]),
}
# Themes that must never show people or celebration imagery
QUIET_THEMES = {"solemn"}
# Themes where non-vegetarian dishes would be out of place
VEG_THEMES = {"wedding", "engagement", "family_ritual", "traditional", "solemn", "healthy", "tiffin", "prewedding"}

# First matching rule wins. Plain words match at a word start; "^..." is a raw regex.
KEYWORDS = [
    ("solemn", ["funeral", "condolence", "obsequies", "death", "remembrance", "memorial", "tithi", "karumathi", "shraddh", "shradh", "bereavement"]),
    ("prewedding", ["haldi", "mehendi", "mehndi", "sangeet", "bridal shower", "bachelor", "pre-wedding", "pre wedding"]),
    ("family_ritual", ["valaikappu", "seemandham", "seemantham", "baby shower", "baby welcome", "naming", "cradle", "annaprasana",
                       "punyavachanam", "ear piercing", "puberty", "manjal"]),
    ("biryani", ["muslim", "ramadan", "iftar", "halal", "eid", "bakrid", "non-veg", "non veg", "chettinad", "andhra",
                 "hyderabadi", "seafood", "bbq", "barbecue", "biryani", "arabic"]),
    ("kerala", ["kerala", "onam", "sadya"]),
    ("northindian", ["north indian", "punjabi", "gujarati", "rajasthani", "marwari", "mughlai", "chinese", "continental",
                     "italian", "mexican", "fusion", "chaat", "tandoor", "bengali", "thai", "international", "asian",
                     "mediterranean", "multi-cuisine", "maharashtrian"]),
    ("healthy", ["vegan", "jain", "gluten", "ayurved", "diabetic", "satvik", "sattvic", "organic", "millet", "keto",
                 "diet", "allergy", "healthy", "senior"]),
    ("sweets", ["sweet", "dessert", "ice cream", "bakery", "cake"]),
    ("tiffin", ["breakfast", "tiffin", "coffee", r"^\btea\b", "brunch", "beverage"]),
    ("cocktail", ["cocktail", "pool party", "dj", "celebrity", "club", "lounge", "rooftop"]),
    ("destination", ["destination"]),
    ("engagement", ["engagement", "nichayathartham", "ring ceremony", "betrothal"]),
    ("reception", ["reception", "groom", "bridal welcome"]),
    ("wedding", ["wedding", "marriage", "kalyanam", "nikah"]),
    ("institutional", ["retirement home", "parent-teacher", "graduation", "convocation", "school", "college", "university", "hostel", "student", "sports",
                       "annual day", "canteen", "hospital", "healthcare", "patient", "old age", "orphanage", "ngo",
                       "government", "public", "community", "apartment", "association", "industrial", "factory"]),
    ("celebration", ["birthday", "kids", "children", "anniversary", "reunion", "friendship", "success", "milestone",
                     "retirement", "farewell", "party", "get-together", "get together", "christmas"]),
    ("traditional", ["banana leaf", "thali", "pooja", "puja", "temple", "annadhanam", "annadanam", "religious", "navratri", "ganesh", "krishna",
                     "saraswati", "pongal", "tamil new year", "festival", "diwali", "deepavali", "sathabhishekam",
                     "sashti", "housewarming", "griha", "gruha", "upanayanam", "homam", "christmas", "church",
                     "spiritual", "bhajan", "ayudha", "karthigai", "hindu", "christian"]),
    ("corporate", ["corporate", "office", "conference", "seminar", "dealer", "agm", "press", "product", "team",
                   "meeting", "award", "business", "board", "launch", "trade", "exhibition", "expo", "training",
                   "workshop", "summit", "political", "backstage"]),
    ("everyday", ["packaged", "packed", "box", "daily", "subscription", "mini meal", "cloud kitchen", "food truck",
                  "delivery", "parcel", "lunch", "bulk", "cafe", "hotel", "restaurant", "retail", "shop", "mess"]),
    ("service", ["live counter", "buffet", "on-site", "onsite", "full service", "outdoor", "venue", "hall",
                 "convention", "travel", "airport", "mandapam", "resort", "farm", "kitchen", "staff"]),
]
CATEGORY_THEME = {
    "Wedding & Marriage": "wedding", "Special Occasions": "celebration", "Birthday & Family": "celebration",
    "Religious & Traditional": "traditional", "Religious Festivals & Seasonal": "traditional",
    "Religious & Spiritual": "traditional", "Corporate & Business": "corporate", "Events & Entertainment": "cocktail",
    "Food Service Formats": "service", "Cuisine-Based": "traditional", "Specialized & Dietary": "healthy",
    "Travel & Venue": "service", "Social & Community": "institutional", "Education": "institutional",
    "Retail & Commercial": "everyday", "Healthcare & Institutional": "institutional",
}
AREA_SLOTS = {"hero": ["hero", "feast", "buffet"], "food": ["tiffin", "sweets", "feast"],
              "wedding": ["couple", "bride", "ritual", "wedding"]}

# Locality pages stay with South Indian food and Tamil-style occasions
AREA_AVOID = {"northindian", "haldi", "cocktail"}

TEXT_FIXES = [
    ("Generated, copyright-free illustrations for planning inspiration; they are not presented as photographs of past client events.",
     "Representative stock photographs (free Pexels licence) shown for planning inspiration; they are not presented as photographs of past client events."),
    ("These original illustrations are visual placeholders until you add your own real event photography.",
     "The photos below are representative stock images for presentation ideas, not records of past client events."),
    ("Illustrative artwork is used until verified real-event photographs are supplied.",
     "Representative stock photographs are used until verified real-event photographs are supplied."),
    ("The visual is illustrative and is not presented as a photograph of a completed client event.",
     "The photo is a representative stock image and is not presented as a photograph of a completed client event."),
]

IMG_RE = re.compile(r"<img\b[^>]*>")
VERSION_RE = re.compile(r"(<!-- Vellore Catering World \| [^|]+ \| Version: )V1\b")
GENERATED_RE = re.compile(r"(<!-- Vellore Catering World \| [^|]+ \| GENERATED )V2\b")
PRELOAD_RE = re.compile(r'<link rel="preload" as="image"[^>]*>')
VIDEO_RE = re.compile(r"<video\b[^>]*>.*?</video>", re.S)
FIGURE_RE = re.compile(r"<figure\b[^>]*>.*?</figure>", re.S)
SLOT_SRC = re.compile(r"assets/img/(pages|areas|blogs|master-generated)/([^\"'/?#\s]+?)\.svg")
VSLOT_SRC = re.compile(r"assets/video/(pages|master-generated)/([^\"'/?#\s]+?)\.webm")
PAGE_PART = re.compile(r"^(.*)-(hero|gallery-1|gallery-2|gallery-3)$")
AREA_PART = re.compile(r"^(.*)-(hero|food|wedding)$")
META_IMG = re.compile(r'(<meta (?:property="og:image"|name="twitter:image") content=")([^"]*)(")')
LD_IMG = re.compile(r'("image":\s*")([^"]*)(")')
REPLACEABLE = re.compile(r"/assets/img/(?:pages|areas|blogs|stock)/|images\.pexels\.com")


# ------------------------------------------------------------------ helpers
def h32(text: str) -> int:
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16)


def get_attr(tag, name):
    m = re.search(r"\s%s=\"([^\"]*)\"" % re.escape(name), tag)
    return html.unescape(m.group(1)) if m else None


def set_attr(tag, name, value):
    val = html.escape(str(value), quote=True)
    pat = re.compile(r"(\s%s=\")[^\"]*(\")" % re.escape(name))
    if pat.search(tag):
        return pat.sub(lambda m: m.group(1) + val + m.group(2), tag, count=1)
    end = "/>" if tag.endswith("/>") else ">"
    return tag[: -len(end)].rstrip() + f' {name}="{val}"' + end


def del_attr(tag, name):
    return re.sub(r"\s%s=\"[^\"]*\"" % re.escape(name), "", tag)


def titleize(slug):
    return re.sub(r"\s+", " ", slug.replace("-", " ")).strip().title()


def pages():
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS:
            continue
        yield p


def fetch(url, dest=None, headers=None, tries=3):
    hdrs = {"User-Agent": UA}
    hdrs.update(headers or {})
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=90) as r:
                if dest is None:
                    return r.read()
                with open(dest, "wb") as fh:
                    shutil.copyfileobj(r, fh, 1024 * 256)
                return dest
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"{url} -> {last}")


# ------------------------------------------------------------------ library
class Library:
    def __init__(self):
        data = json.loads(LIB_PATH.read_text(encoding="utf-8"))
        self.tpl = data["photo_url"]
        self.photos = {p["key"]: p for p in data["photos"]}
        self.videos = {v["key"]: v for v in data["videos"]}
        self.keys = sorted(self.photos)
        self.catalog = {}
        cat = ROOT / "data" / "catering-catalog.json"
        if cat.exists():
            for it in json.loads(cat.read_text(encoding="utf-8"))["items"]:
                self.catalog[it["slug"]] = it
        self.blogs = {}
        blog = ROOT / "data" / "blog-catalog.json"
        if blog.exists():
            for it in json.loads(blog.read_text(encoding="utf-8"))["items"]:
                self.blogs[it["slug"]] = it
        self.areas = {}
        area = ROOT / "data" / "servicing-areas.json"
        if area.exists():
            for it in json.loads(area.read_text(encoding="utf-8")).get("items", []):
                slug = it.get("image_slug") or it.get("slug")
                if slug:
                    self.areas[slug] = it
        self.photo_requests = set()   # (key, w, h, fmt)
        self.video_requests = set()
        self.photo_usage = Counter()
        self.video_usage = Counter()
        self.remote_hits = 0
        self.local_hits = 0

    # ---- URLs
    def remote_img(self, key, w, h):
        p = self.photos[key]
        extra = "&fm=jpg" if p["ext"] == "png" else ""
        return self.tpl.format(id=p["pexels_id"], ext=p["ext"], w=w, h=h, extra=extra)

    @staticmethod
    def local_img(key, w, h, fmt):
        return IMG_DIR / f"{key}-{w}x{h}.{fmt}"

    def img_url(self, key, w, h, depth):
        self.photo_requests.add((key, w, h, "webp"))
        for fmt in ("webp", "jpg"):
            lp = self.local_img(key, w, h, fmt)
            if lp.exists():
                self.local_hits += 1
                return "../" * depth + lp.relative_to(ROOT).as_posix()
        self.remote_hits += 1
        return self.remote_img(key, w, h)

    def og_url(self, key):
        self.photo_requests.add((key, 1200, 630, "jpg"))
        lp = self.local_img(key, 1200, 630, "jpg")
        if lp.exists():
            return f"{SITE}/{lp.relative_to(ROOT).as_posix()}"
        return self.remote_img(key, 1200, 630)

    def video_available(self, vkey):
        return (VID_DIR / f"{vkey}.mp4").exists() or bool(self.videos[vkey].get("verified_file"))

    def video_url(self, vkey, depth):
        local = VID_DIR / f"{vkey}.mp4"
        if local.exists():
            return "../" * depth + local.relative_to(ROOT).as_posix()
        return self.videos[vkey]["verified_file"]

    # ---- selection
    def pick(self, tags, seed, used, quiet=False, veg=False, avoid=()):
        tags, avoid = set(tags), set(avoid)

        def ok(p, fresh):
            if quiet and (p["people"] or {"sweets", "festival", "celebration", "cocktail"} & set(p["tags"])):
                return False
            if veg and "nonveg" in p["tags"]:
                return False
            if avoid & set(p["tags"]):
                return False
            return (not fresh or p["key"] not in used) and bool(tags & set(p["tags"]))

        for fresh in (True, False):
            cands = [k for k in self.keys if ok(self.photos[k], fresh)]
            if cands:
                return cands[h32(seed) % len(cands)]
        cands = [k for k in self.keys if "feast" in self.photos[k]["tags"] and k not in used] or self.keys
        return cands[h32(seed) % len(cands)]

    def pick_video(self, tags, seed):
        cands = sorted(k for k, v in self.videos.items() if set(tags) & set(v["tags"])) or [DEFAULT_VIDEO]
        wanted = cands[h32(seed) % len(cands)]
        self.video_requests.add(wanted)
        return wanted if self.video_available(wanted) else DEFAULT_VIDEO

    def theme_for(self, name, categories=()):
        low = name.lower()
        for theme, words in KEYWORDS:
            for w in words:
                pat = w[1:] if w.startswith("^") else r"\b" + re.escape(w)
                if re.search(pat, low):
                    return theme
        for c in categories:
            if c in CATEGORY_THEME:
                return CATEGORY_THEME[c]
        return "traditional"

    def service_info(self, slug):
        it = self.catalog.get(slug)
        if it:
            return it["catering_type"], self.theme_for(it["catering_type"], it.get("categories", []))
        name = titleize(slug.replace("-in-vellore", ""))
        return name, self.theme_for(name)

    def assign_service(self, slug):
        name, theme = self.service_info(slug)
        prefs = THEMES[theme]
        quiet, veg = theme in QUIET_THEMES, theme in VEG_THEMES
        used, out = set(), {}
        for part, tags in zip(("hero", "gallery-1", "gallery-2", "gallery-3"), prefs[:4]):
            k = self.pick(tags, f"pages/{slug}-{part}", used, quiet, veg)
            used.add(k)
            out[part] = k
        return out, name, theme

    def assign_area(self, slug):
        used, out = set(), {}
        for part in ("hero", "food", "wedding"):
            k = self.pick(AREA_SLOTS[part], f"areas/{slug}-{part}", used, veg=True, avoid=AREA_AVOID)
            used.add(k)
            out[part] = k
        return out

    def area_name(self, slug):
        it = self.areas.get(slug)
        for field in ("area", "name", "locality", "title"):
            if it and it.get(field):
                return it[field]
        return titleize(slug)

    def resolve(self, slot):
        """slot -> (photo key, keep_alt, context label, kind, part)"""
        kind, _, name = slot.partition("/")
        if kind == "master":
            key, keep = MASTER.get(name, ("feast-elaborate", False))
            return key, keep, "", kind, ""
        if kind == "pages":
            m = PAGE_PART.match(name)
            slug, part = (m.group(1), m.group(2)) if m else (name, "hero")
            chosen, sname, _ = self.assign_service(slug)
            return chosen[part], False, f"{sname} in Vellore", kind, part
        if kind == "areas":
            m = AREA_PART.match(name)
            slug, part = (m.group(1), m.group(2)) if m else (name, "hero")
            name = self.area_name(slug)
            label = f"catering in {name}" + ("" if "vellore" in name.lower() else ", Vellore")
            return self.assign_area(slug)[part], False, label, kind, part
        if kind == "blogs":
            it = self.blogs.get(name, {})
            sslug = it.get("service_slug") or name
            sname, theme = self.service_info(sslug)
            key = self.pick(THEMES[theme][0], f"blogs/{name}", set(), theme in QUIET_THEMES, theme in VEG_THEMES)
            return key, False, f"{sname} in Vellore", kind, "hero"
        return None


LIB: Library | None = None


# ------------------------------------------------------------------ rewriting
def widths_for(w):
    """Standard widths below the slot, the first one above it, and one retina step
    only when it is no more than 1.5x the slot (keeps the repo size sensible)."""
    bigger = [x for x in WIDTHS if x >= w]
    ws = [x for x in WIDTHS if x < w] + bigger[:1] + [x for x in bigger[1:2] if x <= w * 1.5]
    return sorted(set(ws)) or [WIDTHS[-1]]


def slot_of_img(tag):
    s = get_attr(tag, "data-slot")
    if s:
        return s
    m = SLOT_SRC.search(get_attr(tag, "src") or "")
    if not m:
        return None
    return ("master" if m.group(1) == "master-generated" else m.group(1)) + "/" + m.group(2)


def alt_for(photo_alt, orig_alt, keep, label, page_hero, in_link):
    if (in_link or keep) and orig_alt:
        return orig_alt                       # link purpose / already-accurate text
    if page_hero and label:
        return f"{photo_alt} ({label})"
    return photo_alt


def rewrite_img(tag, depth, in_link):
    slot = slot_of_img(tag)
    if not slot:
        return tag
    res = LIB.resolve(slot)
    if not res:
        return tag
    key, keep, label, kind, part = res
    photo = LIB.photos[key]
    LIB.photo_usage[key] += 1
    try:
        w = int(get_attr(tag, "width") or 1200)
        h = int(get_attr(tag, "height") or 800)
    except ValueError:
        w, h = 1200, 800
    ws = widths_for(w)
    src_w = next((x for x in ws if x >= min(w, 1200)), ws[-1])
    srcset = ", ".join(f"{LIB.img_url(key, x, round(x * h / w), depth)} {x}w" for x in ws)
    page_hero = get_attr(tag, "fetchpriority") == "high"
    alt = alt_for(photo["alt"], get_attr(tag, "alt") or "", keep, label, page_hero, in_link)
    tag = set_attr(tag, "src", LIB.img_url(key, src_w, round(src_w * h / w), depth))
    tag = set_attr(tag, "srcset", srcset)
    tag = set_attr(tag, "sizes", "100vw" if w >= 1600 or page_hero else "(max-width: 768px) 100vw, 50vw")
    tag = set_attr(tag, "alt", alt)
    if get_attr(tag, "data-full") is not None:
        full_w = 1600
        tag = set_attr(tag, "data-full", LIB.img_url(key, full_w, round(full_w * h / w), depth))
    tag = set_attr(tag, "data-slot", slot)
    tag = set_attr(tag, "data-media", key)
    return tag


def rewrite_video(block, depth, page_slug_hint):
    open_tag = re.match(r"<video\b[^>]*>", block).group(0)
    slot = get_attr(open_tag, "data-slot")
    if not slot:
        m = VSLOT_SRC.search(block)
        if not m:
            return block
        slot = ("vmaster" if m.group(1) == "master-generated" else "vpages") + "/" + m.group(2)
    kind, _, name = slot.partition("/")
    if kind == "vmaster":
        vkey, pslot, pw, ph = MASTER_VIDEO.get(name, (DEFAULT_VIDEO, "adde795c011ff9", 1600, 900))
        LIB.video_requests.add(vkey)
        if not LIB.video_available(vkey):
            vkey = DEFAULT_VIDEO
        poster_key = MASTER[pslot][0]
    else:
        _, theme = LIB.service_info(name)
        vkey = LIB.pick_video(THEMES[theme][4], f"vpages/{name}")
        poster_key, pw, ph = LIB.videos[vkey]["poster"], 1600, 1000
    LIB.video_usage[vkey] += 1
    video = LIB.videos[vkey]
    url = LIB.video_url(vkey, depth)
    new_open = set_attr(open_tag, "poster", LIB.img_url(poster_key, 1200, round(1200 * ph / pw), depth))
    if get_attr(new_open, "data-src") is not None:
        new_open = set_attr(new_open, "data-src", url)
    if get_attr(new_open, "aria-label") is not None:
        new_open = set_attr(new_open, "aria-label", f"Video: {video['title']}")
    new_open = set_attr(new_open, "data-slot", slot)
    new_open = set_attr(new_open, "data-media", vkey)
    out = block.replace(open_tag, new_open, 1)
    out = re.sub(r"<source\b[^>]*>", f'<source src="{html.escape(url, quote=True)}" type="video/mp4">', out, count=1)
    return out


def rewrite_figure(fig):
    """Captions follow the photo inside catering/area/gallery figures."""
    inner_slot = re.search(r'data-slot="(pages|areas|master|vpages)/', fig)
    if not inner_slot:
        return fig
    kind = inner_slot.group(1)
    if kind == "master" and "gallery-item" not in fig[:80]:
        return fig
    vid = re.search(r'<video\b[^>]*data-media="([^"]+)"', fig)
    img = IMG_RE.search(fig)
    if vid:
        caption = LIB.videos[vid.group(1)]["title"]
    elif img:
        key = get_attr(img.group(0), "data-media")
        caption = get_attr(img.group(0), "alt") if kind == "master" else LIB.photos[key]["alt"]
    else:
        return fig
    if kind == "areas" and img and re.search(r"<a\b", fig):
        return fig
    esc = html.escape(caption, quote=False)
    fig = re.sub(r"(<figcaption>)(.*?)(</figcaption>)", lambda m: m.group(1) + esc + m.group(3), fig, count=1, flags=re.S)
    if kind == "master":
        fig = re.sub(r'(aria-label="Enlarge photo: )[^"]*(")',
                     lambda m: m.group(1) + html.escape(caption, quote=True) + m.group(2), fig, count=1)
    return fig


def rewrite_preload(tag, text, depth):
    """Keep <link rel=preload> in step with the hero <img> it announces."""
    slot = get_attr(tag, "data-slot")
    if not slot:
        m = SLOT_SRC.search(get_attr(tag, "href") or "")
        if not m:
            return tag
        slot = ("master" if m.group(1) == "master-generated" else m.group(1)) + "/" + m.group(2)
    img = re.search(r'<img\b[^>]*data-slot="%s"[^>]*>' % re.escape(slot), text)
    if not img:
        return tag
    itag = img.group(0)
    tag = set_attr(tag, "href", get_attr(itag, "src"))
    tag = set_attr(tag, "imagesrcset", get_attr(itag, "srcset"))
    tag = set_attr(tag, "imagesizes", get_attr(itag, "sizes"))
    return set_attr(tag, "data-slot", slot)


def first_hero_key(text):
    m = re.search(r'data-slot="((?:pages/[^"]+-hero)|(?:areas/[^"]+-hero)|(?:blogs/[^"]+))"', text)
    if not m:
        return None
    res = LIB.resolve(m.group(1))
    return res[0] if res else None


def process_page(path, write=True):
    rel = path.relative_to(ROOT).as_posix()
    depth = rel.count("/")
    text = path.read_text(encoding="utf-8")
    orig = text

    def img_sub(m):
        before = m.string[max(0, m.start() - 300): m.start()]
        in_link = bool(re.search(r"<a\b[^>]*>\s*$", before))
        return rewrite_img(m.group(0), depth, in_link)

    text = IMG_RE.sub(img_sub, text)
    text = PRELOAD_RE.sub(lambda m: rewrite_preload(m.group(0), text, depth), text)
    text = VIDEO_RE.sub(lambda m: rewrite_video(m.group(0), depth, path.stem), text)
    text = FIGURE_RE.sub(lambda m: rewrite_figure(m.group(0)), text)
    for old, new in TEXT_FIXES:
        text = text.replace(old, new)

    if "data-media=" in text:           # page now carries stock media: V1 -> V2
        text = VERSION_RE.sub(r"\g<1>V2", text, count=1)
        text = GENERATED_RE.sub(r"\g<1>V3", text, count=1)

    hero = first_hero_key(text)
    if hero:
        og = LIB.og_url(hero)
        text = META_IMG.sub(lambda m: m.group(1) + (html.escape(og, quote=True) if REPLACEABLE.search(m.group(2))
                                                     else m.group(2)) + m.group(3), text)
        text = LD_IMG.sub(lambda m: m.group(1) + (og if REPLACEABLE.search(m.group(2)) else m.group(2)) + m.group(3),
                          text)
    if text != orig:
        if write:
            path.write_text(text, encoding="utf-8")
        return True
    return False


# ------------------------------------------------------------------ credits page
def write_credits():
    tpl_path = ROOT / "privacy.html"
    if not tpl_path.exists():
        return False
    t = tpl_path.read_text(encoding="utf-8")
    title = "Photo & Video Credits | Vellore Catering World"
    desc = ("Credits and licence details for the free Pexels stock photos and videos of South Indian food, "
            "catering and weddings shown on the Vellore Catering World website.")
    url = f"{SITE}/credits.html"
    t = re.sub(r"<!-- Vellore Catering World \| privacy\.html \| Version: [^>]*-->",
               "<!-- Vellore Catering World | credits.html | Version: V1 | generated by tools/stock_media.py -->", t)
    t = re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)}</title>", t, count=1)
    for pat, val in ((r'(<meta name="description" content=")[^"]*', desc),
                     (r'(<meta property="og:description" content=")[^"]*', desc),
                     (r'(<meta name="twitter:description" content=")[^"]*', desc),
                     (r'(<meta property="og:title" content=")[^"]*', title),
                     (r'(<meta name="twitter:title" content=")[^"]*', title),
                     (r'(<link rel="canonical" href=")[^"]*', url),
                     (r'(<link rel="alternate" hreflang="en-IN" href=")[^"]*', url),
                     (r'(<meta property="og:url" content=")[^"]*', url),
                     (r'(<meta name="robots" content=")[^"]*', "noindex, follow")):
        t = re.sub(pat, lambda m, v=val: m.group(1) + html.escape(v, quote=True), t, count=1)
    t = t.replace('"name": "Privacy policy"', '"name": "Photo credits"').replace(f"{SITE}/privacy.html", url)

    used_p = [k for k in LIB.keys if LIB.photo_usage[k]]
    used_v = [k for k in sorted(LIB.videos) if LIB.video_usage[k]]
    li = []
    for k in used_p:
        p = LIB.photos[k]
        li.append(f'            <li><a href="{p["page"]}" target="_blank" rel="noopener">{html.escape(p["alt"])}</a> '
                  f'<span class="page-context">(Pexels photo {p["pexels_id"]})</span></li>')
    lv = []
    for k in used_v:
        v = LIB.videos[k]
        lv.append(f'            <li><a href="{v["page"]}" target="_blank" rel="noopener">{html.escape(v["title"])}</a> '
                  f'<span class="page-context">(Pexels video {v["pexels_id"]})</span></li>')
    main = f"""  <main id="main">

    <section style="padding-top:calc(var(--nav-h) + 6rem)">
      <div class="container">
        <nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="index.html">Home</a></li><li><span aria-current="page">Photo credits</span></li></ol></nav>
        <h1 class="gilded">Photo and video credits</h1>
        <div class="prose" style="margin-top:2rem">

          <p>The food, catering and wedding photographs and video clips on this website are representative stock media from <a href="https://www.pexels.com/" target="_blank" rel="noopener">Pexels</a>. They show the kind of South Indian food and occasions we cater for; they are not photographs of our own events, and the people shown are not our staff or customers.</p>
          <p>Pexels media is free to use under the <a href="https://www.pexels.com/license/" target="_blank" rel="noopener">Pexels licence</a>. Attribution is not required, but we thank every photographer and videographer. Each link below opens the original item and its creator's profile.</p>
          <h2>Photos ({len(used_p)})</h2>
          <ul>
{chr(10).join(li)}
          </ul>
          <h2>Videos ({len(used_v)})</h2>
          <ul>
{chr(10).join(lv) if lv else '            <li>No videos in use.</li>'}
          </ul>
          <h2>Other assets</h2>
          <p>The Vellore Catering World logo and kolam artwork are the business's own. Fonts (Rozha One, Mukta, Tiro Tamil) are used under the SIL Open Font License.</p>
          <p>Are you the creator of an item listed here and want it credited differently or removed? Call or WhatsApp <a href="tel:+919445978140">+91 94459 78140</a>.</p>

        </div>
      </div>
    </section>

  </main>"""
    t = re.sub(r"  <main id=\"main\">.*?</main>", lambda m: main, t, count=1, flags=re.S)
    old = CREDITS_PATH.read_text(encoding="utf-8") if CREDITS_PATH.exists() else ""
    if old != t:
        CREDITS_PATH.write_text(t, encoding="utf-8")
    return True


# ------------------------------------------------------------------ commands
def cmd_apply(args):
    changed = sum(1 for page in pages() if process_page(page))
    write_credits()
    if not args.quiet:
        print(f"stock_media apply: {changed} pages updated | {len(LIB.photo_usage)} photos used "
              f"({sum(LIB.photo_usage.values())} slots) | {len(LIB.video_usage)} videos used | "
              f"image URLs: {LIB.local_hits} local, {LIB.remote_hits} Pexels CDN")
        missing = sorted(k for k in LIB.video_requests if not LIB.video_available(k))
        if missing:
            print(f"  note: {len(missing)} category videos not downloaded yet ({', '.join(missing)}); "
                  f"pages use '{DEFAULT_VIDEO}' until you run: python tools/stock_media.py download")


def plan():
    """Collect every photo size and video the pages need, without writing anything."""
    for page in pages():
        process_page(page, write=False)


def cmd_check(args):
    print(f"Checking {len(LIB.photos)} photos and {len(LIB.videos)} videos on Pexels ...")
    bad = []
    for i, k in enumerate(LIB.keys, 1):
        url = LIB.remote_img(k, 64, 64)
        try:
            data = fetch(url, tries=2)
            if len(data) < 200:
                raise RuntimeError("tiny response")
            print(f"  ok  [{i:>2}] {k}")
        except Exception as exc:  # noqa: BLE001
            bad.append(k)
            print(f"  BAD [{i:>2}] {k}: {exc}")
    for k, v in sorted(LIB.videos.items()):
        if not v.get("verified_file"):
            continue
        try:
            fetch(v["verified_file"], headers={"Range": "bytes=0-1023"}, tries=2)
            print(f"  ok  video {k}")
        except Exception as exc:  # noqa: BLE001
            bad.append("video:" + k)
            print(f"  BAD video {k}: {exc}")
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("  tip: pip install pillow  (download saves WebP instead of JPEG)")
    if not shutil.which("ffmpeg"):
        print("  tip: install FFmpeg so download can shrink videos")
    if bad:
        print(f"{len(bad)} problem(s). Swap those keys in data/media-library.json (or remove them) and re-run apply.")
        sys.exit(1)
    print("All media reachable.")


def save_photo(data, key, w, h, fmt):
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    if fmt == "jpg":
        Library.local_img(key, w, h, "jpg").write_bytes(data)
        return
    try:
        from io import BytesIO
        from PIL import Image
        im = Image.open(BytesIO(data)).convert("RGB")
        im.save(Library.local_img(key, w, h, "webp"), "WEBP", quality=78, method=6)
    except ImportError:
        Library.local_img(key, w, h, "jpg").write_bytes(data)


def pick_api_file(vid_id, api_key):
    raw = fetch(f"https://api.pexels.com/videos/videos/{vid_id}", headers={"Authorization": api_key})
    files = [f for f in json.loads(raw).get("video_files", [])
             if f.get("file_type") == "video/mp4" and f.get("width") and f["width"] <= 1920]
    if not files:
        return None
    return min(files, key=lambda f: abs(f["width"] - 1280))["link"]


def download_videos(keys):
    VID_DIR.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    api_key = os.environ.get("PEXELS_API_KEY", "").strip()
    for vkey in sorted(keys):
        v = LIB.videos[vkey]
        target = VID_DIR / f"{vkey}.mp4"
        if target.exists():
            continue
        try:
            src = pick_api_file(v["pexels_id"], api_key) if api_key else v.get("verified_file")
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {vkey}: Pexels API failed ({exc})")
            src = v.get("verified_file")
        if not src:
            print(f"  - {vkey}: skipped (set PEXELS_API_KEY to fetch it)")
            continue
        tmp = VID_DIR / f"{vkey}.source.mp4"
        print(f"  video {vkey} ...")
        try:
            fetch(src, dest=tmp)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {vkey}: download failed ({exc})")
            continue
        if ffmpeg:
            cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", str(tmp), "-t", "12", "-an",
                   "-vf", "scale=w='min(1280,iw)':h=-2", "-c:v", "libx264", "-preset", "slow", "-crf", "28",
                   "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target)]
            r = subprocess.run(cmd)
            tmp.unlink(missing_ok=True)
            if r.returncode != 0:
                print(f"  ! {vkey}: ffmpeg failed")
                target.unlink(missing_ok=True)
        elif tmp.stat().st_size <= 25 * 1024 * 1024:
            tmp.rename(target)
        else:
            mb = tmp.stat().st_size / 1048576
            tmp.unlink()
            print(f"  ! {vkey}: {mb:.0f} MB is too heavy for a background clip; install FFmpeg and re-run")


def download_photos():
    """Fetch every photo size the pages currently need; returns the failure count."""
    plan()
    todo = sorted(r for r in LIB.photo_requests
                  if not Library.local_img(r[0], r[1], r[2], r[3]).exists()
                  and not (r[3] == "webp" and Library.local_img(r[0], r[1], r[2], "jpg").exists()))
    print(f"stock_media download: {len(LIB.photo_requests)} photo files needed, {len(todo)} to fetch")
    failed = 0
    for i, (key, w, h, fmt) in enumerate(todo, 1):
        url = LIB.remote_img(key, w, h)
        if "fm=" not in url:
            url += "&fm=jpg"
        try:
            save_photo(fetch(url), key, w, h, fmt)
            if i % 25 == 0 or i == len(todo):
                print(f"  photos {i}/{len(todo)}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  ! {key} {w}x{h}: {exc}")
    return failed


def cmd_download(args):
    failed = download_photos()
    if not args.skip_video:
        download_videos(LIB.video_requests | {DEFAULT_VIDEO})
        reset_library()
        failed += download_photos()      # posters for videos that just became available
    reset_library()
    cmd_apply(args)
    if failed:
        print(f"{failed} photo file(s) failed; those slots keep the Pexels CDN link. Re-run to retry.")


def cmd_review(args):
    plan()
    rows = []
    for k in LIB.keys:
        p = LIB.photos[k]
        thumb = LIB.img_url(k, 480, 360, 1)
        flag = " people" if p["people"] else ""
        rows.append(f'<figure><img src="{html.escape(thumb, quote=True)}" width="480" height="360" loading="lazy" alt="">'
                    f'<figcaption><b>{k}</b>{flag} &middot; used {LIB.photo_usage[k]}&times;<br>{html.escape(p["alt"])}<br>'
                    f'<small>{", ".join(p["tags"])}</small><br><a href="{p["page"]}" target="_blank" rel="noopener">'
                    f'Pexels {p["pexels_id"]}</a></figcaption></figure>')
    vids = "".join(
        f'<li><b>{k}</b> &middot; used {LIB.video_usage[k]}&times; &middot; {html.escape(v["title"])} &middot; '
        f'<a href="{v["page"]}" target="_blank" rel="noopener">Pexels {v["pexels_id"]}</a>'
        f'{" &middot; local" if (VID_DIR / (k + ".mp4")).exists() else (" &middot; verified CDN file" if v.get("verified_file") else " &middot; needs download")}</li>'
        for k, v in sorted(LIB.videos.items()))
    doc = f"""<!DOCTYPE html>
<!-- media-review.html | generated by tools/stock_media.py | Version: V1 -->
<html lang="en-IN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>Media review | Vellore Catering World</title>
<style>
body{{margin:0;padding:2rem;background:#0d0c0a;color:#f3ead3;font:16px/1.5 system-ui,sans-serif}}
h1{{font-weight:600;margin:0 0 .5rem}} p{{max-width:70ch;color:#cfc4a8}} a{{color:#e2bd62}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:1rem;margin:1.5rem 0}}
figure{{margin:0;background:#1a1814;border:1px solid #3a3326;border-radius:8px;overflow:hidden}}
img{{display:block;width:100%;height:auto;aspect-ratio:4/3;object-fit:cover;background:#26221b}}
figcaption{{padding:.6rem .75rem;font-size:14px}} small{{color:#a99d80}}
</style></head><body>
<h1>Media review</h1>
<p>Every photo and video in <code>data/media-library.json</code>, with how many page slots use it. Flag anything that does not look right for a South Indian caterer, remove or replace its entry in the JSON file, then run <code>python tools/stock_media.py apply</code>.</p>
<div class="grid">{''.join(rows)}</div>
<h2>Videos</h2><ul>{vids}</ul>
</body></html>
"""
    REVIEW_PATH.write_text(doc, encoding="utf-8")
    print(f"stock_media review: wrote {REVIEW_PATH.relative_to(ROOT)} ({len(rows)} photos)")


def cmd_prune(args):
    referenced = set()
    pat = re.compile(r"assets/(?:img|video)/(?:pages|areas|blogs|master-generated)/[^\"'()\s>]+")
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in {".html", ".css", ".js", ".json", ".xml", ".webmanifest"} \
                and ".git" not in p.parts and p.name != "media-library.json":
            for m in pat.findall(p.read_text(encoding="utf-8", errors="ignore")):
                referenced.add(Path(m.split("?")[0]).name)
    victims = [f for d in GENERATED_DIRS if d.exists() for f in d.iterdir()
               if f.is_file() and f.name not in referenced and f.suffix in {".svg", ".webm", ".png"}]
    size = sum(f.stat().st_size for f in victims) / 1048576
    print(f"stock_media prune: {len(victims)} unused placeholder files ({size:.1f} MB)")
    if args.yes:
        for f in victims:
            f.unlink()
        for d in GENERATED_DIRS:
            if d.exists() and not any(d.iterdir()):
                d.rmdir()
        print("  deleted.")
    elif victims:
        print("  run again with --yes to delete them")


def reset_library():
    global LIB
    LIB = Library()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["apply", "check", "download", "review", "prune"])
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--skip-video", action="store_true")
    ap.add_argument("--yes", action="store_true", help="prune: actually delete")
    args = ap.parse_args()
    reset_library()
    {"apply": cmd_apply, "check": cmd_check, "download": cmd_download,
     "review": cmd_review, "prune": cmd_prune}[args.command](args)


if __name__ == "__main__":
    main()
