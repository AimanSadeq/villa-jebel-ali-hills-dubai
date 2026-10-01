"""Massing options for Villa 5130272, with real shadow geometry.

Reads brief/massing.yaml. Converts the plot building grid to site coordinates,
checks every block against the buildable envelope, and casts true shadows from
the massing onto the ground to score each option on afternoon shade.

Shadows are computed geometrically, not estimated. For a mass of height H and a
sun unit vector (sx, sy, sz), every point of the roof lands at ground offset
-(H / sz) * (sx, sy). The shadow of an extruded polygon is the union of the
footprint, the offset footprint, and the quadrilateral swept by each edge. That
is correct for concave footprints too, which matters for the L-shaped option C
where a convex hull would overstate the shade by filling in the courtyard.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model.site import buildable_envelope, plot_polygon  # noqa: E402

MASSING_YAML = REPO_ROOT / "brief" / "massing.yaml"


@lru_cache(maxsize=1)
def load_massing(path: Path | None = None) -> dict:
    with open(path or MASSING_YAML, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def grid_to_site(geom: Polygon, bearing_deg: float | None = None) -> Polygon:
    """Grid coordinates to site x/y. Inverse of the rotation used to find the grid."""
    if bearing_deg is None:
        bearing_deg = float(load_massing()["grid"]["bearing_deg"])
    return affinity.rotate(geom, -bearing_deg, origin=(0, 0))


def site_to_grid(geom: Polygon, bearing_deg: float | None = None) -> Polygon:
    if bearing_deg is None:
        bearing_deg = float(load_massing()["grid"]["bearing_deg"])
    return affinity.rotate(geom, bearing_deg, origin=(0, 0))


def _rect(spec: dict) -> Polygon:
    (u0, u1), (v0, v1) = spec["u"], spec["v"]
    return Polygon([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])


@dataclass
class Option:
    key: str
    name: str
    summary: str
    ground: Polygon            # site coordinates
    first: Polygon
    garage: Polygon
    pool: Polygon
    deck: Polygon
    driveway: Polygon
    heights: dict = field(default_factory=dict)

    @property
    def ground_area(self) -> float:
        return self.ground.area

    @property
    def first_area(self) -> float:
        return self.first.area

    @property
    def open_ground_m2(self) -> float:
        return plot_polygon().area - self.ground.area

    @property
    def pool_and_deck(self) -> Polygon:
        return unary_union([self.pool, self.deck])


def options() -> list[Option]:
    m = load_massing()
    bearing = float(m["grid"]["bearing_deg"])
    out: list[Option] = []

    for spec in m["options"]:
        def conv(key, many=False):
            raw = spec[key]
            if many:
                return grid_to_site(unary_union([_rect(r) for r in raw]), bearing)
            return grid_to_site(_rect(raw), bearing)

        out.append(Option(
            key=spec["key"],
            name=spec["name"],
            summary=" ".join(spec["summary"].split()),
            ground=conv("ground", many=True),
            first=conv("first", many=True),
            garage=conv("garage", many=True),
            pool=conv("pool"),
            deck=conv("deck"),
            driveway=conv("driveway"),
            heights=m["heights"],
        ))
    return out


def validate(option: Option) -> list[str]:
    """Every built block must sit inside the buildable envelope. Pool too."""
    env = buildable_envelope()
    plot = plot_polygon()
    problems: list[str] = []

    for label, geom in (("ground floor", option.ground),
                        ("first floor", option.first),
                        ("garage", option.garage)):
        if not geom.within(env.buffer(1e-6)):
            outside = geom.difference(env).area
            problems.append(
                f"option {option.key}: {label} escapes the buildable envelope by "
                f"{outside:.2f} m2"
            )

    # The pool is held inside the envelope as well. Whether a pool may sit in the
    # 3 m setback is TO VERIFY, so the options do not rely on it.
    if not option.pool.within(env.buffer(1e-6)):
        problems.append(
            f"option {option.key}: pool is outside the buildable envelope, which "
            "the options deliberately do not rely on. See docs/open-items.md"
        )
    if not option.deck.within(plot.buffer(1e-6)):
        problems.append(f"option {option.key}: pool deck escapes the plot")

    if not option.first.within(option.ground.buffer(1e-6)):
        problems.append(
            f"option {option.key}: first floor oversails the ground floor by "
            f"{option.first.difference(option.ground).area:.2f} m2"
        )

    if abs(option.pool.area - 40.0) > 0.5:
        problems.append(
            f"option {option.key}: pool is {option.pool.area:.1f} m2, brief asks "
            "for 10 x 4 m, 40 m2"
        )
    return problems


def wall_to_boundary(option: Option) -> list[dict]:
    """Shortest distance from the villa wall to each plot boundary.

    Measured as the true nearest approach between the ground floor footprint and
    each side, not as a bounding box offset, so it stays correct for the
    L-shaped option and for a plot that is not an exact rectangle.

    Returns the measured distance and the two points it was measured between,
    so a drawing can show the dimension exactly where it was taken.
    """
    from shapely.geometry import LineString
    from shapely.ops import nearest_points

    from model.site import load_site, sides, vertex_map

    site = load_site()
    vmap = vertex_map(site)
    setback = float(site["regulations"]["setback_m"])

    out = []
    for s in sides():
        pts = [(s.start.x, s.start.y)]
        raw = next(r for r in site["sides"] if r["id"] == s.id)
        if "via" in raw:
            via = vmap[raw["via"]]
            pts.append((via.x, via.y))
        pts.append((s.end.x, s.end.y))

        line = LineString(pts)
        a, b = nearest_points(option.ground, line)
        distance = a.distance(b)
        out.append({
            "side": s.id,
            "adjacency": s.adjacency,
            "is_main_access": s.is_main_access,
            "distance_m": distance,
            "from_xy": (a.x, a.y),
            "to_xy": (b.x, b.y),
            "meets_setback": distance >= setback - 1e-6,
        })
    return out


def shadow(footprint: Polygon, height: float, sun: tuple[float, float, float]) -> Polygon:
    """Ground shadow cast by a polygon extruded to `height`.

    `sun` is a unit vector pointing from the ground toward the sun. Returns an
    empty polygon when the sun is at or below the horizon.
    """
    sx, sy, sz = sun
    if sz <= 1e-6:
        return Polygon()

    ox, oy = -sx * height / sz, -sy * height / sz
    moved = affinity.translate(footprint, ox, oy)

    parts = [footprint, moved]
    for poly in ([footprint] if isinstance(footprint, Polygon)
                 else list(footprint.geoms)):
        coords = list(poly.exterior.coords)
        for (x0, y0), (x1, y1) in zip(coords, coords[1:]):
            parts.append(Polygon([(x0, y0), (x1, y1),
                                  (x1 + ox, y1 + oy), (x0 + ox, y0 + oy)]))
    return unary_union([p for p in parts if p.is_valid and not p.is_empty])


def option_shadow(option: Option, sun: tuple[float, float, float]) -> Polygon:
    """Combined shadow of the ground mass and the taller first floor mass."""
    h = option.heights
    ground_h = float(h["ground_floor_m"])
    overall_h = float(h["overall_m"])

    # The single storey part casts from its own roof, the two storey part from
    # the parapet. Modelling one flat height would misstate both.
    single = option.ground.difference(option.first)
    parts = [shadow(single, ground_h + float(h["parapet_m"]), sun),
             shadow(option.first, overall_h, sun)]
    return unary_union([p for p in parts if not p.is_empty])


def shade_fraction(option: Option, when: pd.Timestamp) -> float:
    """Fraction of the pool and its deck lying in the villa's shadow."""
    from analysis.sun_study import sun_vector  # noqa: PLC0415

    sun = sun_vector(when)
    target = option.pool_and_deck
    if sun is None:
        return 1.0   # sun below the horizon, everything is in shade
    shaded = option_shadow(option, sun).intersection(target)
    return shaded.area / target.area


