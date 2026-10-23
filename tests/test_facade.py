"""The facade of the redesign, brief/facade.yaml through src/model/facade.py
(D-060, S1: A, white minimalist after the owner's images).

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
LAY = yaml.safe_load((REPO_ROOT / "brief" / "layouts.yaml").read_text(encoding="utf-8"))


def test_everything_stays_inside_the_setback_line():
    """No facade element crosses the 3 m setback (OI-29 noted projections;
    the redesign keeps them all inside)."""
    bx, _ = facade.boxes([], SPEC)
    assert facade.check(bx) == []


def test_nothing_adds_height():
    """The entrance stone box and the eaves stop at the parapet top (DDA FAQ
    Q29 may cap the height, OI-13). No roof pergola in the redesign."""
    top = float(HEIGHTS["overall_m"])
    for e in SPEC["elements"]:
        assert e["z"][1] <= top + 1e-6, e["name"]
    assert "pergola" not in SPEC


def test_the_entrance_stone_box_frames_the_front_door():
    """The charcoal box's legs stand either side of the pivot door G01 and
    its glass above, with a canopy over the door."""
    g01 = next(d for d in LAY["doors"] if d["no"] == "G01")
    legs = [e for e in SPEC["elements"] if "Entrance stone box" in e["name"] and "leg" in e["name"]]
    assert len(legs) == 2 and all(e["material"] == "stone" for e in legs)
    lo, hi = g01["v"] - g01["width_m"] / 2, g01["v"] + g01["width_m"] / 2
    assert min(e["v"][1] for e in legs) <= lo and max(e["v"][0] for e in legs) >= hi
    canopy = next(e for e in SPEC["elements"] if e["name"] == "Entrance canopy")
    assert canopy["v"][0] <= lo and canopy["v"][1] >= hi and canopy["u"][0] >= 3.0


def test_the_materials_are_the_white_minimalist_set():
    """S1: A. White render, charcoal stone, timber soffits and fins."""
    m = SPEC["materials"]
    assert "white" in m["render"]["label"].lower()
    assert "charcoal" in m["stone"]["label"].lower()
    assert any(e["kind"] == "soffit" and e["material"] == "timber" for e in SPEC["elements"])


def test_the_garden_face_gets_deep_eaves_with_timber_soffits():
    """CLAUDE.md section 5: deep overhangs over the glazed faces."""
    eaves = [e for e in SPEC["elements"] if e["name"].startswith("East eave, roof") and e["kind"] == "canopy"]
    assert eaves and all(e["u"][1] - e["u"][0] >= 0.6 for e in eaves)
    soffits = [e for e in SPEC["elements"] if "East eave" in e["name"] and e["kind"] == "soffit"]
    assert soffits and all(e["material"] == "timber" for e in soffits)


def test_road_windows_get_surrounds_and_fins():
    w = dict(name="Window, Family Lounge, hot", u0=4.00, u1=4.06, v0=26.5, v1=28.3,
             z0=5.9, z1=7.7)
    bx, notes = facade.boxes([w], SPEC, facade.inside_from_layouts())
    kinds = [b.kind for b in bx if w["name"] in b.name]
    assert kinds.count("surround") == 4 and kinds.count("fin") >= 4 and not notes
