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
    "formal_lounge": ("salon", "room", "reference formal lounge; replaced by answer 12"),
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

# Open joins, by our keys (no wall, no door). Ground: answer 12 (D-046): the
# island kitchen, living room, salon, dining and foyer are one open
# space, except the TV wall between the living room and the dining (12g); the
# Arabic kitchen is walled from the service passage (12m).
OPEN_JOINS = {
    "ground": [
        "show_kitchen/living", "entrance_foyer/living", "entrance_foyer/salon",
        "salon/dining", "salon/living",
        "entrance_foyer/stair_lift_ground", "entrance_foyer/stair_hall",
        "stair_lift_ground/stair_hall", "stair_lift_ground/show_kitchen",
        "guest_bedroom/guest_dress",
        "laundry/laundry_bay", "laundry_bay/service_passage",
        "arabic_kitchen/arabic_kitchen_bay",
        "service_steps/service_lobby",
    ],
    "first": [
        "master_suite/master_dress",
        "bedroom_2/bedroom_2_dress", "bedroom_3/bedroom_3_dress", "bedroom_4/bedroom_4_dress",
        "corridor_first/landing", "corridor_first/gallery",
        "landing/lift_lobby", "stair_lift_first/landing",
    ],
}

# The joins as they stood before answer 12, for the decision sketches.
OPEN_JOINS_BEFORE_12 = {
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

# Doors: the schedule in src/model/doors.py (G01 to G23, F01 to F15), copied
# into the plan as data. Every door the owner was shown on sketch VJH-SK-013.

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


# Answer 12, owner decisions 2026-10-02 (docs/ground-floor-decisions.md, 12 and
# 12a to 12m; D-046). Sizes come from the reference rectangles they replace.
DINING_ALONG_ROAD = 6.00    # 12a B: the dining in the north corner, 6.00 m along the road
SALON_ACROSS = 7.50        # 12d, 12e: the salon 6.00 m across, then 1.50 m more from the dining
TV_WALL_T = 0.15            # 12g: the TV wall, taken from the dining as the D-042 wall was


def apply_answer_12(ground: list, first: list, report: list[str]) -> tuple[list, list]:
    """Ground: the salon takes the lawn court's place, lined up with
    the dining and open to the foyer, the living room and the dining; the
    island kitchen, a double height living room and the dining run along the
    backyard; a solid TV wall stands between the living room and the dining.
    First: the family room above the salon, a void over the living room and
    the island kitchen in place of the reference family lounge, pantry and
    linen store (12b, 12l)."""
    g = {r["key"]: r for r in ground}
    f = {r["key"]: r for r in first}
    k, m, c = g["show_kitchen"], g["salon"], g["lawn_court"]
    split = round(m["x1"] - DINING_ALONG_ROAD, 3)
    line = round(c["y0"] + SALON_ACROSS, 3)

    def room(key, x0, x1, y0, y1, ref, why):
        return {"key": key, "kind": "room", "x0": round(x0, 3), "x1": round(x1, 3),
                "y0": round(y0, 3), "y1": round(y1, 3), "reference_key": ref,
                "reference_name": "", "confidence": "owner answer", "decision": why}

    out_g = [r for r in ground if r["key"] not in ("family_sitting", "dining", "salon", "lawn_court")]
    out_g += [
        room("living", k["x1"], split, k["y0"], k["y1"], "family_sitting+dining",
             "answers 12, 12a B, 12g: double height living room, TV wall to the dining"),
        room("dining", split + TV_WALL_T, m["x1"], line, k["y1"], "formal_lounge",
             "answers 12a B, 12e, 12g: dining in the north corner, faces the backyard"),
        room("salon", c["x0"], m["x1"], c["y0"], line, "lawn_court+formal_lounge",
             "answers 12, 12c, 12d, 12e, 12h: the salon in the lawn court's place, open "
             "to the foyer, the living room and the dining"),
    ]
    report.append(f"answer 12: living {split - k['x1']:.2f} x {k['y1'] - k['y0']:.2f}, dining "
                  f"{m['x1'] - split - TV_WALL_T:.2f} x {k['y1'] - line:.2f}, salon "
                  f"{m['x1'] - c['x0']:.2f} x {line - c['y0']:.2f}")

    fam, court, pantry, corr = (f["family_living"], f["lawn_court_open"], f["pantry_first"],
                                f["corridor_first"])
    out_f = [r for r in first if r["key"] not in
             ("family_living", "lawn_court_open", "balcony_family", "pantry_first", "linen_storage")]
    new_fam = room("family_living", court["x0"], court["x1"], court["y0"], court["y1"],
                   "lawn_court_void", "answer 12b: the family room above the salon")
    void = room("void_over_living", pantry["x0"], corr["x1"], corr["y1"], fam["y1"],
                "family_lounge+pantry+store",
                "answers 12 and 12l: void over the living room and the island kitchen")
    void["kind"] = "void"
    out_f += [new_fam, void]
    report.append("answer 12: first floor family room over the salon; reference family lounge, "
                  "pantry, linen store and family balcony replaced by the void (12l)")
    return out_g, out_f


# First floor answers (docs/first-floor-decisions.md, FF1 to FF8), built by
# the owner's FF8 (D-050). main() switches them on; the decision sketch
# VJH-SK-016 draws them from here so the sketch and the build cannot differ.
FIRST_FLOOR_JOINS = ["gallery/family_living"]        # FF5: the family room open to the gallery
FIRST_FLOOR_RETIRED_DOORS = {"F13"}                  # FF5: its double doors go


def apply_first_floor_answers(ground: list, first: list, report: list[str]) -> list:
    """FF7: the first floor wall at the end of the living room void stands on
    the TV wall (12g), so the void and the corridor reach the TV wall's
    living room face and bedroom 4 starts at its dining face. FF2 to FF4 and
    FF6 change no walls (the master suite's furniture, linen in cupboards,
    the margin kept)."""
    g = {r["key"]: r for r in ground}
    living, dining = g["living"], g["dining"]
    out = [dict(r) for r in first]
    for r in out:
        if r["key"] in ("void_over_living", "corridor_first"):
            r["x1"] = living["x1"]
        if r["key"] == "bedroom_4":
            r["x0"] = dining["x0"]
            r["decision"] = "FF7: its wall stands on the TV wall below"
    report.append("first floor answers: FF5 family room open to the gallery, FF7 wall over the TV wall")
    return out


def door_table(placed: set) -> list[dict]:
    """The door schedule as plan data, frame coordinates."""
    from model.doors import FIRST, FIRST_EXT, GROUND, GROUND_EXT  # noqa: PLC0415
    out = []
    for storey, inner, ext in (("ground", GROUND, GROUND_EXT), ("first", FIRST, FIRST_EXT)):
        for no, a, b, w, h, kind, into, at, src in inner:
            if a in placed and b in placed:
                out.append({"no": no, "storey": storey, "a": a, "b": b, "width_m": w,
                            "height_m": h, "kind": kind, "swing_into": into, "at": at,
                            "source": src})
        for no, r, axis, lo, hi, c, w, h, kind, src in ext:
            if r in placed:
                out.append({"no": no, "storey": storey, "a": r, "b": "outside", "axis": axis,
                            "lo": lo, "hi": hi, "at": c, "width_m": w, "height_m": h,
                            "kind": kind, "swing_into": r, "source": src})
    return sorted(out, key=lambda d: d["no"])


def assemble(answer_12: bool = True, first_floor: bool = False) -> tuple[dict, list[str]]:
    """answer_12=False gives the plan as it stood before answer 12, which the
    decision sketches VJH-SK-012 to VJH-SK-014 start from."""
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

    if answer_12:
        ground, first = apply_answer_12(ground, first, report)
        plan["ground"], plan["first"] = ground, first
    if answer_12 and first_floor:
        first = apply_first_floor_answers(ground, first, report)
        plan["first"] = first

    placed = {r["key"] for r in ground + first}
    table = OPEN_JOINS if answer_12 else OPEN_JOINS_BEFORE_12
    joins = {f: [j for j in js if all(k in placed for k in j.split("/"))]
             for f, js in table.items()}
    for f, js in table.items():
        for j in js:
            if j not in joins[f]:
                report.append(f"{f}: open join {j} skipped, a room is missing")
    plan["open_joins"] = joins
    if answer_12:
        plan["doors"] = [d for d in door_table(placed)
                         if not (first_floor and d["no"] in FIRST_FLOOR_RETIRED_DOORS)]
    if answer_12 and first_floor:
        joins["first"] = joins["first"] + FIRST_FLOOR_JOINS
    plan["room_links"] = []
    plan["external_doors"] = []
    plan["levels"] = {"ground_ffl_above_gate_m": 0.45, "carport_ffl_above_gate_m": 0.15,
                      "first_ffl_above_gate_m": 5.45, "carport_roof_m": 3.75,
                      "source": "reference sheet A-09-001"}
    plan["double_height"] = ["entrance_foyer", "living"] if answer_12 else ["entrance_foyer"]
    plan["open_to_sky"] = [] if answer_12 else ["lawn_court"]
    plan["transcription_notes"] = {
        "ground_problems": g_src.get("problems", []),
        "ground_notes": g_src.get("notes", []),
        "first_problems": f_src.get("problems", []),
    }
    return plan, report


def main() -> int:
    # First floor answers FF1 to FF8 built (owner: "A", build it; D-050).
    plan, report = assemble(first_floor=True)
    OUT.write_text(yaml.safe_dump(plan, sort_keys=False, width=100, allow_unicode=False),
                   encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO_ROOT)}: {len(plan['ground'])} ground, {len(plan['first'])} first")
    for line in report:
        print("  " + line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
