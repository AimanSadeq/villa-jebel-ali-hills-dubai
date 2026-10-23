"""Photo-realistic renders of Villa 5130272 with Blender Cycles (answer P9, D-057).

Builds the Blender scene from the project's own outputs, nothing by hand:
  * the IFC model (output/ifc/VJH-ARCH-001_Villa_5130272.ifc) through
    IfcOpenShell, one Blender mesh per element, materials from the IFC
    surface styles mapped to photographic textures (viewer/public/assets,
    fetched by assets/fetch_assets.py; stand-ins from make_standins.py);
  * the interior finishes of the chosen palette (viewer/public/data/model.json,
    "finishes"), the garden surfaces, hedges and trees ("exterior"), and the
    furniture as softened pieces, from the same file;
  * a physical sky (Blender's Nishita model) with the sun at the sun study's
    position for the view (model.json "sun"), so light and shadows are the
    site's own;
  * the six views of CLAUDE.md deliverable 5, each a camera in the plot grid.

Runs with Blender's Python module (pip install bpy) or inside Blender:
    python renders/render_villa.py --view living --samples 128 --size 1920x1080
    python renders/render_villa.py --all --device GPU            (laptop, Intel Arc)
    blender -b -P renders/render_villa.py -- --view aerial
Output: output/renders/VJH-R-00n_<view>.png, stamped CONCEPT DESIGN, NOT FOR CONSTRUCTION.

Coordinates: Blender x = plot grid u, y = v, z = height, metres.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: E402
import ifcopenshell  # noqa: E402
import ifcopenshell.geom  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.geometry import tessellate_polygon  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import furniture_bl  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
IFC = REPO_ROOT / "output" / "ifc" / "VJH-ARCH-001_Villa_5130272.ifc"
MODEL_JSON = REPO_ROOT / "viewer" / "public" / "data" / "model.json"
ASSET_INDEX = REPO_ROOT / "viewer" / "public" / "assets" / "index.json"
ASSET_ROOT = REPO_ROOT / "viewer" / "public"
MASSING = REPO_ROOT / "brief" / "massing.yaml"
OUT = REPO_ROOT / "output" / "renders"
STAMP = "CONCEPT DESIGN, NOT FOR CONSTRUCTION"

# IFC surface style name -> (texture key, tint hex, roughness). Texture keys
# are assets/manifest.yaml; a missing texture leaves the tint as the colour.
STYLE_MAT = {
    "White render": ("plaster_white", "#f2f1ec", 0.9),
    "Beige render": ("beige_render", "#dccdb0", 0.9), "Partition, painted": ("plaster_white", "#f2ece1", 0.9),
    "Slab, rendered edge": ("beige_render", "#e3dbcc", 0.9), "Roof finish": ("concrete_smooth", "#d9d5cc", 0.8),
    "Charcoal stone cladding": ("split_face_stone", "#3a3a3c", 0.85), "Timber, soffits, fins and screens": ("timber", "#9e7045", 0.6),
    "Warm split face stone": ("split_face_stone", "#c8ad7f", 0.85), "Timber, soffits, fins and pergola": ("timber", "#9a643a", 0.6),
    "Linear LED line, warm white": (None, "#ffd9a0", 0.3), "Glazing": ("glass", "#ffffff", 0.05),
    "Timber": ("walnut", "#7a5236", 0.5), "Stone deck": ("terrace_stone", "#d9d3c7", 0.7), "Paving, light": ("paving", "#e3dfd6", 0.8),
    "Garden ground": ("soil", "#8c7a63", 1.0), "Lawn": ("lawn", "#5a8a3a", 1.0), "Planting bed, mulch": ("soil", "#5c4a3a", 1.0),
    "Foliage": (None, "#3f6b2e", 0.8), "Palm fronds": (None, "#4f7a2e", 0.7), "Trunk": ("timber", "#5a4332", 0.9),
    "Stair, stone": ("limestone_floor", "#d9ccb4", 0.6), "Lift car and shaft": (None, "#55585c", 0.4),
    "Joinery, light oak": ("oak_floor", "#c8a272", 0.6), "Upholstery": ("fabric", "#d7cbb5", 1.0),
    "Sanitary ware": (None, "#f7f7f5", 0.15), "Metal, dark": (None, "#262626", 0.35),
    "Pool shell": (None, "#e0e2e0", 0.4), "Pool water": (None, "#3a94c7", 0.05), "Room volume": None,
}
SKIP_CLASSES = {"IfcSpace", "IfcOpeningElement", "IfcFurniture", "IfcSanitaryTerminal"}
SKIP_OBJECT_TYPES = ("Landscape: palm", "Landscape: tree", "Landscape: hedge")

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
PALETTE_DEFAULT = 0


def hexrgb(h: str) -> tuple[float, float, float, float]:
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (r ** 2.2, g ** 2.2, b ** 2.2, 1.0)        # sRGB to linear


class Materials:
    """Principled materials with the project's textures, box-projected so no UVs are needed."""

    def __init__(self, index: dict | None):
        self.index = index or {"textures": {}}
        self.cache: dict[str, bpy.types.Material] = {}

    def get(self, key: str | None, tint: str, roughness: float, name: str | None = None) -> bpy.types.Material:
        k = f"{key}|{tint}|{roughness}"
        if k in self.cache:
            return self.cache[k]
        m = bpy.data.materials.new(name or k)
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        bsdf.inputs["Roughness"].default_value = roughness
        if key == "glass":
            # Architectural glass: refractive for camera rays, transparent for
            # shadow rays, so the sun and the sky light the rooms through the
            # windows (Cycles blocks direct light at glass with caustics off).
            bsdf.inputs["Transmission Weight"].default_value = 1.0
            bsdf.inputs["Roughness"].default_value = 0.02
            bsdf.inputs["IOR"].default_value = 1.5
            bsdf.inputs["Base Color"].default_value = (0.92, 0.96, 0.98, 1)
            out = nt.nodes["Material Output"]
            lp = nt.nodes.new("ShaderNodeLightPath")
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            mix = nt.nodes.new("ShaderNodeMixShader")
            nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs["Fac"])
            nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
            nt.links.new(tr.outputs["BSDF"], mix.inputs[2])
            nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
            self.cache[k] = m
            return m
        bsdf.inputs["Base Color"].default_value = hexrgb(tint)
        e = self.index["textures"].get(key or "")
        if e and e.get("diff"):
            scale = 1.0 / float(e.get("scale_m", 2.0))
            coord = nt.nodes.new("ShaderNodeTexCoord")
            mapping = nt.nodes.new("ShaderNodeMapping")
            mapping.inputs["Scale"].default_value = (scale, scale, scale)
            nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])

            def image(path: str, srgb: bool):
                img = bpy.data.images.load(str(ASSET_ROOT / path), check_existing=True)
                img.colorspace_settings.name = "sRGB" if srgb else "Non-Color"
                node = nt.nodes.new("ShaderNodeTexImage")
                node.image = img
                node.projection = "BOX"
                node.projection_blend = 0.25
                nt.links.new(mapping.outputs["Vector"], node.inputs["Vector"])
                return node

            diff = image(e["diff"], True)
            # Tint multiplies the photograph (white keeps it as photographed).
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            nt.links.new(diff.outputs["Color"], mix.inputs[6])
            mix.inputs[7].default_value = hexrgb(tint) if tint.lower() != "#ffffff" else (1, 1, 1, 1)
            nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
            if e.get("rough"):
                rough = image(e["rough"], False)
                nt.links.new(rough.outputs["Color"], bsdf.inputs["Roughness"])
            if e.get("nor"):
                nor = image(e["nor"], False)
                nm = nt.nodes.new("ShaderNodeNormalMap")
                nm.inputs["Strength"].default_value = 0.6
                nt.links.new(nor.outputs["Color"], nm.inputs["Color"])
                nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        self.cache[k] = m
        return m


