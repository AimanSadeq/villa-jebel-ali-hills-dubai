# Design decisions: Villa 5130272, Jebel Ali Hills

Every design decision and its reason. Newest first.

Columns: date, decision, reason, approved by Aiman.

---

## 2026-10-02, central hall ground floor

### D-037 Pool moved north onto the living room's deck

**Decision.** The pool keeps its Phase 1 orientation and east west position
(u 18.50 to 22.50, 10 m along the plot's long axis) and moves north so that
its deck starts at the living room's north wall: pool v 19.45 to 29.45, deck
to v 30.45, 2 m each side. The deck stays inside the buildable envelope, so
the pool setback question (OI-12) no longer arises for this position.

**Reason.** Follows from D-036: the tall living block now stands where the
Phase 1 pool was, and the owner wants the living room opening onto the pool.
The afternoon shade on the deck must be re-checked against the real footprint
and the 10.20 m height, as promised at the start of Phase 3. An east west pool
across the living room's frontage was considered and can be offered if the
shade check favours it.

**Shade check, same day (VJH-RPT-008, src/analysis/shade_check.py).** On the
planned footprint at the D-030 heights, the deck in this position is in the
villa's shadow for 92.0 % of the summer afternoon hours (15:00 to 18:00, June
and August), against 88.0 % estimated for option C's blocks in Phase 1, and
gets 58 % winter midday sun. The east west alternative across the living
room's frontage scores 93.8 % and 56 %: no better in any way that matters, so
the Phase 1 orientation is kept. At 15:00 in June about a third of the deck is
still in sun; a pergola at the BBQ end (CLAUDE.md section 4) would cover it.

**Approved by Aiman: no,** Claude's consequence of D-036, for review.

### D-036 Central hall ground floor

**Decision.** The ground floor is replanned as a central hall villa. From the
front door on the road: a big hall across the full width of the wing (11.40 x
3.50 m, 39.9 m2, against a 19 m2 program target), the stair open to it; the
majlis north of the hall (on the left when entering) with its powder room at
the road end, both opening off the hall; the dining south of the hall (on the
right) reached along a 1.80 m entrance gallery that it opens onto, with the
pantry at its south end; the double height living room straight ahead, a 7.50
x 6.00 m block 9.00 m tall standing in the courtyard with nothing above it,
open to the hall through a 3.50 m wide join and glazed north to the pool and
east to the landscape plot; the show kitchen beyond the dining in the SSW wing,
open to it across 3.3 m of wall, with the Arabic kitchen behind it at the
south end and its service door on the south face. The guest bedroom takes the
road side of the south end, the office sits beside the stair off the gallery.
The garage, the staff strip and the whole first floor are unchanged, and the
master terrace stays on the kitchen roof.

**Reason.** Owner instruction 2026-10-02: the earlier plan was not an open
area design; the owner asked for the salon on the left, the dining on the
right, a big foyer, the living room in the centre with a high ceiling, and the
kitchen after the dining room. Claude confirmed the orientation (left is
north) and offered two ways to carry the double height: a tall block in the
courtyard, or a void with a gallery upstairs, which would have cost about 45
m2 of first floor program. The owner chose the tall block.

