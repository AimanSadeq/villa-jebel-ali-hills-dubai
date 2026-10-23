"""Twinmotion export of Villa 5130272 (answer W1, D-059).

Writes, from the built model (run src/model/build_model.py first):
  * output/twinmotion/VJH-TM-001_Villa_5130272_<palette>.ifc, one per palette:
    the architecture, the facade, the garden surfaces and walls, and the
    palette's interior finishes as IfcCovering surfaces, every element with a
    material named for what it is (Twinmotion groups surfaces by material
    name, so each finish is replaced from its library in one click). The box
    furniture, the sanitary ware and the procedural trees are left out:
    Twinmotion's library supplies real ones, placed from the lists below.
  * the same model per palette as .glb (binary glTF 2.0) and .obj with .mtl,
    y up, metres, one mesh per material: Twinmotion 2026 does not list IFC in
    its import dialog (owner, 2026-10-05), these are the files to import.
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
                "sidr": "Tree, Ziziphus (sidr) or similar broadleaf", "frangipani": "Tree, Plumeria (frangipani)",
                "olive": "Tree, Olea europaea (olive), ornamental"}
BACK_DEG = {"S": 0.0, "W": -90.0, "N": 180.0, "E": 90.0}   # rotation about z (anticlockwise seen from above) that turns a piece whose back faces -y to face that side; the same convention as renders/furniture_bl.py

VIEWS = {
    # name: (camera position u, v, z; look-at u, v, z; lens mm; sun key; title)
    "entrance": ((-13.0, 1.5, 1.7), (9.5, 18.5, 4.5), 26, "spring_15h", "Entrance and carport from the road"),
    "foyer": ((5.0, 16.0, 1.6), (9.5, 20.5, 3.2), 20, "morning_9h", "Double height foyer and the floating stair"),
    "courtyard": ((18.3, 16.3, 1.5), (9.5, 18.8, 2.4), 18, "spring_15h", "Courtyard from the dining"),
    "living": ((18.2, 29.6, 1.5), (14.2, 23.8, 1.5), 20, "morning_9h", "Family living and the garden glass"),
    "master": ((18.3, 15.7, 6.4), (14.2, 19.4, 6.0), 20, "morning_9h", "Master bedroom, the courtyard window"),
    "garden_sunset": ((27.5, 29.5, 1.6), (17.0, 18.5, 3.5), 22, "sunset", "Garden at sunset"),
    "aerial": ((-12.0, -8.0, 24.0), (13.0, 19.0, 3.0), 35, "spring_15h", "Aerial view"),
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


def _style_name(f, geom_name: str) -> str | None:
    """IfcOpenShell names a tessellated material after its style item
    ("IfcSurfaceStyleShading-76"); return the IfcSurfaceStyle's own name."""
    tail = geom_name.rsplit("-", 1)[-1]
    if not tail.isdigit():
        return None
    try:
        ent = f.by_id(int(tail))
    except RuntimeError:
        return None
    if ent.is_a("IfcSurfaceStyle"):
        return ent.Name
    for inv in f.get_inverse(ent):
        if inv.is_a("IfcSurfaceStyle") and inv.Name:
            return inv.Name
    return None


