# Villa 5130272, Jebel Ali Hills, Dubai

Concept design for a G+1 private villa on plot 5130272, Saih Shuaib 1, Jebel Ali
Hills, Dubai. The building is generated from code: Python and IfcOpenShell
produce the IFC model, ezdxf produces the drawings, and a Three.js walkthrough
renders the result in the browser.

**CONCEPT DESIGN, NOT FOR CONSTRUCTION.** A DDA-registered consultant and a
licensed structural engineer must review, complete, and stamp all final drawings.

| | |
|---|---|
| Plot | 5130272, Saih Shuaib 1, Jebel Ali Hills |
| Authority | Dubai Development Authority (DDA) |
| Plot area | 1,019.98 m² (10,978.97 sq ft) |
| Maximum GFA | 662.99 m² (7,136.36 sq ft) |
| Maximum height | G+1 |
| Setbacks | 3 m on all sides |
| Current phase | Redesign (D-060, D-061): the courtyard villa from the owner's handover of 2026-10-23, built end to end for his review; 504.22 m2 enclosed, 158.77 m2 inside the cap. The active brief is docs/current-approved-brief.md |

## Start here

- `CLAUDE.md` is the project brief. Read it first.
- `SETUP.md` is the laptop setup guide.
- `docs/open-items.md` is everything unresolved.
- `docs/decisions.md` is every design decision and its reason.
- `docs/assumptions.md` is every number not taken from an authority document.

## Running it

Python 3.12 is required. IfcOpenShell publishes no 3.13 or 3.14 wheels.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

| Command | Produces |
|---|---|
| `python src/model/site.py` | Plot area and side length check against the DDA figures |
| `python src/analysis/gfa_check.py` | GFA against the 662.99 m² cap, by scenario |
| `python src/analysis/gfa_check.py --strict` | Same, failing when unverified areas breach the cap |
| `python src/analysis/plan_feasibility.py` | Can the program be laid out inside the massing |
| `python src/analysis/trim_packages.py` | Cost trim packages against the plan geometry |
| `python src/model/layout_court.py` | The courtyard villa's plan (D-061), writes brief/layouts.yaml. The earlier generators (layout_gen.py, assemble_reference.py) stay for the record |
| `python assets/fetch_assets.py` then, in the Python 3.11 render environment of SETUP.md, `python renders/render_villa.py --all --device GPU --quality high` | The seven Blender renders with the real textures and skies, on the laptop's GPU (D-062). `--quality preview` for a quick check |
| `python src/analysis/geometry_validation.py` | The handover's acceptance tests as geometry, the areas and the measured garden: output/reports/geometry_validation.md and output/plans/floor_overlay.pdf |
| `python src/drawings/floor_plans.py` | Ground and first floor plans, A1 at 1:100 |
| `python src/drawings/site_plan.py` | Site plan DXF and PDF |
| `python src/analysis/sun_study.py` | Sun paths and facade solar exposure |
| `python src/model/massing.py` | Validates the options, shade scores, wall to boundary |
| `python src/analysis/massing_study.py` | Massing comparison and recommendation |
| `python src/drawings/massing_sheets.py` | Massing and sun study PDF sheets |
| `python src/drawings/option_c_wing.py` | Option C wing, indicative plan |
| `python src/model/export_massing.py` | Writes the viewer's data file |
| `python src/model/layout_gen.py` | Generates the room layout, brief/layouts.yaml |
| `python src/model/build_model.py` | GFA check, then the IFC model, validation, and the viewer's model data. The IFC and the plan PDF are generated, not committed: run this before the viewer |
| `python src/analysis/shade_check.py` | Afternoon shade on the garden from the planned footprint, VJH-RPT-008 (written when the pool was in scope) |
| `npm run dev --prefix viewer` | Massing viewer at http://localhost:5173 |
| (same server) | IFC model viewer and walkthrough at http://localhost:5173/model.html: walk, day and night, three palettes, real materials and sky. "Go to a room" in the Walkthrough panel sets you down in any room; `model.html?at=courtyard` (any room key of brief/layouts.yaml) opens the page already walking there |
| `python src/model/assemble_reference.py` | The owner's reference villa with his answers, writes brief/reference_plan.yaml (run before layout_gen) |
| `python src/drawings/sketch_12_floors.py` | Decision sketch VJH-SK-013, answer 12 on both floors with the door schedule (also sketch_12a.py, sketch_12_trims.py) |
| `python src/drawings/sketch_facade.py` | Facade elevations VJH-SK-017 from the IFC and brief/facade.yaml |
| `python src/drawings/sketch_palettes.py` | Interior palettes VJH-SK-018 from brief/palettes.yaml |
| `python src/drawings/sketch_garden.py` | Garden plan VJH-SK-019 from brief/garden.yaml |
| `python assets/fetch_assets.py` | Fetches the free CC0 textures and skies (Poly Haven) for the walkthrough and renders, writes assets/LICENSES.md |
| `python assets/make_standins.py` | Synthetic stand-in textures for testing without network |
| `python renders/render_villa.py --all --device GPU` | Blender Cycles renders of the six views, output/renders |
| `python src/model/export_twinmotion.py` | Twinmotion export: one IFC per palette with named materials and finish surfaces, placements and cameras, output/twinmotion (guide: docs/twinmotion-guide.md) |
| `python -m pytest -q` | Setback, GFA, shading, layout, doors, facade, palettes, garden, realism and render guards, 116 checks (2 expected failures on the GFA margin, FF6) |

