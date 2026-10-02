"""Interiors: en-suites, wardrobes and the master suite, D-034 and D-035.

The planner reads every size from brief/program.yaml; these checks make sure
what it draws stays inside its room, leaves a usable bedroom, and gives every
bedroom what the brief asks for.
"""

import sys
from pathlib import Path

import pytest
import yaml
from shapely.geometry import box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model.interiors import plan  # noqa: E402

lay = yaml.safe_load((ROOT / "brief" / "layouts.yaml").read_text(encoding="utf-8"))
prog = yaml.safe_load((ROOT / "brief" / "program.yaml").read_text(encoding="utf-8"))
cfg = prog["interiors"]
interiors = plan(lay, prog)
rooms = {r["key"]: r for f in ("ground", "first")
         for r in lay["floors"][f]["rooms"]}


def _box(r):
    return box(r["u"][0], r["v"][0], r["u"][1], r["v"][1])


ANCILLARY = {a["key"]: a for a in prog.get("ancillary", []) or []}
PLACED = {r["key"]: r for f in ("ground", "first") for r in lay["floors"][f]["rooms"]}


def _own_bathroom(key):
    """A room's own toilet: planned by the interiors planner, or drawn as a room
    of its own in the plan (the reference villa, D-038) next to it or its dress."""
    if key in interiors and any(p.kind == "space" for p in interiors[key].parts):
        return True
    serving = {key} | {a["key"] for a in ANCILLARY.values() if a.get("serves") == key}
    for a in ANCILLARY.values():
        if a.get("serves") in serving and ("toilet" in a["key"] or "bath" in a["name"].lower()):
            if a["key"] in PLACED:
                return True
    return False


@pytest.mark.parametrize("key", list(cfg["ensuite"]["rooms"]) + ["maids_room", "master_suite"])
def test_every_ensuite_room_has_its_own_bathroom(key):
    """CLAUDE.md section 4: every bedroom en-suite, the maid's room with a bathroom."""
    assert _own_bathroom(key), f"{key} has no bathroom of its own"


@pytest.mark.parametrize("key", sorted(plan(lay, prog)))
def test_the_interior_stays_inside_its_room_and_tiles_it(key):
    it = interiors[key]
    room = _box(rooms[key])
    pieces = [it.main] + [p.poly for p in it.parts if p.kind == "space"] + it.partitions
    for g in pieces:
        assert g.buffer(-1e-6).within(room), f"{key}: a part escapes the room"
    assert abs(unary_union(pieces).area - room.area) < 1e-3, f"{key}: gaps or overlaps"
    for p in it.parts:
        if p.kind != "space":
            assert p.poly.buffer(-1e-6).within(it.main), f"{key}: {p.key} not in the room"


@pytest.mark.skip(reason="First floor placeholder until the owner decides that floor (D-038).")
def test_the_master_suite_has_everything_the_brief_lists():
    """CLAUDE.md section 4: bedroom, sitting area, his and hers walk-in
    wardrobes, large bathroom, coffee station, private balcony."""
    it = interiors["master_suite"]
    keys = {p.key for p in it.parts}
    assert {"master_suite.bathroom", "master_suite.wir_hers", "master_suite.wir_his",
            "master_suite.coffee_station"} <= keys
    bath = next(p for p in it.parts if p.key == "master_suite.bathroom")
    assert bath.poly.area >= cfg["master_suite"]["bathroom"]["min_m2"] - 1e-6
    for w in cfg["master_suite"]["walk_in_wardrobes"]:
        part = next(p for p in it.parts if p.key == f"master_suite.{w['key']}")
        assert part.poly.area >= w["target_m2"] - 1e-6
    assert it.main.area >= 40.0             # bedroom and sitting area
    assert cfg["master_suite"]["terrace"]["gfa"] == "excluded"


def test_the_maids_room_keeps_a_bathroom():
    assert _own_bathroom("maids_room")
