"""Twinmotion export of Villa 5130272 (answer W1, D-059).

Writes, from the built model (run src/model/build_model.py first):
  * output/twinmotion/VJH-TM-001_Villa_5130272_<palette>.ifc, one per palette:
    the architecture, the facade, the garden surfaces and walls, and the
    palette's interior finishes as IfcCovering surfaces, every element with a
    material named for what it is (Twinmotion groups surfaces by material
    name, so each finish is replaced from its library in one click). The box
    furniture, the sanitary ware and the procedural trees are left out:
    Twinmotion's library supplies real ones, placed from the lists below.
  * output/twinmotion/VJH-TM-001_placements.csv: every furniture piece and
    tree with its position (x, y, z in metres, the IFC's own frame), size,
    rotation and the library kind to use.
  * output/twinmotion/VJH-TM-001_cameras.csv: the six views of the brief as
    camera position, target and lens, and the sun study's sun positions.
  * docs/twinmotion-guide.md tells the owner what to do with them.

Run: python src/model/export_twinmotion.py            (all three palettes)
     python src/model/export_twinmotion.py --palette 1

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.material
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.style
import ifcopenshell.api.geometry
import ifcopenshell.util.element
import yaml
from ifcopenshell.util.shape_builder import ShapeBuilder

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

IFC_IN = REPO_ROOT / "output" / "ifc" / "VJH-ARCH-001_Villa_5130272.ifc"
MODEL_JSON = REPO_ROOT / "viewer" / "public" / "data" / "model.json"
PALETTES = REPO_ROOT / "brief" / "palettes.yaml"
OUT = REPO_ROOT / "output" / "twinmotion"
STAMP = "CONCEPT DESIGN, NOT FOR CONSTRUCTION"

# Elements Twinmotion's library replaces: left out of the export.
DROP_CLASSES = {"IfcFurniture", "IfcSanitaryTerminal"}
DROP_OBJECT_TYPES = ("Landscape: palm", "Landscape: tree", "Landscape: hedge")

# Library kinds for the placement list, by the furniture piece's name prefix.
LIBRARY_KIND = [
    ("Bed, 1.93", "Bed, king"), ("Bed, 1.60", "Bed, queen"), ("Bed, 0.90", "Bed, single"),
    ("Sofa", "Sofa, 3 seats"), ("Salon sofa", "Sofa, 3 seats"), ("Sitting sofa", "Sofa, 2 seats"),
    ("Armchair", "Armchair"), ("Dining chair", "Dining chair"), ("BBQ chair", "Outdoor chair"),
    ("Desk and chair", "Desk with office chair"), ("TV unit", "TV cabinet with television"),
    ("Dining table", "Dining table"), ("BBQ table", "Outdoor dining table"),
    ("Coffee table", "Coffee table"), ("Salon table", "Coffee table, large"), ("Sitting table", "Coffee table, small"),
    ("Wardrobes", "Wardrobe run"), ("Wardrobe", "Wardrobe"), ("Console and mirror", "Console table with mirror"),
    ("Console", "Console table"), ("Bookshelves", "Bookshelf"), ("Pantry shelves", "Shelving unit"),
    ("Dressing island", "Dressing island"), ("Kitchen run", "Kitchen base and wall units"),
    ("Kitchen counter", "Kitchen base units"), ("Island", "Kitchen island"), ("Coffee station", "Kitchenette units"),
    ("Washer and dryer", "Washing machine and dryer"), ("Vanity, 2", "Double basin vanity with mirror"),
    ("Vanity", "Basin vanity with mirror"), ("WC", "Wall hung WC"), ("Shower", "Walk in shower with glass screen"),
    ("Bathtub", "Freestanding bathtub"), ("Rug", "Rug"),
]
SPECIES_KIND = {"date_palm": "Palm, Phoenix dactylifera (date palm)", "ghaf": "Tree, Prosopis (ghaf) or acacia",
                "sidr": "Tree, Ziziphus (sidr) or similar broadleaf", "frangipani": "Tree, Plumeria (frangipani)"}
BACK_DEG = {"S": 0.0, "W": -90.0, "N": 180.0, "E": 90.0}   # rotation about z (anticlockwise seen from above) that turns a piece whose back faces -y to face that side; the same convention as renders/furniture_bl.py

VIEWS = {
    "entrance": ((-11.0, 28.5, 1.7), (6.0, 20.3, 4.2), 30, "spring_15h", "Entrance from the road"),
    "living": ((15.6, 17.3, 1.55), (19.5, 22.6, 2.6), 22, "morning_9h", "Double height living room"),
    "salon": ((16.6, 24.6, 1.5), (11.0, 28.4, 1.5), 24, "spring_15h", "Salon"),
    "master": ((15.6, 7.0, 6.5), (19.8, 11.6, 6.3), 24, "morning_9h", "Master suite"),
    "garden_sunset": ((26.9, 27.2, 1.5), (21.6, 15.0, 3.8), 22, "sunset", "Garden at sunset"),
    "aerial": ((-14.0, -10.0, 26.0), (13.0, 18.0, 3.0), 35, "spring_15h", "Aerial view"),
}


def hexrgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def finish_label(slot: str, sw: dict) -> str:
    grp, key = slot.split(".")
    where = {"flooring": "Floor", "walls": "Wall", "accents": "Accent", "fixtures": "Fixture"}[grp]
    return f"{where} {key}: {sw['name']}"


def add_finishes(f, data: dict, pal_index: int, body, storeys) -> int:
    """The palette's finish surfaces as IfcCovering, grouped by slot."""
    fin = data["finishes"]
    pal = fin["palettes"][pal_index]
    b = ShapeBuilder(f)
    mats: dict[str, object] = {}
    n = 0
    by_slot: dict[tuple, list] = {}
    for q in fin["quads"]:
        by_slot.setdefault((q["slot"], q["storey"]), []).append(q)
    for (slot, storey), quads in by_slot.items():
        grp, key = slot.split(".")
        sw = pal[grp][key]
        label = finish_label(slot, sw)
        if label not in mats:
            m = ifcopenshell.api.material.add_material(f, name=label, category="finish")
            st = ifcopenshell.api.style.add_style(f, name=label)
            r, g, bl = hexrgb(sw["colour"])
            ifcopenshell.api.style.add_surface_style(
                f, style=st, ifc_class="IfcSurfaceStyleShading",
                attributes={"SurfaceColour": {"Name": None, "Red": r, "Green": g, "Blue": bl}, "Transparency": 0.0})
            mats[label] = (m, st)
        m, st = mats[label]
        items = []
        for q in quads:
            pts = q["p"]
            # A thin plate 4 mm thick, offset into the room by the quad's normal.
            (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = pts[0], pts[1], pts[2]
            ax, ay, az = x1 - x0, y1 - y0, z1 - z0
            bx, by, bz = x2 - x0, y2 - y0, z2 - z0
            nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
            ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            nx, ny, nz = nx / ln, ny / ln, nz / ln
            t = 0.004
            face = [tuple(p) for p in pts]
            back = [(p[0] - nx * t, p[1] - ny * t, p[2] - nz * t) for p in pts]
            verts = face + back
            faces = [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]]
            items.append(b.mesh(verts, faces))
        kind = "FLOORING" if grp == "flooring" else "CEILING" if key == "ceiling" else "CLADDING"
        e = ifcopenshell.api.root.create_entity(f, ifc_class="IfcCovering", name=f"Finish, {label}", predefined_type=kind)
        e.ObjectType = f"Finish: {slot}"
        e.Description = f"Interior palette {pal['name']}, brief/palettes.yaml. {STAMP}"
        ifcopenshell.api.spatial.assign_container(f, products=[e], relating_structure=storeys[storey])
        ifcopenshell.api.geometry.edit_object_placement(f, product=e)
        rep = b.get_representation(body, items)
        ifcopenshell.api.geometry.assign_representation(f, product=e, representation=rep)
        ifcopenshell.api.style.assign_representation_styles(f, shape_representation=rep, styles=[st])
        ifcopenshell.api.material.assign_material(f, products=[e], material=m)
        n += 1
    return n