**Result, measured: 644.82 m2, 18.17 m2 inside the cap,** up from 9.89 m2.
The D-005 margin is restored and its expected failure marker is off. Road
wing 282.12, SSW wing 45.47, living block 49.01, first floor 268.22. Padding:
the hall by design (+20.9), the office +1.8, the master +5.7 (it follows the
guest bedroom's length). The kitchens keep a wall to the living room; opening
it is an option for the owner.

**Approved by Aiman: yes,** the arrangement and the tall living block. The
hall size and the room sizes: for review.

---

## 2026-10-02, interiors drawn in Phase 3

### D-035 Master suite plan, with its terrace on the kitchen roof

**Decision.** The master's private balcony is a terrace on the flat roof of the
single storey kitchen and dining block, outside the master's east wall, about
45 m2, reached through a 3.00 m glazed sliding door. Inside, a 5.00 m service
zone on the road side holds the bathroom (about 13 m2: bathtub, separate
shower, double basin, WC) and his and hers walk-in wardrobes (5 m2 each),
reached along a 1.40 m dressing gallery from the landing door. The bedroom and
sitting area (about 47 m2) take the terrace side, with the coffee station by
the terrace door.

**Reason.** Owner choice 2026-10-02 from three balcony options. The roof is
there already with its 1.20 m parapet (DDA FAQs Building Q34); the two storey
wing shades it in the afternoon; it looks north over the pool; and open
terraces are excluded from GFA (DDA FAQs Building Q25), so it costs nothing
against the cap. The tall living room wall closes its east side, so it has no
direct view of the landscape plot. The service zone goes on the road side so
the bedroom keeps the quiet, shaded terrace side. Waterproofing and the
terrace finish are for the consultant.

**Approved by Aiman: yes,** the terrace position. The internal plan: Claude's
proposal, for review.

### D-034 En-suite bedrooms: bath and wardrobe beside the door

**Decision.** In bedrooms 2 to 4 and the guest bedroom, a 2.40 x 2.40 m
bathroom (walk-in shower, WC, basin) and a 0.65 m deep built-in wardrobe sit
beside the door, forming an entry lobby, so the bedroom keeps its facade and
windows. The bathroom takes the end of the door wall away from the facade. The
bathrooms are internal, with mechanical extract. Partitions 0.10 m. The maid's
room gets a 1.20 m wide shower room across its far end, beside the outdoor
bathroom so the two share drainage.

**Reason.** Owner choice 2026-10-02 from three en-suite layouts, and the
owner's instruction to draw interiors in Phase 3 rather than Phase 4. Each
bedroom keeps 23.75 m2 (guest 25.75 m2) for the bed area. Sizes are Claude
proposals, recorded in brief/program.yaml under interiors.

**Approved by Aiman: yes,** the layout principle. The sizes and the maid's
shower room: for review.

---

## 2026-10-02, open plan and the family hall

### D-033 Owner rule: open space maximization, read as open-plan interiors

**Decision.** A must-rule for the whole villa: shared spaces flow together with
as few walls and corridors as possible. On the ground floor the foyer, stair
hall, corridor and link hall are one open entrance hall, and the show kitchen,
dining and living are one open space. Where they open into the double height
living room a bulkhead stays above 4.70 m to mark the edge of the double height.
Private rooms stay enclosed with doors: bedrooms, bathrooms, majlis (formal, with
its own powder room), office, Arabic kitchen, staff rooms and services.

**Reason.** Owner instruction 2026-10-02, "the villa must be built on the open
space maximization rule". Claude asked which open space was meant; the owner
chose open-plan interiors, not a smaller footprint for more garden. The massing,
footprint and GFA are unchanged by the rule itself.

**Risk.** An open stair joining two floors and an open kitchen may meet fire
separation requirements under the UAE Fire and Life Safety Code, approved by
Dubai Civil Defence (DDA FAQs Building Q42). TO VERIFY, OI-24.

**Approved by Aiman: yes,** the rule and its reading. The list of which spaces
join: Claude's application, for review.

### D-032 First floor around a central family hall

**Decision.** The upstairs corridor is removed. The family room spans the full
width of the first floor in its middle, with the road facade on one side and the
courtyard and pool on the other, and is open to a family hall over the stair and
linen. Bedrooms 2 and 3 sit side by side across the rear and open onto the
family room. The stair arrives on a 1.80 m landing, from which the master suite
and bedroom 4 are entered, so the master shares no wall with the family room
(acoustic separation, CLAUDE.md section 4).

**Reason.** Owner request 2026-10-02: the family room central with the bedrooms
around it. Two arrangements were offered; the owner chose this one. Bedroom 4
cannot sit directly beside the stair because the stair's top flight arrives at
its east end, which must be circulation.

**Result, measured: 653.10 m2, 9.89 m2 inside the cap,** up from 6.52 m2. The
first floor is 3.37 m2 smaller because the 30 m2 corridor became family hall.
The ground floor is unchanged: the band widths are held at the approved 5.10 m
and 4.20 m. Left free, the search would narrow the east band to 3.70 m (648.50
m2), making the majlis a 3.7 m wide gallery; not done without the owner.

Two gaps in the earlier Phase 3 model came to light and are fixed: the home
office had no door (it now opens off the foyer) and the maid's room had only its
outside door (it now also opens into the laundry).

**Approved by Aiman: yes,** the arrangement. The measured result: for review.

---

## 2026-10-02, Phase 3 section and staff strip

### D-031 Staff strip reordered: maid's room and outdoor bathroom on the north wall

**Decision.** In the staff strip north of the corridor, the maid's room and the
outdoor bathroom now sit on the external north wall, with the laundry and plant
room on the corridor side. The plant room keeps its courtyard wall.

**Reason.** CLAUDE.md asks for the maid's room in the staff zone with a separate
entrance. On the old order it had no external wall, so no window and no outside
door. Now it has both, and the outdoor bathroom has north and courtyard walls
for its own door. The laundry is reached from the garage.

**Result, measured:** 656.47 m2, unchanged, 6.52 m2 inside the cap.

**Approved by Aiman: no,** Claude's correction for review at the Phase 3
checkpoint.

### D-030 Tall section: 5.00 m ground, 4.00 m first, 1.20 m parapet, 10.20 m overall

**Decision.** Floor to floor heights of 5.00 m on the ground floor and 4.00 m on
the first floor, with a 1.20 m parapet: 9.00 m to the main roof slab and 10.20 m
overall. The double height living room rises the full 9.00 m.

**Reason.** Owner choice 2026-10-02, for high ceilings. About 4.55 m clear on the
ground floor and 3.55 m upstairs, inside the clear heights in DDA FAQs Building
Q28 (up to 6 m ground, up to 4.2 m typical) and above the Q33 minimum of 2.7 m.
The 1.20 m parapet is DDA FAQs Building Q34.

**Risk.** DDA FAQs Building Q29 gives a metre cap of floors x 4.2 m, 8.40 m for
G+1, which this exceeds. Whether that cap applies to this plot, which states only
"G+1", is TO VERIFY, OI-13. The tall ground floor also forces a compact stair
and lift core, OI-23.

**Approved by Aiman: yes.**

---

## 2026-10-02, bedrooms restored

### D-029 Bedrooms 2 to 4 restored to 30 m2

**Decision.** The D-027 trim on bedrooms 2 to 4 is reversed: back to 30 m2,
their CLAUDE.md minimum. The master stays at 68 and the family room at 33.

**Reason.** Owner decision 2026-10-02, spending the headroom freed when the
driver's room was removed (D-028).

**Result, measured: 656.47 m2, 6.52 m2 inside the cap.** Thinner than the
9.99 m2 margin recommended in D-005, and thinner than Claude estimated before the
change: restoring the three bedrooms cost 10.75 m2 against the cap, not the
7.5 m2 quoted, because the longer first floor needs a longer ground floor under
it. The master is 2.27 times the bedrooms at the bottom of the ranges, inside
the brief's 2.2 to 2.5.

The D-005 margin test is now a strict expected failure, so the shortfall stays
visible. A floor of 5 m2 is still enforced.

**Approved by Aiman: yes.** Restoring the bedrooms. Accepting the thinner
margin: not yet asked.

---

## 2026-10-02, staff zone

### D-028 No driver's room; an outdoor bathroom instead

**Decision.** The driver's room is removed from the program and kept on record
under `removed:` in `brief/program.yaml`. An outdoor bathroom, WC and shower,
4.5 m2, is added. It has its own external door and no internal connection to
the villa, and sits on the courtyard face of the staff strip beside the garage,
facing the north end of the pool deck.

**Reason.** Owner decisions 2026-10-02: first to move the driver's room outside
the villa, then to drop it and make sure there is a bathroom outside. Placing the
bathroom on the courtyard face lets one room serve swimmers, garden use, and a
non-resident driver or outdoor staff by the garage. The 4.5 m2 size and the
placement are Claude's reading of the instruction, flagged for owner review.

A standalone driver's outbuilding was tried first and rejected by the geometry:
north of the garage there is not enough room inside the 3 m setback for it.

**Result, measured: 645.72 m2, 17.27 m2 inside the cap.** Removing the driver's
room shortened the staff strip, so the garage no longer carries padding and is
exactly its 31.3 m2 internal target. The majlis absorbs the floor under the
bedrooms instead and measures 50.1 m2 against its 35 m2 brief.

**Approved by Aiman: yes,** the removal and the outdoor bathroom. The size and
placement of the bathroom: not yet.

---

## 2026-10-02, Phase 2 plan fits

### D-027 Option C confirmed; foyer single height; upstairs trims

**Decision.** Massing option C stands. The living room is double height in the
single storey wing. The foyer is single height, taking its height from a tall
ground floor rather than a void. Upstairs trims, recorded in
`brief/program.yaml` with their brief figures:

| Room | Brief | Now |
|---|---|---|
| Master suite, minimum | 70 | 68 |
| Bedrooms 2 to 4, minimum | 30 | 28 |
| Family living | 35 | 33 |

**Reason.** Owner decision 2026-10-02, after option A was measured at 698.86 m2,
35.87 over, because a double height living room in a two storey bar takes plate
the bedrooms need. Option C puts the living room where a high ceiling costs no
plate. The owner wants high ceilings; ceiling height is not GFA, and DDA FAQ Q28
allows a ground floor clear height up to 6 m, subject to OI-13.

The cuts are upstairs because in option C a ground floor cut in the two storey
wing only turns into padding under the bedrooms. The master stays 2.43 times the
bedrooms at the bottom of the ranges and 2.29 at the top, inside the brief's
2.2 to 2.5.

**Result, measured from the drawn plan: 651.22 m2, 11.77 m2 inside the cap**,
above the 9.99 m2 margin recommended in D-005. The majlis comes out at 44.3 m2
against its 35 m2 brief, because it fills the ground floor under the bedrooms.

**Approved by Aiman: yes.** Chose option C and the master to 68 directly.

---

## 2026-10-02, design basis settled by the owner

### D-026 Garage counts toward GFA, and corridors are 1.80 m

**Decision.** The design proceeds on two owner decisions: the enclosed garage
counts toward the 662.99 m2 GFA cap, and DDA FAQs Building Q12's 1.80 m corridor
minimum applies to corridors inside this private villa.

**Reason.** Owner decision 2026-10-02. Both were open DDA questions (OI-01 and
OI-21). The owner settled them on the conservative reading rather than wait, so
neither can return area later through a DDA answer.

**Approved by Aiman: yes.** Stated directly.

---

## 2026-10-02, trim package 2 and the measured plan

### D-025 Once a plan exists, measured GFA is the binding figure

**Decision.** `src/analysis/gfa_check.py` now reads `brief/layouts.yaml` and
tests the cap against GFA measured from the drawn plan, failing loudly when it is
exceeded, as CLAUDE.md section 3 requires. The net to gross estimate is still
printed, but it no longer decides the verdict.

**Reason.** Four successive estimates of this plan each came in optimistic: a
flat wall allowance, a corridor assumed shorter than the plan needed, a corridor
width below the DDA figure, and finally a first floor allowed to be deeper than
the ground floor it sits on. Each was corrected, and each correction made the
figure worse. Drawn geometry ends that pattern: `src/model/layout_gen.py` places
every room, stacks the stair cores, keeps the first floor over the ground floor,
and the area is measured from what is drawn.

**Approved by Aiman: not required.** Technical.

### D-024 Trim package 2: the sunroom is removed

**Decision.** The sunroom, 20 m2 net, is removed from the program. It is kept on
record under `removed:` in `brief/program.yaml` with its brief figure and reason.
The SSW wing is sized to its rooms at brief size rather than to the Phase 1
massing.

**Reason.** Owner chose package 2 of the four costed on 2026-10-02, the only one
that left every other room at its brief size. The courtyard and the double height
living room facing it already give the house its garden room.

**Approved by Aiman: yes.** Chose package 2 directly.

---

## 2026-10-02, Phase 2

### D-023 Net to gross factor replaced by measurement, 1.18 to 1.222

**Decision.** `brief/site.yaml` now carries 1.222, measured, with the previous
1.18 kept beside it as `net_to_gross_previous`.

**Reason.** A-01 always said the Phase 0 assumption would be replaced by the
ratio of the actual plan at Phase 2. This is that replacement. It comes from
`src/analysis/plan_feasibility.py`: external walls from each wing's real
perimeter at 0.25 m, partitions at 4.5% of net, a 1.40 m corridor on the first
floor and a service spine on the ground.

It is worse than assumed because option C has two long thin wings, and a long
thin wing pays for its external walls by the metre. The single depth SSW wing,
where every room opens to the courtyard and there is no corridor, measures 1.13
on its own.

The GFA check and the feasibility model now agree to within 0.1 m2, 656.33
against 656.43, where before they differed by 21 m2.

**Approved by Aiman: not required.** Replacing an assumption with a measurement.

### D-022 Garage reduced to two cars, 55 m2 to 38 m2

**Decision.** The enclosed garage holds two cars, not the three in CLAUDE.md
section 4. 38 m2.

**Reason.** Owner decision 2026-10-02. Sized from the DDA bay standard rather
than scaled down: DDA FAQs Building Q5 gives a standard bay as 2.5 x 5.5 m, and
the 55 m2 three car figure works out as roughly 8.15 x 6.75 m holding three bays
at 2.55 m. Removing one bay takes 2.55 m off the width, giving about
5.60 x 6.75 m, so 38 m2.

The DDA plot details require a minimum of one parking space, so two remains
compliant.

**This is what made the plan fit.** A garage target is already a gross footprint,
so the 17 m2 comes straight off GFA with no net to gross factor applied. Plan 2
moves from 10.31 m2 over the cap to 6.56 m2 inside it.

**Approved by Aiman: yes.** Stated directly.

### D-021 Plan direction 2, Courtyard

**Decision.** The reception rooms interconnect around the courtyard rather than
hanging off a corridor, and the corridor shrinks to a short service spine serving
the staff zone, guest bedroom and office.

**Reason.** Owner decision 2026-10-02. It saves 20.96 m2 against a conventional
corridor plan, all of it circulation, and it is the plan that actually uses the
courtyard that option C commits to. Plan 1, the corridor plan, remains 14.29 m2
over the cap even after the two car garage, and is not available.

The cost is how the house works: some parts of the ground floor are reached by
crossing the courtyard or passing through a reception room rather than walking a
corridor.

**Approved by Aiman: yes.** Stated directly.

---

## 2026-10-01, trims

### D-019 Trim route B, service and circulation only, 13 m2 net

**Decision.** Owner approved trim route B. Eight rooms reduced, none of them a
principal room:

| Room | Brief | Trimmed | |
|---|---|---|---|
| Staircase + elevator, first | 20 | 15 | now the top landing, no roof flight to accommodate |
| Staircase + elevator, ground | 20 | 18 | tightened with the first floor core |
| Entrance foyer | 20 | 19 | still double height |
| Pantry / storage | 6 | 5 | |
| Laundry | 8 | 7 | |
| Maid's room | 12 | 11 | |
| Driver's room | 12 | 11 | |
| MEP plant room | 8 | 7 | |
| **Total** | | | **13 m2 net, 15.34 m2 gross** |

**Reason.** Counting the garage toward GFA (D-018) put the program 4.43 m2 over
the cap and 14.42 m2 over the design target at the minimum of every range. Four
routes were costed and put to the owner, who chose B because it touches no
principal room. The largest single saving, 5 m2 from the first floor stair and
lift, comes almost free: removing the roof stop in D-017 means there is no
further flight to accommodate.

**Result.** The program now lands at **652.08 m2** at the minimum of every range,
10.91 m2 inside the cap and 0.92 m2 inside the design target. The GFA check
passes.

Every trimmed room keeps its CLAUDE.md figure in `brief/program.yaml` as
`brief_target_m2`, with the reason, so the trim stays visible and reversible. A
pytest check enforces that, and another enforces that no principal room was
touched.

**Approved by Aiman: yes.** Chose route B directly.

### D-020 GFA check pass and fail semantics corrected

**Decision.** A breach at the minimum of the ranges is a FAIL. A breach only at
the maximum is reported as "fits at minimum, high end unaffordable", with a new
RANGE HEADROOM section quantifying how much of the range can be spent.

**Reason.** The old logic failed the build whenever the top of the bedroom ranges
did not fit, which would have left the suite permanently red for a condition that
is a budget to manage rather than a defect. The villa is built at one size, not
at a range. What matters is that a buildable version exists under the cap and
that everyone can see how much of the range is affordable.

**Approved by Aiman: not required.** Technical.

---

## 2026-10-01, owner decisions on roof and garage

### D-018 Count the parking as part of the GFA

**Decision.** The 55 m2 garage counts toward the 662.99 m2 GFA cap.
`brief/program.yaml` now marks it `gfa: counts`, and the GFA check has no
unverified areas left.

**Reason.** Owner decision. DDA's published material does not rule on garages,
so rather than design against an unknown and risk a redesign at submission, the
conservative reading is adopted. If the issued Site Plan later excludes the
garage, 55 m2 comes straight back and the room ranges reopen.

**Consequence, and it is not small.** The briefed program no longer fits. At the
low end of every bedroom range it reaches 667.42 m2 against the 662.99 m2 cap,
over by 4.43 m2, and over the 653.00 m2 design target by 14.42 m2. At the high
end it is 33.93 m2 over the cap, and no plan efficiency tested can recover that,
so the top of the bedroom ranges is no longer available. Trims are needed and
are tracked as OI-18. No room has been cut.

**Approved by Aiman: yes.** Stated directly.

### D-017 No roof terrace and no roof enclosure

**Decision.** The roof terrace and the roof stair and elevator enclosure are
removed from scope. `brief/program.yaml` now has an empty `roof` section. The
elevator serves ground and first only.

**Reason.** Owner decision. This also removes the risk found in the DDA FAQ,
where Q27 counts a roof gym as an additional floor unless the master developer
excludes it. On that reading a roof enclosure could have breached the G+1 cap
outright rather than merely adding GFA. That risk is now gone, and OI-02 closes.

**Carried forward.** The flat roof still exists and still needs a 1.20 m parapet.
The VRF outdoor units still need a location, either on the flat roof behind a low
screen, which needs no enclosure and adds no floor, or at ground level in the
service zone. Decided in Phase 5, tracked as OI-17.

**Approved by Aiman: yes.** Stated directly.

---

## 2026-10-01, owner selection and DDA research

### D-016 Parapet raised to 1.20 m, the DDA minimum

**Decision.** `brief/massing.yaml` now carries a 1.20 m parapet, up from the
1.10 m previously assumed.

**Reason.** Not a design choice, a correction. DDA FAQs - Building, retrieved 2026-10-01 from https://webzoning.dda.gov.ae/Zoning/Content/dda/FAQs.pdf, Q34: "What is the minimum
parapet and balcony handrail height?" Answer: "1.2m from the floor finish
level." The earlier 1.10 m was below the DDA minimum. Overall height moves from
8.90 m to 9.00 m and every shadow figure was recomputed.

**Approved by Aiman: not required.** Correcting to a cited authority minimum.

### D-015 DDA published material checked for the garage question

**Decision.** OI-01 stays OPEN. DDA's published guidance does not answer it.

**Reason.** Owner asked for DDA to be checked before any query was drafted. Two
DDA sources were retrieved and parsed in full:

- DDA FAQs - Building, retrieved 2026-10-01 from https://webzoning.dda.gov.ae/Zoning/Content/dda/FAQs.pdf, 20 pages
- Objectives of the Dubai Building Code, dda.gov.ae, 17 pages

The word "garage" appears **zero times** in either document. DDA's own answer to
"Where can I find the Planning Regulations for my Plot?" is "You can find the
regulations for your plot on the issued site plan", and to "What are the Parking
standards as per DDA?" is "as mentioned in the site plan". So the answer is
plot-specific and lives in the issued Site Plan and the Meraas development
guideline, neither of which we hold. See OI-01 and OI-03.

What the FAQ does settle is that **GFA and BUA are different measures** in DDA's
own usage. Q25: "Balconies are always excluded from GFA calculations, but
included in the BUA calculation." The cap on this plot is on GFA, 662.99 m2, not
on BUA.

**Approved by Aiman: not required.** Research, reported to the owner.

### D-014 Option C, Courtyard, selected, with the double height living room

**Decision.** Option C is the massing to carry into Phase 2. The living room in
the single storey SSW wing is double height.

**Reason.** Owner decision, stated 2026-10-01. Option C holds 87% of the pool
deck in shade through cooling season afternoons against option A's 93%, and
gives up the open view east, but it encloses a private courtyard and the double
height living room costs no upper floor area because nothing sits above that
wing. The owner weighed that against the recommendation and chose C.

All three options carry the same 406.5 m2 ground floor and 290.3 m2 first floor,
so the choice moves no GFA.

**Approved by Aiman: yes.** Stated directly.

---

## 2026-10-01, Phase 1

### D-013 Plans are drawn plot up, not north up

**Decision.** The massing sheet and the viewer draw the plot squared to its own
building grid, bearing 30.18 degrees, rather than north up. The north arrow is
rotated to match and the sheet says "Plot up, not north up".

**Reason.** Owner request. North up renders this plot as a rotated diamond, which
makes it hard to see which face is the entrance and which is the backyard. Plot
up renders it as a rectangle: side 1 and the entrance on the left, side 3 and the
backyard on the right, neighbours top and bottom. The true orientation is still
on the sheet, so nothing is lost.

The formal site plan VJH-SP-001 stays north up, which is the convention a
consultant expects.

**Approved by Aiman: yes.** Requested directly.

### D-012 Side numbers and wall to boundary dimensions shown on every plan

**Decision.** Every massing plan and the viewer label all four sides with their
number and role (ENTRANCE, BACKYARD, NEIGHBOUR), and dimension the shortest
distance from the villa wall to each boundary.

**Reason.** Owner request. The distances are measured as the true nearest
approach between the ground floor footprint and each side, not as a bounding box
offset, so they stay correct for the L-shaped option C and for a plot that is not
an exact rectangle. A pytest check asserts every one of them clears the 3 m
setback.

**Approved by Aiman: yes.** Requested directly.

### D-011 Boundary wall concept

**Decision.** 2.40 m overall. Solid to 1.20 m with a lighter screen above on the
road side and on the landscape plot side; solid full height against both
neighbours.

**Reason.** The road face should not present a blank 2.4 m wall to the street,
and the landscape plot side has no building and no overlooking on the far side,
so there is a view worth keeping. Both neighbour sides are about privacy only.
Gates are recessed so a car can pull clear of the 18.30 m road while the gate
opens. Heights are TO VERIFY against DDA rules.

**Approved by Aiman: not yet.** Proposed at the Phase 1 checkpoint.

### D-010 Massing option A, Garden East, recommended

**Decision.** Recommend option A: a single bar along the road edge with the
garden and pool on the ESE side facing landscape plot 5130274, and the upper
floor pushed to the ESE edge of the bar.

**Reason.** Computed, not asserted. The villa stands west of the pool, so its
shadow crosses the water through the afternoon: 65% of the pool deck shaded at
15:00, 99% by 16:00, complete from 17:00, a 93% mean across the cooling season
and never below 61% at any hour tested. In winter the sun swings far enough south
to pass the mass entirely, leaving 100% sun on the water at midday. It is the
only option that wins on both.

Option B, the alternative CLAUDE.md asks to be tested, gets no shade at all from
15:00 to 18:00, because the villa sits north-east of the pool and the afternoon
shadow runs along the water rather than across it. Option C shades well, 87%, but
the wing that blocks the summer afternoon sun also blocks the low winter sun,
leaving 78% winter midday sun, and it gives up the view east.

Option A also puts the garden and the main glazing on the face the sun study
shows is cheapest to glaze: side 3 takes 368 kWh/m2 in summer mornings but only
51 in the afternoons, against 233 for the road face. That same face has no
building on the far side and never will.

**Approved by Aiman: not yet.** Presented at the Phase 1 checkpoint.

### D-009b Clear-sky irradiance, not a typical year

**Decision.** The sun study uses Ineichen clear-sky irradiance with the pvlib
Linke turbidity climatology, and Perez-Driesse transposition to vertical
surfaces, at 15 minute steps through a full year.

**Reason.** The design case in Dubai is the cloudless day, not the average day.
Shading and glazing decisions have to hold on the worst day, not the mean one.
Figures are modelled for comparison between options, not measured site data.

**Approved by Aiman: not yet.** Technical, reported at the Phase 1 checkpoint.

---

## 2026-10-01

### D-009 Boundary taken from the DDA GIS, and true north confirmed

**Decision.** `brief/site.yaml` now carries the DDA Development Information
System's own plot geometry in WGS84, with the source lon and lat stored on every
vertex, replacing the coordinates scaled off the plot plan drawing. Plan-up is
confirmed as true north and `orientation.to_verify` is set to false.

**Reason.** Phase 1 rests entirely on the orientation being right. An error there
would have invalidated the sun study, every facade solar exposure figure, the
master suite orientation, and the pool and garden recommendation, rather than
merely shifting a number. The owner asked for it to be settled before Phase 1.

Two independent measurements, neither by eye:

- The north arrow on the DDA plan, measured from the PDF vector geometry, runs
  apex to tail notch at identical x, so exactly 0.000 degrees from sheet vertical.
- The DDA GIS polygon bearings match the project coordinates to a mean of -0.02
  degrees across all five edges.

The GIS geometry also improved the boundary itself. Plot area deviation fell from
+0.029% to -0.001%, and all four stated side lengths are now reproduced to within
0.02%. The site location was corrected from an assumed 25.0 N, 55.1 E to the
actual 24.897528 N, 54.964976 E, 17.7 km away, though that correction changes sun
altitude by only about 0.1 degrees and was immaterial.

Pytest checks now guard the orientation, the location, and the agreement between
each vertex's local coordinates and its stored WGS84 source, so none of this can
silently revert.

**Approved by Aiman: yes.** The owner directed the verification.

---

### D-008 Site plan issued at 1:200 on A2 landscape, not A3

**Decision.** The site plan sheet is A2 landscape at a true 1:200.

**Reason.** At 1:200 the plot plus its dimension lines measures 55.7 x 56.6 m of
model space, against 57.0 x 55.4 m available on A3. It does not fit, by 1.2 m.
The options were to drop to 1:250 on A3 or move to A2 at 1:200. A2 at 1:200 is
the standard site plan sheet for this scale and keeps dimension text at its
designed printed size. A fit check in `src/drawings/site_plan.py` raises an error
rather than silently producing a cramped sheet.

**Approved by Aiman: not yet.** Reported at the Phase 0 checkpoint.

### D-007 Garage and roof enclosure are treated as gross areas, not net

**Decision.** The 55 m² garage and 20 m² roof enclosure targets are taken as
whole-footprint figures. The net-to-gross factor is not applied to them.

**Reason.** Those two targets already describe a whole enclosed footprint rather
than a net internal room area. Applying a 1.18 factor would inflate the garage to
65 m² of GFA and overstate the case against the cap by 10 m². Overstating a
constraint is as misleading as understating it.

**Approved by Aiman: not yet.** Reported at the Phase 0 checkpoint.

### D-006 A 20 m² stair and elevator landing added on the first floor

**Decision.** `brief/program.yaml` carries a 20 m² staircase and home elevator on
the first floor, flagged `added_by_claude`, and the GFA check reports it under
"ADDED BY CLAUDE, needs owner review".

**Reason.** CLAUDE.md section 4 itemises the stair and elevator on the ground
floor only, while also stating the elevator serves ground, first, and roof. A
first floor landing is physically required. Rather than absorb it silently into
the net-to-gross factor, it is itemised so the owner sees the 20 m² and can set a
different allowance.

**Approved by Aiman: not yet.** Open item OI-09.

### D-005 Design target set at 653.00 m², holding 9.99 m² back from the cap

**Decision.** `brief/site.yaml` carries a design target of 653.00 m² against the
DDA cap of 662.99 m².

**Reason.** GFA on stamped drawings is measured to the outside face of external
walls by the consultant. A concept-stage figure can drift by several square
metres on wall thicknesses alone, and exceeding the cap at submission means
redesign. The margin is a single parameter and is released once the consultant
confirms the measurement basis, so effectively none of the area is lost.

**Approved by Aiman: not yet.** Advice given with the owner's maximise directive
on 2026-10-01. The owner was told that running at the full 662.99 m² is available
on request, with the risk stated.

### D-004 Target built-up area is the GFA cap, not the earlier 650 m²

**Decision.** The strategy in `brief/site.yaml` is `maximise_to_cap`. The brief's
earlier "about 650 m²" target is superseded.

**Reason.** Owner directive, stated 2026-10-01: "I want the maximum size for the
built-up." The hard limit of 662.99 m² is unchanged and is enforced by
`src/analysis/gfa_check.py` and the pytest suite.

**Approved by Aiman: yes.** Stated directly.

### D-003 The majlis and the salon are one room

**Decision.** One formal reception room, labelled `Majlis (Salon)` in drawings
and in `brief/program.yaml`. No mezzanine, no additional salon.

**Reason.** Owner confirmed 2026-10-01. An earlier reading of "the mezzanine is
the salon" raised the possibility of a third reception room on a new mezzanine
level, which would have added roughly 41 m² gross and breached the cap, and would
have raised a G+1 height question. The owner clarified that the word was majlis,
not mezzanine. Both concerns are withdrawn.

**Approved by Aiman: yes.** Stated directly.

### D-002 The dining room is on the ground floor

**Decision.** Dining is confirmed on the ground floor at an indicative 22 m².

**Reason.** Owner confirmed 2026-10-01. CLAUDE.md section 4 had listed the dining
room as not specified by the owner. Size and placement within the ground floor
are still proposed at the Phase 2 checkpoint.

**Approved by Aiman: yes.** Stated directly.

### D-001 Buildable envelope offset with a mitred join, not the shapely default

**Decision.** `src/model/site.py` offsets the plot inward using
`join_style="mitre"` with `mitre_limit=100.0`.

**Reason.** Shapely's default mitre limit of 5.0 bevels sharp corners. The plot
has a bend at vertex C where side 3 changes direction, and a bevelled corner
there would understate the buildable envelope. The mitred offset produces a true
3 m setback to a real corner, which a pytest check confirms by measuring the
minimum distance from the envelope to the boundary.

**Approved by Aiman: not yet.** Technical, reported at the Phase 0 checkpoint.

---

## Project setup, 2026-10-01

### S-003 Python 3.12, not the installed 3.13 or 3.14

Python 3.12.10 was installed alongside the existing 3.13 and 3.14. IfcOpenShell
publishes no CPython 3.13 or 3.14 wheels, and CLAUDE.md section 8 pins 3.12.
Versions pinned in `requirements.txt`.

### S-002 Repository folder and name

The repository lives at `C:\Projects\Villa-Jebel-Ali-Hills-Dubai` under the name
`villa-jebel-ali-hills-dubai`, rather than the `villa-5130272` in SETUP.md.
Owner's instruction. The `Reference` folder was renamed to lowercase `reference`
to match CLAUDE.md section 9.

### S-001 Git LFS from the first commit

LFS tracks IFC, Blender, PDF, image, and 3D asset formats. CLAUDE.md anticipates
a repository of several GB once assets and renders are added. Setting LFS before
the first commit avoids a history rewrite later, which rule 6 forbids on `main`.
