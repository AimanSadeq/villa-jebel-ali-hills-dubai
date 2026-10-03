"""The garden, brief/garden.yaml through src/model/landscape.py (G1 to G4, D-055).

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

import json
import sys
from pathlib import Path

import yaml
from shapely.geometry import Point, Polygon, box

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model import landscape  # noqa: E402
from model.massing import site_to_grid  # noqa: E402
from model.site import buildable_envelope, plot_polygon  # noqa: E402

SPEC = landscape.load()
LAY = yaml.safe_load((REPO_ROOT / "brief" / "layouts.yaml").read_text(encoding="utf-8"))
PLOT = site_to_grid(plot_polygon())
ENV = site_to_grid(buildable_envelope())
HOUSE = Polygon(LAY["outlines"]["road_ground"])
CARPORT = box(LAY["plates"]["carport"]["u"][0], LAY["plates"]["carport"]["v"][0],
              LAY["plates"]["carport"]["u"][1], LAY["plates"]["carport"]["v"][1])
G = landscape.build(SPEC, PLOT, HOUSE, CARPORT, [])


def test_the_bbq_pergola_sits_in_the_south_corner_inside_the_setback():
    """G1: by the Arabic kitchen door G21, inside the 3 m setback line."""
    p = SPEC["bbq"]["pergola"]
    assert ENV.buffer(0.01).contains(box(p["u"][0], p["v"][0], p["u"][1], p["v"][1]))
    g21 = next(d for d in LAY["doors"] if d["no"] == "G21")
    assert abs(g21["v"] - p["v"][1]) < 2.0 and p["u"][0] > g21["u"]


def test_every_garden_door_opens_onto_paving():
    """G2: the terrace links G20, G21 and G22; the front door's porch meets the court."""
    paving = [poly for s, poly in G.surfaces if s["kind"] == "paving"]
    for no in ("G20", "G21", "G22"):
        d = next(d for d in LAY["doors"] if d["no"] == no)
        out = Point(d["u"] + 0.4, d["v"])
        assert any(p.contains(out) for p in paving), no


def test_the_boundary_wall_rings_the_plot_with_two_gates_on_the_road():
    """G3, D-011: walls on every side; the car gate and the pedestrian gate on side 1."""
    walls = [it for it in G.items if it.object_type == "Landscape: boundary wall"]
    assert {it.name.split(", ")[1] for it in walls} == {"road side", "landscape side", "south side", "north side"}
    gates = [it for it in G.items if it.object_type == "Landscape: gate"]
    assert len(gates) == 2 and all(p.bounds[0] < 0.2 for g in gates for p, _, _ in g.prisms)
    screens = [it for it in G.items if it.object_type == "Landscape: wall screen"]
    assert {it.name.split(", ")[1] for it in screens} == {"road side", "landscape side"}


def test_surfaces_do_not_overlap_each_other_or_the_house():
    polys = [poly for _, poly in G.surfaces]
    for i, a in enumerate(polys):
        assert a.intersection(HOUSE).area < 0.01 and a.intersection(CARPORT).area < 0.01
        for b in polys[i + 1:]:
            assert a.intersection(b).area < 0.01


def test_trees_stand_in_planting_beds_or_lawns_inside_the_plot():
    beds = [poly for s, poly in G.surfaces if s["kind"] in ("bed", "lawn")]
    for tr, sp in G.trees:
        pt = Point(tr["u"], tr["v"])
        assert PLOT.contains(pt) and any(b.contains(pt) for b in beds), sp["name"]


def test_the_walkthrough_reaches_the_garden():
    """The exported walk zones carry the terrace, the lawn, the paths and the entrance steps."""
    data = json.loads((REPO_ROOT / "viewer" / "public" / "data" / "model.json").read_text(encoding="utf-8"))
    names = {z["name"] for z in data["walk"]["zones"]}
    for n in ("garden, garden terrace", "garden, lawn", "garden, entrance path", "garden, side path, north",
              "Entrance steps"):
        assert n in names, n
