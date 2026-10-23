# CLAUDE.md: Villa 5130272, Jebel Ali Hills

This file is the project brief. Read it fully at the start of every session before doing any work.

## 1. Owner and working rules

The owner is Aiman Sadeq. He reviews every phase and personally supervises the MEP.

Working rules (mandatory):

1. Always ask for Aiman's approval before starting each phase and before any major design decision.
2. When something is unclear, ask questions one at a time until you are at least 95% sure. Never guess silently.
3. Never use em dashes in any text, labels, drawings, or UI. Use commas, colons, or parentheses.
4. In any UI (viewer, dashboards), use SVG icons only. Never use emoji or icon fonts.
5. Do not invent regulatory values. Any code requirement (Dubai Building Code, DEWA, Civil Defence, DDA) must cite its source document and clause, or be marked `TO VERIFY` in the output and listed in `docs/open-items.md`.
6. Commit to Git at the end of every working session with a clear message. Never rewrite history on `main`.
7. Log every design decision and its reason in `docs/decisions.md` (date, decision, reason, approved by Aiman: yes/no).
8. Every drawing and model export carries the stamp: `CONCEPT DESIGN, NOT FOR CONSTRUCTION`.
9. Whenever room sizes are shown (drawings, sketches, reports, schedules, viewer labels, chat), give width x length in metres, then the area in m2 and sq ft, and the room's clear height (on the label, or in a heights note on the same sheet). Aiman, 2026-10-02, D-045.

## 2. Site data (from DDA Plot Details, `reference/5130272_-_Plot_Details.pdf`)

| Item | Value |
|---|---|
| Plot number | 5130272 |
| Community / project | Saih Shuaib 1, Jebel Ali Hills |
| Master developer | Meraas Estates (L.L.C) |
| Authority | Dubai Development Authority (DDA) |
| Land use | Residential: villa |
| Plot area | 1,019.98 m² (10,978.97 sq ft) |
| Maximum GFA | 662.99 m² (7,136.36 sq ft) |
| Maximum coverage | N/A (not specified) |
| Maximum height | G+1 |
| Building setbacks | 3 m on all sides (sides 1 to 4) |
| Parking | Minimum one space |
| Design guidelines | Open design. No Meraas style rules beyond the plot requirements and GFA |

### Plot boundary

Five-sided plot. Side lengths from the plan:

- Side 1: 33.80 m, northwest, fronting an 18.30 m road (main access side)
- Side 4: 30.53 m, northeast, neighbour plot 5130271
- Side 3: two segments, 7.72 m and 25.41 m, east, facing landscape plot 5130274
- Side 2: 30.56 m, southwest, neighbour plot 5130123

Approximate vertex coordinates (metres, x = east, y = north, origin at the west vertex), scaled from the plan drawing. Shoelace area of this polygon is 1,020.27 m², within 0.03% of the official figure:

```
E (west)        ( 0.00,   0.00)
A (north)       (17.10,  29.17)
B (east)        (43.34,  13.66)
C (east bend)   (39.31,   6.96)
D (south)       (26.57, -15.00)
```

Rules for the boundary:

- Treat these coordinates as provisional. The plan states it is for illustration only; authoritative data comes from the Site Plan and Demarcation Certificate. Store the coordinates in `brief/site.yaml` so they can be replaced in one place when the certificate arrives.
- Assume plan-up is true north (north arrow on the DDA plan). Mark this `TO VERIFY`.
- Build the buildable envelope as the plot polygon offset inward by 3 m on every side.
- Location for sun studies: Jebel Ali Hills, Dubai, approx. 25.0 N, 55.1 E, timezone Asia/Dubai. Mark exact coordinates `TO VERIFY`.

## Redesign under way (2026-10-23, D-060)

The owner's handover `reference/owner/Owner_handover_2026-10-23.md` replaces the area target (section 3), the room program (section 4) and, pending his style images, the architectural style (section 5) below. Sections 3 to 5 stay as the record of the earlier design until the new brief is confirmed and written in. The owner's priority now is the look and feel; technical detail comes later. The hard GFA limit of 662.99 m² and every working rule in section 1 still apply.

## 3. Area targets and GFA control

- Target gross area: about 650 m² (7,000 sq ft). Hard limit: 662.99 m². Never exceed it.
- Double-height voids do not add upper-floor area. Show them separately.
- Track the enclosed 3-car garage (about 55 m²) as a separate line. Whether it counts toward GFA under DDA rules is `TO VERIFY`. Report the GFA total both with and without the garage.
- The roof stair and elevator enclosure must be tracked separately as well (`TO VERIFY` whether it counts).
- `src/analysis/gfa_check.py` must run on every model build and fail loudly if the limit is exceeded.
- The room targets below are net and indicative. If they do not fit within the limit, propose trims to Aiman at the checkpoint. Do not cut rooms on your own.

## 4. Room program

### Ground floor

