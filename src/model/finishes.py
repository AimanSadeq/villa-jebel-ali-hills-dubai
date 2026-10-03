"""Interior finish surfaces for the walkthrough's palettes (answers P1 to P4).

finish_data(model) returns, for every room and hall of the built model, the
floor, the wall faces and the ceiling as quads, each tagged with the palette
slot it takes (brief/palettes.yaml): flooring by zone, walls (main, wet or
feature) and ceilings. The viewer colours them from the palette chosen and
switches them with one button. Wall faces follow the walls actually built
and leave the doors, windows and open joins clear.

Quads are (u, v, z) points in the plot building grid, wound so their face
points into the room.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from shapely.geometry import box
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

PALETTES = REPO_ROOT / "brief" / "palettes.yaml"
INSET = 0.004             # finishes sit just inside the room
SKIP = ("garage", "main_entrance", "stair", "lift", "landing")


def load() -> dict:
    return yaml.safe_load(PALETTES.read_text(encoding="utf-8"))


def zone_of(key: str) -> str:
    """The palette zone of a room key (brief/palettes.yaml, header)."""
    k = key.lower()
    if any(w in k for w in ("toilet", "powder", "bath", "wash")):
        return "wet"
    if any(w in k for w in ("kitchen", "pantry")):
        return "kitchen"
    if any(w in k for w in ("bedroom", "master", "dress", "office", "maids_room")):
        return "service" if "maids" in k else "bedrooms"
    if any(w in k for w in ("laundry", "plant", "service", "maid", "outdoor")):
        return "service"
    return "public"


def _intervals(edge_len: float, segs: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out = []
    for a, b in sorted(segs):
        a, b = max(0.0, a), min(edge_len, b)
        if b - a < 0.02:
            continue
        if out and a <= out[-1][1] + 0.01:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _rects(a0: float, a1: float, h: float, holes: list[tuple[float, float, float, float]]):
    """[a0, a1] x [0, h] less the hole rectangles (a, b, z0, z1), as rectangles."""
    xs = sorted({a0, a1, *[min(max(x, a0), a1) for hb in holes for x in hb[:2]]})
    out = []
    for x0, x1 in zip(xs[:-1], xs[1:]):
        if x1 - x0 < 1e-3:
            continue
        mid = (x0 + x1) / 2
        cuts = sorted((max(z0, 0.0), min(z1, h)) for a, b, z0, z1 in holes if a < mid < b and z1 > 0 and z0 < h)
        z = 0.0
        for c0, c1 in cuts:
            if c0 > z + 1e-3:
                out.append((x0, x1, z, c0))
            z = max(z, c1)
        if h > z + 1e-3:
            out.append((x0, x1, z, h))
    return out


def finish_data(m) -> dict:
    """Quads per palette slot for the model m (architecture.Model, built)."""
    spec = load()
    feature = {(f["room"], f["side"]) for f in spec.get("feature_walls", []) or []}
    clear_g = m.HG - m.SLAB - m.SERV
    clear_f = m.HF - m.SLAB - m.SERV
    tall = m.HG + m.HF - m.SLAB - m.SERV
    voids = unary_union([v.poly for v in m.voids]) if m.voids else None
    skip_keys = set(m.open_sky_keys) | set(m.porch_keys)
    quads: list[dict] = []

    def add(slot, storey, pts, room):
        quads.append({"slot": slot, "storey": storey, "room": room,
                      "p": [[round(c, 3) for c in pt] for pt in pts]})

    for storey, rooms in (("ground", m.g_rooms + m.g_circ), ("first", m.f_rooms + m.f_circ)):
        e = m.elev[storey]
        walls = unary_union([poly for _, poly, _ in m.walls[storey]])
        holes_all = [(c, z0, z1) for st, c, z0, z1 in m.opening_boxes if st == storey]
        for r in rooms:
            if r.key in skip_keys or any(s in r.key for s in SKIP):
                continue
            zone = zone_of(r.key)
            poly = r.poly
            under = poly.intersection(voids).area if (voids is not None and storey == "ground") else 0.0
            is_tall = under > 0.5 * poly.area
            h = tall if is_tall else (clear_g if storey == "ground" else clear_f)
            # Floor.
            u0, u1, v0, v1 = r.u0, r.u1, r.v0, r.v1
            z = e + 0.003
            add(f"flooring.{zone}", storey, [(u0, v0, z), (u1, v0, z), (u1, v1, z), (u0, v1, z)], r.key)
            # Ceiling, at the tall height under a void and the room's own elsewhere.
            parts = [(poly, h)]
            if storey == "ground" and voids is not None and 0 < under < poly.area and not is_tall:
                parts = [(poly.difference(voids), h), (poly.intersection(voids), tall)]
            for g, hh in parts:
                for q in ([g] if g.geom_type == "Polygon" else list(getattr(g, "geoms", []))):
                    if q.area < 0.05:
                        continue
                    a, b, c, d = q.bounds
                    zc = e + hh
                    add("walls.ceiling", storey, [(a, b, zc), (a, d, zc), (c, d, zc), (c, b, zc)], r.key)
            # Walls: each side, where a wall stands, less the openings in it.
            sides = {"S": ((u0, v0), (u1, v0), (0, 1)), "N": ((u1, v1), (u0, v1), (0, -1)),
                     "W": ((u0, v1), (u0, v0), (1, 0)), "E": ((u1, v0), (u1, v1), (-1, 0))}
            for side, (p0, p1, n) in sides.items():
                du, dv = p1[0] - p0[0], p1[1] - p0[1]
                L = abs(du) + abs(dv)
                tu, tv = du / L, dv / L
                # A 6 cm strip just outside this side: where it meets a wall.
                strip = box(min(p0[0], p1[0]) - 0.0 - (0.06 if n[0] > 0 else 0),
                            min(p0[1], p1[1]) - (0.06 if n[1] > 0 else 0),
                            max(p0[0], p1[0]) + (0.06 if n[0] < 0 else 0),
                            max(p0[1], p1[1]) + (0.06 if n[1] < 0 else 0))
                hit = strip.intersection(walls)
                segs = []
                for g in ([hit] if hit.geom_type == "Polygon" else list(getattr(hit, "geoms", []))):
                    if g.is_empty or g.area < 0.06 * 0.02:
                        continue
                    bx = g.bounds
                    if abs(tu) > 0:
                        a, b = (bx[0] - p0[0]) * tu, (bx[2] - p0[0]) * tu
                    else:
                        a, b = (bx[1] - p0[1]) * tv, (bx[3] - p0[1]) * tv
                    segs.append((min(a, b), max(a, b)))
                spans = _intervals(L, segs)
                if not spans:
                    continue
                holes = []
                for c, z0, z1 in holes_all:
                    if not c.intersects(strip.buffer(0.01)):
                        continue
                    bx = c.bounds
                    if abs(tu) > 0:
                        a, b = (bx[0] - p0[0]) * tu, (bx[2] - p0[0]) * tu
                    else:
                        a, b = (bx[1] - p0[1]) * tv, (bx[3] - p0[1]) * tv
                    holes.append((min(a, b), max(a, b), z0, z1))
                slot = ("walls.feature" if (r.key, side) in feature
                        else "walls.wet" if zone == "wet" else "walls.main")
                ou, ov = n[0] * INSET, n[1] * INSET
                for a0, a1 in spans:
                    for x0, x1, z0, z1 in _rects(a0, a1, h, holes):
                        q0 = (p0[0] + tu * x0 + ou, p0[1] + tv * x0 + ov)
                        q1 = (p0[0] + tu * x1 + ou, p0[1] + tv * x1 + ov)
                        # Wound so the face points into the room.
                        add(slot, storey, [(q0[0], q0[1], e + z0), (q0[0], q0[1], e + z1),
                                           (q1[0], q1[1], e + z1), (q1[0], q1[1], e + z0)], r.key)
    # Floors in the open joins between rooms and in the door openings, so the
    # floor runs on without a gap. They take the floor of the room they open from.
    rooms_by = {r.key: r for r in m.g_rooms + m.g_circ + m.f_rooms + m.f_circ}
    for storey in ("ground", "first"):
        e = m.elev[storey] + 0.002
        walls = unary_union([poly for _, poly, _ in m.walls[storey]])
        pieces = [(k, g) for k, g in m.bridges[storey]]
        pieces += [(None, c.intersection(walls)) for st, c, z0, z1 in m.opening_boxes
                   if st == storey and z0 < 0.05]
        for k, g in pieces:
            for q in ([g] if g.geom_type == "Polygon" else list(getattr(g, "geoms", []))):
                if q.is_empty or q.area < 0.01:
                    continue
                a, b_, c, d = q.bounds
                owner = k
                if owner is None:
                    near = [r for r in rooms_by.values() if r.poly.distance(q) < 0.06
                            and (storey == "ground") == (r in m.g_rooms + m.g_circ)]
                    near = [r for r in near if not any(x in r.key for x in SKIP)]
                    owner = min(near, key=lambda r: ("toilet" in r.key or "bath" in r.key, r.area)).key \
                        if near else None
                if owner is None or owner in skip_keys or any(x in owner for x in SKIP):
                    continue
                add(f"flooring.{zone_of(owner)}", storey,
                    [(a, b_, e), (c, b_, e), (c, d, e), (a, d, e)], owner)

    palettes = [{k: p[k] for k in ("key", "name", "flooring", "walls", "accents", "fixtures")}
                for p in spec["palettes"]]
    return {"quads": quads, "palettes": palettes,
            "note": "Interior palettes, brief/palettes.yaml (P1 to P4). Visual concept finishes, "
                    "not a specification. CONCEPT DESIGN, NOT FOR CONSTRUCTION."}
