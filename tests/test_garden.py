"""The garden, brief/garden.yaml through src/model/landscape.py (G1 to G4, D-055,
redesigned for the courtyard villa, D-060).

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
    """G1: by the show kitchen's garden door G09, inside the 3 m setback line."""
    p = SPEC["bbq"]["pergola"]
    assert ENV.buffer(0.01).contains(box(p["u"][0], p["v"][0], p["u"][1], p["v"][1]))
    g09 = next(d for d in LAY["doors"] if d["no"] == "G09")
    assert p["v"][0] - 2.0 < g09["v"] < p["v"][1] + 2.0 and p["u"][0] > g09["u"]


def test_every_garden_door_opens_onto_paving():
    """G2: the terraces meet the kitchen, dining and family living garden doors."""
    paving = [poly for s, poly in G.surfaces if s["kind"] == "paving"]
    for no in ("G09", "G14", "G15"):
        d = next(d for d in LAY["doors"] if d["no"] == no)
        out = Point(d["u"] + 0.4, d["v"])
        assert any(p.contains(out) for p in paving), no


def test_the_boundary_wall_leaves_the_road_side_open_with_no_gate():
    """D-011 walls to the neighbours and the landscape plot (TO VERIFY, OI-14);
    the handover: no vehicle gate and no pedestrian gate, so the road side is
    an open planted edge."""
    walls = [it for it in G.items if it.object_type == "Landscape: boundary wall"]
    assert {it.name.split(", ")[1] for it in walls} == {"landscape side", "south side", "north side"}
    assert not [it for it in G.items if it.object_type == "Landscape: gate"]
    screens = [it for it in G.items if it.object_type == "Landscape: wall screen"]
    assert {it.name.split(", ")[1] for it in screens} == {"landscape side"}


def test_surfaces_do_not_overlap_each_other_or_the_house():
    polys = [poly for _, poly in G.surfaces]
    for i, a in enumerate(polys):
        assert a.intersection(HOUSE).area < 0.01 and a.intersection(CARPORT).area < 0.01
        for b in polys[i + 1:]:
            assert a.intersection(b).area < 0.01


def test_trees_stand_in_planting_beds_or_lawns_inside_the_plot():
    beds = [poly for s, poly in G.surfaces if s["kind"] in ("bed", "lawn")]
    cr = next(r for r in LAY["floors"]["ground"]["rooms"] if r["key"] == "courtyard")
    court = box(cr["u"][0], cr["v"][0], cr["u"][1], cr["v"][1])
    for tr, sp in G.trees:
        pt = Point(tr["u"], tr["v"])
        if tr.get("courtyard"):
            assert court.contains(pt), sp["name"]      # the statement tree, in its planter (S2)
            continue
        assert PLOT.contains(pt) and any(b.contains(pt) for b in beds), sp["name"]


def test_the_walkthrough_reaches_the_garden():
    """The exported walk zones carry the terrace, the lawn, the paths and the entrance steps."""
    data = json.loads((REPO_ROOT / "viewer" / "public" / "data" / "model.json").read_text(encoding="utf-8"))
    names = {z["name"] for z in data["walk"]["zones"]}
    for n in ("garden, garden terrace", "garden, lawn", "garden, entrance path", "garden, side path, north",
              "Entrance steps"):
        assert n in names, n
