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


def test_every_ensuite_bedroom_and_the_master_are_planned():
    wanted = set(cfg["ensuite"]["rooms"]) | set(cfg["staff_ensuite"]["rooms"]) | {"master_suite"}
    assert wanted <= set(interiors)


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


@pytest.mark.parametrize("key", cfg["ensuite"]["rooms"])
def test_each_ensuite_has_a_bathroom_a_wardrobe_and_a_bedroom(key):
    it = interiors[key]
    kinds = {p.kind for p in it.parts}
    assert {"space", "wardrobe"} <= kinds
    bath = next(p for p in it.parts if p.kind == "space")
    b = cfg["ensuite"]["bathroom"]
    assert abs(bath.poly.area - b["width_m"] * b["depth_m"]) < 1e-6
    assert it.main.area >= cfg["ensuite"]["bedroom_min_m2"] - 1e-6
    assert it.entry is not None and it.entry.width >= 0.9
    assert len(it.doors) == 1               # the bathroom door


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


def test_the_master_terrace_sits_on_the_kitchen_roof():
    """D-035: the terrace door is on the master's east wall, which faces the
    single storey kitchen and dining block."""
    m = rooms["master_suite"]
    ssw = lay["plates"]["ssw"]
    assert abs(m["u"][1] + lay["meta"]["wall_external_m"] - ssw["u"][0]) < 1e-6
    assert m["v"][0] >= ssw["v"][0] - 1e-6 and m["v"][1] <= ssw["v"][1] + 1e-6


def test_the_maids_room_keeps_a_bathroom():
    it = interiors["maids_room"]
    assert any(p.kind == "space" for p in it.parts)
    assert it.main.area >= cfg["staff_ensuite"]["bedroom_min_m2"] - 1e-6
