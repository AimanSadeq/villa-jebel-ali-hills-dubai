"""Checks on the courtyard villa's plan in brief/layouts.yaml (D-060).

These test the geometry a builder would care about and the owner's handover
acceptance tests: every room placed once, nothing overlaps, the first floor
enclosed over the guest suite and the powder room, exactly three bedrooms
upstairs, the courtyard open to the sky, the foyer double height, no gates,
the stair straight, and the plan inside the GFA cap and behind the setbacks.
"""

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import pytest
import yaml
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

LAYOUTS = REPO_ROOT / "brief" / "layouts.yaml"
PROGRAM = REPO_ROOT / "brief" / "program.yaml"
GARDEN = REPO_ROOT / "brief" / "garden.yaml"

lay = yaml.safe_load(LAYOUTS.read_text(encoding="utf-8"))
prog = yaml.safe_load(PROGRAM.read_text(encoding="utf-8"))
garden = yaml.safe_load(GARDEN.read_text(encoding="utf-8"))


def _box(r):
    return box(r["u"][0], r["v"][0], r["u"][1], r["v"][1])


def _room(floor, key):
    return next(r for r in lay["floors"][floor]["rooms"] + lay["floors"][floor]["circulation"]
                if r["key"] == key)


PLACED = {r["key"] for f in ("ground", "first") for r in lay["floors"][f]["rooms"]}


def test_every_program_room_is_placed_exactly_once():
    """Every room of brief/program.yaml and every ancillary room is placed
    once; the carport is a roofed plate outside the house, not a room."""
    placed = [r["key"] for f in ("ground", "first") for r in lay["floors"][f]["rooms"]]
    wanted = [r["key"] for f in ("ground", "first") for r in prog[f]
              if not r.get("outside_the_house")]
    wanted += [a["key"] for a in prog.get("ancillary", []) or []]
    assert sorted(placed) == sorted(wanted)


def test_the_removed_rooms_are_on_record_and_not_placed():
    """The handover: no fourth bedroom, no linen room, no ground floor office
    (S5), no pool (D-041). Each removal names its decision."""
    removed = {r["key"]: r for r in prog.get("removed", [])}
    for key in ("bedroom_4", "linen_storage", "home_office", "pool", "drivers_room", "sunroom"):
        assert key in removed and removed[key]["decision"], key
        assert key not in PLACED, key


def test_exactly_three_bedrooms_upstairs_each_with_its_own_bathroom():
    """The handover's acceptance test: master plus two, three en-suites."""
    first = {r["key"] for r in lay["floors"]["first"]["rooms"]}
    bedrooms = {k for k in first if (k.startswith("bedroom_") or k == "master_suite")
                and not any(x in k for x in ("dress", "toilet"))}
    assert bedrooms == {"master_suite", "bedroom_2", "bedroom_3"}
    assert {"master_toilet", "bedroom_2_toilet", "bedroom_3_toilet"} <= first
    serves = {a["key"]: a["serves"] for a in prog["ancillary"]}
    assert serves["master_toilet"] == "master_suite"
    assert serves["bedroom_2_toilet"] == "bedroom_2" and serves["bedroom_3_toilet"] == "bedroom_3"


def test_the_master_has_an_integrated_walk_in_and_a_shower_bathroom():
    """Handover: the walk-in closet opens from the bedroom and the bathroom
    from the closet; shower only, no bathtub."""
    pairs = {frozenset((d["a"], d["b"])) for d in lay["doors"] if d["kind"] != "fixed"}
    assert frozenset(("master_suite", "master_dress")) in pairs
    assert frozenset(("master_dress", "master_toilet")) in pairs
    bath = next(a for a in prog["ancillary"] if a["key"] == "master_toilet")
    assert "shower" in bath["name"].lower()
    assert "bathtub" not in " ".join(prog["interiors"]["master_suite"]["bathroom"]["fittings"])


