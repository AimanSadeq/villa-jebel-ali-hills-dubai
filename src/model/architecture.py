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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import facade as facade_mod  # noqa: E402
from model import landscape as landscape_mod  # noqa: E402

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

PRINCIPAL = {"living", "dining", "show_kitchen", "salon", "master_suite", "family_hall",
             "family_living", "bedroom_2", "bedroom_3", "bedroom_4",
             "guest_bedroom"}
SERVICE_WINDOWS = {"home_office", "arabic_kitchen", "maids_room", "laundry",
                   "stair_lift_ground", "stair_lift_first"}
HIGH_WINDOWS = {"guest_powder", "outdoor_bathroom", "guest_toilet", "office_toilet",
                "maids_toilet", "powder_toilet", "wash", "master_toilet", "bedroom_2_toilet",
                "bedroom_3_toilet", "bedroom_4_toilet"}
NO_WINDOWS = {"garage", "pantry", "plant_room", "linen_storage", "lift", "main_entrance",
              "lawn_court", "guest_dress", "master_dress", "bedroom_2_dress", "bedroom_3_dress",
              "bedroom_4_dress", "pantry_first", "stair_lift_ground", "stair_lift_first"}

# First floor voids over a double height room whose external faces are glazed
# full height (D-046). The porch void is outdoor space and stays open.
VOID_GLAZING = {"void_over_living"}

DOOR_WIDTH = {"salon": 1.20, "master_suite": 1.00, "family_living": 1.20,
              "garage": 0.90, "dining": 1.60}