def score(option: Option, year: int = 2026) -> dict:
    """Score an option on afternoon shade in summer and midday sun in winter."""
    m = load_massing()
    a = m["assessment"]
    tz = "Asia/Dubai"

    summer, winter = [], []
    detail = {}
    for date in a["summer_dates"]:
        for hour in a["afternoon_hours"]:
            t = pd.Timestamp(f"{year}-{date} {hour:02d}:00", tz=tz)
            f = shade_fraction(option, t)
            summer.append(f)
            detail[f"{date} {hour:02d}:00"] = f
    for date in a["winter_dates"]:
        for hour in a["winter_midday_hours"]:
            t = pd.Timestamp(f"{year}-{date} {hour:02d}:00", tz=tz)
            winter.append(shade_fraction(option, t))

    return {
        "key": option.key,
        "name": option.name,
        "ground_m2": option.ground_area,
        "first_m2": option.first_area,
        "open_ground_m2": option.open_ground_m2,
        "pool_deck_m2": option.pool_and_deck.area,
        "summer_pm_shade": float(np.mean(summer)),
        "winter_midday_shade": float(np.mean(winter)),
        "winter_midday_sun": 1.0 - float(np.mean(winter)),
        "detail": detail,
    }


def scores() -> pd.DataFrame:
    rows = [score(o) for o in options()]
    df = pd.DataFrame([{k: v for k, v in r.items() if k != "detail"} for r in rows])
    return df


if __name__ == "__main__":
    problems = [p for o in options() for p in validate(o)]
    if problems:
        print("VALIDATION FAILED")
        for p in problems:
            print("  " + p)
        raise SystemExit(1)
    print("All options validate inside the buildable envelope.\n")
    print(scores().to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    print()
    print("WALL TO BOUNDARY, metres")
    print(f"{'Option':<8}{'Side 1':>9}{'Side 2':>9}{'Side 3':>9}{'Side 4':>9}")
    for o in options():
        d = {r["side"]: r["distance_m"] for r in wall_to_boundary(o)}
        print(f"{o.key:<8}" + "".join(f"{d[i]:>9.2f}" for i in (1, 2, 3, 4)))
