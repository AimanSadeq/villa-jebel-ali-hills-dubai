"""IFC4 architectural model of Villa 5130272, generated from the brief.

Reads brief/layouts.yaml (rooms, circulation, outlines), brief/massing.yaml
(heights, pool) and brief/site.yaml (location, stamp). Nothing is drawn by hand.

How the building is derived:

  * Walls are the material between the rooms. On each storey, the footprint
    minus every room and corridor leaves the wall zones. The outer 0.25 m ring
    is the external wall; the rest is partitions. Walls around the double height
    living room run the full 9.00 m.
  * Slabs follow the footprints: a ground bearing slab, the first floor slab,
    and roofs at 5.00 m over single storey parts and 9.00 m over the rest, each
    with a 1.20 m parapet (DDA FAQ Q34) except where it meets a taller wall.
  * Doors are placed wherever a room meets the corridor, plus a short list of
    deliberate connections. Windows are placed on every external face of a
    habitable room, sized by orientation from the sun study: generous on the
    courtyard and landscape faces, small and recessed on the hot road and south
    faces.
  * The stair and lift core is a dog leg of two flights with a compact home lift.
    With a 5.00 m ground floor it fits the 18 m2 / 15 m2 core only with 0.90 m
    flights and a 1.0 x 1.0 m lift. Both TO VERIFY, OI-23.

Coordinates are the plot building grid used throughout, in metres, with true
north set on the model context so the orientation is correct in any viewer.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.feature
import ifcopenshell.api.geometry
import ifcopenshell.api.material
import ifcopenshell.api.project
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.style
import ifcopenshell.api.unit
import numpy as np
import yaml
from ifcopenshell.util.shape_builder import ShapeBuilder
from shapely.geometry import MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model.interiors import HUBS, plan as plan_interiors  # noqa: E402
from model.massing import load_massing, site_to_grid  # noqa: E402
from model.site import load_site, plot_polygon  # noqa: E402

LAYOUTS = REPO_ROOT / "brief" / "layouts.yaml"
PROGRAM = REPO_ROOT / "brief" / "program.yaml"
OUT = REPO_ROOT / "output" / "ifc" / "VJH-ARCH-001_Villa_5130272.ifc"

T_EXT = 0.25
T_INT = 0.15

PRINCIPAL = {"living", "dining", "show_kitchen", "majlis", "master_suite", "family_hall",
             "family_living", "bedroom_2", "bedroom_3", "bedroom_4",
             "guest_bedroom"}
SERVICE_WINDOWS = {"home_office", "arabic_kitchen", "maids_room", "laundry",
                   "stair_lift_ground", "stair_lift_first"}
HIGH_WINDOWS = {"guest_powder", "outdoor_bathroom"}
NO_WINDOWS = {"garage", "pantry", "plant_room", "linen_storage"}

DOOR_WIDTH = {"majlis": 1.20, "master_suite": 1.00, "family_living": 1.20,
              "garage": 0.90, "dining": 1.60}

# key, name, RGB, transparency. Neutral concept colours, not finishes.
STYLES = [
    ("ext", "White render", (0.96, 0.95, 0.92), 0.0),
    ("int", "Partition, painted", (0.90, 0.89, 0.86), 0.0),
    ("slab", "Slab, rendered edge", (0.93, 0.92, 0.89), 0.0),
    ("roof", "Roof finish", (0.86, 0.85, 0.82), 0.0),
    ("glass", "Glazing", (0.52, 0.70, 0.80), 0.55),
    ("door", "Timber", (0.58, 0.43, 0.30), 0.0),
    ("pool", "Pool shell", (0.88, 0.89, 0.88), 0.0),
    ("water", "Pool water", (0.22, 0.58, 0.78), 0.35),
    ("deck", "Stone deck", (0.86, 0.81, 0.71), 0.0),
    ("terrain", "Garden ground", (0.78, 0.80, 0.66), 0.0),
    ("stair", "Stair, stone", (0.83, 0.80, 0.75), 0.0),
    ("lift", "Lift car and shaft", (0.40, 0.42, 0.45), 0.0),
    ("space", "Room volume", (0.55, 0.78, 0.62), 0.8),
    ("joinery", "Joinery, light oak", (0.80, 0.70, 0.55), 0.0),
]

# Open plan, D-033 (owner's must-rule): shared spaces join with no partition
# between them. Private rooms keep walls and doors. Where an open join meets the
# double height living room, a bulkhead stays above the lower ceiling to mark
# the edge of the double height.
OPEN_JOINS = {
    # Central hall plan, D-036: the hall opens to the stair, the entrance
    # gallery and the living room; the dining opens to the gallery and the
    # show kitchen. The kitchen keeps a wall to the living room.
    "ground": [("entrance_foyer", "corridor"), ("stair_lift_ground", "entrance_foyer"),
               ("stair_lift_ground", "corridor"), ("entrance_foyer", "living"),
               ("dining", "corridor"), ("show_kitchen", "dining")],
    "first": [("stair_lift_first", "hall_arm"), ("hall_arm", "family_hall"),
              ("family_hall", "family_living")],
}
# Where private rooms take their doors from, in order of preference. On the
# first floor there is no corridor: rooms open off the landing, the family hall
# or the family room itself (D-032).
# HUBS, the rooms private rooms take their doors from, lives in
# src/model/interiors.py so the interiors planner uses the same list.

# Deliberate connections beyond "every room opens off the corridor".
ROOM_LINKS = [
    ("arabic_kitchen", "show_kitchen", 0.90, "door"),
    ("show_kitchen", "dining", 2.40, "opening"),
    ("dining", "living", 3.00, "opening"),
    ("garage", "laundry", 0.90, "door"),
    ("laundry", "maids_room", 0.90, "door"),     # the maid's way into the house
    ("pantry", "arabic_kitchen", 0.90, "door"),  # D-036: pantry beside the kitchens
]
# External doors: room, face, width, height, material. The master suite's
# terrace door (D-035) is added from brief/program.yaml.
EXTERNAL_DOORS = [
    ("entrance_foyer", "W", 1.40, 3.00, "door"),     # front door, road side
    ("garage", "W", 5.00, 2.60, "door"),             # two car overhead door
    ("outdoor_bathroom", "E", 0.90, 2.40, "door"),   # opens to the courtyard, D-028
    ("maids_room", "N", 0.90, 2.40, "door"),         # staff entrance, CLAUDE.md s4
    ("plant_room", "E", 0.90, 2.40, "door"),         # service access
    ("arabic_kitchen", "S", 0.90, 2.40, "door"),     # kitchen service door, D-036
]


@dataclass
class R:
    key: str
    u0: float
    u1: float
    v0: float
    v1: float

    @classmethod
    def of(cls, d):
        return cls(d["key"], d["u"][0], d["u"][1], d["v"][0], d["v"][1])

    @property
    def poly(self):
        return box(self.u0, self.v0, self.u1, self.v1)

    @property
    def area(self):
        return (self.u1 - self.u0) * (self.v1 - self.v0)


def clean(geom, tol=0.003):
    """Drop the slivers that rounding leaves along shared edges."""
    g = geom.buffer(-tol, join_style=2).buffer(tol, join_style=2)
    parts = [g] if isinstance(g, Polygon) else list(getattr(g, "geoms", []))
    return [p for p in parts if p.area > 0.02]


class Model:
    def __init__(self):
        self.lay = yaml.safe_load(LAYOUTS.read_text(encoding="utf-8"))
        self.prog = yaml.safe_load(PROGRAM.read_text(encoding="utf-8"))
        self.m = load_massing()
        self.site = load_site()
        h = self.m["heights"]
        self.HG = float(h["ground_floor_m"])
        self.HF = float(h["first_floor_m"])
        self.PAR = float(h["parapet_m"])
        self.SLAB = float(h.get("slab_m", 0.30))
        self.SERV = float(h.get("services_zone_m", 0.15))
        self.names = {r["key"]: r["name"]
                      for f in ("ground", "first") for r in self.prog[f]}
        self.names.update({"corridor": "Corridor", "hall_link": "Link hall",
                           "family_hall": "Family hall", "hall_arm": "Stair landing"})
        self.f = ifcopenshell.file(schema="IFC4")
        self.b = ShapeBuilder(self.f)
        self.walls: dict[str, list] = {"ground": [], "first": []}
        self.bridges: dict[str, list] = {"ground": [], "first": []}
        self.no_hub_door: list[tuple[str, str, str]] = []
        # Interiors, D-034 and D-035: en-suites, wardrobes, the master suite.
        self.icfg = self.prog["interiors"]
        self.interiors = plan_interiors(self.lay, self.prog)
        terrace = self.icfg["master_suite"]["terrace"]
        self.external_doors = EXTERNAL_DOORS + [
            ("master_suite", "E", terrace["door_width_m"], terrace["door_height_m"],
             "glass")]
        self.counts: dict[str, int] = {}

    # Setup -----------------------------------------------------------------

    def setup(self):
        f = self.f
        stamp = self.site["meta"]["stamp"]
        self.project = ifcopenshell.api.root.create_entity(
            f, ifc_class="IfcProject", name="Villa 5130272")
        self.project.Description = stamp
        length = ifcopenshell.api.unit.add_si_unit(f, unit_type="LENGTHUNIT")
        area = ifcopenshell.api.unit.add_si_unit(f, unit_type="AREAUNIT")
        volume = ifcopenshell.api.unit.add_si_unit(f, unit_type="VOLUMEUNIT")
        angle = ifcopenshell.api.unit.add_si_unit(f, unit_type="PLANEANGLEUNIT")
        ifcopenshell.api.unit.assign_unit(f, units=[length, area, volume, angle])

        model = ifcopenshell.api.context.add_context(f, context_type="Model")
        self.body = ifcopenshell.api.context.add_context(
            f, context_type="Model", context_identifier="Body",
            target_view="MODEL_VIEW", parent=model)
        # True north in the grid frame: the grid's v axis runs on bearing 30.18,
        # so north sits 30.18 degrees anticlockwise from it.
        bearing = math.radians(float(self.m["grid"]["bearing_deg"]))
        model.TrueNorth = f.createIfcDirection((-math.sin(bearing), math.cos(bearing)))

        pset = ifcopenshell.api.pset.add_pset(f, product=self.project,
                                              name="VJH_ConceptDesign")
        ifcopenshell.api.pset.edit_pset(f, pset=pset, properties={
            "Stamp": stamp, "Phase": "3", "Plot": self.site["plot"]["number"],
            "GridBearingDeg": float(self.m["grid"]["bearing_deg"]),
            "Source": "Generated by src/model/architecture.py from brief/*.yaml",
        })

        self.ifc_site = ifcopenshell.api.root.create_entity(
            f, ifc_class="IfcSite", name=f"Plot {self.site['plot']['number']}")
        loc = self.site["location"]
        self.ifc_site.RefLatitude = self._dms(float(loc["latitude"]))
        self.ifc_site.RefLongitude = self._dms(float(loc["longitude"]))
        self.ifc_site.RefElevation = 0.0
        self.building = ifcopenshell.api.root.create_entity(
            f, ifc_class="IfcBuilding", name="Villa 5130272")
        ifcopenshell.api.aggregate.assign_object(f, products=[self.ifc_site],
                                                 relating_object=self.project)
        ifcopenshell.api.aggregate.assign_object(f, products=[self.building],
                                                 relating_object=self.ifc_site)
        for obj in (self.ifc_site, self.building):
            ifcopenshell.api.geometry.edit_object_placement(f, product=obj)

        self.storeys = {}
        for key, name, elev in (("ground", "Ground Floor", 0.0),
                                ("first", "First Floor", self.HG),
                                ("roof", "Roof", self.HG + self.HF)):
            st = ifcopenshell.api.root.create_entity(
                f, ifc_class="IfcBuildingStorey", name=name)
            st.Elevation = elev
            ifcopenshell.api.aggregate.assign_object(f, products=[st],
                                                     relating_object=self.building)
            ifcopenshell.api.geometry.edit_object_placement(
                f, product=st, matrix=self._at(elev))
            self.storeys[key] = (st, elev)

        # Surface styles, so the model reads correctly in any viewer and in
        # Blender. Colours are neutral concept colours, not finishes: the three
        # interior palettes come in Phase 4.
        self.style = {}
        for key, name, rgb, transparency in STYLES:
            st = ifcopenshell.api.style.add_style(f, name=name)
            ifcopenshell.api.style.add_surface_style(
                f, style=st, ifc_class="IfcSurfaceStyleShading", attributes={
                    "SurfaceColour": {"Name": None, "Red": rgb[0], "Green": rgb[1],
                                      "Blue": rgb[2]},
                    "Transparency": transparency})
            self.style[key] = st

        self.mat = {}
        for key, name, cat in (("ext", "Masonry, white render", "block"),
                               ("int", "Blockwork partition", "block"),
                               ("slab", "Reinforced concrete", "concrete"),
                               ("glass", "Glazing", "glass"),
                               ("door", "Timber door", "wood"),
                               ("pool", "Concrete pool shell", "concrete"),
                               ("deck", "Stone deck", "stone")):
            self.mat[key] = ifcopenshell.api.material.add_material(f, name=name,
                                                                   category=cat)
            ifcopenshell.api.style.assign_material_style(
                f, material=self.mat[key], style=self.style[key], context=self.body)

    @staticmethod
    def _dms(deg):
        sign = -1 if deg < 0 else 1
        deg = abs(deg)
        d = int(deg)
        m = int((deg - d) * 60)
        s = int(((deg - d) * 60 - m) * 60)
        ms = int(round(((((deg - d) * 60 - m) * 60) - s) * 1e6))
        return (sign * d, sign * m, sign * s, sign * ms)

    @staticmethod
    def _at(z):
        mat = np.eye(4)
        mat[2, 3] = z
        return mat

    # Element helpers -------------------------------------------------------

    def _prism(self, poly: Polygon, z0: float, h: float):
        # Drop zero length edges left where unions meet (a repeated vertex
        # makes the profile invalid and the solid fails to build).
        poly = poly.simplify(0.0005)
        outer = self.b.polyline([tuple(c) for c in list(poly.exterior.coords)[:-1]],
                                closed=True)
        inners = [self.b.polyline([tuple(c) for c in list(i.coords)[:-1]], closed=True)
                  for i in poly.interiors]
        prof = self.b.profile(outer, inner_curves=inners)
        return self.b.extrude(prof, magnitude=h, position=(0.0, 0.0, z0))

    def element(self, ifc_class, name, storey_key, items, predefined=None,
                object_type=None, material=None, container=True, style=None):
        f = self.f
        e = ifcopenshell.api.root.create_entity(f, ifc_class=ifc_class, name=name,
                                                predefined_type=predefined)
        if object_type:
            e.ObjectType = object_type
        st, elev = self.storeys[storey_key] if storey_key else (self.ifc_site, 0.0)
        if container:
            ifcopenshell.api.spatial.assign_container(f, products=[e],
                                                      relating_structure=st)
        ifcopenshell.api.geometry.edit_object_placement(f, product=e,
                                                        matrix=self._at(elev))
        rep = self.b.get_representation(self.body, items)
        ifcopenshell.api.geometry.assign_representation(f, product=e,
                                                        representation=rep)
        style = style or material
        if style is not None:
            ifcopenshell.api.style.assign_representation_styles(
                f, shape_representation=rep, styles=[self.style[style]])
        if material is not None:
            ifcopenshell.api.material.assign_material(f, products=[e],
                                                      material=self.mat[material])
        self.counts[ifc_class] = self.counts.get(ifc_class, 0) + 1
        return e

    # Geometry from the layout ----------------------------------------------

    def footprints(self):
        lay = self.lay
        self.road = Polygon(lay["outlines"]["road_ground"])
        p = lay["plates"]["ssw"]
        self.ssw = box(p["u"][0], p["v"][0], p["u"][1], p["v"][1])
        self.first_fp = Polygon(lay["outlines"]["first"])
        self.g_rooms = [R.of(d) for d in lay["floors"]["ground"]["rooms"]]
        self.f_rooms = [R.of(d) for d in lay["floors"]["first"]["rooms"]]
        self.g_circ = [R.of(d) for d in lay["floors"]["ground"]["circulation"]]
        self.f_circ = [R.of(d) for d in lay["floors"]["first"]["circulation"]]
        self.voids = [R.of(d) for d in lay["floors"]["first"].get("voids", [])
                      if d["area_m2"] > 0.01]
        living = next(r for r in self.g_rooms if r.key == "living")
        self.living = living
        if "living" in lay["plates"]:
            # Central hall plan, D-036: the living room is a tall block of its
            # own, sharing the SSW wing's north wall.
            p = lay["plates"]["living"]
            self.living_block = box(p["u"][0], p["v"][0], p["u"][1], p["v"][1])
            self.kitchen_block = self.ssw
        else:
            # Wing plans: the SSW wing splits into the single storey kitchen
            # block and the double height living block at the living's partition.
            cut = living.u0 - T_INT
            self.kitchen_block = box(self.ssw.bounds[0], self.ssw.bounds[1], cut,
                                     self.ssw.bounds[3])
            self.living_block = box(cut, self.ssw.bounds[1], self.ssw.bounds[2],
                                    self.ssw.bounds[3])
        self.g_fp = unary_union([self.road, self.ssw, self.living_block])

    # Walls -------------------------------------------------------------------

    def open_bridges(self, storey, rooms, circ):
        """The partitions removed by the open joins, as (owner key, polygon).

        Each bridge is the gap between two rooms over their shared length. Where
        bridges meet at a T, the small square of partition left between them is
        bridged too, so no stub of wall stands in the open space.
        """
        by_key = {r.key: r for r in rooms + circ}
        out = []
        for a_key, b_key in OPEN_JOINS[storey]:
            a, b = by_key.get(a_key), by_key.get(b_key)
            if not a or not b:
                continue
            if a.poly.touches(b.poly) or a.poly.intersects(b.poly):
                continue                       # already one open space
            s = self._shared(a, b)
            if not s:
                raise ValueError(f"open join {a_key} / {b_key}: no shared wall")
            along_u, (u, v), t, length = s
            lo = max(a.u0, b.u0) if along_u else max(a.v0, b.v0)
            hi = lo + length
            gap = (box(lo, v - t / 2, hi, v + t / 2) if along_u
                   else box(u - t / 2, lo, u + t / 2, hi))
            out.append((a_key, gap))
        interior = unary_union([r.poly for r in rooms + circ] + [g for _, g in out])
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                (ka, ga), (_, gb) = out[i], out[j]
                if ga.distance(gb) > T_EXT:
                    continue
                hull = unary_union([ga, gb]).envelope
                stub = hull.difference(interior)
                if 0 < stub.area < 0.05:
                    out.append((ka, stub))
                    interior = interior.union(stub)
        return out

    def walls_for(self, storey, footprint, rooms, circ, voids, z_top,
                  tall_zone=None, tall_top=None):
        bridges = self.open_bridges(storey, rooms, circ)
        self.bridges[storey] = bridges
        interior = unary_union([r.poly for r in rooms + circ + voids]
                               + [g for _, g in bridges])
        wall_zone = footprint.difference(interior)
        if tall_zone is not None:
            for _, g in bridges:
                for poly in clean(g.intersection(tall_zone), tol=0.001):
                    self.element("IfcWall", "Bulkhead, edge of the double height",
                                 storey, [self._prism(poly, self.HG - self.SLAB,
                                                      tall_top - (self.HG - self.SLAB))],
                                 predefined="PARTITIONING", material="int")
        ext_ring = footprint.difference(footprint.buffer(-T_EXT, join_style=2,
                                                         mitre_limit=10))
        internal = wall_zone.difference(ext_ring)
        groups = [("ext", True, ext_ring), ("int", False, internal)]
        for mat, is_ext, zone in groups:
            parts = [(zone, z_top)]
            if tall_zone is not None:
                parts = [(zone.difference(tall_zone), z_top),
                         (zone.intersection(tall_zone), tall_top)]
            for geom, top in parts:
                for poly in clean(geom):
                    kind = "external" if is_ext else "partition"
                    w = self.element("IfcWall", f"Wall, {kind}, {storey}", storey,
                                     [self._prism(poly, 0.0, top)],
                                     predefined="SOLIDWALL" if is_ext else "PARTITIONING",
                                     material=mat)
                    pset = ifcopenshell.api.pset.add_pset(self.f, product=w,
                                                          name="Pset_WallCommon")
                    ifcopenshell.api.pset.edit_pset(self.f, pset=pset,
                                                    properties={"IsExternal": is_ext})
                    self.walls[storey].append((w, poly, is_ext))
        return ext_ring

    def build_walls(self):
        tall = self.living.poly.buffer(0.30, join_style=2)
        self.ext_ring_g = self.walls_for(
            "ground", self.g_fp, self.g_rooms, self.g_circ, [],
            z_top=self.HG - self.SLAB, tall_zone=tall,
            tall_top=self.HG + self.HF - self.SLAB)
        self.ext_ring_f = self.walls_for(
            "first", self.first_fp, self.f_rooms, self.f_circ, self.voids,
            z_top=self.HF - self.SLAB)
        # Interior partitions, full height to the slab above.
        for it in self.interiors.values():
            top = (self.HG if it.storey == "ground" else self.HF) - self.SLAB
            for g in it.partitions:
                for poly in clean(g):
                    w = self.element("IfcWall",
                                     f"Partition, {self.names.get(it.room, it.room)}",
                                     it.storey, [self._prism(poly, 0.0, top)],
                                     predefined="PARTITIONING", material="int")
                    self.walls[it.storey].append((w, poly, False))

    # Slabs, roofs, parapets ------------------------------------------------

    def build_slabs(self):
        S = self.SLAB
        top = self.HG + self.HF
        self.element("IfcSlab", "Ground bearing slab", "ground",
                     [self._prism(p, -S, S) for p in clean(self.g_fp)],
                     predefined="BASESLAB", material="slab")
        # Where the first floor ends a few centimetres short of the ground floor
        # (packer rounding), the slab runs on over the strip rather than leaving
        # a sliver of roof: a shadow gap under the upper wall, no extra GFA.
        low = self.road.difference(self.first_fp)
        self.low_road = low.buffer(-0.15, join_style=2).buffer(0.15, join_style=2)
        sliver = low.difference(self.low_road)
        first_floor = unary_union([self.first_fp, sliver])
        for v in self.voids:
            first_floor = first_floor.difference(v.poly)
        # Stairwell and lift shaft pass through: see build_core.
        first_floor = first_floor.difference(self.stairwell).difference(self.shaft)
        self.element("IfcSlab", "First floor slab", "first",
                     [self._prism(p, -S, S) for p in clean(first_floor)],
                     predefined="FLOOR", material="slab")

        roofs = [
            ("Main roof", "roof", self.first_fp, 0.0, [self.living_block]),
            ("Roof over the garage and service end", "first",
             self.low_road, 0.0, [self.first_fp]),
            ("Roof terrace over the kitchen, master suite terrace",
             "first", self.kitchen_block, 0.0,
             [self.first_fp, self.living_block]),
            ("Roof over the double height living room", "roof", self.living_block,
             0.0, [self.first_fp]),
        ]
        for name, storey, poly, _, taller in roofs:
            parts = clean(poly)
            if not parts:
                continue
            self.element("IfcSlab", name, storey,
                         [self._prism(p, -S, S) for p in parts],
                         predefined="ROOF", material="slab",
                         style="deck" if "terrace" in name else "roof")
            ring = unary_union(parts)
            ring = ring.difference(ring.buffer(-T_EXT, join_style=2, mitre_limit=10))
            for t in taller:
                ring = ring.difference(t.buffer(0.01, join_style=2))
            for p in clean(ring):
                self.element("IfcWall", f"Parapet, {name.lower()}", storey,
                             [self._prism(p, 0.0, self.PAR)],
                             predefined="PARAPET", material="ext")

    # Stair and lift core ---------------------------------------------------

    def build_core(self):
        g = next(r for r in self.g_rooms if r.key == "stair_lift_ground")
        u0, u1, v0 = g.u0, g.u1, g.v0
        flight_w, lift = 0.90, 1.00
        rise_total = self.HG
        risers = math.ceil(rise_total / 0.18)
        if risers % 2:
            risers += 1
        riser = rise_total / risers
        per_flight = risers // 2
        going = 0.28
        run = (per_flight - 1) * going
        landing = (u1 - u0) - run - 0.05
        self.core_note = (f"{risers} risers of {riser * 1000:.0f} mm, going "
                          f"{going * 1000:.0f} mm, two flights {flight_w:.2f} m wide, "
                          f"half landing {landing:.2f} m, lift {lift:.2f} x {lift:.2f} m")
        if landing < flight_w:
            raise ValueError(f"stair does not fit the core: landing {landing:.2f} m")

        def flight(u_start, direction, lane_v0, z0):
            steps = []
            for i in range(per_flight - 1):
                ua = u_start + direction * i * going
                ub = ua + direction * going
                lo, hi = min(ua, ub), max(ua, ub)
                steps.append(self._prism(box(lo, lane_v0, hi, lane_v0 + flight_w),
                                         z0, riser * (i + 1)))
            return steps

        # Flight 1 rises from the corridor side towards the west, flight 2
        # returns east to the first floor, beside it.
        f1 = flight(u1 - 0.05, -1, v0 + flight_w + 0.05, 0.0)
        z_land = riser * per_flight
        f2 = flight(u0 + landing, +1, v0, z_land)
        land = self._prism(box(u0, v0, u0 + landing, v0 + 2 * flight_w + 0.05),
                           z_land - 0.20, 0.20)
        stair = self.element("IfcStair", "Main stair", "ground", f1 + f2 + [land],
                             predefined="HALF_TURN_STAIR", material="slab",
                             style="stair")
        ifcopenshell.api.pset.edit_pset(
            self.f, pset=ifcopenshell.api.pset.add_pset(self.f, product=stair,
                                                        name="Pset_StairCommon"),
            properties={"NumberOfRiser": risers, "RiserHeight": riser,
                        "TreadLength": going})
        self.stairwell = box(u0, v0, u1, v0 + 2 * flight_w + 0.05)

        self.shaft = box(u1 - lift, v0 + 2 * flight_w + 0.10, u1,
                         v0 + 2 * flight_w + 0.10 + lift)
        first_core = next(r for r in self.f_rooms if r.key == "stair_lift_first")
        for room in (g, first_core):
            if not room.poly.contains(self.stairwell.union(self.shaft)):
                raise ValueError(f"stair and lift do not fit {room.key}")
        self.element("IfcTransportElement", "Home lift", "ground",
                     [self._prism(self.shaft, 0.0, self.HG + self.HF - self.SLAB)],
                     predefined="ELEVATOR", style="lift")

    # Spaces ------------------------------------------------------------------

    def build_spaces(self):
        clear_g = self.HG - self.SLAB - self.SERV
        clear_f = self.HF - self.SLAB - self.SERV
        clear_living = self.HG + self.HF - self.SLAB - self.SERV
        for storey, rooms, circ, clear in (("ground", self.g_rooms, self.g_circ, clear_g),
                                           ("first", self.f_rooms, self.f_circ, clear_f)):
            for r in rooms + circ:
                h = clear_living if r.key == "living" else clear
                it = self.interiors.get(r.key)
                shape = unary_union([it.main if it else r.poly]
                                    + [g for k, g in self.bridges[storey] if k == r.key])
                parts = [shape] if isinstance(shape, Polygon) else list(shape.geoms)
                sp = self.element("IfcSpace", self.names.get(r.key, r.key), storey,
                                  [self._prism(q, 0.0, h) for q in parts],
                                  predefined="INTERNAL", container=False,
                                  style="space")
                sp.LongName = r.key
                ifcopenshell.api.aggregate.assign_object(
                    self.f, products=[sp], relating_object=self.storeys[storey][0])
                qto = ifcopenshell.api.pset.add_qto(self.f, product=sp,
                                                    name="Qto_SpaceBaseQuantities")
                ifcopenshell.api.pset.edit_qto(self.f, qto=qto, properties={
                    "NetFloorArea": round(it.main.area if it else r.area, 3),
                    "Height": round(h, 3)})
                for part in (it.parts if it else []):
                    if part.kind != "space":
                        continue
                    sub = self.element("IfcSpace", part.name, storey,
                                       [self._prism(part.poly, 0.0, h)],
                                       predefined="INTERNAL", container=False,
                                       style="space")
                    sub.LongName = part.key
                    ifcopenshell.api.aggregate.assign_object(
                        self.f, products=[sub], relating_object=self.storeys[storey][0])
                    q = ifcopenshell.api.pset.add_qto(self.f, product=sub,
                                                      name="Qto_SpaceBaseQuantities")
                    ifcopenshell.api.pset.edit_qto(self.f, qto=q, properties={
                        "NetFloorArea": round(part.poly.area, 3), "Height": round(h, 3)})

    # Openings ----------------------------------------------------------------

    def host(self, storey, point):
        for w, poly, _ in self.walls[storey]:
            if poly.buffer(0.02).contains(point):
                return w
        return None

    def opening(self, storey, kind, name, u_c, v_c, along_u, width, sill, height,
                wall_t, material=None):
        """Cut an opening through the host wall and fill it."""
        if along_u:   # wall runs along u, so the opening spans u
            cut = box(u_c - width / 2, v_c - wall_t / 2 - 0.05,
                      u_c + width / 2, v_c + wall_t / 2 + 0.05)
            pane = box(u_c - width / 2, v_c - 0.03, u_c + width / 2, v_c + 0.03)
        else:
            cut = box(u_c - wall_t / 2 - 0.05, v_c - width / 2,
                      u_c + wall_t / 2 + 0.05, v_c + width / 2)
            pane = box(u_c - 0.03, v_c - width / 2, u_c + 0.03, v_c + width / 2)
        w = self.host(storey, Point(u_c, v_c))
        if w is None:
            self.counts["unhosted"] = self.counts.get("unhosted", 0) + 1
            return None
        op = self.element("IfcOpeningElement", f"Opening for {name}", storey,
                          [self._prism(cut, sill, height)], container=False)
        ifcopenshell.api.feature.add_feature(self.f, feature=op, element=w)
        if kind == "opening":
            return op
        cls = "IfcDoor" if kind == "door" else "IfcWindow"
        fill = self.element(cls, name, storey, [self._prism(pane, sill, height)],
                            material=material or ("door" if cls == "IfcDoor" else "glass"))
        fill.OverallWidth = width
        fill.OverallHeight = height
        ifcopenshell.api.feature.add_filling(self.f, opening=op, element=fill)
        return fill

    @staticmethod
    def _shared(a: R, b: R):
        """Shared wall between two rectangles: (along_u, centre, wall_t, length)."""
        for gap in (T_INT, T_EXT):
            if abs(b.u0 - a.u1 - gap) < 2e-3 or abs(a.u0 - b.u1 - gap) < 2e-3:
                lo, hi = max(a.v0, b.v0), min(a.v1, b.v1)
                u = (a.u1 + b.u0) / 2 if abs(b.u0 - a.u1 - gap) < 2e-3 else (b.u1 + a.u0) / 2
                if hi - lo > 0:
                    return False, (u, (lo + hi) / 2), gap, hi - lo
            if abs(b.v0 - a.v1 - gap) < 2e-3 or abs(a.v0 - b.v1 - gap) < 2e-3:
                lo, hi = max(a.u0, b.u0), min(a.u1, b.u1)
                v = (a.v1 + b.v0) / 2 if abs(b.v0 - a.v1 - gap) < 2e-3 else (b.v1 + a.v0) / 2
                if hi - lo > 0:
                    return True, ((lo + hi) / 2, v), gap, hi - lo
        return None

    def build_doors(self):
        for storey, rooms, circ in (("ground", self.g_rooms, self.g_circ),
                                    ("first", self.f_rooms, self.f_circ)):
            door_h = 2.70 if storey == "ground" else 2.40
            open_pairs = {frozenset(p) for p in OPEN_JOINS[storey]}
            everything = {r.key: r for r in rooms + circ}
            hubs = [everything[k] for k in HUBS if k in everything]
            for r in rooms:
                if r.key in ("living", "dining", "show_kitchen", "outdoor_bathroom"):
                    continue      # open plan, or reached from outside
                if r.key in HUBS or any(r.key in p for p in open_pairs):
                    continue      # part of the open space
                it = self.interiors.get(r.key)
                if it:
                    for d in it.doors:
                        self.opening(storey, "door", d.name, d.u, d.v, d.along_u,
                                     d.width, 0.0, min(door_h, 2.40), d.wall_t)
                    if it.entry:
                        e = it.entry
                        self.opening(storey, "door", e.name, e.u, e.v, e.along_u,
                                     e.width, 0.0, door_h, e.wall_t)
                        continue
                for hub in hubs:
                    s = self._shared(r, hub)
                    if s and s[3] >= 1.0:
                        along_u, (u, v), t, length = s
                        wdt = min(DOOR_WIDTH.get(r.key, 0.90), length - 0.2)
                        self.opening(storey, "door", f"Door, {self.names.get(r.key, r.key)}",
                                     u, v, along_u, wdt, 0.0, door_h, t)
                        break
                else:
                    # Acceptable only when the room is reached another way: a
                    # deliberate link (the garage through the laundry) or its
                    # own external door. Anything else is a room with no way in.
                    linked = any(r.key in (x, y) for x, y, _, _ in ROOM_LINKS)
                    outside = any(r.key == k for k, *_ in EXTERNAL_DOORS)
                    if not (linked or outside):
                        raise ValueError(f"{r.key} on the {storey} floor has no door")
                    self.no_hub_door.append((storey, r.key, "link" if linked else "external door"))
            for a_key, b_key, wdt, kind in ROOM_LINKS:
                a, b = everything.get(a_key), everything.get(b_key)
                if not a or not b or frozenset((a_key, b_key)) in open_pairs:
                    continue
                s = self._shared(a, b)
                if s:
                    along_u, (u, v), t, length = s
                    self.opening(storey, kind,
                                 f"{'Door' if kind == 'door' else 'Opening'}, "
                                 f"{self.names[a_key]} to {self.names[b_key]}",
                                 u, v, along_u, min(wdt, length - 0.2), 0.0, door_h, t)

    def _external_faces(self, storey, r: R, ring):
        """Which faces of a room sit against the external wall."""
        probes = {"W": (r.u0 - 0.10, (r.v0 + r.v1) / 2, False, r.v1 - r.v0, r.u0 - T_EXT / 2),
                  "E": (r.u1 + 0.10, (r.v0 + r.v1) / 2, False, r.v1 - r.v0, r.u1 + T_EXT / 2),
                  "S": ((r.u0 + r.u1) / 2, r.v0 - 0.10, True, r.u1 - r.u0, r.v0 - T_EXT / 2),
                  "N": ((r.u0 + r.u1) / 2, r.v1 + 0.10, True, r.u1 - r.u0, r.v1 + T_EXT / 2)}
        out = {}
        for face, (pu, pv, along_u, length, wall_line) in probes.items():
            if ring.buffer(0.01).contains(Point(pu, pv)):
                out[face] = (along_u, length, wall_line)
        return out

    def _face_segments(self, r: R, face: str, along_u: bool):
        """Split an external face by what lies behind it: the room itself
        ("main"), an en-suite or master bathroom ("bath"), or a walk-in
        wardrobe ("wir"). Partitions are taken out of the main stretches."""
        w0, w1 = (r.u0, r.u1) if along_u else (r.v0, r.v1)
        it = self.interiors.get(r.key)
        if not it:
            return [("main", w0, w1)]
        p = self.icfg["partition_m"]
        line = {"W": r.u0, "E": r.u1, "S": r.v0, "N": r.v1}[face]
        idx = {"W": 0, "S": 1, "E": 2, "N": 3}[face]
        out, taken = [], []
        for part in it.parts:
            if part.kind != "space":
                continue
            b = part.poly.bounds
            if abs(b[idx] - line) > 1e-3:
                continue
            a0, a1 = (b[0], b[2]) if along_u else (b[1], b[3])
            out.append(("bath" if part.key.endswith("bathroom") else "wir", a0, a1))
            taken.append((a0 - p, a1 + p))
        free = [(w0, w1)]
        for a, b2 in taken:
            nxt = []
            for x, y in free:
                if b2 <= x or a >= y:
                    nxt.append((x, y))
                    continue
                if a > x:
                    nxt.append((x, a))
                if b2 < y:
                    nxt.append((b2, y))
            free = nxt
        return out + [("main", x, y) for x, y in free if y - x > 0.3]

    def build_furniture(self):
        """Built-in wardrobes and the master's coffee station."""
        for it in self.interiors.values():
            for part in it.parts:
                if part.kind not in ("wardrobe", "furniture"):
                    continue
                self.element("IfcFurniture", part.name, it.storey,
                             [self._prism(part.poly, 0.0, part.height)],
                             predefined="USERDEFINED",
                             object_type=("Built-in wardrobe" if part.kind == "wardrobe"
                                          else part.name),
                             style="joinery")

    def _face_kind(self, r: R, face: str) -> str:
        if r.key == "living" and "living" in self.lay["plates"]:
            return {"N": "courtyard", "E": "landscape", "S": "hot", "W": "inner"}[face]
        in_ssw = self.ssw.buffer(0.01).contains(r.poly)
        if in_ssw:
            return {"N": "courtyard", "E": "landscape", "S": "hot", "W": "inner"}[face]
        return {"E": "courtyard", "W": "hot", "S": "hot", "N": "north"}[face]

    def build_windows_and_external_doors(self):
        lived_in = [c for c in self.f_circ if c.key == "family_hall"]
        for storey, rooms, ring in (("ground", self.g_rooms, self.ext_ring_g),
                                    ("first", self.f_rooms + lived_in, self.ext_ring_f)):
            ground = storey == "ground"
            clear = (self.HG if ground else self.HF) - self.SLAB - self.SERV
            ext_doors = {(k, face): (w, h, m) for k, face, w, h, m in self.external_doors}
            for r in rooms:
                faces = self._external_faces(storey, r, ring)
                for face, (along_u, length, wall_line) in faces.items():
                    segs = self._face_segments(r, face, along_u)
                    for kind_s, a0, a1 in segs:
                        if kind_s == "bath" and a1 - a0 >= 0.9:
                            mid = (a0 + a1) / 2
                            ub, vb = ((mid, wall_line) if along_u else (wall_line, mid))
                            self.opening(storey, "window",
                                         f"Window, {self.names.get(r.key, r.key)}, bathroom",
                                         ub, vb, along_u, 0.60, 1.80, 0.60, T_EXT)
                    mains = [x for x in segs if x[0] == "main"]
                    if not mains:
                        continue
                    _, s0, s1 = max(mains, key=lambda x: x[2] - x[1])
                    length = s1 - s0
                    centre = (s0 + s1) / 2
                    u_c, v_c = ((centre, wall_line) if along_u else (wall_line, centre))
                    door = ext_doors.get((r.key, face))
                    if door:
                        wdt, hgt, mat = door
                        name = ("Front door" if r.key == "entrance_foyer" else
                                "Terrace door, Master Suite" if mat == "glass" else
                                f"External door, {self.names.get(r.key, r.key)}")
                        # Share the face with a window when the room has one.
                        if (r.key in PRINCIPAL | SERVICE_WINDOWS and length > wdt + 2.0
                                and mat != "glass"):
                            centre_d = s0 + length / 3
                            centre_w = s0 + 2 * length / 3
                            ud, vd = ((centre_d, wall_line) if along_u else (wall_line, centre_d))
                            self.opening(storey, "door", name, ud, vd, along_u, wdt,
                                         0.0, hgt, T_EXT)
                            uw_, vw_ = ((centre_w, wall_line) if along_u else (wall_line, centre_w))
                            self.opening(storey, "window",
                                         f"Window, {self.names.get(r.key, r.key)}", uw_, vw_,
                                         along_u, min(0.9, length / 3 - 0.3), 1.0, 1.4, T_EXT)
                        else:
                            self.opening(storey, "door", name, u_c, v_c, along_u, wdt,
                                         0.0, hgt, T_EXT, material=mat)
                        continue
                    if r.key in NO_WINDOWS or r.key == "entrance_foyer":
                        continue
                    kind = self._face_kind(r, face)
                    if kind == "inner":
                        continue
                    if r.key in HIGH_WINDOWS:
                        wdt, sill, hgt = 0.60, 1.80, 0.60
                    elif r.key in PRINCIPAL and kind in ("courtyard", "landscape"):
                        wdt = min(0.75 * length, 6.0)
                        sill = 0.15 if ground else 0.90     # DDA FAQ Q35 upstairs
                        hgt = clear - 0.30 - sill
                    elif kind == "hot":
                        wdt, sill = min(0.35 * length, 1.80), 0.90
                        hgt = 1.80
                    elif kind == "north":
                        wdt, sill = min(0.50 * length, 2.40), 0.90
                        hgt = 1.80
                    else:
                        wdt, sill = min(0.40 * length, 1.20), 1.00
                        hgt = 1.40
                    wdt = min(wdt, length - 0.60)
                    if wdt < 0.5:
                        continue
                    self.opening(storey, "window",
                                 f"Window, {self.names.get(r.key, r.key)}, {kind}",
                                 u_c, v_c, along_u, wdt, sill, hgt, T_EXT)

    # Site, pool, deck ------------------------------------------------------

    def build_site(self):
        plot = site_to_grid(plot_polygon())
        self.element("IfcGeographicElement", "Plot terrain", None,
                     [self._prism(plot, -0.45, 0.30)], predefined="TERRAIN",
                     container=True, style="terrain")
        spec = self.lay if self.lay.get("pool") else next(
            o for o in self.m["options"] if o["key"] == "C")
        (pu0, pu1), (pv0, pv1) = spec["pool"]["u"], spec["pool"]["v"]
        (du0, du1), (dv0, dv1) = spec["deck"]["u"], spec["deck"]["v"]
        pool = box(pu0, pv0, pu1, pv1)
        shell = pool.buffer(T_EXT, join_style=2)
        depth = 1.50
        if self.g_fp.buffer(-0.01).intersects(box(du0, dv0, du1, dv1)):
            raise ValueError("pool deck clashes with the building")
        self.element("IfcBuildingElementProxy", "Swimming pool shell", None,
                     [self._prism(shell.difference(pool), -depth - T_EXT, depth + T_EXT),
                      self._prism(pool, -depth - T_EXT, T_EXT)],
                     object_type="Swimming pool, 10 x 4 m", material="pool")
        water = self.element("IfcSpace", "Swimming pool water", None,
                             [self._prism(pool, -depth, depth - 0.15)],
                             predefined="EXTERNAL", container=False,
                             style="water")
        water.LongName = "pool_water"
        ifcopenshell.api.aggregate.assign_object(self.f, products=[water],
                                                 relating_object=self.ifc_site)
        deck = box(du0, dv0, du1, dv1).difference(shell)
        self.element("IfcSlab", "Pool deck", None, [self._prism(deck, -0.15, 0.15)],
                     predefined="USERDEFINED", object_type="Pool deck",
                     material="deck")

    # Build ---------------------------------------------------------------------

    def build(self) -> Path:
        self.setup()
        self.footprints()
        self.build_core()
        self.build_walls()
        self.build_slabs()
        self.build_spaces()
        self.build_doors()
        self.build_windows_and_external_doors()
        self.build_furniture()
        self.build_site()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        self.f.write(str(OUT))
        return OUT


def main() -> int:
    m = Model()
    out = m.build()
    print(f"IFC  {out.relative_to(REPO_ROOT)}")
    print(f"     core: {m.core_note}")
    for k in sorted(m.counts):
        print(f"     {k:<26}{m.counts[k]:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
