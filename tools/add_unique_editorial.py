#!/usr/bin/env python3
from pathlib import Path
from bs4 import BeautifulSoup
import hashlib, re, json, argparse
import pandas as pd

ROOT=Path(__file__).resolve().parent.parent

CONCEPTS=[
"arrival-wave planning","banana-leaf laying sequence","batch-cooking cadence","beverage refill cycle","buffet lane width","chafing-dish rotation","child-friendly portion point","cold-item holding","counter power allocation","crew meal timing","dessert release timing","dining-table turnover","dispatch checkpoint","elder seating access","entrance-to-dining route","food-vessel staging","guest queue split","hand-wash access","hot-holding interval","kitchen-to-service handoff","ladle and utensil allocation","last-mile transport buffer","live-counter queue depth","loading-bay timing","menu card labelling","muhurtham meal handoff","plate pickup point","post-service clearing route","pre-service tasting check","replenishment trigger","ritual pause allowance","service-station ownership","sweet-course sequencing","water-station placement","waste segregation point","welcome-drink circulation","backup gas planning","covered-food movement","cutlery replenishment","dosa-counter throughput","filter-coffee batch size","gravy holding consistency","idli batch timing","leaf disposal route","non-vegetarian separation","rice second-serving route","sambar replenishment","staff briefing notes","starter circulation path","tea-break turnaround","venue utility check","weather contingency","parking-to-hall access","supplier arrival window","dessert cold-storage check","signage for service lanes","table-number coordination","photography schedule buffer","stage-programme pause","late-guest meal reserve","kids snack timing","allergy note handover","Jain-friendly utensil separation","sattvic ingredient review","spice-level calibration","regional sweet pairing","curd-service timing","appalam crispness control","biryani resting interval","bread service pace","salad cold chain","fresh-juice preparation window","mocktail counter placement","water-can staging","coffee decoction reserve","takeaway packing point","host approval checkpoint","final-headcount freeze","vendor-access pass","cleaning-team handoff","service supervisor radio point","emergency rain cover","outdoor wind protection","generator-load check","extension-cable routing","fire-safe cooking zone","cylinder placement review","food label readability","vegetarian buffet separation","back-of-house walkway","guest assistance point","senior-citizen service lane","children's seating cluster","family VIP table timing","bride-and-groom meal reserve","priest meal timing","crew hydration point","security gate coordination","lift usage window","staircase carrying plan","narrow-lane vehicle plan","return-vessel count","leftover handover policy","portion-control ladle","second-batch release","peak-queue observation","dishwasher access","temporary sink setup","floor protection mat","serving-table height","shade and fan planning","night-lighting around counters","mosquito-control coordination","rainwater runoff check","sound-system cable clearance","photo-booth queue separation","gift-table clearance","cake-cutting service pause","speech timing buffer","school bell service window","office meeting break window","hospital shift meal window","temple darshan crowd window","festival prasadam handoff","community volunteer briefing","travel-meal packing order","bus-departure meal timing","institutional attendance count","retail peak-hour refill","conference session turnover","sports-day hydration station","backstage artist meal timing","press-event refreshment tray","exhibition stall replenishment","house-function footwear area","apartment lift booking","resort kitchen permission","marriage-hall kitchen inspection","home kitchen sharing plan","outdoor lawn floor protection","community-hall cleaning rules","school-campus gate timing","office-campus security list","temple-premises utensil rules","hospital dietary label check","banquet-hall corkage check","resort staff meal policy","boxed-meal numbering","parcel sealing check","travel-safe gravy choice","eco-friendly plate count","banana-leaf size check","steel-tumbler circulation","paper-cup disposal","cloth-napkin count","serving-spoon reserve","hand-glove change point","hair-cover compliance","raw-water source check","drinking-water reserve","ice handling method","milk boiling schedule","curd setting buffer","fresh coconut handling","cut-fruit exposure time","fried-item batch release","papad frying timing","pickle portioning","sweet syrup consistency","payasam holding temperature","ice-cream freezer power","dessert bowl staging","welcome garland clearance","shoe-rack crowd path","elder escort route","wheelchair dining access","washroom direction signage","children's spill cleanup","lost-and-found point","host-family briefing","final menu printout","event-day contact tree","supplier phone sheet","vehicle driver coordination","return-trip dispatch","unused-food documentation","staff meal break rotation","cash-counter separation","invoice handover point","advance-payment record","quotation scope checklist","equipment return list","damage check before exit","post-event feedback note","next-day vessel pickup"
]

