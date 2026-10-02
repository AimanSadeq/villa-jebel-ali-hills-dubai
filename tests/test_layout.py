"""Checks on the generated plan in brief/layouts.yaml.

These test the geometry a builder would care about, not the estimate: every room
is placed once, nothing overlaps, the upper floor sits on the lower one, and the
stair cores stack.
"""

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import pytest
import yaml
from shapely.geometry import Point, Polygon, box

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

LAYOUTS = REPO_ROOT / "brief" / "layouts.yaml"
PROGRAM = REPO_ROOT / "brief" / "program.yaml"

lay = yaml.safe_load(LAYOUTS.read_text(encoding="utf-8"))
prog = yaml.safe_load(PROGRAM.read_text(encoding="utf-8"))


def _box(r):
    return box(r["u"][0], r["v"][0], r["u"][1], r["v"][1])


def test_every_program_room_is_placed_exactly_once():
    """Every room of brief/program.yaml, the reference villa's own dress rooms,
    toilets and bays (the ancillary list) included, is placed once."""
    placed = [r["key"] for f in ("ground", "first") for r in lay["floors"][f]["rooms"]]
    wanted = [r["key"] for f in ("ground", "first") for r in prog[f]]
    wanted += [a["key"] for a in prog.get("ancillary", []) or []]
    assert sorted(placed) == sorted(wanted)


def test_the_sunroom_is_removed_and_on_record():
    placed = {r["key"] for f in ("ground", "first") for r in lay["floors"][f]["rooms"]}
    assert "sunroom" not in placed
    removed = {r["key"]: r for r in prog.get("removed", [])}
    assert removed["sunroom"]["brief_target_m2"] == 20


@pytest.mark.parametrize("floor", ["ground", "first"])
def test_no_two_rooms_overlap(floor):
    rooms = lay["floors"][floor]["rooms"] + lay["floors"][floor]["circulation"]
    for a, b in combinations(rooms, 2):
        assert _box(a).intersection(_box(b)).area < 1e-6, (
            f"{a['key']} and {b['key']} overlap on the {floor} floor"
        )


