# Open items: Villa 5130272, Jebel Ali Hills

Every item that is unresolved, unverified, or awaiting an authority answer.
Nothing here is a regulatory value invented by Claude. Each regulatory question
names the document that must answer it.

Status key: OPEN, ASKED (sent to a third party), CLOSED.

Last updated: 2026-10-02 (Phase 2 opened, plan feasibility tested)

## Critical. Blocks Phase 2 room layouts

### OI-01 Does the enclosed garage count toward GFA?

| | |
|---|---|
| Status | **SETTLED BY OWNER DECISION 2026-10-01, still worth confirming** |
| Worth | 55.00 m2 |
| Answered by | The issued Site Plan, if ever obtained |

The owner decided on 2026-10-01 to **count the parking as part of the GFA**, the
conservative reading, rather than wait. The design now proceeds on that basis and
no longer depends on the answer. See decision D-018.

It is still worth confirming, because a DDA answer excluding the garage would
return 55 m2 and reopen the full bedroom ranges. An enquiry covering this and
five other points is drafted and sits in the owner's Gmail awaiting a confirmed
recipient. DDA publishes no enquiry email address: their contact page gives phone
numbers and a web form only.

What DDA's published material does establish, from the FAQs retrieved
2026-10-01: GFA and BUA are different measures, since Q25 excludes balconies from
GFA but includes them in BUA. The cap on this plot is on GFA.

### OI-02 Does the roof stair and elevator enclosure count toward GFA?

| | |
|---|---|
| Status | **CLOSED 2026-10-01** |

Closed by removing the roof terrace and the roof enclosure from scope, on the
owner's decision. See D-017. The question no longer arises, and with it goes the
sharper risk that DDA FAQ Q27's treatment of a roof gym as an additional floor
might have applied to a roof enclosure and breached G+1 outright.

### OI-18 The program no longer fits, and needs trims

| | |
|---|---|
| Status | **CLOSED 2026-10-01** |
| Decided by | Aiman |

Closed by trim route B, 13 m2 net from service and circulation only. See D-019.
The program lands at 652.08 m2 at the minimum of every range, inside both the
662.99 m2 cap and the 653.00 m2 design target.

### OI-20 The plan needs more area than the cap allows

| | |
|---|---|
| Status | **OPEN, blocks the Phase 2 layouts** |
| Raised | 2026-10-02, Phase 2 |
| Updated | 2026-10-02, wall model corrected |
| Decided by | Aiman |

Tested before drawing any room, by `src/analysis/plan_feasibility.py`.

**Plan direction chosen by the owner: plan 2, Courtyard.** Reception rooms
interconnect around the courtyard and the corridor shrinks to a service spine.
That saves **20.96 m2** against a conventional corridor plan, all of it
circulation, and it is the right call. It is still not enough.

| | Gross | vs cap | vs target | net:gross | corridor |
|---|---|---|---|---|---|
| Plan 1, Corridor | 694.26 | **31.27 over** | 41.26 over | 1.263 | 63.00 |
| **Plan 2, Courtyard** | **673.30** | **10.31 over** | 20.30 over | 1.222 | 42.00 |

**A correction to my own figures.** The first pass allowed a flat 8% of net area
for walls. That does not even cover the external walls of a 27 m long wing, and
it understated the total by about 29 m2. Walls are now computed from each wing's
real perimeter, with partitions at 4.5% of net area. The numbers above are the
corrected ones.

| Zone | Size | Net | Corridor | External wall | Gross |
|---|---|---|---|---|---|
| SSW wing, single depth | 8.30 x 13.35 | 92.0 | 0.0 | 10.8 | 106.97 |
| Road wing | 11.03 x 27.00 | 198.0 | 16.8 | 19.0 | 297.72 |
| First floor | 11.03 x 24.36 | 216.0 | 25.2 | 17.7 | 268.61 |

**Three ways out, and they are not equal.**

**Settle OI-01.** The garage is worth 55.00 m2, which is **5.3 times** the 10.31
m2 shortfall. If the Site Plan excludes it, plan 2 needs 618.30 m2 and fits with
44 m2 to spare, which also reopens the bedroom ranges in OI-19. Cutting another
10 m2 while a 55 m2 question sits unanswered is the wrong order of work.

**A third round of trims, about 8.5 m2 net.** Possible, but this would be the
third pass over the same room list, and the rooms that are easy to trim have
already been trimmed in route B.

**Drop a room.** The sunroom at 20 m2 net would clear the shortfall outright and
leave margin. It is the only ground floor room with no fixed function in the
brief beyond being glazed and garden facing, and option C's courtyard already
gives the house a garden room of sorts. This is the owner's call, not mine.