| Space | Target (m²) | Notes |
|---|---|---|
| Entrance foyer | 20 | Double height |
| Living room | 45 | Double height, connects to garden and pool |
| Salon | 35 | Formal reception, close to entrance, with its own guest powder room. Always called the salon, never majlis (Aiman, 2026-10-02, D-047) |
| Guest powder room | 4 | Next to the salon |
| Guest bedroom, en-suite | 32 | Only bedroom on ground floor |
| Dining | 22 | Not specified by owner: propose placement at checkpoint 2 |
| Show kitchen | 25 | Open to dining or living |
| Arabic (dirty) kitchen | 15 | Behind show kitchen, service access |
| Pantry / storage | 6 | |
| Laundry | 8 | Near staff and service zone |
| Sunroom | 20 | Glazed, garden facing, sun-controlled |
| Home office | 14 | Quiet, near entrance |
| Maid's room with bathroom | 12 | In staff zone with separate entrance |
| Driver's room with bathroom | 12 | In staff zone, can open to outside or garage |
| MEP plant room | 8 | Water tanks, filtration, controls, low-current rack |
| Staircase + home elevator | 20 | Elevator serves ground, first, and roof |
| Garage, enclosed, 3 cars | 55 | Track separately for GFA |

### First floor

| Space | Target (m²) | Notes |
|---|---|---|
| Master suite | 70 to 80 | Excluding balcony. Must be much larger than other bedrooms (2.2 to 2.5 times) |
| Bedroom 2, en-suite | 30 to 35 | |
| Bedroom 3, en-suite | 30 to 35 | |
| Bedroom 4, en-suite | 30 to 35 | |
| Family living room | 35 | Acoustically separated from master suite |
| Linen and general storage | 6 | REMOVED by owner decision 2026-10-02 (D-050, FF4): linen in built-in cupboards |

Master suite contents: bedroom, private sitting area, his and hers walk-in wardrobes, large bathroom with bathtub and separate shower, coffee / kitchenette station, private balcony. Give it the best upstairs orientation, ideally toward the east landscape plot if the sun study supports it.

### Roof

- Roof terrace with stair and elevator access. Parapets and enclosure rules `TO VERIFY` against the Dubai Building Code.
- Space for VRF outdoor units, screened from the terrace.

### Outside

- Swimming pool, 10 x 4 m, with deck. REMOVED by owner decision 2026-10-02 (D-041): no pool.
- BBQ area with pergola: south corner of the back garden by the Arabic kitchen door (G1, D-055)
- Landscape and softscape: trees, palms, lawn, planting beds, hardscape paving, driveway
- Boundary walls and gates: D-011 wall approved (G3), TO VERIFY with Meraas (OI-14); car gate to the carport and pedestrian gate on the portal line (G4)
- Main garden: east, toward the landscape plot, a balanced garden with terrace, central lawn and planting beds (G2, D-055). No pool (D-041).

## 5. Architectural style

- Modern, after the owner's reference renders (sheets A-02-001 and A-02-101 in reference/owner/, answers F1 and F2, 2026-10-02): clean cubic volumes, warm split face stone on the entrance portal and the frames, beige render elsewhere, timber soffits and fins, large glass in slim dark frames, linear LED outlines. Replaces the earlier "minimalist white, white render".
- Must-rule (Aiman, 2026-10-02, D-033): open space maximization, meaning open-plan interiors. Shared spaces (foyer, stair hall, circulation, kitchen, dining, living, family hall) join with as few walls and corridors as possible. Private rooms (bedrooms, bathrooms, office, Arabic kitchen, staff, services) stay enclosed. The salon is open to the foyer, living room and dining by owner decision (D-046); the Arabic kitchen is walled with an open entrance from the island kitchen.
- Because large glass drives cooling loads in Dubai, use deep overhangs and recessed glazing on south and west faces. Report the solar exposure of each facade.
- Interior: propose three distinct palettes (flooring, walls, accents, fixtures). These become switchable options in the walkthrough.
- Drawings in English, metric units, with room areas shown in both m² and sq ft.

## 6. MEP scope

Aiman will supervise the MEP personally. Be thorough and transparent: show every assumption and every calculation.

- Cooling: VRF system. Room-by-room cooling load calculation (ASHRAE method, Dubai design conditions with source cited). Indoor unit selection per room, refrigerant pipe routes, condensate drainage, fresh air strategy.
- Electrical: load schedule, distribution boards, lighting circuits, power outlets, DEWA connection assumptions (cite the DEWA regulation used).
- Plumbing: water supply, storage tanks, pumps, hot water, whole-house water filtration.
- Drainage: soil, waste, and stormwater routes.
- Low current: smart home automation (lighting, AC, security), CCTV, access control, data network, intercom.
- Pool MEP: not required, no pool (D-041).
- Run clash detection between MEP, architecture, and the indicative structural grid (IfcOpenShell clash tools). Report every clash.

## 7. Structural boundary

