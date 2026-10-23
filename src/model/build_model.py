"""Build the villa model: GFA check, IFC generation, validation, report.

Order matters. The GFA check runs first and stops the build if the plan is over
the cap, as CLAUDE.md section 3 requires. Then the IFC is generated and checked
three ways:

  1. Schema validation with ifcopenshell.validate.
  2. Every element with a body is tessellated; any that fails stops the build.
  3. The model's floor area is measured back from the IFC itself, by projecting
     the walls and spaces of each storey to plan, and compared with the plan's
     measured GFA in brief/layouts.yaml. A mismatch means the model and the plan
     have drifted apart, and stops the build.

Writes output/reports/VJH-RPT-007_Model_Build.txt.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import json
import logging
import math
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.validate
import numpy as np
import yaml
from shapely.geometry import Polygon
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis import gfa_check  # noqa: E402
from model import architecture  # noqa: E402
from model.finishes import exterior_data, finish_data  # noqa: E402
from model.heights import clear_heights, room_height_text  # noqa: E402
from model.site import sqft  # noqa: E402

REPORT = REPO_ROOT / "output" / "reports" / "VJH-RPT-007_Model_Build.txt"
VIEWER_DATA = REPO_ROOT / "viewer" / "public" / "data"

# Short names for the viewer's room labels; the full name shows on selection.
LABEL = {
    "outdoor_bathroom": "Outdoor WC", "maids_room": "Maid",
    "laundry": "Laundry", "plant_room": "Plant", "home_office": "Office",
    "guest_powder": "Powder",
    "stair_lift_ground": "Stair + lift", "stair_lift_first": "Stair + lift",
    "salon": "Salon", "guest_bedroom": "Guest bedroom", "pantry": "Pantry",
    "arabic_kitchen": "Arabic kitchen", "show_kitchen": "Show kitchen",
    "dining": "Dining", "living": "Living", "master_suite": "Master suite",
    "family_living": "Family room", "linen_storage": "Linen",
    "hall_link": "Link hall",
    "family_hall": "Family hall", "hall_arm": "Landing",
    "entrance_foyer": "Hall", "corridor": "Gallery",
    "bedroom_2": "Bedroom 2", "bedroom_3": "Bedroom 3", "bedroom_4": "Bedroom 4",
    "lawn_court": "Lawn court", "wash": "Wash", "lift": "Lift", "main_entrance": "Entrance",
    "guest_dress": "Dress", "guest_toilet": "Toilet", "office_toilet": "WC",
    "maids_toilet": "WC", "powder_toilet": "WC", "master_dress": "Dress",
    "master_toilet": "Bath", "bedroom_2_dress": "Dress", "bedroom_2_toilet": "Bath",
    "bedroom_3_dress": "Dress", "bedroom_3_toilet": "Bath", "bedroom_4_dress": "Dress",
    "bedroom_4_toilet": "Bath", "pantry_first": "Pantry", "garage": "Carport",
    "courtyard": "Courtyard", "hall": "Hall", "gallery": "Gallery", "gallery_west": "Gallery",
    "north_lobby": "Lobby", "guest_lobby": "Lobby", "salon_lobby": "Lobby",
    "service_corridor": "Service", "workspace": "Workspace", "lift_first": "Lift",
    "family_living": "Family lounge", "plant_room": "Plant",
}
AREA_TOLERANCE_M2 = 0.10


def validate(f) -> list[str]:
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(f, logger, express_rules=False)
    return [f"{s.get('level', '')}: {s.get('message', s)}" for s in logger.statements]


def tessellate(f):
    """World coordinate meshes for every element with a body."""
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    meshes, failed = {}, []
    for el in f.by_type("IfcProduct"):
        if not el.Representation or el.is_a("IfcOpeningElement"):
            continue
        try:
            shape = ifcopenshell.geom.create_shape(settings, el)
        except Exception as exc:  # noqa: BLE001, reported and fails the build
            failed.append(f"{el.is_a()} '{el.Name}': {exc}")
            continue
        g = shape.geometry
        verts = np.array(g.verts).reshape(-1, 3)
        faces = np.array(g.faces).reshape(-1, 3)
        if len(faces) == 0:
            failed.append(f"{el.is_a()} '{el.Name}': empty mesh")
            continue
        meshes[el.id()] = (el, verts, faces)
    return meshes, failed


def volume(verts, faces) -> float:
    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    return float(abs(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6.0)


def plan_area(items) -> float:
    polys = []
    for _, verts, faces in items:
        for tri in verts[faces][:, :, :2]:
            p = Polygon(tri)
            if p.area > 1e-6:
                polys.append(p)
    return unary_union(polys).area if polys else 0.0


def sun_positions() -> dict:
    """Sun directions for the walkthrough's shadows, in the plot grid (pvlib,
    brief/site.yaml location): a spring afternoon and a summer afternoon.
    dir_uvz points from the ground toward the sun."""
    import math  # noqa: PLC0415

    import pandas as pd  # noqa: PLC0415
    import pvlib  # noqa: PLC0415

    from model.massing import load_massing  # noqa: PLC0415
    from model.site import load_site  # noqa: PLC0415
    loc = load_site()["location"]
    bearing = float(load_massing()["grid"]["bearing_deg"])
    out = {}
    for key, when in (("spring_15h", "2026-03-21 15:00"), ("summer_16h", "2026-06-21 16:00"),
                      ("winter_15h", "2026-12-21 15:00"), ("sunset", "2026-03-21 18:05"),
                      ("morning_9h", "2026-03-21 09:00")):
        t = pd.DatetimeIndex([pd.Timestamp(when, tz=loc["timezone"])])
        sp = pvlib.solarposition.get_solarposition(t, float(loc["latitude"]), float(loc["longitude"]))
        az, el = float(sp["azimuth"].iloc[0]), float(sp["apparent_elevation"].iloc[0])
        th = math.radians(az - bearing)          # clockwise from the grid's v axis
        out[key] = {"when": when, "azimuth_deg": round(az, 1), "elevation_deg": round(el, 1),
                    "dir_uvz": [round(math.sin(th) * math.cos(math.radians(el)), 4),
                                round(math.cos(th) * math.cos(math.radians(el)), 4),
                                round(math.sin(math.radians(el)), 4)]}
    return out


def measured_from_ifc(f, meshes) -> dict:
    """Walls and spaces of each storey projected to plan. Walls are measured
    without their openings: a door or a full height glazed opening does not
    take floor area away (answer 12i's glass above the front door, D-046)."""
    whole = ifcopenshell.geom.settings()
    whole.set("use-world-coords", True)
    whole.set("disable-opening-subtractions", True)
    out = {}
    for storey in f.by_type("IfcBuildingStorey"):
        items = []
        for el, verts, faces in meshes.values():
            container = ifcopenshell.util.element.get_container(el)
            parent = ifcopenshell.util.element.get_aggregate(el)
            if storey not in (container, parent):
                continue
            if el.is_a("IfcSpace") and el.PredefinedType != "EXTERNAL":
                items.append((el, verts, faces))
            elif el.is_a("IfcWall") and el.PredefinedType != "PARAPET":
                g = ifcopenshell.geom.create_shape(whole, el).geometry
                items.append((el, np.array(g.verts).reshape(-1, 3),
                              np.array(g.faces).reshape(-1, 3)))
        out[storey.Name] = plan_area(items)
    return out


def publish_to_viewer(model, path: Path, lay: dict, ifc_areas: dict) -> None:
    """Copy the IFC next to the viewer and write the labels and figures it shows.

    Only a passing build is published, so the viewer never shows a model that
    failed its checks.
    """
    VIEWER_DATA.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, VIEWER_DATA / path.name)
    elev = {"ground": 0.0, "first": model.HG}
    heights = clear_heights(lay)
    rooms = []
    for storey, key in (("ground", "ground"), ("first", "first")):
        floor = lay["floors"][key]
        for d in floor["rooms"] + floor["circulation"]:
            (u0, u1), (v0, v1) = d["u"], d["v"]
            area = (u1 - u0) * (v1 - v0)
            w, l = sorted((u1 - u0, v1 - v0))
            rooms.append({
                "key": d["key"], "name": model.names.get(d["key"], d["key"]),
                "label": LABEL.get(d["key"], model.names.get(d["key"], d["key"])),
                "storey": storey, "u": round((u0 + u1) / 2, 3),
                "v": round((v0 + v1) / 2, 3), "z": elev[storey] + 1.2,
                "area_m2": round(area, 2), "area_sqft": round(sqft(area), 1),
                # CLAUDE.md rule 9 (D-045): width x length and clear height.
                "w_m": round(w, 2), "l_m": round(l, 2),
                "rect": [round(u0, 3), round(u1, 3), round(v0, 3), round(v1, 3)],
                "height": room_height_text(d, storey, lay, heights),
                "circulation": d in floor["circulation"],
            })
    # Sub-rooms from the interiors: small labels, picked by their LongName.
    for key, it in model.interiors.items():
        for part in it.parts:
            if part.kind != "space":
                continue
            c = part.poly.representative_point()
            rooms.append({
                "key": part.key, "name": part.name,
                "label": ("Bath" if "bathroom" in part.key or "shower" in part.name.lower()
                          else "WIR"),
                "storey": it.storey, "u": round(c.x, 3), "v": round(c.y, 3),
                "z": elev[it.storey] + 1.2, "area_m2": round(part.poly.area, 2),
                "area_sqft": round(sqft(part.poly.area), 1), "circulation": False,
                "sub": True,
            })
    bearing = math.radians(float(model.m["grid"]["bearing_deg"]))
    data = {
        "meta": {"plot": model.site["plot"]["number"],
                 "community": model.site["plot"]["community"],
                 "stamp": model.site["meta"]["stamp"], "phase": 4,
                 "ifc": f"data/{path.name}",
                 "built": datetime.now().isoformat(timespec="minutes")},
        "north_uv": [round(-math.sin(bearing), 5), round(math.cos(bearing), 5)],
        "heights": {"ground_m": model.HG, "first_m": model.HF,
                    "parapet_m": model.PAR, "roof_m": model.HG + model.HF,
                    "overall_m": model.HG + model.HF + model.PAR},
        "outside_gfa": lay["gfa_measured"].get("outside_gfa_to_verify", {}),
        "reference": lay.get("reference", ""),
        "gfa": {k: lay["gfa_measured"][k] for k in
                ("road_wing_ground", "ssw_wing_ground", "living_block_ground",
                 "first_floor_less_void",
                 "total", "cap", "margin")},
        "gfa_from_ifc": {k: round(v, 2) for k, v in ifc_areas.items()},
        "core": model.core_note,
        "counts": {k: v for k, v in sorted(model.counts.items())
                   if k != "IfcOpeningElement"},
        "rooms": rooms,
        # The walkthrough (D-049): where a person can stand on each level.
        "walk": model.walk_data(),
        "finishes": finish_data(model),
        "exterior": exterior_data(model),
        "sun": sun_positions(),
    }
    (VIEWER_DATA / "model.json").write_text(json.dumps(data, indent=1),
                                           encoding="utf-8")