def export_palette(data: dict, pal_index: int, pal_name: str) -> Path:
    f = ifcopenshell.open(str(IFC_IN))
    # Drop what the library replaces.
    dropped = 0
    for e in list(f.by_type("IfcElement")):
        ot = getattr(e, "ObjectType", None) or ""
        if e.is_a() in DROP_CLASSES or ot.startswith(DROP_OBJECT_TYPES):
            ifcopenshell.api.root.remove_product(f, product=e)
            dropped += 1
    for sp in list(f.by_type("IfcSpace")):            # room volumes would read as solids
        ifcopenshell.api.root.remove_product(f, product=sp)
    body = next(c for c in f.by_type("IfcGeometricRepresentationSubContext") if c.ContextIdentifier == "Body")
    storeys = {("ground" if s.Name == "Ground Floor" else "first" if s.Name == "First Floor" else "roof"): s
               for s in f.by_type("IfcBuildingStorey")}
    n = add_finishes(f, data, pal_index, body, storeys)
    proj = f.by_type("IfcProject")[0]
    proj.Description = f"{STAMP}. Twinmotion export, interior palette {pal_index + 1} {pal_name}."
    slug = pal_name.lower().replace(",", "").replace(" ", "_")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"VJH-TM-001_Villa_5130272_palette{pal_index + 1}_{slug}.ifc"
    f.write(str(path))
    print(f"IFC  {_rel(path)}   finishes {n} coverings, library items left out {dropped}")
    return path


