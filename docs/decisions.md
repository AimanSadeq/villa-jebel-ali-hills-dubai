# Design decisions: Villa 5130272, Jebel Ali Hills

Every design decision and its reason. Newest first.

Columns: date, decision, reason, approved by Aiman.

---

## 2026-10-23, Redesign from the owner's handover

### D-062 Image upgrades: the Twinmotion step list and the laptop render upgrade (answers U1, U2)

**Date.** 2026-10-23.

**Decision.** The owner found the first renders of the courtyard villa very basic. Two upgrades, both his choice: (1) docs/twinmotion-steps-courtyard-villa.md, the exact Twinmotion steps for this house (import, location and north, every material name with its library match and scale, 17 tree positions, the furniture that matters, the seven cameras with sun times), the photorealistic route he chose in D-059; (2) renders/render_villa.py upgraded for his laptop: quality presets with adaptive sampling and the OpenImageDenoise denoiser, the fetched Poly Haven sky as the visible dome with the physical sky lighting the scene, light portals at the garden glass and the courtyard, translucent foliage, depth of field indoors. The cloud sessions cannot reach the texture library, so the realistic renders are made on the laptop: `python assets/fetch_assets.py`, then `python renders/render_villa.py --all --device GPU --quality high`. The third option, an AI finishing prompt over the renders, stays available.

**Reason.** The owner's answers U1 (A, the Twinmotion list) and his instruction to do the render upgrade as well.

**Approved by Aiman.** Yes (U1: A; "now do the laptop render upgrade too").

### D-061 The courtyard villa: first design of the redesign built end to end

**Date.** 2026-10-23.

**Decision.** The redesign is built from the handover (D-060) and answers S1 to S7 as one geometric model, src/model/layout_court.py, through the existing pipeline: brief/layouts.yaml, the IFC model, the walkthrough data, the floor plans, the Twinmotion export and the Blender renders all come from it. The plan: an open courtyard of 4.50 x 4.60 m (20.7 m2) in the middle of the house between the double height foyer and the dining (S2); a straight floating stair in two flights along the courtyard's north glass, the upper flight in the foyer void, landing on a gallery bridge; the salon and the guest suite along the north, each off its own lobby; dining, family living and show kitchen along the garden with a continuous 20 m glazed face under deep eaves; the service row (corridor, maid's room and shower room, laundry, prep kitchen) behind the open two car carport in the south corner (S4), the plant room beside the carport; upstairs exactly three bedrooms with their own bathrooms, the master over the dining with its walk-in wardrobe, shower bathroom and covered terrace, bedroom 2 over the guest suite, bedroom 3 over the family living, the family lounge and workspace over the salon (S5). White minimalist facade (S1): white render, a charcoal stone box around the entrance, timber soffits under the eaves and the carport, timber fins on the hot windows, LED lines. No gates; walls to the neighbours and the landscape side stay (D-011, OI-14). Heights 5.00 and 4.00 m (S6). The full program is docs/current-approved-brief.md.
- Measured: 295.81 m2 ground and 208.41 m2 first, 504.22 m2 enclosed, 158.77 m2 inside the cap; the courtyard (20.70) and the voids (50.39) excluded; carport 38.91 and terrace 9.20 m2 outside GFA (D-039, TO VERIFY OI-01). The private garden east of the house measures 367.6 m2, 11.3 m deep and 23.1 m along the house, by polygon from the plan, in place of the earlier boards' unmeasured 12 x 20 m.
- The handover's acceptance tests are geometric assertions in src/model/layout_court.py, tests/test_layout.py and src/analysis/geometry_validation.py (output/reports/geometry_validation.md, output/plans/floor_overlay.pdf): the first floor covers 100% of the guest suite and the powder room with nothing open above them; three bedrooms and three bathrooms; no linen room; the courtyard and the foyer void kept; no gates; the living's garden door; both floors in one grid; everything behind the setbacks.
- Pipeline changes: the IFC generator builds a straight stair from the layout's stair block, fixed glass from the door schedule, courtyard paving with a planter, and windows for the halls that look out; the landscape builder takes open boundary sides and a courtyard tree; the facade spec no longer needs a pergola; the walkthrough's flood fill test keyed by height so a flight over a floor is not merged with it. The furniture leaves the desk out of bedrooms under 21 m2, which had sealed the guest bathroom's door.
- Known limits of this first design, for the owner: the salon does not see the courtyard; the guest bedroom and bedroom 2 are 19.8 m2; the stair's landing has 2.20 m headroom under the gallery (OI-23); the lift shaft 1.60 x 2.15 m is TO VERIFY with the supplier; the enclosed total is 4 m2 over the handover's 500 m2 figure.

**Reason.** The owner asked for the look and feel first (2026-10-23) and chose to wait for his images (S7: B), which arrived the same day; the design follows them as a built model rather than as pictures, so every later change is a change to one model.

**Approved by Aiman.** Pending: the first design is for his review.

### D-060 The owner's handover brief replaces the current design (answer H1: A)

**Date.** 2026-10-23.

**Decision.** The handover Aiman brought from his work with another assistant, kept as reference/owner/Owner_handover_2026-10-23.md, becomes the brief for a redesign. In short: about 450 to 500 m2 enclosed over G+1; exactly three bedrooms upstairs, each with its own bathroom, the master with an integrated walk-in wardrobe and a shower only; a family lounge with a workspace and a gallery over a double height foyer; a straight statement stair and a lift; an open courtyard of about 22 m2 with a tree; an open two car carport; no vehicle or pedestrian gate; no pool; enclosed rooms, not a roof garden, over the ground floor guest suite and powder room.
- Everything recorded before this entry stays as history: nothing is deleted, and the current model and drawings remain until the new design replaces them.
- Items that reverse rules Aiman gave earlier are confirmed with him before they are built: the name of the formal room (D-047, salon), and the facade character (D-048, D-051, his reference renders).
- Aiman's priority on 2026-10-23: the look and feel first, the technical detail later. He is sending the images he liked as the style reference.
- Checked the same day: the handover's roof garden over the guest suite and powder room was in the other assistant's images, not in this project's model. Polygon test: the 41.29 m2 of those rooms was 100% covered by enclosed first floor rooms, with 0.00 m2 under any terrace, balcony or void.

**Reason.** Owner's answer H1: A, 2026-10-23.

**Approved by Aiman.** Yes (H1: A).

---

## 2026-10-03, Phase 4: facade, palettes, furniture, garden, renders

### D-059 The realistic walkthrough in Twinmotion, from the project's IFC (answer W1: A)

**Date.** 2026-10-03.

**Decision.** The owner is not satisfied with the look of the browser walkthrough, and a browser walkthrough written here will not reach the look of his reference renders in a reasonable number of sessions (real time photo realism needs large libraries of detailed furniture, plants and materials and a mature rendering engine). The realistic walkthrough is therefore made in Twinmotion from the project's own model:
- src/model/export_twinmotion.py writes one IFC per interior palette (VJH-TM-001) with every element carrying a material named for what it is (the model build now gives every style a matching material), the palette's finishes as IfcCovering surfaces named per finish slot so each is swapped from the library in one click, and without the box furniture, sanitary ware, trees and room volumes that the library replaces; plus VJH-TM-001_placements.csv (every furniture piece and tree with position, size, rotation and the library kind) and VJH-TM-001_cameras.csv (the six views of deliverable 5 with the sun study's sun).
- docs/twinmotion-guide.md tells the owner how to install, import (collapse by material, north offset 30.18 degrees TO VERIFY against a shadow, Dubai location), assign materials, place the furniture and plants, and set the cameras and sun; and that design changes are made in the brief files and re-imported.
- The browser walkthrough (viewer/model.html) stays as the plan checking tool (reachability, labels, areas, palettes); the Blender pipeline stays for the Phase 7 stills.
- Twinmotion is a free Community Edition for personal, non-commercial use at the time of writing, TO VERIFY on its site; the laptop's integrated GPU may need reduced quality.
- Update 2026-10-05: the owner's Twinmotion 2026.2 import dialog offers no IFC file type. The export now also writes, per palette, the same model as `.glb` (binary glTF 2.0) and `.obj` with `.mtl`, tessellated from the palette IFC: y up, metres, one mesh per material with the same material names, UVs in metres so library textures keep their scale. The `.glb` is the file to import; the `.obj` is the fallback if the dialog does not list glTF. Checked by re-importing the GLB in Blender: 26 materials, the model at the plot coordinates.