# key, name, RGB, transparency. Neutral concept colours, not finishes.
STYLES = [
    ("ext", "Beige render", (0.86, 0.80, 0.69), 0.0),        # D-048, brief/facade.yaml
    ("stone", "Warm split face stone", (0.78, 0.68, 0.50), 0.0),
    ("timber", "Timber, soffits, fins and pergola", (0.60, 0.39, 0.23), 0.0),
    ("led", "Linear LED line, warm white", (1.00, 0.86, 0.60), 0.0),
    ("int", "Partition, painted", (0.90, 0.89, 0.86), 0.0),
    ("slab", "Slab, rendered edge", (0.93, 0.92, 0.89), 0.0),
    ("roof", "Roof finish", (0.86, 0.85, 0.82), 0.0),
    ("glass", "Glazing", (0.52, 0.70, 0.80), 0.55),
    ("door", "Timber", (0.58, 0.43, 0.30), 0.0),
    ("pool", "Pool shell", (0.88, 0.89, 0.88), 0.0),
    ("water", "Pool water", (0.22, 0.58, 0.78), 0.35),
    ("deck", "Stone deck", (0.86, 0.81, 0.71), 0.0),
    ("terrain", "Garden ground", (0.78, 0.80, 0.66), 0.0),
    ("lawn", "Lawn", (0.45, 0.62, 0.30), 0.0),
    ("soil", "Planting bed, mulch", (0.45, 0.36, 0.27), 0.0),
    ("paving", "Paving, light", (0.80, 0.78, 0.72), 0.0),
    ("leaf", "Foliage", (0.33, 0.50, 0.26), 0.0),
    ("palm", "Palm fronds", (0.42, 0.58, 0.28), 0.0),
    ("trunk", "Trunk", (0.42, 0.33, 0.24), 0.0),
    ("stair", "Stair, stone", (0.83, 0.80, 0.75), 0.0),
    ("lift", "Lift car and shaft", (0.40, 0.42, 0.45), 0.0),
    ("space", "Room volume", (0.55, 0.78, 0.62), 0.8),
    ("joinery", "Joinery, light oak", (0.80, 0.70, 0.55), 0.0),
    ("textile", "Upholstery", (0.84, 0.80, 0.72), 0.0),
    ("sanitary", "Sanitary ware", (0.96, 0.96, 0.95), 0.0),
    ("metal", "Metal, dark", (0.20, 0.20, 0.20), 0.0),
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
        self.names.update({v["key"]: v["name"] for v in self.prog.get("voids", []) or []})
        # The reference plan's own rooms and halls (D-040, D-046).
        self.names.update({a["key"]: a["name"] for a in self.prog.get("ancillary", []) or []})
        self.names.update({"stair_hall": "Stair Hall", "service_lobby": "Service Lobby",
                           "service_steps": "Service Steps", "service_passage": "Service Passage",
                           "corridor_first": "First Floor Corridor", "gallery": "Gallery",
                           "landing": "Landing", "lift_lobby": "Lift Lobby"})
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
        self.lay_doors = list(self.lay.get("doors") or [])
        if self.lay.get("external_doors") or self.lay_doors:
            self.external_doors = []
        for d in self.lay.get("external_doors") or []:
            if isinstance(d, dict):
                self.external_doors.append((d["room"], d["face"], float(d.get("width_m", 0.9)),
                                            float(d.get("height_m", 2.4)), d.get("material", "door")))
        placed = {r["key"] for f in ("ground", "first")
                  for r in self.lay["floors"][f]["rooms"] + self.lay["floors"][f]["circulation"]}
        self.external_doors = [d for d in self.external_doors if d[0] in placed]
        self.counts: dict[str, int] = {}
        # Facade, answers R1 to R4: brief/facade.yaml.
        self.fspec = facade_mod.load()
        self.cuts = self.fspec.get("cuts", []) or []
        self.elev = {"ground": 0.0, "first": self.HG, "roof": self.HG + self.HF}
        self.window_boxes: list[dict] = []
        self.facade_obstacles: list[Polygon] = []
        self.opening_boxes: list[tuple] = []      # (storey, 2D cut, z0, z1), for finishes

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
        for key, name, cat in (("ext", "Masonry, beige render", "block"),
                               ("stone", "Split face stone cladding", "stone"),
                               ("timber", "Timber, exterior", "wood"),
                               ("led", "Linear LED profile", "aluminium"),
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

    def _cut(self, geom, storey, z0, z1):
        """geom less the facade cuts (brief/facade.yaml) that span its height."""
        e = self.elev[storey]
        for c in self.cuts:
            if c["z"][0] <= e + z0 + 1e-6 and c["z"][1] >= e + z1 - 1e-6:
                geom = geom.difference(box(c["u"][0], c["v"][0], c["u"][1], c["v"][1]))
        return geom

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
        plates = lay["plates"]
        self.ssw = (box(plates["ssw"]["u"][0], plates["ssw"]["v"][0], plates["ssw"]["u"][1],
                        plates["ssw"]["v"][1]) if "ssw" in plates else Polygon())
        self.carport = (box(plates["carport"]["u"][0], plates["carport"]["v"][0],
                            plates["carport"]["u"][1], plates["carport"]["v"][1])
                        if "carport" in plates else None)
        self.first_fp = Polygon(lay["outlines"]["first"])
        self.double_height = list(lay.get("double_height", []) or [])
        self.open_sky_keys = set(lay.get("open_to_sky", []) or [])
        self.porch_keys = {d["key"] for d in lay.get("porches", []) or []}
        self.f_outdoor = [R.of(d) for d in lay["floors"]["first"].get("outdoor", []) or []]
        self.g_rooms = [R.of(d) for d in lay["floors"]["ground"]["rooms"]]
        self.f_rooms = [R.of(d) for d in lay["floors"]["first"]["rooms"]]
        self.g_circ = [R.of(d) for d in lay["floors"]["ground"]["circulation"]]
        self.f_circ = [R.of(d) for d in lay["floors"]["first"]["circulation"]]
        self.voids = [R.of(d) for d in lay["floors"]["first"].get("voids", [])
                      if d["area_m2"] > 0.01]
        living = next((r for r in self.g_rooms if r.key == "living"), None)
        self.living = living
        self.open_sky = unary_union([r.poly for r in self.g_rooms if r.key in self.open_sky_keys]) \
            if self.open_sky_keys else Polygon()
        if self.ssw.is_empty:
            self.living_block = Polygon()
            self.kitchen_block = Polygon()
        elif "living" in lay["plates"]:
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
        self.g_fp = unary_union([g for g in (self.road, self.ssw, self.living_block) if not g.is_empty])

    # Walls -------------------------------------------------------------------

    def _joins(self, storey) -> list[tuple[str, str]]:
        """Open joins for a storey: the plan's own when it lists them (the
        reference villa, D-038), otherwise the generated plans' table."""
        lay_joins = (self.lay.get("open_joins") or {}).get(storey)
        if lay_joins is None:
            return list(OPEN_JOINS[storey])
        return [tuple(j.split("/")) if isinstance(j, str) else tuple(j) for j in lay_joins]

    def open_bridges(self, storey, rooms, circ):
        """The partitions removed by the open joins, as (owner key, polygon).

        Each bridge is the gap between two rooms over their shared length. Where
        bridges meet at a T, the small square of partition left between them is
        bridged too, so no stub of wall stands in the open space.
        """
        by_key = {r.key: r for r in rooms + circ}
        out = []
        for a_key, b_key in self._joins(storey):
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
            # 1 micron overlap so the bridge fuses with both rooms (no float seam).
            h = t / 2 + 1e-6
            gap = (box(lo, v - h, hi, v + h) if along_u
                   else box(u - h, lo, u + h, hi))
            out.append((a_key, gap))
        interior = unary_union([r.poly for r in rooms + circ] + [g for _, g in out])
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                (ka, ga), (_, gb) = out[i], out[j]
                if ga.distance(gb) > T_EXT:
                    continue
                hull = unary_union([ga, gb]).envelope
                stub = hull.difference(interior)
                # 0.10 m2: the pier where the foyer, living room and salon meet
                # (0.20 x 0.26 m, D-046) is open space, not a wall.
                if 0 < stub.area < 0.10:
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
                for poly in clean(self._cut(geom, storey, 0.0, top)):
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
        dh_keys = set(self.double_height) or ({"living"} if "living" not in self.lay["plates"]
                                              and self.living and not self.ssw.is_empty else set())
        if "living" in self.lay["plates"]:
            dh_keys.add("living")
        # A double height room under a first floor void (the reference plan's
        # foyer and, from D-046, its living room) takes its height from the
        # void; only one with no first floor over it is a tall block of its own.
        void_u = unary_union([v.poly for v in self.voids]) if self.voids else Polygon()
        tall_rooms = [r.poly for r in self.g_rooms if r.key in dh_keys
                      and r.poly.intersection(void_u).area < 0.5 * r.area]
        tall = unary_union(tall_rooms).buffer(0.30, join_style=2) if tall_rooms else Polygon()
        tall = tall.difference(self.first_fp.buffer(0.01, join_style=2))
        self.ext_ring_g = self.walls_for(
            "ground", self.g_fp, self.g_rooms, self.g_circ, [],
            z_top=self.HG - self.SLAB, tall_zone=None if tall.is_empty else tall,
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
                     [self._prism(p, -S, S) for p in clean(self.g_fp.difference(self.open_sky))],
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

        balconies = unary_union([r.poly for r in self.f_outdoor if "terrace" not in r.key]) \
            if self.f_outdoor else Polygon()
        main_roof = unary_union([self.first_fp, balconies.buffer(T_EXT, join_style=2)]) \
            if not balconies.is_empty else self.first_fp
        sky = unary_union([self.open_sky] + [v.poly for v in self.voids
                                             if not self.open_sky.is_empty
                                             and v.poly.intersects(self.open_sky.buffer(0.5))])
        main_roof = main_roof.difference(sky)
        self.low_road = self.low_road.difference(sky)
        # The balconies stand on the strip where the ground floor reaches past
        # the first floor: no separate roof or parapet under them (review,
        # D-046), so the balcony doors open onto the balcony.
        if not balconies.is_empty:
            self.low_road = self.low_road.difference(balconies.buffer(0.01, join_style=2))
        roofs = [
            ("Main roof", "roof", main_roof, 0.0, [self.living_block]),
            ("Roof over the garage and service end", "first",
             self.low_road, 0.0, [self.first_fp]),
            ("Roof terrace over the kitchen, master suite terrace",
             "first", self.kitchen_block, 0.0,
             [self.first_fp, self.living_block]),
            ("Roof over the double height living room", "roof", self.living_block,
             0.0, [self.first_fp]),
        ]
        for name, storey, poly, _, taller in roofs:
            parts = clean(poly) if not poly.is_empty else []
            if not parts:
                continue
            self.element("IfcSlab", name, storey,
                         [self._prism(p, -S, S) for p in parts],
                         predefined="ROOF", material="slab",
                         style="deck" if "terrace" in name else "roof")
            ring = unary_union(parts)
            ring = ring.difference(ring.buffer(-T_EXT, join_style=2, mitre_limit=10))
            for t in taller:
                if not t.is_empty:
                    ring = ring.difference(t.buffer(0.01, join_style=2))
            for p in clean(self._cut(ring, storey, 0.0, self.PAR)):
                self.element("IfcWall", f"Parapet, {name.lower()}", storey,
                             [self._prism(p, 0.0, self.PAR)],
                             predefined="PARAPET", material="ext")

    def build_outdoor(self):
        """Covered balconies at first floor level, the carport roof terrace and
        its columns. All outside GFA by D-039, TO VERIFY."""
        S = self.SLAB
        for r in self.f_outdoor:
            if "terrace" in r.key:
                continue
            self.element("IfcSlab", f"Covered balcony slab, {r.key}", "first",
                         [self._prism(r.poly, -S, S)], predefined="FLOOR", material="deck")
            ring = r.poly.difference(r.poly.buffer(-T_EXT, join_style=2))
            # No parapet on the house side, where the balcony door is.
            ring = ring.difference(self.first_fp.buffer(T_EXT + 0.02, join_style=2))
            for q in clean(ring):
                self.element("IfcWall", f"Balcony parapet, {r.key}", "first",
                             [self._prism(q, 0.0, self.PAR)], predefined="PARAPET",
                             material="ext")
            sp = self.element("IfcSpace", f"Covered balcony, {r.key}", "first",
                              [self._prism(r.poly, 0.0, self.HF - S - self.SERV)],
                              predefined="EXTERNAL", container=False, style="space")
            sp.LongName = r.key
            ifcopenshell.api.aggregate.assign_object(
                self.f, products=[sp], relating_object=self.storeys["first"][0])
        if self.carport is not None:
            # Levels on the reference sheets are above the gate; the ground
            # storey's zero is the house FFL, 0.45 m above it (A-09-001).
            lv = self.lay.get("levels", {}) or {}
            ffl = float(lv.get("ground_ffl_above_gate_m", 0.45))
            floor = float(lv.get("carport_ffl_above_gate_m", 0.15)) - ffl
            top = float(lv.get("carport_roof_m", 3.75)) - ffl
            roof = self.carport.difference(self.g_fp.buffer(0.01, join_style=2))
            self.element("IfcSlab", "Carport roof, open terrace above", "ground",
                         [self._prism(q, top - S, S) for q in clean(roof)],
                         predefined="ROOF", material="slab", style="deck")
            ring = roof.difference(roof.buffer(-T_EXT, join_style=2))
            ring = ring.difference(self.g_fp.buffer(0.02, join_style=2))
            for q in clean(ring):
                self.element("IfcWall", "Carport terrace parapet", "ground",
                             [self._prism(q, top, self.PAR)], predefined="PARAPET",
                             material="ext")
            # A column at each free corner of the carport roof, 0.40 m square.
            b, c = roof.bounds, 0.40
            for cu0 in (b[0], b[2] - c):
                for cv0 in (b[1], b[3] - c):
                    col = box(cu0, cv0, cu0 + c, cv0 + c)
                    if self.g_fp.buffer(0.05).intersects(col):
                        continue
                    self.element("IfcColumn", "Carport column", "ground",
                                 [self._prism(col, floor, top - S - floor)],
                                 predefined="COLUMN", material="ext")
            sp = self.element("IfcSpace", "Carport", "ground",
                              [self._prism(roof, floor, top - S - floor)],
                              predefined="EXTERNAL", container=False, style="space")
            sp.LongName = "garage"
            ifcopenshell.api.aggregate.assign_object(
                self.f, products=[sp], relating_object=self.storeys["ground"][0])
            self.element("IfcSlab", "Carport paving", "ground",
                         [self._prism(q, floor - 0.15, 0.15) for q in clean(roof)],
                         predefined="BASESLAB", material="deck")

    # Stair and lift core ---------------------------------------------------

    def build_core(self):
        g = next(r for r in self.g_rooms if r.key == "stair_lift_ground")
        lift_room = next((r for r in self.g_rooms if r.key == "lift"), None)
        u0, u1, v0 = g.u0, g.u1, g.v0
        lift = 1.00
        rise_total = self.HG
        risers = math.ceil(rise_total / 0.18)
        if risers % 2:
            risers += 1
        riser = rise_total / risers
        per_flight = risers // 2
        if lift_room is not None:
            self._build_reference_stair(g, lift_room, risers, riser, per_flight)
            return
        flight_w, going = 0.90, 0.28
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
            if not room.poly.buffer(0.01).contains(self.stairwell.union(self.shaft)):
                raise ValueError(f"stair and lift do not fit {room.key}")
        self.element("IfcTransportElement", "Home lift", "ground",
                     [self._prism(self.shaft, 0.0, self.HG + self.HF - self.SLAB)],
                     predefined="ELEVATOR", style="lift")

    def _build_reference_stair(self, g, lift_room, risers, riser, per_flight):
        """The reference villa's stair (A-07-001, A-07-002, A-09-001): a dog leg
        of two flights side by side in the stair room drawn on the first floor,
        the first flight rising from the foyer end in the lane of the ground
        floor stair, a half landing at the far end, the return flight arriving
        at the first floor stair head over the stair hall. The lift has its own
        shaft beside it. The reference states 28 risers, 300 mm treads, 1.5 m
        flights and a 1.5 x 3.0 m landing; the stair room as transcribed is
        shorter than that needs, so the going is fitted to the room and the
        difference is reported (OI-23, TO VERIFY)."""
        F = next((r for r in self.f_rooms if r.key == "stair_lift_first"), None) or g
        foyer = next((r for r in self.g_rooms if r.key == "entrance_foyer"), None)
        long_u = (F.u1 - F.u0) >= (F.v1 - F.v0)
        L = (F.u1 - F.u0) if long_u else (F.v1 - F.v0)
        W = (F.v1 - F.v0) if long_u else (F.u1 - F.u0)
        flight_w = min(1.50, (W - 0.05) / 2)
        # The landing goes at the end away from the foyer.
        fc = foyer.poly.centroid if foyer else F.poly.centroid
        mid = (F.u0 + F.u1) / 2 if long_u else (F.v0 + F.v1) / 2
        landing_low = (fc.x if long_u else fc.y) > mid
        # Flight 1 takes the lane on the ground floor stair's side.
        gc = g.poly.centroid
        across_mid = (F.v0 + F.v1) / 2 if long_u else (F.u0 + F.u1) / 2
        lane1_high = (gc.y if long_u else gc.x) > across_mid
        going = min(0.30, (L - 0.05 - flight_w) / (per_flight - 1))
        if going < 0.22:
            raise ValueError(f"stair room too short: going would be {going:.3f} m")
        run = (per_flight - 1) * going
        landing = L - run - 0.05
        z_land = riser * per_flight

        def box_l(s0, s1, t0, t1):
            """Local s along the run from the landing end, t across from lane 1."""
            if landing_low:
                a0, a1 = s0, s1
            else:
                a0, a1 = L - s1, L - s0
            if lane1_high:
                b0, b1 = W - t1, W - t0
            else:
                b0, b1 = t0, t1
            if long_u:
                return box(F.u0 + a0, F.v0 + b0, F.u0 + a1, F.v0 + b1)
            return box(F.u0 + b0, F.v0 + a0, F.u0 + b1, F.v0 + a1)

        steps = []
        # Flight 1: from the stair head end down toward the landing, rising.
        for i in range(per_flight - 1):
            s1 = L - 0.05 - i * going
            steps.append(self._prism(box_l(s1 - going, s1, 0.0, flight_w), 0.0, riser * (i + 1)))
        # Landing across both lanes.
        steps.append(self._prism(box_l(0.0, landing, 0.0, W), z_land - 0.20, 0.20))
        # Flight 2: from the landing back to the stair head, rising.
        for i in range(per_flight - 1):
            s0 = landing + i * going
            steps.append(self._prism(box_l(s0, s0 + going, W - flight_w, W),
                                     z_land, riser * (i + 1)))
        # Walk zones for the walkthrough (D-049): each flight is a ramp from
        # its foot to its head, the landing a flat at its level.
        def pt(s_, t_):
            c = box_l(s_ - 1e-3, s_ + 1e-3, t_ - 1e-3, t_ + 1e-3).centroid
            return (c.x, c.y)
        tm1, tm2 = flight_w / 2, W - flight_w / 2
        # Under the stair a person stands only where it is at least 2.0 m up:
        # the low end of flight 1 is solid; the wash and powder room under the
        # landing stay walkable (their headroom is OI-23).
        s_head = L - (L - landing) * min(1.0, 2.0 / z_land)
        self.walk_stair_solid = box_l(s_head, L, 0.0, flight_w)
        self.walk_stair = [
            {"name": "stair flight 1", "kind": "ramp", "poly": box_l(landing, L, 0.0, flight_w),
             "p0": pt(L, tm1), "z0": 0.0, "p1": pt(landing, tm1), "z1": z_land},
            {"name": "stair landing", "kind": "flat", "poly": box_l(0.0, landing, 0.0, W),
             "z": z_land},
            {"name": "stair flight 2", "kind": "ramp", "poly": box_l(landing, L, W - flight_w, W),
             "p0": pt(landing, tm2), "z0": z_land, "p1": pt(L, tm2), "z1": self.HG},
        ]
        stair = self.element("IfcStair", "Main stair", "ground", steps,
                             predefined="HALF_TURN_STAIR", material="slab", style="stair")
        ifcopenshell.api.pset.edit_pset(
            self.f, pset=ifcopenshell.api.pset.add_pset(self.f, product=stair,
                                                        name="Pset_StairCommon"),
            properties={"NumberOfRiser": risers, "RiserHeight": riser, "TreadLength": going})
        need = (per_flight - 1) * 0.30 + 1.50 + 0.05
        self.core_note = (f"reference stair: {risers} risers of {riser * 1000:.0f} mm, going "
                          f"{going * 1000:.0f} mm, two flights {flight_w:.2f} m wide, half "
                          f"landing {landing:.2f} m, in a {L:.2f} x {W:.2f} m stair room; the "
                          f"reference's 300 mm treads and 1.5 m landing need {need:.2f} m "
                          f"(OI-23, TO VERIFY); lift in its own shaft "
                          f"{lift_room.u1 - lift_room.u0:.2f} x {lift_room.v1 - lift_room.v0:.2f} m")
        self.stairwell = F.poly
        self.shaft = lift_room.poly.buffer(-0.10, join_style=2)
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
                tall_key = r.key in self.double_height or (r.key == "living" and not self.ssw.is_empty)
                h = clear_living if tall_key else clear
                if r.key == "garage" and self.carport is not None:
                    continue      # the open carport's space is built with the carport
                if r.key in self.porch_keys:
                    self.element("IfcSlab", f"Paving, {self.names.get(r.key, r.key)}", storey,
                                 [self._prism(r.poly.buffer(0.10, join_style=2), -self.SLAB, self.SLAB)],
                                 predefined="USERDEFINED", object_type="Porch paving",
                                 material="deck")
                    sp = self.element("IfcSpace", self.names.get(r.key, r.key), storey,
                                      [self._prism(r.poly, 0.0, h)],
                                      predefined="EXTERNAL", container=False, style="space")
                    sp.LongName = r.key
                    ifcopenshell.api.aggregate.assign_object(
                        self.f, products=[sp], relating_object=self.storeys[storey][0])
                    continue
                if r.key in self.open_sky_keys:
                    sp = self.element("IfcSpace", self.names.get(r.key, r.key), storey,
                                      [self._prism(r.poly, -0.15, 0.10)],
                                      predefined="EXTERNAL", container=False, style="terrain")
                    sp.LongName = r.key
                    ifcopenshell.api.aggregate.assign_object(
                        self.f, products=[sp], relating_object=self.storeys[storey][0])
                    continue
                it = self.interiors.get(r.key)
                shape = unary_union([it.main if it else r.poly]
                                    + [g for k, g in self.bridges[storey] if k == r.key])
                parts = [shape] if isinstance(shape, Polygon) else list(shape.geoms)
                items = [self._prism(q, 0.0, h) for q in parts]
                if storey == "ground" and self.voids:
                    # With a first floor over the room, its double height is
                    # only where a void is above (D-046: the foyer, the living
                    # room and about half the island kitchen).
                    void_u = unary_union([v.poly for v in self.voids])
                    tall = clean(shape.intersection(void_u))
                    low = clean(shape.difference(void_u))
                    if tall:
                        items = ([self._prism(q, 0.0, clear_living) for q in tall]
                                 + [self._prism(q, 0.0, clear) for q in low])
                        h = clear_living if sum(q.area for q in tall) > 0.5 * shape.area else clear
                    else:
                        items = [self._prism(q, 0.0, clear) for q in parts]
                        h = clear
                sp = self.element("IfcSpace", self.names.get(r.key, r.key), storey,
                                  items, predefined="INTERNAL", container=False,
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
        self.opening_boxes.append((storey, cut, sill, sill + height))
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
        if cls == "IfcWindow":
            b = pane.bounds
            e = self.elev[storey]
            self.window_boxes.append(dict(name=name, u0=b[0], u1=b[2], v0=b[1], v1=b[3],
                                          z0=e + sill, z1=e + sill + height))
        ifcopenshell.api.feature.add_filling(self.f, opening=op, element=fill)
        return fill

    # A wall between two rooms is anything from 0.05 to 0.35 m thick: the
    # generated plans use 0.15 and 0.25, the owner's reference 0.10 to 0.25.
    WALL_MIN, WALL_MAX = 0.05, 0.35

    @classmethod
    def _shared(cls, a: R, b: R):
        """Shared wall between two rectangles: (along_u, centre, wall_t, length)."""
        lo_t, hi_t = cls.WALL_MIN - 2e-3, cls.WALL_MAX + 2e-3
        for gap, u in ((b.u0 - a.u1, (a.u1 + b.u0) / 2), (a.u0 - b.u1, (b.u1 + a.u0) / 2)):
            if lo_t <= gap <= hi_t:
                lo, hi = max(a.v0, b.v0), min(a.v1, b.v1)
                if hi - lo > 0:
                    return False, (u, (lo + hi) / 2), gap, hi - lo
        for gap, v in ((b.v0 - a.v1, (a.v1 + b.v0) / 2), (a.v0 - b.v1, (b.v1 + a.v0) / 2)):
            if lo_t <= gap <= hi_t:
                lo, hi = max(a.u0, b.u0), min(a.u1, b.u1)
                if hi - lo > 0:
                    return True, ((lo + hi) / 2, v), gap, hi - lo
        return None

    # IFC4 IfcDoorTypeOperationEnum for each kind in src/model/doors.py.
    OPERATION = {"single": "SINGLE_SWING_LEFT", "double": "DOUBLE_DOOR_SINGLE_SWING",
                 "sliding": "SLIDING_TO_LEFT", "pivot": "USERDEFINED", "lift": "USERDEFINED"}

    def _door_name(self, d) -> str:
        a = self.names.get(d["a"], d["a"])
        if d["b"] != "outside":
            return f"Door {d['no']}, {a} to {self.names.get(d['b'], d['b'])}"
        if d["a"] == "entrance_foyer":
            return f"Front door {d['no']}"
        if d["kind"] == "sliding":
            where = "Garden" if d["storey"] == "ground" else "Balcony"
            return f"{where} door {d['no']}, {a}"
        return f"External door {d['no']}, {a}"

    def build_scheduled_doors(self):
        """The plan's door schedule (src/model/doors.py, D-046), each door on
        the wall the layout resolved it to. Openings that are open joins have
        no wall to cut and are skipped; a door with no host wall fails the
        build (build_model.py)."""
        open_pairs = {st: {frozenset(p) for p in self._joins(st)} for st in ("ground", "first")}
        for d in self.lay_doors:
            st = d["storey"]
            if d["kind"] == "open" and frozenset((d["a"], d["b"])) in open_pairs[st]:
                continue
            kind = "opening" if d["kind"] == "open" else "door"
            # An opening with no height given runs the full storey height.
            height = d["height_m"] or ((self.HG if st == "ground" else self.HF) - self.SLAB)
            fill = self.opening(st, kind, self._door_name(d), d["u"], d["v"], d["along_u"],
                                d["width_m"], 0.0, height, d["wall_t"],
                                material="glass" if d["kind"] == "sliding" else None)
            if fill is None or kind == "opening":
                continue
            fill.OperationType = self.OPERATION[d["kind"]]
            if fill.OperationType == "USERDEFINED":
                fill.UserDefinedOperationType = {"pivot": "PIVOT", "lift": "LIFT_SLIDING"}[d["kind"]]
            pset = ifcopenshell.api.pset.add_pset(self.f, product=fill, name="VJH_DoorSchedule")
            ifcopenshell.api.pset.edit_pset(self.f, pset=pset, properties={
                "Number": d["no"], "Kind": d["kind"], "Source": d["source"]})
            if d["kind"] == "pivot" and st == "ground":
                top = self.HG - self.SLAB
                if top - height > 0.05:
                    self.opening("ground", "window", f"Glass above front door {d['no']}, lower",
                                 d["u"], d["v"], d["along_u"], d["width_m"], height,
                                 top - height, d["wall_t"])
                # 12i: fixed glass above the front door to the full double height.
                host = self.host("first", Point(d["u"], d["v"]))
                if host is not None:
                    self.opening("first", "window", f"Glass above front door {d['no']}",
                                 d["u"], d["v"], d["along_u"], d["width_m"], 0.0,
                                 self.HF - self.SLAB, d["wall_t"])

    def build_doors(self):
        if self.lay_doors:
            self.build_scheduled_doors()
            return
        for storey, rooms, circ in (("ground", self.g_rooms, self.g_circ),
                                    ("first", self.f_rooms, self.f_circ)):
            door_h = 2.70 if storey == "ground" else 2.40
            open_pairs = {frozenset(p) for p in self._joins(storey)}
            everything = {r.key: r for r in rooms + circ}
            hub_keys = list(HUBS) + [c.key for c in circ if c.key not in HUBS]
            hub_keys += [k for k in ("main_entrance", "garden_room") if k in everything and k not in hub_keys]
            hub_keys = [k for k in hub_keys if k not in self.porch_keys and k not in self.open_sky_keys]
            hubs = [everything[k] for k in hub_keys if k in everything]
            # A plan that lists its own doors (the reference, D-038) uses only
            # those; the generated plans use the standard links and the doors
            # of their ancillary rooms. One door per pair of rooms.
            if self.lay.get("room_links"):
                raw = [tuple(x) for x in self.lay["room_links"]]
            else:
                raw = list(ROOM_LINKS) + [(an["serves"], an["key"], 0.80, "door")
                                          for an in self.prog.get("ancillary", []) or []]
            links, pairs = [], set()
            for l in raw:
                pair = frozenset(l[:2])
                if pair not in pairs:
                    pairs.add(pair)
                    links.append(l)
            # A room a link opens into takes its door from that link only.
            link_targets = {l[1] for l in links if len(l) > 3 and l[3] == "door"}
            for r in rooms:
                if r.key in ("living", "dining", "show_kitchen", "outdoor_bathroom"):
                    continue      # open plan, or reached from outside
                if r.key in hub_keys or any(r.key in p for p in open_pairs):
                    continue      # part of the open space
                if r.key in self.open_sky_keys or r.key in self.porch_keys:
                    continue      # open areas: the court is glazed from the foyer
                if r.key in link_targets:
                    continue      # its door comes from its link
                if r.key == "garage" and self.carport is not None:
                    continue      # an open carport has no door (D-040)
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
                    linked = any(r.key in tuple(l[:2]) for l in links)
                    outside = any(r.key == k for k, *_ in self.external_doors)
                    if not (linked or outside):
                        raise ValueError(f"{r.key} on the {storey} floor has no door")
                    self.no_hub_door.append((storey, r.key, "link" if linked else "external door"))
            for link in links:
                a_key, b_key, wdt, kind = link[:4]
                at = link[4] if len(link) > 4 else None
                a, b = everything.get(a_key), everything.get(b_key)
                if not a or not b or frozenset((a_key, b_key)) in open_pairs:
                    continue
                s = self._shared(a, b)
                if s:
                    along_u, (u, v), t, length = s
                    width = min(wdt, length - 0.2)
                    if at is not None:
                        # Measured from the end of the shared wall nearer the road.
                        lo = max(a.u0, b.u0) if along_u else max(a.v0, b.v0)
                        if along_u:
                            u = max(a.u0, b.u0) + max(at, width / 2 + 0.1)
                        else:
                            v = lo + max(at, width / 2 + 0.1)
                    label = {"door": "Door", "window": "Glazed screen"}.get(kind, "Opening")
                    self.opening(storey, kind,
                                 f"{label}, {self.names.get(a_key, a_key)} to "
                                 f"{self.names.get(b_key, b_key)}",
                                 u, v, along_u, width, 0.0, door_h, t)

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

    FURN_STYLE = {"accents.joinery": "joinery", "accents.worktop": "joinery",
                  "fixtures.sanitary": "sanitary", "fixtures.metal": "metal"}

    def build_furniture(self):
        """Furniture in every room (answer P5, src/model/furniture.py): one
        IfcFurniture or IfcSanitaryTerminal per piece. Indicative."""
        from model import furniture as furniture_mod  # noqa: PLC0415
        self.furniture, self.furniture_report = furniture_mod.layout(self)
        for p in self.furniture:
            e = self.elev[p.storey]
            items = [self._prism(box(q[1], q[3], q[2], q[4]), q[5], q[6] - q[5]) for q in p.parts
                     if q[2] - q[1] > 0.005 and q[4] - q[3] > 0.005 and q[6] - q[5] > 0.005]
            if not items:
                continue
            slot = max(p.parts, key=lambda q: (q[2] - q[1]) * (q[4] - q[3]) * (q[6] - q[5]))[0]
            el = self.element(p.ifc, f"{p.name}, {self.names.get(p.room, p.room)}", p.storey, items,
                              predefined="NOTDEFINED", object_type="Furniture, indicative",
                              style=self.FURN_STYLE.get(slot, "textile"))
            el.Description = "Indicative furniture, src/model/furniture.py. CONCEPT DESIGN, NOT FOR CONSTRUCTION."
            del e

    def _face_kind(self, r: R, face: str) -> str:
        if r.key == "living" and "living" in self.lay["plates"]:
            return {"N": "courtyard", "E": "landscape", "S": "hot", "W": "inner"}[face]
        in_ssw = self.ssw.buffer(0.01).contains(r.poly)
        if in_ssw:
            return {"N": "courtyard", "E": "landscape", "S": "hot", "W": "inner"}[face]
        return {"E": "courtyard", "W": "hot", "S": "hot", "N": "north"}[face]

    def _door_spans(self, storey, r: R, face: str) -> list[tuple[float, float]]:
        """Stretches of a room's external face taken by scheduled doors, with
        0.30 m of wall either side."""
        out = []
        for d in self.lay_doors:
            if d["storey"] != storey or d["b"] != "outside" or d["a"] != r.key:
                continue
            if d["along_u"]:
                f = "S" if d["v"] < r.v0 else "N"
                c = d["u"]
            else:
                f = "W" if d["u"] < r.u0 else "E"
                c = d["v"]
            if f == face:
                out.append((c - d["width_m"] / 2 - 0.30, c + d["width_m"] / 2 + 0.30))
        return sorted(out)

    def build_windows_and_external_doors(self):
        lived_in = [c for c in self.f_circ if c.key == "family_hall"]
        glazed_voids = [v for v in self.voids if v.key in VOID_GLAZING]
        for storey, rooms, ring in (("ground", self.g_rooms, self.ext_ring_g),
                                    ("first", self.f_rooms + lived_in + glazed_voids,
                                     self.ext_ring_f)):
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
                    spans = self._door_spans(storey, r, face)
                    if spans:
                        pieces = [(s0, s1)]
                        for a, b2 in spans:
                            pieces = [q for x, y in pieces
                                      for q in ((x, min(y, a)), (max(x, b2), y)) if q[1] - q[0] > 0.01]
                        pieces = [q for q in pieces if q[1] - q[0] >= 0.9]
                        if r.key in NO_WINDOWS or r.key == "entrance_foyer" or not pieces:
                            continue
                        kind = self._face_kind(r, face)
                        if r.key in PRINCIPAL and kind in ("courtyard", "landscape"):
                            # Fixed glass either side of a garden or balcony door.
                            sill = 0.15 if ground else 0.90
                            for x, y in pieces:
                                mid = (x + y) / 2
                                uw_, vw_ = ((mid, wall_line) if along_u else (wall_line, mid))
                                self.opening(storey, "window",
                                             f"Fixed glass, {self.names.get(r.key, r.key)}",
                                             uw_, vw_, along_u, y - x - 0.30, sill,
                                             clear - 0.30 - sill, T_EXT)
                            continue
                        s0, s1 = max(pieces, key=lambda q: q[1] - q[0])
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
                    out_pt = {"W": Point(u_c - 0.6, v_c), "E": Point(u_c + 0.6, v_c),
                              "S": Point(u_c, v_c - 0.6), "N": Point(u_c, v_c + 0.6)}[face]
                    if not self.open_sky.is_empty and self.open_sky.buffer(0.3).contains(out_pt):
                        kind = "courtyard"
                    if kind == "inner":
                        continue
                    if r.key in VOID_GLAZING:
                        # Full height glass, continuing the double height room's
                        # glazing below (D-046).
                        wdt, sill, hgt = length - 0.60, 0.0, self.HF - self.SLAB - 0.30
                    elif r.key in HIGH_WINDOWS:
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
                    face_name = ("garden" if kind == "courtyard" and self.lay_doors
                                 and self.open_sky.is_empty else kind)
                    self.opening(storey, "window",
                                 f"Window, {self.names.get(r.key, r.key)}, {face_name}",
                                 u_c, v_c, along_u, wdt, sill, hgt, T_EXT)

    # Site, pool, deck ------------------------------------------------------

    def build_site(self):
        plot = site_to_grid(plot_polygon())
        ground_level = -float((self.lay.get("levels", {}) or {}).get("ground_ffl_above_gate_m", 0.15))
        self.element("IfcGeographicElement", "Plot terrain", None,
                     [self._prism(plot, ground_level - 0.30, 0.30)], predefined="TERRAIN",
                     container=True, style="terrain")
        # The garden (brief/garden.yaml, G1 to G4, D-055). The carport columns
        # and the facade parts on the ground are obstacles for the walker.
        obstacles = list(self.facade_obstacles)
        if self.carport is not None:
            roof = self.carport.difference(self.g_fp.buffer(0.01, join_style=2))
            b, c = roof.bounds, 0.40
            for cu0 in (b[0], b[2] - c):
                for cv0 in (b[1], b[3] - c):
                    col = box(cu0, cv0, cu0 + c, cv0 + c)
                    if not self.g_fp.buffer(0.05).intersects(col):
                        obstacles.append(col.buffer(0.05))
        self.garden = landscape_mod.build(landscape_mod.load(), plot, self.g_fp, self.carport, obstacles)
        for it in self.garden.items:
            items = [self._prism(p, z0, h) for p, z0, h in it.prisms if h > 0.005 and p.area > 1e-4]
            if not items:
                continue
            el = self.element(it.cls, it.name, None, items, predefined=it.predefined,
                              object_type=it.object_type, material=it.material, style=it.style)
            el.Description = "Landscape, brief/garden.yaml, indicative. CONCEPT DESIGN, NOT FOR CONSTRUCTION."
        removed = {r["key"] for r in self.prog.get("removed", []) or []}
        if "pool" in removed and not self.lay.get("pool"):
            return        # no pool, owner decision D-041
        spec = self.lay if self.lay.get("pool") else next(
            o for o in self.m["options"] if o["key"] == "C")
        (pu0, pu1), (pv0, pv1) = spec["pool"]["u"], spec["pool"]["v"]
        (du0, du1), (dv0, dv1) = spec["deck"]["u"], spec["deck"]["v"]
        pool = box(pu0, pv0, pu1, pv1)
        shell = pool.buffer(T_EXT, join_style=2)
        depth = 1.50
        if self.g_fp.buffer(-0.01).intersects(box(du0, dv0, du1, dv1)) or (
                self.carport is not None and self.carport.buffer(-0.01).intersects(box(du0, dv0, du1, dv1))):
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

    FACADE_CLASS = {
        "cladding": ("IfcCovering", "CLADDING"),
        "surround": ("IfcCovering", "CLADDING"),
        "soffit": ("IfcCovering", "USERDEFINED"),
        "canopy": ("IfcSlab", "USERDEFINED"),
        "fin": ("IfcShadingDevice", "USERDEFINED"),
        "pergola": ("IfcBuildingElementProxy", "USERDEFINED"),
    }

    def build_facade(self):
        """The facade of brief/facade.yaml (answers F1, F2, R1 to R4): stone
        portal and garden frame, eaves, carport piers, surrounds and fins on
        the hot windows, the open roof pergola and the LED lines. One element
        per named part; a window's surround, its fins, and the pergola each as
        one element. Visual concept finishes, not a specification."""
        inside = facade_mod.inside_from_layouts(LAYOUTS)
        bx, self.facade_notes = facade_mod.boxes(self.window_boxes, self.fspec, inside)
        self.facade_boxes = bx
        groups: dict[tuple, list] = {}
        for b in bx:
            key = ("Roof pergola" if b.kind == "pergola" else b.name, b.kind, b.material)
            groups.setdefault(key, []).append(b)
        for (name, kind, mat), parts in groups.items():
            z0 = min(p.z0 for p in parts)
            storey = "roof" if z0 >= self.HG + self.HF - 0.31 else ("first" if z0 >= self.HG - 0.31
                                                                     else "ground")
            e = self.elev[storey]
            items = [self._prism(box(p.u0, p.v0, p.u1, p.v1), p.z0 - e, p.z1 - p.z0) for p in parts]
            cls, pre = self.FACADE_CLASS[kind]
            el = self.element(cls, name, storey, items, predefined=pre,
                              object_type=f"Facade: {kind}",
                              material={"render": "ext"}.get(mat, mat))
            el.Description = "Facade proposal, brief/facade.yaml. CONCEPT DESIGN, NOT FOR CONSTRUCTION."
            if kind in ("cladding",) and z0 < 0.5:
                self.facade_obstacles += [box(p.u0, p.v0, p.u1, p.v1).buffer(0.02) for p in parts]
        # LED lines: 40 mm profiles along the polylines.
        t = 0.04
        for ln in self.fspec.get("led", []) or []:
            pts = ln["points"]
            items = []
            for p, q in zip(pts[:-1], pts[1:]):
                lo = [min(a, b) - t / 2 for a, b in zip(p, q)]
                hi = [max(a, b) + t / 2 for a, b in zip(p, q)]
                items.append(self._prism(box(lo[0], lo[1], hi[0], hi[1]), lo[2], hi[2] - lo[2]))
            el = self.element("IfcLightFixture", f"Linear LED, {ln['name']}", "ground", items,
                              predefined="NOTDEFINED", object_type="Facade: led", material="led")
            el.Description = "Facade proposal, brief/facade.yaml. CONCEPT DESIGN, NOT FOR CONSTRUCTION."

    def build_railings(self):
        """Glass balustrades along every open edge of the first floor voids,
        where no wall stands. Height 1.20 m from the floor finish, the DDA
        minimum for parapets and balcony handrails (DDA FAQs Building Q34,
        brief/massing.yaml); its use for an internal void edge is TO VERIFY
        against the Dubai Building Code."""
        walls = unary_union([poly for _, poly, _ in self.walls["first"]]).buffer(0.03)
        h = float(self.PAR)
        for v in self.voids:
            edge = v.poly.exterior.difference(walls)
            lines = [edge] if edge.geom_type == "LineString" else list(getattr(edge, "geoms", []))
            for ln in lines:
                if ln.length < 0.30:
                    continue
                band = ln.buffer(0.03, cap_style=2, join_style=2)
                self.element("IfcRailing", f"Balustrade, {self.names.get(v.key, v.key)}",
                             "first", [self._prism(band, 0.0, h)], predefined="BALUSTRADE",
                             material="glass")

    def walk_data(self) -> dict:
        """Where a person can stand, for the walkthrough's collision and floor
        following (D-049): flat zones per level, the stair as ramps and a flat
        landing, door openings joining the rooms, and the lift shaft that rides
        between levels. Grid coordinates (u, v), heights z above the ground
        floor finish. The outside is the plot, at the ground floor level."""
        def door_rect(d):
            w, t = d["width_m"] - 0.10, d["wall_t"] + 0.06
            if d["along_u"]:
                return box(d["u"] - w / 2, d["v"] - t / 2, d["u"] + w / 2, d["v"] + t / 2)
            return box(d["u"] - t / 2, d["v"] - w / 2, d["u"] + t / 2, d["v"] + w / 2)

        def interior(storey, rooms, circ):
            parts = [r.poly for r in rooms + circ] + [g for _, g in self.bridges[storey]]
            parts += [door_rect(d) for d in self.lay_doors if d["storey"] == storey]
            return unary_union(parts)

        stair = getattr(self, "walk_stair", [])
        solid = getattr(self, "walk_stair_solid", Polygon())
        ground = interior("ground", self.g_rooms, self.g_circ).difference(solid)
        # Facade parts standing on the ground (portal legs, carport piers).
        for ob in self.facade_obstacles:
            ground = ground.difference(ob)
        # Furniture the walker cannot pass (beds, sofas, tables, counters).
        blocks = {"ground": [], "first": []}
        for p in getattr(self, "furniture", []):
            if p.block and not p.footprint().is_empty:
                blocks[p.storey].append(p.footprint().buffer(-0.03, join_style=2))
        ground = ground.difference(unary_union(blocks["ground"])) if blocks["ground"] else ground
        voids = unary_union([v.poly for v in self.voids]) if self.voids else Polygon()
        first = unary_union([interior("first", self.f_rooms, self.f_circ)]
                            + [r.poly for r in self.f_outdoor if "terrace" not in r.key])
        first = first.difference(voids).difference(self.stairwell)
        if blocks["first"]:
            first = first.difference(unary_union(blocks["first"]))

        def rings(poly):
            out = []
            for p in ([poly] if poly.geom_type == "Polygon" else list(getattr(poly, "geoms", []))):
                if p.area < 0.05:
                    continue
                out.append([[[round(x, 3), round(y, 3)] for x, y in p.exterior.coords]]
                           + [[[round(x, 3), round(y, 3)] for x, y in r.coords]
                              for r in p.interiors])
            return out

        zones = []
        garden = getattr(self, "garden", None)
        outside = [(n, p, z) for n, p, z in garden.flat] if garden else []
        for name, poly, z in [("ground floor", ground, 0.0), ("first floor", first, self.HG)] + outside:
            for rg in rings(poly):
                zones.append({"name": name, "kind": "flat", "z": z, "rings": rg})
        for zdef in stair + (garden.ramps if garden else []):
            for rg in rings(zdef["poly"]):
                zz = {k: v for k, v in zdef.items() if k != "poly"}
                for k in ("p0", "p1"):
                    if k in zz:
                        zz[k] = [round(zz[k][0], 3), round(zz[k][1], 3)]
                zz["rings"] = rg
                zones.append(zz)
        lift = self.shaft
        return {
            "eye_m": 1.60, "radius_m": 0.20, "step_m": 0.45,
            "zones": zones,
            "lift": {"rings": rings(lift)[0] if rings(lift) else [], "levels": [0.0, self.HG]},
            "start": {"u": round(door_rect(next(d for d in self.lay_doors
                                                if d["no"] == "G01")).centroid.x - 2.5, 3),
                      "v": round(next(d for d in self.lay_doors if d["no"] == "G01")["v"], 3),
                      "z": 0.0},
            "levels": {"ground": 0.0, "first": self.HG},
        }

    def build(self) -> Path:
        self.setup()
        self.footprints()
        self.build_core()
        self.build_walls()
        self.build_railings()
        self.build_slabs()
        self.build_spaces()
        self.build_doors()
        self.build_windows_and_external_doors()
        self.build_furniture()
        self.build_outdoor()
        self.build_facade()
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
