"""The courtyard villa: the redesign of 2026-10-23 (D-060, answers H1 to S7).

The plan is laid out here as rectangles in the plot building grid of
brief/massing.yaml (u from the road toward the garden, v from the SSW
neighbour toward the NNE neighbour, metres), checked, and written to
brief/layouts.yaml in the same schema src/model/layout_gen.py and
src/model/reference_plan.py produce, so the GFA check, the IFC generator, the
drawings, the walkthrough, the renders and the Twinmotion export all work
unchanged.

The organising idea (S2: A): an open courtyard in the middle of the house,
between the double height entrance foyer and the dining, with the family
rooms along the garden side, the salon and the guest suite along the north,
the service rooms along the south by the open two car carport (S4: A). Three
bedrooms upstairs (the handover), the master over the dining with its terrace
to the garden. The stair is a straight floating stair in two flights along
the courtyard's north glass, rising westward into the double height foyer.

Every wall is 0.15 m inside and 0.25 m outside; room rectangles are the clear
room, so two rooms 0.15 m apart share a partition and a room 0.25 m inside an
outline edge stands on an external wall.

Run: python src/model/layout_court.py          writes brief/layouts.yaml

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from collections import deque
from itertools import combinations
from pathlib import Path

import yaml
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis.gfa_check import totals  # noqa: E402
from model.interiors import Rect, shared  # noqa: E402
from model.massing import site_to_grid  # noqa: E402
from model.site import buildable_envelope  # noqa: E402

OUT = REPO_ROOT / "brief" / "layouts.yaml"
T_EXT, T_INT = 0.25, 0.15
STAMP = "CONCEPT DESIGN, NOT FOR CONSTRUCTION"

# Levels above the gate level (the garden ground), as the reference set
# states them (A-09-001, D-044): the house floor is 0.45 m up.
LEVELS = {"ground_ffl_above_gate_m": 0.45, "carport_ffl_above_gate_m": 0.15,
          "first_ffl_above_gate_m": 5.45, "carport_roof_m": 3.75,
          "source": "reference sheet A-09-001 levels kept for the redesign (D-060)"}


def R(key, u0, u1, v0, v1):
    return {"key": key, "u": [u0, u1], "v": [v0, v1]}


# Ground floor. Rows from the south (the carport side): the service row with
# its corridor, the courtyard row, the hall with the stair, the lobby row and
# the north row. Columns: the road side (F), the courtyard (C), the garden (B).
GROUND_ROOMS = [
    # Service row (v 10.15 to 15.00) behind the carport, served by a corridor
    # along the south wall with the sheltered service door from the carport.
    R("maids_room", 4.25, 6.85, 11.80, 15.00),
    R("maids_toilet", 7.00, 8.50, 11.80, 15.00),
    R("laundry", 8.65, 10.75, 11.80, 15.00),
    R("arabic_kitchen", 10.90, 13.65, 11.80, 15.00),
    R("show_kitchen", 13.80, 18.75, 10.15, 15.00),
    R("plant_room", 10.75, 13.65, 7.50, 9.90),          # single storey block beside the carport
    # Courtyard row: foyer, open court, dining and garden room.
    R("entrance_foyer", 4.25, 9.00, 15.25, 19.85),
    R("courtyard", 9.15, 13.65, 15.25, 19.85),            # open to the sky
    R("dining", 13.80, 18.75, 15.25, 23.30),
    # Lobby row north of the hall.
    R("lift", 4.25, 5.85, 23.45, 25.60),
    R("guest_powder", 7.55, 9.00, 23.45, 25.60),
    R("guest_toilet", 10.80, 13.65, 23.45, 25.60),
    # North row.
    R("salon", 4.25, 9.00, 25.75, 30.15),
    R("guest_bedroom", 9.15, 13.65, 25.75, 30.15),
    R("living", 13.80, 18.75, 23.45, 30.15),
]
GROUND_CIRC = [
    R("service_corridor", 4.25, 13.65, 10.15, 11.65),
    R("hall", 4.25, 13.65, 20.00, 23.30),                 # the stair hall along the courtyard
    R("salon_lobby", 6.00, 7.40, 23.45, 25.60),
    R("guest_lobby", 9.15, 10.65, 23.45, 25.60),
]
FIRST_ROOMS = [
    R("master_dress", 13.80, 16.20, 10.15, 15.00),
    R("master_toilet", 16.35, 18.75, 10.15, 15.00),
    R("master_suite", 13.80, 18.75, 15.25, 19.85),
    R("lift_first", 4.25, 5.85, 23.45, 25.60),
    R("workspace", 6.00, 9.00, 23.45, 25.60),
    R("bedroom_2_toilet", 9.15, 11.50, 23.45, 25.60),
    R("bedroom_3_dress", 13.80, 16.20, 23.45, 25.60),
    R("bedroom_3_toilet", 16.35, 18.75, 23.45, 25.60),
    R("family_living", 4.25, 9.00, 25.75, 30.15),
    R("bedroom_2", 9.15, 13.65, 25.75, 30.15),
    R("bedroom_3", 13.80, 18.75, 25.75, 30.15),
]
FIRST_CIRC = [
    R("gallery", 9.00, 18.75, 20.00, 23.30),
    R("gallery_west", 4.25, 9.00, 21.50, 23.30),           # the bridge over the foyer's north edge
    R("north_lobby", 11.65, 13.65, 23.45, 25.60),
]
VOIDS = [
    R("void_over_foyer", 4.25, 9.00, 15.25, 21.50),       # the foyer and the stair's upper flight
    R("void_over_courtyard", 9.15, 13.65, 15.25, 19.85),  # open to the sky
]
FIRST_OUTDOOR = [
    R("balcony_master", 19.00, 21.00, 15.25, 19.85),      # covered terrace to the garden
]
GROUND_OUTLINE = [(4.00, 9.90), (10.50, 9.90), (10.50, 7.25), (13.90, 7.25), (13.90, 9.90),
                  (19.00, 9.90), (19.00, 30.40), (4.00, 30.40)]
FIRST_OUTLINE = [(13.55, 9.90), (19.00, 9.90), (19.00, 30.40), (4.00, 30.40), (4.00, 15.00),
                 (13.55, 15.00)]
CARPORT = {"u": [4.00, 10.50], "v": [3.90, 9.90]}      # open, two cars, provisional 6.5 x 6.0

OPEN_JOINS = {
    "ground": ["entrance_foyer/hall", "hall/dining", "show_kitchen/dining", "dining/living",
               "hall/salon_lobby"],
    "first": ["gallery/gallery_west", "gallery_west/workspace", "workspace/family_living",
              "gallery/north_lobby"],
}
DOUBLE_HEIGHT = ["entrance_foyer"]
OPEN_TO_SKY = ["courtyard"]

# The straight stair (the handover): two flights of 14 risers along the
# courtyard's north glass in the hall, the lower flight rising westward from
# the dining end, a landing, the upper flight floating in the foyer void and
# landing on the gallery bridge. Lane v 20.30 to 21.50.
STAIR = {"kind": "straight", "hall": "hall", "lift": "lift", "v": [20.30, 21.50],
         "u_foot": 13.30, "direction": -1, "going_m": 0.27, "landing_m": 1.20,
         "tread_m": 0.08, "rail_m": 1.10}

# Doors between rooms: number, from, to, kind, width, height, position along
# the shared wall (None: its middle), source. Kinds as src/model/doors.py plus
# "fixed" (fixed glass, no passage). Heights 0 mean the full storey height.
DOORS = {
    "ground": [
        ("G01", "entrance_foyer", "outside", "pivot", 1.50, 3.00, ("W", None),
         "front door, glass above to the double height (D-046 12i)"),
        ("G02", "service_corridor", "outside", "single", 0.90, 2.40, ("S", 5.00),
         "service door from the carport, sheltered (handover)"),
        ("G03", "service_corridor", "maids_room", "single", 0.90, 2.40, None, "handover: maid's room"),
        ("G04", "maids_room", "maids_toilet", "single", 0.70, 2.40, None, "maid's bathroom"),
        ("G05", "service_corridor", "laundry", "single", 0.90, 2.40, None, "laundry"),
        ("G06", "service_corridor", "arabic_kitchen", "single", 0.90, 2.40, None, "Arabic kitchen, service side"),
        ("G07", "arabic_kitchen", "show_kitchen", "single", 0.90, 2.40, None, "prep kitchen behind the show kitchen"),
        ("G08", "service_corridor", "plant_room", "single", 0.90, 2.40, None, "plant room"),
        ("G09", "show_kitchen", "outside", "sliding", 2.40, 2.70, ("E", 12.60),
         "kitchen door to the BBQ terrace"),
        ("G10", "entrance_foyer", "courtyard", "sliding", 4.00, 4.20, None,
         "glass wall between the foyer and the courtyard (S2)"),
        ("G11", "dining", "courtyard", "sliding", 4.00, 4.20, None,
         "glass wall between the dining and the courtyard (S2)"),
        ("G12", "hall", "courtyard", "fixed", 4.20, 4.20, None,
         "fixed glass behind the floating stair"),
        ("G13", "arabic_kitchen", "courtyard", "fixed", 2.40, 0.60, (None, 1.80),
         "high window onto the courtyard: light and air for the closed kitchen (OI-15)"),
        ("G14", "dining", "outside", "sliding", 4.80, 4.20, ("E", 19.30), "garden doors, dining"),
        ("G15", "living", "outside", "sliding", 4.80, 4.20, ("E", 26.80), "garden doors, family living (handover)"),
        ("G16", "hall", "lift", "lift", 0.90, 2.10, None, "home lift, size TO VERIFY (OI-23)"),
        ("G17", "salon_lobby", "salon", "double", 1.40, 2.70, None, "salon from its lobby, privacy (handover)"),
        ("G18", "salon_lobby", "guest_powder", "single", 0.80, 2.40, None, "powder room beside the salon"),
        ("G19", "hall", "guest_lobby", "single", 0.90, 2.40, None, "guest lobby, privacy (handover)"),
        ("G20", "guest_lobby", "guest_bedroom", "single", 0.90, 2.40, None, "guest bedroom"),
        ("G21", "guest_bedroom", "guest_toilet", "single", 0.80, 2.40, None, "guest bathroom, accessible (handover, TO VERIFY)"),
    ],
    "first": [
        ("F01", "gallery_west", "lift_first", "lift", 0.90, 2.10, None, "home lift"),
        ("F02", "north_lobby", "bedroom_2", "single", 0.90, 2.40, None, "bedroom 2"),
        ("F03", "bedroom_2", "bedroom_2_toilet", "single", 0.80, 2.40, None, "bedroom 2 en-suite"),
        ("F04", "north_lobby", "bedroom_3_dress", "single", 0.90, 2.40, None, "bedroom 3 through its dressing room"),
        ("F05", "bedroom_3_dress", "bedroom_3", "single", 0.90, 2.40, None, "bedroom 3"),
        ("F06", "bedroom_3", "bedroom_3_toilet", "single", 0.80, 2.40, None, "bedroom 3 en-suite"),
        ("F07", "gallery", "master_suite", "single", 1.00, 2.40, (17.30,),
         "master suite from the gallery, at the terrace end so the bed wall stays clear"),
        ("F08", "master_suite", "master_dress", "single", 0.90, 2.40, None, "walk-in wardrobe from the bedroom (handover)"),
        ("F09", "master_dress", "master_toilet", "single", 0.80, 2.40, None, "shower bathroom from the wardrobe (handover)"),
        ("F10", "master_suite", "outside", "sliding", 3.00, 2.70, ("E", None), "terrace door"),
        ("F11", "master_suite", "void_over_courtyard", "fixed", 3.00, 1.60, (None, 0.90),
         "window from the master bedroom onto the courtyard"),
        ("F12", "gallery", "void_over_courtyard", "fixed", 4.20, 1.60, (None, 0.90),
         "gallery window onto the courtyard"),
    ],
}


def rects(items):
    return {d["key"]: Rect.of(d) for d in items}


def _place(a: Rect, b, spec):
    """A door on the wall a shares with b (a Rect, or a face letter for the
    outside): centre (u, v), along_u, wall thickness."""
    if isinstance(b, str):                      # outside, on a given face
        face, at = spec
        if face in ("W", "E"):
            u = a.u0 - T_EXT / 2 if face == "W" else a.u1 + T_EXT / 2
            return u, (at if at is not None else (a.v0 + a.v1) / 2), False, T_EXT
        v = a.v0 - T_EXT / 2 if face == "S" else a.v1 + T_EXT / 2
        return (at if at is not None else (a.u0 + a.u1) / 2), v, True, T_EXT
    s = shared(a, b)
    if s is None:
        raise ValueError(f"{a.key} and {b.key} share no wall")
    side, lo, hi, gap = s
    at = spec[0] if spec and spec[0] is not None else None
    c = at if at is not None else (lo + hi) / 2
    if side in ("N", "S"):
        v = a.v1 + gap / 2 if side == "N" else a.v0 - gap / 2
        return c, v, True, gap
    u = a.u1 + gap / 2 if side == "E" else a.u0 - gap / 2
    return u, c, False, gap


def resolve_doors() -> list[dict]:
    out = []
    for floor, rooms, circ, extra in (("ground", GROUND_ROOMS, GROUND_CIRC, []),
                                      ("first", FIRST_ROOMS, FIRST_CIRC, VOIDS)):
        rr = rects(rooms + circ + extra)
        for no, a, b, kind, w, h, pos, src in DOORS[floor]:
            A = rr[a]
            if b == "outside":
                u, v, along_u, t = _place(A, "outside", pos)
                sill = 0.0
            else:
                B = rr[b]
                u, v, along_u, t = _place(A, B, (pos[0],) if pos else None)
                sill = pos[1] if pos and len(pos) > 1 and pos[1] is not None else 0.0
                s = shared(A, B)
                length = s[2] - s[1]
                if w > length + 1e-6:
                    raise ValueError(f"door {no}: {w:.2f} m wide on a {length:.2f} m wall")
            out.append({"no": no, "storey": floor, "a": a, "b": b, "kind": kind,
                        "width_m": round(w, 3), "height_m": h, "u": round(u, 3), "v": round(v, 3),
                        "along_u": along_u, "wall_t": round(t, 3), "swing": 1,
                        "sill_m": round(sill, 3), "source": src})
    return out


def check(doors: list[dict]) -> list[str]:
    """Geometry a builder would care about: nothing overlaps, walls are the
    standard thickness, everything stays behind the setback line, and every
    room can be reached. Returns the failures (an empty list passes)."""
    bad: list[str] = []
    env = site_to_grid(buildable_envelope()).buffer(0.01)
    for floor, rooms, circ, outline in (("ground", GROUND_ROOMS, GROUND_CIRC, GROUND_OUTLINE),
                                        ("first", FIRST_ROOMS + VOIDS + FIRST_OUTDOOR, FIRST_CIRC,
                                         FIRST_OUTLINE)):
        rr = rects(rooms + circ)
        for a, b in combinations(rr.values(), 2):
            if a.poly.intersection(b.poly).area > 1e-6:
                bad.append(f"{floor}: {a.key} overlaps {b.key}")
        # Walls between neighbours: 0.15 inside, 0.25 at an outline edge.
        for a, b in combinations(rr.values(), 2):
            s = shared(a, b)
            if s and s[3] > 0.001 and abs(s[3] - T_INT) > 1e-3 and abs(s[3] - T_EXT) > 1e-3:
                bad.append(f"{floor}: wall between {a.key} and {b.key} is {s[3]:.3f} m")
        fp = Polygon(outline)
        if not env.contains(fp):
            bad.append(f"{floor}: outline leaves the 3 m setback envelope")
        inner = fp.buffer(-T_EXT, join_style=2, mitre_limit=10)
        for r in rr.values():
            if r.key.startswith("balcony"):
                if not env.contains(r.poly):
                    bad.append(f"{floor}: {r.key} leaves the setback envelope")
                continue
            if not inner.buffer(0.001).contains(r.poly):
                bad.append(f"{floor}: {r.key} is not 0.25 m inside the outline")
    if not env.contains(box(CARPORT["u"][0], CARPORT["v"][0], CARPORT["u"][1], CARPORT["v"][1])):
        bad.append("carport leaves the setback envelope")
    # Reachability: ground from the front door, first from the stair arrival.
    for floor, start, rooms, circ in (("ground", "entrance_foyer", GROUND_ROOMS, GROUND_CIRC),
                                      ("first", "gallery_west", FIRST_ROOMS, FIRST_CIRC)):
        keys = {d["key"] for d in rooms + circ}
        links: dict[str, set] = {k: set() for k in keys}
        for d in doors:
            if d["storey"] == floor and d["kind"] != "fixed" and d["b"] in keys:
                links[d["a"]].add(d["b"])
                links[d["b"]].add(d["a"])
        for j in OPEN_JOINS[floor]:
            a, b = j.split("/")
            links[a].add(b)
            links[b].add(a)
        seen, q = {start}, deque([start])
        while q:
            for n in links[q.popleft()]:
                if n not in seen:
                    seen.add(n)
                    q.append(n)
        for k in sorted(keys - seen):
            bad.append(f"{floor}: no way into {k}")
    # The handover's acceptance test: the first floor is enclosed over the
    # guest suite and the powder room, with no terrace or void above them.
    g = rects(GROUND_ROOMS)
    target = unary_union([g[k].poly for k in ("guest_bedroom", "guest_toilet", "guest_powder")])
    enclosed = unary_union([r.poly for r in rects(FIRST_ROOMS + FIRST_CIRC).values()])
    enclosed = enclosed.buffer(0.08, join_style=2).buffer(-0.08, join_style=2)
    covered = target.intersection(enclosed).area / target.area
    if covered < 0.999:
        bad.append(f"first floor covers only {covered:.1%} of the guest suite and powder room")
    opens = unary_union([Rect.of(d).poly for d in VOIDS + FIRST_OUTDOOR])
    if opens.intersection(target).area > 1e-6:
        bad.append("a void or terrace lies over the guest suite or the powder room")
    return bad


def gfa() -> dict:
    ground = Polygon(GROUND_OUTLINE)
    court = Rect.of(next(d for d in GROUND_ROOMS if d["key"] == "courtyard")).poly
    first = Polygon(FIRST_OUTLINE)
    void = sum(Rect.of(d).poly.area for d in VOIDS)
    carport = box(CARPORT["u"][0], CARPORT["v"][0], CARPORT["u"][1], CARPORT["v"][1])
    carport = carport.difference(ground.buffer(0.01)).area
    g = ground.area - court.area
    f = first.area - void
    t = totals()
    return {"road_wing_ground": round(g, 2), "ssw_wing_ground": 0.0, "living_block_ground": 0.0,
            "first_floor_less_void": round(f, 2), "first_floor_voids": round(void, 2),
            "courtyard_open_to_sky_m2": round(court.area, 2),
            "total": round(g + f, 2), "cap": t["cap_m2"], "margin": round(t["cap_m2"] - g - f, 2),
            "outside_gfa_to_verify": {"carport_m2": round(carport, 2), "lawn_court_m2": 0.0,
                                      "first_floor_balconies_terrace_m2":
                                          round(sum(Rect.of(d).poly.area for d in FIRST_OUTDOOR), 2)}}


def _with_area(items):
    out = []
    for d in items:
        r = Rect.of(d)
        out.append({"key": d["key"], "u": [round(r.u0, 3), round(r.u1, 3)],
                    "v": [round(r.v0, 3), round(r.v1, 3)], "area_m2": round(r.poly.area, 2)})
    return out


def layout() -> dict:
    doors = resolve_doors()
    bad = check(doors)
    if bad:
        raise SystemExit("layout_court: the plan fails its checks:\n  " + "\n  ".join(bad))
    g = gfa()
    return {
        "meta": {"stamp": STAMP, "phase": 2, "massing_option": "Q", "plan_direction": "court",
                 "note": "Generated by src/model/layout_court.py (D-060). Do not edit by hand.",
                 "corridor_m": 1.80, "wall_external_m": T_EXT, "wall_internal_m": T_INT},
        "params": {"front_u": 4.0, "back_u": 19.0, "mirror": 0},
        "plates": {"road": {"u": [4.0, 19.0], "v": [9.9, 30.4]},
                   "first": {"u": [4.0, 19.0], "v": [9.9, 30.4]},
                   "carport": CARPORT},
        "gfa_measured": g,
        "outlines": {"road_ground": [list(p) for p in GROUND_OUTLINE],
                     "ground": [list(p) for p in GROUND_OUTLINE],
                     "first": [list(p) for p in FIRST_OUTLINE]},
        "reference": "reference/owner/Owner_handover_2026-10-23.md and the owner's images (D-060)",
        "open_joins": OPEN_JOINS,
        "room_links": [],
        "external_doors": [],
        "doors": doors,
        "double_height": DOUBLE_HEIGHT,
        "open_to_sky": OPEN_TO_SKY,
        "porches": [],
        "levels": LEVELS,
        "stair": STAIR,
        "pool": None, "deck": None, "padding": [],
        "floors": {
            "ground": {"rooms": _with_area(GROUND_ROOMS), "circulation": _with_area(GROUND_CIRC)},
            "first": {"rooms": _with_area(FIRST_ROOMS), "circulation": _with_area(FIRST_CIRC),
                      "voids": _with_area(VOIDS), "outdoor": _with_area(FIRST_OUTDOOR)},
        },
    }


def main() -> int:
    data = layout()
    OUT.write_text(yaml.safe_dump(data, sort_keys=False, width=88), encoding="utf-8")
    g = data["gfa_measured"]
    print(f"Wrote {OUT.relative_to(REPO_ROOT)}")
    print(f"  GFA measured: ground {g['road_wing_ground']:.2f} (courtyard {g['courtyard_open_to_sky_m2']:.2f} "
          f"open to the sky, excluded) + first {g['first_floor_less_void']:.2f} (voids "
          f"{g['first_floor_voids']:.2f} excluded) = {g['total']:.2f} m2; cap {g['cap']:.2f}, "
          f"margin {g['margin']:+.2f}")
    o = g["outside_gfa_to_verify"]
    print(f"  outside GFA, TO VERIFY: carport {o['carport_m2']:.2f}, terrace "
          f"{o['first_floor_balconies_terrace_m2']:.2f} m2")
    for floor in ("ground", "first"):
        print(f"  {floor}:")
        for r in data["floors"][floor]["rooms"] + data["floors"][floor]["circulation"]:
            w, l = r["u"][1] - r["u"][0], r["v"][1] - r["v"][0]
            print(f"    {r['key']:<18}{w:6.2f} x{l:6.2f} = {r['area_m2']:6.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
