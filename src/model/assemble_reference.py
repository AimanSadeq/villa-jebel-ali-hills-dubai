"""Assemble brief/reference_plan.yaml from the transcription of the owner's
reference villa and the owner's ground floor answers.

Inputs:
  reference/owner/transcription/ground_floor.json   sheet A-07-001, measured
  reference/owner/transcription/first_floor.json    sheet A-07-002, measured
Each holds the reconciled, checked rectangles in the sheet's frame (x along the
road from the carport side outer wall, y from the road side edge).

The owner's answers (docs/ground-floor-decisions.md) are applied here as an
explicit table of renames, substitutions, joins and doors, so every departure
from the reference is visible in one place. The first floor is a PLACEHOLDER
until the owner decides it; it is only renamed to our program keys and trimmed
where it would cross our setback lines.

Run: .venv/Scripts/python.exe src/model/assemble_reference.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

TRANSCRIPTION = REPO_ROOT / "reference" / "owner" / "transcription"
OUT = REPO_ROOT / "brief" / "reference_plan.yaml"

SOURCE = ("reference/owner/Reference_villa_plot_5131627_Paradise_Home_2025-07.pdf, "
          "sheets A-07-001 and A-07-002, Paradise Home Engineering Consultancy, July 2025")

# Reference key -> (our key, kind, why). Kinds: room, circulation, porch (open,
# covered, outside the body), open_to_sky (outside the body), carport.
GROUND_MAP = {
    "ent_foyer": ("entrance_foyer", "room", "reference, double height"),
    "main_entrance": ("main_entrance", "porch", "reference: open, recessed, double height porch"),
    "formal_lounge": ("majlis", "room", "D-042: the majlis, closed off from the dining"),
    "island_kitchen": ("show_kitchen", "room", "reference"),
    "family_sitting": ("family_sitting", "room", "answer 5"),
    "dining": ("dining", "room", "reference"),
    "prep_kitchen": ("arabic_kitchen", "room", "reference"),
    "prep_kitchen_bay": ("arabic_kitchen_bay", "room", "reference, part of the L"),
    "utility_laundry": ("laundry", "room", "reference"),
    "utility_laundry_bay": ("laundry_bay", "room", "reference, part of the L"),
    "store": ("pantry", "room", "reference"),
    "maids_room": ("maids_room", "room", "reference"),
    "maids_toilet": ("maids_toilet", "room", "reference"),
    "powder_room": ("guest_powder", "room", "reference"),
    "wash": ("wash", "room", "reference, the powder room's basin room"),
    "office_study": ("home_office", "room", "reference"),
    "office": ("home_office", "room", "reference"),
    "office_toilet": ("office_toilet", "room", "reference"),
    "guest_bedroom": ("guest_bedroom", "room", "reference"),
    "guest_dress": ("guest_dress", "room", "reference"),
    "guest_toilet": ("guest_toilet", "room", "reference"),
    "lift": ("lift", "room", "reference"),
    "stair": ("stair_lift_ground", "room", "reference stair; the lift is beside it"),
    "stair_hall": ("stair_hall", "circulation", "reference"),
    "service_lobby": ("service_lobby", "circulation", "reference: entry from the carport"),
    "service_steps": ("service_steps", "circulation", "reference: steps up from the carport"),
    "service_passage": ("service_passage", "circulation", "reference: 1.0 m wide, flagged"),
    "lawn_court": ("lawn_court", "open_to_sky", "answer 3, D-040"),
    "carport": ("garage", "carport", "answer 3, D-039, D-040: 3 car open carport"),
    "drivers_room": ("plant_room", "room", "answers 9 and 11a, D-043"),
    "drivers_toilet": ("outdoor_bathroom", "room", "answers 11 and 11a, D-043: opens onto the carport"),
}

FIRST_MAP = {
    "master_ensuite": ("master_suite", "room"),
    "master_dress": ("master_dress", "room"),
    "master_toilet": ("master_toilet", "room"),
    "bedroom_1": ("bedroom_2", "room"),
    "bedroom_1_dress": ("bedroom_2_dress", "room"),
    "bedroom_1_toilet": ("bedroom_2_toilet", "room"),
    "bedroom_2": ("bedroom_3", "room"),
    "bedroom_2_dress": ("bedroom_3_dress", "room"),
    "bedroom_2_toilet": ("bedroom_3_toilet", "room"),
    "bedroom_3": ("bedroom_4", "room"),
    "bedroom_3_dress": ("bedroom_4_dress", "room"),
    "bedroom_3_toilet": ("bedroom_4_toilet", "room"),
    "family_lounge": ("family_living", "room"),
    "store": ("linen_storage", "room"),
    "pantry": ("pantry_first", "room"),
    "stair": ("stair_lift_first", "room"),
    "lift": ("lift_first", "room"),
    "landing": ("landing", "circulation"),
    "lift_lobby": ("lift_lobby", "circulation"),
    "corridor": ("corridor_first", "circulation"),
    "gallery": ("gallery", "circulation"),
    "foyer_void": ("void_over_foyer", "void"),
    "lawn_court_void": ("lawn_court_open", "void"),
    "entrance_porch_void": ("void_over_entrance", "void"),
    "balcony_1": ("balcony_master", "balcony"),
    "balcony_2": ("balcony_family", "balcony"),
    "balcony_3": ("balcony_bedroom_4", "balcony"),
    "open_terrace": ("terrace_over_carport", "terrace"),
    "open_terrace_west": ("terrace_over_carport_side", "terrace"),
}
# Pieces the transcription split off only to avoid overlaps; in a placeholder
# they fold into the partition zone.
FIRST_DROP = {"bedroom_1_dress_strip"}

# Open joins, by our keys. Ground: the reference's, less dining/majlis (D-042).
OPEN_JOINS = {
    "ground": [
        "show_kitchen/family_sitting", "family_sitting/dining",
        "entrance_foyer/family_sitting", "entrance_foyer/dining",
        "entrance_foyer/stair_lift_ground", "entrance_foyer/stair_hall",
        "stair_lift_ground/stair_hall", "stair_lift_ground/show_kitchen",
        "guest_bedroom/guest_dress",
        "laundry/laundry_bay", "laundry_bay/service_passage",
        "arabic_kitchen/arabic_kitchen_bay", "arabic_kitchen_bay/service_passage",
        "service_steps/service_lobby",
    ],
    "first": [
        "master_suite/master_dress",
        "bedroom_2/bedroom_2_dress", "bedroom_3/bedroom_3_dress", "bedroom_4/bedroom_4_dress",
        "corridor_first/family_living", "corridor_first/pantry_first",
        "corridor_first/landing", "corridor_first/gallery",
        "landing/lift_lobby", "stair_lift_first/landing",
    ],
}

# Doors between rooms that are not hubs: (a, b, width m, kind[, at m]). "at"
# places the door centre that far along the shared wall from its end nearer
# the road; otherwise the door is centred.
ROOM_LINKS = [
    # D-042: wide double doors from the dining into the majlis, by the foyer.
    ["dining", "majlis", 1.60, "door", 1.10],
    ["wash", "guest_powder", 0.80, "door"],
    ["service_passage", "show_kitchen", 0.90, "door"],
    ["service_lobby", "stair_hall", 0.90, "door"],
    ["guest_bedroom", "guest_toilet", 0.80, "door"],
    ["home_office", "office_toilet", 0.80, "door"],
    ["laundry", "maids_room", 0.80, "door"],
    ["maids_room", "maids_toilet", 0.80, "door"],
    ["master_dress", "master_toilet", 0.80, "door"],
    ["bedroom_2_dress", "bedroom_2_toilet", 0.80, "door"],
    ["bedroom_3_dress", "bedroom_3_toilet", 0.80, "door"],
    ["bedroom_4_dress", "bedroom_4_toilet", 0.80, "door"],
    ["pantry_first", "linen_storage", 0.80, "door"],
    # The lawn court is glazed toward the foyer, as the reference draws it.
    ["entrance_foyer", "lawn_court", 3.00, "window"],
]

# External doors, faces in our grid after mirroring: W road, E rear garden,
# S south (the carport end), N north.
EXTERNAL_DOORS = [
    {"room": "entrance_foyer", "face": "W", "width_m": 2.40, "height_m": 3.00,
     "material": "door", "why": "reference: the main double door, at the back of the porch"},
    {"room": "service_steps", "face": "W", "width_m": 1.00, "height_m": 2.40,
     "material": "door", "why": "reference: service entry from the carport"},
    {"room": "plant_room", "face": "S", "width_m": 0.90, "height_m": 2.40,
     "material": "door", "why": "answers 9 and 11a: its own outside door"},
    {"room": "outdoor_bathroom", "face": "W", "width_m": 0.80, "height_m": 2.20,
     "material": "door", "why": "answers 11 and 11a: opens onto the carport"},
    {"room": "laundry", "face": "S", "width_m": 0.90, "height_m": 2.40,
     "material": "door", "why": "reference: side door to the service yard"},
    {"room": "family_sitting", "face": "E", "width_m": 3.00, "height_m": 3.00,
     "material": "glass", "why": "reference: the garden room opens to the garden"},
]

T_EXT = 0.25


def _load(name: str) -> dict:
    return json.loads((TRANSCRIPTION / name).read_text(encoding="utf-8"))


def _norm(key: str) -> str:
    return key.strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")


def _rect(d: dict, key: str, kind: str) -> dict:
    return {"key": key, "kind": kind,
            "x0": round(float(d["x0"]), 3), "x1": round(float(d["x1"]), 3),
            "y0": round(float(d["y0"]), 3), "y1": round(float(d["y1"]), 3),
            "reference_key": d["key"], "reference_name": d.get("name", ""),
            "confidence": d.get("confidence", "")}


def assemble() -> tuple[dict, list[str]]:
    from model.reference_plan import Placement  # noqa: PLC0415

    g_src, f_src = _load("ground_floor.json"), _load("first_floor.json")
    report: list[str] = []

    ground, seen = [], set()
    for d in g_src["rooms"]:
        k = _norm(d["key"])
        if k not in GROUND_MAP:
            report.append(f"ground: '{d['key']}' ({d.get('name', '')}) has no mapping; left out")
            continue
        key, kind, why = GROUND_MAP[k]
        if key in seen:
            report.append(f"ground: second rectangle for {key} from '{d['key']}'; left out")
            continue
        seen.add(key)
        r = _rect(d, key, kind)
        r["decision"] = why
        ground.append(r)

    first = []
    for d in f_src["rooms"]:
        k = _norm(d["key"])
        if k in FIRST_DROP:
            report.append(f"first: '{d['key']}' folded into the partition zone (placeholder)")
            continue
        if k not in FIRST_MAP:
            report.append(f"first: '{d['key']}' ({d.get('name', '')}) has no mapping; left out")
            continue
        key, kind = FIRST_MAP[k]
        first.append(_rect(d, key, kind))

    # D-042: the majlis is closed off from the dining. The reference has no
    # wall there (the rooms touch), so a 0.15 m partition is taken from the
    # dining, which narrows by that much.
    gk = {r["key"]: r for r in ground}
    if "dining" in gk and "majlis" in gk and abs(gk["dining"]["x1"] - gk["majlis"]["x0"]) < 0.01:
        gk["dining"]["x1"] = round(gk["majlis"]["x0"] - 0.15, 3)
        gk["dining"]["adjusted"] = "D-042: 0.15 m partition to the majlis taken from the dining"
        report.append(f"ground: dining narrowed by 0.15 m for the D-042 wall to the majlis")

    body = [r for r in ground if r["kind"] in ("room", "circulation")]
    plan = {
        "source": SOURCE,
        "note": ("Generated by src/model/assemble_reference.py from the measured transcription. "
                 "Do not edit by hand; change the tables in that script."),
        "frame": {"length_along_road_m": round(max(r["x1"] for r in body) + T_EXT, 3),
                  "rear_wall_y_m": round(max(r["y1"] for r in body) + T_EXT, 3)},
        "placement": {"mirror": True, "road_edge_y_m": 0.0,
                      "front_wall_y_m": round(min(r["y0"] for r in body) - T_EXT, 3)},
        "ground": ground, "first": first,
    }

    # Trim the first floor placeholder at our side setback lines.
    pl = Placement(plan)
    x_lim = pl.v_north - pl.v0
    for r in first:
        lim = x_lim - (0.0 if r["kind"] in ("balcony", "terrace") else T_EXT)
        if r["x1"] > lim + 1e-6:
            report.append(f"first: {r['key']} trimmed at the north setback line, x1 {r['x1']:.3f} -> "
                          f"{lim:.3f} ({r['x1'] - lim:.2f} m; placeholder)")
            r["x1"], r["trimmed"] = round(lim, 3), "north setback line, placeholder"
        if r["x0"] < -1e-6:
            report.append(f"first: {r['key']} trimmed at the carport end, x0 {r['x0']:.3f} -> 0.000")
            r["x0"], r["trimmed"] = 0.0, "carport end, placeholder"

    placed = {r["key"] for r in ground + first}
    joins = {f: [j for j in js if all(k in placed for k in j.split("/"))]
             for f, js in OPEN_JOINS.items()}
    for f, js in OPEN_JOINS.items():
        for j in js:
            if j not in joins[f]:
                report.append(f"{f}: open join {j} skipped, a room is missing")
    plan["open_joins"] = joins
    plan["room_links"] = [l for l in ROOM_LINKS if l[0] in placed and l[1] in placed]
    plan["external_doors"] = [d for d in EXTERNAL_DOORS if d["room"] in placed]
    plan["levels"] = {"ground_ffl_above_gate_m": 0.45, "carport_ffl_above_gate_m": 0.15,
                      "first_ffl_above_gate_m": 5.45, "carport_roof_m": 3.75,
                      "source": "reference sheet A-09-001"}
    plan["double_height"] = ["entrance_foyer"]
    plan["open_to_sky"] = ["lawn_court"]
    plan["transcription_notes"] = {
        "ground_problems": g_src.get("problems", []),
        "ground_notes": g_src.get("notes", []),
        "first_problems": f_src.get("problems", []),
    }
    return plan, report


def main() -> int:
    plan, report = assemble()
    OUT.write_text(yaml.safe_dump(plan, sort_keys=False, width=100, allow_unicode=False),
                   encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO_ROOT)}: {len(plan['ground'])} ground, {len(plan['first'])} first")
    for line in report:
        print("  " + line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