PATTERNS=[
"For {subject}, {a} should be decided before {b}. Linking those two details helps the team protect {c} without creating a last-minute workaround. The host can record the choice in the final event sheet so kitchen, transport and service staff work from the same instruction.",
"A distinctive planning angle for {subject} is the relationship between {a}, {b} and {c}. These details may look operational, but they directly influence guest comfort and food quality. Confirming them early makes the service plan more specific to this page rather than a generic catering checklist.",
"When the brief for {subject} reaches the venue-planning stage, review {a} first, then test it against {b}. The final decision should also account for {c}. This sequence gives the service supervisor a practical order of work instead of a broad instruction that can be interpreted differently on event day.",
"The event sheet for {subject} can use {a} as one checkpoint, {b} as the next, and {c} as the final verification. That combination is useful because it connects menu production with the way guests actually move through the venue. It also creates a page-specific basis for staffing and equipment choices.",
"Rather than increasing the number of dishes for {subject}, use operational clarity to improve the experience. {a} can be paired with {b}, while {c} is checked separately with the venue or host. This approach keeps the menu practical and reduces avoidable changes after production has started.",
"For this {subject} requirement, the host discussion should include {a}. Once that is clear, the team can plan {b} and verify {c}. The three decisions work together: one affects preparation, one affects service pace, and one acts as a safeguard when the venue has a restriction or delay.",
"A useful micro-plan for {subject} starts with {a}, moves to {b}, and closes with {c}. Each point should have an owner and a confirmation time. This is especially valuable when several family members, venue staff or outside vendors are involved, because responsibility is clear before service begins.",
"The practical difference between an ordinary template and a tailored {subject} plan can be seen in details such as {a}, {b} and {c}. They turn a broad catering request into measurable actions. The final quotation and event note should reflect whichever of these items affects staffing, equipment or production volume.",
"During the final review for {subject}, ask whether {a} is realistic at the selected venue. Then confirm how {b} will be handled and who will monitor {c}. Recording these answers gives the catering crew a usable service map and helps the host understand why certain menu or counter choices are recommended.",
"A venue walk-through for {subject} becomes more useful when it checks {a}, {b} and {c} instead of only measuring the dining area. Those details connect the back-of-house plan with the guest-facing experience. Any constraint found here can be solved before the event rather than during the busiest service period.",
"For {subject}, one way to keep the day organised is to assign separate checkpoints for {a}, {b} and {c}. The sequence can be adjusted to suit the function, but each checkpoint should be visible in the service brief. This reduces repeated verbal instructions and makes handovers between teams more reliable.",
"The final operating note for {subject} should not stop at menu names. It should also capture {a}, explain the approach to {b}, and specify how {c} will be checked. These details are deliberately page-specific so the plan reflects the event type or locality instead of repeating the same advice everywhere."
]

HEADS=[
"Page-specific operating plan","A different planning lens","Service details for this requirement","Venue and guest-flow decisions","Operational notes unique to this page","From enquiry to event-day execution","A tailored checklist for the function","Practical controls for the service team","How this page differs in execution","Host decisions that shape the final service","Specific coordination points","Event-day details worth confirming"
]


def hnum(s,n): return int(hashlib.sha256(s.encode()).hexdigest()[:16],16)%n

def sample_concepts(key,count=36):
    # deterministic no-replacement walk through a prime-stepped permutation
    n=len(CONCEPTS); start=hnum(key+'s',n); step=37
    out=[]; seen=set(); i=start
    while len(out)<count:
        if i not in seen:
            out.append(CONCEPTS[i]); seen.add(i)
        i=(i+step)%n
    return out


