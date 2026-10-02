"""The door schedule of Villa 5130272, and how each door finds its wall.

One table per floor, each door tagged with where it comes from: the reference
set (reference/owner/transcription/*.json records the doors it could read), an
owner answer (docs/ground-floor-decisions.md), or an assumption to confirm.
Positions are in the frame of brief/reference_plan.yaml: x along the road from
the carport end, y from the road. Door heights are indicative.

src/model/assemble_reference.py copies the table into brief/reference_plan.yaml;
src/model/reference_plan.py resolves every door to its wall in the plot grid
and refuses a plan where any room has no way in; the IFC generator, the floor
plans and the decision sketches all draw from that one list.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations


# Interior doors between two rooms: (no, a, b, width, height, kind, swing_into,
# centre along the wall or None for the middle of the shared wall, source).
# Kinds: single, double, pivot, sliding, open (an opening without a leaf), lift.
GROUND = [
    ("G02", "entrance_foyer", "home_office", 0.90, 2.70, "single", "home_office", None,
     "reference: door in the office's foyer wall"),
    ("G03", "home_office", "office_toilet", 0.80, 2.40, "single", "office_toilet", None,
     "reference: the toilet's only door is from the office"),
    ("G04", "entrance_foyer", "guest_bedroom", 0.90, 2.70, "single", "guest_bedroom", None,
     "answer 12f: from the foyer (not readable on the reference)"),
    ("G05", "guest_dress", "guest_toilet", 0.80, 2.40, "single", "guest_toilet", None,
     "reference: toilet entered from the dress"),
    ("G07", "entrance_foyer", "living", 6.90, 0.0, "open", "living", None,
     "reference: the foyer opens into the garden room (D-033)"),
    ("G08", "lift", "stair_hall", 0.90, 2.10, "lift", "stair_hall", None,
     "model: home lift door, size TO VERIFY with the lift supplier (OI-23)"),
    ("G09", "service_lobby", "stair_hall", 0.90, 2.70, "single", "service_lobby", None,
     "reference: door in the service lobby's top wall"),
    ("G11", "stair_hall", "wash", 0.90, 2.40, "single", "wash", None,
     "reference: wash entered from the stair hall"),
    ("G12", "wash", "guest_powder", 0.80, 2.40, "single", "guest_powder", None,
     "reference: powder room entered through the wash"),
    ("G13", "maids_room", "maids_toilet", 0.80, 2.40, "single", "maids_toilet", None,
     "reference: toilet door in the maid's room wall"),
    ("G14", "laundry", "maids_room", 0.80, 2.40, "single", "maids_room", None,
     "model (D-044): maid's room reached through the laundry"),
    ("G18", "service_passage", "pantry", 0.90, 2.40, "single", "pantry", None,
     "model (D-044): store off the service passage"),
    ("G19", "service_passage", "show_kitchen", 0.80, 2.40, "single", "show_kitchen", None,
     "reference: door from the passage into the island kitchen; swings into the kitchen, "
     "clear of the 1.0 m passage (review, 2026-10-02)"),
    ("G23", "show_kitchen", "arabic_kitchen", 1.20, 2.40, "open", "arabic_kitchen", 19.50,
     "answer 12m: open entrance from the island kitchen, no door leaf"),
]
FIRST = [
    ("F01", "corridor_first", "master_suite", 1.00, 2.40, "single", "master_suite", 15.67,
     "reference: master door from the corridor"),
    ("F02", "master_suite", "master_dress", 1.00, 2.40, "open", "master_dress", 5.75,
     "reference: doorless opening"),
    ("F03", "master_dress", "master_toilet", 0.80, 2.40, "single", "master_toilet", 5.50,
     "reference: master bath from the dress"),
    ("F04", "lift_lobby", "bedroom_2", 1.00, 2.40, "single", "bedroom_2", 14.20,
     "reference: bedroom 2 from the lift lobby"),
    ("F05", "bedroom_2_dress", "bedroom_2_toilet", 0.80, 2.40, "single", "bedroom_2_toilet", 8.35,
     "reference: toilet from the dress"),
    ("F06", "gallery", "bedroom_3", 1.00, 2.40, "single", "bedroom_3", 19.85,
     "reference: bedroom 3 from the gallery"),
    ("F07", "bedroom_3_dress", "bedroom_3_toilet", 0.80, 2.40, "single", "bedroom_3_toilet", 24.88,
     "reference: toilet from the dress"),
    ("F08", "corridor_first", "bedroom_4", 1.00, 2.40, "single", "bedroom_4", 15.65,
     "reference: bedroom 4 from the corridor"),
    ("F09", "bedroom_4_dress", "bedroom_4_toilet", 0.80, 2.40, "single", "bedroom_4_toilet", 26.15,
     "reference: toilet from the dress"),
    ("F10", "corridor_first", "pantry_first", 1.00, 2.40, "open", "pantry_first", 12.60,
     "reference: open entry; moved 0.95 m by the living room void"),
    ("F11", "pantry_first", "linen_storage", 0.80, 2.40, "single", "linen_storage", 12.60,
     "reference: store from the pantry; moved by the void. Retired by 12l, store removed by FF4"),
    ("F12", "lift_first", "lift_lobby", 0.90, 2.10, "lift", "lift_lobby", None,
     "reference: lift door on the lobby face; size TO VERIFY (OI-23)"),
    ("F13", "gallery", "family_living", 1.60, 2.40, "double", "family_living", None,
     "answer 12b: family room off the gallery; double doors proposed. Retired by FF5 (open)"),
]
# External doors: (no, room, wall axis, wall lo, wall hi, centre, width, height,
# kind, source). Axis "y": the wall spans frame y lo..hi and the door runs
# along x; axis "x": the wall spans frame x lo..hi and the door runs along y.
GROUND_EXT = [
    ("G01", "entrance_foyer", "y", 9.49, 9.74, 17.05, 2.40, 4.50, "pivot",
     "answer 12i: tall pivot door at the back of the porch, fixed glass above to full height"),
    ("G10", "service_steps", "y", 8.79, 9.04, 8.26, 1.20, 0.0, "open",
     "reference: opening from the carport, no leaf"),
    ("G15", "laundry", "x", 2.81, 3.06, 16.68, 0.90, 2.40, "single",
     "reference: side door to the service yard"),
    ("G16", "plant_room", "x", 2.81, 3.06, 9.88, 0.90, 2.40, "single",
     "answers 9 and 11a: the old driver's outside door"),
    ("G17", "outdoor_bathroom", "y", 8.99, 9.24, 6.71, 0.80, 2.20, "single",
     "answer 11a: opens onto the carport"),
    ("G20", "living", "y", 21.04, 21.29, 17.11, 3.00, 3.00, "sliding",
     "answer 12j: garden door of the living room; kitchen rear glass fixed"),
    ("G22", "dining", "y", 21.04, 21.29, 23.74, 3.00, 3.00, "sliding",
     "answer 12k: garden door of the dining, as the living room's, centred on its back wall"),
    ("G21", "arabic_kitchen", "y", 21.04, 21.29, 4.40, 1.00, 2.40, "single",
     "answer 12j: service door from the Arabic kitchen to the backyard, laundry end; position proposed"),
]
FIRST_EXT = [
    ("F14", "master_suite", "y", 20.55, 20.80, 6.80, 3.00, 2.40, "sliding",
     "reference: glazed rear wall to the master balcony"),
    ("F15", "bedroom_4", "y", 20.55, 20.80, 22.90, 2.00, 2.40, "sliding",
     "reference: glazed rear wall to the bedroom 4 balcony"),
]

WALL_MIN, WALL_MAX = 0.05, 0.45


def shared_wall(a: dict, b: dict):
    """(axis, lo, hi, s0, s1): the wall between two rectangles, its thickness
    lo..hi on the axis it crosses, and the shared length s0..s1 along it."""
    for ax, other in (("x", "y"), ("y", "x")):
        for p, q in ((a, b), (b, a)):
            gap = q[ax + "0"] - p[ax + "1"]
            if WALL_MIN - 1e-3 <= gap <= WALL_MAX + 1e-3:
                s0, s1 = max(a[other + "0"], b[other + "0"]), min(a[other + "1"], b[other + "1"])
                if s1 - s0 > 0.3:
                    return ax, p[ax + "1"], q[ax + "0"], s0, s1
    return None



def resolve(rooms: list, entries: list[dict]) -> list[dict]:
    """Resolve door entries (as src/model/assemble_reference.py writes them
    into the plan) to wall geometry in the plan frame. Raises if an interior
    door has no shared wall, so no door is ever dropped silently."""
    by = {r["key"]: r for r in rooms}
    out = []
    for d in entries:
        kind, w = d["kind"], float(d["width_m"])
        if d["b"] == "outside":
            axis, lo, hi, c = d["axis"], float(d["lo"]), float(d["hi"]), float(d["at"])
            width = w
        else:
            sw = shared_wall(by[d["a"]], by[d["b"]])
            if sw is None:
                raise ValueError(f"{d['no']}: {d['a']} and {d['b']} share no wall")
            axis, lo, hi, s0, s1 = sw
            width = min(w, s1 - s0 - 0.2) if kind != "open" else min(w, s1 - s0)
            c = d["at"] if d.get("at") is not None else (s0 + s1) / 2
            if kind != "open":
                c = min(max(c, s0 + width / 2 + 0.05), s1 - width / 2 - 0.05)
        r_in = by[d["swing_into"]]
        s = 1 if (r_in[axis + "0"] + r_in[axis + "1"]) / 2 > hi else -1
        out.append(dict(no=d["no"], a=d["a"], b=d["b"], axis=axis, lo=lo, hi=hi, c=c, w=width,
                        h=float(d["height_m"]), kind=kind, s=s, src=d["source"]))
    return sorted(out, key=lambda x: x["no"])


def table_entries(floor: str, removed: frozenset = frozenset()) -> list[dict]:
    """The schedule above for one floor, as plan entries."""
    out = []
    for no, a, b, w, h, kind, into, at, src in (GROUND if floor == "ground" else FIRST):
        if a in removed or b in removed:
            continue
        out.append({"no": no, "a": a, "b": b, "width_m": w, "height_m": h, "kind": kind,
                    "swing_into": into, "at": at, "source": src})
    for no, r, axis, lo, hi, c, w, h, kind, src in (GROUND_EXT if floor == "ground" else FIRST_EXT):
        out.append({"no": no, "a": r, "b": "outside", "axis": axis, "lo": lo, "hi": hi, "at": c,
                    "width_m": w, "height_m": h, "kind": kind, "swing_into": r, "source": src})
    return out


def place(rooms: list, floor: str, removed: frozenset = frozenset()) -> list[dict]:
    """The schedule for one floor resolved against the given rooms. Doors of
    rooms named in `removed` (taken out on purpose) are left out."""
    return resolve(rooms, table_entries(floor, removed))


def unreached(rooms: list, doors: list[dict], open_pairs: set, start: str) -> list[str]:
    """Rooms that cannot be reached from `start` through doors and open joins."""
    edges = {}
    for d in doors:
        if d["b"] == "outside":
            continue
        edges.setdefault(d["a"], set()).add(d["b"])
        edges.setdefault(d["b"], set()).add(d["a"])
    for p in open_pairs:
        a, b = tuple(p)
        edges.setdefault(a, set()).add(b)
        edges.setdefault(b, set()).add(a)
    seen, todo = {start}, [start]
    while todo:
        k = todo.pop()
        for n in edges.get(k, ()):
            if n not in seen:
                seen.add(n)
                todo.append(n)
    return [r["key"] for r in rooms if r["key"] not in seen]

