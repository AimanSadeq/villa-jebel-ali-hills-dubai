# Redesign: the owner's answers

CONCEPT DESIGN, NOT FOR CONSTRUCTION.

On 2026-10-23 Aiman adopted the handover from his work with another assistant
as the brief for a redesign (answer H1: A, D-060), and asked for the look and
feel first, technical detail later. Questions are asked one at a time; every
answer is recorded here, newest last, and logged in docs/decisions.md once a
set is complete.

| No. | Question | Answer | Consequence |
|---|---|---|---|
| H1 | Which design to work on: the handover, or the current four bedroom design | **A: the handover replaces the current design.** | D-060. The earlier design stays as history. |
| S1 | The look of the new villa: white minimalist, the warm modern of 2 October, or a mix | **A: the white minimalist villa:** white volumes, flat roofs, charcoal accents, as in the handover and the owner's ChatGPT images. | Supersedes the facade character of D-048 and D-051 for the new design. The owner's images are the style reference once received. |
| S2 | Where the open courtyard (about 22 m2, a statement tree) sits | **A: in the middle of the house,** between the entrance foyer and the family living, seen from the foyer, the salon and the living room; it lights the deep middle of the plan at the cost of a few metres of corridor. | Fixes the plan's organising idea: rooms around a central court. |
| S3 | The formal reception room: salon, or majlis as the handover calls it | **A: salon.** | D-047 stands: salon everywhere, never majlis, in the new design too. |
| S4 | Which side of the road frontage the open two car carport sits on | **A: the south corner,** as in the current design; kitchens and staff rooms stay south, the entrance in the middle of the frontage. | Service side fixed south. |
| S5 | Home office: upstairs workspace only (handover), ground floor office only, or both | **A: upstairs workspace only,** in the family lounge. | No ground floor office or office WC in the new program. |
| S6 | Floor heights: 4.5 m ground and 3.6 m first, 5.0 and 4.0 as now, or 4.0 and 3.4 | **B: 5.0 m ground, 4.0 m first,** as the current design: the grandest foyer and living room, 10.2 m overall with the 1.20 m parapet. | D-030 stands for the new design. Stair of 28 risers over 5.0 m, as now (OI-23 TO VERIFY). |
| S7 | Start the first design now, or wait for the owner's ChatGPT images | **B: wait for the images.** | The first design is drawn only after the images arrive, so it follows them from the start. |

## The owner's images, received 2026-10-23

One board from his work with the other assistant: a front elevation from the
road, a rear elevation from the garden, both floor plans, and four interiors
(the double height foyer with a floating stair and a tree, the family living
toward the garden, the dining with the courtyard, the master bedroom). What the
redesign takes from it as the style reference (S1: A): white render volumes
with flat roofs; a charcoal stone volume around the double height entrance;
timber soffits under the eaves and the carport; vertical timber fins; large
glass in slim dark frames; warm interiors with timber slat walls, light stone
floors and cream furniture; palms and planted beds at the front. What it does
not take, because the handover corrected it: the fourth bedroom, the linen
room, the word majlis, the planted roof over the guest suite, and the garden
figure of 12 x 20 m, which was never measured. The board is not stored in the
repository (it could not be saved from the chat); the owner holds it.

| No. | Question | Answer | Consequence |
|---|---|---|---|
| R1 | Does the courtyard villa go in the right direction (plans and seven renders sent 2026-10-23) | Not answered yet: the owner's reaction was that the images are very basic. | The design stays for review; the image upgrade goes first. |
| U1 | Which image upgrade first: a Twinmotion step list, laptop renders with textures, or an AI finishing prompt | **A: the Twinmotion step list.** | docs/twinmotion-steps-courtyard-villa.md: the exact import, material, vegetation and camera steps for this house. The other two upgrades remain available. |
| U2 | The laptop render upgrade (the owner, 2026-10-23: "now do the laptop render upgrade too") | **Done in renders/render_villa.py:** quality presets (preview, medium, high) with adaptive sampling and the OpenImageDenoise denoiser, the fetched sky photographs as the visible sky dome with the physical sky still lighting the scene, light portals at the garden glass and the courtyard, translucent foliage, depth of field in the interior views. | Run on the laptop after assets/fetch_assets.py: `python renders/render_villa.py --all --device GPU --quality high`. |
| U3 | The browser walkthrough: "Not like Twinmotion at all. It does not render any real images. Very hard to use" (the owner, 2026-10-23). Which route for the realistic images: an AI finish over the renders, Twinmotion on the laptop, Blender on the laptop GPU, or Blender in the cloud | **A: the AI finish over the renders.** | D-063: five of the seven views finished in the owner's Canva account (entrance, foyer, courtyard, living, master bedroom); the garden at sunset and the aerial followed the same day once the image credits allowed, so all seven exist. The walkthrough itself got a "Go to a room" list and a hosted copy. |
| U4 | "Open everything on the right side so I can see as I make changes on the left side" (the owner, 2026-10-23) | **The design board** (D-064), a hosted page with the seven views, the AI-finished links, the plans, the room schedule and the GFA. | Rebuilt and republished after every change: `python src/drawings/design_board.py`. |
