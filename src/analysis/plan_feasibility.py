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

# A double loaded corridor needs this width.
CORRIDOR_W = 1.40

# Wall thicknesses. External walls are the expensive ones: they scale with the
# perimeter, so a long thin wing pays far more for them than a compact one.
T_EXTERNAL = 0.25
T_INTERNAL = 0.15

# Internal partitions, as a share of net area. Partitions are genuinely roughly
# proportional to the number and size of rooms, unlike external walls.
PARTITION_FRACTION = 0.045

# How much corridor each plan direction needs along the road wing. Plan 1 runs a
# corridor the full length. Plan 2 lets the reception rooms interconnect around
# the courtyard and keeps a short service spine.
ROAD_CORRIDOR_M = {"plan1": 27.0, "plan2": 12.0}
FIRST_CORRIDOR_M = 18.0


@dataclass
class Zone:
    name: str
    net_m2: float
    depth_m: float
    length_m: float
    corridor_length_m: float
    flat_m2: float = 0.0        # areas already expressed as a footprint

    @property
    def corridor_m2(self) -> float:
        return CORRIDOR_W * self.corridor_length_m

    @property
    def external_wall_m2(self) -> float:
        return 2 * (self.depth_m + self.length_m) * T_EXTERNAL

    @property
    def partition_m2(self) -> float:
        return self.net_m2 * PARTITION_FRACTION

    @property
    def walls_m2(self) -> float:
        return self.external_wall_m2 + self.partition_m2

    @property
    def gross_m2(self) -> float:
        return (self.net_m2 + self.corridor_m2 + self.walls_m2 + self.flat_m2)


def zones(plan: str = "plan2") -> list[Zone]:
    """The three zones of massing option C, sized to hold their rooms."""
    by_floor_key = {(r.floor, r.key): r for r in rooms()}
    ground = [r for r in rooms() if r.floor == "ground"]
    first = [r for r in rooms() if r.floor == "first"]

    spec = next(o for o in load_massing()["options"] if o["key"] == "C")
    road_length = spec["ground"][0]["v"][1] - spec["ground"][0]["v"][0]
    ssw = spec["ground"][1]
    ssw_length = ssw["u"][1] - ssw["u"][0]
    ssw_depth = ssw["v"][1] - ssw["v"][0]

    ssw_net = sum(by_floor_key[("ground", k)].low_m2 for k in SSW_WING_ROOMS)
    garage = by_floor_key[("ground", "garage")].low_m2
    road_net = sum(r.low_m2 for r in ground
                   if r.key not in SSW_WING_ROOMS and r.key != "garage")
    first_net = sum(r.low_m2 for r in first)

    road_corridor = ROAD_CORRIDOR_M[plan]
    road_depth = _solve_depth(road_length, road_net, road_corridor, flat=garage)
    first_length = _solve_length(road_depth, first_net, FIRST_CORRIDOR_M)

    return [
        # Single depth, every room opening straight to the courtyard, so no
        # corridor at all. This is why it measured 1.13 in VJH-MA-002.
        Zone("SSW wing, single depth", ssw_net, ssw_depth, ssw_length, 0.0),
        Zone("Road wing", road_net, road_depth, road_length, road_corridor,
             flat_m2=garage),
        Zone("First floor", first_net, road_depth, first_length, FIRST_CORRIDOR_M),
    ]


def _solve_depth(length, net, corridor_m, flat=0.0):
    """Depth at which a wing of this length exactly holds its contents."""
    rhs = (net + CORRIDOR_W * corridor_m + flat
           + 2 * length * T_EXTERNAL + net * PARTITION_FRACTION)
    return rhs / (length - 2 * T_EXTERNAL)


def _solve_length(depth, net, corridor_m, flat=0.0):
    rhs = (net + CORRIDOR_W * corridor_m + flat
           + 2 * depth * T_EXTERNAL + net * PARTITION_FRACTION)
    return rhs / (depth - 2 * T_EXTERNAL)


def assess(plan: str = "plan2") -> dict:
    t = totals()
    zs = zones(plan)
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
        "plan": plan,
    }