def test_the_first_floor_stays_inside_the_envelope_and_cantilevers_no_further_than_the_reference():
    """The first floor is the reference's, a placeholder until the owner decides
    it (D-038). It may cantilever past the ground floor as the reference does
    (its bedroom wing runs about 1.6 m past the guest wing), but never past a
    setback line; the placeholder was trimmed there."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from model.massing import site_to_grid
    from model.site import buildable_envelope

    first = Polygon(lay["outlines"]["first"])
    ground = Polygon(lay["outlines"]["ground"])
    env = site_to_grid(buildable_envelope())
    assert first.buffer(-0.01).within(env), "the first floor crosses a setback line"
    over = first.difference(ground.buffer(0.01))
    reach = max((ground.distance(Point(x, y)) for x, y in over.exterior.coords),
                default=0.0) if not over.is_empty and over.geom_type == "Polygon" else 0.0
    assert reach <= 1.8, f"the first floor cantilevers {reach:.2f} m past the ground floor"


def test_the_stair_and_lift_stack():
    """The ground floor stair lane lies mostly under the first floor stair room
    (the dog leg's return flight runs over the stair hall), and the lift shafts
    coincide."""
    def room(f, k):
        return next(r for r in lay["floors"][f]["rooms"] if r["key"] == k)
    g, f = _box(room("ground", "stair_lift_ground")), _box(room("first", "stair_lift_first"))
    assert g.intersection(f).area >= 0.6 * g.area
    lg, lf = _box(room("ground", "lift")), _box(room("first", "lift_first"))
    assert lg.intersection(lf).area >= 0.9 * min(lg.area, lf.area)


# Circulation narrower than the 1.80 m the owner set for corridors (D-026,
# DDA FAQs Building Q12), each as drawn in the reference villa and flagged in
# docs/open-items.md (OI-26). A new narrow passage fails this test.
KNOWN_NARROW = {
    "service_passage": "reference: 1.0 m passage behind the store, OI-26",
    "service_steps": "reference: steps up from the carport, not a corridor",
    "stair_hall": "reference: 1.5 m hall between the lift and the stair, OI-26",
    "corridor_first": "first floor placeholder, 1.5 m, OI-26",
    "gallery": "first floor placeholder, 1.5 m, OI-26",
}


def test_circulation_is_the_dda_width_or_a_known_exception():
    for floor in ("ground", "first"):
        for c in lay["floors"][floor]["circulation"]:
            width = min(c["u"][1] - c["u"][0], c["v"][1] - c["v"][0])
            if width < lay["meta"]["corridor_m"] - 1e-3:
                assert c["key"] in KNOWN_NARROW, (
                    f"{c['key']} on the {floor} floor is {width:.2f} m wide and not a known exception")


def test_the_measured_plan_fits_the_cap():
    """The hard limit, tested on drawn geometry. Strict xfail until 2026-10-02,
    when trim D-027 brought the plan inside the cap and the marker came off."""
    m = lay["gfa_measured"]
    assert m["total"] <= m["cap"]


def test_the_measured_plan_holds_the_recommended_margin():
    """D-005: hold about 10 m2 back for the consultant's remeasure. A strict
    expected failure from D-029 (6.52 m2) until the central hall plan, D-036,
    restored the margin."""
    m = lay["gfa_measured"]
    assert m["margin"] >= 9.99 - 1e-6, f"only {m['margin']:.2f} m2 held back"


def test_there_is_no_drivers_room_and_its_removal_is_on_record():
    """Owner decision 2026-10-02, D-028."""
    placed = {r["key"] for f in ("ground", "first") for r in lay["floors"][f]["rooms"]}
    assert "drivers_room" not in placed
    assert any(r["key"] == "drivers_room" for r in prog.get("removed", []))


def test_the_outdoor_bathroom_and_plant_room_are_attached_to_the_carport():
    """D-043: the old driver's slot, split. Both share a wall with the carport;
    the bathroom opens onto it."""
    g = {r["key"]: r for r in lay["floors"]["ground"]["rooms"]}
    car = _box(g["garage"])
    for k in ("outdoor_bathroom", "plant_room"):
        d = _box(g[k]).distance(car)
        assert d <= 0.30, f"{k} is {d:.2f} m from the carport"


def test_the_outdoor_bathroom_counts_toward_gfa():
    """It is enclosed floor area, so it counts, like everything else here."""
    progs = {r["key"]: r for r in prog["ground"]}
    assert progs["outdoor_bathroom"]["gfa"] == "counts"


def test_the_measured_plan_holds_a_real_margin():
    """The floor below the D-005 recommendation: never design with nothing in
    hand against a consultant's remeasure."""
    assert lay["gfa_measured"]["margin"] >= 5.0


def _room(floor, key):
    return next(r for r in lay["floors"][floor]["rooms"] if r["key"] == key)


def test_the_plan_is_the_reference_mirrored_with_the_carport_south():
    """D-038, answer 7: the reference villa facing the road, mirrored, so the
    carport takes the south (low v) end and the majlis the north rear corner."""
    rooms = lay["floors"]["ground"]["rooms"]
    car, majlis = _room("ground", "garage"), _room("ground", "majlis")
    assert car["v"][0] <= min(r["v"][0] for r in rooms) + 1e-6
    assert majlis["v"][1] >= max(r["v"][1] for r in rooms) - 0.6
    assert majlis["u"][1] >= max(r["u"][1] for r in rooms) - 1e-6
    assert lay["meta"]["massing_option"] == "R"


def test_the_majlis_is_closed_off_from_the_dining():
    """D-042: a wall, with double doors by the foyer, between the dining and the
    majlis; they are not one open space."""
    joins = {frozenset(j.split("/")) for j in lay["open_joins"]["ground"]}
    assert frozenset(("dining", "majlis")) not in joins
    gap = _box(_room("ground", "dining")).distance(_box(_room("ground", "majlis")))
    assert 0.10 <= gap <= 0.30, f"no wall between the dining and the majlis ({gap:.2f} m)"
    assert any({l[0], l[1]} == {"dining", "majlis"} and l[3] == "door" for l in lay["room_links"])


def test_the_house_stays_behind_the_setback_lines():
    """Every enclosed ground floor room is inside the buildable envelope. Only
    the open carport and the porch reach into the front setback, as in the
    reference (TO VERIFY), and both stay on the plot."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from model.massing import site_to_grid
    from model.site import buildable_envelope, plot_polygon

    env = site_to_grid(buildable_envelope()).buffer(0.01)
    plot = site_to_grid(plot_polygon()).buffer(0.01)
    porch = {p["key"] for p in lay.get("porches", []) or []}
    for r in lay["floors"]["ground"]["rooms"] + lay["floors"]["ground"]["circulation"]:
        b = _box(r)
        if r["key"] == "garage" or r["key"] in porch:
            assert b.within(plot), f"{r['key']} leaves the plot"
        else:
            assert b.within(env), f"{r['key']} crosses a setback line"


def test_there_is_no_pool():
    """D-041: the owner does not want a pool."""
    assert not lay.get("pool")
    assert any(r["key"] == "pool" for r in prog.get("removed", []))
