# Design decisions: Villa 5130272, Jebel Ali Hills

Every design decision and its reason. Newest first.

Columns: date, decision, reason, approved by Aiman.

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