**Reason.** Owner's answer W1 (2026-10-03), after the Phase 4 walkthrough fell short of "a complete realistic walkthrough" (F3). CLAUDE.md section 8 names the project's own stack for the walkthrough; the owner's instruction takes precedence for the realistic one, and the stack keeps the design, the checks and the deliverables.

**Approved by Aiman.** Yes (W1: A, 2026-10-03).

### D-058 Phase 4 independent review, findings fixed

**Date.** 2026-10-03.

**Decision.** Three read-only review lenses (fidelity to the owner's answers; model, walkthrough and render integrity; project rules) were run over the whole Phase 4 build and their findings fixed:
- Walkthrough: four first floor rooms (the dress rooms and bathrooms of bedrooms 2 and 4) had been sealed by a wardrobe or the bed standing across the open entry; open joins between touching rooms now keep a 1.0 m passage. Vanities now block the walker. The carport floor is its own level (0.30 m below the house). A flood fill test (tests/test_walk_reach.py) now proves every room and the garden reachable from the front door.
- Model: the first floor slab strip and a glass balustrade left across the portal opening are removed (the porch is open over its full height, D-051); a glass guard is added at the stair head on the first floor, leaving the flight's arrival open (1.20 m, DDA FAQs Building Q34, TO VERIFY for an internal edge); the front palms moved 0.6 m toward the road so no crown reaches the house, and the landscape build now refuses any tree whose crown would.
- Viewer: the entrance steps no longer disappear with real materials on; the BBQ furniture stays visible with a palette on; night with real materials off keeps the night sky; textures are cached.
- Renders: the BBQ furniture is rendered; shower screens are real glass; the stamp writer is mandatory (Pillow).
- Records: README, SETUP, CLAUDE.md and program.yaml describe the current pipeline and the decided garden; the generated IFC and plan PDF are no longer tracked (the committed copy was the ground floor only; the build makes them); OI-10 closed properly, OI-14 lists the assumed wall values, OI-28 and OI-29 say built; the master's coffee station shortfall (1.35 m against the 1.80 m of FF3) is on record in D-054 and OI-27.
- Left as found, told to the owner: facade cladding boxes overlap the parapet returns and slab edges by a few centimetres rather than trimming them (coplanar faces, visible only as flicker in the viewer); the roof hatch is not modelled (Phase 6 roof plan).

**Reason.** Owner's answer P11 (C): review before the Phase 4 checkpoint and the MEP.

**Approved by Aiman.** Pending, at the Phase 4 checkpoint.

### D-057 Photo-realistic renders brought forward (answer P9: A)

**Date.** 2026-10-03.

**Decision.** The Phase 7 renders start now, from the model as it stands. renders/render_villa.py builds the Blender scene from the project's own outputs and renders it with Cycles:
- the IFC model through IfcOpenShell, each element with its surface style mapped to the photographic materials of assets/manifest.yaml (box projected, so no UV work); window glass refractive to the eye and transparent to light, so the sun and sky light the rooms;
- the chosen palette's finishes, the furniture as softened pieces in the palette's colours, the garden surfaces, hedges, procedural palms and trees, and the land and road around the plot, all from viewer/public/data/model.json;
- a physical sky (Blender's Nishita model) with the sun at the sun study's position for the view (pvlib, brief/site.yaml), exposure calibrated from a preview;
- the six views of CLAUDE.md deliverable 5: entrance, double height living room, salon, master suite, garden at sunset, aerial. Output output/renders/VJH-R-00n_<view>.png, stamped.
Runs with Blender's Python module (pip install bpy, kept in its own environment) or inside Blender on the laptop with the Intel Arc GPU (--device GPU, oneAPI). Test renders at low quality were made in the cloud with stand-in textures; the real photographs and the full quality renders are made on the laptop.

**Stage 2 (answer P10: B, 2026-10-03).** The Blender route kept over Twinmotion. renders/furniture_bl.py builds every layout piece as modelled furniture in the palette's materials: beds with frame, mattress, pillows, duvet and bedside lamps; sofas and armchairs with cushions and legs; dining and desk chairs; tables; wardrobes, consoles and shelves with door lines and handles; kitchen runs with wall units, worktops and the island; vanities with basins, taps and mirror; WCs, showers with glass screens, the bathtub; rugs. Palms get a rachis with leaflets, trees branches with leaf clusters kept above head height. The walkthrough keeps the boxes (stage 2 there is not planned while the renders are the pictures). Review 2026-10-03: pieces now export their full plan extent, so wall hung vanities and rugs reach the builders too.

**Reason.** Owner's answer P9: the walkthrough looked unreal; photographs of the finished house can only come from path traced renders (CLAUDE.md deliverable 5, Phase 7), and the same model and materials feed them.

**Approved by Aiman.** Yes, the approach (P9: A, 2026-10-03).

### D-056 Real materials, sky and sun in the walkthrough (answer P7: A)

**Date.** 2026-10-03.

**Decision.** The walkthrough gets photographs of real materials, a real sky and a sun with shadows, from free CC0 assets (Poly Haven), as CLAUDE.md section 8 asks:
- assets/manifest.yaml lists every asset (skies, 19 material textures, and the stage 2 furniture and plant models) with preferred Poly Haven ids and a category and tag search as fallback; assets/fetch_assets.py downloads them on the laptop into viewer/public/assets/ (not committed, binaries) and writes assets/LICENSES.md and an index the viewer reads. The cloud sessions cannot reach polyhaven.com, so assets/make_standins.py makes synthetic stand-ins for testing the pipeline there.
- Each palette swatch in brief/palettes.yaml names its texture (limestone, travertine, marbles, oak, walnut, terrazzo, concrete, plaster, fabric, leather); the facade's stone, timber and render and the garden's lawn, soil, terrace stone and paving have theirs.
- The viewer (viewer/src/realism.ts): the sky as background and light (HDRI), filmic tone mapping, a sun casting shadows at the sun study's position (pvlib, brief/site.yaml: 21 March 15:00, azimuth 242, elevation 46; summer and winter afternoons exported too), the finishes and furniture in photographic materials with normal and roughness maps at their real scale, and a textured exterior layer for the facade parts, the garden surfaces and the hedges in place of their plain IFC copies. A "Real materials and sky" switch; without the fetched assets the viewer keeps its drawn textures and tells the owner what to run.
- Stage 2 (next): 3D models for the furniture, palms and trees in place of the boxes.

**Reason.** Owner's answer P7 (2026-10-03): the walkthrough looked unreal; the villa does not exist, so photographs of it cannot, and photographs of real materials with real light are the closest thing in an interactive view. Deliverable 2, CLAUDE.md section 8 (free assets, licences recorded, compressed textures, smooth frame rate).

**Approved by Aiman.** Yes, the approach (P7: A, 2026-10-03).

### D-055 The garden built (answers G1 to G4)

**Date.** 2026-10-03.

**Decision.** brief/garden.yaml holds the landscape; src/model/landscape.py builds it into the IFC, the walkthrough and sketch VJH-SK-019:
- G1: the BBQ area in the south corner of the back garden by the Arabic kitchen door G21: a paved BBQ terrace 6.11 x 6.69 m, 40.9 m2 (440 sq ft), an open timber pergola 4.00 x 3.60 m with 2.45 m clear under the beams, a 3.00 m BBQ counter and a table for six. Inside the 3 m setback line.
- G2: a balanced back garden: a 3.00 m paved terrace along the house linking G20, G21 and G22 (3.01 x 20.17 m, 60.7 m2, 653 sq ft); one 0.15 m step down to the lawn in front of the living room and dining (3.60 x 20.17 m, 72.6 m2, 782 sq ft); a planting bed along the landscape plot with three date palms, a ghaf and a sidr; a side path along the north wall round to the front; a paved service yard from the carport to the laundry and plant room doors and the BBQ terrace; planting strips in the setbacks.
- G3: the D-011 boundary wall, 2.40 m, solid to 1.20 m with a timber screen above on the road and landscape sides, solid against both neighbours. Whether a wall is allowed (DDA FAQ Q3) and its heights TO VERIFY (OI-14).
- G4: a sliding car gate into the carport (the carport's road edge, D-044 TO VERIFY) and a pedestrian gate on the line of the stone portal; a 1.50 m path, three steps up to the entrance court inside the portal at the porch level (2.95 x 3.09 m, 9.1 m2, 98 sq ft); front lawns with two date palms south of the path, a frangipani north of it (that lawn is only 3.8 m deep) and two date palms in the north west corner bed, a low hedge along the road wall (tree positions revised at the Phase 4 review, D-058, so no crown reaches the house).
- Levels: garden ground 0.45 m below the house floor (gate level, reference sheet A-09-001), terraces 0.15 m below, carport floor 0.30 m below. The walker follows them; beds, hedges, trees, the wall and the BBQ furniture stop it.
- Plants: indicative species common in UAE residential gardens, native where possible, for the landscape architect to confirm with the irrigation design (Phase 5). No regulatory value is assumed.

**Reason.** Owner's answers G1 to G4; CLAUDE.md section 4 (outside), deliverables 1 and 2.

**Approved by Aiman.** Yes (G1 to G4, 2026-10-03). The layout as built is for his review at the Phase 4 checkpoint.

### D-054 Furniture in every room (answer P5: A)

**Date.** 2026-10-03.

**Decision.** src/model/furniture.py furnishes every room by type: beds with bedside tables, a TV unit and a desk in the bedrooms; the master suite's king bed, private sitting group by the balcony and coffee station (FF3); wardrobe runs and the master's dressing island; showers, vanities, WCs and the master's bathtub and two basins; the living and family rooms' TV unit, sofa, coffee table and rug; a 12 seat dining table; the salon's two facing sofas, table, rug and console on the feature wall; kitchen runs and the island; the office desk and shelves; pantry shelves, laundry and the foyer console. Each piece is checked against the walls, door swings, the passages through open joins, windows and the other pieces, and left out (and reported) if it does not fit. In the IFC as IfcFurniture and IfcSanitaryTerminal; in the walkthrough coloured by the chosen palette, and the walker cannot pass through beds, sofas, tables and counters. Sizes indicative.

**Reason.** CLAUDE.md deliverables 1 and 2 (furniture in the IFC and the walkthrough); owner's answer P5.

**Shortfall told to the owner (review 2026-10-03).** The master's coffee station (FF3, 1.80 m on VJH-SK-015) is placed at 1.35 m: no free wall of the suite takes 1.80 m once the bed, the sitting group and the doors are in. The search now tries 1.80 m on every wall before shrinking; the length built is the one the layout report prints.

**Approved by Aiman.** Yes (P5: A; layouts P6: A, 2026-10-03).

### D-053 Palette 1 back to Sand and Oak

**Date.** 2026-10-03.

**Decision.** Palette 1 is Sand and Oak again, as first proposed on VJH-SK-018 (beige limestone look floors, warm white walls, travertine feature walls, light oak joinery, brushed brass), replacing White, Black and Beige (P2, P3). It is the walkthrough's default. White, Black and Beige stays in the git history if wanted later.

**Reason.** Owner's instruction, 2026-10-03.

**Approved by Aiman.** Yes.

### D-052 Three interior palettes in the walkthrough (answers P1 to P4)

**Date.** 2026-10-03.

**Decision.** brief/palettes.yaml holds the three palettes the owner approved on VJH-SK-018 Rev B:
1. White, Black and Beige (the owner's direction, replacing Sand and Oak, P2 C, P3 C): white walls and joinery, beige floors and soft furnishings, a black marble look feature wall, black worktops, matt black metal.
2. Marble and Walnut: white marble look floors, greige walls, walnut joinery and bedroom floors, champagne bronze.
3. Stone and Charcoal: grey terrazzo look floors, white walls, charcoal feature wall, smoked oak, matt black.

The model build exports every room's floor, wall faces (leaving doors, windows and open joins clear) and ceiling as finish surfaces tagged with a palette slot (src/model/finishes.py); the viewer colours them from the chosen palette and switches with one button (viewer/src/palettes.ts). Feature walls: both faces of the TV wall (12g) and the salon's long solid wall. Textures are drawn in the browser from the palette's pattern, so no image assets or licences are involved. Joinery, worktop, textile and fixture colours apply when the furniture is modelled. Visual concept finishes, not a specification.

**Reason.** CLAUDE.md section 5 and deliverable 2 (switchable interior palettes); owner's answers P1 to P4.

**Approved by Aiman.** Yes (P4: A, 2026-10-03).

### D-051 Facade built, after the owner's renders (answers R1 to R4)

**Date.** 2026-10-02.

**Decision.** The facade of sketch VJH-SK-017 is built in the IFC from brief/facade.yaml (src/model/facade.py, architecture.build_facade):
- Road side: a warm split face stone portal around the double height porch, 3.85 m wide outside, 2.95 m inside, from the ground to the parapet top (+10.20), timber soffit and LED.
- Garden side: a stone frame 2.55 m deep around the tall glass of the double height living room; its bottom band shades the living room glass 2.06 m deep.
- South face: eaves 1.50 m at the roof and 1.00 m over the ground floor, timber soffits.
- Carport columns clad in stone; projecting surrounds on the windows of the hot faces, vertical timber fins on the larger road side windows.
- An open timber louvred pergola, 6.00 x 9.41 m, over the garden frame, no roof access (R1, R2, D-017 stands), top +11.70 TO VERIFY (OI-28, OI-13). The maintenance roof hatch (R1) is not modelled; it belongs with the roof plan in Phase 6.
- Beige render replaces white on the walls (D-048); linear LED lines as in the renders.
- Model changes: the first floor wall across the road side of the porch removed (the porch opens to the road over its full double height); the 1.20 m parapet on the 0.49 m ledge in front of the living room's tall glass removed inside the frame (TO VERIFY, OI-29); bedroom 4's balcony starts at v 24.12, 0.70 x 2.00 m shorter.
- GFA measured from the plan 659.98 m2, margin 3.01 m2 (was 660.82 m2, 2.17 m2): the removed wall over the porch (3.39 x 0.25 m) no longer counts. IFC check 659.94 m2.

**Reason.** Owner's answers F1, F2 (the renders' design language), R1 to R4; the brief's deep overhangs and recessed glazing on the south and west faces (CLAUDE.md section 5), the road face taking the most afternoon sun (VJH-RPT-003).

**Approved by Aiman.** Yes (R4: A, 2026-10-02).

### D-050 First floor built (answers FF1 to FF8)

**Date.** 2026-10-02.

**Decision.** The first floor is the reference first floor adjusted by the owner's answers (docs/first-floor-decisions.md):
- FF2, FF3: the master suite keeps its walls (75.3 m2, 811 sq ft, clear height 3.55 m) and fits the brief's contents as on VJH-SK-015.
- FF4: no separate linen store; linen goes into built-in cupboards. brief/program.yaml lists linen_storage as removed. A departure from the brief, the owner's decision.
- FF5: the family room opens onto the gallery, door F13 retired: one open room of 4.99 x 5.25 m plus the 1.49 x 5.04 m gallery, about 33.7 m2 (363 sq ft), clear height 3.55 m.
- FF6: no further GFA trims; the owner accepts the thin margin.
- FF7: the first floor wall over the TV wall lines up with it; bedroom 4 is 4.35 x 5.50 m, 23.9 m2 (257 sq ft), clear height 3.55 m.
- GFA measured from the plan 660.82 m2, margin 2.17 m2 to the 662.99 m2 cap (IFC check 660.79 m2).

**Reason.** Owner's answers FF1 to FF8; D-033 (shared spaces open).

**Approved by Aiman.** Yes (FF8: A, 2026-10-02).

### D-049 Walkthrough engine, first version

**Date.** 2026-10-02.

**Decision.** The first person walkthrough is built into the existing viewer (viewer/model.html, viewer/src/walk.ts), driven by data the model build exports (walk_data in src/model/architecture.py, published in viewer/public/data/model.json):
- Walkable zones per level: the rooms, halls, open joins and door openings, the balconies, and the plot outside at ground level; the stair as two ramps and a flat landing; the void edges and walls are not walkable, so walls, glass and balustrades stop the walker (0.20 m clearance, eye height 1.60 m, steps up to 0.45 m).
- Under the stair a person stands only where the flight is at least 2.0 m up.
- The lift rides between the ground and first floors (E key or the panel button).
- Doors are shown open while walking (the leaves hide).
- Day and night: at night the sun and sky dim and warm lights come on in the rooms near the walker. These are interim fixtures, one per room under its ceiling, until the reflected ceiling plans (Phase 6) place the real ones.
- A mini-map of the current floor and a readout of the room with its size, area and clear height (rule 9).
Materials, furniture, landscape and the three palettes follow; the facade after the first floor design (F4).

**Reason.** Owner answers F3 (interactive browser walkthrough) and F4 (A: walkthrough now). CLAUDE.md deliverable 2.

**Approved by Aiman.** Yes for the phase (F3, F4); the engine's details are reviewed in the walkthrough.

## 2026-10-02, the ground floor built from the reference

### D-048 Facade after the owner's reference renders

**Date.** 2026-10-02.

**Decision.** The facade follows the reference set's renders, sheets A-02-001 (road side) and A-02-101 (rear) in reference/owner/: warm split face stone on the entrance portal and the frames, beige render elsewhere, timber soffits and fins, large glass in slim dark frames, linear LED outlines. CLAUDE.md section 5 updated; it replaces "minimalist white, white render". Not yet modelled; the facade and the walkthrough are the next work (docs/facade-and-walkthrough-decisions.md).

**Reason.** Aiman: "I also want the facade to be like the file I attached with villa architecture. Modern design." Answers F1 (A, those renders) and F2 (A, their materials). Nothing is copied from the consultant's drawings; the facade will be generated by this project's scripts.

**Approved by Aiman.** Yes (answers F1 and F2).

### D-047 The room is the salon, never majlis

**Date.** 2026-10-02.

**Decision.** The formal reception room is called the salon everywhere: program key `salon`, labels, the IFC model, drawings, the viewer, CLAUDE.md. Earlier entries in this log keep the old word as history.

**Reason.** Aiman: "do not use majlis, use always salon." Closes OI-10.

**Approved by Aiman.** Yes (his instruction).

### D-046 Ground floor answer 12 built, with first floor trim 12l

**Date.** 2026-10-02.

**Decision.** The owner's answers 12 and 12a to 12m (docs/ground-floor-decisions.md), drawn on sketches VJH-SK-013 and VJH-SK-014 and built (commits 6eb501d, 33d110c and the review fixes that follow):
- The salon takes the lawn court's place, 5.95 x 7.50 m = 44.6 m2 (480 sq ft), clear height 4.55 m, lined up with the dining and open to the foyer, the living room and the dining (12, 12c, 12d, 12e, 12h). The lawn court is removed. This departs from D-033 (the salon was an enclosed private room) and replaces D-042 (closed off, double doors) and the lawn court of D-040, by the owner's decisions.
- Along the backyard (12a B): island kitchen 4.10 x 6.00 m = 24.6 m2 (265 sq ft); living room 6.00 x 7.10 m = 42.6 m2 (459 sq ft), double height, 8.55 m clear under the void (about 68% of it; 4.55 m under the corridor strip); dining 3.75 x 5.85 m = 21.9 m2 (236 sq ft), 4.55 m. About half the island kitchen (11.8 of 24.6 m2) is under the void and 8.55 m clear.
- A solid TV wall, 0.15 m, 3.75 m long, between the living room and the dining, with 2.25 m open from the living room to the salon (12g): a departure from D-033 by the owner's decision.
- The Arabic kitchen walled, entered from the island kitchen by a 1.20 m opening with no door (12m).
- Doors: the schedule in src/model/doors.py, G01 to G23 and F01 to F15 (G06, F10, F11 retired). Front door G01 a 2.40 x 4.50 m pivot door at the back of the porch with glass above (12i; the porch stays outside GFA); garden doors 3.00 x 3.00 m sliding from the living room (G20) and the dining (G22), a 1.00 x 2.40 m door from the Arabic kitchen (G21) (12j, 12k); guest bedroom door from the foyer (12f).
- First floor (placeholder, D-038): the family room above the salon, 4.99 x 5.25 m = 26.2 m2 (282 sq ft), 3.55 m (12b); the reference family lounge, pantry, linen store and family balcony become the void over the living room and the island kitchen, 4.21 x 9.70 m = 40.8 m2 (12, 12l).
- Build fixes found on the way: the 6322806 model had no entry door to any bedroom (the door check counted a link to the room's own WC); the layout now refuses a plan where any room has no way in. Glass balustrades, 1.20 m (DDA FAQs Building Q34; use on an internal void edge TO VERIFY), on every open void edge. A pier 0.20 x 0.26 m left at the salon corner removed.

**Result, measured: 661.69 m2 (7,122 sq ft) GFA, 1.30 m2 inside the 662.99 m2 cap** (ground 355.58, first 306.11 less voids 80.87). If DDA counts the carport (77.35 m2): 739.04 m2, over the cap (OI-01). The D-005 reserve (not approved) is not held; tests/test_layout.py carries the reserve and the 5 m2 floor as strict expected failures until the first floor design restores them (OI-27).

**Not asked for, told to the owner:** full height fixed glass on the first floor face of the living room void; fixed glass either side of the garden and balcony doors; the guest bedroom lost its window onto the old lawn court; the salon has one north window; the guest powder room is about 12 m from the salon (the brief says next to it); the covered rear balcony of the reference family lounge went with 12l, so the living room glass has no overhang (the facade work, D-048, takes this up).

**Reason.** The owner's answers 12 to 12m; "Build" (2026-10-02).

**Approved by Aiman.** Yes: each answer, and "Build".

### D-045 Room sizes always shown as width x length, area and height

**Date.** 2026-10-02.

**Decision.** Anywhere room measurements are shown, they read width x length (metres), area in m2 and sq ft, and clear height. Heights are the indicative D-030 values from brief/massing.yaml: ground floor 5.00 m floor to floor, 4.55 m clear; first floor 4.00 m, 3.55 m clear; double height 8.55 m clear; carport 3.30 m clear (reference levels, sheet A-09-001). Clear height is floor to floor less the 0.30 m slab and the 0.15 m services zone, both indicative.

**Reason.** Aiman: "Anytime you're showing the measurements of rooms ... show me the width multiplied by the length and also show the height somewhere." Applied first on sketch VJH-SK-013; added to CLAUDE.md working rule 9. The formal floor plans (src/drawings/floor_plans.py) take it at the next build.

**Approved by Aiman.** Yes (his instruction).

### D-044 Ground floor built: the reference villa, mirrored, with the owner's answers

**Decision.** The ground floor is built from a measured transcription of the
owner's reference set (sheet A-07-001; three independent readings, reconciled
and checked, filed in reference/owner/transcription/), placed facing our road
and mirrored so the carport takes the south end (answer 7). The owner's answers
are applied as an explicit table in src/model/assemble_reference.py: formal
lounge to majlis, closed off from the dining by a wall with 1.6 m double doors
by the foyer (D-042, the 0.15 m wall taken from the dining); driver's room to
plant room and driver's toilet to outdoor bathroom opening onto the carport
(D-043); no pool (D-041); 3 car open carport and lawn court kept (D-040). Room
sizes are the reference's (answer 6); program.yaml targets follow them, each
with its earlier figure on record, and the route B trims on those rooms are
marked superseded. The first floor is the reference's, a PLACEHOLDER until the
owner decides it, trimmed 0.6 m where its bedroom wing would cross the north
setback line.

**Result, measured: 645.07 m2 GFA, 17.92 m2 inside the cap**
(ground 324.37, first floor placeholder 320.70).
Outside GFA by D-039, TO VERIFY: carport 77.35 m2, the open
lawn court 27.47 m2, the open entrance porch, and the first
floor's balconies and terrace 104.11 m2. The
IFC model measures back to the plan within 0.03 m2.

**Placement.** The reference's carport and porch stand forward of the main front
wall; to keep them on the plot the main front wall sits 0.8 m behind our 3 m
setback line and the carport roof reaches to within about 0.3 m of the road
boundary (TO VERIFY, as in the reference). Along the road the ground floor has
0.39 m to spare inside the side setbacks, measured at its full depth
(the side setback lines are not square to the road; the 0.8 m first reported
in VJH-RF-001 was the bounding box, corrected). The rear garden is about 9.2 m
deep to the boundary.

**Flagged, not changed:** the stair room as transcribed is 4.80 m long, where
the reference's stated 300 mm treads and 1.5 m landing need 5.45 m; the model
fits the going to the room (253 mm), OI-23. Three circulation spaces are
narrower than the owner's 1.80 m: the service passage 1.0 m and the stair hall
1.5 m on the ground floor, and two 1.5 m corridors on the first floor
placeholder, OI-26.

The interiors planner's en-suite and master suite layouts (D-034, D-035) give
way where the reference draws its own dress rooms and toilets.

**Approved by Aiman: yes,** the instruction to build ("build", 2026-10-02) and
every answer applied. The flagged items: for review.

---

## 2026-10-02, restart from the ground floor on the owner's reference

### D-043 Plant room and outdoor bathroom in the old driver's slot by the carport

**Decision.** The reference villa's driver's room and toilet, at the back of
the carport, become the MEP plant room (about 2.8 x 2.4 m, 6.7 m2) and the
outdoor bathroom (WC and shower, about 1.5 x 2.4 m), the bathroom opening onto
the carport. Neither has a door into the house.

**Reason.** Owner answers 2026-10-02 to ground floor questions 9, 11 and 11a:
the plant room in the driver's slot; the outdoor bathroom "attached to the
carport", replacing the garden side placement first chosen; the slot split
between them rather than a new block. No GFA beyond the reference. The plant
room is 0.3 m2 under its 7 m2 target; to be confirmed in the MEP phase.

**Approved by Aiman: yes.**

### D-042 Majlis inside the house, entered from the main door, closed off from the dining

**Decision.** The majlis is the reference villa's formal lounge, at the end of
the long garden room. Guests come in through the main door and the foyer;
there is no separate majlis entrance. Unlike the reference, where the lounge
is open to the dining, a wall with wide double doors separates the majlis
from the dining, the doors placed by the foyer so guests step in after about
2 m. The powder room stays off the foyer by the stair, as in the reference.

**Reason.** Owner answers 2026-10-02 to ground floor questions 10 and 10a.
Claude had described the lounge in question 5 as beside the garden room; the
reference sheet shows it as the fourth zone of the same open room. The owner
was told and chose to close it off. It keeps the open-plan rule (D-033), under
which the majlis is a private room.

**Approved by Aiman: yes.**

### D-041 No swimming pool

**Decision.** The villa has no swimming pool. CLAUDE.md section 4 asked for a
10 x 4 m pool with a deck and a BBQ by the pool; the pool is removed from the
program and kept on record under `removed:` in brief/program.yaml. The BBQ and
pergola stay in the brief and are placed with the garden later. Pool MEP
(CLAUDE.md section 6) and the pool at sunset render (section 10) fall away.

**Reason.** Owner decision 2026-10-02, replacing his answer 8 (one 10 x 4 m
pool, no kids' pool) a few minutes earlier: "You know what? I don't need a
pool." Pools are not GFA, so no area changes.

**Approved by Aiman: yes.**

### D-040 Ground floor, answer 3: no driver's room, 3 car carport, lawn court

**Decision.** From the reference villa the owner keeps the open 3 car carport
(reversing the two car part of D-026) and the internal lawn court open to the
sky; he does not keep the driver's room (D-028 stands). A bathroom reachable
from outside is a must (the outdoor bathroom of D-028 stays). The MEP plant
room (8 m2), absent from the reference, is added. The carport and the lawn
court are designed as outside GFA under D-039, both TO VERIFY. Answer 4: no
separate double height living room; the garden room stays as the reference
draws it and the double height stays in the entrance foyer. Answer 5: the
garden room keeps its full 17.2 m, island kitchen, sitting area and dining
for 12, so the sitting area is kept after all.

**Reason.** Owner answers 2026-10-02 to ground floor questions 3 to 5 in
docs/ground-floor-decisions.md.

**Approved by Aiman: yes.**

### D-039 Carport and balconies designed as outside GFA, TO VERIFY

**Decision.** The design proceeds on the reading in the owner's reference
set: GFA is usable rooms plus circulation; the car parking, balconies,
pergolas and roof terraces are outside it. This reverses D-026's safe
reading that the garage counts. It stays TO VERIFY with DDA (OI-01) and must
be confirmed before the Phase 6 drawing set.

**Reason.** Owner choice 2026-10-02 from three options. On the reference
set's own DDA area sheet (A-03-001, Paradise Home Engineering Consultancy,
plot 5131627, same community, July 2025) a registered consultant shows the 83
m2 car parking outside GFA. Under D-026 the reference plan would be about 53
m2 over our cap on this plot; under this reading about 30 m2 under. The
risk, accepted by the owner: if DDA counts the carport, about 53 m2 must be
trimmed later.

**Approved by Aiman: yes.**

### D-038 Design restarted floor by floor on the owner's reference villa

**Decision.** All generated plans (D-026 to D-037) are set aside. The design
restarts one floor at a time, the ground floor first, with the owner deciding
each question in turn (docs/ground-floor-decisions.md). The owner supplied a
consultant's preliminary set for plot 5131627 (reference/owner/) as the
design he likes; its ground floor becomes the basis, placed with its front to
our road (side 1), and adapted to our plot and brief question by question.
Answer 1 before the reference arrived: a single block along the road with
the garden east, which the reference also is.

**Reason.** Owner instruction 2026-10-02: "I don't like the setup. Let's
start from the beginning." Three generated plans had not matched what he had
in mind. The reference footprint, 26.9 m along the road by 17.5 m deep, fits
our envelope facing the road with 0.8 m spare along the road and a 10.1 m
rear garden toward the landscape plot (VJH-RF-001). Its section is 5.00 m
floor to floor on both floors, matching the owner's D-030 ground floor.

**Approved by Aiman: yes.**

---

## 2026-10-02, central hall ground floor

### D-037 Pool moved north onto the living room's deck

**Decision.** The pool keeps its Phase 1 orientation and east west position
(u 18.50 to 22.50, 10 m along the plot's long axis) and moves north so that
its deck starts at the living room's north wall: pool v 19.45 to 29.45, deck
to v 30.45, 2 m each side. The deck stays inside the buildable envelope, so
the pool setback question (OI-12) no longer arises for this position.

**Reason.** Follows from D-036: the tall living block now stands where the
Phase 1 pool was, and the owner wants the living room opening onto the pool.
The afternoon shade on the deck must be re-checked against the real footprint
and the 10.20 m height, as promised at the start of Phase 3. An east west pool
across the living room's frontage was considered and can be offered if the
shade check favours it.

**Shade check, same day (VJH-RPT-008, src/analysis/shade_check.py).** On the
planned footprint at the D-030 heights, the deck in this position is in the
villa's shadow for 92.0 % of the summer afternoon hours (15:00 to 18:00, June
and August), against 88.0 % estimated for option C's blocks in Phase 1, and
gets 58 % winter midday sun. The east west alternative across the living
room's frontage scores 93.8 % and 56 %: no better in any way that matters, so
the Phase 1 orientation is kept. At 15:00 in June about a third of the deck is
still in sun; a pergola at the BBQ end (CLAUDE.md section 4) would cover it.

**Approved by Aiman: no,** Claude's consequence of D-036, for review.

### D-036 Central hall ground floor

**Decision.** The ground floor is replanned as a central hall villa. From the
front door on the road: a big hall across the full width of the wing (11.40 x
3.50 m, 39.9 m2, against a 19 m2 program target), the stair open to it; the
majlis north of the hall (on the left when entering) with its powder room at
the road end, both opening off the hall; the dining south of the hall (on the
right) reached along a 1.80 m entrance gallery that it opens onto, with the
pantry at its south end; the double height living room straight ahead, a 7.50
x 6.00 m block 9.00 m tall standing in the courtyard with nothing above it,
open to the hall through a 3.50 m wide join and glazed north to the pool and
east to the landscape plot; the show kitchen beyond the dining in the SSW wing,
open to it across 3.3 m of wall, with the Arabic kitchen behind it at the
south end and its service door on the south face. The guest bedroom takes the
road side of the south end, the office sits beside the stair off the gallery.
The garage, the staff strip and the whole first floor are unchanged, and the
master terrace stays on the kitchen roof.

**Reason.** Owner instruction 2026-10-02: the earlier plan was not an open
area design; the owner asked for the salon on the left, the dining on the
right, a big foyer, the living room in the centre with a high ceiling, and the
kitchen after the dining room. Claude confirmed the orientation (left is
north) and offered two ways to carry the double height: a tall block in the
courtyard, or a void with a gallery upstairs, which would have cost about 45
m2 of first floor program. The owner chose the tall block.

**Result, measured: 644.82 m2, 18.17 m2 inside the cap,** up from 9.89 m2.
The D-005 margin is restored and its expected failure marker is off. Road
wing 282.12, SSW wing 45.47, living block 49.01, first floor 268.22. Padding:
the hall by design (+20.9), the office +1.8, the master +5.7 (it follows the
guest bedroom's length). The kitchens keep a wall to the living room; opening
it is an option for the owner.

**Approved by Aiman: yes,** the arrangement and the tall living block. The
hall size and the room sizes: for review.

---

## 2026-10-02, interiors drawn in Phase 3

### D-035 Master suite plan, with its terrace on the kitchen roof

**Decision.** The master's private balcony is a terrace on the flat roof of the
single storey kitchen and dining block, outside the master's east wall, about
45 m2, reached through a 3.00 m glazed sliding door. Inside, a 5.00 m service
zone on the road side holds the bathroom (about 13 m2: bathtub, separate
shower, double basin, WC) and his and hers walk-in wardrobes (5 m2 each),
reached along a 1.40 m dressing gallery from the landing door. The bedroom and
sitting area (about 47 m2) take the terrace side, with the coffee station by
the terrace door.

**Reason.** Owner choice 2026-10-02 from three balcony options. The roof is
there already with its 1.20 m parapet (DDA FAQs Building Q34); the two storey
wing shades it in the afternoon; it looks north over the pool; and open
terraces are excluded from GFA (DDA FAQs Building Q25), so it costs nothing
against the cap. The tall living room wall closes its east side, so it has no
direct view of the landscape plot. The service zone goes on the road side so
the bedroom keeps the quiet, shaded terrace side. Waterproofing and the
terrace finish are for the consultant.

**Approved by Aiman: yes,** the terrace position. The internal plan: Claude's
proposal, for review.

### D-034 En-suite bedrooms: bath and wardrobe beside the door

**Decision.** In bedrooms 2 to 4 and the guest bedroom, a 2.40 x 2.40 m
bathroom (walk-in shower, WC, basin) and a 0.65 m deep built-in wardrobe sit
beside the door, forming an entry lobby, so the bedroom keeps its facade and
windows. The bathroom takes the end of the door wall away from the facade. The
bathrooms are internal, with mechanical extract. Partitions 0.10 m. The maid's
room gets a 1.20 m wide shower room across its far end, beside the outdoor
bathroom so the two share drainage.

**Reason.** Owner choice 2026-10-02 from three en-suite layouts, and the
owner's instruction to draw interiors in Phase 3 rather than Phase 4. Each
bedroom keeps 23.75 m2 (guest 25.75 m2) for the bed area. Sizes are Claude
proposals, recorded in brief/program.yaml under interiors.

**Approved by Aiman: yes,** the layout principle. The sizes and the maid's
shower room: for review.

---

## 2026-10-02, open plan and the family hall

### D-033 Owner rule: open space maximization, read as open-plan interiors

**Decision.** A must-rule for the whole villa: shared spaces flow together with
as few walls and corridors as possible. On the ground floor the foyer, stair
hall, corridor and link hall are one open entrance hall, and the show kitchen,
dining and living are one open space. Where they open into the double height
living room a bulkhead stays above 4.70 m to mark the edge of the double height.
Private rooms stay enclosed with doors: bedrooms, bathrooms, majlis (formal, with
its own powder room), office, Arabic kitchen, staff rooms and services.

**Reason.** Owner instruction 2026-10-02, "the villa must be built on the open
space maximization rule". Claude asked which open space was meant; the owner
chose open-plan interiors, not a smaller footprint for more garden. The massing,
footprint and GFA are unchanged by the rule itself.

**Risk.** An open stair joining two floors and an open kitchen may meet fire
separation requirements under the UAE Fire and Life Safety Code, approved by
Dubai Civil Defence (DDA FAQs Building Q42). TO VERIFY, OI-24.

**Approved by Aiman: yes,** the rule and its reading. The list of which spaces
join: Claude's application, for review.

### D-032 First floor around a central family hall

**Decision.** The upstairs corridor is removed. The family room spans the full
width of the first floor in its middle, with the road facade on one side and the
courtyard and pool on the other, and is open to a family hall over the stair and
linen. Bedrooms 2 and 3 sit side by side across the rear and open onto the
family room. The stair arrives on a 1.80 m landing, from which the master suite
and bedroom 4 are entered, so the master shares no wall with the family room
(acoustic separation, CLAUDE.md section 4).

**Reason.** Owner request 2026-10-02: the family room central with the bedrooms
around it. Two arrangements were offered; the owner chose this one. Bedroom 4
cannot sit directly beside the stair because the stair's top flight arrives at
its east end, which must be circulation.

**Result, measured: 653.10 m2, 9.89 m2 inside the cap,** up from 6.52 m2. The
first floor is 3.37 m2 smaller because the 30 m2 corridor became family hall.
The ground floor is unchanged: the band widths are held at the approved 5.10 m
and 4.20 m. Left free, the search would narrow the east band to 3.70 m (648.50
m2), making the majlis a 3.7 m wide gallery; not done without the owner.

Two gaps in the earlier Phase 3 model came to light and are fixed: the home
office had no door (it now opens off the foyer) and the maid's room had only its
outside door (it now also opens into the laundry).

**Approved by Aiman: yes,** the arrangement. The measured result: for review.

---

## 2026-10-02, Phase 3 section and staff strip

### D-031 Staff strip reordered: maid's room and outdoor bathroom on the north wall

**Decision.** In the staff strip north of the corridor, the maid's room and the
outdoor bathroom now sit on the external north wall, with the laundry and plant
room on the corridor side. The plant room keeps its courtyard wall.

**Reason.** CLAUDE.md asks for the maid's room in the staff zone with a separate
entrance. On the old order it had no external wall, so no window and no outside
door. Now it has both, and the outdoor bathroom has north and courtyard walls
for its own door. The laundry is reached from the garage.

**Result, measured:** 656.47 m2, unchanged, 6.52 m2 inside the cap.

**Approved by Aiman: no,** Claude's correction for review at the Phase 3
checkpoint.

### D-030 Tall section: 5.00 m ground, 4.00 m first, 1.20 m parapet, 10.20 m overall

**Decision.** Floor to floor heights of 5.00 m on the ground floor and 4.00 m on
the first floor, with a 1.20 m parapet: 9.00 m to the main roof slab and 10.20 m
overall. The double height living room rises the full 9.00 m.

**Reason.** Owner choice 2026-10-02, for high ceilings. About 4.55 m clear on the
ground floor and 3.55 m upstairs, inside the clear heights in DDA FAQs Building
Q28 (up to 6 m ground, up to 4.2 m typical) and above the Q33 minimum of 2.7 m.
The 1.20 m parapet is DDA FAQs Building Q34.

**Risk.** DDA FAQs Building Q29 gives a metre cap of floors x 4.2 m, 8.40 m for
G+1, which this exceeds. Whether that cap applies to this plot, which states only
"G+1", is TO VERIFY, OI-13. The tall ground floor also forces a compact stair
and lift core, OI-23.

**Approved by Aiman: yes.**

---

## 2026-10-02, bedrooms restored

### D-029 Bedrooms 2 to 4 restored to 30 m2

**Decision.** The D-027 trim on bedrooms 2 to 4 is reversed: back to 30 m2,
their CLAUDE.md minimum. The master stays at 68 and the family room at 33.

**Reason.** Owner decision 2026-10-02, spending the headroom freed when the
driver's room was removed (D-028).

**Result, measured: 656.47 m2, 6.52 m2 inside the cap.** Thinner than the
9.99 m2 margin recommended in D-005, and thinner than Claude estimated before the
change: restoring the three bedrooms cost 10.75 m2 against the cap, not the
7.5 m2 quoted, because the longer first floor needs a longer ground floor under
it. The master is 2.27 times the bedrooms at the bottom of the ranges, inside
the brief's 2.2 to 2.5.

The D-005 margin test is now a strict expected failure, so the shortfall stays
visible. A floor of 5 m2 is still enforced.

**Approved by Aiman: yes.** Restoring the bedrooms. Accepting the thinner
margin: not yet asked.

---

## 2026-10-02, staff zone

### D-028 No driver's room; an outdoor bathroom instead

**Decision.** The driver's room is removed from the program and kept on record
under `removed:` in `brief/program.yaml`. An outdoor bathroom, WC and shower,
4.5 m2, is added. It has its own external door and no internal connection to
the villa, and sits on the courtyard face of the staff strip beside the garage,
facing the north end of the pool deck.

**Reason.** Owner decisions 2026-10-02: first to move the driver's room outside
the villa, then to drop it and make sure there is a bathroom outside. Placing the
bathroom on the courtyard face lets one room serve swimmers, garden use, and a
non-resident driver or outdoor staff by the garage. The 4.5 m2 size and the
placement are Claude's reading of the instruction, flagged for owner review.

A standalone driver's outbuilding was tried first and rejected by the geometry:
north of the garage there is not enough room inside the 3 m setback for it.

**Result, measured: 645.72 m2, 17.27 m2 inside the cap.** Removing the driver's
room shortened the staff strip, so the garage no longer carries padding and is
exactly its 31.3 m2 internal target. The majlis absorbs the floor under the
bedrooms instead and measures 50.1 m2 against its 35 m2 brief.

**Approved by Aiman: yes,** the removal and the outdoor bathroom. The size and
placement of the bathroom: not yet.

---

## 2026-10-02, Phase 2 plan fits

### D-027 Option C confirmed; foyer single height; upstairs trims

**Decision.** Massing option C stands. The living room is double height in the
single storey wing. The foyer is single height, taking its height from a tall
ground floor rather than a void. Upstairs trims, recorded in
`brief/program.yaml` with their brief figures:

| Room | Brief | Now |
|---|---|---|
| Master suite, minimum | 70 | 68 |
| Bedrooms 2 to 4, minimum | 30 | 28 |
| Family living | 35 | 33 |

**Reason.** Owner decision 2026-10-02, after option A was measured at 698.86 m2,
35.87 over, because a double height living room in a two storey bar takes plate
the bedrooms need. Option C puts the living room where a high ceiling costs no
plate. The owner wants high ceilings; ceiling height is not GFA, and DDA FAQ Q28
allows a ground floor clear height up to 6 m, subject to OI-13.

The cuts are upstairs because in option C a ground floor cut in the two storey
wing only turns into padding under the bedrooms. The master stays 2.43 times the
bedrooms at the bottom of the ranges and 2.29 at the top, inside the brief's
2.2 to 2.5.

**Result, measured from the drawn plan: 651.22 m2, 11.77 m2 inside the cap**,
above the 9.99 m2 margin recommended in D-005. The majlis comes out at 44.3 m2
against its 35 m2 brief, because it fills the ground floor under the bedrooms.

**Approved by Aiman: yes.** Chose option C and the master to 68 directly.

---

## 2026-10-02, design basis settled by the owner

### D-026 Garage counts toward GFA, and corridors are 1.80 m

**Decision.** The design proceeds on two owner decisions: the enclosed garage
counts toward the 662.99 m2 GFA cap, and DDA FAQs Building Q12's 1.80 m corridor
minimum applies to corridors inside this private villa.

**Reason.** Owner decision 2026-10-02. Both were open DDA questions (OI-01 and
OI-21). The owner settled them on the conservative reading rather than wait, so
neither can return area later through a DDA answer.

**Approved by Aiman: yes.** Stated directly.

---

## 2026-10-02, trim package 2 and the measured plan

### D-025 Once a plan exists, measured GFA is the binding figure

**Decision.** `src/analysis/gfa_check.py` now reads `brief/layouts.yaml` and
tests the cap against GFA measured from the drawn plan, failing loudly when it is
exceeded, as CLAUDE.md section 3 requires. The net to gross estimate is still
printed, but it no longer decides the verdict.

**Reason.** Four successive estimates of this plan each came in optimistic: a
flat wall allowance, a corridor assumed shorter than the plan needed, a corridor
width below the DDA figure, and finally a first floor allowed to be deeper than
the ground floor it sits on. Each was corrected, and each correction made the
figure worse. Drawn geometry ends that pattern: `src/model/layout_gen.py` places
every room, stacks the stair cores, keeps the first floor over the ground floor,
and the area is measured from what is drawn.

**Approved by Aiman: not required.** Technical.

### D-024 Trim package 2: the sunroom is removed

**Decision.** The sunroom, 20 m2 net, is removed from the program. It is kept on
record under `removed:` in `brief/program.yaml` with its brief figure and reason.
The SSW wing is sized to its rooms at brief size rather than to the Phase 1
massing.

**Reason.** Owner chose package 2 of the four costed on 2026-10-02, the only one
that left every other room at its brief size. The courtyard and the double height
living room facing it already give the house its garden room.

**Approved by Aiman: yes.** Chose package 2 directly.

---

## 2026-10-02, Phase 2

### D-023 Net to gross factor replaced by measurement, 1.18 to 1.222

**Decision.** `brief/site.yaml` now carries 1.222, measured, with the previous
1.18 kept beside it as `net_to_gross_previous`.

**Reason.** A-01 always said the Phase 0 assumption would be replaced by the
ratio of the actual plan at Phase 2. This is that replacement. It comes from
`src/analysis/plan_feasibility.py`: external walls from each wing's real
perimeter at 0.25 m, partitions at 4.5% of net, a 1.40 m corridor on the first
floor and a service spine on the ground.

It is worse than assumed because option C has two long thin wings, and a long
thin wing pays for its external walls by the metre. The single depth SSW wing,
where every room opens to the courtyard and there is no corridor, measures 1.13
on its own.

The GFA check and the feasibility model now agree to within 0.1 m2, 656.33
against 656.43, where before they differed by 21 m2.

**Approved by Aiman: not required.** Replacing an assumption with a measurement.

### D-022 Garage reduced to two cars, 55 m2 to 38 m2

**Decision.** The enclosed garage holds two cars, not the three in CLAUDE.md
section 4. 38 m2.

**Reason.** Owner decision 2026-10-02. Sized from the DDA bay standard rather
than scaled down: DDA FAQs Building Q5 gives a standard bay as 2.5 x 5.5 m, and
the 55 m2 three car figure works out as roughly 8.15 x 6.75 m holding three bays
at 2.55 m. Removing one bay takes 2.55 m off the width, giving about
5.60 x 6.75 m, so 38 m2.

The DDA plot details require a minimum of one parking space, so two remains
compliant.

**This is what made the plan fit.** A garage target is already a gross footprint,
so the 17 m2 comes straight off GFA with no net to gross factor applied. Plan 2
moves from 10.31 m2 over the cap to 6.56 m2 inside it.

**Approved by Aiman: yes.** Stated directly.

### D-021 Plan direction 2, Courtyard

**Decision.** The reception rooms interconnect around the courtyard rather than
hanging off a corridor, and the corridor shrinks to a short service spine serving
the staff zone, guest bedroom and office.

**Reason.** Owner decision 2026-10-02. It saves 20.96 m2 against a conventional
corridor plan, all of it circulation, and it is the plan that actually uses the
courtyard that option C commits to. Plan 1, the corridor plan, remains 14.29 m2
over the cap even after the two car garage, and is not available.

The cost is how the house works: some parts of the ground floor are reached by
crossing the courtyard or passing through a reception room rather than walking a
corridor.

**Approved by Aiman: yes.** Stated directly.

---

## 2026-10-01, trims

### D-019 Trim route B, service and circulation only, 13 m2 net

**Decision.** Owner approved trim route B. Eight rooms reduced, none of them a
principal room:

| Room | Brief | Trimmed | |
|---|---|---|---|
| Staircase + elevator, first | 20 | 15 | now the top landing, no roof flight to accommodate |
| Staircase + elevator, ground | 20 | 18 | tightened with the first floor core |
| Entrance foyer | 20 | 19 | still double height |
| Pantry / storage | 6 | 5 | |
| Laundry | 8 | 7 | |
| Maid's room | 12 | 11 | |
| Driver's room | 12 | 11 | |
| MEP plant room | 8 | 7 | |
| **Total** | | | **13 m2 net, 15.34 m2 gross** |

**Reason.** Counting the garage toward GFA (D-018) put the program 4.43 m2 over
the cap and 14.42 m2 over the design target at the minimum of every range. Four
routes were costed and put to the owner, who chose B because it touches no
principal room. The largest single saving, 5 m2 from the first floor stair and
lift, comes almost free: removing the roof stop in D-017 means there is no
further flight to accommodate.

**Result.** The program now lands at **652.08 m2** at the minimum of every range,
10.91 m2 inside the cap and 0.92 m2 inside the design target. The GFA check
passes.

Every trimmed room keeps its CLAUDE.md figure in `brief/program.yaml` as
`brief_target_m2`, with the reason, so the trim stays visible and reversible. A
pytest check enforces that, and another enforces that no principal room was
touched.

**Approved by Aiman: yes.** Chose route B directly.

### D-020 GFA check pass and fail semantics corrected

**Decision.** A breach at the minimum of the ranges is a FAIL. A breach only at
the maximum is reported as "fits at minimum, high end unaffordable", with a new
RANGE HEADROOM section quantifying how much of the range can be spent.

**Reason.** The old logic failed the build whenever the top of the bedroom ranges
did not fit, which would have left the suite permanently red for a condition that
is a budget to manage rather than a defect. The villa is built at one size, not
at a range. What matters is that a buildable version exists under the cap and
that everyone can see how much of the range is affordable.

**Approved by Aiman: not required.** Technical.

---

## 2026-10-01, owner decisions on roof and garage

### D-018 Count the parking as part of the GFA

**Decision.** The 55 m2 garage counts toward the 662.99 m2 GFA cap.
`brief/program.yaml` now marks it `gfa: counts`, and the GFA check has no
unverified areas left.

**Reason.** Owner decision. DDA's published material does not rule on garages,
so rather than design against an unknown and risk a redesign at submission, the
conservative reading is adopted. If the issued Site Plan later excludes the
garage, 55 m2 comes straight back and the room ranges reopen.

**Consequence, and it is not small.** The briefed program no longer fits. At the
low end of every bedroom range it reaches 667.42 m2 against the 662.99 m2 cap,
over by 4.43 m2, and over the 653.00 m2 design target by 14.42 m2. At the high
end it is 33.93 m2 over the cap, and no plan efficiency tested can recover that,
so the top of the bedroom ranges is no longer available. Trims are needed and
are tracked as OI-18. No room has been cut.

**Approved by Aiman: yes.** Stated directly.

### D-017 No roof terrace and no roof enclosure

**Decision.** The roof terrace and the roof stair and elevator enclosure are
removed from scope. `brief/program.yaml` now has an empty `roof` section. The
elevator serves ground and first only.

**Reason.** Owner decision. This also removes the risk found in the DDA FAQ,
where Q27 counts a roof gym as an additional floor unless the master developer
excludes it. On that reading a roof enclosure could have breached the G+1 cap
outright rather than merely adding GFA. That risk is now gone, and OI-02 closes.

**Carried forward.** The flat roof still exists and still needs a 1.20 m parapet.
The VRF outdoor units still need a location, either on the flat roof behind a low
screen, which needs no enclosure and adds no floor, or at ground level in the
service zone. Decided in Phase 5, tracked as OI-17.

**Approved by Aiman: yes.** Stated directly.

---

## 2026-10-01, owner selection and DDA research

### D-016 Parapet raised to 1.20 m, the DDA minimum

**Decision.** `brief/massing.yaml` now carries a 1.20 m parapet, up from the
1.10 m previously assumed.

**Reason.** Not a design choice, a correction. DDA FAQs - Building, retrieved 2026-10-01 from https://webzoning.dda.gov.ae/Zoning/Content/dda/FAQs.pdf, Q34: "What is the minimum
parapet and balcony handrail height?" Answer: "1.2m from the floor finish
level." The earlier 1.10 m was below the DDA minimum. Overall height moves from
8.90 m to 9.00 m and every shadow figure was recomputed.

**Approved by Aiman: not required.** Correcting to a cited authority minimum.

### D-015 DDA published material checked for the garage question

**Decision.** OI-01 stays OPEN. DDA's published guidance does not answer it.

**Reason.** Owner asked for DDA to be checked before any query was drafted. Two
DDA sources were retrieved and parsed in full:

- DDA FAQs - Building, retrieved 2026-10-01 from https://webzoning.dda.gov.ae/Zoning/Content/dda/FAQs.pdf, 20 pages
- Objectives of the Dubai Building Code, dda.gov.ae, 17 pages

The word "garage" appears **zero times** in either document. DDA's own answer to
"Where can I find the Planning Regulations for my Plot?" is "You can find the
regulations for your plot on the issued site plan", and to "What are the Parking
standards as per DDA?" is "as mentioned in the site plan". So the answer is
plot-specific and lives in the issued Site Plan and the Meraas development
guideline, neither of which we hold. See OI-01 and OI-03.

What the FAQ does settle is that **GFA and BUA are different measures** in DDA's
own usage. Q25: "Balconies are always excluded from GFA calculations, but
included in the BUA calculation." The cap on this plot is on GFA, 662.99 m2, not
on BUA.

**Approved by Aiman: not required.** Research, reported to the owner.

### D-014 Option C, Courtyard, selected, with the double height living room

**Decision.** Option C is the massing to carry into Phase 2. The living room in
the single storey SSW wing is double height.

**Reason.** Owner decision, stated 2026-10-01. Option C holds 87% of the pool
deck in shade through cooling season afternoons against option A's 93%, and
gives up the open view east, but it encloses a private courtyard and the double
height living room costs no upper floor area because nothing sits above that
wing. The owner weighed that against the recommendation and chose C.

All three options carry the same 406.5 m2 ground floor and 290.3 m2 first floor,
so the choice moves no GFA.

**Approved by Aiman: yes.** Stated directly.

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

**Approved by Aiman: yes,** 2026-10-03 (answer G3: A), kept TO VERIFY: DDA FAQ Q3 allows a boundary wall only where the development guideline does (OI-14).

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
