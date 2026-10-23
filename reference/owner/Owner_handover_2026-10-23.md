# CLAUDE CODE HANDOVER — Jebel Ali Hills Villa, Plot 5130272
**Date:** 2026-10-23  
**Status:** Owner-approved conceptual brief; geometric reconciliation required  
**Instruction:** Work from measured geometry, not from AI-generated marketing images. All drawings are CONCEPT DESIGN — NOT FOR CONSTRUCTION.

## 1. Immediate assignment
Fix the recurring first-floor defect: the previous AI images show an **open planted roof garden/terrace below Bedroom 3's ensuite**, directly above the **ground-floor guest suite and powder room**. The owner has explicitly rejected this. Extend the first-floor **enclosed floor plate** over the relevant ground-floor enclosed rooms, allocate the added space sensibly to Bedroom 3/its ensuite/wardrobe and circulation, and remove all roof planting/terrace from that specific zone. Do **not** fill the intentionally open courtyard or the double-height foyer. Produce a coordinated 2D ground floor and first floor **from the same geometric model**, then derive corresponding 3D views from that model. Verify actual overlap using polygon tests; a visually plausible render is not sufficient.

## 2. Project repository and source of truth
Repository: https://github.com/AimanSadeq/villa-jebel-ali-hills-dubai

Relevant files to inspect first:
- `CLAUDE.md` (repository workflow; some directives may be superseded)
- `brief/site.yaml` (plot and authority inputs)
- `brief/program.yaml` (may reflect OLD program)
- `docs/decisions.md` and `docs/ground-floor-decisions.md` (historical approvals; NOT all current)
- `reference/5130272_-_Plot_Details.pdf`
- `reference/owner/` and `src/model/assemble_reference.py` (historical reference-based model)
- `src/analysis/plan_feasibility.py`, existing IFC / geometry / drawing scripts, tests and reports

**Conflict warning:** As of this handover, `brief/site.yaml` still specifies a 653 m² GFA target and `docs/decisions.md` records a 3-car carport, four upstairs bedrooms in some historical schemes, a reference-based 645 m² scheme, and other older decisions. Those are superseded by the owner's decisions in this handover. Do not silently keep the old scheme or overwrite historical records. Record a new dated decision and update the active program/targets while retaining provenance.

## 3. Provisional site data (from project `brief/site.yaml`)
- Plot 5130272, Saih Shuaib 1, Jebel Ali Hills, Dubai.
- Area 1,019.98 m²; DDA Development Information System GIS coordinates, pending legal Demarcation Certificate.
- Local metre coordinates (x east, y north):
  - E (0.000, 0.000)
  - A (16.994, 29.217)
  - B (43.226, 13.591)
  - C (39.230, 6.980)
  - D (26.588, -15.063)
  - Polygon E→A→B→C→D→E.
- Road E–A: 33.80 m, northwest frontage, road width 18.30 m.
- A–B 30.53 m neighboring plot; B–C 7.72 m and C–D 25.41 m landscape adjacency; D–E 30.56 m neighboring plot.
- Recorded DDA conditions (RECONFIRM): G+1, 3 m setbacks all boundaries, max GFA 662.99 m². Inward-offset polygon area approximately 671.99 m², **not** a permission to build over that entire area.
- True north and GIS source are documented in `brief/site.yaml`.
- No Demarcation Certificate currently available. Treat regulatory compliance, gate/driveway rules, carport exclusion, and terrace/GFA treatment as TO VERIFY.

## 4. Current owner-approved architecture and program (overrides older repository decisions)
**Character:** Ultra-modern minimalist villa; clean white volumes, flat roofs, charcoal accents, refined proportions; street privacy, controlled glazing, larger garden/courtyard glazing, passive shading. No swimming pool. Target ~450–500 m² enclosed across G+1, optimize rather than fill the allowance. Regulatory GFA tracked separately.

