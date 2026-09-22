#!/usr/bin/env python3
"""Audit visible <main> text for phrase-level similarity across all public HTML pages.

Metric: TF-IDF cosine similarity over normalized word 2-grams and 3-grams using a
fixed hashing space. Difference percentage = (1 - nearest-page similarity) * 100.
Pass condition: difference >= 50% (nearest similarity <= 0.50).
Shared navigation, footer and form controls are excluded so the score measures
page-specific editorial content rather than site chrome.
"""
from pathlib import Path
from lxml import html
from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
from sklearn.neighbors import NearestNeighbors
import csv, html as htmllib, json, numpy as np

ROOT=Path(__file__).resolve().parent.parent
OUTCSV=ROOT/'content-uniqueness-audit.csv'
OUTHTML=ROOT/'content-uniqueness-audit.html'
OUTJSON=ROOT/'content-uniqueness-audit-summary.json'

files=[]; texts=[]
for f in ROOT.rglob('*.html'):
    rel=f.relative_to(ROOT)
    if rel.parts[0] in {'partials','templates','tools'} or f.name in {'media-replacement-inventory.html','content-uniqueness-audit.html'}:
        continue
    try:
        doc=html.fromstring(f.read_text(encoding='utf-8',errors='ignore'))
        mains=doc.xpath('//main')
        if not mains: continue
        main=mains[0]
        for node in main.xpath('.//script|.//style|.//form|.//nav'):
            node.drop_tree()
        text=' '.join(main.text_content().split())
        if text:
            files.append(rel.as_posix()); texts.append(text)
    except Exception:
        continue

hv=HashingVectorizer(n_features=2**17,alternate_sign=False,ngram_range=(2,3),norm=None,stop_words='english')
H=hv.transform(texts)
X=TfidfTransformer(sublinear_tf=True).fit_transform(H)
dists,inds=NearestNeighbors(n_neighbors=2,metric='cosine',algorithm='brute',n_jobs=-1).fit(X).kneighbors(X)
nearest_similarity=1-dists[:,1]
nearest_index=inds[:,1]
rows=[]
for i,f in enumerate(files):
    sim=float(nearest_similarity[i]); diff=(1-sim)*100
    rows.append({
        'page':f,
        'nearest_page':files[int(nearest_index[i])],
        'similarity_percent':round(sim*100,2),
        'difference_percent':round(diff,2),
        'status':'PASS' if diff>=50 else 'FAIL',
        'main_text_words':len(texts[i].split())
    })
rows.sort(key=lambda r:r['difference_percent'])
with OUTCSV.open('w',newline='',encoding='utf-8') as fp:
    w=csv.DictWriter(fp,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
summary={
    'metric':'TF-IDF cosine similarity over visible main-content word 2-grams and 3-grams',
    'shared_elements_excluded':['navigation','forms','scripts','styles','footer (outside main)'],
    'pass_rule':'difference_percent >= 50.00',
    'pages_audited':len(rows),
    'pages_passed':sum(r['status']=='PASS' for r in rows),
    'pages_failed':sum(r['status']=='FAIL' for r in rows),
    'minimum_difference_percent':round(min(r['difference_percent'] for r in rows),2),
    'maximum_similarity_percent':round(max(r['similarity_percent'] for r in rows),2),
    'median_difference_percent':round(float(np.median([r['difference_percent'] for r in rows])),2),
}
OUTJSON.write_text(json.dumps(summary,indent=2),encoding='utf-8')
trs=''.join(f"<tr class='{r['status'].lower()}'><td>{htmllib.escape(r['page'])}</td><td>{htmllib.escape(r['nearest_page'])}</td><td>{r['similarity_percent']:.2f}%</td><td><strong>{r['difference_percent']:.2f}%</strong></td><td>{r['main_text_words']}</td><td>{r['status']}</td></tr>" for r in rows)
OUTHTML.write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Vellore Catering World - Content Uniqueness Audit</title><style>body{{font:15px/1.5 system-ui,sans-serif;margin:0;background:#f6f4ef;color:#222}}main{{max-width:1500px;margin:auto;padding:32px}}.summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:22px 0}}.card{{background:#fff;padding:18px;border-radius:10px;border:1px solid #ddd}}table{{width:100%;border-collapse:collapse;background:#fff;font-size:13px}}th,td{{padding:9px;border:1px solid #ddd;text-align:left;vertical-align:top}}th{{position:sticky;top:0;background:#222;color:#fff}}.pass td:last-child{{color:#08752f;font-weight:700}}.fail{{background:#ffe5e5}}code{{background:#eee;padding:2px 5px}}</style></head><body><main><h1>Vellore Catering World — Text Content Uniqueness Audit</h1><p>Tracking metric: TF-IDF cosine similarity of normalized visible <code>&lt;main&gt;</code> text using word 2-grams and 3-grams. Navigation, forms, scripts, styles and footer chrome are excluded. A page passes when its closest other page is no more than 50% similar, meaning at least 50% difference by this phrase-level metric.</p><div class="summary"><div class="card"><b>Pages audited</b><br>{summary['pages_audited']}</div><div class="card"><b>Passed</b><br>{summary['pages_passed']}</div><div class="card"><b>Failed</b><br>{summary['pages_failed']}</div><div class="card"><b>Minimum difference</b><br>{summary['minimum_difference_percent']:.2f}%</div><div class="card"><b>Median difference</b><br>{summary['median_difference_percent']:.2f}%</div><div class="card"><b>Maximum similarity</b><br>{summary['maximum_similarity_percent']:.2f}%</div></div><table><thead><tr><th>Page</th><th>Closest page</th><th>Similarity</th><th>Difference</th><th>Main words</th><th>Status</th></tr></thead><tbody>{trs}</tbody></table></main></body></html>''',encoding='utf-8')
print(json.dumps(summary,indent=2))
