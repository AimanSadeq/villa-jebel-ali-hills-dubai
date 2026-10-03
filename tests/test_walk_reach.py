"""Every room and the garden can be walked to (Phase 4 review, 2026-10-03).

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import walkreach  # noqa: E402


def test_every_room_is_reachable_on_foot_from_the_front_door():
    """The furniture, the facade and the garden may not seal any room off:
    the four en-suite dress rooms and bathrooms were sealed before this test."""
    wanted = {(r["storey"], r["key"]) for r in walkreach.rooms}
    missing = wanted - walkreach.reached_rooms()
    assert not missing, sorted(missing)


def test_the_garden_terrace_lawn_bbq_and_gate_path_are_reachable():
    from shapely.geometry import Point
    for name in ("garden, garden terrace", "garden, lawn", "garden, bbq terrace", "garden, entrance path", "carport"):
        polys = [p for z, p in walkreach.zones if z["name"] == name]
        assert polys, name
        assert any(p.contains(Point(u, v)) for p in polys for u, v, _ in walkreach.reached_pts), name
