# Geometry validation, Villa 5130272, the courtyard villa (D-060)

CONCEPT DESIGN, NOT FOR CONSTRUCTION. Generated 2026-10-23 by src/analysis/geometry_validation.py from brief/layouts.yaml (the plan), brief/program.yaml, brief/garden.yaml and brief/site.yaml.

| Check | Result | Measure |
|---|---|---|
| First floor enclosed over the guest suite and the powder room | PASS | 100.0% covered by first floor rooms; 0.00 m2 under a void or terrace (the other assistant's images showed a planted roof here; this plan has bedroom 2 and its lobby above) |
| Exactly three bedrooms upstairs | PASS | bedroom_2, bedroom_3, master_suite |
| Three dedicated en-suite bathrooms | PASS | bedroom_2_toilet, bedroom_3_toilet, master_toilet |
| No linen room, no fourth bedroom | PASS | removed on record in brief/program.yaml |
| Master walk-in wardrobe integrated, shower only bathroom | PASS | walk-in 11.6 m2 and bathroom 11.6 m2 off the bedroom 22.8 m2; fittings walk-in shower, double basin, WC |
| Courtyard open to the sky, about 22 m2 | PASS | 4.50 x 4.60 m, 20.7 m2 (223 sq ft) |
| Foyer double height, not infilled | PASS | void over the foyer 29.7 m2, including the stair's upper flight |
| No vehicle gate, no pedestrian gate | PASS | road side open with a planted edge (brief/garden.yaml); whether Meraas requires a wall or gate is open, OI-14 |
| Open carport, two cars | PASS | 6.5 x 6.0 m, 39.0 m2; two bays of 2.5 x 5.5 m fit; exact SUV size pending |
| Family living opens to the private garden | PASS | door G15, 4.8 m sliding, under the ground floor canopy |
| Both floors in one grid, first floor on the ground floor | PASS | first floor outline 258.8 m2 inside the ground outline 316.5 m2; cantilever 0.00 m2 |
| Everything behind the 3 m setback lines | PASS | ground and first outlines, the terrace and the carport inside the envelope |
| GFA inside the DDA cap | PASS | 504.22 m2 measured against 662.99 m2, margin 158.77 m2 |
| Enclosed area near the handover's 450 to 500 m2 | PASS | 504.22 m2 enclosed over G+1: ground 295.81, first 208.41; courtyard 20.70 and voids 50.39 m2 not counted |
| Carport and terrace counted outside GFA | TO VERIFY | carport 38.91 m2, master terrace 9.20 m2; whether DDA counts them is open, OI-01 |
| Private garden east of the house, measured from the plan | PASS | 367.6 m2 (3957 sq ft) contiguous, bounded by the house, the two neighbours and the landscape plot; largest clear rectangle 10.8 x 32.5 m = 349 m2 at u 19.2, v 0.7; depth from the house 11.3 m, length along the house 23.1 m. The earlier boards' 12 x 20 m was not measured; this is. |
| Front garden, measured | PASS | 124.6 m2 between the road and the house, less the driveway |
| Stair: 28 risers of 179 mm, going 270 mm, straight in two flights | TO VERIFY | headroom 2.20 m over the landing under the gallery; riser, going, headroom and the 1.20 m width against the Dubai Building Code and the UAE Fire and Life Safety Code, OI-23 |
| Floor to floor 5.00 and 4.00 m, parapet 1.20 m, 10.20 m overall | TO VERIFY | DDA FAQ Q29 may cap the height in metres, OI-13 |
| Carport treatment, SUV swept path, demarcation certificate | TO VERIFY | exact SUV dimensions pending; the plot boundary is the DDA GIS geometry until the certificate arrives, OI-03 |
| Internal bathrooms and the closed prep kitchen | TO VERIFY | mechanical extract rates, OI-25; the prep kitchen takes light and air from the courtyard window, OI-15 |

## Room schedule, measured

| Floor | Room | w x l (m) | m2 | sq ft |
|---|---|---|---|---|
| ground | Maid's Room with Bathroom | 2.60 x 3.20 | 8.3 | 90 |
| ground | Maid's Shower Room | 1.50 x 3.20 | 4.8 | 52 |
| ground | Laundry | 2.10 x 3.20 | 6.7 | 72 |
| ground | Arabic (Prep) Kitchen | 2.75 x 3.20 | 8.8 | 95 |
| ground | Show Kitchen | 4.85 x 4.95 | 24.0 | 258 |
| ground | MEP Plant Room | 2.40 x 2.90 | 7.0 | 75 |
| ground | Entrance Foyer | 4.60 x 4.75 | 21.9 | 235 |
| ground | Courtyard, open to the sky | 4.50 x 4.60 | 20.7 | 223 |
| ground | Dining and Garden Room | 4.95 x 8.05 | 39.9 | 429 |
| ground | Home Lift | 1.60 x 2.15 | 3.4 | 37 |
| ground | Guest Powder Room | 1.45 x 2.15 | 3.1 | 34 |
| ground | Guest Bathroom | 2.15 x 2.85 | 6.1 | 66 |
| ground | Salon | 4.40 x 4.75 | 20.9 | 225 |
| ground | Guest Bedroom, En-suite | 4.40 x 4.50 | 19.8 | 213 |
| ground | Family Living | 4.95 x 6.70 | 33.2 | 357 |
| ground | service corridor | 1.50 x 9.40 | 14.1 | 152 |
| ground | hall | 3.30 x 9.40 | 31.0 | 334 |
| ground | salon lobby | 1.40 x 2.15 | 3.0 | 32 |
| ground | guest lobby | 1.50 x 2.15 | 3.2 | 35 |
| first | Master Walk-in Wardrobe | 2.40 x 4.85 | 11.6 | 125 |
| first | Master Bathroom, shower only | 2.40 x 4.85 | 11.6 | 125 |
| first | Master Bedroom | 4.60 x 4.95 | 22.8 | 245 |
| first | Home Lift, first floor | 1.60 x 2.15 | 3.4 | 37 |
| first | Workspace | 2.15 x 3.00 | 6.5 | 69 |
| first | Bedroom 2 En-suite | 2.15 x 2.35 | 5.0 | 54 |
| first | Bedroom 3 Dressing Room | 2.15 x 2.40 | 5.2 | 56 |
| first | Bedroom 3 En-suite | 2.15 x 2.40 | 5.2 | 56 |
| first | Family Lounge | 4.40 x 4.75 | 20.9 | 225 |
| first | Bedroom 2, En-suite | 4.40 x 4.50 | 19.8 | 213 |
| first | Bedroom 3, En-suite | 4.40 x 4.95 | 21.8 | 234 |
| first | gallery | 3.30 x 9.75 | 32.2 | 346 |
| first | gallery west | 1.80 x 4.75 | 8.6 | 92 |
| first | north lobby | 2.00 x 2.15 | 4.3 | 46 |

Clear heights: ground floor 4.55 m (foyer 8.55 m under its void), first floor 3.55 m (brief/massing.yaml, D-030).

RESULT: PASS. CONCEPT DESIGN, NOT FOR CONSTRUCTION.
