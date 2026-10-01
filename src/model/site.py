"""Site geometry for Villa 5130272: plot polygon and buildable envelope.

Reads brief/site.yaml. Never hard-codes site values.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import hypot
from pathlib import Path

import yaml
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_YAML = REPO_ROOT / "brief" / "site.yaml"

SQM_TO_SQFT = 10.763910416709722


@lru_cache(maxsize=1)
def load_site(path: Path | None = None) -> dict:
    """Load and cache brief/site.yaml."""
    with open(path or SITE_YAML, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@dataclass(frozen=True)
class Vertex:
    id: str
    name: str
    x: float
    y: float
    # Source WGS84 position, carried so the local metric frame can always be
    # rebuilt or checked against the DDA GIS. Absent only if a future boundary
    # source supplies local coordinates alone.
    lon: float | None = None
    lat: float | None = None

    @property
    def xy(self) -> tuple[float, float]:
        return (self.x, self.y)

    @property
    def lonlat(self) -> tuple[float, float] | None:
        return None if self.lon is None or self.lat is None else (self.lon, self.lat)


@dataclass(frozen=True)
class Side:
    """One plot boundary side, as described on the DDA plan."""

    id: int
    start: Vertex
    end: Vertex
    stated_length_m: float
    computed_length_m: float
    orientation: str
    adjacency: str
    is_main_access: bool

    @property
    def deviation_m(self) -> float:
        return self.computed_length_m - self.stated_length_m

    @property
    def deviation_pct(self) -> float:
        if self.stated_length_m == 0:
            return 0.0
        return self.deviation_m / self.stated_length_m * 100.0

    @property
    def midpoint(self) -> tuple[float, float]:
        return (
            (self.start.x + self.end.x) / 2.0,
            (self.start.y + self.end.y) / 2.0,
        )


def vertices(site: dict | None = None) -> list[Vertex]:
    site = site or load_site()
    return [Vertex(**v) for v in site["boundary"]["vertices"]]


def vertex_map(site: dict | None = None) -> dict[str, Vertex]:
    return {v.id: v for v in vertices(site)}


def plot_polygon(site: dict | None = None) -> Polygon:
    """The plot boundary as a closed polygon, from the site.yaml vertices."""
    poly = Polygon([v.xy for v in vertices(site)])
    if not poly.is_valid:
        raise ValueError(
            "Plot polygon from brief/site.yaml is not valid (self-intersecting). "
            "Check the vertex order."
        )
    # Shoelace sign depends on winding. Normalise to counter-clockwise so that a
    # negative buffer is unambiguously inward.
    return poly if poly.exterior.is_ccw else Polygon(list(poly.exterior.coords)[::-1])


def buildable_envelope(site: dict | None = None, setback_m: float | None = None) -> Polygon:
    """Plot polygon offset inward by the setback on every side.

    Uses a mitred join with a high mitre limit so the bend at vertex C is offset
    to a true corner rather than clipped back. Shapely's default mitre_limit of
    5.0 can bevel sharp corners, which would understate the envelope.
    """
    site = site or load_site()
    setback = setback_m if setback_m is not None else float(site["regulations"]["setback_m"])

    env = plot_polygon(site).buffer(-setback, join_style="mitre", mitre_limit=100.0)

    if env.is_empty:
        raise ValueError(f"A {setback} m setback leaves no buildable area.")
    if isinstance(env, MultiPolygon):
        # A concave plot can split into parts under a large setback. Keep them
        # all, but report it, because a split envelope changes the design problem.
        env = unary_union(env)
    return env


def sides(site: dict | None = None) -> list[Side]:
    """Plot sides, with the length stated on the DDA plan beside the computed one."""
    site = site or load_site()
    vmap = vertex_map(site)
    out: list[Side] = []
    for s in site["sides"]:
        start, end = vmap[s["from"]], vmap[s["to"]]
        if "via" in s:
            via = vmap[s["via"]]
            computed = hypot(via.x - start.x, via.y - start.y) + hypot(
                end.x - via.x, end.y - via.y
            )
        else:
            computed = hypot(end.x - start.x, end.y - start.y)
        out.append(
            Side(
                id=s["id"],
                start=start,
                end=end,
                stated_length_m=float(s["length_m"]),
                computed_length_m=computed,
                orientation=s["orientation"],
                adjacency=s["adjacency"],
                is_main_access=bool(s.get("is_main_access", False)),
            )
        )
    return sorted(out, key=lambda s: s.id)


def area_check(site: dict | None = None) -> dict:
    """Compare the computed geometry against the official DDA figures."""
    site = site or load_site()
    plot = plot_polygon(site)
    env = buildable_envelope(site)

    official = float(site["plot"]["area_m2"])
    computed = plot.area
    max_gfa = float(site["regulations"]["max_gfa_m2"])
    capacity = env.area * 2.0  # G+1 means two storeys over the envelope footprint

    return {
        "official_plot_area_m2": official,
        "computed_plot_area_m2": computed,
        "plot_area_deviation_m2": computed - official,
        "plot_area_deviation_pct": (computed - official) / official * 100.0,
        "setback_m": float(site["regulations"]["setback_m"]),
        "envelope_area_m2": env.area,
        "envelope_is_split": isinstance(env, MultiPolygon),
        "envelope_pct_of_plot": env.area / computed * 100.0,
        "max_gfa_m2": max_gfa,
        "geometric_capacity_m2": capacity,
        "gfa_as_pct_of_capacity": max_gfa / capacity * 100.0,
        "binding_constraint": "GFA" if max_gfa < capacity else "setbacks",
        "boundary_to_verify": bool(site["boundary"].get("to_verify")),
    }


def sqft(value_m2: float) -> float:
    return value_m2 * SQM_TO_SQFT


def report(site: dict | None = None) -> str:
    site = site or load_site()
    a = area_check(site)
    lines: list[str] = []
    w = lines.append

    w("SITE AND ENVELOPE CHECK")
    w(f"Plot {site['plot']['number']}, {site['plot']['community']}")
    w(f"Authority: {site['plot']['authority']}")
    w("")
    w(f"{'Official plot area':<34}{a['official_plot_area_m2']:>10.2f} m2 "
      f"{sqft(a['official_plot_area_m2']):>11.2f} sq ft")
    w(f"{'Computed from site.yaml vertices':<34}{a['computed_plot_area_m2']:>10.2f} m2 "
      f"{sqft(a['computed_plot_area_m2']):>11.2f} sq ft")
    w(f"{'Deviation':<34}{a['plot_area_deviation_m2']:>10.2f} m2 "
      f"{a['plot_area_deviation_pct']:>10.3f} %")
    w("")
    w(f"{'Setback, all sides':<34}{a['setback_m']:>10.2f} m")
    w(f"{'Buildable envelope':<34}{a['envelope_area_m2']:>10.2f} m2 "
      f"{sqft(a['envelope_area_m2']):>11.2f} sq ft")
    w(f"{'Envelope as share of plot':<34}{a['envelope_pct_of_plot']:>10.1f} %")
    w(f"{'Envelope split into parts':<34}{str(a['envelope_is_split']):>10s}")
    w("")
    w(f"{'Max GFA (DDA)':<34}{a['max_gfa_m2']:>10.2f} m2 "
      f"{sqft(a['max_gfa_m2']):>11.2f} sq ft")
    w(f"{'Geometric capacity, G+1':<34}{a['geometric_capacity_m2']:>10.2f} m2 "
      f"{sqft(a['geometric_capacity_m2']):>11.2f} sq ft")
    w(f"{'GFA as share of capacity':<34}{a['gfa_as_pct_of_capacity']:>10.1f} %")
    w(f"{'Binding constraint':<34}{a['binding_constraint']:>10s}")
    w("")
    w("SIDE LENGTHS: stated on the DDA plan vs computed from the vertices")
    w(f"{'Side':<6}{'Stated':>9}{'Computed':>10}{'Dev':>8}{'Dev %':>8}  "
      f"{'Orientation':<12}Adjacency")
    for s in sides(site):
        flag = "  MAIN ACCESS" if s.is_main_access else ""
        w(f"{s.id:<6}{s.stated_length_m:>9.2f}{s.computed_length_m:>10.2f}"
          f"{s.deviation_m:>8.2f}{s.deviation_pct:>8.2f}  {s.orientation:<12}"
          f"{s.adjacency}{flag}")

    w("")
    w("DATA PROVENANCE")
    w(f"Boundary source: {site['boundary'].get('source', 'not stated')}")
    if a["boundary_to_verify"]:
        w("TO VERIFY: the Demarcation Certificate remains the legally authoritative")
        w("source and should replace these coordinates when issued.")

    orient = site["orientation"]
    if orient.get("to_verify"):
        w("TO VERIFY: plan-up is assumed to be true north. See brief/site.yaml.")
    else:
        w(f"VERIFIED {orient.get('verified_on', '')}: plan-up is true north, mean "
          f"bearing error {orient.get('mean_bearing_error_deg', 0):+.2f} deg.")

    loc = site["location"]
    tag = "TO VERIFY" if loc.get("to_verify") else f"VERIFIED {loc.get('verified_on', '')}"
    w(f"{tag}: site at {loc['latitude']:.6f} N, {loc['longitude']:.6f} E, "
      f"{loc['timezone']}.")

    w("")
    w(site["meta"]["stamp"])
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