def report(plan: str = "plan2") -> str:
    a = assess(plan)
    site = load_site()
    lines: list[str] = []
    w = lines.append

    w("PLAN FEASIBILITY")
    w(f"Plot {site['plot']['number']}, {site['plot']['community']}")
    w(f"Phase 2, before any room is drawn. Massing option C, after trim route B.")
    w(f"Plan direction: {plan}.")
    w("")
    w(f"Assumptions stated: corridor {CORRIDOR_W:.2f} m wide, external walls "
      f"{T_EXTERNAL:.2f} m,")
    w(f"internal partitions {T_INTERNAL:.2f} m taken as {PARTITION_FRACTION:.1%} of net area.")
    w("")
    w("External walls are computed from each wing's real perimeter, not as a flat")
    w("share of area. A first pass used a flat 8%, which did not even cover the")
    w("external walls of a 27 m long wing and understated the total by 29 m2.")
    w("")

    w("WHAT EACH ZONE NEEDS")
    w(f"{'Zone':<26}{'Size':>14}{'Net':>8}{'Corr':>7}{'Ext wall':>9}"
      f"{'Part':>7}{'Flat':>7}{'Gross':>9}")
    for z in a["zones"]:
        size = f"{z.depth_m:.2f} x {z.length_m:.2f}"
        w(f"{z.name:<26}{size:>14}{z.net_m2:>8.1f}{z.corridor_m2:>7.1f}"
          f"{z.external_wall_m2:>9.1f}{z.partition_m2:>7.1f}{z.flat_m2:>7.1f}"
          f"{z.gross_m2:>9.2f}")
    w(f"{'TOTAL':<26}{'':>14}{a['net_m2']:>8.1f}{a['corridor_m2']:>7.1f}"
      f"{sum(z.external_wall_m2 for z in a['zones']):>9.1f}"
      f"{sum(z.partition_m2 for z in a['zones']):>7.1f}"
      f"{a['flat_m2']:>7.1f}{a['gross_m2']:>9.2f}")
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
    blocks = []
    for plan, label in (("plan1", "PLAN 1, CORRIDOR"),
                        ("plan2", "PLAN 2, COURTYARD")):
        rule = "=" * 72
        blocks.append(f"{rule}\n{label}\n{rule}\n\n" + report(plan))

    a1, a2 = assess("plan1"), assess("plan2")
    summary = [
        "=" * 72, "SIDE BY SIDE", "=" * 72, "",
        f"{'':<22}{'Gross':>10}{'vs cap':>10}{'vs target':>11}"
        f"{'net:gross':>11}{'corridor':>10}",
    ]
    for a, label in ((a1, "Plan 1, Corridor"), (a2, "Plan 2, Courtyard")):
        summary.append(
            f"{label:<22}{a['gross_m2']:>10.2f}{-a['over_cap_m2']:>+10.2f}"
            f"{-a['over_target_m2']:>+11.2f}{a['measured_factor']:>11.3f}"
            f"{a['corridor_m2']:>10.2f}")
    garage = next(r for r in rooms() if r.key == "garage").low_m2
    summary += [
        "",
        f"Plan 2 saves {a1['gross_m2'] - a2['gross_m2']:.2f} m2 against plan 1, "
        "all of it corridor.",
        "",
    ]
    if a2["fits_cap"]:
        held = a2["cap_m2"] - a2["gross_m2"]
        summary += [
            f"PLAN 2 FITS. It lands {held:.2f} m2 inside the "
            f"{a2['cap_m2']:.2f} m2 cap.",
            "",
        ]
        if a2["over_target_m2"] > 0:
            summary += [
                f"It sits {a2['over_target_m2']:.2f} m2 above the "
                f"{a2['target_m2']:.2f} m2 design target, so the margin held",
                f"back against a remeasure is {held:.2f} m2 rather than the "
                f"{a2['cap_m2'] - a2['target_m2']:.2f} m2 recommended in",
                f"D-005. That is {held / a2['cap_m2']:.1%} of the cap, against "
                "the 1.5% advised. Thinner, not reckless.",
                "",
            ]
    else:
        summary += [
            f"Plan 2 is still {a2['over_cap_m2']:.2f} m2 over the cap.",
            "",
            f"For scale: the garage counts {garage:.2f} m2 toward GFA under the "
            "owner decision of",
            f"2026-10-01, which is {garage / a2['over_cap_m2']:.1f} times the "
            "shortfall. Settling OI-01",
            "would make a further round of trims unnecessary.",
            "",
        ]
    if not a1["fits_cap"]:
        summary += [
            f"Plan 1, the corridor plan, remains {a1['over_cap_m2']:.2f} m2 over "
            "the cap and is not available.",
            "",
        ]
    text = "\n\n".join(blocks) + "\n\n" + "\n".join(summary)
    print(text)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(text + "\n", encoding="utf-8")
    print(f"\nWritten to {REPORT_OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
