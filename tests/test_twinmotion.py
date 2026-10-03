"""The Twinmotion export, src/model/export_twinmotion.py (answer W1, D-059).

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

import csv
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model import export_twinmotion as tm  # noqa: E402

DATA = json.loads((REPO_ROOT / "viewer" / "public" / "data" / "model.json").read_text(encoding="utf-8"))


def test_every_furniture_piece_and_tree_has_a_library_kind():
    for p in DATA["finishes"]["pieces"]:
        assert any(p["name"].startswith(pre) for pre, _ in tm.LIBRARY_KIND), p["name"]
    for t in DATA["exterior"]["trees"]:
        assert t["species"] in tm.SPECIES_KIND, t["species"]


def test_the_six_views_name_sun_positions_that_exist():
    assert set(tm.VIEWS) == {"entrance", "living", "salon", "master", "garden_sunset", "aerial"}
    for name, (pos, look, lens, sun_key, title) in tm.VIEWS.items():
        assert sun_key in DATA["sun"], (name, sun_key)


def test_rotation_follows_the_render_builders_convention():
    """The CSV's rotation turns a piece whose back faces -y to its back side,
    anticlockwise seen from above, as renders/furniture_bl.py does."""
    import math
    sys.path.insert(0, str(REPO_ROOT / "renders"))
    try:
        import furniture_bl  # noqa: PLC0415
    except ImportError:          # bpy is not needed here; the table is a constant
        pytest.skip("furniture_bl imports bpy")
    for side, deg in tm.BACK_DEG.items():
        assert math.isclose(math.radians(deg), furniture_bl.BACK_ROT[side], abs_tol=1e-9), side


def test_the_export_writes_the_placements_and_cameras(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "OUT", tmp_path)
    tm.write_placements(DATA)
    tm.write_cameras(DATA)
    rows = list(csv.DictReader((tmp_path / "VJH-TM-001_placements.csv").open(encoding="utf-8")))
    assert len(rows) == len(DATA["finishes"]["pieces"]) + len(DATA["exterior"]["trees"])
    assert all(r["library_kind"] and r["rotation_deg"] in ("0.0", "90.0", "180.0", "-90.0") for r in rows)
    cams = list(csv.DictReader((tmp_path / "VJH-TM-001_cameras.csv").open(encoding="utf-8")))
    assert len(cams) == 6 and all(float(c["sun_elevation_deg"]) > 0 for c in cams)
