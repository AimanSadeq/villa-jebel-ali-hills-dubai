# Assumptions: Villa 5130272, Jebel Ali Hills

Every number used in this project that is not taken directly from an authority
document. Each one states where it came from, what it affects, and how to change
it. No regulatory value appears here: those are in `docs/open-items.md` marked
`TO VERIFY` until a document and clause can be cited.

Last updated: 2026-10-01 (end of Phase 1)

## A-01 Net-to-gross factor, 1.18

| | |
|---|---|
| Value | 1.18 |
| Set in | `brief/site.yaml`, `targets.net_to_gross_factor` |
| Type | Engineering assumption |
| Affects | Every GFA figure in the project |

The room targets in CLAUDE.md section 4 are net internal areas. GFA is measured
to the outside face of external walls. The factor covers external and internal
walls, structure, and circulation not itemised in the room program.

1.18 is a typical figure for a villa of this size with a compact plan. It is not
a regulation and it is not derived from this design, because no plan exists yet.
From Phase 2 it will be replaced by the measured ratio of the actual plan, and
the GFA check will report both.

**Sensitivity.** Each 0.01 reduction frees roughly 5 m² of net room area. The
full range from 1.12 to 1.22 moves the house total from 581 m² to 634 m² at the
low end of the room ranges. `src/analysis/gfa_check.py` prints this table on
every run, because under the owner's maximise directive plan efficiency converts
directly into rooms.

## A-02 Garage and roof enclosure treated as already gross

| | |
|---|---|
| Set in | `src/analysis/gfa_check.py`, `ALREADY_GROSS` |
| Type | Measurement convention |

The 55 m² garage and 20 m² roof enclosure targets describe whole enclosed
footprints, not net internal areas, so A-01 is not applied to them. Applying it
would inflate the garage to 65 m² and overstate the case against the cap by
10 m². See decision D-007.

## A-03 Plot boundary coordinates: RETIRED 2026-10-01

No longer an assumption. `brief/site.yaml` carries the DDA Development
Information System's own WGS84 geometry, with the source lon and lat stored on
every vertex. Plot area deviation is -0.001% and every stated side length is
reproduced to within 0.02%.

The Demarcation Certificate is still the legally authoritative document, tracked
as OI-03, but the boundary is no longer a measurement scaled off a drawing.

## A-04 Plan-up is true north: RETIRED 2026-10-01

No longer an assumption. Verified twice over, see OI-04. The north arrow on the
DDA plan measures exactly 0.000 degrees from sheet vertical in the PDF vector
geometry, and the DDA GIS polygon bearings agree with the project coordinates to
a mean of -0.02 degrees across all five edges.

This was the highest-leverage unverified item in the project, because an error
would have invalidated Phase 1 rather than merely shifting a number. It is now
guarded by a pytest check.

## A-05 Site location: RETIRED 2026-10-01

No longer an assumption. The site is at 24.897528 N, 54.964976 E, from the
centroid of the DDA GIS polygon. The earlier 25.0 N, 55.1 E was 17.7 km away but
changed sun altitude by only about 0.1 degrees, so nothing computed before this
correction was materially wrong.

## A-06 First floor stair and elevator allowance, 20 m²

| | |
|---|---|
| Set in | `brief/program.yaml`, `first.stair_lift_first` |
| Type | Added by Claude, awaiting owner review |
| Tracked as | OI-09 |

Mirrors the ground floor allowance in CLAUDE.md section 4. The brief itemises the
stair and elevator on the ground floor only while stating the elevator serves
three levels, so a first floor landing is required. Itemised rather than hidden
inside A-01 so the owner can see and change it. See decision D-006.

## A-07 Design margin below the GFA cap, 9.99 m²

| | |
|---|---|
| Value | design target 653.00 m² against a cap of 662.99 m² |
| Set in | `brief/site.yaml`, `targets.design_target_gfa_m2` |
| Type | Risk allowance |

See decision D-005. A single parameter, released on request or once the
consultant confirms the measurement basis.

## A-08 Drawing conventions

| | |
|---|---|
| Set in | `src/drawings/site_plan.py` |
| Type | Drafting convention |

- Site plan at 1:200 on A2 landscape, true scale, so printed dimensions measure.
- Model space in metres. `$INSUNITS` is 6 and `$MEASUREMENT` is 1 in the DXF.
- The stock ezdxf dimension style carries a length factor of 100 for millimetre
  drawings. It is overridden to 1.0, otherwise a 30.48 m side annotates as
  "3048.11". Worth knowing before adding any further drawing script.
- Areas are shown in both m² and sq ft, at 1 m² = 10.763910416709722 sq ft.
- Every sheet carries `CONCEPT DESIGN, NOT FOR CONSTRUCTION`.

## A-10 Building heights for the massing study

| | |
|---|---|
| Set in | `brief/massing.yaml`, `heights` |
| Type | Engineering assumption, not a regulation |
| Tracked as | OI-13 |

4.00 m ground, 3.80 m first, 1.10 m parapet, 8.90 m overall. Typical for a Dubai
villa of this size, but not taken from any code. Every shadow figure in the
Phase 1 study scales with it: a taller mass shades more of the pool, a shorter
one less. The ranking of the options is unlikely to change, since it comes from
where the mass sits relative to the pool rather than from how tall it is, but the
percentages would move.

## A-11 Clear-sky irradiance as the design basis

| | |
|---|---|
| Set in | `src/analysis/sun_study.py` |
| Type | Modelling choice |

Ineichen clear-sky with the pvlib Linke turbidity climatology, Perez-Driesse
transposition to vertical surfaces, 15 minute steps through a full year. These
are modelled figures for comparing options, not measured site data, and they
describe the cloudless day rather than the average one. Measured or typical-year
data would change the absolute kWh/m2 but not the relative standing of the four
facades, which is what the design decisions rest on.

## A-12 The plot's building grid, bearing 30.18 degrees

| | |
|---|---|
| Set in | `brief/massing.yaml`, `grid.bearing_deg` |
| Type | Derived from the boundary |

The bearing of plot sides 1 and 3. The buildable envelope fills 98.7% of its own
bounding box in this frame, so the plot is very nearly a rectangle of
24.5 x 27.7 m once squared to it. All massing geometry is authored in this grid,
and plans are drawn in it, so the entrance and backyard read as front and back.

The largest rectangle that actually fits inside the envelope is 661.48 m2, a
little smaller than the 680.55 m2 bounding box. Laying blocks out against the
bounding box pushes them past the setback line, which `src/model/massing.py`
rejects.

## A-09 Room areas are indicative

The room targets in CLAUDE.md section 4 are described by the brief as net and
indicative. They are treated as a starting point, not as fixed requirements. No
room is cut or resized without the owner's approval, per working rule in
CLAUDE.md section 1. Where the brief gives a range, the GFA check reports both
ends rather than picking one.
