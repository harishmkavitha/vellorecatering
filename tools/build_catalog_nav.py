#!/usr/bin/env python3
import html, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DATA=json.loads((ROOT/'data/catering-catalog.json').read_text(encoding='utf-8'))['items']
E=html.escape

def sid(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
order=[]; groups={}
for item in DATA:
    for cat in item['categories']:
        if cat not in groups: groups[cat]=[]; order.append(cat)
        groups[cat].append(item)
blocks=[]
for cat in order:
    cid='mega-'+sid(cat)
    links=''.join(f'<li><a href="services/{p["slug"]}.html">{E(p["catering_type"])}</a></li>' for p in groups[cat])
    blocks.append(f'''<section class="mega-group" data-mega-group>
  <div class="mega-group__head"><h3>{E(cat)}</h3><button class="mega-group__toggle" type="button" aria-expanded="false" aria-controls="{cid}"><span class="visually-hidden">Show {E(cat)} pages</span><svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 9l7 7 7-7" fill="none" stroke="currentColor" stroke-width="2"/></svg></button></div>
  <ul id="{cid}" class="mega-group__links">{links}</ul>
</section>''')
nav=f'''<!-- partial: nav.html | Version: V2 | generated from catering-catalog.json -->
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header" data-section="1" data-section-name="Header / Navigation">
  <nav class="site-nav" aria-label="Main">
    <div class="site-nav__bar">
      <a class="site-nav__logo" href="index.html"><img src="assets/img/logo.svg" width="226" height="72" alt="Vellore Catering World home"></a>
      <ul class="site-nav__list" id="nav-list">
        <li><a href="index.html">Home</a></li>
        <li><a href="about.html">About us</a></li>
        <li class="has-sub has-mega">
          <a href="services/index.html">Catering</a>
          <button class="sub-toggle" type="button" aria-expanded="false" aria-controls="sub-catering"><span class="visually-hidden">Show catering categories</span><svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 9l7 7 7-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
          <div class="sub sub--mega" id="sub-catering">
            <div class="mega-menu__top"><div><strong>236 catering services</strong><span>Grouped by the 16 categories in your source sheet</span></div><a class="text-link" href="services/other-caterings-in-vellore.html">View all caterings</a></div>
            <div class="mega-menu__search"><label class="visually-hidden" for="nav-catering-search">Search catering pages</label><input id="nav-catering-search" type="search" placeholder="Search catering type…" data-mega-search></div>
            <div class="mega-menu__grid">{''.join(blocks)}</div>
          </div>
        </li>
        <li class="has-sub">
          <a href="servicing-areas/index.html">Services</a>
          <button class="sub-toggle" type="button" aria-expanded="false" aria-controls="sub-services" aria-label="Open Services submenu"><span></span></button>
          <ul class="sub" id="sub-services">
            <li><a href="servicing-areas/index.html">Servicing Areas</a></li>
          </ul>
        </li>
        <li><a href="menus.html">Menus</a></li>
        <li class="has-sub">
          <a href="guides/index.html">Guides</a>
          <button class="sub-toggle" type="button" aria-expanded="false" aria-controls="sub-guides" aria-label="Open Guides submenu"><span></span></button>
          <ul class="sub" id="sub-guides">
            <li><a href="guides/blogs/index.html">Blogs</a></li>
          </ul>
        </li>
        <li><a href="gallery.html">Gallery</a></li>
        <li><a href="contact.html">Contact</a></li>
        <li class="nav-cta-item"><a class="btn btn--gold btn--sm" href="tel:+919445978140">Call 94459 78140</a></li>
      </ul>
      <button class="site-nav__toggle" type="button" aria-expanded="false" aria-controls="nav-list"><span class="visually-hidden">Open menu</span><span class="bar"></span><span class="bar"></span><span class="bar"></span></button>
    </div>
  </nav>
</header>'''
(ROOT/'partials/nav.html').write_text(nav,encoding='utf-8')
print('build_catalog_nav: wrote 16 groups and 236 unique catering links')
