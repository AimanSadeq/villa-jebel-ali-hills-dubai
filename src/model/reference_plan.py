"""The owner's reference villa, transcribed and placed on plot 5130272.

On 2026-10-02 the owner set the generated plans aside and supplied a
consultant's set for plot 5131627 (reference/owner/) as the design he likes,
to face the road. This module turns the transcription of that set,
brief/reference_plan.yaml, into the same layout dictionary that
src/model/layout_gen.py produces for its own plans, so everything downstream
(the GFA check, the IFC generator, the drawings, the viewer) works unchanged.

The transcription is in the sheet's own frame: x along the road from the
carport side outer wall, y from the road side edge toward the rear garden. It
is placed on our plot with the main front wall (grid 2) on the road setback
line and, by the owner's answer 7, mirrored: the carport at the south end.
The owner's answers to the ground floor questions (docs/ground-floor-
decisions.md) are applied as room substitutions in the YAML, never here.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model.massing import site_to_grid  # noqa: E402
from model.site import buildable_envelope, plot_polygon  # noqa: E402

PLAN_YAML = REPO_ROOT / "brief" / "reference_plan.yaml"

T_EXT = 0.25
T_INT = 0.15


def load_plan(path: Path | None = None) -> dict:
    return yaml.safe_load((path or PLAN_YAML).read_text(encoding="utf-8"))


class Placement:
    """Maps the sheet frame (x along the road, y into the plot) to our grid.

    y = 0 on the sheet is the road side edge, which the reference puts on its
    plot boundary at the carport; it goes on our road boundary (u = 0), so the
    carport reaches toward the road as in the reference and the main front wall
    sits behind our 3 m setback line. Along the road, x = 0 (the carport end)
    goes on the south setback line, measured at the deepest point of the
    building because the side setback lines are not square to the road.
    """

    def __init__(self, plan: dict):
        from shapely.geometry import LineString  # noqa: PLC0415

        p = plan["placement"]
        self.env = site_to_grid(buildable_envelope())
        plot = site_to_grid(plot_polygon())
        self.u_road = plot.bounds[0]                         # road boundary, u = 0
        self.road_edge_y = float(p.get("road_edge_y_m", 0.0))
        self.mirror = bool(p.get("mirror", True))
        ys = [d[k] for f in ("ground", "first") for d in plan[f] for k in ("y0", "y1")]
        self.depth_u = (self.u(min(ys)), self.u(max(ys)))
        front_u = self.u(float(p["front_wall_y_m"]))
        if front_u < self.env.bounds[0] - 1e-6:
            raise ValueError(f"main front wall {self.env.bounds[0] - front_u:.2f} m in the setback")

        def vlim(u):
            seg = LineString([(u, -50.0), (u, 100.0)]).intersection(self.env)
            return seg.bounds[1], seg.bounds[3]
        body_u = (front_u, self.u(float(plan["frame"]["rear_wall_y_m"])))
        lims = [vlim(u) for u in body_u + (min(self.depth_u[1], self.env.bounds[2] - 0.01),)]
        self.v_south = max(lo for lo, _ in lims)              # x = 0 sits here
        self.v_north = min(hi for _, hi in lims)
        length = float(plan["frame"]["length_along_road_m"])
        self.spare = self.v_north - self.v_south - length
        if self.spare < -1e-6:
            raise ValueError(f"reference plan is {-self.spare:.2f} m too long for the plot")
        self.v0 = self.v_south
        self.v1 = self.v0 + length

    def u(self, y: float) -> float:
        return self.u_road + (y - self.road_edge_y)

    def rect(self, x0, x1, y0, y1) -> Polygon:
        u0, u1 = self.u(y0), self.u(y1)
        if self.mirror:
            v0, v1 = self.v0 + x0, self.v0 + x1              # carport (x = 0) at the south end
        else:
            v0, v1 = self.v1 - x1, self.v1 - x0
        return box(u0, min(v0, v1), u1, max(v0, v1))


def _outline(polys: list[Polygon]) -> Polygon:
    """External outline: rooms grown to close the partitions, then by the
    external wall. Mitred buffers keep the outline orthogonal."""
    # Close the partitions (the reference's are up to 0.30 m), then grow by
    # what is left of the external wall.
    close = 0.15
    core = unary_union([g.buffer(close, join_style=2) for g in polys])
    out = core.buffer(T_EXT - close, join_style=2)
    if out.geom_type != "Polygon":
        out = max(out.geoms, key=lambda g: g.area)
    return Polygon(out.exterior).simplify(0.01)


def resolve_doors(plan: dict, pl: "Placement") -> list[dict]:
    """Every door of the plan on its wall, in our grid, after checking that
    every room can be reached: from the foyer on the ground floor (rooms with
    their own outside door excepted) and from the stair on the first."""
    from model.doors import resolve, unreached  # noqa: PLC0415

    entries = plan.get("doors") or []
    if not entries:
        return []
    out = []
    for floor, start in (("ground", "entrance_foyer"), ("first", "stair_lift_first")):
        rooms = plan[floor]
        doors = resolve(rooms, [d for d in entries if d["storey"] == floor])
        joins = {frozenset(j.split("/")) for j in plan.get("open_joins", {}).get(floor, [])}
        outside = {d["a"] for d in doors if d["b"] == "outside"}
        lost = [k for k in unreached([r for r in rooms if r["kind"] in ("room", "circulation")],
                                     doors, joins, start) if k not in outside]
        if lost:
            raise ValueError(f"{floor} floor: no way into {', '.join(lost)}")
        for d in doors:
            mid = (d["lo"] + d["hi"]) / 2
            if d["axis"] == "x":     # wall across the frame x (our v); the door spans u
                v = pl.v0 + mid if pl.mirror else pl.v1 - mid
                u, along_u = pl.u(d["c"]), True
                swing = d["s"] if pl.mirror else -d["s"]
            else:                    # wall across the frame y (our u); the door spans v
                u = pl.u(mid)
                v = pl.v0 + d["c"] if pl.mirror else pl.v1 - d["c"]
                along_u, swing = False, d["s"]
            out.append({"no": d["no"], "storey": floor, "a": d["a"], "b": d["b"],
                        "kind": d["kind"], "width_m": round(d["w"], 3), "height_m": d["h"],
                        "u": round(u, 3), "v": round(v, 3), "along_u": along_u,
                        "wall_t": round(d["hi"] - d["lo"], 3), "swing": swing,
                        "source": d["src"]})
    return out


def build_layout(plan: dict | None = None) -> dict:
    """The layout dictionary, in the shape layout_gen.build() returns."""
    from model.layout_gen import Rect  # noqa: PLC0415

    plan = plan or load_plan()
    pl = Placement(plan)

    def rects(items):
        out = []
        for d in items:
            g = pl.rect(d["x0"], d["x1"], d["y0"], d["y1"])
            b = g.bounds
            out.append((d, Rect(d["key"], b[0], b[2], b[1], b[3])))
        return out

    g_all = rects(plan["ground"])
    f_all = rects(plan["first"])
    kind = lambda d: d.get("kind", "room")  # noqa: E731

    g_rooms = [r for d, r in g_all if kind(d) in ("room", "service", "open_to_sky", "carport", "porch")]
    g_circ = [r for d, r in g_all if kind(d) == "circulation"]
    f_rooms = [r for d, r in f_all if kind(d) == "room"]
    f_circ = [r for d, r in f_all if kind(d) == "circulation"]
    f_voids = [r for d, r in f_all if kind(d) == "void"]
    f_outdoor = [(d, r) for d, r in f_all if kind(d) in ("balcony", "terrace")]
    # The facade shortens a balcony where the garden frame stands (answer R4,
    # brief/facade.yaml balcony_trims).
    from model.facade import load as load_facade  # noqa: PLC0415
    for t in load_facade().get("balcony_trims", []) or []:
        for d, r in f_outdoor:
            if r.key == t["key"]:
                for k in ("u0", "u1", "v0", "v1"):
                    if k in t:
                        setattr(r, k, float(t[k]))

    # Footprints. The carport is roofed but open and outside GFA (D-039); the
    # lawn court is open to the sky through both floors (D-040).
    body_keys = {r.key for d, r in g_all if kind(d) in ("room", "service", "circulation")}
    court = [r for d, r in g_all if kind(d) == "open_to_sky"]
    carport = [r for d, r in g_all if kind(d) == "carport"]
    body = _outline([r.poly() for d, r in g_all if r.key in body_keys])
    # The transcribed carport runs to the outer face of its walls already.
    carport_plate = unary_union([c.poly() for c in carport]) if carport else None
    first_body = _outline([r.poly() for r in f_rooms + f_circ + f_voids])
    court_u = unary_union([c.poly() for c in court]) if court else None

    # Measured areas. GFA: the body plate less the open court; the carport,
    # balconies and terraces are reported but not counted (D-039, TO VERIFY).
    # The court sits in a notch of the outline, open on one side, so it is
    # already outside the body; only an enclosed court would need taking out.
    road_g = body.area - (body.intersection(court_u).area if court_u is not None else 0.0)
    # A facade cut that removes the first floor wall over its full height
    # (brief/facade.yaml cuts, answer R4: the wall over the porch) leaves no
    # floor area there.
    from model.facade import load as load_facade  # noqa: PLC0415
    hts = yaml.safe_load((REPO_ROOT / "brief" / "massing.yaml").read_text(encoding="utf-8"))["heights"]
    f_lo = float(hts["ground_floor_m"])
    f_hi = f_lo + float(hts["first_floor_m"]) - float(hts.get("slab_m", 0.30))
    measured_first = first_body
    for c in load_facade().get("cuts", []) or []:
        if c["z"][0] <= f_lo + 1e-6 and c["z"][1] >= f_hi - 1e-6:
            measured_first = measured_first.difference(box(c["u"][0], c["v"][0], c["u"][1], c["v"][1]))
    # Voids and cuts may overlap at the cut's edge: take them out as one shape.
    first_g = measured_first.difference(unary_union([v.poly() for v in f_voids])).area
    carport_g = carport_plate.area if carport_plate is not None else 0.0
    outdoor_first = sum(r.area for d, r in f_outdoor)
    ground_poly = unary_union([body] + ([carport_plate] if carport_plate is not None else []))

    stair_g = next((r for r in g_rooms if r.key == "stair_lift_ground"), None)
    stair_f = next((r for r in f_rooms if r.key == "stair_lift_first"), None)
    offset = abs(stair_g.v0 - stair_f.v0) if stair_g and stair_f else 0.0

    pool = plan.get("pool")
    deck = plan.get("deck")
    if pool:
        pool_t = tuple(pl.rect(*pool["x"], *pool["y"]).bounds)
        deck_t = tuple(pl.rect(*deck["x"], *deck["y"]).bounds)
        pool_t = (pool_t[0], pool_t[2], pool_t[1], pool_t[3])
        deck_t = (deck_t[0], deck_t[2], deck_t[1], deck_t[3])
        if not box(deck_t[0], deck_t[2], deck_t[1], deck_t[3]).within(site_to_grid(plot_polygon())):
            raise ValueError("pool deck escapes the plot")
    else:
        pool_t = deck_t = None

    def coords(g):
        return [[round(x, 3), round(y, 3)] for x, y in g.exterior.coords]

    def ext(g):
        b = g.bounds
        return (b[0], b[2], b[1], b[3])

    out = {
        "params": {"dw": 0.0, "de": 0.0, "W": pl.v1 - pl.v0, "corridor": 0.0,
                   "mirror": pl.mirror, "front_u": pl.u(float(plan["placement"]["front_wall_y_m"])),
                   "spare_along_road_m": pl.spare},
        "ground": g_rooms,
        "ground_circulation": g_circ,
        "first": f_rooms,
        "first_circulation": f_circ,
        "voids": f_voids,
        "first_outdoor": [r for d, r in f_outdoor],
        "first_outline": coords(first_body),
        "ground_outline": coords(body),
        "footprint_outline": coords(ground_poly if ground_poly.geom_type == "Polygon"
                                    else max(ground_poly.geoms, key=lambda g: g.area)),
        "plates": {"road": ext(body), "first": ext(first_body),
                   **({"carport": ext(carport_plate)} if carport_plate is not None else {})},
        "gfa": {"road": road_g, "ssw": 0.0, "living": 0.0, "first": first_g,
                "void": sum(v.area for v in f_voids), "carport": carport_g,
                "lawn_court": court_u.area if court_u is not None else 0.0,
                "first_outdoor": outdoor_first, "total": road_g + first_g},
        "stair_offset": offset,
        "massing": "R",
        "reference": plan.get("source", ""),
        "open_joins": plan.get("open_joins", {}),
        "room_links": plan.get("room_links", []),
        "doors": resolve_doors(plan, pl),
        "open_to_sky": plan.get("open_to_sky", []),
        "porches": [r.as_dict() for d, r in g_all if kind(d) == "porch"],
        "external_doors": plan.get("external_doors", []),
        "double_height": plan.get("double_height", []),
        "levels": plan.get("levels", {}),
    }
    if pool_t:
        out["pool"], out["deck"] = pool_t, deck_t
    return out


def main() -> int:
    lay = build_layout()
    g = lay["gfa"]
    print(f"reference plan placed: body {g['road']:.2f} + first {g['first']:.2f} = {g['total']:.2f} m2 GFA; "
          f"carport {g['carport']:.2f}, lawn court {g['lawn_court']:.2f}, first floor outdoor {g['first_outdoor']:.2f} (outside GFA, D-039)")
    for floor in ("ground", "first"):
        print(f"  {floor}:")
        for r in lay[floor]:
            print(f"    {r.key:<22}{r.u1 - r.u0:6.2f} x {r.v1 - r.v0:6.2f} = {r.area:7.2f} m2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