Structural design is NOT in scope. Provide only an indicative column grid and slab zones for coordination, labelled `INDICATIVE, BY LICENSED STRUCTURAL ENGINEER`.

## 8. Tech stack

- Model generation: Python 3.12 + IfcOpenShell. The villa is generated from code. Aiman reviews and gives feedback; feedback becomes script changes.
- Single source of truth: `brief/program.yaml` and `brief/site.yaml`. Scripts read them; never hard-code room sizes in scripts.
- Viewer: Vite + Three.js + That Open Engine (`@thatopen/components`, `web-ifc`). Use Three.js WebGPURenderer where compatible; fall back to WebGL when a library requires it. Working output comes first.
- Drawings: `ezdxf` for DXF, rendered to PDF (ezdxf drawing add-on with matplotlib, or equivalent).
- Sun studies: `pvlib` (or equivalent) for sun positions.
- Renders: Blender with Bonsai, scripted where possible, Cycles with Intel oneAPI GPU.
- Free assets only, with licence recorded in `assets/LICENSES.md` (for example Poly Haven, CC0).
- Hardware: Windows laptop, Intel Core i7, 32 GB RAM, Intel Arc 140V GPU. Keep the viewer at a smooth frame rate: use instancing for plants, compressed textures, and level of detail.

## 9. Repository structure

```
villa-5130272/
  CLAUDE.md
  SETUP.md
  README.md
  reference/        DDA plot details and any authority documents
  brief/            program.yaml, site.yaml, palettes.yaml
  src/model/        site.py, architecture.py, mep.py, landscape.py, build_model.py
  src/analysis/     gfa_check.py, sun_study.py, cooling_load.py, electrical_load.py, clash_check.py
  src/drawings/     plans.py, elevations.py, sections.py, rcp.py, mep_layouts.py, schedules.py
  viewer/           Vite + Three.js + That Open walkthrough app
  renders/          Blender scripts and camera setups
  assets/           free 3D assets and LICENSES.md
  output/           ifc/, dxf/, pdf/, renders/, reports/
  docs/             decisions.md, open-items.md, assumptions.md
```

## 10. Deliverables

1. IFC model (architecture, MEP, landscape, furniture), IFC4.
2. Browser walkthrough:
   - First-person walking (W/A/S/D + mouse look) and orbit view
   - Day / night lighting toggle (night uses the light fixtures from the ceiling plans)
   - Switchable interior palettes (three options)
   - MEP layer toggles: HVAC, refrigerant, electrical, plumbing, drainage, low current
   - X-ray mode to see MEP through walls and ceilings
   - Floor plan mini-map and room labels with areas
   - Collision with walls, working stairs, elevator ride between levels
3. Drawing set in PDF and DXF:
   - Site plan with setbacks, plot dimensions, parking
   - Dimensioned floor plans (ground, first, roof)
   - Elevations (all sides) and at least two sections
   - Furniture layouts
   - Reflected ceiling plans (lighting, AC grilles, diffusers)
   - MEP layouts: HVAC, electrical (lighting and power), plumbing, drainage, low current
   - Door and window schedules
   - Room finishes schedule
4. Reports: GFA report, sun study, cooling load, electrical load, clash report.
5. Photo-realistic still renders (Blender): entrance, double-height living, salon, master suite, garden at sunset (no pool, D-041), aerial view.
6. Consultant handover package: IFC + DXF + PDF + reports + `docs/open-items.md`.

## 11. Phases and review checkpoints

Stop at the end of each phase, summarise what was done, show it, and wait for Aiman's approval before continuing.

| Phase | Work | Checkpoint shows |
|---|---|---|
| 0 | Repo setup, `brief/*.yaml` from this file, verify plot polygon and area | Site plan with buildable envelope and area check |
| 1 | Sun-path study, 2 to 3 massing options with pool and garden positions, boundary wall concept | Massing options in the viewer with sun data and a recommendation |
| 2 | Room layouts for the chosen massing, 2 plan options, GFA check | Plan options with areas in m² and sq ft |
| 3 | Full IFC architectural model: walls, slabs, openings, stairs, elevator, roof, pool | Model in the viewer (orbit) |
| 4 | Walkthrough features, furniture, landscape and softscape, three palettes | Live walkthrough on the laptop |
| 5 | MEP design and calculations, MEP in IFC, clash detection, X-ray mode | MEP layers in the viewer plus calculation reports |
| 6 | Full drawing set in PDF and DXF, schedules | Drawing set |
| 7 | Photo-realistic renders in Blender | Render images |
| 8 | Consultant handover package and open-items list | Final package |

## 12. Known open items (start of project)

- Demarcation Certificate coordinates (replace the scaled plot coordinates)
- True north confirmation
- Whether the enclosed garage and roof enclosure count toward GFA under DDA rules
- Roof terrace parapet and enclosure rules
- Dining room size and position (not specified by owner)
- A DDA-registered consultant and a licensed structural engineer must review, complete, and stamp all final drawings. This project produces concept design only.