def mesh_object(name: str, verts, faces, mat: bpy.types.Material | None, collection, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    if mat is not None:
        me.materials.append(mat)
    collection.objects.link(ob)
    return ob


def box_object(name, u0, u1, v0, v1, z0, z1, mat, collection, bevel=0.0, smooth=False):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=((u0 + u1) / 2, (v0 + v1) / 2, (z0 + z1) / 2))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (max(u1 - u0, 0.01), max(v1 - v0, 0.01), max(z1 - z0, 0.01))
    bpy.ops.object.transform_apply(scale=True)
    if mat is not None:
        ob.data.materials.append(mat)
    if bevel > 0:
        b = ob.modifiers.new("bevel", "BEVEL")
        b.width = min(bevel, (min(u1 - u0, v1 - v0, z1 - z0)) * 0.45)
        b.segments = 4
        b.limit_method = "NONE"
        if smooth:
            for p in ob.data.polygons:
                p.use_smooth = True
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    collection.objects.link(ob)
    return ob


# Scene parts ---------------------------------------------------------------------

def add_ifc(mats: Materials, col) -> int:
    f = ifcopenshell.open(str(IFC))
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)
    it = ifcopenshell.geom.iterator(s, f, 4)
    # The iterator names materials after the shading entity; the style's own
    # name sits on the IfcSurfaceStyle the material's instance id points to.
    style_names = {st.id(): st.Name for st in f.by_type("IfcSurfaceStyle")}
    n = 0
    if not it.initialize():
        return 0
    while True:
        sh = it.get()
        e = f.by_id(sh.id)
        ot = getattr(e, "ObjectType", None) or ""
        if e.is_a() not in SKIP_CLASSES and not ot.startswith(SKIP_OBJECT_TYPES):
            g = sh.geometry
            verts = np.array(g.verts).reshape(-1, 3)
            faces = np.array(g.faces).reshape(-1, 3)
            mat_ids = np.array(g.material_ids)
            styles = [style_names.get(m.instance_id(), m.name) for m in g.materials]
            # One object per style used by the element.
            for si, sname in enumerate(styles):
                sel = faces[mat_ids == si] if len(mat_ids) == len(faces) else faces
                if len(sel) == 0:
                    continue
                spec = STYLE_MAT.get(sname, ("plaster_white", "#e8e2d6", 0.9))
                if spec is None:
                    continue
                key, tint, rough = spec
                mat = mats.get(key, tint, rough, sname)
                name = f"{e.is_a()} {e.Name or ''} [{sname}]"[:60]
                mesh_object(name, verts, sel, mat, col, smooth=False)
                n += 1
        if not it.next():
            break
    return n


