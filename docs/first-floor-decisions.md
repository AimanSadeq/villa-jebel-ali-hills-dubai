# First floor: the owner's answers

CONCEPT DESIGN, NOT FOR CONSTRUCTION.

The first floor is designed alongside the walkthrough (answer F4, 2026-10-02),
one question at a time, as the ground floor was. Each answer is recorded here,
newest last, and logged in docs/decisions.md once the floor is complete.

Starting point (D-046): the reference villa's first floor (sheet A-07-002) as a
placeholder, with the family room above the salon (12b) and the void over the
living room and island kitchen (12l). GFA 661.69 m2, 1.30 m2 inside the cap.
Open items it must settle: OI-27 (linen store, coffee station, family room
size, the GFA margin, the TV wall step, the powder room distance).

| No. | Question | Answer | Consequence |
|---|---|---|---|
| FF1 | What should the first floor start from | **A: the reference first floor, adjusted.** Keep its layout as the base and change only what the owner asks, as on the ground floor. | Walls, stair, lift and the void stay as built; each later answer is a change to it. |
| FF2 | How the master suite meets the brief | **A: keep its walls (75.3 m2) and fit the brief's contents inside:** sitting area in the bedroom by the balcony, his and hers walk-in wardrobes in the dressing room, a coffee station between them, a bathroom with a bathtub and a separate shower. | No GFA change. Layout drawn on sketch VJH-SK-015 for the owner to check. The 2.2 to 2.5 times ratio to the other bedrooms (today about 1.9) is settled with the bedrooms. |
| FF3 | Is the master suite right as sketched (VJH-SK-015) | **A: yes, as sketched.** | Bedroom and private sitting 5.50 x 7.50 m (41.2 m2), his and hers dressing 3.99 x 4.51 m (18.0 m2) with 4.3 m of wardrobes each side and an island, bath 3.99 x 4.01 m (16.0 m2) with tub, walk-in shower, two basins and a WC room, coffee station 1.80 m; clear height 3.55 m; suite 75.3 m2. To be modelled with the first floor build. |
| FF4 | Where the brief's 6 m2 linen store comes from | **C: no separate linen store; linen goes into built-in cupboards** (for example in the dressing rooms). | A departure from the brief (CLAUDE.md section 4, first floor: linen and general storage 6 m2), the owner's decision. Bedrooms 2 and 3 keep their sizes (39.5 and 37.9 m2). At the first floor build, brief/program.yaml moves linen_storage from deferred to removed, citing FF4; OI-27 item closed. |
| FF5 | What the family room should be | **A: open the family room onto the gallery**, removing the wall and the double doors F13. | One open family room of about 33.7 m2 (363 sq ft) with the gallery, looking over the double height foyer through the glass balustrade; clear height 3.55 m. Bedroom 3 is entered from its open side (door F06). Follows D-033 (family hall is a shared space). No GFA change. To be built with the first floor. |
| FF6 | How much GFA margin to keep | **A: keep 1.30 m2.** No step back of bedrooms 2 and 3. | The owner accepts that the consultant's measurement could take the house over the cap; the D-005 reserve (9.99 m2) and the 5 m2 floor are declined for now. Bedrooms 2 and 3 keep 4.50 x 5.49 m and 4.50 x 5.50 m. The two strict expected failures in tests/test_layout.py now cite FF6. |
| FF7 | How the TV wall meets the first floor wall above | **A: line them up.** The first floor wall between the living room void and bedroom 4 moves 0.21 m to stand on the TV wall, one surface from floor to ceiling. | Bedroom 4 4.35 x 5.50 m = 23.9 m2 (257 sq ft), clear height 3.55 m (was 24.7 m2); the void grows 0.87 m2, GFA about 660.82 m2, margin about 2.17 m2. To be built with the first floor. |
| FF8 | Is the first floor right, as on VJH-SK-016 | **A: yes, build it.** | Built 2026-10-02 (D-050): FF4, FF5 and FF7 applied in src/model/assemble_reference.py (apply_first_floor_answers), model, floor plans VJH-GA-001 and walkthrough rebuilt. GFA 660.82 m2, margin 2.17 m2. Master suite furniture (FF3) follows with the Phase 4 furniture. |
