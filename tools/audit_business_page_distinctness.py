#!/usr/bin/env python3
from pathlib import Path
from lxml import html
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re, json
ROOT=Path(__file__).resolve().parent.parent
PAGES=[ROOT/'services'/'wedding-catering-in-vellore.html',ROOT/'services'/'reception-catering-in-vellore.html']
def extract(path):
    doc=html.fromstring(path.read_text(encoding='utf-8',errors='ignore'))
    main=doc.xpath('//main')[0]
    for n in main.xpath('.//script|.//style|.//form|.//nav'): n.drop_tree()
    text=' '.join(main.text_content().split())
    heads=[' '.join(h.text_content().split()) for h in main.xpath('.//h2|.//h3')]
    return text,heads
def normhead(h):
    h=h.lower()
    h=re.sub(r'\b(wedding|reception) catering(?: in vellore)?\b','',h)
    h=re.sub(r'[^a-z0-9 ]+',' ',h)
    return ' '.join(h.split())
texts=[]; heads=[]
for p in PAGES:
    t,h=extract(p); texts.append(t); heads.append({normhead(x) for x in h if normhead(x)})
X=TfidfVectorizer(ngram_range=(2,3),stop_words='english',sublinear_tf=True).fit_transform(texts)
text_sim=float(cosine_similarity(X[0],X[1])[0,0])
inter=heads[0]&heads[1]; union=heads[0]|heads[1]
heading_overlap=len(inter)/len(union) if union else 0
result={
  'pages':[str(p.relative_to(ROOT)) for p in PAGES],
  'text_similarity_percent':round(text_sim*100,2),
  'text_difference_percent':round((1-text_sim)*100,2),
  'normalized_heading_overlap_percent':round(heading_overlap*100,2),
  'normalized_heading_difference_percent':round((1-heading_overlap)*100,2),
  'original_requirement_pass': text_sim <= 0.50,
  'business_critical_strict_pass': text_sim <= 0.35 and heading_overlap <= 0.20,
  'strict_rule':'text similarity <=35% AND normalized heading overlap <=20%'
}
print(json.dumps(result,indent=2))
(ROOT/'business-page-distinctness-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