def add_finishes(data: dict, palette: int, mats: Materials, col) -> None:
    fin = data.get("finishes") or {}
    pal = fin["palettes"][palette]
    for q in fin["quads"]:
        grp, slot = q["slot"].split(".")
        sw = pal[grp][slot]
        # A photographed material shows as photographed; a dark marble keeps
        # its tint (the photograph is of a light one); plain colours stay.
        dark = int(sw["colour"].lstrip("#")[:2], 16) < 0x55
        tint = sw["colour"] if not sw.get("texture") or dark else "#ffffff"
        mat = mats.get(sw.get("texture"), tint, float(sw["roughness"]), f"finish {q['slot']}")
        pts = q["p"]
        mesh_object(f"finish {q['slot']} {q['room']}", pts, [(0, 1, 2, 3)], mat, col)
    # Furniture: modelled pieces (furniture_bl.py) in the palette's colours;
    # the layout's boxes, softened, for anything without a builder.
    soft = {"accents.textile": 0.07, "accents.highlight": 0.05, "fixtures.sanitary": 0.03,
            "accents.joinery": 0.012, "accents.worktop": 0.008, "fixtures.metal": 0.004}

    def slot_mat(slot: str):
        if slot.startswith("fixed."):
            colour = slot[6:]
            if colour == "#bcd3dd":                      # shower screens: real glass
                return mats.get("glass", colour, 0.02, "shower glass")
            rough = 0.5 if colour == "#121212" else 0.15 if colour in ("#c9d4d8", "#9fb7c2") else 0.8
            return mats.get(None, colour, rough, f"fixed {colour}")
        grp, key = slot.split(".")
        sw = pal[grp][key]
        return mats.get(sw.get("texture"), "#ffffff" if sw.get("texture") else sw["colour"], float(sw["roughness"]),
                        f"furniture {slot}")

    built = set()
    for piece in fin.get("pieces", []):
        if furniture_bl.build_piece(piece, col, slot_mat):
            built.add(piece["index"])
    for b in fin.get("boxes", []):
        if b.get("piece") in built:
            continue
        slot = b["slot"]
        u0, u1, v0, v1, z0, z1 = b["b"]
        bevel = 0.0 if slot.startswith("fixed.") else soft.get(slot, 0.01)
        box_object(f"furniture {slot}", u0, u1, v0, v1, z0, z1, slot_mat(slot), col, bevel=bevel, smooth=bevel >= 0.03)