def test_the_first_floor_is_enclosed_over_the_guest_suite_and_the_powder_room():
    """The defect the owner rejected in the other assistant's images: an open
    planted roof over the guest suite. Here the first floor rooms cover the
    guest bedroom, its bathroom and the powder room entirely, and no void,
    terrace or balcony lies over them."""
    g = {r["key"]: _box(r) for r in lay["floors"]["ground"]["rooms"]}
    target = unary_union([g["guest_bedroom"], g["guest_toilet"], g["guest_powder"]])
    f = lay["floors"]["first"]
    enclosed = unary_union([_box(r) for r in f["rooms"] + f["circulation"]])
    enclosed = enclosed.buffer(0.08, join_style=2).buffer(-0.08, join_style=2)   # close the partitions
    assert target.intersection(enclosed).area / target.area > 0.999
    opens = unary_union([_box(r) for r in f["voids"] + f["outdoor"]])
    assert opens.intersection(target).area < 1e-6
    over = {r["key"] for r in f["rooms"] if _box(r).intersection(target).area > 1.0}
    assert "bedroom_2" in over


def test_the_courtyard_is_open_to_the_sky_and_the_foyer_double_height():
    """S2: a central court of about 22 m2; the handover: keep only the
    intentional voids, the courtyard and the double height foyer."""
    assert lay["open_to_sky"] == ["courtyard"]
    court = _box(_room("ground", "courtyard"))
    assert 20.0 <= court.area <= 25.0
    void_c = next(v for v in lay["floors"]["first"]["voids"] if v["key"] == "void_over_courtyard")
    assert _box(void_c).equals(court)
    assert lay["double_height"] == ["entrance_foyer"]
    void_f = next(v for v in lay["floors"]["first"]["voids"] if v["key"] == "void_over_foyer")
    assert _box(void_f).contains(_box(_room("ground", "entrance_foyer")).buffer(-0.01))
    assert {v["key"] for v in lay["floors"]["first"]["voids"]} == {"void_over_foyer", "void_over_courtyard"}


def test_no_gates_and_an_open_two_car_carport():
    """Handover: no vehicle gate, no pedestrian gate; an open carport for a
    large SUV and a standard car. Two bays of 2.5 x 5.5 m (DDA FAQs Building
    Q5) must fit."""
    assert garden["wall"]["gates"] == [] and "road" in garden["wall"]["open_sides"]
    c = lay["plates"]["carport"]
    w, d = sorted((c["u"][1] - c["u"][0], c["v"][1] - c["v"][0]))
    assert w >= 5.5 and d >= 2 * 2.5
    assert "garage" not in PLACED


def test_the_family_living_opens_to_the_garden():
    """Handover: direct shaded door access from the family living to the garden."""
    d = next(d for d in lay["doors"] if d["a"] == "living" and d["b"] == "outside")
    assert d["kind"] == "sliding" and d["u"] > _room("ground", "living")["u"][1]


@pytest.mark.parametrize("floor", ["ground", "first"])
def test_no_two_rooms_overlap(floor):
    f = lay["floors"][floor]
    rooms = f["rooms"] + f["circulation"] + f.get("voids", []) + f.get("outdoor", [])
    for a, b in combinations(rooms, 2):
        assert _box(a).intersection(_box(b)).area < 1e-6, (
            f"{a['key']} and {b['key']} overlap on the {floor} floor")


def test_the_house_stays_behind_the_setback_lines():
    """Both outlines, the terrace and the open carport inside the 3 m envelope."""
    from model.massing import site_to_grid
    from model.site import buildable_envelope

    env = site_to_grid(buildable_envelope()).buffer(0.01)
    assert env.contains(Polygon(lay["outlines"]["ground"]))
    assert env.contains(Polygon(lay["outlines"]["first"]))
    assert env.contains(_box(lay["plates"]["carport"]))
    for r in lay["floors"]["first"]["outdoor"]:
        assert env.contains(_box(r)), r["key"]


def test_the_stair_is_straight_in_the_hall_and_the_lift_stacks():
    """Handover: a straight floating statement stair. Its lane lies in the
    hall along the courtyard; the lift shafts coincide."""
    s = lay["stair"]
    assert s["kind"] == "straight"
    hall = _box(_room("ground", s["hall"]))
    lane = box(hall.bounds[0], s["v"][0], hall.bounds[2], s["v"][1])
    assert hall.contains(lane.buffer(-0.001))
    lg, lf = _box(_room("ground", "lift")), _box(_room("first", "lift_first"))
    assert lg.intersection(lf).area >= 0.9 * min(lg.area, lf.area)


