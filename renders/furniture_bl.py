"""Furniture for the renders, built in Blender from the layout's pieces (D-057, stage 2).

Each builder takes a piece from viewer/public/data/model.json ("finishes",
"pieces": name, footprint, height, the wall side it stands against, its
back side) and makes it as modelled objects: a bed with frame, mattress,
pillows and duvet; sofas and armchairs with cushions and legs; chairs;
tables; cabinets with door lines and handles; kitchen counters with units,
worktop and wall cupboards; vanities with basins and mirror; WCs, showers
and bathtubs; rugs. Materials come from the chosen palette through the
render script's Materials (slot names of brief/palettes.yaml).

Shapes are generic, sized from the piece's box; they are indicative furniture
for the pictures, not a specification or a product.

Local frame of a builder: x along the piece's front (left to right as seen
from the room), y from the back toward the room, z up; the builder returns
objects in grid coordinates through `place`.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Euler, Vector

LINEN = "fixed.#f4f1ea"
SCREEN = "fixed.#121212"
GLASS = "fixed.#bcd3dd"
MIRROR = "fixed.#c9d4d8"
J, TX, HI, WT, ME, SA = ("accents.joinery", "accents.textile", "accents.highlight",
                         "accents.worktop", "fixtures.metal", "fixtures.sanitary")
BACK_ROT = {"S": 0.0, "W": -math.pi / 2, "N": math.pi, "E": math.pi / 2}


class Frame:
    """Places local boxes and primitives into the grid for one piece."""

    def __init__(self, piece: dict, col, get_mat):
        u0, u1, v0, v1 = piece["fp"]
        self.z0 = piece["z"][0]
        self.back = piece.get("back") or piece.get("side") or "S"
        self.rot = BACK_ROT[self.back]
        # Width along the front, depth from the back.
        if self.back in ("S", "N"):
            self.w, self.d = u1 - u0, v1 - v0
        else:
            self.w, self.d = v1 - v0, u1 - u0
        self.cu, self.cv = (u0 + u1) / 2, (v0 + v1) / 2
        self.col = col
        self.get_mat = get_mat
        self.objects: list = []
        self.name = piece["name"]

    def to_grid(self, x: float, y: float, z: float) -> Vector:
        # Local: x right, y toward the room from the back face, origin at the
        # back-centre of the footprint. Rotate about z by the back side.
        lx, ly = x, y - self.d / 2
        c, s = math.cos(self.rot), math.sin(self.rot)
        return Vector((self.cu + lx * c - ly * s, self.cv + lx * s + ly * c, self.z0 + z))

    def box(self, slot, x0, x1, y0, y1, z0, z1, bevel=0.0, smooth=False, subsurf=0, name=None):
        if x1 - x0 < 0.004 or y1 - y0 < 0.004 or z1 - z0 < 0.004:
            return None
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        ob = bpy.context.active_object
        ob.name = name or f"{self.name} part"
        ob.scale = (x1 - x0, y1 - y0, z1 - z0)
        bpy.ops.object.transform_apply(scale=True)
        ob.location = self.to_grid((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        ob.rotation_euler = Euler((0, 0, self.rot))
        ob.data.materials.append(self.get_mat(slot))
        if bevel > 0:
            b = ob.modifiers.new("bevel", "BEVEL")
            b.width = min(bevel, min(x1 - x0, y1 - y0, z1 - z0) * 0.45)
            b.segments = 3
            b.limit_method = "NONE"
        if subsurf:
            sm = ob.modifiers.new("subsurf", "SUBSURF")
            sm.levels = sm.render_levels = subsurf
        if smooth:
            for p in ob.data.polygons:
                p.use_smooth = True
        self._link(ob)
        return ob

    def cylinder(self, slot, x, y, z0, z1, r, smooth=True, name=None, verts=24):
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=z1 - z0)
        ob = bpy.context.active_object
        ob.name = name or f"{self.name} cylinder"
        ob.location = self.to_grid(x, y, (z0 + z1) / 2)
        ob.rotation_euler = Euler((0, 0, self.rot))
        ob.data.materials.append(self.get_mat(slot))
        if smooth:
            for p in ob.data.polygons:
                p.use_smooth = True
        self._link(ob)
        return ob

    def ellipsoid(self, slot, x, y, z, rx, ry, rz, name=None):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0)
        ob = bpy.context.active_object
        ob.name = name or f"{self.name} rounded"
        ob.scale = (rx, ry, rz)
        bpy.ops.object.transform_apply(scale=True)
        ob.location = self.to_grid(x, y, z)
        ob.rotation_euler = Euler((0, 0, self.rot))
        ob.data.materials.append(self.get_mat(slot))
        for p in ob.data.polygons:
            p.use_smooth = True
        self._link(ob)
        return ob

    def _link(self, ob):
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        self.col.objects.link(ob)
        self.objects.append(ob)


# Builders --------------------------------------------------------------------

def bed(f: Frame, piece: dict):
    w, d = f.w, f.d
    stands = w > 1.3
    bw = w - (1.1 if stands else 0.0)            # bed width without bedside tables
    x0, x1 = -bw / 2, bw / 2
    L = min(d, 2.15)
    f.box(TX, x0 - 0.04, x1 + 0.04, 0.0, 0.08, 0.0, 1.15, bevel=0.02, name=f"{f.name} headboard")
    f.box(J, x0, x1, 0.08, L, 0.0, 0.28, bevel=0.01, name=f"{f.name} frame")
    f.box(LINEN, x0 + 0.02, x1 - 0.02, 0.10, L - 0.02, 0.28, 0.52, bevel=0.05, smooth=True, subsurf=1, name=f"{f.name} mattress")
    f.box(HI, x0 - 0.03, x1 + 0.03, 0.75, L + 0.02, 0.50, 0.60, bevel=0.06, smooth=True, subsurf=1, name=f"{f.name} duvet")
    n = 2 if bw > 1.2 else 1
    pw = (bw - 0.2) / n
    for i in range(n):
        a = x0 + 0.1 + i * pw
        f.box(LINEN, a + 0.04, a + pw - 0.04, 0.14, 0.62, 0.52, 0.70, bevel=0.07, smooth=True, subsurf=1, name=f"{f.name} pillow")
    if stands:
        for sg in (-1, 1):
            a = sg * (bw / 2 + 0.07)
            lo, hi = sorted((a, a + sg * 0.48))
            f.box(J, lo, hi, 0.02, 0.48, 0.0, 0.55, bevel=0.008, name=f"{f.name} bedside")
            f.cylinder(ME, (lo + hi) / 2, 0.25, 0.55, 0.62, 0.015, name=f"{f.name} lamp stem")
            f.ellipsoid(LINEN, (lo + hi) / 2, 0.25, 0.80, 0.14, 0.14, 0.10, name=f"{f.name} lamp shade")


def sofa(f: Frame, piece: dict):
    w, d = f.w, min(f.d, 1.0)
    h = w / 2
    f.box(TX, -h, h, 0.0, d, 0.12, 0.42, bevel=0.03, smooth=True, name=f"{f.name} base")
    f.box(TX, -h, h, 0.0, 0.24, 0.42, 0.88, bevel=0.05, smooth=True, subsurf=1, name=f"{f.name} back")
    for sg in (-1, 1):
        lo, hi = sorted((sg * h, sg * (h - 0.20)))
        f.box(TX, lo, hi, 0.18, d, 0.42, 0.64, bevel=0.05, smooth=True, subsurf=1, name=f"{f.name} arm")
    n = max(1, round((w - 0.4) / 0.75))
    cw = (w - 0.4) / n
    for i in range(n):
        a = -h + 0.2 + i * cw
        f.box(TX, a + 0.02, a + cw - 0.02, 0.26, d - 0.03, 0.42, 0.56, bevel=0.06, smooth=True, subsurf=1, name=f"{f.name} seat cushion")
        f.box(TX, a + 0.03, a + cw - 0.03, 0.20, 0.36, 0.56, 0.86, bevel=0.07, smooth=True, subsurf=1, name=f"{f.name} back cushion")
    for sg in (-1, 1):
        f.box(HI, sg * (h - 0.55) - 0.2, sg * (h - 0.55) + 0.2, 0.30, 0.44, 0.56, 0.96, bevel=0.06, smooth=True, subsurf=1, name=f"{f.name} cushion")
    for x in (-h + 0.08, h - 0.08):
        for y in (0.08, d - 0.08):
            f.cylinder(ME, x, y, 0.0, 0.12, 0.02, name=f"{f.name} leg")


def armchair(f: Frame, piece: dict):
    w, d = min(f.w, 0.95), min(f.d, 0.95)
    h = w / 2
    f.box(TX, -h, h, 0.0, d, 0.10, 0.42, bevel=0.04, smooth=True, subsurf=1, name=f"{f.name} base")
    f.box(TX, -h, h, 0.0, 0.2, 0.42, 0.82, bevel=0.06, smooth=True, subsurf=1, name=f"{f.name} back")
    for sg in (-1, 1):
        lo, hi = sorted((sg * h, sg * (h - 0.16)))
        f.box(TX, lo, hi, 0.16, d, 0.42, 0.62, bevel=0.05, smooth=True, subsurf=1, name=f"{f.name} arm")
    f.box(TX, -h + 0.18, h - 0.18, 0.22, d - 0.03, 0.42, 0.55, bevel=0.06, smooth=True, subsurf=1, name=f"{f.name} seat")
    for x in (-h + 0.06, h - 0.06):
        for y in (0.06, d - 0.06):
            f.cylinder(ME, x, y, 0.0, 0.10, 0.018, name=f"{f.name} leg")


def chair(f: Frame, piece: dict):
    w = min(f.w, 0.48)
    d = min(f.d, 0.5)
    h = w / 2
    f.box(TX, -h, h, 0.04, d, 0.42, 0.47, bevel=0.02, smooth=True, name=f"{f.name} seat")
    f.box(TX, -h + 0.02, h - 0.02, 0.02, 0.07, 0.47, 0.92, bevel=0.015, smooth=True, name=f"{f.name} back")
    for x in (-h + 0.03, h - 0.03):
        for y in (0.06, d - 0.04):
            f.cylinder(ME, x, y, 0.0, 0.43, 0.012, name=f"{f.name} leg", verts=10)


def table(f: Frame, piece: dict, top=0.74, slot=WT, legs_slot=ME):
    w, d = f.w, f.d
    f.box(slot, -w / 2, w / 2, 0.0, d, top - 0.035, top, bevel=0.006, name=f"{f.name} top")
    inset = 0.12
    for x in (-w / 2 + inset, w / 2 - inset):
        for y in (inset, d - inset):
            f.box(legs_slot, x - 0.025, x + 0.025, y - 0.025, y + 0.025, 0.0, top - 0.035, name=f"{f.name} leg")


def coffee_table(f: Frame, piece: dict):
    w, d = f.w, f.d
    f.box(WT, -w / 2, w / 2, 0.0, d, 0.36, 0.40, bevel=0.01, name=f"{f.name} top")
    f.box(J, -w / 2 + 0.08, w / 2 - 0.08, 0.08, d - 0.08, 0.0, 0.36, bevel=0.01, name=f"{f.name} base")


def desk(f: Frame, piece: dict):
    """A desk with a chair pulled up to its front."""
    w = f.w
    d = min(f.d, 0.8)
    f.box(J, -w / 2, w / 2, 0.0, d, 0.72, 0.75, bevel=0.006, name=f"{f.name} top")
    for x in (-w / 2 + 0.03, w / 2 - 0.03):
        f.box(J, x - 0.02, x + 0.02, 0.04, d - 0.04, 0.0, 0.72, name=f"{f.name} side")
    f.box(J, -w / 2, w / 2, 0.02, 0.05, 0.1, 0.72, name=f"{f.name} back panel")
    # Chair facing the desk.
    cx, cy = 0.0, d + 0.3
    f.box(TX, cx - 0.23, cx + 0.23, cy - 0.24, cy + 0.24, 0.42, 0.48, bevel=0.02, smooth=True, name=f"{f.name} chair seat")
    f.box(TX, cx - 0.21, cx + 0.21, cy + 0.20, cy + 0.26, 0.48, 0.95, bevel=0.015, smooth=True, name=f"{f.name} chair back")
    f.cylinder(ME, cx, cy, 0.0, 0.42, 0.02, name=f"{f.name} chair stem")
    f.cylinder(ME, cx, cy, 0.0, 0.03, 0.28, name=f"{f.name} chair base")


def tv_unit(f: Frame, piece: dict):
    w, d = f.w, min(f.d, 0.5)
    f.box(J, -w / 2, w / 2, 0.0, d, 0.08, 0.50, bevel=0.006, name=f"{f.name} cabinet")
    for i in range(int(max(1, round(w / 0.9)))):
        a = -w / 2 + i * w / max(1, round(w / 0.9))
        f.box(J, a + 0.015, a + w / max(1, round(w / 0.9)) - 0.015, d, d + 0.004, 0.10, 0.48, name=f"{f.name} door")
    sw = min(1.65, w * 0.7)
    f.box(SCREEN, -sw / 2, sw / 2, 0.0, 0.035, 1.05, 1.05 + sw * 9 / 16, bevel=0.004, name=f"{f.name} screen")


def cabinet(f: Frame, piece: dict, doors=True, shelves=False):
    """Wardrobes, consoles, shelving: a carcass with door lines or open shelves."""
    w, d, h = f.w, f.d, piece["z"][1] - piece["z"][0]
    f.box(J, -w / 2, w / 2, 0.0, d, 0.0, h, bevel=0.004, name=f"{f.name} carcass")
    if shelves:
        for k in range(1, int(h / 0.38)):
            f.box(J, -w / 2 + 0.02, w / 2 - 0.02, 0.02, d, k * 0.38 - 0.015, k * 0.38 + 0.015, name=f"{f.name} shelf")
        return
    if doors:
        n = max(1, round(w / 0.55))
        dw = w / n
        for i in range(n):
            a = -w / 2 + i * dw
            f.box(J, a + 0.006, a + dw - 0.006, d, d + 0.006, 0.02, h - 0.02, name=f"{f.name} door")
            hx = a + dw - 0.08 if i % 2 == 0 else a + 0.08
            f.box(ME, hx - 0.006, hx + 0.006, d + 0.006, d + 0.03, min(h - 0.3, 0.9), min(h - 0.1, 1.1), name=f"{f.name} handle")


def counter(f: Frame, piece: dict, wall_units=False, island=False):
    w, d = f.w, f.d
    base_d = min(d, 0.62) if not island else d
    f.box(J, -w / 2, w / 2, 0.0 if not island else 0.0, base_d - 0.02, 0.1, 0.86, name=f"{f.name} units")
    f.box(J, -w / 2 + 0.02, w / 2 - 0.02, 0.0, 0.08, 0.0, 0.1, name=f"{f.name} plinth")
    f.box(WT, -w / 2 - 0.02, w / 2 + 0.02, 0.0, base_d + 0.02, 0.86, 0.90, bevel=0.004, name=f"{f.name} worktop")
    n = max(1, round(w / 0.6))
    dw = w / n
    front = base_d - 0.02
    for i in range(n):
        a = -w / 2 + i * dw
        f.box(J, a + 0.006, a + dw - 0.006, front, front + 0.006, 0.12, 0.84, name=f"{f.name} door")
        f.box(ME, a + dw / 2 - 0.08, a + dw / 2 + 0.08, front + 0.006, front + 0.025, 0.78, 0.80, name=f"{f.name} handle")
    if island:
        for i in range(n):
            a = -w / 2 + i * dw
            f.box(J, a + 0.006, a + dw - 0.006, -0.006, 0.0, 0.12, 0.84, name=f"{f.name} door")
    if wall_units:
        f.box(J, -w / 2, w / 2, 0.0, 0.35, 1.45, 2.2, name=f"{f.name} wall units")
        for i in range(n):
            a = -w / 2 + i * dw
            f.box(J, a + 0.006, a + dw - 0.006, 0.35, 0.356, 1.47, 2.18, name=f"{f.name} wall door")


def vanity(f: Frame, piece: dict):
    w, d = f.w, min(f.d, 0.55)
    f.box(J, -w / 2, w / 2, 0.0, d - 0.03, 0.30, 0.82, bevel=0.004, name=f"{f.name} cabinet")
    f.box(WT, -w / 2 - 0.01, w / 2 + 0.01, 0.0, d, 0.82, 0.86, bevel=0.004, name=f"{f.name} top")
    n = 2 if "2" in piece["name"] else 1
    for i in range(n):
        cx = -w / 2 + (i + 0.5) * w / n
        f.ellipsoid(SA, cx, d / 2, 0.88, 0.21, 0.17, 0.07, name=f"{f.name} basin")
        f.cylinder(ME, cx, 0.08, 0.86, 1.05, 0.012, name=f"{f.name} tap")
    f.box(MIRROR, -w / 2 + 0.05, w / 2 - 0.05, 0.0, 0.015, 1.15, 2.0, name=f"{f.name} mirror")


def wc(f: Frame, piece: dict):
    f.box(SA, -0.19, 0.19, 0.0, 0.17, 0.0, 0.78, bevel=0.03, smooth=True, subsurf=1, name=f"{f.name} cistern")
    f.ellipsoid(SA, 0.0, 0.40, 0.36, 0.19, 0.27, 0.06, name=f"{f.name} seat")
    f.box(SA, -0.16, 0.16, 0.16, 0.60, 0.0, 0.34, bevel=0.06, smooth=True, subsurf=1, name=f"{f.name} bowl")


def shower(f: Frame, piece: dict):
    w, d = f.w, min(f.d, 0.95)
    f.box(SA, -w / 2, w / 2, 0.0, d, 0.0, 0.04, bevel=0.01, name=f"{f.name} tray")
    f.box(GLASS, -w / 2, w / 2, d - 0.01, d, 0.04, 2.0, name=f"{f.name} screen")
    f.cylinder(ME, 0.0, 0.08, 1.0, 2.05, 0.012, name=f"{f.name} riser")
    f.box(ME, -0.1, 0.1, 0.06, 0.26, 2.05, 2.07, name=f"{f.name} head")


def bathtub(f: Frame, piece: dict):
    w, d = f.w, min(f.d, 0.85)
    f.box(SA, -w / 2, w / 2, 0.0, d, 0.0, 0.58, bevel=0.07, smooth=True, subsurf=1, name=f"{f.name} shell")
    f.box("fixed.#9fb7c2", -w / 2 + 0.1, w / 2 - 0.1, 0.1, d - 0.1, 0.42, 0.56, bevel=0.06, smooth=True, subsurf=1, name=f"{f.name} inside")
    f.cylinder(ME, 0.0, 0.06, 0.58, 0.75, 0.012, name=f"{f.name} tap")


def rug(f: Frame, piece: dict):
    f.box(HI, -f.w / 2, f.w / 2, 0.0, f.d, 0.0, 0.014, bevel=0.005, name=f"{f.name}")


BUILDERS = [
    ("Bed", bed), ("Sofa", sofa), ("Salon sofa", sofa), ("Sitting sofa", sofa), ("Armchair", armchair),
    ("Dining chair", chair), ("BBQ chair", chair), ("Desk and chair", desk), ("TV unit", tv_unit),
    ("Dining table", lambda f, p: table(f, p)), ("BBQ table", lambda f, p: table(f, p, slot=J, legs_slot=J)),
    ("Coffee table", coffee_table), ("Salon table", coffee_table), ("Sitting table", coffee_table),
    ("Wardrobes", cabinet), ("Wardrobe", cabinet), ("Console and mirror", lambda f, p: cabinet(f, p)),
    ("Console", cabinet), ("Bookshelves", lambda f, p: cabinet(f, p, shelves=True)),
    ("Pantry shelves", lambda f, p: cabinet(f, p, shelves=True)), ("Dressing island", lambda f, p: cabinet(f, p)),
    ("Kitchen run", lambda f, p: counter(f, p, wall_units=True)), ("Kitchen counter", counter),
    ("Island", lambda f, p: counter(f, p, island=True)), ("Coffee station", lambda f, p: counter(f, p, wall_units=True)),
    ("Washer and dryer", counter), ("Vanity", vanity), ("WC", wc), ("Shower", shower), ("Bathtub", bathtub), ("Rug", rug),
]


def build_piece(piece: dict, col, get_mat) -> bool:
    """Build the piece with the matching builder; False if none matches."""
    for prefix, fn in BUILDERS:
        if piece["name"].startswith(prefix):
            f = Frame(piece, col, get_mat)
            fn(f, piece)
            return True
    return False