def add_garden(data: dict, mats: Materials, col) -> None:
    ext = data.get("exterior") or {}
    tex = {"lawn": ("lawn", "#ffffff", 1.0), "bed": ("soil", "#ffffff", 1.0), "ground": ("soil", "#cfc6b8", 1.0),
           "paving": ("terrace_stone", "#ffffff", 0.7), "step": ("terrace_stone", "#ffffff", 0.7), "path": ("paving", "#ffffff", 0.8)}
    for s in ext.get("garden", []):
        key, tint, rough = tex.get(s["kind"], ("soil", "#ffffff", 1.0))
        mat = mats.get(key, tint, rough, f"garden {s['kind']}")
        for rings in s["rings"]:
            polys = [[Vector((u, v, 0.0)) for u, v in ring] for ring in rings]
            tris = tessellate_polygon(polys)
            pts = [p for ring in polys for p in ring]
            verts = [(p.x, p.y, s["z"] + 0.006) for p in pts]
            mesh_object(f"garden {s['key']}", verts, tris, mat, col)
    leaf = mats.get(None, "#3f6b2e", 0.75, "leaf")
    for h in ext.get("hedges", []):
        u0, u1, v0, v1, z0, z1 = h["b"]
        ob = box_object("hedge", u0, u1, v0, v1, z0, z1, leaf, col, bevel=0.12, smooth=True)
        d = ob.modifiers.new("displace", "DISPLACE")
        t = bpy.data.textures.new("hedge_noise", "CLOUDS")
        t.noise_scale = 0.12
        d.texture = t
        d.strength = 0.08
    add_surroundings(mats, col, float(ext.get("ground_z", -0.45)))
    trunk = mats.get("timber", "#5a4332", 0.9, "trunk")
    palm_leaf = mats.get(None, "#4f7a2e", 0.65, "palm leaf")
    for t in ext.get("trees", []):
        add_tree(t, trunk, leaf if t["kind"] == "tree" else palm_leaf, col, ground=float(ext.get("ground_z", -0.45)))


def add_surroundings(mats: Materials, col, ground: float) -> None:
    """Sand coloured ground far around the plot, so the view beyond the
    boundary wall is land, not the sky model's black underside; and the road
    along side 1 as a darker strip."""
    sand = mats.get(None, "#e6dcc4", 1.0, "surroundings sand")
    box_object("surroundings", -300, 330, -300, 330, ground - 0.6, ground - 0.02, sand, col)
    road = mats.get("concrete_smooth", "#8f8a82", 0.9, "road")
    box_object("road", -18.3, -0.2, -40, 70, ground - 0.5, ground - 0.01, road, col)


