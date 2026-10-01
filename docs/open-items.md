# Open items: Villa 5130272, Jebel Ali Hills

Every item that is unresolved, unverified, or awaiting an authority answer.
Nothing here is a regulatory value invented by Claude. Each regulatory question
names the document that must answer it.

Status key: OPEN, ASKED (sent to a third party), CLOSED.

Last updated: 2026-10-01 (north and location verified against the DDA GIS)

## Critical. Blocks Phase 2 room layouts

### OI-01 Does the enclosed garage count toward GFA?

| | |
|---|---|
| Status | OPEN |
| Raised | 2026-10-01, Phase 0 |
| Worth | 55.00 m² |
| Answered by | DDA development control regulations for Saih Shuaib 1, via a DDA-registered consultant |
| Source needed | Document reference and clause number |

The DDA Plot Details give a maximum GFA of 662.99 m² but do not state how an
enclosed garage is treated. With the owner directive to maximise built-up area,
this is now the single most consequential unknown in the project.

Impact, from `output/reports/VJH-RPT-001_GFA_Check.txt`:

- If the garage is **excluded**: the house fits at 612.42 to 641.92 m², leaving
  21 to 51 m² of headroom to distribute.
- If the garage **counts**: the total reaches 667.42 to 696.92 m², which breaches
  the 662.99 m² cap **at both ends of the room ranges**, not only at the top.
  Trims of roughly 5 to 34 m² would be required, and more against the design
  target of 653.00 m².

Until this is answered, no room layout can be finalised.

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
| Status | OPEN |
| Raised | 2026-10-01, Phase 0 |
| Answered by | Dubai Building Code |
| Source needed | Clause reference for parapet height and roof enclosure extent |

Needed before the roof is modelled in Phase 3.

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

## Owner decisions outstanding

### OI-07 Pool and main garden position

| | |
|---|---|
| Status | OPEN, scheduled |
| Decided by | Aiman, at the Phase 1 checkpoint |

Not decided. At least two options to be tested with sun-path and shading
studies: east toward the landscape plot 5130274, and south or southwest. A
recommendation with reasons follows in Phase 1.

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
