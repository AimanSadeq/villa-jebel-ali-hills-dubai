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


def test_corridors_are_the_dda_width():
    for floor in ("ground", "first"):
        for c in lay["floors"][floor]["circulation"]:
            assert abs((c["u"][1] - c["u"][0]) - lay["meta"]["corridor_m"]) < 1e-6


@pytest.mark.xfail(strict=True, reason=(
    "OI-22: the drawn plan measures 669.29 m2 against the 662.99 m2 cap. Strict, "
    "so this test fails the suite the moment the plan fits, prompting removal of "
    "the marker rather than leaving a stale expectation."))
def test_the_measured_plan_fits_the_cap():
    m = lay["gfa_measured"]
    assert m["total"] <= m["cap"]