def add_tree(t: dict, trunk_mat, leaf_mat, col, ground: float) -> None:
    u, v = t["u"], t["v"]
    hgt, tk, crown = float(t["height_m"]), float(t["trunk_m"]), float(t["crown_m"])
    rng = np.random.default_rng(int(u * 10 + v * 100))
    if t["kind"] == "palm":
        # Trunk with a slight lean, then fronds: a rachis with leaflets either side.
        lean = rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06)
        bpy.ops.mesh.primitive_cone_add(vertices=14, radius1=0.30, radius2=0.20, depth=tk, location=(u, v, ground + tk / 2))
        tr = bpy.context.active_object
        tr.rotation_euler = (lean[1], -lean[0], 0)
        tr.data.materials.append(trunk_mat)
        for p in tr.data.polygons:
            p.use_smooth = True
        for c in list(tr.users_collection):
            c.objects.unlink(tr)
        col.objects.link(tr)
        top = Vector((u + lean[0] * tk, v + lean[1] * tk, ground + tk))
        n = 22
        for i in range(n):
            a = 2 * math.pi * i / n + rng.uniform(-0.12, 0.12)
            tilt = rng.uniform(0.15, 1.1)
            L = crown * 0.6
            segs = 14
            verts, faces = [], []
            spine = []
            for k in range(segs + 1):
                sgm = k / segs
                droop = tilt * sgm + 1.4 * sgm * sgm
                ang = max(-1.2, 1.1 - droop)
                dist = L * sgm * math.cos(ang) if k else 0.0
                z = top.z + L * sgm * math.sin(ang)
                spine.append(Vector((top.x + dist * math.cos(a), top.y + dist * math.sin(a), z)))
            # Rachis.
            for k in range(segs + 1):
                px, py = -math.sin(a) * 0.035, math.cos(a) * 0.035
                sp = spine[k]
                verts += [(sp.x - px, sp.y - py, sp.z), (sp.x + px, sp.y + py, sp.z)]
                if k:
                    b0 = 2 * (k - 1)
                    faces.append((b0, b0 + 1, b0 + 3, b0 + 2))
            # Leaflets: close pairs of blades along the rachis, angled down and out.
            for k in range(1, segs):
                sgm = k / segs
                lw = 0.55 * math.sin(math.pi * min(1.0, sgm * 1.1)) + 0.12
                sp, nxt = spine[k], spine[min(k + 1, segs)]
                d = (nxt - sp).normalized()
                side = Vector((-math.sin(a), math.cos(a), 0.0))
                for j in range(3):
                    base = sp + d * (j * 0.33 * (nxt - sp).length)
                    for sg in (-1, 1):
                        tip = base + side * (sg * lw) + Vector((0, 0, -lw * 0.5)) + d * 0.15
                        b0 = len(verts)
                        verts += [tuple(base - d * 0.03), tuple(base + d * 0.06), tuple(tip)]
                        faces.append((b0, b0 + 1, b0 + 2))
            mesh_object("palm frond", verts, faces, leaf_mat, col, smooth=True)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.24, radius2=0.14, depth=tk + 0.6, location=(u, v, ground + (tk + 0.6) / 2))
        tr = bpy.context.active_object
        tr.data.materials.append(trunk_mat)
        for p in tr.data.polygons:
            p.use_smooth = True
        for c in list(tr.users_collection):
            c.objects.unlink(tr)
        col.objects.link(tr)
        # Branches fanning out from the top of the trunk, each with a leaf cluster.
        for i in range(7):
            a = 2 * math.pi * i / 7 + rng.uniform(-0.3, 0.3)
            rise = rng.uniform(0.45, 0.85)
            L = crown * rng.uniform(0.3, 0.5)
            end = Vector((u + L * math.cos(a) * math.cos(rise), v + L * math.sin(a) * math.cos(rise), ground + tk + 0.6 + L * math.sin(rise)))
            start = Vector((u, v, ground + tk + 0.3))
            mid = (start + end) / 2
            d = end - start
            bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.09, radius2=0.04, depth=d.length, location=mid)
            br = bpy.context.active_object
            br.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
            br.data.materials.append(trunk_mat)
            for c in list(br.users_collection):
                c.objects.unlink(br)
            col.objects.link(br)
            for j in range(3):
                cr = crown * rng.uniform(0.16, 0.24)
                # Crowns stay above head height: nothing lower than the trunk top plus a metre.
                cpos = end + Vector((rng.uniform(-0.3, 0.3) * cr * 2, rng.uniform(-0.3, 0.3) * cr * 2, rng.uniform(0.1, 0.6) * cr))
                cpos.z = max(cpos.z, ground + tk + 1.0 + cr)
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=cr, location=cpos)
                sp = bpy.context.active_object
                sp.data.materials.append(leaf_mat)
                for p in sp.data.polygons:
                    p.use_smooth = True
                dm = sp.modifiers.new("displace", "DISPLACE")
                tx = bpy.data.textures.new("leaf_noise", "CLOUDS")
                tx.noise_scale = 0.25
                dm.texture = tx
                dm.strength = cr * 0.7
                for c in list(sp.users_collection):
                    c.objects.unlink(sp)
                col.objects.link(sp)