Recommendation: get the Site Plan before cutting again.

### OI-19 How to spend the remaining range headroom

| | |
|---|---|
| Status | OPEN, not blocking |
| Raised | 2026-10-01 |
| Decided by | Aiman, at the Phase 2 checkpoint |

CLAUDE.md gives the master suite as 70 to 80 m2 and bedrooms 2 to 4 as 30 to
35 m2, a span of 25 m2 net in total. After route B, only part of that span is
affordable.

| | Net available |
|---|---|
| Full range, minimum to maximum | 25.00 m2 |
| Affordable against the 662.99 m2 cap | **9.25 m2**, 37% of the range |
| Affordable against the 653.00 m2 design target | 0.78 m2 |

So the master suite at 80 m2 with all three bedrooms at 35 m2 is **not
reachable**: it needs 15.75 m2 net more than the cap allows.

The 9.25 m2 figure assumes the 9.99 m2 design margin from D-005 is released. Kept
as it stands, there is effectively nothing to spend and every bedroom sits at its
minimum.

Three ways to spend it, for the owner at the Phase 2 checkpoint:
- All on the master suite, taking it from 70 to about 79 m2, which is the brief's
  stated priority that the master be much larger than the other bedrooms.
- Spread evenly, about 2.3 m2 on each of the four bedrooms.
- Keep the margin and leave the rooms at minimum until the Site Plan answers
  OI-01. If the garage turns out to be excluded from GFA, 55 m2 returns and the
  full range reopens.

### OI-17 Where do the VRF outdoor units go?

| | |
|---|---|
| Status | OPEN, Phase 5 |
| Raised | 2026-10-01 |

The roof terrace was removed on 2026-10-01, but the VRF condensers still need a
home. Either on the flat roof behind a low screen, which needs no enclosure and
adds no floor, or at ground level in the service zone. Roof mounting is normally
preferable for noise and for refrigerant pipe runs. Decided in Phase 5.

## Important. Blocks Phase 1 or Phase 3## Important. Blocks Phase 1 or Phase 3

### OI-03 Demarcation Certificate coordinates

| | |
|---|---|
| Status | OPEN, downgraded 2026-10-01 |
| Raised | 2026-10-01, Phase 0 |
| Answered by | Site Plan and Demarcation Certificate from the master developer |

**Downgraded.** The boundary no longer comes from coordinates scaled off a
drawing. `brief/site.yaml` now carries the DDA's own GIS geometry in WGS84,
retrieved from the Development Information System on 2026-10-01, with the source
lon and lat stored on every vertex.

| Check | Result |
|---|---|
| Plot area vs official 1,019.98 m² | 1,019.97 m², deviation **-0.001%** |
| Side 1, stated 33.80 m | 33.80 m, -0.00% |
| Side 2, stated 30.56 m | 30.56 m, -0.01% |
| Side 3, stated 33.13 m | 33.14 m, +0.02% |
| Side 4, stated 30.53 m | 30.53 m, +0.01% |

The GIS polygon reproduces every stated side length. This is the authority's own
published data, so it is good enough to design and model on.

It is still not the Demarcation Certificate, which remains the legally
authoritative document and should replace these values when issued. Replacing
them is a single edit to `boundary.vertices` in `brief/site.yaml`.

### OI-04 True north confirmation

| | |
|---|---|
| Status | **CLOSED 2026-10-01** |
| Raised | 2026-10-01, Phase 0 |
| Closed by | Two independent measurements, see below |

**Plan-up is true north. Confirmed.** Phase 1 can proceed on this.

Two independent confirmations, neither of them by eye:

1. **The north arrow on the DDA plot plan**, measured from the PDF vector
   geometry rather than from a rendered image. Its axis runs from apex
   (1149.236, 42.882) to tail notch (1149.236, 60.082) in PDF points. Identical
   x, so the axis is exactly vertical on the sheet: **0.000 degrees**.
2. **The DDA GIS polygon in WGS84**, compared edge by edge against the project
   coordinates. Mean bearing difference across all five edges is **-0.02
   degrees**, with a spread of 0.48 degrees, which is within the precision of
   the data.

| Edge | GIS bearing | Project bearing | Difference |
|---|---|---|---|
| E to A, road frontage | 30.18° | 30.38° | -0.20° |
| A to B | 120.78° | 120.59° | +0.19° |
| B to C | 211.15° | 211.03° | +0.13° |
| C to D | 209.83° | 210.12° | -0.29° |
| D to E | 299.53° | 299.45° | +0.09° |

