from bs4 import BeautifulSoup
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
PAGES={
'services/school-college-sports-day-catering-in-vellore.html':[
('Field-side hydration and heat planning','Sports-day catering follows the pace of the ground, not a classroom timetable. Relay heats, track events and team games can create sudden demand for water, buttermilk, fruit and light snacks. Hydration points should sit close enough for students and officials to reach quickly while remaining clear of running lanes, sports equipment and emergency access.'),
('Separate athlete, official and spectator service','Participants, coaches, referees, teachers and parents rarely need food at the same moment. Team-wise meal tokens or house-wise release can keep athletes moving efficiently, while officials receive meals around match schedules and spectators use a separate refreshment counter. This prevents one queue from blocking the pavilion or delaying the next event.'),
('Outdoor food protection','Sun, dust and wind change the way a sports-day menu should be held and replenished. Covered serving tables, shaded beverage stations, smaller hot-food batches and protected waste points are more useful than elaborate indoor presentation. Vehicle movement should also be restricted once students begin using the field-side circulation routes.'),
('Medal ceremony and bus departure','The final meal window has to allow for medal presentations, team photographs, school announcements and transport departure. A reserve batch for late-finishing teams avoids rushed eating, and clearly marked collection points help students return to their houses or buses without crossing the main service queue.'),
('Recovery-friendly menu choices','Very heavy food immediately before physical activity can be uncomfortable. A practical sports-day menu can use familiar tiffin, rice meals, fruit, curd, buttermilk and controlled sweet portions, with the larger meal scheduled after the main competition block where possible.')],
'services/school-annual-day-catering-in-vellore.html':[
('Rehearsal and backstage meals','Annual-day catering revolves around rehearsal calls, costume changes and stage timing. Students performing early may need a compact snack before their programme, while teachers, technicians and volunteers often eat at different times. Food near the green room should be easy to handle without affecting costumes, makeup, props or stage access.'),
('Auditorium interval rush','Parents and invited guests usually create a concentrated refreshment rush during the interval. Tea, coffee, savouries and water can be staged near the foyer with a clear entry and exit path, while the backstage corridor remains reserved for performers and organisers. This is different from continuous canteen-style service during a normal school day.'),
('Chief guest and faculty hospitality','Management members, faculty, award recipients and a chief guest may require a smaller hospitality arrangement linked to speeches and prize distribution. Reserved seating or a separate refreshment table can avoid sending formal guests through the main student queue and keeps the programme moving on time.'),
('Dinner after the final performance','The largest crowd movement may happen only after the vote of thanks and group photographs. The catering team should be ready for a sudden audience release from the auditorium, with enough serving points to prevent a bottleneck. Late-performing students and backstage crew should have protected portions even if the main dinner has started.'),
('Programme-aware service timing','Sound checks, dance blocks, drama performances and prize sections create fixed moments when service should pause or accelerate. The food plan therefore needs the final running order, not only the expected headcount, before dispatch and staffing are confirmed.')],
'services/school-catering-in-vellore.html':[
('Class-wise meal release','Regular school catering works best when food service follows the bell schedule and class groups are released in a controlled sequence. Primary students may need earlier, smaller portions, while older students can use a later window. Class-wise movement reduces crowding and helps teachers supervise the dining area.'),
('Daily attendance and portion planning','Unlike a one-day celebration, school catering may need to respond to attendance changes throughout the week. The kitchen can use expected strength, absentee patterns and staff meal counts to prepare sensible buffers without routinely overproducing food.'),
('Teacher and staff meal windows','Teachers, office staff and support teams often have shorter breaks than students. A separate staff pickup point or reserved service window can help them eat without joining the main student queue, particularly on examination or meeting days.'),
('Age-appropriate everyday menus','A school menu should favour familiar dishes, manageable spice levels and practical serving portions. Breakfast, lunch and snack combinations can rotate across the week so students receive variety without making service unnecessarily complicated.'),
('Campus access and routine logistics','Daily catering requires predictable gate entry, vessel movement, cleaning and waste removal. These routine controls are different from sports-day or annual-day catering because the goal is repeatability across ordinary teaching days rather than a single programme schedule.')],
'services/college-catering-in-vellore.html':[
('Lecture and department schedules','College catering has to work around lectures, laboratory sessions and department timetables. Student groups may be released at different times, so lunch service can be staggered rather than designed around one large event break.'),
('Hostel and day-scholar needs','Residential students, day scholars and faculty may have different meal patterns. Hostel-related catering can require breakfast or dinner planning, while day events may focus on lunch, tea and seminar refreshments. The service brief should identify which population is actually being fed.'),
('Academic events and seminars','Department meetings, guest lectures, workshops and placement programmes often need compact refreshment service near seminar halls. These bookings are usually smaller and more time-sensitive than a college festival, with emphasis on punctual delivery and quiet setup.'),
('Faculty and administrative hospitality','Faculty meetings, accreditation visits and management sessions may call for a separate table or boxed service with clear timing. That arrangement should not interfere with the larger student meal line.'),
('Routine campus access','Vehicle entry, security permission, kitchen access and vessel return are recurring operational details in a college campus. A regular catering plan benefits from a consistent loading point and named campus contact.')],
'services/college-fest-catering-in-vellore.html':[
('Stage programmes and crowd surges','A college fest can shift from a quiet afternoon to a very busy evening within minutes. Music performances, competitions and headline events create sudden crowd surges, so snack counters and beverage points need more capacity around the stage schedule than during an ordinary college meal service.'),
('Student club and sponsor zones','Festivals may include club stalls, sponsor areas, exhibition booths and multiple activity zones. Catering counters should be placed so food queues do not block registration desks, merchandise areas or performance entrances.'),
('Artist, crew and volunteer meals','Performers, sound technicians, security teams and student volunteers often work while the audience is eating. Protected crew meals and a separate pickup window help them stay on duty without depending on the public queue.'),
('Late-evening service','College fests frequently continue into the evening, which changes lighting, hot-food holding and cleanup requirements. Dinner or late snacks may need a fresh production batch rather than simply extending the afternoon buffet.'),
('Token and multi-counter control','When several counters operate at once, coupon or token rules should be easy to understand. Separate queues for beverages, snacks and main meals can improve throughput during peak programme breaks.')],
'services/birthday-party-catering-in-vellore.html':[
('Cake cutting and party games','General birthday-party catering has to move around the celebration itself. Snacks may be served during games, the main meal may pause for cake cutting, and desserts can follow photographs or announcements. The menu should therefore support a flexible party timeline rather than one fixed service moment.'),
('Children and adult guests together','Many birthday parties include school-age children, parents, grandparents and family friends. A useful menu can combine easy-to-eat child portions with fuller options for adults, instead of assuming every guest wants the same plate size or spice level.'),
('Activity and food-zone separation','Magic shows, games, balloon decoration, return gifts and photo areas can compete for floor space. Food counters should be positioned so children are not carrying plates through active play zones and the cake table remains accessible for photographs.'),
('Party-style snacks and desserts','Finger foods, mini tiffin, chaat, juices, ice cream and themed sweets can be timed in smaller waves. This keeps the party lively and avoids putting the entire menu on display before guests are ready to eat.'),
('End-of-party handoff','After cake, dinner and return gifts, the service team can help the host close the food area cleanly while late family members still have access to a protected portion.')],
'services/first-birthday-catering-in-vellore.html':[
('A milestone centred on the child','A first birthday is usually a family milestone built around a one-year-old child rather than a large activity programme. Grandparents, close relatives and photographs often shape the schedule, so the meal can be calmer and more family-oriented than a typical school-age birthday party.'),
('Nap time and early evening timing','Toddlers may become tired before a late dinner. Families often benefit from an earlier cake-cutting and meal window that respects the child\'s nap and bedtime pattern, especially when grandparents and other young children are attending.'),
('High chairs and toddler-safe space','The dining layout should keep a clear, low-traffic area for the birthday child and other toddlers. High-chair placement, spill cleanup and hot-food distance matter more here than game-zone queue management.'),
('Soft and familiar family options','The main catering menu is for the guests, but families may also request a few mild, soft-texture items suitable for very young children. These should be discussed separately from any dietary or medical advice and prepared only as agreed with the parents.'),
('Cake-smash and photo cleanup','First-birthday photography may include a cake-smash or extended family photo session. The service plan can allow time for cleanup and clothing changes before the main meal begins, preventing the dining queue from starting while the family is still occupied.')]
}

for rel,items in PAGES.items():
    p=ROOT/rel
    s=BeautifulSoup(p.read_text(encoding='utf-8',errors='ignore'),'html.parser')
    m=s.find('main')
    old=m.find(id='close-pair-unique-copy')
    if old: old.decompose()
    sec=s.new_tag('section',id='close-pair-unique-copy'); sec['class']=['close-pair-unique-copy']
    box=s.new_tag('div'); box['class']=['container']; sec.append(box)
    k=s.new_tag('p'); k['class']=['section-kicker']; k.string='Event-specific planning'; box.append(k)
    h=s.new_tag('h2'); h.string='Planning details unique to this service'; box.append(h)
    for title,body in items:
        art=s.new_tag('article'); hh=s.new_tag('h3'); hh.string=title; pp=s.new_tag('p'); pp.string=body; art.append(hh); art.append(pp); box.append(art)
    m.append(sec)
    p.write_text(str(s),encoding='utf-8')
print('updated',len(PAGES),'close-pair pages')
