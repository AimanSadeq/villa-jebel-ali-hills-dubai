"""Facade proposal, brief/facade.yaml through src/model/facade.py (answer R3).

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model import facade  # noqa: E402

SPEC = facade.load()
HEIGHTS = yaml.safe_load((REPO_ROOT / "brief" / "massing.yaml").read_text(encoding="utf-8"))["heights"]


def test_everything_but_the_carport_piers_stays_inside_the_setback_line():
    """The carport already stands in the setback (D-044, TO VERIFY); nothing
    else of the facade may."""
    bx, _ = facade.boxes([], SPEC)
    assert set(facade.check(bx)) <= {"Carport pier, road north", "Carport pier, road south"}


def test_the_portal_and_the_frame_add_no_height():
    """Only the pergola (R1, R2, OI-28) rises above the parapet top; DDA FAQ
    Q29 may cap the height (OI-13)."""
    top = float(HEIGHTS["overall_m"])
    for e in SPEC["elements"]:
        assert e["z"][1] <= top + 1e-6, e["name"]


def test_the_pergola_is_open_and_over_the_garden_frame():
    """R1 B, R2 A: an open pergola above the living room, set back from the
    roof edge, inside the garden frame's span."""
    p = SPEC["pergola"]
    legs = [e for e in SPEC["elements"] if e["name"].startswith("Garden frame") and "leg" in e["name"]]
    assert p["v"][0] >= min(e["v"][0] for e in legs) and p["v"][1] <= max(e["v"][1] for e in legs)
    assert p["u"][1] < min(e["u"][1] for e in legs)
    bx, _ = facade.boxes([], SPEC)
    assert all(b.kind != "enclosure" for b in bx)


def test_a_window_on_the_porch_looks_out_of_the_porch():
    """The guest bedroom's window onto the porch faces south, although it is
    north of the house centre: the open porch is not a room."""
    inside = facade.inside_from_layouts()
    w = dict(name="Window, Guest Bedroom, En-suite, hot", u0=5.89, u1=7.69, v0=22.07, v1=22.13,
             z0=0.9, z1=2.7)
    assert facade.face_of(w, inside)[0] == "S"


def test_road_windows_get_surrounds_and_fins():
    w = dict(name="Window, Bedroom 2, En-suite, hot", u0=4.89, u1=4.95, v0=14.67, v1=16.47,
             z0=5.9, z1=7.7)
    bx, notes = facade.boxes([w], SPEC, facade.inside_from_layouts())
    kinds = [b.kind for b in bx if w["name"] in b.name]
    assert kinds.count("surround") == 4 and kinds.count("fin") >= 4 and not notes
