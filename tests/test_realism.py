"""Real materials, sky and sun for the walkthrough (answer P7, D-056).

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

import json
import math
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = yaml.safe_load((REPO_ROOT / "assets" / "manifest.yaml").read_text(encoding="utf-8"))
PALETTES = yaml.safe_load((REPO_ROOT / "brief" / "palettes.yaml").read_text(encoding="utf-8"))
DATA = json.loads((REPO_ROOT / "viewer" / "public" / "data" / "model.json").read_text(encoding="utf-8"))


def test_every_palette_texture_key_is_in_the_manifest():
    keys = set(MANIFEST["textures"])
    for pal in PALETTES["palettes"]:
        for grp in ("flooring", "walls", "accents", "fixtures"):
            for slot, sw in pal[grp].items():
                if "texture" in sw:
                    assert sw["texture"] in keys, (pal["key"], grp, slot, sw["texture"])
    # The floors and walls, what the eye sees most, all carry a photograph.
    for pal in PALETTES["palettes"]:
        for slot in ("public", "bedrooms", "wet"):
            assert "texture" in pal["flooring"][slot], (pal["key"], slot)
        for slot in ("main", "feature"):
            assert "texture" in pal["walls"][slot], (pal["key"], slot)


def test_the_manifest_assets_are_cc0_from_poly_haven_with_a_search_fallback():
    assert "CC0" in MANIFEST["meta"]["source"]
    for grp in ("hdri", "textures", "models"):
        for key, spec in MANIFEST[grp].items():
            assert spec.get("prefer") and spec["search"]["type"], (grp, key)
            if grp == "textures":
                assert 0.3 <= float(spec["scale_m"]) <= 5.0, key


def test_the_sun_comes_from_the_sun_study_location():
    """Spring afternoon: the sun is in the west-south-west, well above the horizon."""
    s = DATA["sun"]["spring_15h"]
    assert 220 <= s["azimuth_deg"] <= 260 and 35 <= s["elevation_deg"] <= 55
    d = s["dir_uvz"]
    assert abs(math.hypot(*d) - 1) < 0.01 and d[2] > 0.5


def test_the_exterior_export_carries_the_facade_and_the_garden():
    e = DATA["exterior"]
    assert {f["material"] for f in e["facade"]} >= {"stone", "timber"}
    kinds = {g["kind"] for g in e["garden"]}
    assert {"lawn", "bed", "paving", "path"} <= kinds
    assert len(e["trees"]) >= 10 and all(t["kind"] in ("palm", "tree") for t in e["trees"])
    for g in e["garden"]:
        for rings in g["rings"]:
            assert len(rings[0]) >= 3
