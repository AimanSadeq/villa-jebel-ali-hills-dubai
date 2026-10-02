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
    toilets and bays (the ancillary list) included, is placed once. A room the
    owner deferred is not placed and carries its reason (the linen store was
    deferred by 12l and removed by FF4, D-050)."""
    placed = [r["key"] for f in ("ground", "first") for r in lay["floors"][f]["rooms"]]
    wanted = [r["key"] for f in ("ground", "first") for r in prog[f] if not r.get("deferred")]
    wanted += [a["key"] for a in prog.get("ancillary", []) or []]
    assert sorted(placed) == sorted(wanted)


def test_the_linen_store_is_removed_and_on_record():
    """D-050, first floor answer FF4: no separate linen store; linen in the
    dressing rooms' built-in wardrobes. Nothing else is deferred."""
    removed = {r["key"]: r for r in prog.get("removed", [])}
    assert removed["linen_storage"]["decision"] == "D-050"
    assert not [r for f in ("ground", "first") for r in prog[f] if r.get("deferred")]
    placed = {r["key"] for f in ("ground", "first") for r in lay["floors"][f]["rooms"]}
    assert "linen_storage" not in placed


def test_first_floor_answers_are_built():
    """D-050: the family room opens to the gallery (FF5) and the first floor
    wall at the end of the living room void stands on the TV wall (FF7)."""
    joins = {frozenset(j.split("/")) for j in lay["open_joins"]["first"]}
    assert frozenset(("gallery", "family_living")) in joins
    assert not any(d["no"] == "F13" for d in lay["doors"])
    living, dining = _room("ground", "living"), _room("ground", "dining")
    b4 = _room("first", "bedroom_4")
    void = next(v for v in lay["floors"]["first"]["voids"] if v["key"] == "void_over_living")
    # In the grid the road-to-garden axis is u and the along-road axis is v.
    assert abs(b4["v"][0] - dining["v"][0]) < 0.01 and abs(void["v"][1] - living["v"][1]) < 0.01


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


@pytest.mark.xfail(strict=True, reason=(
    "D-046 and first floor answer FF6: the owner keeps 3.01 m2 inside the cap (2.17 m2 before R4, 1.30 m2 before FF7) and declines "
    "the D-005 reserve for now, knowing a remeasure could take the house over."))
def test_the_measured_plan_holds_the_recommended_margin():
    """D-005: hold about 10 m2 back for the consultant's remeasure. A strict
    expected failure from D-029 (6.52 m2) until the central hall plan, D-036,
    restored the margin, and again from answer 12 (D-046)."""
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


@pytest.mark.xfail(strict=True, reason=(
    "D-046 and first floor answer FF6: the owner keeps 3.01 m2 (2.17 m2 before R4, 1.30 m2 before FF7) and declines the 5 m2 floor "
    "for now (offered a 0.50 m step back of bedrooms 2 and 3 for 7.80 m2)."))
def test_the_measured_plan_holds_a_real_margin():
    """The floor below the D-005 recommendation: never design with nothing in
    hand against a consultant's remeasure."""
    assert lay["gfa_measured"]["margin"] >= 5.0


def _room(floor, key):
    return next(r for r in lay["floors"][floor]["rooms"] if r["key"] == key)


def test_the_plan_is_the_reference_mirrored_with_the_carport_south():
    """D-038, answer 7: the reference villa facing the road, mirrored, so the
    carport takes the south (low v) end. Answer 12a B: the dining takes the
    north rear corner, the salon the old lawn court beside it."""
    rooms = lay["floors"]["ground"]["rooms"]
    car, dining = _room("ground", "garage"), _room("ground", "dining")
    salon = _room("ground", "salon")
    assert car["v"][0] <= min(r["v"][0] for r in rooms) + 1e-6
    assert dining["v"][1] >= max(r["v"][1] for r in rooms) - 0.6
    assert dining["u"][1] >= max(r["u"][1] for r in rooms) - 1e-6
    assert abs(salon["v"][1] - dining["v"][1]) < 0.01, "12d: the salon lines up with the dining"
    assert lay["meta"]["massing_option"] == "R"


def test_answer_12_open_plan_with_a_tv_wall():
    """D-046: the salon is open to the foyer, the living room and the
    dining (12c, 12h); the island kitchen opens to the living room; a solid
    wall stands between the living room and the dining for the TV (12g)."""
    joins = {frozenset(j.split("/")) for j in lay["open_joins"]["ground"]}
    for pair in (("salon", "dining"), ("salon", "entrance_foyer"), ("salon", "living"),
                 ("show_kitchen", "living"), ("entrance_foyer", "living")):
        assert frozenset(pair) in joins, f"{pair} should be open"
    assert frozenset(("living", "dining")) not in joins
    gap = _box(_room("ground", "living")).distance(_box(_room("ground", "dining")))
    assert 0.10 <= gap <= 0.30, f"no TV wall between the living room and the dining ({gap:.2f} m)"
    assert "living" in lay["double_height"] and "entrance_foyer" in lay["double_height"]


def test_the_arabic_kitchen_is_walled_with_an_open_entrance_from_the_kitchen():
    """D-046, answer 12m: walled from the service passage, entered from the
    island kitchen by an opening with no door leaf."""
    joins = {frozenset(j.split("/")) for j in lay["open_joins"]["ground"]}
    assert frozenset(("arabic_kitchen_bay", "service_passage")) not in joins
    entry = [d for d in lay["doors"] if {d["a"], d["b"]} == {"show_kitchen", "arabic_kitchen"}]
    assert len(entry) == 1 and entry[0]["kind"] == "open"


def test_the_door_schedule_is_complete_and_numbered_once():
    """D-046: the doors the owner was shown on VJH-SK-013, each once, each with
    its source, each between placed rooms or to the outside. F13 (family
    room) is retired by FF5: the family room opens to the gallery."""
    nos = [d["no"] for d in lay["doors"]]
    assert len(nos) == len(set(nos)) == 34
    assert "F13" not in nos
    placed = {r["key"] for f in ("ground", "first")
              for r in lay["floors"][f]["rooms"] + lay["floors"][f]["circulation"]}
    for d in lay["doors"]:
        assert d["source"], d["no"]
        assert d["a"] in placed and (d["b"] in placed or d["b"] == "outside"), d["no"]


@pytest.mark.parametrize("bedroom", ["guest_bedroom", "master_suite", "bedroom_2",
                                     "bedroom_3", "bedroom_4"])
def test_every_bedroom_has_an_entry_door_from_a_hall(bedroom):
    """The defect in the 2026-10-02 build (commit 6322806): no bedroom had a
    door from a hall, only to its own dress or WC. Each now has one."""
    halls = {"entrance_foyer", "corridor_first", "gallery", "lift_lobby", "landing"}
    assert any(d["kind"] != "open" and {d["a"], d["b"]} & halls and bedroom in (d["a"], d["b"])
               for d in lay["doors"]), f"{bedroom} has no door from a hall"


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
