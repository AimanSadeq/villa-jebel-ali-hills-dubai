"""Can the program actually be laid out inside the chosen massing?

Phase 1 sized option C before the route B trims and against a flat 1.18 net to
gross assumption. Phase 2 has to test that assumption against the geometry a
real plan needs: corridors have length, walls have thickness.

This runs before any room is drawn, because finding out that the program is over
the cap is cheaper now than after two floor plans exist.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis.gfa_check import rooms, totals  # noqa: E402
from model.massing import load_massing  # noqa: E402
from model.site import SQM_TO_SQFT, load_site  # noqa: E402

REPORT_OUT = REPO_ROOT / "output" / "reports" / "VJH-RPT-005_Plan_Feasibility.txt"

# Rooms the Phase 1 indicative plan put in the single storey SSW wing.
SSW_WING_ROOMS = ("living", "dining", "show_kitchen")

# A double loaded corridor needs this width, and walls take roughly this share
# of net area in a room-dense plan. Both are assumptions, stated not buried.
CORRIDOR_W = 1.40
WALL_FRACTION = 0.08


@dataclass
class Zone:
    name: str
    net_m2: float
    corridor_length_m: float
    flat_m2: float = 0.0        # areas already expressed as a footprint

    @property
    def corridor_m2(self) -> float:
        return CORRIDOR_W * self.corridor_length_m

    @property
    def walls_m2(self) -> float:
        return self.net_m2 * WALL_FRACTION

    @property
    def gross_m2(self) -> float:
        return self.net_m2 + self.corridor_m2 + self.walls_m2 + self.flat_m2


def zones() -> list[Zone]:
    by_floor_key = {(r.floor, r.key): r for r in rooms()}
    ground = [r for r in rooms() if r.floor == "ground"]
    first = [r for r in rooms() if r.floor == "first"]

    spec = next(o for o in load_massing()["options"] if o["key"] == "C")
    road_length = spec["ground"][0]["v"][1] - spec["ground"][0]["v"][0]
    ssw_length = spec["ground"][1]["u"][1] - spec["ground"][1]["u"][0]

    ssw_net = sum(by_floor_key[("ground", k)].low_m2 for k in SSW_WING_ROOMS)
    garage = by_floor_key[("ground", "garage")].low_m2
    road_net = sum(r.low_m2 for r in ground
                   if r.key not in SSW_WING_ROOMS and r.key != "garage")
    first_net = sum(r.low_m2 for r in first)

    return [
        # Single depth, every room opening straight to the courtyard, so no
        # corridor at all. This is why it measured 1.13 in VJH-MA-002.
        Zone("SSW wing, single depth", ssw_net, 0.0),
        Zone("Road wing, double loaded", road_net, road_length, flat_m2=garage),
        Zone("First floor, double loaded", first_net, 24.0),
    ]


def assess() -> dict:
    t = totals()
    zs = zones()
    gross = sum(z.gross_m2 for z in zs)
    net = sum(z.net_m2 for z in zs)
    flat = sum(z.flat_m2 for z in zs)
    return {
        "zones": zs,
        "net_m2": net,
        "flat_m2": flat,
        "gross_m2": gross,
        "cap_m2": t["cap_m2"],
        "target_m2": t["design_target_m2"],
        "over_cap_m2": gross - t["cap_m2"],
        "over_target_m2": gross - t["design_target_m2"],
        "measured_factor": (gross - flat) / net,
        "assumed_factor": t["factor"],
        "corridor_m2": sum(z.corridor_m2 for z in zs),
        "fits_cap": gross <= t["cap_m2"],
    }


def report() -> str:
    a = assess()
    site = load_site()
    lines: list[str] = []
    w = lines.append

    w("PLAN FEASIBILITY")
    w(f"Plot {site['plot']['number']}, {site['plot']['community']}")
    w("Phase 2, before any room is drawn. Massing option C, after trim route B.")
    w("")
    w(f"Assumptions stated: corridor width {CORRIDOR_W:.2f} m, "
      f"walls {WALL_FRACTION:.0%} of net area.")
    w("")

    w("WHAT EACH ZONE NEEDS")
    w(f"{'Zone':<30}{'Net':>9}{'Corridor':>10}{'Walls':>8}{'Flat':>8}{'Gross':>9}")
    for z in a["zones"]:
        w(f"{z.name:<30}{z.net_m2:>9.2f}{z.corridor_m2:>10.2f}{z.walls_m2:>8.2f}"
          f"{z.flat_m2:>8.2f}{z.gross_m2:>9.2f}")
    w(f"{'TOTAL':<30}{a['net_m2']:>9.2f}{a['corridor_m2']:>10.2f}"
      f"{a['net_m2'] * WALL_FRACTION:>8.2f}{a['flat_m2']:>8.2f}{a['gross_m2']:>9.2f}")
    w("")

    w("AGAINST THE LIMIT")
    w(f"{'Gross the plan needs':<34}{a['gross_m2']:>9.2f} m2 "
      f"{a['gross_m2'] * SQM_TO_SQFT:>10.0f} sq ft")
    w(f"{'DDA cap':<34}{a['cap_m2']:>9.2f} m2")
    w(f"{'Over the cap by':<34}{a['over_cap_m2']:>9.2f} m2")
    w(f"{'Design target':<34}{a['target_m2']:>9.2f} m2")
    w(f"{'Over the target by':<34}{a['over_target_m2']:>9.2f} m2")
    w("")
    w(f"{'Net to gross the plan implies':<34}{a['measured_factor']:>9.3f}")
    w(f"{'Net to gross assumed so far':<34}{a['assumed_factor']:>9.3f}")
    w("")

    if a["fits_cap"]:
        w("VERDICT: the program fits inside the cap as laid out.")
    else:
        w("VERDICT: the program does NOT fit. The 1.18 net to gross assumption")
        w("was optimistic. Corridors are the cost: "
          f"{a['corridor_m2']:.2f} m2, which is "
          f"{a['corridor_m2'] / a['gross_m2']:.0%} of the whole building, almost")
        w("all of it in two wings that are long and thin.")
        w("")
        w("This is a decision for the owner, not a trim to make unilaterally.")
        w("See docs/open-items.md OI-20.")

    w("")
    w(site["meta"]["stamp"])
    return "\n".join(lines)


def main() -> int:
    text = report()
    print(text)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(text + "\n", encoding="utf-8")
    print(f"\nWritten to {REPORT_OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
