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
| Current phase | Phase 1 complete, awaiting owner review |

## Start here

- `CLAUDE.md` is the project brief. Read it first.
- `SETUP.md` is the laptop setup guide.
- `docs/open-items.md` is everything unresolved. **OI-01, whether the garage
  counts toward GFA, blocks Phase 2.**
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
| `python src/drawings/site_plan.py` | Site plan DXF and PDF |
| `python src/analysis/sun_study.py` | Sun paths and facade solar exposure |
| `python src/model/massing.py` | Validates the options, shade scores, wall to boundary |
| `python src/analysis/massing_study.py` | Massing comparison and recommendation |
| `python src/drawings/massing_sheets.py` | Massing and sun study PDF sheets |
| `python src/drawings/option_c_wing.py` | Option C wing, indicative plan |
| `python src/model/export_massing.py` | Writes the viewer's data file |
| `npm run dev --prefix viewer` | Massing viewer at http://localhost:5173 |
| `python -m pytest -q` | Setback, GFA, shading and orientation guards, 50 checks |

## Where things live

```
brief/      site.yaml, program.yaml, palettes.yaml. Single source of truth.
reference/  DDA plot details and authority documents
src/model/      site geometry, architecture, MEP, landscape
src/analysis/   GFA, sun study, cooling load, electrical load, clash detection
src/drawings/   site plan, floor plans, elevations, sections, schedules
viewer/     Vite + Three.js + That Open walkthrough (Phase 3)
renders/    Blender scripts and camera setups (Phase 7)
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
| 1 | Sun study, massing options, pool and garden position | Complete, awaiting review |
| 2 | Room layouts, two plan options, GFA check | Started, blocked by OI-20 |
| 3 | Full IFC architectural model | Not started |
| 4 | Walkthrough, furniture, landscape, three palettes | Not started |
| 5 | MEP design, calculations, clash detection | Not started |
| 6 | Drawing set in PDF and DXF, schedules | Not started |
| 7 | Photo-realistic renders in Blender | Not started |
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