def tessellate(ifc_path: Path) -> dict[str, dict]:
    """Every visible element of the IFC as triangles in world coordinates,
    grouped by material name: {name: {"tris": (n, 3, 3) array, "rgb", "alpha"}}.
    Openings and room volumes carry no visible surface and are skipped."""
    import multiprocessing

    import ifcopenshell.geom
    import numpy as np

    f = ifcopenshell.open(str(ifc_path))
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)
    it = ifcopenshell.geom.iterator(s, f, max(1, multiprocessing.cpu_count()),
                                    exclude=("IfcOpeningElement", "IfcSpace"))
    groups: dict[str, dict] = {}
    if not it.initialize():
        return groups
    while True:
        sh = it.get()
        g = sh.geometry
        v = np.asarray(g.verts, dtype=np.float64).reshape(-1, 3)
        tri = np.asarray(g.faces, dtype=np.int64).reshape(-1, 3)
        mids = np.asarray(g.material_ids, dtype=np.int64)
        elem_mat = None
        for k, m in enumerate(g.materials):
            name = _style_name(f, m.name)
            if name is None:                       # no style: the element's IfcMaterial
                if elem_mat is None:
                    em = ifcopenshell.util.element.get_material(f.by_id(sh.id))
                    elem_mat = getattr(em, "Name", None) or "Unnamed"
                name = elem_mat
            sel = tri[mids == k] if len(mids) == len(tri) else tri
            if not len(sel):
                continue
            d = m.diffuse
            rgb = tuple(float(c) for c in ((d.r(), d.g(), d.b()) if hasattr(d, "r") else d))
            grp = groups.setdefault(name, {"tris": [], "rgb": rgb,
                                           "alpha": 1.0 - float(m.transparency or 0.0)})
            grp["tris"].append(v[sel])
        if not it.next():
            break
    for grp in groups.values():
        grp["tris"] = np.concatenate(grp["tris"]).astype(np.float32)
    return groups


def _mesh_arrays(tris):
    """Flat shaded vertices in glTF's frame (y up, -z toward model +y), normals
    and UVs in metres by box projection, so library textures keep their scale."""
    import numpy as np

    p = tris.reshape(-1, 3)
    pos = np.stack([p[:, 0], p[:, 2], -p[:, 1]], axis=1).astype(np.float32)   # z up to y up
    t = pos.reshape(-1, 3, 3)
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    keep = ln[:, 0] > 1e-12                                           # drop degenerate triangles
    t, n, ln = t[keep], n[keep], ln[keep]
    n = (n / ln).astype(np.float32)
    nrm = np.repeat(n, 3, axis=0)
    pos = t.reshape(-1, 3)
    ax = np.argmax(np.abs(nrm), axis=1)
    uv = np.where(ax[:, None] == 0, pos[:, [2, 1]], np.where(ax[:, None] == 1, pos[:, [0, 2]], pos[:, [0, 1]]))
    uv = uv.astype(np.float32) * np.array([1.0, -1.0], dtype=np.float32)
    return pos, nrm, uv


def _pbr(name: str, rgb, alpha: float) -> dict:
    low = name.lower()
    mat = {"name": name, "doubleSided": True,
           "pbrMetallicRoughness": {"baseColorFactor": [*rgb, alpha], "metallicFactor": 0.0,
                                    "roughnessFactor": 0.05 if alpha < 1.0 else 0.8}}
    if alpha < 1.0:
        mat["alphaMode"] = "BLEND"
    if "led" in low:
        mat["emissiveFactor"] = list(rgb)
    return mat


