# Open items: Villa 5130272, Jebel Ali Hills

Every item that is unresolved, unverified, or awaiting an authority answer.
Nothing here is a regulatory value invented by Claude. Each regulatory question
names the document that must answer it.

Status key: OPEN, ASKED (sent to a third party), CLOSED.

Last updated: 2026-10-01 (end of Phase 0)

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
| Status | OPEN |
| Raised | 2026-10-01, Phase 0 |
| Answered by | Site Plan and Demarcation Certificate from the master developer |

The DDA plot plan states it is for illustration only. The boundary coordinates
in `brief/site.yaml` are scaled from that drawing. They are good: the computed
area is within 0.029% of the official 1,019.98 m², and all four side lengths are
within 0.23% of the stated figures. They are still provisional.

Replace the `boundary.vertices` block in `brief/site.yaml` when the certificate
arrives. Nothing else needs to change, and the full drawing and report set
regenerates from that one edit.

### OI-04 True north confirmation

| | |
|---|---|
| Status | OPEN |
| Raised | 2026-10-01, Phase 0 |
| Answered by | Site Plan |

Plan-up is assumed to be true north, from the north arrow on the DDA plan. Every
sun study, shading calculation, facade solar exposure figure, and the pool and
garden recommendation in Phase 1 depends on this. If it is wrong, Phase 1 is
wrong. Confirm before the Phase 1 checkpoint.

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
| Status | OPEN |
| Raised | 2026-10-01, Phase 0 |
| Answered by | Demarcation Certificate, follows from OI-03 |

`brief/site.yaml` carries 25.0 N, 55.1 E as an approximation. Adequate for
concept-stage sun paths, since a few kilometres of error moves sun altitude by a
negligible amount at this latitude, but it should be refined.

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
