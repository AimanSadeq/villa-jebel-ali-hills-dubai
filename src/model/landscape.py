"""The garden, from brief/garden.yaml (answers G1 to G4, D-055).

build(spec, plot, house, carport, obstacles) turns the garden data into:
  * items for the IFC (paving, terraces, steps, lawn, planting beds, hedges,
    trees and palms, the boundary wall with its screen and gates, the BBQ
    pergola, counter and table), each as prisms in the plot building grid;
  * walk zones for the walkthrough: the terraces, lawns, paths and the
    entrance steps at their own levels, with the beds, hedges, trees, the
    wall and the BBQ furniture as obstacles;
  * the surfaces for the sketch VJH-SK-019.

Every surface is clipped to the plot inside the wall and has the house, the
carport and the surfaces listed after it taken out, so nothing overlaps.
Plants are indicative species for the landscape architect to confirm.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parents[2]
GARDEN = REPO_ROOT / "brief" / "garden.yaml"

STYLE = {"paving": "deck", "step": "deck", "steps": "deck", "path": "paving", "lawn": "lawn",
         "bed": "soil", "ground": "terrain"}
IFC = {"paving": "IfcSlab", "step": "IfcSlab", "steps": "IfcSlab", "path": "IfcSlab",
       "lawn": "IfcGeographicElement", "bed": "IfcGeographicElement",
       "ground": "IfcGeographicElement"}
THICK = {"lawn": 0.02, "bed": 0.03, "ground": 0.0}


@dataclass
class Item:
    cls: str
    name: str
    object_type: str
    style: str
    prisms: list            # (polygon, z0, height)
    predefined: str = "USERDEFINED"
    material: str | None = None


@dataclass
class Landscape:
    items: list[Item] = field(default_factory=list)
    flat: list = field(default_factory=list)       # (name, polygon, z)
    ramps: list = field(default_factory=list)      # dicts as architecture.walk_stair
    surfaces: list = field(default_factory=list)   # (spec, polygon) for the sketch
    trees: list = field(default_factory=list)      # (spec, species dict)
    report: list[str] = field(default_factory=list)


def load(path: Path = GARDEN) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _parts(g):
    if g.is_empty:
        return []
    return [g] if g.geom_type == "Polygon" else [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]


def _side_of(p, q, plot) -> str:
    b = plot.bounds
    mu, mv = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    d = {"road": mu - b[0], "landscape": b[2] - mu, "south": mv - b[1], "north": b[3] - mv}
    return min(d, key=d.get)


def _octagon(u, v, r):
    return Point(u, v).buffer(r, 2)


def build(spec: dict, plot: Polygon, house: Polygon, carport: Polygon | None,
          obstacles: list[Polygon]) -> Landscape:
    L = Landscape()
    g0 = float(spec["meta"]["ground_z"])
    w = spec["wall"]
    t = float(w["thickness_m"])
    inner = plot.buffer(-t, join_style=2)
    taken = unary_union([house] + ([carport] if carport is not None else []))

    # Boundary wall (D-011, G3), by plot side, with the gates cut out.
    gates = w.get("gates", []) or []
    coords = list(plot.exterior.coords)
    screen_z = (float(w["solid_m"]), float(w["overall_m"]))
    for p, q in zip(coords[:-1], coords[1:]):
        side = _side_of(p, q, plot)
        strip = LineString([p, q]).buffer(t + 0.001, cap_style=2).intersection(plot)
        strip = strip.difference(inner.buffer(-0.001))
        for gt in gates:
            if gt["side"] == side:
                lo, hi = gt["v"] if side in ("road", "landscape") else gt["u"]
                cut = (box(plot.bounds[0] - 1, lo, plot.bounds[2] + 1, hi) if side in ("road", "landscape")
                       else box(lo, plot.bounds[1] - 1, hi, plot.bounds[3] + 1))
                strip = strip.difference(cut)
        solid_top = float(w["overall_m"]) if side in w["solid_sides"] else screen_z[0]
        for poly in _parts(strip):
            L.items.append(Item("IfcWall", f"Boundary wall, {side} side", "Landscape: boundary wall",
                                "ext", [(poly, g0 - 0.3, solid_top + 0.3)], material="ext"))
            if side in w["screen_sides"]:
                # The lighter screen above the solid part: a thin timber slat band.
                thin = poly.buffer(-(t - 0.06) / 2, join_style=2)
                for q2 in _parts(thin):
                    L.items.append(Item("IfcWall", f"Boundary screen, {side} side",
                                        "Landscape: wall screen", "timber",
                                        [(q2, g0 + screen_z[0], screen_z[1] - screen_z[0])]))
    wall_poly = plot.difference(inner)
    for gt in gates:
        lo, hi = gt["v"]
        b = plot.bounds
        leaf = box(b[0] + 0.05, lo, b[0] + 0.11, hi) if gt["side"] == "road" else box(b[2] - 0.11, lo, b[2] - 0.05, hi)
        L.items.append(Item("IfcDoor", gt["name"], "Landscape: gate", "metal",
                            [(leaf, g0, float(gt["height_m"]))]))

    # Surfaces, later ones cut from earlier ones.
    specs = spec["surfaces"]
    polys = []
    for i, s in enumerate(specs):
        poly = box(s["u"][0], s["v"][0], s["u"][1], s["v"][1]).intersection(inner).difference(taken)
        for later in specs[i + 1:]:
            poly = poly.difference(box(later["u"][0], later["v"][0], later["u"][1], later["v"][1]))
        polys.append(poly)
    covered = unary_union([p for p in polys if not p.is_empty] + [taken, wall_poly])
    leftover = inner.difference(covered)
    specs = specs + [{"key": "ground", "name": "Garden ground", "kind": "ground", "z": g0}]
    polys.append(leftover)

    block = unary_union([o for o in obstacles] or [Polygon()])
    for s, poly in zip(specs, polys):
        kind = s["kind"]
        parts = [p for p in _parts(poly) if p.area > 0.02]
        if not parts:
            if kind != "ground":
                L.report.append(f"{s['name']}: nothing left after the cuts, left out")
            continue
        L.surfaces.append((s, unary_union(parts)))
        z = float(s["z"])
        if kind == "steps":
            n = int(s.get("risers", 3))
            zl = float(s["z_low"])
            u0, u1 = s["u"]
            tread = (u1 - u0) / n
            for k in range(n):
                tr = box(u0 + k * tread, s["v"][0], u1, s["v"][1]).intersection(inner)
                L.items.append(Item("IfcSlab", f"{s['name']}, tread {k + 1}", "Landscape: steps", "deck",
                                    [(tr, zl - 0.05, (zl + (k + 1) * (z - zl) / n) - (zl - 0.05))]))
            ring = box(u0, s["v"][0], u1, s["v"][1])
            L.ramps.append({"name": s["name"], "kind": "ramp", "poly": ring.difference(block),
                            "p0": (u0, (s["v"][0] + s["v"][1]) / 2), "z0": zl,
                            "p1": (u1, (s["v"][0] + s["v"][1]) / 2), "z1": z})
            continue
        if kind in ("paving", "step", "path"):
            prisms = [(p, g0 - 0.05, z - (g0 - 0.05)) for p in parts]
        elif kind == "ground":
            prisms = []
        else:
            prisms = [(p, g0, THICK[kind]) for p in parts]
        if prisms:
            L.items.append(Item(IFC[kind], s["name"], f"Landscape: {kind}", STYLE[kind], prisms))
        if kind != "bed":
            zone = unary_union(parts).difference(block)
            L.flat.append((f"garden, {s['name'].lower()}", zone, z))

    # Hedges.
    for h in spec.get("hedges", []) or []:
        poly = box(h["u"][0], h["v"][0], h["u"][1], h["v"][1]).intersection(inner).difference(taken)
        for p in _parts(poly):
            L.items.append(Item("IfcGeographicElement", h["name"], "Landscape: hedge", "leaf",
                                [(p, g0, float(h["height_m"]))]))
            block = block.union(p.buffer(0.15))

    # Trees and palms.
    for tr in spec.get("trees", []) or []:
        sp = spec["species"][tr["species"]]
        u, v = float(tr["u"]), float(tr["v"])
        if not inner.contains(Point(u, v)):
            L.report.append(f"{sp['name']} at ({u:.1f}, {v:.1f}) is outside the plot, left out")
            continue
        hgt, trunk, crown = float(sp["height_m"]), float(sp["trunk_m"]), float(sp["crown_m"])
        if Point(u, v).buffer(crown / 2).intersects(house.buffer(0.3)):
            L.report.append(f"{sp['name']} at ({u:.1f}, {v:.1f}): crown reaches the house, moved out")
            continue
        name = f"{'Palm' if sp['kind'] == 'palm' else 'Tree'}, {sp['name']}"
        if sp["kind"] == "palm":
            prisms = [(_octagon(u, v, 0.22), g0, trunk)]
            crown_prisms = [(_octagon(u, v, crown / 2), g0 + trunk - 0.2, 0.9),
                            (_octagon(u, v, crown * 0.3), g0 + trunk + 0.7, hgt - trunk - 0.7)]
        else:
            prisms = [(_octagon(u, v, 0.18), g0, trunk)]
            h1 = (hgt - trunk) * 0.6
            crown_prisms = [(_octagon(u, v, crown / 2), g0 + trunk, h1),
                            (_octagon(u, v, crown * 0.3), g0 + trunk + h1, hgt - trunk - h1)]
        L.items.append(Item("IfcGeographicElement", f"{name}, trunk", f"Landscape: {sp['kind']}",
                            "trunk", prisms))
        L.items.append(Item("IfcGeographicElement", f"{name}, crown", f"Landscape: {sp['kind']}",
                            "palm" if sp["kind"] == "palm" else "leaf", crown_prisms))
        L.trees.append((tr, sp))
        block = block.union(Point(u, v).buffer(0.45))

    # BBQ area (G1).
    bq = spec["bbq"]
    pg = bq["pergola"]
    (u0, u1), (v0, v1) = pg["u"], pg["v"]
    zb, zt, s, bd = float(pg["z_base"]), float(pg["z_top"]), float(pg["post_m"]), float(pg["beam_depth_m"])
    posts = [box(pu, pv, pu + s, pv + s) for pu in (u0, u1 - s) for pv in (v0, v1 - s)]
    prisms = [(p, zb, zt - bd - zb) for p in posts]
    prisms += [(box(u0, v0, u1, v0 + s), zt - bd, bd), (box(u0, v1 - s, u1, v1), zt - bd, bd),
               (box(u0, v0, u0 + s, v1), zt - bd, bd), (box(u1 - s, v0, u1, v1), zt - bd, bd)]
    sp_, ld, lt = float(pg["louvre_spacing_m"]), float(pg["louvre_depth_m"]), float(pg["louvre_thickness_m"])
    c = v0 + sp_ / 2
    while c < v1:
        prisms.append((box(u0, c - lt / 2, u1, c + lt / 2), zt - ld, ld))
        c += sp_
    L.items.append(Item("IfcBuildingElementProxy", "BBQ pergola, timber louvres", "Landscape: pergola",
                        "timber", prisms))
    block = block.union(unary_union(posts).buffer(0.05))
    ct = bq["counter"]
    cbox = box(ct["u"][0], ct["v"][0], ct["u"][1], ct["v"][1])
    gr = ct["grill"]
    L.items.append(Item("IfcFurniture", "BBQ counter", "Landscape: furniture", "joinery",
                        [(cbox, zb, float(ct["height_m"]) - 0.04),
                         (cbox, zb + float(ct["height_m"]) - 0.04, 0.04)]))
    L.items.append(Item("IfcFurniture", "BBQ grill", "Landscape: furniture", "metal",
                        [(box(gr["u"][0], gr["v"][0], gr["u"][1], gr["v"][1]), zb + float(ct["height_m"]), 0.25)]))
    block = block.union(cbox)
    tb = bq["table"]
    tbox = box(tb["u"][0], tb["v"][0], tb["u"][1], tb["v"][1])
    th = float(tb["height_m"])
    L.items.append(Item("IfcFurniture", f"BBQ table, {tb['seats']} seats", "Landscape: furniture", "timber",
                        [(tbox, zb + th - 0.04, 0.04), (tbox.buffer(-0.6, join_style=2), zb, th - 0.04)]))
    block = block.union(tbox)
    n_side = max(1, int(tb["seats"]) // 2)
    for i in range(n_side):
        cu = tb["u"][0] + (i + 0.5) * (tb["u"][1] - tb["u"][0]) / n_side
        for south in (True, False):
            v_seat = tb["v"][0] - 0.55 if south else tb["v"][1] + 0.10
            seat = box(cu - 0.22, v_seat, cu + 0.22, v_seat + 0.45)
            back = (box(cu - 0.22, v_seat, cu + 0.22, v_seat + 0.05) if south
                    else box(cu - 0.22, v_seat + 0.40, cu + 0.22, v_seat + 0.45))
            L.items.append(Item("IfcFurniture", "BBQ chair", "Landscape: furniture", "timber",
                                [(seat, zb, 0.45), (back, zb + 0.45, 0.45)]))
            block = block.union(seat)

    # Obstacles cut from every zone (hedges, trees and the BBQ came after the zones).
    L.flat = [(n, z.difference(block), zz) for n, z, zz in L.flat]
    L.ramps = [{**r, "poly": r["poly"].difference(block)} for r in L.ramps]
    return L
