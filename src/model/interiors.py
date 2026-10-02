"""Room interiors: en-suite bathrooms, wardrobes, and the master suite plan.

Reads brief/layouts.yaml (the rooms) and the interiors block of
brief/program.yaml (every size). Both the IFC generator and the floor plan
drawing call plan(), so the model and the drawings show the same interiors.

En-suite rooms (D-034, owner choice): the bathroom and a built-in wardrobe sit
beside the door, forming an entry lobby, and the bedroom keeps the facade. The
door wall is the wall the room shares with its hub (corridor, foyer, landing,
family hall or family room). The bathroom takes the end of that wall that is
not on the facade, so it never blocks a window, and next to it comes a clear
entry holding the door, then the wardrobe.

Master suite (D-035): a service zone on the road side holds the bathroom and
the his and hers walk-in wardrobes, reached along a dressing gallery from the
landing door. The bedroom and sitting area take the terrace side, with the
coffee station by the terrace door.

Coordinates are the plot building grid (u, v) in metres, as everywhere else.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parents[2]
LAYOUTS = REPO_ROOT / "brief" / "layouts.yaml"
PROGRAM = REPO_ROOT / "brief" / "program.yaml"

T_INT = 0.15
T_EXT = 0.25

# Where private rooms take their doors from, in order of preference (D-032,
# D-033). Shared with src/model/architecture.py.
HUBS = ["corridor", "entrance_foyer", "hall_arm", "family_hall", "family_living"]


@dataclass
class Rect:
    key: str
    u0: float
    u1: float
    v0: float
    v1: float

    @classmethod
    def of(cls, d):
        return cls(d["key"], d["u"][0], d["u"][1], d["v"][0], d["v"][1])

    @property
    def poly(self):
        return box(self.u0, self.v0, self.u1, self.v1)


@dataclass
class Opening:
    """A door. (u, v) is its centre on the wall line; along_u says the wall
    runs along u; wall_t is the wall it sits in."""
    name: str
    u: float
    v: float
    along_u: bool
    width: float
    wall_t: float


@dataclass
class Part:
    key: str
    name: str
    kind: str              # "space", "wardrobe" or "furniture"
    poly: Polygon
    height: float = 0.0    # furniture only


@dataclass
class Interior:
    room: str
    storey: str
    entry: Opening | None               # the room's own door, from its hub
    main: Polygon                       # what is left for the room itself
    parts: list[Part] = field(default_factory=list)
    partitions: list[Polygon] = field(default_factory=list)
    doors: list[Opening] = field(default_factory=list)


def config(prog: dict | None = None) -> dict:
    prog = prog or yaml.safe_load(PROGRAM.read_text(encoding="utf-8"))
    return prog["interiors"]


def shared(a: Rect, b: Rect):
    """The wall room a shares with b: (side of a, lo, hi, wall thickness)."""
    for gap in (T_INT, T_EXT):
        for side, ok, lo, hi in (
            ("E", abs(b.u0 - a.u1 - gap) < 2e-3, max(a.v0, b.v0), min(a.v1, b.v1)),
            ("W", abs(a.u0 - b.u1 - gap) < 2e-3, max(a.v0, b.v0), min(a.v1, b.v1)),
            ("N", abs(b.v0 - a.v1 - gap) < 2e-3, max(a.u0, b.u0), min(a.u1, b.u1)),
            ("S", abs(a.v0 - b.v1 - gap) < 2e-3, max(a.u0, b.u0), min(a.u1, b.u1)),
        ):
            if ok and hi - lo > 0:
                return side, lo, hi, gap
    return None


def _along_u(side: str) -> bool:
    return side in ("S", "N")


def _extent(r: Rect, side: str) -> tuple[float, float]:
    return (r.u0, r.u1) if _along_u(side) else (r.v0, r.v1)


def _lbox(r: Rect, side: str, s0: float, s1: float, t0: float, t1: float) -> Polygon:
    """A box in the room's local frame: s along the door wall, t into the room."""
    s0, s1 = min(s0, s1), max(s0, s1)
    if side == "S":
        return box(s0, r.v0 + t0, s1, r.v0 + t1)
    if side == "N":
        return box(s0, r.v1 - t1, s1, r.v1 - t0)
    if side == "W":
        return box(r.u0 + t0, s0, r.u0 + t1, s1)
    return box(r.u1 - t1, s0, r.u1 - t0, s1)


def _lpoint(r: Rect, side: str, s: float, t: float) -> tuple[float, float]:
    return {"S": (s, r.v0 + t), "N": (s, r.v1 - t),
            "W": (r.u0 + t, s), "E": (r.u1 - t, s)}[side]


def _external_sides(r: Rect, footprint: Polygon) -> set[str]:
    """Sides of the room on the outside wall: just past the wall is outside."""
    d = T_EXT + 0.05
    probes = {"W": (r.u0 - d, (r.v0 + r.v1) / 2), "E": (r.u1 + d, (r.v0 + r.v1) / 2),
              "S": ((r.u0 + r.u1) / 2, r.v0 - d), "N": ((r.u0 + r.u1) / 2, r.v1 + d)}
    from shapely.geometry import Point
    return {k for k, (u, v) in probes.items() if not footprint.contains(Point(u, v))}