## Where things live

```
brief/      site.yaml, program.yaml, palettes.yaml, facade.yaml, garden.yaml. Single source of truth.
assets/     manifest.yaml, fetch_assets.py, LICENSES.md (free CC0 assets, not committed)
reference/  DDA plot details and authority documents
src/model/      site geometry, architecture, MEP, landscape
src/analysis/   GFA, sun study, cooling load, electrical load, clash detection
src/drawings/   site plan, floor plans, elevations, sections, schedules
viewer/     Vite + Three.js + That Open walkthrough
renders/    Blender Cycles render pipeline, render_villa.py and furniture_bl.py
output/     ifc, dxf, pdf, renders, reports
docs/       decisions, open items, assumptions
tests/      automated checks
```

Room sizes and site values are never hard-coded in scripts. They live in
`brief/*.yaml` and the scripts read them. To change the plot boundary when the
Demarcation Certificate arrives, edit `boundary.vertices` in `brief/site.yaml`
and regenerate: nothing else needs touching.

## Phases

| Phase | Work | Status |
|---|---|---|
| 0 | Repo setup, brief files, plot and area verification | Complete, awaiting review |
| 1 | Sun study, massing options, garden position | Complete, approved |
| 2 | Room layouts, two plan options, GFA check | Approved, 656.47 m2, 6.52 inside the cap |
| 3 | Full IFC architectural model | Built floor by floor from the owner's reference and answers (D-044 to D-051) |
| 4 | Walkthrough, furniture, landscape, three palettes | Built (D-049 to D-056), in review |
| 5 | MEP design, calculations, clash detection | Not started |
| 6 | Drawing set in PDF and DXF, schedules | Not started |
| 7 | Photo-realistic renders in Blender | Pipeline built and brought forward (D-057); full quality renders on the laptop |
| 8 | Consultant handover package | Not started |

Each phase stops for the owner's approval before the next begins.

## Current output

| File | What |
|---|---|
| `output/pdf/VJH-SP-001_Site_Plan.pdf` | Site plan, A2 landscape, true 1:200 |
| `output/dxf/VJH-SP-001_Site_Plan.dxf` | Same, for AutoCAD |
| `output/reports/VJH-RPT-001_GFA_Check.txt` | GFA by scenario against the cap |
| `output/reports/VJH-RPT-002_Site_Check.txt` | Plot area and side lengths vs the DDA plan |
| `output/pdf/VJH-MA-001_Massing_Options.pdf` | Three massing options with cast shadows, plot up |
| `output/pdf/VJH-SS-001_Sun_Study.pdf` | Sun paths and solar exposure rose |
| `output/reports/VJH-RPT-003_Sun_Study.txt` | Facade solar exposure, am and pm split |
| `output/reports/VJH-RPT-004_Massing_Options.txt` | Option comparison and recommendation |
| `output/pdf/VJH-MA-002_Option_C_Wing.pdf` | Option C single storey wing, indicative layout, true 1:75 |
| `output/pdf/VJH-GA-001_Floor_Plans.pdf` | Ground and first floor plans, measured GFA, A1 at 1:100 |
