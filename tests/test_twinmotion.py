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


def _read_glb(path):
    import struct
    b = path.read_bytes()
    magic, version, length = struct.unpack("<III", b[:12])
    assert (magic, version, length) == (0x46546C67, 2, len(b))
    jlen, jtype = struct.unpack("<II", b[12:20])
    assert jtype == 0x4E4F534A and jlen % 4 == 0
    js = json.loads(b[20:20 + jlen])
    blen, btype = struct.unpack("<II", b[20 + jlen:28 + jlen])
    assert btype == 0x004E4942 and blen == js["buffers"][0]["byteLength"] == len(b) - 28 - jlen
    return js, b[28 + jlen:]


def test_the_glb_is_valid_glTF_with_y_up_and_named_materials(tmp_path):
    """Twinmotion 2026 does not list IFC on import (owner, 2026-10-05): the
    export writes glTF. A triangle at height 3 m on the model's +y side must
    come out at glTF y 3 and negative z (y up, model +y toward glTF -z)."""
    import numpy as np
    tri = np.array([[[0, 5, 3], [1, 5, 3], [0, 6, 3]]], dtype=np.float32)
    groups = {"Glazing": {"tris": tri, "rgb": (0.5, 0.7, 0.8), "alpha": 0.45},
              "Wall main: Warm white paint, matt": {"tris": tri + 1, "rgb": (0.9, 0.9, 0.9), "alpha": 1.0}}
    path = tmp_path / "t.glb"
    assert tm.write_glb(groups, path) == 2
    js, blob = _read_glb(path)
    assert [m["name"] for m in js["materials"]] == sorted(groups)
    glass = js["materials"][0]
    assert glass["alphaMode"] == "BLEND" and glass["pbrMetallicRoughness"]["baseColorFactor"][3] == 0.45
    acc = js["accessors"][js["meshes"][0]["primitives"][0]["attributes"]["POSITION"]]
    assert acc["min"] == [0.0, 3.0, -6.0] and acc["max"] == [1.0, 3.0, -5.0]
    nacc = js["accessors"][js["meshes"][0]["primitives"][0]["attributes"]["NORMAL"]]
    view = js["bufferViews"][nacc["bufferView"]]
    n = np.frombuffer(blob[view["byteOffset"]:view["byteOffset"] + view["byteLength"]], dtype=np.float32)
    assert np.allclose(n.reshape(-1, 3)[0], [0, 1, 0])            # a floor faces up
    obj = tmp_path / "t.obj"
    assert tm.write_obj(groups, obj) == 2
    assert "usemtl Wall_main__Warm_white_paint__matt" in obj.read_text(encoding="utf-8")
    assert "d 0.450" in obj.with_suffix(".mtl").read_text(encoding="utf-8")


@pytest.mark.skipif(not tm.IFC_IN.exists(), reason="run src/model/build_model.py first")
def test_the_model_tessellates_with_every_surface_named():
    groups = tm.tessellate(tm.IFC_IN)
    names = set(groups)
    assert {"Beige render", "Warm split face stone", "Glazing", "Lawn"} <= names
    assert not any(n.startswith("IfcSurfaceStyle") or n in ("DefaultMaterial", "Unnamed") for n in names), names
    assert groups["Glazing"]["alpha"] < 1.0
