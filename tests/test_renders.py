"""The Blender render set-up, renders/render_villa.py (answer P9, D-057).

Blender itself is not needed here: the checks read the script's view table
and the model export it renders from.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "renders" / "render_villa.py"
DATA = json.loads((REPO_ROOT / "viewer" / "public" / "data" / "model.json").read_text(encoding="utf-8"))


def _views() -> dict:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "VIEWS" for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("VIEWS not found")


def test_the_views_of_the_brief_are_defined_with_sun_positions_that_exist():
    views = _views()
    assert set(views) == {"entrance", "foyer", "courtyard", "living", "master", "garden_sunset", "aerial"}
    for name, (pos, look, lens, sun_key, title) in views.items():
        assert sun_key in DATA["sun"], (name, sun_key)
        assert 14 <= lens <= 50 and len(pos) == 3 and len(look) == 3 and title


def test_interior_cameras_stand_inside_their_rooms_clear_of_furniture():
    views = _views()
    rooms = {r["key"]: r for r in DATA["rooms"] if r.get("rect")}
    for name, room in (("living", "living"), ("foyer", "entrance_foyer"), ("courtyard", "dining"),
                       ("master", "master_suite")):
        (u, v, z), *_ = views[name]
        r = rooms[room]
        assert r["rect"][0] < u < r["rect"][1] and r["rect"][2] < v < r["rect"][3], name
        for p in DATA["finishes"]["pieces"]:
            if p["room"] == r["key"]:
                inside = p["fp"][0] <= u <= p["fp"][1] and p["fp"][2] <= v <= p["fp"][3] and p["z"][0] <= z <= p["z"][1]
                assert not inside, (name, p["name"])


def test_the_sunset_sun_is_low_in_the_west():
    s = DATA["sun"]["sunset"]
    assert 0 < s["elevation_deg"] < 12 and 250 <= s["azimuth_deg"] <= 290
