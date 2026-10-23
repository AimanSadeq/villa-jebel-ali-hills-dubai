# Twinmotion, step by step, for the courtyard villa

CONCEPT DESIGN, NOT FOR CONSTRUCTION.

Answer U1 (2026-10-23): the way to photorealistic views of the redesign
(D-061) is your own Twinmotion 2026.2, with the model exported from this
project. This is the exact list for this house. The general guide,
docs/twinmotion-guide.md, has the background; this file has the actions.
Where a panel in your version carries a different name, look for the nearest
one and tell me, so the list can be corrected.

Allow about an hour for steps 1 to 5 the first time. Steps 6 and 7, the
furniture and the cameras, can follow in a second session.

## 1. Produce the files (PowerShell, in the project folder)

```
git pull
.\.venv\Scripts\Activate.ps1
python src/model/build_model.py
python src/model/export_twinmotion.py
```

This writes `output\twinmotion\`. The file to import is
`VJH-TM-001_Villa_5130272_palette1_sand_and_oak.glb`. The lists you will
use are `VJH-TM-001_placements.csv` (furniture and trees) and
`VJH-TM-001_cameras.csv` (the seven views), also in the Excel workbook
`VJH-TM-001_Twinmotion_lists.xlsx`.

## 2. Import

1. File, New project. Settings, Quality: Medium (the laptop's integrated GPU).
2. Import (bottom bar), Geometry, choose the `.glb`. Collapse: "Collapse all".
   Leave the other options at their defaults. OK.
3. In the Scene graph (right panel) click the eye icon of "Starting Ground",
   "Starting Landscape" and "Starting Base" to hide them. The model brings its
   own ground, lawn and paving.
4. Press F with the villa selected to frame it. The house stands with the
   road on its west (WNW) side, the carport in the south corner, the garden
   to the east. The courtyard is the square hole in the middle of the roof.

## 3. Location and sun

1. Ambience, Env: keep "Dynamic sky". Open Location (a globe or map icon):
   latitude 24.8975, longitude 54.9650 (Dubai, brief/site.yaml).
2. North: the model's long axis, from the carport toward the north end of the
   house, points to bearing 30 degrees, not north. Set the north offset so
   north is 30 degrees clockwise from that axis. TO VERIFY with a shadow:
   set the date to 21 March and the time to 15:00; standing on the road
   facing the house, the shadow of the entrance's charcoal box should fall
   toward your left, the north-east. If it falls to your right, turn the
   north offset by 180 degrees.
3. Time of day for the exterior views: 15:00 for the entrance and the aerial,
   18:05 for the garden at sunset (a long, low sun from the west), 09:00 for
   the interiors (sun from the east through the garden glass).

## 4. Materials

Library (bottom left), Materials. Drag a library material onto a surface:
because the import was collapsed by material, every surface with that name
changes at once. Click a surface first and read its name in the Properties
panel; the names below are exactly as the file carries them. After dropping
a material, set its Scale so the pattern reads at the right size (the figure
in the last column), and its Reflection or Glossiness as noted.

| Surface in the import | Where it is | Library material | Scale and notes |
|---|---|---|---|
| White render | All outside walls, the eaves and canopies, the parapets | Plaster or Concrete, smooth white, matt | 2 m; keep it slightly off-white, not pure white |
| Slab, rendered edge | Slab edges, parapet caps | The same white plaster | 2 m |
| Charcoal stone cladding | The entrance box, two storeys tall | Stone, dark basalt or slate, large panels; or dark concrete panels | 1 m; low gloss |
| Timber, soffits, fins and screens | Soffits under the eaves and canopies, the carport ceiling, the vertical fins, the BBQ pergola | Wood, teak or iroko, planks | 1 m; matt |
| Timber | Doors, inside and out | Wood, walnut or dark oak | 1 m |
| Glazing | All windows, the garden glass, the courtyard glass | Glass, clear, low iron; reflections on | Opacity about 10% |
| Linear LED line, warm white | The LED lines at the entrance and the eaves | Neon or emissive, warm white 2700 K, low intensity | Visible at sunset and at night |
| Partition, painted | Inside walls with no finish of their own | Paint, warm white, matt (same as Wall main) | 2 m |
| Wall main: Warm white paint, matt | Most interior walls | Paint, warm white, matt | 2 m |
| Wall ceiling: Warm white paint, flat | Ceilings | Paint, warm white, flat | 2 m |
| Wall feature: Travertine slab, TV wall and salon wall | The foyer's south wall, the wall behind the floating stair, the living's TV wall, the salon's east wall | Stone, travertine slab, honed; or Wood, vertical slats, as in your images | 1.2 m |
| Wall wet: Beige stone look porcelain, large format | Bathroom walls | Stone, light limestone, large tiles | 1.2 m |
| Floor public: Beige limestone look porcelain, 1200 x 600, honed | Foyer, hall, salon, dining, living, lobbies | Stone, limestone or travertine tiles, 120 x 60 | 1.2 m; low gloss |
| Floor kitchen: As the public floor | Show kitchen and prep kitchen | The same tiles | 1.2 m |
| Floor bedrooms: Light oak engineered timber, wide plank | All bedrooms, the family lounge, the workspace, the gallery, the dressing rooms | Wood, light oak, wide planks | 1 m; matt |
| Floor wet: Beige limestone look porcelain, textured | Bathrooms, powder room | Stone, textured limestone | 0.6 m |
| Floor service: Light beige porcelain, matt | Corridor, laundry, maid's room, plant room | Tiles, light beige porcelain, matt | 0.6 m |
| Stair, stone | The floating stair treads | Stone, limestone, honed | 1 m |
| Lift car and shaft | The home lift | Metal, brushed stainless steel | |
| Stone deck | Garden terrace, BBQ terrace, entrance court, courtyard paving | Stone, beige pavers 60 x 60 | 0.6 m |
| Paving, light | Driveway, entrance path, side path, service yard | Concrete pavers, light | 0.6 m |
| Roof finish | The flat roofs | Concrete or gravel, light grey | 1 m |
| Lawn | The lawns | Grass, short; or replace with Vegetation, grass scatter | 1 m |
| Planting bed, mulch | The planting beds | Soil, dark mulch | 1 m |
| Garden ground | The rest of the plot | Sand or dry soil | 2 m |

Palettes 2 (Marble and Walnut) and 3 (Stone and Charcoal) are separate
`.glb` files with their own floor and wall names; the same method applies.

## 5. Trees and hedges

My placeholder trees are not in the file; the library's are real. Library,
Vegetation, drag each one in, then type its position in the Properties
panel, Transform (if the panel shows centimetres, multiply by 100). X runs
from the road into the plot, Y along the road toward the north end, Z is the
house floor level: the garden ground is 0.45 m below it, the courtyard at
house level.

| Library | X | Y | Z | Height |
|---|---|---|---|---|
| Olive, the courtyard tree, in the planter | 11.4 | 17.55 | 0.00 | 4.5 m |
| Date palm | 29.3 | 6.0 | -0.45 | 7 m |
| Date palm | 29.3 | 12.5 | -0.45 | 7 m |
| Ghaf (Prosopis) or an acacia | 29.1 | 18.5 | -0.45 | 7 m |
| Date palm | 29.3 | 23.5 | -0.45 | 7 m |
| Sidr (Ziziphus) or any broadleaf | 29.1 | 28.5 | -0.45 | 6 m |
| Frangipani (Plumeria) | 25.0 | 32.6 | -0.45 | 4 m |
| Frangipani | 16.0 | 32.6 | -0.45 | 4 m |
| Frangipani | 25.0 | 15.5 | -0.45 | 4 m |
| Frangipani, front | 1.8 | 11.5 | -0.45 | 4 m |
| Frangipani, front | 1.8 | 14.2 | -0.45 | 4 m |
| Frangipani, front | 1.8 | 20.5 | -0.45 | 4 m |
| Frangipani, front | 1.8 | 27.5 | -0.45 | 4 m |
| Date palm, north-west corner | 1.5 | 32.8 | -0.45 | 7 m |
| Date palm, north edge | 7.0 | 33.3 | -0.45 | 7 m |
| Date palm, south-west corner | 1.5 | 1.6 | -0.45 | 7 m |
| Date palm, south-east corner | 25.0 | 1.6 | -0.45 | 7 m |

Hedges: with the Vegetation paint tool, paint a clipped hedge 0.9 m high
along the road edge (X about 0.6, Y 10.5 to 15.9 and 19.3 to 30.5) and a
1.5 m hedge along the two neighbour walls and the north wall. Ground cover
and a few shrubs in the beds along the garden's east side finish it.

## 6. Furniture (second session)

Library, Objects. `VJH-TM-001_placements.csv` lists every piece with its
centre, size, rotation and library kind; the workbook has the same with
room names. For the seven views the pieces that matter are: the foyer
console; the dining table for 12; the living's sofa, coffee table and TV
unit; the master bed with bedside tables; the salon's two facing sofas; the
BBQ counter and table on the BBQ terrace. Lights for the night views come
from the library too (the ceiling plans are Phase 6).

## 7. The seven views

Media, Image, create one image per view. Navigate to about the camera point,
aim at the target, set the focal length, then set the date and time in
Ambience before you save the image. If your version shows the camera's
position in the image's properties, type the numbers; otherwise place it by
eye from the plan. Heights are above the house floor.

| View | Camera X, Y, Z | Target X, Y, Z | Lens | Date and time |
|---|---|---|---|---|
| Entrance and carport from the road | -13.0, 1.5, 1.7 | 9.5, 18.5, 4.5 | 26 mm | 21 March 15:00 |
| Double height foyer and the floating stair | 5.0, 16.0, 1.6 | 9.5, 20.5, 3.2 | 20 mm | 21 March 09:00 |
| Courtyard from the dining | 18.3, 16.3, 1.5 | 9.5, 18.8, 2.4 | 18 mm | 21 March 15:00 |
| Family living and the garden glass | 18.2, 29.6, 1.5 | 14.2, 23.8, 1.5 | 20 mm | 21 March 09:00 |
| Master bedroom, the courtyard window | 18.3, 15.7, 6.4 | 14.2, 19.4, 6.0 | 20 mm | 21 March 09:00 |
| Garden at sunset | 27.5, 29.5, 1.6 | 17.0, 18.5, 3.5 | 22 mm | 21 March 18:05 |
| Aerial | -12.0, -8.0, 24.0 | 13.0, 19.0, 3.0 | 35 mm | 21 March 15:00 |

Export each image at 1920 x 1080 or larger. The path tracer gives the best
result where your graphics card supports it; otherwise the standard
renderer at high quality. TO VERIFY on your laptop.

## 8. Send me

A screenshot or export of each view, and any surface whose name you could
not find. Changes to the house itself are made here, in the model, and
re-imported: Twinmotion keeps the materials you assigned by name, and the
trees and furniture you placed stay where they are.