# Circulation narrower than 1.80 m (D-026, DDA FAQs Building Q12, OI-21), each
# a short vestibule or a service passage, listed so a new narrow corridor fails.
KNOWN_NARROW = {
    "service_corridor": "1.50 m service passage behind the carport, OI-26",
    "salon_lobby": "1.40 m vestibule between the hall and the salon",
    "guest_lobby": "1.50 m vestibule between the hall and the guest suite",
}


def test_circulation_is_the_dda_width_or_a_known_exception():
    for floor in ("ground", "first"):
        for c in lay["floors"][floor]["circulation"]:
            width = min(c["u"][1] - c["u"][0], c["v"][1] - c["v"][0])
            if width < lay["meta"]["corridor_m"] - 1e-3:
                assert c["key"] in KNOWN_NARROW, (
                    f"{c['key']} on the {floor} floor is {width:.2f} m wide and not a known exception")


def test_the_measured_plan_fits_the_cap_and_sits_near_the_handover_range():
    """The hard limit and the handover's target of about 450 to 500 m2
    enclosed, optimised rather than filled. The plan lands within a few
    square metres of the top of that range; the courtyard is not counted."""
    m = lay["gfa_measured"]
    assert m["total"] <= m["cap"]
    assert m["margin"] >= 100.0
    assert 450.0 <= m["total"] <= 510.0, m["total"]
    assert m["first_floor_voids"] > 45.0 and m["courtyard_open_to_sky_m2"] > 20.0


def test_the_door_schedule_is_complete_and_numbered_once():
    nos = [d["no"] for d in lay["doors"]]
    assert len(nos) == len(set(nos)) == 33
    placed = {r["key"] for f in ("ground", "first")
              for r in lay["floors"][f]["rooms"] + lay["floors"][f]["circulation"]}
    voids = {v["key"] for v in lay["floors"]["first"]["voids"]}
    for d in lay["doors"]:
        assert d["source"], d["no"]
        assert d["a"] in placed, d["no"]
        assert d["b"] in placed or d["b"] == "outside" or (d["kind"] == "fixed" and d["b"] in voids), d["no"]


@pytest.mark.parametrize("bedroom", ["guest_bedroom", "master_suite", "bedroom_2", "bedroom_3"])
def test_every_bedroom_has_an_entry_door_from_a_hall(bedroom):
    """Each bedroom opens off a hall or its own lobby or dressing room."""
    halls = {"hall", "gallery", "gallery_west", "north_lobby", "guest_lobby", "bedroom_3_dress"}
    assert any(d["kind"] not in ("open", "fixed") and {d["a"], d["b"]} & halls and bedroom in (d["a"], d["b"])
               for d in lay["doors"]), f"{bedroom} has no door from a hall"


def test_every_room_can_be_reached_and_the_generator_agrees():
    """The generator's own checks: walls of the standard thickness, nothing
    outside the envelope, every room reached on foot, the overlap test."""
    from model import layout_court
    assert layout_court.check(layout_court.resolve_doors()) == []


def test_the_formal_room_is_the_salon_never_majlis():
    """D-047 and S3: salon everywhere."""
    names = [r["key"] + " " + r["name"] for f in ("ground", "first") for r in prog[f]]
    names += [a["key"] + " " + a["name"] for a in prog["ancillary"]]
    assert not any("majlis" in n.lower() for n in names)
    assert "majlis" not in LAYOUTS.read_text(encoding="utf-8").lower()
    assert "salon" in PLACED


def test_the_arabic_kitchen_looks_into_the_courtyard():
    """OI-15: the closed prep kitchen gets light and air from the open court."""
    assert any(d["a"] == "arabic_kitchen" and d["b"] == "courtyard" and d["kind"] == "fixed"
               for d in lay["doors"])


def test_there_is_no_pool():
    """D-041: the owner does not want a pool; the handover agrees."""
    assert not lay.get("pool")
    assert any(r["key"] == "pool" for r in prog.get("removed", []))
