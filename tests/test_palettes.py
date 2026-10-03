"""Interior palettes, brief/palettes.yaml (CLAUDE.md section 5, answer P1).

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = yaml.safe_load((REPO_ROOT / "brief" / "palettes.yaml").read_text(encoding="utf-8"))
SLOTS = {"flooring": {"public", "kitchen", "bedrooms", "wet", "service"},
         "walls": {"main", "feature", "wet", "ceiling"},
         "accents": {"joinery", "worktop", "textile", "highlight"},
         "fixtures": {"metal", "sanitary", "lighting"}}


def test_three_distinct_palettes_fill_every_slot():
    pals = SPEC["palettes"]
    assert len(pals) == SPEC["meta"]["count"] == 3
    assert len({p["name"] for p in pals}) == 3
    for p in pals:
        for grp, slots in SLOTS.items():
            assert set(p[grp]) == slots, (p["key"], grp)
            for s in slots:
                sw = p[grp][s]
                assert re.fullmatch(r"#[0-9a-f]{6}", sw["colour"]) and 0 <= sw["roughness"] <= 1
                assert sw["name"] and "\u2014" not in sw["name"]
    floors = [tuple(p["flooring"][k]["colour"] for k in ("public", "bedrooms")) for p in pals]
    assert len(set(floors)) == 3


def test_the_walkthrough_finishes_use_the_palettes():
    """P4, D-052: the model build exports floor, wall and ceiling finishes per
    room; every slot exists in every palette; the feature walls are placed."""
    import json
    data = json.loads((REPO_ROOT / "viewer" / "public" / "data" / "model.json").read_text(encoding="utf-8"))
    fin = data["finishes"]
    assert len(fin["palettes"]) == 3 and len(fin["quads"]) > 100
    for q in fin["quads"]:
        grp, key = q["slot"].split(".")
        assert len(q["p"]) == 4
        for p in fin["palettes"]:
            assert key in p[grp], (q["slot"], p["key"])
    feature = {q["room"] for q in fin["quads"] if q["slot"] == "walls.feature"}
    assert feature == {f["room"] for f in SPEC["feature_walls"]}
    floored = {q["room"] for q in fin["quads"] if q["slot"].startswith("flooring.")}
    assert {"living", "salon", "master_suite", "family_living", "master_toilet"} <= floored


def test_palette_1_is_sand_and_oak_again():
    """D-053: the owner restored Sand and Oak as palette 1, the default."""
    assert SPEC["palettes"][0]["name"] == "Sand and Oak"


def test_the_rooms_are_furnished():
    """P5, D-054: furniture in the walkthrough, coloured by palette slot."""
    import json
    data = json.loads((REPO_ROOT / "viewer" / "public" / "data" / "model.json").read_text(encoding="utf-8"))
    boxes = data["finishes"]["boxes"]
    assert len(boxes) > 150
    slots = {b["slot"] for b in boxes}
    assert {"accents.joinery", "accents.textile", "fixtures.sanitary"} <= slots
    for b in boxes:
        u0, u1, v0, v1, z0, z1 = b["b"]
        assert u1 > u0 and v1 > v0 and z1 > z0