def write_placements(data: dict) -> Path:
    path = OUT / "VJH-TM-001_placements.csv"
    rows = []
    for p in data["finishes"]["pieces"]:
        kind = next((k for pre, k in LIBRARY_KIND if p["name"].startswith(pre)), p["name"])
        u0, u1, v0, v1 = p["fp"]
        back = p.get("back") or p.get("side") or "S"
        w, d = (u1 - u0, v1 - v0) if back in ("S", "N") else (v1 - v0, u1 - u0)
        rows.append({"item": p["name"], "library_kind": kind, "room": p["room"], "storey": p["storey"],
                     "x_m": round((u0 + u1) / 2, 2), "y_m": round((v0 + v1) / 2, 2), "z_m": round(p["z"][0], 2),
                     "width_m": round(w, 2), "depth_m": round(d, 2), "height_m": round(p["z"][1] - p["z"][0], 2),
                     "rotation_deg": BACK_DEG[back], "back_toward": back})
    g = data["exterior"]
    for t in g["trees"]:
        rows.append({"item": t["species"], "library_kind": SPECIES_KIND.get(t["species"], t["species"]), "room": "garden",
                     "storey": "site", "x_m": t["u"], "y_m": t["v"], "z_m": g["ground_z"], "width_m": t["crown_m"],
                     "depth_m": t["crown_m"], "height_m": t["height_m"], "rotation_deg": 0.0, "back_toward": ""})
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"CSV  {_rel(path)}   {len(rows)} placements")
    return path


def write_cameras(data: dict) -> Path:
    path = OUT / "VJH-TM-001_cameras.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["view", "title", "camera_x", "camera_y", "camera_z", "target_x", "target_y", "target_z",
                    "lens_mm", "sun", "sun_when", "sun_azimuth_deg", "sun_elevation_deg"])
        for key, (pos, look, lens, sun_key, title) in VIEWS.items():
            s = data["sun"][sun_key]
            w.writerow([key, title, *pos, *look, lens, sun_key, s["when"], s["azimuth_deg"], s["elevation_deg"]])
    print(f"CSV  {_rel(path)}")
    return path


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Twinmotion export of Villa 5130272.")
    ap.add_argument("--palette", type=int, help="1, 2 or 3; default all three.")
    args = ap.parse_args()
    if not IFC_IN.exists():
        print(f"Missing {IFC_IN}: run src/model/build_model.py first.")
        return 1
    data = json.loads(MODEL_JSON.read_text(encoding="utf-8"))
    pals = yaml.safe_load(PALETTES.read_text(encoding="utf-8"))["palettes"]
    which = [args.palette - 1] if args.palette else range(len(pals))
    for i in which:
        export_palette(data, i, pals[i]["name"])
    write_placements(data)
    write_cameras(data)
    shutil.copy(REPO_ROOT / "docs" / "twinmotion-guide.md", OUT / "README.md")
    print(STAMP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
