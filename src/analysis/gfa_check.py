"""GFA check for Villa 5130272.

Reads brief/program.yaml and brief/site.yaml, converts net room areas to gross
floor area, and tests the result against the DDA limit of 662.99 m2.

Runs on every model build. Exits non-zero when the limit is breached by areas
that are confirmed to count toward GFA.

Scenarios: the garage and the roof stair enclosure are marked "unverified" in
program.yaml because whether they count toward GFA under DDA rules is not
confirmed. See docs/open-items.md. Breaches caused only by unverified areas are
reported as RISK rather than FAIL, so the check stays usable while the question
is open. Use --strict to fail on those too, once the answer is known.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model.site import SQM_TO_SQFT, load_site  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRAM_YAML = REPO_ROOT / "brief" / "program.yaml"

FLOORS = ("ground", "first", "roof")

# Garage and roof enclosure targets in program.yaml are already whole-footprint
# figures, so the net-to-gross factor is not applied to them. Applying it would
# inflate a 55 m2 garage to 65 m2 of GFA, which overstates the case.
ALREADY_GROSS = {"garage", "roof_enclosure"}


def load_program(path: Path | None = None) -> dict:
    with open(path or PROGRAM_YAML, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@dataclass
class Room:
    key: str
    name: str
    floor: str
    gfa: str
    low_m2: float
    high_m2: float
    is_range: bool
    already_gross: bool
    added_by_claude: bool

    @property
    def unverified(self) -> bool:
        return self.gfa == "unverified"

    @property
    def counts(self) -> bool:
        return self.gfa == "counts"


def rooms(program: dict | None = None) -> list[Room]:
    program = program or load_program()
    out: list[Room] = []
    for floor in FLOORS:
        for entry in program.get(floor, []):
            target = entry.get("target_m2")
            low = entry.get("target_min_m2")
            high = entry.get("target_max_m2")
            if low is not None or high is not None:
                lo, hi, is_range = float(low), float(high), True
            elif target is None:
                continue  # open terrace and similar, area follows from the plan
            else:
                lo = hi = float(target)
                is_range = False
            out.append(
                Room(
                    key=entry["key"],
                    name=entry["name"],
                    floor=floor,
                    gfa=entry.get("gfa", "counts"),
                    low_m2=lo,
                    high_m2=hi,
                    is_range=is_range,
                    already_gross=entry["key"] in ALREADY_GROSS,
                    added_by_claude=bool(entry.get("added_by_claude")),
                )
            )
    return out


def gross(net_m2: float, factor: float) -> float:
    return net_m2 * factor


def totals(program: dict | None = None, site: dict | None = None, factor: float | None = None) -> dict:
    """Net and gross totals, by scenario, at the low and high end of the ranges."""
    program = program or load_program()
    site = site or load_site()
    t = site["targets"]
    factor = factor if factor is not None else float(t["net_to_gross_factor"])

    rs = rooms(program)

    def bucket(predicate) -> dict:
        sel = [r for r in rs if predicate(r)]
        net_lo = sum(r.low_m2 for r in sel if not r.already_gross)
        net_hi = sum(r.high_m2 for r in sel if not r.already_gross)
        flat_lo = sum(r.low_m2 for r in sel if r.already_gross)
        flat_hi = sum(r.high_m2 for r in sel if r.already_gross)
        return {
            "net_low": net_lo + flat_lo,
            "net_high": net_hi + flat_hi,
            "gross_low": gross(net_lo, factor) + flat_lo,
            "gross_high": gross(net_hi, factor) + flat_hi,
        }

    core = bucket(lambda r: r.counts)
    garage = bucket(lambda r: r.key == 'garage')
    roof_encl = bucket(lambda r: r.key == 'roof_enclosure')

    # Scenarios are built from the unverified items that actually exist, so the
    # report shrinks as questions get answered instead of printing dead rows.
    unverified_keys = sorted({r.key for r in rs if r.unverified})
    scenarios = {
        "core": {
            "label": "All areas confirmed to count",
            "gross_low": core["gross_low"],
            "gross_high": core["gross_high"],
            "unverified_included": [],
        }
    }
    for key in unverified_keys:
        b = bucket(lambda r, k=key: r.key == k)
        scenarios[f"core_{key}"] = {
            "label": f"Plus {key.replace('_', ' ')}",
            "gross_low": core["gross_low"] + b["gross_low"],
            "gross_high": core["gross_high"] + b["gross_high"],
            "unverified_included": [key],
        }
    if len(unverified_keys) > 1:
        b = bucket(lambda r: r.unverified)
        scenarios["core_all_unverified"] = {
            "label": "Plus every unverified area",
            "gross_low": core["gross_low"] + b["gross_low"],
            "gross_high": core["gross_high"] + b["gross_high"],
            "unverified_included": list(unverified_keys),
        }

    cap = float(site["regulations"]["max_gfa_m2"])
    design_target = float(t["design_target_gfa_m2"])
    for s in scenarios.values():
        s["headroom_cap_low"] = cap - s["gross_low"]
        s["headroom_cap_high"] = cap - s["gross_high"]
        s["headroom_target_low"] = design_target - s["gross_low"]
        s["headroom_target_high"] = design_target - s["gross_high"]
        s["breaches_cap_low"] = s["gross_low"] > cap
        s["breaches_cap_high"] = s["gross_high"] > cap

    by_floor = {
        f: {
            "net_low": sum(r.low_m2 for r in rs if r.floor == f and r.counts),
            "net_high": sum(r.high_m2 for r in rs if r.floor == f and r.counts),
        }
        for f in FLOORS
    }

    return {
        "factor": factor,
        "cap_m2": cap,
        "design_target_m2": design_target,
        "design_margin_m2": cap - design_target,
        "core": core,
        "garage_m2": garage["gross_low"],
        "roof_enclosure_m2": roof_encl["gross_low"],
        "scenarios": scenarios,
        "by_floor": by_floor,
        "rooms": rs,
        "voids_m2": sum(float(v["target_m2"]) for v in program.get("voids", []) if v.get("target_m2")),
    }


def sensitivity(program: dict | None = None, site: dict | None = None,
                factors: tuple[float, ...] = (1.12, 1.14, 1.16, 1.18, 1.20, 1.22)) -> list[dict]:
    """How plan efficiency moves the result. Relevant when maximising to the cap."""
    out = []
    for f in factors:
        t = totals(program, site, factor=f)
        core = t["scenarios"]["core"]
        out.append({
            "factor": f,
            "core_low": core["gross_low"],
            "core_high": core["gross_high"],
            "headroom_low": t["cap_m2"] - core["gross_low"],
            "headroom_high": t["cap_m2"] - core["gross_high"],
        })
    return out


def sqft(v: float) -> float:
    return v * SQM_TO_SQFT


def report(program: dict | None = None, site: dict | None = None) -> tuple[str, bool, bool]:
    """Return (text, fails, at_risk)."""
    program = program or load_program()
    site = site or load_site()
    t = totals(program, site)

    lines: list[str] = []
    w = lines.append

    w("GFA CHECK")
    w(f"Plot {site['plot']['number']}, {site['plot']['community']}")
    w(f"Strategy: {site['targets']['strategy']}")
    w("")
    w(f"{'DDA maximum GFA':<40}{t['cap_m2']:>9.2f} m2 {sqft(t['cap_m2']):>10.2f} sq ft")
    w(f"{'Design target (margin held back)':<40}{t['design_target_m2']:>9.2f} m2 "
      f"{sqft(t['design_target_m2']):>10.2f} sq ft")
    w(f"{'Margin held back':<40}{t['design_margin_m2']:>9.2f} m2")
    w(f"{'Net to gross factor (assumption)':<40}{t['factor']:>9.2f}")
    w("")

    w("NET ROOM AREA BY FLOOR, confirmed GFA areas only")
    w(f"{'Floor':<12}{'Low':>10}{'High':>10}")
    for f in FLOORS:
        bf = t["by_floor"][f]
        if bf["net_low"] or bf["net_high"]:
            w(f"{f:<12}{bf['net_low']:>10.2f}{bf['net_high']:>10.2f}")
    w(f"{'TOTAL NET':<12}{t['core']['net_low']:>10.2f}{t['core']['net_high']:>10.2f}")
    w("")
    w(f"Of which the garage, counted toward GFA by owner decision: "
      f"{t['garage_m2']:.2f} m2")
    w(f"Double-height voids, excluded from upper floor area: {t['voids_m2']:.2f} m2")
    w("")

    w("GROSS FLOOR AREA BY SCENARIO, against the 662.99 m2 cap")
    w(f"{'Scenario':<34}{'Low':>9}{'High':>9}{'Head low':>10}{'Head high':>10}  Verdict")
    fails = at_risk = False
    for key, s in t["scenarios"].items():
        over = s["breaches_cap_low"] or s["breaches_cap_high"]
        if over:
            if s["unverified_included"]:
                at_risk = True
                verdict = "RISK, unverified areas"
            else:
                fails = True
                verdict = "FAIL, over the cap"
        else:
            verdict = "fits"
        if s["breaches_cap_low"] and s["breaches_cap_high"]:
            verdict += ", at both ends"
        elif over:
            verdict += ", at the high end"
        w(f"{s['label']:<34}{s['gross_low']:>9.2f}{s['gross_high']:>9.2f}"
          f"{s['headroom_cap_low']:>10.2f}{s['headroom_cap_high']:>10.2f}  {verdict}")
    w("")

    w("HEADROOM AGAINST THE DESIGN TARGET OF "
      f"{t['design_target_m2']:.2f} m2")
    for s in t["scenarios"].values():
        w(f"{s['label']:<34}{s['headroom_target_low']:>9.2f}{s['headroom_target_high']:>9.2f}")
    w("")
    w("Positive means area still available to distribute. Negative means trims")
    w("are needed. Trims are never made without the owner's approval.")
    w("")

    w("PLAN EFFICIENCY SENSITIVITY")
    w("Lower net to gross means more room area for the same GFA. Headroom is")
    w(f"against the {t['cap_m2']:.2f} m2 cap, with the garage counted.")
    w(f"{'Factor':<9}{'Gross low':>11}{'Gross high':>12}{'Head low':>11}{'Head high':>11}")
    for row in sensitivity(program, site):
        flag = "  fits" if row["headroom_low"] >= 0 else "  over"
        w(f"{row['factor']:<9.2f}{row['core_low']:>11.2f}{row['core_high']:>12.2f}"
          f"{row['headroom_low']:>11.2f}{row['headroom_high']:>11.2f}{flag}")
    w("")

    added = [r for r in t["rooms"] if r.added_by_claude]
    if added:
        w("ADDED BY CLAUDE, needs owner review")
        for r in added:
            w(f"  {r.name} ({r.floor}), {r.low_m2:.0f} m2")
        w("")

    if fails:
        w("VERDICT: FAIL. Confirmed GFA areas exceed the DDA cap.")
    elif at_risk:
        w("VERDICT: PASS with RISK. The house alone fits. One or more unverified")
        w("areas push the total over the cap if they are ruled to count.")
    else:
        w("VERDICT: PASS in every scenario.")

    w("")
    w(program["meta"]["stamp"])
    return "\n".join(lines), fails, at_risk


def main() -> int:
    ap = argparse.ArgumentParser(description="GFA check for Villa 5130272.")
    ap.add_argument("--strict", action="store_true",
                    help="Also fail when unverified areas breach the cap.")
    ap.add_argument("--out", type=Path, default=None,
                    help="Write the report to this file as well as stdout.")
    args = ap.parse_args()

    text, fails, at_risk = report()
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")

    if fails or (args.strict and at_risk):
        print("\nGFA CHECK FAILED", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