A pytest check now guards this, so it cannot silently revert.

Note this is **true** north, not magnetic. Magnetic declination at Dubai is
roughly 2 degrees east and is irrelevant to solar geometry.

### OI-05 Roof terrace parapet and enclosure rules

| | |
|---|---|
| Status | **PARTLY CLOSED 2026-10-01** |
| Raised | 2026-10-01, Phase 0 |

**Parapet: answered.** DDA FAQs - Building Q34, "What is the minimum parapet and
balcony handrail height?", answer "1.2m from the floor finish level."
`brief/massing.yaml` previously assumed 1.10 m, below the minimum, and has been
corrected to 1.20 m. All shadow figures were recomputed.

**Roof enclosure: still open, and now looks riskier.** The FAQ does not address a
roof stair and lift enclosure, but Q27 rules that "When the gym is constructed on
the roof then it will be counted as an additional floor unless the master
developer allows it to be excluded." If that logic extends to a roof enclosure,
the enclosure could be read as an additional floor and breach the G+1 cap, not
merely add GFA. This connects OI-02 to the height question in OI-13.

Source: DDA FAQs - Building, retrieved 2026-10-01 from https://webzoning.dda.gov.ae/Zoning/Content/dda/FAQs.pdf

### OI-06 Exact site coordinates for sun studies

| | |
|---|---|
| Status | **CLOSED 2026-10-01** |
| Raised | 2026-10-01, Phase 0 |
| Closed by | Centroid of the DDA GIS plot polygon |

The site is at **24.897528 N, 54.964976 E**, Asia/Dubai.

The earlier assumption of 25.0 N, 55.1 E was **17.7 km** away from the real plot.
That sounds alarming and was not: the effect on solar geometry is about
**0.1 degrees** of sun altitude, which is immaterial at concept stage and far
below the uncertainty that OI-04 carried before it closed.

| Moment | Altitude, assumed | Altitude, real | Change |
|---|---|---|---|
| 21 Jun 12:00 | 84.88° | 84.79° | -0.09° |
| 21 Dec 12:00 | 41.39° | 41.48° | +0.09° |
| 21 Jun 16:00, west sun | 40.50° | 40.60° | +0.10° |

Corrected anyway, because the exact figure was available at no cost.

### OI-12 May a swimming pool sit within the 3 m setback?

| | |
|---|---|
| Status | OPEN |
| Raised | 2026-10-01, Phase 1 |
| Answered by | DDA regulations |
| Source needed | Document reference and clause number |

All three massing options keep the pool entirely inside the buildable envelope,
so **no option depends on the answer**. A yes would free roughly 90 to 100 m2 of
additional garden on the chosen side and would let the pool sit further from the
villa, which would change the shading balance. Worth asking, not blocking.

### OI-13 Overall building height in metres

| | |
|---|---|
| Status | OPEN, now with a cited figure to test against |
| Raised | 2026-10-01, Phase 1 |
| Answered by | The issued Site Plan and the Meraas development guideline |

DDA FAQs - Building Q29: "What is the maximum height allowed for building by
meter?" Answer: "Maximum height by meter allowed for buildings is calculated by
number of floors multiplied by 4.2. and this height is measured to the last point
of the project. **However in some developments the maximum height is not limited
to the equation above but to the number of floors.**"

For G+1 that gives **8.40 m to the last point of the project**. The DDA plot
details for 5130272 give only "G+1" with no metre figure, so it is genuinely
unclear which case applies.

| Case | Ground | First | Parapet | Overall | Option C pool shade, 21 Aug mean |
|---|---|---|---|---|---|
| As designed | 4.00 | 3.80 | 1.20 | **9.00 m** | 83% |
| Within the 8.40 m cap | 3.60 | 3.60 | 1.20 | **8.40 m** | 80% |

The stricter case costs 3 percentage points of afternoon shade, so it does not
change the design, and at 3.60 m floor to floor the clear height is still about
3.25 m against the 2.70 m minimum for livable space in Q33. Both cases are
carried in `brief/massing.yaml` under `height_scenarios`.

Related DDA figures now on record: ground floor clear height up to 6 m and
typical floors limited to 4.2 m (Q28); minimum clear height 2.7 m for livable
space and 2.4 m for corridors, kitchens and service rooms (Q33).

Source: DDA FAQs - Building, retrieved 2026-10-01 from https://webzoning.dda.gov.ae/Zoning/Content/dda/FAQs.pdf

