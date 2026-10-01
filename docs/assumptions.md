# Assumptions: Villa 5130272, Jebel Ali Hills

Every number used in this project that is not taken directly from an authority
document. Each one states where it came from, what it affects, and how to change
it. No regulatory value appears here: those are in `docs/open-items.md` marked
`TO VERIFY` until a document and clause can be cited.

Last updated: 2026-10-01 (end of Phase 0)

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

## A-03 Plot boundary coordinates

| | |
|---|---|
| Set in | `brief/site.yaml`, `boundary.vertices` |
| Type | Measured from a drawing, provisional |
| Tracked as | OI-03 |

Scaled from the DDA plot plan, which states it is for illustration only.

Quality of the fit, from `output/reports/VJH-RPT-002_Site_Check.txt`:

| Check | Result |
|---|---|
| Plot area vs official 1,019.98 m² | 1,020.27 m², deviation +0.029% |
| Side 1, stated 33.80 m | 33.81 m, +0.04% |
| Side 2, stated 30.56 m | 30.51 m, -0.16% |
| Side 3, stated 33.13 m | 33.21 m, +0.23% |
| Side 4, stated 30.53 m | 30.48 m, -0.16% |

Good enough for concept massing and the Phase 1 sun study. Not good enough for
construction. Replace with the Demarcation Certificate.

## A-04 Plan-up is true north

| | |
|---|---|
| Set in | `brief/site.yaml`, `orientation` |
| Type | Read from a drawing, provisional |
| Tracked as | OI-04 |

Taken from the north arrow on the DDA plan. Affects every sun study, all facade
solar exposure figures, the master suite orientation, and the pool and garden
recommendation. The highest-leverage unverified item in the project, because an
error here invalidates Phase 1 rather than merely shifting a number.

## A-05 Site location, 25.0 N, 55.1 E, Asia/Dubai

| | |
|---|---|
| Set in | `brief/site.yaml`, `location` |
| Type | Approximation |
| Tracked as | OI-06 |

Adequate for concept-stage sun paths. At this latitude a few kilometres of
positional error changes sun altitude by a negligible amount, far less than the
uncertainty in A-04. Refine once OI-03 closes.

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

## A-09 Room areas are indicative

The room targets in CLAUDE.md section 4 are described by the brief as net and
indicative. They are treated as a starting point, not as fixed requirements. No
room is cut or resized without the owner's approval, per working rule in
CLAUDE.md section 1. Where the brief gives a range, the GFA check reports both
ends rather than picking one.
