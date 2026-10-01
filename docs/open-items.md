# Open items: Villa 5130272, Jebel Ali Hills

Every item that is unresolved, unverified, or awaiting an authority answer.
Nothing here is a regulatory value invented by Claude. Each regulatory question
names the document that must answer it.

Status key: OPEN, ASKED (sent to a third party), CLOSED.

Last updated: 2026-10-01 (DDA published material checked, option C selected)

## Critical. Blocks Phase 2 room layouts

### OI-01 Does the enclosed garage count toward GFA?

| | |
|---|---|
| Status | **OPEN. DDA published material checked 2026-10-01 and does not answer it.** |
| Raised | 2026-10-01, Phase 0 |
| Worth | 55.00 m2 |
| Answered by | The issued Site Plan for plot 5130272, and the Meraas development guideline |
| Checked | DDA FAQs, 20 pages, and the Dubai Building Code objectives, 17 pages |

**What was checked.** Both documents were retrieved and parsed in full. The word
"garage" appears **zero times** in either. There is no published DDA rule on
whether an enclosed villa garage counts toward GFA.

**Where the answer actually lives.** DDA's own FAQ says so twice:

- "Where can I find the Planning Regulations for my Plot?" to which the answer is
  "You can find the regulations for your plot on the issued site plan, or you may
  log your enquiry through 'connect with us' under DDA website".
- "What are the Parking standards as per DDA?" to which the answer is "as
  mentioned in the site plan".

So this is plot-specific, and the Site Plan, which is also OI-03, answers it.

**One thing the FAQ does settle.** GFA and BUA are not the same measure in DDA's
usage. Q25: "Balconies are always excluded from GFA calculations, but included in
the BUA calculation." The 662.99 m2 cap on this plot is on **GFA**. A garage
could in principle sit in BUA but outside GFA, which is the outcome that would
suit this project.

**Pattern worth noting, not a conclusion.** Where the FAQ does address a space
that might be excluded, the phrasing is consistently "unless the master developer
allows it to be excluded", for the gym in Q26 and the roof gym in Q27, and
"Podium floors are only allowed if they are mentioned in the affection plan" in
Q32. The default in those answers is inclusion, with exclusion at the master
developer's discretion. That leans toward the garage counting unless Meraas's
guideline says otherwise. **It is an inference from adjacent rulings, not a rule
about garages, and must not be designed against.**

Impact is unchanged: if the garage counts, the program breaches the cap at both
ends of the room ranges. Until this is answered, no room layout can be finalised.

Source: DDA FAQs - Building, retrieved 2026-10-01 from https://webzoning.dda.gov.ae/Zoning/Content/dda/FAQs.pdf

### OI-02 Does the roof stair and elevator enclosure count toward GFA?

| | |
|---|---|
| Status | OPEN |
| Raised | 2026-10-01, Phase 0 |
| Worth | 20.00 m² |
| Answered by | DDA regulations and the Dubai Building Code |
| Source needed | Document reference and clause number |

Compounds OI-01. If both the garage and the roof enclosure count, the total
reaches 687.42 to 716.92 m², over the cap by 24 to 54 m².

## Important. Blocks Phase 1 or Phase 3

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