def door_wall(r: Rect, hubs: list[Rect]):
    """The first hub the room shares at least a door's width of wall with."""
    for h in hubs:
        s = shared(r, h)
        if s and s[2] - s[1] >= 1.0:
            return h, s
    return None, None


def ensuite(r: Rect, storey: str, side: str, lo: float, hi: float, wall_t: float,
            external: set[str], cfg: dict, names: dict) -> Interior:
    c, p = cfg["ensuite"], cfg["partition_m"]
    wb, db = c["bathroom"]["width_m"], c["bathroom"]["depth_m"]
    entry = c["entry_m"]
    wd = c["wardrobe"]
    w0, w1 = _extent(r, side)
    end_side = ("W", "E") if _along_u(side) else ("S", "N")

    options = []
    for at_start in (True, False):
        if at_start:
            bath = (w0, w0 + wb)
            e0 = bath[1] + p
            ent = (e0, e0 + entry)
            wr = (ent[1], min(ent[1] + wd["max_length_m"], w1))
        else:
            bath = (w1 - wb, w1)
            e1 = bath[0] - p
            ent = (e1 - entry, e1)
            wr = (max(ent[0] - wd["max_length_m"], w0), ent[0])
        door_ok = ent[0] >= lo - 1e-6 and ent[1] <= hi + 1e-6
        wr_ok = wr[1] - wr[0] >= wd["min_length_m"] - 1e-6
        on_facade = end_side[0 if at_start else 1] in external
        if door_ok and wr_ok:
            options.append((on_facade, not at_start, bath, ent, wr, at_start))
    if not options:
        raise ValueError(f"{r.key}: no room for the en-suite beside its door")
    _, _, bath, ent, wr, at_start = min(options)

    room_name = names.get(r.key, r.key).split(",")[0]
    bath_poly = _lbox(r, side, *bath, 0.0, db)
    if at_start:
        block = _lbox(r, side, bath[0], bath[1] + p, 0.0, db + p)
        bdoor_s = bath[1] + p / 2
    else:
        block = _lbox(r, side, bath[0] - p, bath[1], 0.0, db + p)
        bdoor_s = bath[0] - p / 2
    partitions = [g for g in [block.difference(bath_poly)] if g.area > 1e-6]
    eu, ev = _lpoint(r, side, (ent[0] + ent[1]) / 2, -wall_t / 2)
    bu, bv = _lpoint(r, side, bdoor_s, db / 2)
    main = r.poly.difference(block)
    if main.area < c["bedroom_min_m2"] - 1e-6:
        raise ValueError(f"{r.key}: only {main.area:.1f} m2 left for the bedroom")
    return Interior(
        room=r.key, storey=storey,
        entry=Opening(f"Door, {room_name}", eu, ev, _along_u(side), 0.90, wall_t),
        main=main,
        parts=[Part(f"{r.key}.bathroom", f"{room_name}, en-suite bathroom", "space",
                    bath_poly),
               Part(f"{r.key}.wardrobe", f"{room_name}, built-in wardrobe", "wardrobe",
                    _lbox(r, side, *wr, 0.0, wd["depth_m"]), wd["height_m"])],
        partitions=partitions,
        doors=[Opening(f"Door, {room_name} en-suite", bu, bv, not _along_u(side),
                       0.80, p)],
    )


def staff_ensuite(r: Rect, storey: str, door_s: float, cfg: dict,
                  names: dict) -> Interior:
    """A shower room across the full depth of the room, at the end of its long
    side away from the door. The room's own doors are placed elsewhere."""
    c, p = cfg["staff_ensuite"], cfg["partition_m"]
    wb = c["bathroom"]["width_m"]
    long_u = (r.u1 - r.u0) >= (r.v1 - r.v0)
    a0, a1 = (r.u0, r.u1) if long_u else (r.v0, r.v1)
    at_end = abs(door_s - a0) < abs(door_s - a1)      # door near the start
    if at_end:
        bath_a, block_a, wall_a = (a1 - wb, a1), (a1 - wb - p, a1), a1 - wb - p / 2
    else:
        bath_a, block_a, wall_a = (a0, a0 + wb), (a0, a0 + wb + p), a0 + wb + p / 2

    def span(lo, hi):
        return box(lo, r.v0, hi, r.v1) if long_u else box(r.u0, lo, r.u1, hi)

    bath, block = span(*bath_a), span(*block_a)
    main = r.poly.difference(block)
    if main.area < c["bedroom_min_m2"] - 1e-6:
        raise ValueError(f"{r.key}: only {main.area:.1f} m2 left for the bedroom")
    room_name = names.get(r.key, r.key).split(" with ")[0]
    mid = ((r.v0 + r.v1) / 2) if long_u else ((r.u0 + r.u1) / 2)
    du, dv = (wall_a, mid) if long_u else (mid, wall_a)
    return Interior(
        room=r.key, storey=storey, entry=None, main=main,
        parts=[Part(f"{r.key}.bathroom", f"{room_name}, shower room", "space", bath)],
        partitions=[block.difference(bath)],
        doors=[Opening(f"Door, {room_name} shower room", du, dv, not long_u, 0.70, p)],
    )


