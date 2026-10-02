"""Cost trim packages against the plan 2 geometry at a given corridor width.

Every wing is sized from what it has to hold: rooms, a corridor that runs its
real length, partitions, and external walls on its real perimeter. Nothing is a
flat coefficient on area, which is the mistake the first two feasibility passes
made.

Proposals only. CLAUDE.md section 3: rooms are not cut without the owner.

Run: .\\.venv\\Scripts\\python.exe src/analysis/trim_packages.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis.gfa_check import rooms, totals  # noqa: E402

REPORT_OUT = REPO_ROOT / "output" / "reports" / "VJH-RPT-006_Trim_Packages.txt"

T_EXT = 0.25
PART = 0.045                 # internal partitions, share of net area

# Plan 2 geometry, plot grid metres.
ROAD_L = 27.00               # road wing length
BANDED_L = 20.80             # banded part of the road wing, where the spine runs
NORTH_L = 5.55               # north block: garage and staff strip
FIRST_L = 25.03              # first floor length
MASTER_BAND = 7.10           # master suite runs full depth, no corridor past it
SSW_INT_DEPTH = 7.80         # SSW wing internal depth
SSW_EXT_DEPTH = 8.30
SSW_AS_DRAWN = 115.37        # u 13.45 to 27.35 in the Phase 1 massing

GARAGE_INTERNAL_PER_GROSS = 31.3 / 38.0

SSW_ROOMS = ("living", "dining", "show_kitchen")
NORTH_ROOMS = ("maids_room", "drivers_room")
FIRST_ROOMS = ("master_suite", "bedroom_2", "bedroom_3", "bedroom_4",
               "family_living", "linen_storage", "stair_lift_first")


@dataclass
class Package:
    key: str
    name: str
    cuts: dict[str, float] = field(default_factory=dict)   # key -> new net m2
    right_size_ssw: bool = True
    notes: dict[str, str] = field(default_factory=dict)


def base_areas() -> dict[str, float]:
    return {r.key: r.low_m2 for r in rooms()}


def cost(areas: dict[str, float], corridor_w: float, right_size_ssw: bool) -> dict:
    garage = areas["garage"]
    first = sum(areas[k] for k in FIRST_ROOMS)
    north = sum(areas[k] for k in NORTH_ROOMS)
    ssw_net = sum(areas[k] for k in SSW_ROOMS)
    banded = sum(v for k, v in areas.items()
                 if k not in SSW_ROOMS and k not in NORTH_ROOMS
                 and k not in FIRST_ROOMS and k != "garage")

    banded_depth = (banded * (1 + PART) + corridor_w * BANDED_L) / BANDED_L
    north_depth = (garage * GARAGE_INTERNAL_PER_GROSS + north * (1 + PART)) / NORTH_L
    road = (max(banded_depth, north_depth) + 2 * T_EXT) * ROAD_L

    first_depth = (first * (1 + PART) + corridor_w * (FIRST_L - MASTER_BAND)) / FIRST_L
    first_g = (first_depth + 2 * T_EXT) * FIRST_L

    if right_size_ssw:
        ssw_len = ssw_net * (1 + PART) / SSW_INT_DEPTH + 2 * T_EXT
        ssw = ssw_len * SSW_EXT_DEPTH
    else:
        ssw = SSW_AS_DRAWN

    total = road + first_g + ssw
    cap = totals()["cap_m2"]
    return {"road": road, "first": first_g, "ssw": ssw, "total": total,
            "margin": cap - total, "cap": cap}


PACKAGES = [
    Package("0", "Right-size the SSW wing only, no room cut", {}),
    Package("1", "Spread thin, no room loses more than 2 m2", {
        "salon": 33, "guest_bedroom": 30, "sunroom": 18, "home_office": 12,
        "entrance_foyer": 17, "family_living": 33, "bedroom_2": 29,
        "bedroom_3": 29, "bedroom_4": 29, "master_suite": 68,
        "living": 44, "dining": 21, "show_kitchen": 24,
    }),
    Package("2", "Drop the sunroom", {"sunroom": 0}, notes={
        "sunroom": "Removed. The courtyard and the double height living room "
                   "already give the house its garden room.",
    }),
    Package("3", "Smaller guest suite, salon and sunroom", {
        "guest_bedroom": 26, "salon": 30, "sunroom": 15, "home_office": 12,
    }),
    Package("4", "Shave the bedroom floor", {
        "master_suite": 64, "bedroom_2": 27, "bedroom_3": 27, "bedroom_4": 27,
        "family_living": 31,
    }, notes={
        "master_suite": "64 against 27 keeps the brief's 2.2 to 2.5 times ratio, "
                        "at 2.37.",
    }),
]


def evaluate(corridor_w: float = 1.80) -> list[dict]:
    base = base_areas()
    out = []
    baseline = cost(base, corridor_w, right_size_ssw=False)
    for p in PACKAGES:
        areas = dict(base)
        areas.update(p.cuts)
        c = cost(areas, corridor_w, p.right_size_ssw)
        net_cut = sum(base[k] - v for k, v in p.cuts.items())
        out.append({"package": p, "cost": c, "net_cut": net_cut,
                    "gross_saved": baseline["total"] - c["total"]})
    return out, baseline


def report(corridor_w: float = 1.80) -> str:
    rows, baseline = evaluate(corridor_w)
    base = base_areas()
    lines: list[str] = []
    w = lines.append
    w("TRIM PACKAGES")
    w(f"Plan 2, massing option C, two car garage, corridors {corridor_w:.2f} m "
      "per DDA FAQ Q12.")
    w("Proposals only. No room is cut without the owner.")
    w("")
    w(f"Baseline, as drawn:  {baseline['total']:.2f} m2   "
      f"{baseline['margin']:+.2f} against the {baseline['cap']:.2f} m2 cap")
    w("")
    w(f"{'Pkg':<5}{'Net cut':>9}{'Gross saved':>13}{'Total':>10}{'Margin':>9}  Name")
    for r in rows:
        p, c = r["package"], r["cost"]
        w(f"{p.key:<5}{r['net_cut']:>9.1f}{r['gross_saved']:>13.2f}"
          f"{c['total']:>10.2f}{c['margin']:>+9.2f}  {p.name}")
    w("")
    for r in rows:
        p = r["package"]
        w(f"PACKAGE {p.key}  {p.name}")
        if not p.cuts:
            w("    No room changes.")
        for k, v in p.cuts.items():
            note = f"   {p.notes[k]}" if k in p.notes else ""
            w(f"    {k:<20}{base[k]:>5.0f} -> {v:<4.0f}{v - base[k]:+5.0f}{note}")
        w(f"    lands at {r['cost']['total']:.2f} m2, margin {r['cost']['margin']:+.2f}")
        w("")
    w("CONCEPT DESIGN, NOT FOR CONSTRUCTION")
    return "\n".join(lines)


def main() -> int:
    text = report()
    print(text)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