### OI-14 Is a boundary wall permitted on this plot?

| | |
|---|---|
| Status | OPEN |
| Raised | 2026-10-01 |
| Answered by | The Meraas development guideline |

DDA FAQs - Building Q3: "Is Boundary wall allowed in all sites?" Answer: "Not
allowed unless the development guideline allow the boundary wall."

The Phase 1 boundary wall concept, decision D-011, assumes a wall is permitted.
That assumption now has a citation against it and needs the Meraas guideline to
confirm. If walls are not permitted, the privacy argument for the SSW and NNE
faces changes and the landscape design has to carry it instead.

Source: DDA FAQs - Building, retrieved 2026-10-01 from https://webzoning.dda.gov.ae/Zoning/Content/dda/FAQs.pdf

### OI-15 Air well for the enclosed Arabic kitchen

| | |
|---|---|
| Status | OPEN, affects Phase 2 |
| Raised | 2026-10-01 |

DDA FAQs - Building Q16: "All Kitchen must have natural source of light and
ventilation as per standard, In Case of closed kitchen air well of 3*3 meter is a
must."

CLAUDE.md section 4 puts the Arabic (dirty) kitchen behind the show kitchen with
service access, which makes it a closed kitchen. On this reading it needs a 3 x 3
m air well, 9 m2, which is not in the room program and would have to come out of
the floor plate. Confirm the reading before Phase 2 layouts.

Source: DDA FAQs - Building, retrieved 2026-10-01 from https://webzoning.dda.gov.ae/Zoning/Content/dda/FAQs.pdf

### OI-16 Dubai Civil Defence approval

| | |
|---|---|
| Status | OPEN, standing |
| Raised | 2026-10-01 |

DDA FAQs - Building Q42: "Is DCD approval mandatory for individual and community
villas and private/commercial villas?" Answer: "Yes, as per UAE life Safety code
2017 DCD approvals are mandatory."

Noted for the consultant handover package in Phase 8.

Source: DDA FAQs - Building, retrieved 2026-10-01 from https://webzoning.dda.gov.ae/Zoning/Content/dda/FAQs.pdf

## Owner decisions outstanding## Owner decisions outstanding

### OI-07 Pool and main garden position

| | |
|---|---|
| Status | **CLOSED 2026-10-01** |
| Decided by | Aiman |

**Option C, Courtyard, selected**, with the double height living room in the
single storey SSW wing. The pool sits in the courtyard, enclosed by the road wing
to the WNW and the single storey wing to the SSW, open to the NNE and ESE.

| Option | Summer afternoon shade | Winter midday sun | |
|---|---|---|---|
| A, Garden East | 93% | 100% | recommended on the numbers |
| B, Garden Southwest | 12% | 100% | rejected |
| **C, Courtyard** | **87%** | **78%** | **selected by owner** |

The owner weighed the 6 point shade difference and the loss of the view east
against a private courtyard and a double height living room that costs no upper
floor area, and chose C. All three options carry identical floor areas, so the
choice moved no GFA. See decision D-014.

### OI-08 Dining room size

| | |
|---|---|
| Status | PARTLY CLOSED |
| Raised | start of project |
| Updated | 2026-10-01 |

Position is now settled: the owner confirmed the dining room is on the ground
floor. Size remains at the indicative 22 m². Placement within the ground floor
is proposed at the Phase 2 checkpoint.

### OI-09 First floor stair and elevator landing, added by Claude

| | |
|---|---|
| Status | OPEN |
| Raised | 2026-10-01, Phase 0 |
| Worth | 20.00 m² |
| Decided by | Aiman |

CLAUDE.md section 4 itemises a 20 m² staircase and home elevator on the ground
floor but none on the first floor, while the brief also states the elevator
serves ground, first, and roof. A first floor landing is physically required, so
20 m² was added and flagged. It is included in the GFA figures above. Confirm the
allowance, or set a different one.

### OI-10 Room label wording, majlis or salon

| | |
|---|---|
| Status | OPEN, low priority |
| Decided by | Aiman |

The owner confirmed on 2026-10-01 that the majlis and the salon are the same
room. Drawings currently label it `Majlis (Salon)`. Confirm, or pick one word.

## Standing item

### OI-11 Consultant and structural engineer review

| | |
|---|---|
| Status | OPEN, by definition |

A DDA-registered consultant and a licensed structural engineer must review,
complete, and stamp all final drawings. This project produces concept design
only. Structural content is limited to an indicative column grid and slab zones,
labelled `INDICATIVE, BY LICENSED STRUCTURAL ENGINEER`.