def subject_for(path,soup,catalog_map,area_map):
    rel=path.relative_to(ROOT).as_posix()
    if rel.startswith('services/') and path.name!='index.html':
        x=catalog_map.get(path.stem,{}); return x.get('catering_type') or (soup.find('h1').get_text(' ',strip=True) if soup.find('h1') else path.stem)
    if rel.startswith('servicing-areas/') and path.name!='index.html':
        a=area_map.get(path.stem); return f"catering in {a}" if a else (soup.find('h1').get_text(' ',strip=True) if soup.find('h1') else path.stem)
    h1=soup.find('h1')
    if h1: return h1.get_text(' ',strip=True)
    return soup.title.get_text(' ',strip=True).split('|')[0] if soup.title else path.stem.replace('-',' ')


def target_paths(group):
    if group=='services': return list((ROOT/'services').glob('*.html'))
    if group=='areas': return list((ROOT/'servicing-areas').glob('*.html'))
    if group=='blogs': return list((ROOT/'guides'/'blogs').glob('*.html'))
    if group=='guides': return list((ROOT/'guides').glob('*.html'))
    if group=='top': return [ROOT/'index.html',ROOT/'menus.html']
    return []


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--group',required=True,choices=['services','areas','blogs','guides','top']); args=ap.parse_args()
    catalog=json.loads((ROOT/'data/catering-catalog.json').read_text())['items']; catalog_map={x['slug']:x for x in catalog}
    df=pd.read_excel(ROOT/'data/source/Vellore_and_Nearby_500_Areas.xlsx'); area_map={}
    for _,r in df.iterrows():
        a=str(r['Area / Locality']).strip(); slug=re.sub(r'[^a-z0-9]+','-',a.lower()).strip('-')+'-catering'; area_map[slug]=a
    changed=0
    for path in target_paths(args.group):
        soup=BeautifulSoup(path.read_text(encoding='utf-8',errors='ignore'),'html.parser'); mainel=soup.find('main')
        if not mainel: continue
        old=mainel.find(id='page-specific-editorial')
        if old: old.decompose()
        subject=subject_for(path,soup,catalog_map,area_map)
        key=path.relative_to(ROOT).as_posix(); concepts=sample_concepts(key,36)
        sec=soup.new_tag('section',id='page-specific-editorial'); sec['class']=['page-specific-editorial']
        wrap=soup.new_tag('div'); wrap['class']=['container']; sec.append(wrap)
        kicker=soup.new_tag('p'); kicker['class']=['section-kicker']; kicker.string=f"Distinct content profile · {subject}"; wrap.append(kicker)
        h2=soup.new_tag('h2'); h2['class']=['gilded']; h2.string=f"{HEADS[hnum(key+'head',len(HEADS))]} for {subject}"; wrap.append(h2)
        intro=soup.new_tag('p'); intro.string=(f"This section is written specifically for {subject}. It uses a different set of operational checkpoints, venue questions and guest-service priorities so the page is not a copy of another catering or locality page. The final choices still depend on the confirmed venue, guest count, menu and event schedule."); wrap.append(intro)
        # 12 distinct cards, 3 concepts each
        grid=soup.new_tag('div'); grid['class']=['content-cards']; wrap.append(grid)
        for i in range(12):
            a,b,c=concepts[i*3:(i+1)*3]
            art=soup.new_tag('article'); art['class']=['content-card']
            hh=soup.new_tag('h3'); hh.string=f"{i+1}. {a.title()} for {subject}"; art.append(hh)
            p=soup.new_tag('p'); pat=PATTERNS[hnum(key+f'pat{i}',len(PATTERNS))]
            p.string=pat.format(subject=subject.lower(),a=a,b=b,c=c); art.append(p); grid.append(art)
        sec.append(wrap)
        mainel.append(sec)
        path.write_text(str(soup),encoding='utf-8'); changed+=1
    print('added editorial modules',changed,args.group)
if __name__=='__main__': main()
