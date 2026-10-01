# Design decisions: Villa 5130272, Jebel Ali Hills

Every design decision and its reason. Newest first.

Columns: date, decision, reason, approved by Aiman.

---

## 2026-10-01

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
