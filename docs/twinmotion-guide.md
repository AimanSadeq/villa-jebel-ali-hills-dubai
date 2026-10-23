# Twinmotion guide: the realistic walkthrough of Villa 5130272

CONCEPT DESIGN, NOT FOR CONSTRUCTION.

Owner decision W1 (2026-10-03, D-059): the realistic walkthrough is made in
Twinmotion from this project's IFC export. The design still comes from the
brief files and the scripts here; after each design change, rebuild and
re-import (step 3), and Twinmotion keeps your materials, furniture and plants
where they were.

## 1. Install Twinmotion

- Download from https://www.twinmotion.com. At the time of writing a free
  Community Edition exists for personal, non-commercial use and a paid
  licence for commercial use: check the current terms on the site before
  choosing. Installation is through the Epic Games Launcher.
- Requirements, TO VERIFY on the Twinmotion site: a DirectX 12 graphics card
  with 8 GB of memory is recommended. The laptop's Intel Arc 140V is an
  integrated GPU with shared memory: expect to run at reduced quality
  (Settings, Quality: Medium, and a smaller window). A desktop with a
  dedicated card gives the full result.

## 2. Produce the export

In PowerShell, from the project folder:

```
.\.venv\Scripts\Activate.ps1
python src/model/build_model.py
python src/model/export_twinmotion.py
```

This writes `output/twinmotion/`:

| File | What |
|---|---|
| `VJH-TM-001_Villa_5130272_palette1_sand_and_oak.glb` | **The file to import.** The villa with palette 1's finishes (and `palette2_…`, `palette3_…`) |
| `VJH-TM-001_Villa_5130272_palette1_sand_and_oak.obj` and `.mtl` | The same model, if the import dialog does not list `.glb` (keep the `.mtl` beside the `.obj`) |
| `VJH-TM-001_Villa_5130272_palette1_sand_and_oak.ifc` | The same model as IFC, for programs that read IFC (Twinmotion 2026.2 does not list IFC on import, 2026-10-05) |
| `VJH-TM-001_placements.csv` | Every furniture piece and tree: position, size, rotation, library kind |
| `VJH-TM-001_cameras.csv` | The six views of the brief and the sun positions from the sun study |

Each file carries the walls, slabs, roof, doors, windows, stair, lift, facade
(stone portal, garden frame, eaves, fins, pergola, LED lines), the garden
surfaces, the boundary wall and gates, and the interior finishes of one
palette as thin surfaces. The box furniture, sanitary ware and the
procedural trees are left out on purpose: Twinmotion's library has real ones.

## 3. Import into Twinmotion

1. Import (bottom bar), Geometry, choose the palette's `.glb` (if the
   file-type list has no glTF entry, pick "All files" or use the `.obj`).
   Options: Collapse: "Collapse all" (it merges the geometry but keeps each
   material separate, which is how the finishes are meant to be swapped);
   leave the axis and unit options at their defaults (the file is in metres,
   y up, as glTF requires). (Twinmotion 2026.1; older versions call the
   collapse option "Collapse by material".)
2. The model lands at the plot's own coordinates: x east-south-east
   along the plot grid, the plot's y north-north-east, z up; the house
   floor is z 0.00 and the garden ground z -0.45. Nothing needs moving. The
   ground plane "Starting Base" of an empty scene can be hidden (Scene panel,
   eye icon) so it does not cut the garden. If the house comes in lying on
   its side, re-import the `.obj` and set the import's up axis to Y.
3. Orientation: the model's +y is bearing 30.18 degrees (NNE), not north.
   In Twinmotion's Location panel set the north offset so the sun matches:
   rotate north by 30 degrees from +y toward +x (TO VERIFY by checking a
   shadow against `VJH-TM-001_cameras.csv`: at 15:00 on 21 March the sun
   stands at azimuth 242, elevation 46, and the roof pergola's shadow falls
   toward the north-east).