def main() -> int:
    lines = ["VJH-RPT-007  MODEL BUILD", architecture.Model().site["meta"]["stamp"], ""]
    ok = True

    print("1. GFA check")
    if gfa_check.main() != 0:
        print("\nBUILD STOPPED: GFA check failed. The model is not generated.")
        return 1
    lines.append("1. GFA check: PASS (output/reports/VJH-RPT-001_GFA_Check.txt)")

    print("\n2. IFC generation")
    model = architecture.Model()
    path = model.build()
    print(f"   {path.relative_to(REPO_ROOT)}")
    lines += ["", f"2. IFC generated: {path.relative_to(REPO_ROOT).as_posix()}",
              f"   Schema IFC4. Stair and lift core: {model.core_note}"]
    for k in sorted(model.counts):
        lines.append(f"   {k:<26}{model.counts[k]:>5}")
    if model.counts.get("unhosted"):
        ok = False
        lines.append("   FAIL: openings with no host wall")

    f = ifcopenshell.open(str(path))

    print("\n3. Schema validation")
    logging.getLogger("ifcopenshell").setLevel(logging.ERROR)
    issues = validate(f)
    lines += ["", f"3. Schema validation: {'PASS' if not issues else 'FAIL'}, "
                  f"{len(issues)} issue(s)"]
    lines += [f"   {i}" for i in issues[:40]]
    ok &= not issues
    print(f"   {len(issues)} issue(s)")

    print("\n4. Geometry")
    meshes, failed = tessellate(f)
    by_class = Counter(el.is_a() for el, _, _ in meshes.values())
    vols = Counter()
    for el, v, fc in meshes.values():
        vols[el.is_a()] += volume(v, fc)
    lines += ["", f"4. Geometry: {len(meshes)} elements tessellated, {len(failed)} failed"]
    for cls in sorted(by_class):
        lines.append(f"   {cls:<26}{by_class[cls]:>5}   {vols[cls]:>9.2f} m3")
    lines += [f"   FAIL {x}" for x in failed]
    ok &= not failed
    print(f"   {len(meshes)} tessellated, {len(failed)} failed")

    print("\n5. Floor area measured back from the IFC")
    lay = yaml.safe_load(architecture.LAYOUTS.read_text(encoding="utf-8"))
    g = lay["gfa_measured"]
    plan = {"Ground Floor": (g["road_wing_ground"] + g["ssw_wing_ground"]
                             + g.get("living_block_ground", 0.0)),
            "First Floor": g["first_floor_less_void"]}
    ifc = measured_from_ifc(f, meshes)
    lines += ["", "5. Floor area, IFC against the plan (walls and spaces in plan; "
                  f"tolerance {AREA_TOLERANCE_M2:.2f} m2)"]
    for name, want in plan.items():
        got = ifc.get(name, 0.0)
        good = abs(got - want) <= AREA_TOLERANCE_M2
        ok &= good
        lines.append(f"   {name:<14} IFC {got:8.2f}   plan {want:8.2f}   "
                     f"{'PASS' if good else 'FAIL'}")
        print(f"   {name:<14} IFC {got:8.2f}   plan {want:8.2f}")
    total = sum(ifc.get(n, 0.0) for n in plan)
    lines.append(f"   Total          IFC {total:8.2f}   plan {g['total']:8.2f}   "
                 f"cap {g['cap']:.2f}")

    lines += ["", f"RESULT: {'PASS' if ok else 'FAIL'}"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if ok:
        publish_to_viewer(model, path, lay, ifc)
        print(f"   viewer data: {VIEWER_DATA.relative_to(REPO_ROOT)}")
    print(f"\nRESULT: {'PASS' if ok else 'FAIL'}   {REPORT.relative_to(REPO_ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