def write_glb(groups: dict[str, dict], path: Path) -> int:
    """A binary glTF 2.0 file: one node and mesh per material, metres, y up."""
    import struct

    import numpy as np

    gltf = {"asset": {"version": "2.0", "generator": "villa-5130272 export_twinmotion.py",
                      "copyright": STAMP},
            "scene": 0, "scenes": [{"name": "Villa 5130272", "nodes": []}],
            "nodes": [], "meshes": [], "materials": [], "accessors": [], "bufferViews": [], "buffers": []}
    blob = bytearray()
    ntri = 0

    def add(arr, kind, minmax=False):
        arr = np.ascontiguousarray(arr, dtype=np.float32)
        while len(blob) % 4:
            blob.append(0)
        gltf["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": arr.nbytes,
                                    "target": 34962})
        blob.extend(arr.tobytes())
        acc = {"bufferView": len(gltf["bufferViews"]) - 1, "componentType": 5126, "count": len(arr), "type": kind}
        if minmax:
            acc["min"] = [float(x) for x in arr.min(axis=0)]
            acc["max"] = [float(x) for x in arr.max(axis=0)]
        gltf["accessors"].append(acc)
        return len(gltf["accessors"]) - 1

    for name in sorted(groups):
        grp = groups[name]
        pos, nrm, uv = _mesh_arrays(grp["tris"])
        if not len(pos):
            continue
        ntri += len(pos) // 3
        gltf["materials"].append(_pbr(name, grp["rgb"], grp["alpha"]))
        prim = {"attributes": {"POSITION": add(pos, "VEC3", True), "NORMAL": add(nrm, "VEC3"),
                               "TEXCOORD_0": add(uv, "VEC2")},
                "material": len(gltf["materials"]) - 1, "mode": 4}
        gltf["meshes"].append({"name": name, "primitives": [prim]})
        gltf["nodes"].append({"name": name, "mesh": len(gltf["meshes"]) - 1})
        gltf["scenes"][0]["nodes"].append(len(gltf["nodes"]) - 1)
    while len(blob) % 4:
        blob.append(0)
    gltf["buffers"].append({"byteLength": len(blob)})
    js = json.dumps(gltf, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    js += b" " * (-len(js) % 4)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)))
        fh.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        fh.write(struct.pack("<II", len(blob), 0x004E4942) + bytes(blob))
    return ntri


def _obj_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name).strip("_")


def write_obj(groups: dict[str, dict], path: Path) -> int:
    """The same geometry as Wavefront OBJ with an MTL file (y up, metres), for
    a Twinmotion version whose import dialog does not list glTF."""
    mtl = path.with_suffix(".mtl")
    lines = [f"# Villa 5130272, {STAMP}", f"mtllib {mtl.name}"]
    mlines = [f"# Villa 5130272, {STAMP}"]
    base = 1
    for name in sorted(groups):
        grp = groups[name]
        pos, nrm, uv = _mesh_arrays(grp["tris"])
        if not len(pos):
            continue
        on = _obj_name(name)
        r, g, b = grp["rgb"]
        mlines += ["", f"newmtl {on}", f"Kd {r:.4f} {g:.4f} {b:.4f}", "Ka 0 0 0", "Ks 0.04 0.04 0.04",
                   f"d {grp['alpha']:.3f}", "illum 2"]
        lines += [f"o {on}", f"usemtl {on}"]
        lines += [f"v {x:.4f} {y:.4f} {z:.4f}" for x, y, z in pos]
        lines += [f"vn {x:.4f} {y:.4f} {z:.4f}" for x, y, z in nrm]
        lines += [f"vt {u:.4f} {v:.4f}" for u, v in uv]
        for i in range(0, len(pos), 3):
            a, b2, c = base + i, base + i + 1, base + i + 2
            lines.append(f"f {a}/{a}/{a} {b2}/{b2}/{b2} {c}/{c}/{c}")
        base += len(pos)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mtl.write_text("\n".join(mlines) + "\n", encoding="utf-8")
    return (base - 1) // 3


def export_meshes(ifc_path: Path) -> tuple[Path, Path]:
    """GLB and OBJ beside the palette's IFC: Twinmotion 2026 does not offer IFC
    in its import dialog (owner, 2026-10-05), it does take glTF, FBX and OBJ."""
    groups = tessellate(ifc_path)
    glb = ifc_path.with_suffix(".glb")
    obj = ifc_path.with_suffix(".obj")
    n = write_glb(groups, glb)
    write_obj(groups, obj)
    print(f"GLB  {_rel(glb)}   {len(groups)} materials, {n} triangles (and the same as .obj)")
    return glb, obj


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
                     "storey": "site", "x_m": t["u"], "y_m": t["v"],
                     "z_m": (t["z"] if t.get("z") is not None else g["ground_z"]), "width_m": t["crown_m"],
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
        export_meshes(export_palette(data, i, pals[i]["name"]))
    write_placements(data)
    write_cameras(data)
    shutil.copy(REPO_ROOT / "docs" / "twinmotion-guide.md", OUT / "README.md")
    print(STAMP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
