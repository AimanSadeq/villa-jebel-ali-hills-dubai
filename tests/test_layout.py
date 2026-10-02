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


@pytest.mark.xfail(strict=True, reason=(
    "D-029 left 6.52 m2 against the 9.99 m2 recommended in D-005; the family hall, "
    "D-032, brought it to 9.89 m2. Inside the cap, 0.10 m2 thinner than advised. "
    "Strict, so the marker must come off if the margin is ever restored."))
def test_the_measured_plan_holds_the_recommended_margin():
    """D-005: hold about 10 m2 back for the consultant's remeasure."""
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


def test_the_family_rooms_are_reached_without_crossing_the_majlis():
    """A link hall must run from the corridor to the dining room, so the
    kitchen, dining and living wing is never reached through the majlis or the
    Arabic kitchen. Found while placing doors in Phase 3."""
    g = lay["floors"]["ground"]
    corridor = next(c for c in g["circulation"] if c["key"] == "corridor")
    link = next(c for c in g["circulation"] if c["key"] == "hall_link")
    dining = next(r for r in g["rooms"] if r["key"] == "dining")
    # The link starts across one partition from the corridor...
    assert abs(link["u"][0] - corridor["u"][1] - 0.15) < 1e-3
    # ...and ends across one external wall thickness from the dining room...
    assert abs(dining["u"][0] - link["u"][1] - lay["meta"]["wall_external_m"]) < 1e-3
    # ...with enough shared length for a door.
    overlap = min(link["v"][1], dining["v"][1]) - max(link["v"][0], dining["v"][0])
    assert overlap >= 1.2
