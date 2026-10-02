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
                assert sw["name"] and "—" not in sw["name"]
    floors = [tuple(p["flooring"][k]["colour"] for k in ("public", "bedrooms")) for p in pals]
    assert len(set(floors)) == 3