def add_sky(sun: dict, bearing_deg: float) -> None:
    world = bpy.data.worlds.new("Sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(float(sun["elevation_deg"]))
    # Nishita's rotation turns the sun anticlockwise from +Y; the compass
    # azimuth turns clockwise from north, and +Y (grid v) bears bearing_deg.
    sky.sun_rotation = -math.radians(float(sun["azimuth_deg"]) - bearing_deg)
    sky.sun_size = math.radians(0.6)
    sky.sun_intensity = 1.0
    sky.altitude = 20.0
    sky.air_density = 1.0
    sky.dust_density = 1.6 if sun.get("elevation_deg", 40) < 12 else 1.0
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def add_camera(view: str, size: tuple[int, int]) -> bpy.types.Object:
    pos, look, lens, _, _ = VIEWS[view]
    cam_data = bpy.data.cameras.new(f"cam_{view}")
    cam_data.lens = lens
    cam_data.sensor_width = 36
    cam_data.clip_end = 500
    cam = bpy.data.objects.new(f"cam_{view}", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = Vector(pos)
    direction = Vector(look) - Vector(pos)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = size
    return cam


def setup_render(samples: int, device: str) -> None:
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.device = device
    if device == "GPU":
        prefs = bpy.context.preferences.addons.get("cycles")
        if prefs:
            prefs.preferences.compute_device_type = "ONEAPI"      # Intel Arc on the laptop
            prefs.preferences.get_devices()
            for d in prefs.preferences.devices:
                d.use = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    sc.cycles.max_bounces = 8
    sc.cycles.diffuse_bounces = 4
    sc.cycles.transmission_bounces = 8
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False


def calibrate_exposure(target: float = 0.50) -> float:
    """The Nishita sky is in physical units: render a tiny preview and set
    the exposure so the mean of the picture lands near the target."""
    sc = bpy.context.scene
    rx, ry, pct, smp = sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage, sc.cycles.samples
    sc.render.resolution_percentage = 5
    sc.cycles.samples = 8
    sc.cycles.use_denoising = False
    sc.view_settings.exposure = 0.0
    tmp = OUT / "_calib.png"
    sc.render.filepath = str(tmp)
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(str(tmp))
    px = np.array(img.pixels[:]).reshape(-1, 4)[:, :3]
    lum = np.clip(px, 0, 1).mean(1)
    # Windows and the sky blow out whatever the exposure: judge the rest.
    body = lum[lum < 0.97]
    mean = float(body.mean()) if len(body) > lum.size * 0.2 else float(lum.mean())
    bpy.data.images.remove(img)
    tmp.unlink(missing_ok=True)
    sc.render.resolution_percentage = pct
    sc.cycles.samples = smp
    sc.cycles.use_denoising = True
    # AgX is roughly logarithmic in the mid range: one stop moves the mean about 0.12.
    ev = (target - mean) / 0.12
    ev = max(-8.0, min(6.0, ev))
    sc.view_settings.exposure = ev
    return ev


def stamp(path: Path, title: str) -> None:
    """Write the stamp and the view title onto the finished render."""
    try:
        from PIL import Image, ImageDraw  # noqa: PLC0415
    except ImportError as e:
        raise SystemExit("Pillow is needed to stamp the render (pip install pillow); "
                         "every output must carry CONCEPT DESIGN, NOT FOR CONSTRUCTION.") from e
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    w, h = im.size
    size = max(11, w // 90)
    try:
        from PIL import ImageFont  # noqa: PLC0415
        font = ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:  # noqa: BLE001
        font = None
    band = int(size * 3.2)
    d.rectangle([0, h - band, w, h], fill=(20, 20, 20))
    d.text((size, h - band + size * 0.4), f"Villa 5130272, Jebel Ali Hills   {title}", fill=(240, 236, 228), font=font)
    d.text((size, h - band + size * 1.8), STAMP, fill=(230, 80, 60), font=font)
    im.save(path)


def render_view(view: str, data: dict, mats: Materials, args) -> Path:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.data.collections.new("villa")
    bpy.context.scene.collection.children.link(col)
    add_ifc(mats, col)
    add_finishes(data, args.palette, mats, col)
    add_garden(data, mats, col)
    pos, look, lens, sun_key, title = VIEWS[view]
    sun = (data.get("sun") or {}).get(sun_key) or {"azimuth_deg": 242.0, "elevation_deg": 45.0}
    bearing = float(yaml.safe_load(MASSING.read_text(encoding="utf-8"))["grid"]["bearing_deg"])
    add_sky(sun, bearing)
    w, h = (int(x) for x in args.size.lower().split("x"))
    add_camera(view, (w, h))
    setup_render(args.samples, args.device)
    OUT.mkdir(parents=True, exist_ok=True)
    ev = calibrate_exposure()
    n = list(VIEWS).index(view) + 1
    path = OUT / f"VJH-R-{n:03d}_{view}.png"
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    stamp(path, f"{title}, sun {sun.get('when', '')}, palette {args.palette + 1}")
    print(f"rendered {path.relative_to(REPO_ROOT)}   exposure {ev:+.1f} EV   samples {args.samples}")
    return path


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Cycles renders of Villa 5130272.")
    ap.add_argument("--view", choices=list(VIEWS), help="One view.")
    ap.add_argument("--all", action="store_true", help="All six views.")
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--device", choices=["CPU", "GPU"], default="CPU")
    ap.add_argument("--palette", type=int, default=PALETTE_DEFAULT, help="0, 1 or 2 (brief/palettes.yaml order).")
    args = ap.parse_args(argv)
    if not IFC.exists():
        print(f"Missing {IFC}: run src/model/build_model.py first.")
        return 1
    data = json.loads(MODEL_JSON.read_text(encoding="utf-8"))
    index = json.loads(ASSET_INDEX.read_text(encoding="utf-8")) if ASSET_INDEX.exists() else None
    if index is None:
        print("No viewer/public/assets/index.json: materials render as plain colours. Run assets/fetch_assets.py.")
    elif index.get("standin"):
        print("Stand-in textures (assets/make_standins.py): run assets/fetch_assets.py for the real photographs.")
    mats = Materials(index)
    views = list(VIEWS) if args.all else [args.view or "living"]
    for v in views:
        render_view(v, data, Materials(index), args)
    return 0


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    sys.exit(main(argv))