**Ground floor:**
- Landscaped front arrival, **NO vehicle gate and NO pedestrian gate** (owner's latest instruction); still verify access rules and boundary treatments.
- Integrated **open** side-by-side carport for one large SUV and one standard car; provisional 6.5 × 6.0 m. Exact SUV dimensions to be provided later. Sheltered service access toward kitchen.
- Shared grand entrance; double-height foyer, straight floating statement staircase, lift.
- Majlis accessible from main foyer, with privacy separation.
- Open family sitting/dining/show kitchen with island; separate enclosed Arabic prep kitchen and pantry.
- Family living has **direct shaded-door access to private garden**.
- Guest bedroom with private accessible bath, accessed from foyer with privacy.
- Powder/guest WC, maid bedroom/bath, laundry, services, integrated storage.
- ~20–25 m² open-to-sky courtyard (target ~22 m², e.g. 4.5 × 5 m) with a statement tree and views from living/dining. No pool.

**First floor — EXACTLY three bedrooms:**
1. Master bedroom suite with **walk-in closet integrated into the master suite** and connected to bedroom/bathroom; private ensuite **shower only, no bathtub**; garden-facing master terrace where feasible.
2. Bedroom 2 with own ensuite and wardrobe.
3. Bedroom 3 with own ensuite and wardrobe.
- Family lounge/gallery with integrated flexible workspace, lift, stair, gallery overlooking double-height foyer.
- **NO fourth upstairs bedroom. NO linen room. NO unexplained first-floor planted roof garden.**
- Specifically, **NO open planted terrace/roof above the ground-floor guest suite and powder room**. Enclose and use this space as part of the first floor.
- Keep only intentional voids: courtyard open to sky and foyer double-height. A master private terrace may remain if its location is coherent and not the rejected roof garden.
- Tall ceilings primarily family living, dining and majlis; avoid excessive height elsewhere. Check floor-to-floor and stair compliance.

**Garden:** meaningful contiguous private landscape; direct access from family living. Earlier AI presentation boards claimed **12.0 × 20.0 m = 240 m²**. This was **invented/unverified**, and may not fit the actual polygon with the building and carport. Do not present these as measured dimensions. Calculate true contiguous garden polygon and dimensions from the actual coordinated geometry; if 240 m² cannot fit, report feasible alternatives and tradeoffs.

## 5. Root cause of failed previous attempts
Previous assistant repeatedly used image generation to redraw an attractive multi-panel brochure. Images independently hallucinated room outlines and reintroduced a planted void under Bedroom 3, even when text claimed the defect was fixed. Some renders had inconsistent area labels. **Do not regenerate brochure first.** Build deterministic architectural geometry, validate it, then render views from that geometry. Marketing images are not CAD, BIM, or measured plans.

## 6. Required implementation workflow
1. Inspect repository and existing geometry/model/drawing pipeline. Identify the most recent *usable* measured source, but do not assume the older 645 m² reference design satisfies the revised brief.
2. Create/update a machine-readable **current** program and owner decision record, with explicit superseded historical constraints. Avoid destructive rewriting of historical decisions.
3. Generate plot polygon and 3 m provisional setback polygon from `brief/site.yaml` using the existing pipeline or Shapely. Validate area and geometry.
4. Build a coherent ground-floor footprint and room polygons including the guest suite and powder room; first-floor footprint and room polygons must share one global coordinate system and wall alignment.
5. **Critical overlap test:** identify the union of ground-floor guest-suite and powder-room polygons (or their roofed footprint). Verify that the first-floor enclosed slab/rooms cover this designated region, except legitimate structural/edge adjustments. No `roof_garden`, `terrace`, `open_void`, or landscaped region may intersect the designated area. Ensure this is a tested geometric assertion, not only a note.
6. Enforce exactly three first-floor bedroom entities, each linked to its own bathroom; master walk-in closet is part of master suite; no linen-room entity. Preserve gallery, lift, stair and intended voids. Confirm stairs connect and doors/circulation work.
7. Compute net areas, enclosed gross areas, footprint, voids, courtyard, open carport, terrace and regulatory GFA as separate metrics. Do not claim carport/terrace exclusion without official verification.
8. Perform provisional carport and access study; exact SUV model pending. Verify stair dimensions, risers, goings, landings and floor-to-floor; flag code checks rather than assume compliance.
9. Calculate **actual** private garden polygon and minimum/maximum usable dimensions, accounting for five-sided boundaries and setback areas. State the method and assumptions. No unsupported 12 × 20 m claim.
10. Produce matching dimensioned **2D ground and first floor** with identical coordinate origin, north arrow, plot/setback boundaries, room labels, floor plates, openings and level-to-level overlay. Produce **3D exterior and interior views from the same model**, including front, garden, foyer/stair, family living, dining/courtyard, master suite. Use 3D modeling/rendering tools, not independent image hallucination.
11. Add automated geometry validation and a short QA report. Clearly distinguish PASS, FAIL, TO VERIFY. Include a before/after callout of the specific former roof-garden defect.

## 7. Non-negotiable acceptance tests
- [ ] The area over the ground-floor guest suite and powder room is **enclosed on first floor**, not a planted roof garden.
- [ ] First floor has **exactly 3 bedrooms** (master + 2) and **3 dedicated ensuite bathrooms**.
- [ ] Master has integrated walk-in closet and shower-only bathroom.
- [ ] **No linen room**, no fourth first-floor bedroom.
- [ ] Courtyard remains open to sky and foyer remains double-height; no accidental infill of these voids.
- [ ] No vehicle gate or pedestrian gate depicted; carport is open and integrated.
- [ ] Family living has direct access to private garden.
- [ ] Both floor plans geometrically align in one coordinate system; overlap/void assertions pass.
- [ ] Dimensions and area schedule derive from geometry, not labels typed onto an image.
- [ ] Garden area and dimensions are measured from geometry, with irregular shape reported honestly.
- [ ] All images/drawings match the same source model and carry **CONCEPT DESIGN — NOT FOR CONSTRUCTION**.
- [ ] Authority constraints, demarcation, carport treatment, SUV swept path and stair code checks explicitly marked pending as needed.

## 8. Suggested deliverables
- `docs/current-approved-brief.md` — superseding decision record with date and change log.
- Updated active program/configuration (preserve old values in history).
- `output/plans/ground_floor.pdf` and `output/plans/first_floor.pdf` (dimensioned conceptual plans).
- `output/plans/floor_overlay.pdf` highlighting vertical alignment and designated enclosed area above guest suite/powder.
- Source geometry/model file(s), ideally IFC or the repo's existing canonical model representation.
- `output/reports/geometry_validation.md` including tests, areas, garden dimensions and unresolved constraints.
- `output/renders/` for model-derived exterior and interior images.

## 9. Explicit instruction to Claude Code
**Start by inspecting the repository and reporting which existing model/files are reusable, which owner requirements conflict with old repo state, and your proposed geometric fix. Then implement and validate. Do not claim success based on a generated image alone. If the plot or spatial program cannot support all requirements, report the exact geometric conflict and propose the smallest viable adjustment for owner approval. Do not fabricate compliance or garden dimensions.**