4. Location: Dubai, latitude 24.8975, longitude 54.9650 (brief/site.yaml).

## 4. Materials

Every surface in the import carries a material named for what it is:

- Facade (the redesign, D-061): "White render", "Charcoal stone cladding", "Timber,
  soffits, fins and screens", "Glazing", "Linear LED line, warm white".
- Interior finishes of the palette: "Floor public: Beige limestone look
  porcelain…", "Wall feature: Travertine slab…", "Wall ceiling: …", and so
  on, one material per finish slot of brief/palettes.yaml.
- Garden: "Lawn", "Planting bed, mulch", "Stone deck" (terraces), "Paving,
  light" (paths and the service yard), "Garden ground".

In Twinmotion, click a surface, open the Material panel and drag a library
material onto it: the whole slot changes at once (every public floor, every
main wall). Suggested library matches, palette 1 Sand and Oak:

| Material in the import | Twinmotion library |
|---|---|
| Floor public, kitchen | Stone, limestone or travertine tiles, 1200 x 600 |
| Floor bedrooms | Wood, light oak planks |
| Floor wet | Stone, textured limestone |
| Wall main, ceiling | Paint, warm white matt |
| Wall feature | Stone, travertine slab |
| Wall wet | Stone, light limestone, large tiles |
| White render | Plaster or stucco, white, smooth |
| Charcoal stone cladding | Stone, charcoal or dark basalt, large panels |
| Timber, soffits, fins and screens | Wood, teak or iroko |
| Glazing | Glass, clear, low iron |
| Linear LED line, warm white | Neon or emissive, warm white 2700 K |
| Lawn | Grass, short |
| Stone deck | Stone pavers, beige |
| Paving, light | Concrete pavers |

Palettes 2 (Marble and Walnut) and 3 (Stone and Charcoal) follow the names
in their files; the swatch sheet VJH-SK-018 shows the intent.

## 5. Furniture and plants

`VJH-TM-001_placements.csv` has one row per piece: `x_m, y_m` is the centre
of its footprint in the model's frame, `z_m` its floor level, `width_m` and
`depth_m` its size along its front and back to front, `rotation_deg` the
rotation about z such that `back_toward` names the wall side it stands
against (S means its back faces the model's -y, the SSW side).

Workflow: open the Library, pick the `library_kind` named in the row (for
example "Sofa, 3 seats"), drop it anywhere, then in its Transform panel type
the x, y, z and rotation from the row, and scale to the width if needed. The
furniture rows are indicative placements (D-054); move them as you like.

Trees and palms: rows with room `garden`. The species are UAE natives or
common garden plants (brief/garden.yaml); Twinmotion's library has date
palms and broadleaf trees; frangipani can be any small flowering tree.
Scatter paint is quicker for the hedges along the planting beds.

## 6. Sun, cameras and the views

`VJH-TM-001_cameras.csv`: for each of the seven views (entrance and carport, foyer and stair, courtyard,
family living, master bedroom, garden at sunset, aerial),
the camera position and target in metres, the lens, and the sun's date, time,
azimuth and elevation from the sun study. In Twinmotion create an Image
(Media panel), place the camera by typing the position, point it at the
target, set the focal length, and set the date and time in the Location
panel; the sun then matches the study.

## 7. What Twinmotion does not get from the export

- Light fixtures: none yet; the reflected ceiling plans (Phase 6) place them.
  Until then use Twinmotion's library lights for night views.
- Door swings and the walkable route: Twinmotion walks through anything;
  the browser walkthrough (viewer/model.html) stays the tool for checking
  that every room is reachable (tests/test_walk_reach.py).
- Room labels and areas: see the floor plans VJH-GA-001.

## 8. After a design change

Edit the brief files (never the Twinmotion scene for design changes), run
`python src/model/build_model.py` and `python src/model/export_twinmotion.py`,
then in Twinmotion use File, Import, Refresh (or re-import the same file):
materials assigned by name are kept; furniture and plants you placed stay
where they are.
