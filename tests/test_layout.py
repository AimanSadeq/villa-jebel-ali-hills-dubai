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
from shapely.geometry import Polygon, box

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

LAYOUTS = REPO_ROOT / "brief" / "layouts.yaml"
PROGRAM = REPO_ROOT / "brief" / "program.yaml"

lay = yaml.safe_load(LAYOUTS.read_text(encoding="utf-8"))
prog = yaml.safe_load(PROGRAM.read_text(encoding="utf-8"))


def _box(r):
    return box(r["u"][0], r["v"][0], r["u"][1], r["v"][1])


def test_every_program_room_is_placed_exactly_once():
    placed = [r["key"] for f in ("ground", "first") for r in lay["floors"][f]["rooms"]]
    wanted = [r["key"] for f in ("ground", "first") for r in prog[f]]
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


def test_the_first_floor_sits_on_the_ground_floor():
    first = Polygon(lay["outlines"]["first"])
    ground = Polygon(lay["outlines"]["road_ground"])
    assert first.buffer(-1e-6).within(ground)


def test_the_stair_cores_stack():
    g = next(r for r in lay["floors"]["ground"]["rooms"] if r["key"] == "stair_lift_ground")
    f = next(r for r in lay["floors"]["first"]["rooms"] if r["key"] == "stair_lift_first")
    assert g["u"] == f["u"]
    assert abs(g["v"][0] - f["v"][0]) < 1e-6


OPEN_HALLS = {"family_hall"}


def test_corridors_are_the_dda_width():
    """Width is the narrow dimension: the main corridors run along the plan and
    the link hall runs across it. Corridors are exactly the DDA width; open
    halls (D-032, D-033) are wider by design and must be at least it."""
    for floor in ("ground", "first"):
        for c in lay["floors"][floor]["circulation"]:
            width = min(c["u"][1] - c["u"][0], c["v"][1] - c["v"][0])
            if c["key"] in OPEN_HALLS:
                assert width >= lay["meta"]["corridor_m"] - 1e-6, c["key"]
            else:
                assert abs(width - lay["meta"]["corridor_m"]) < 1e-6, c["key"]


def test_every_first_floor_room_opens_off_the_family_hall():
    """D-032: no upstairs corridor. Each bedroom, the linen store and the stair
    shares a wall with the hall, its landing, or the family room. The master is
    entered from the landing, so it shares no wall with the family room."""
    f = lay["floors"]["first"]
    hubs = list(f["circulation"]) + [r for r in f["rooms"] if r["key"] == "family_living"]
    fam = next(r for r in f["rooms"] if r["key"] == "family_living")
    for r in f["rooms"]:
        if r["key"] == "family_living":
            continue
        # A shared partition at least a door wide (1.0 m).
        touching = []
        for h in hubs:
            i = _box(r).buffer(0.151, join_style=2).intersection(_box(h))
            if not i.is_empty and max(i.bounds[2] - i.bounds[0], i.bounds[3] - i.bounds[1]) >= 1.0:
                touching.append(h["key"])
        assert touching, f"{r['key']} has no wall on the hall"
    master = next(r for r in f["rooms"] if r["key"] == "master_suite")
    assert _box(master).distance(_box(fam)) > 1.0


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


def test_the_outdoor_bathroom_sits_on_an_external_wall():
    """It takes its door from outside, so one face must be the building's
    external wall: the courtyard face of the two storey wing."""
    bath = next(r for r in lay["floors"]["ground"]["rooms"] if r["key"] == "outdoor_bathroom")
    road = lay["plates"]["road"]
    t_ext = lay["meta"]["wall_external_m"]
    assert abs(bath["u"][1] - (road["u"][1] - t_ext)) < 1e-3, (
        "the outdoor bathroom does not reach the courtyard wall"
    )


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


def _shared_length(a, b, gap):
    """Length of wall two rectangles share across a gap of one wall thickness."""
    if abs(b["u"][0] - a["u"][1] - gap) < 2e-3 or abs(a["u"][0] - b["u"][1] - gap) < 2e-3:
        return min(a["v"][1], b["v"][1]) - max(a["v"][0], b["v"][0])
    if abs(b["v"][0] - a["v"][1] - gap) < 2e-3 or abs(a["v"][0] - b["v"][1] - gap) < 2e-3:
        return min(a["u"][1], b["u"][1]) - max(a["u"][0], b["u"][0])
    return 0.0


def test_the_hall_is_central_with_the_rooms_the_owner_placed_around_it():
    """D-036: from the front door, the majlis is on the left (north), the
    dining on the right (south), the living room straight ahead (east), and
    the kitchen beyond the dining."""
    t_int, t_ext = lay["meta"]["wall_internal_m"], lay["meta"]["wall_external_m"]
    hall, majlis = _room("ground", "entrance_foyer"), _room("ground", "majlis")
    dining, living = _room("ground", "dining"), _room("ground", "living")
    show, stair = _room("ground", "show_kitchen"), _room("ground", "stair_lift_ground")
    road = lay["plates"]["road"]
    # The hall spans the wing and touches the road wall: the front door.
    assert abs(hall["u"][0] - (road["u"][0] + t_ext)) < 1e-3
    assert abs(hall["u"][1] - (road["u"][1] - t_ext)) < 1e-3
    # Majlis north of the hall, across one partition.
    assert _shared_length(hall, majlis, t_int) >= 6.0 and majlis["v"][0] > hall["v"][1]
    # Dining south of the hall, reached along the entrance gallery.
    gallery = next(c for c in lay["floors"]["ground"]["circulation"] if c["key"] == "corridor")
    assert dining["v"][1] < hall["v"][0]
    assert _shared_length(gallery, hall, t_int) >= 1.5
    assert _shared_length(gallery, dining, t_int) >= 2.4
    # Living straight ahead through the courtyard wall, a wide open join.
    assert living["u"][0] >= hall["u"][1] + t_ext - 1e-3
    assert _shared_length(hall, living, t_ext) >= 2.4
    # Kitchen beyond the dining, sharing enough wall to open to it.
    assert show["u"][0] >= dining["u"][1] + t_ext - 1e-3
    assert _shared_length(dining, show, t_ext) >= 2.4
    # The stair opens off the hall.
    assert _shared_length(stair, hall, t_int) >= 2.4


def test_the_living_room_is_a_tall_block_with_nothing_above():
    """D-036: the living block sits outside the first floor outline."""
    living = lay["plates"]["living"]
    first = Polygon(lay["outlines"]["first"])
    assert box(living["u"][0] + 0.01, living["v"][0] + 0.01,
               living["u"][1], living["v"][1]).disjoint(first)


def test_the_pool_sits_on_the_living_room_deck_inside_the_envelope():
    """D-037: the deck starts at the living room's north wall; nothing of the
    pool or deck runs into the building or past the setback line."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from model.massing import site_to_grid
    from model.site import buildable_envelope

    pool, deck, living = lay["pool"], lay["deck"], lay["plates"]["living"]
    assert abs(deck["v"][0] - living["v"][1]) < 1e-3
    deck_box = box(deck["u"][0], deck["v"][0], deck["u"][1], deck["v"][1])
    pool_box = box(pool["u"][0], pool["v"][0], pool["u"][1], pool["v"][1])
    assert pool_box.within(deck_box)
    assert abs(pool_box.area - 40.0) < 1e-6
    ground = Polygon(lay["outlines"]["ground"])
    assert deck_box.buffer(-1e-6).disjoint(ground)
    assert deck_box.buffer(-1e-6).within(site_to_grid(buildable_envelope()))