def master(r: Rect, storey: str, side: str, lo: float, hi: float, wall_t: float,
           cfg: dict) -> Interior:
    c, p = cfg["master_suite"], cfg["partition_m"]
    if side != "N":
        raise ValueError("the master suite plan expects its door on the north wall")
    ws, gd = c["service_zone_width_m"], c["gallery_depth_m"]
    u0, u1, v0, v1 = r.u0, r.u1, r.v0, r.v1
    us = u0 + ws                                   # east edge of the service zone
    w_w = (ws - p) / 2
    hers, his = c["walk_in_wardrobes"]
    d_w = max(hers["target_m2"], his["target_m2"]) / w_w
    g0 = v1 - gd                                   # south edge of the gallery
    wir_v = (g0 - p - d_w, g0 - p)
    bath = box(u0, v0, us, wir_v[0] - p)
    if bath.area < c["bathroom"]["min_m2"] - 1e-6:
        raise ValueError(f"master bathroom only {bath.area:.1f} m2")
    w_hers = box(u0, wir_v[0], u0 + w_w, wir_v[1])
    w_his = box(u0 + w_w + p, wir_v[0], us, wir_v[1])
    service = box(u0, v0, us + p, g0)
    partitions = [service.difference(unary_union([bath, w_hers, w_his]))]
    cs = c["coffee_station"]
    coffee = box(u1 - 0.20 - cs["length_m"], v1 - cs["depth_m"], u1 - 0.20, v1)
    door_u = (lo + hi) / 2
    return Interior(
        room=r.key, storey=storey,
        entry=Opening("Door, Master Suite", door_u, v1 + wall_t / 2, True, 1.00, wall_t),
        main=r.poly.difference(service),
        parts=[Part("master_suite.bathroom", "Master bathroom", "space", bath),
               Part(f"master_suite.{hers['key']}", hers["name"], "space", w_hers),
               Part(f"master_suite.{his['key']}", his["name"], "space", w_his),
               Part("master_suite.coffee_station", "Coffee station", "furniture",
                    coffee, cs["height_m"])],
        partitions=partitions,
        doors=[Opening("Door, walk-in wardrobe, hers", (u0 + u0 + w_w) / 2, g0 - p / 2,
                       True, 0.80, p),
               Opening("Door, walk-in wardrobe, his", (u0 + w_w + p + us) / 2, g0 - p / 2,
                       True, 0.80, p),
               Opening("Door, master bathroom", us + p / 2,
                       (v0 + wir_v[0] - p) / 2, False, 0.90, p)],
    )


def plan(lay: dict | None = None, prog: dict | None = None) -> dict[str, Interior]:
    lay = lay or yaml.safe_load(LAYOUTS.read_text(encoding="utf-8"))
    prog = prog or yaml.safe_load(PROGRAM.read_text(encoding="utf-8"))
    cfg = config(prog)
    names = {r["key"]: r["name"] for f in ("ground", "first") for r in prog[f]}
    footprints = {
        "ground": Polygon(lay["outlines"].get("ground", lay["outlines"]["road_ground"])),
        "first": Polygon(lay["outlines"]["first"]),
    }
    out = {}
    for storey in ("ground", "first"):
        floor = lay["floors"][storey]
        rects = {d["key"]: Rect.of(d) for d in floor["rooms"] + floor["circulation"]}
        hubs = [rects[k] for k in HUBS if k in rects]
        for key, r in rects.items():
            if key in cfg["staff_ensuite"]["rooms"]:
                s = shared(r, rects[cfg["staff_ensuite"]["door_from"]])
                if s is None:
                    raise ValueError(f"{key} shares no wall with its door room")
                out[key] = staff_ensuite(r, storey, (s[1] + s[2]) / 2, cfg, names)
                continue
            if key in cfg["ensuite"]["rooms"] or key == "master_suite":
                hub, s = door_wall(r, hubs)
                if hub is None:
                    raise ValueError(f"{key} shares no door-width wall with a hub")
                side, lo, hi, t = s
                if key == "master_suite":
                    out[key] = master(r, storey, side, lo, hi, t, cfg)
                else:
                    out[key] = ensuite(r, storey, side, lo, hi, t,
                                       _external_sides(r, footprints[storey]), cfg, names)
    return out


def main() -> int:
    for key, it in plan().items():
        door = f"({it.entry.u:.2f}, {it.entry.v:.2f})" if it.entry else "via its link"
        print(f"{key:<14} {it.storey:<6} main {it.main.area:6.2f} m2   door {door}")
        for part in it.parts:
            print(f"    {part.name:<34} {part.kind:<9} {part.poly.area:6.2f} m2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
