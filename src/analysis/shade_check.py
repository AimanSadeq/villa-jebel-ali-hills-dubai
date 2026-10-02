"""Afternoon shade on the pool deck, cast by the villa as actually planned.

Phase 1 scored the massing options with simple blocks. This check repeats the
measurement on the real footprint from brief/layouts.yaml, at the heights the
owner chose (D-030), for the pool position that follows the central hall plan
(D-037), and for one alternative: an east west pool across the living room's
frontage. The Phase 1 score for option C is printed beside them so the change
is visible.

Shadows are true geometry (src/model/massing.shadow): each mass is extruded to
its own parapet height and projected along the sun vector from pvlib.

Writes output/reports/VJH-RPT-008_Shade_Check.txt.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis.sun_study import sun_vector  # noqa: E402
from model.massing import grid_to_site, load_massing, options, score, shadow, site_to_grid  # noqa: E402
from model.site import buildable_envelope  # noqa: E402

LAYOUTS = REPO_ROOT / "brief" / "layouts.yaml"
REPORT = REPO_ROOT / "output" / "reports" / "VJH-RPT-008_Shade_Check.txt"
TZ = "Asia/Dubai"


def _rect(spec: dict) -> Polygon:
    return box(spec["u"][0], spec["v"][0], spec["u"][1], spec["v"][1])


def masses(lay: dict, heights: dict) -> list[tuple[str, Polygon, float]]:
    """(name, site polygon, height to the top of its parapet) for each mass."""
    hg, hf, par = (float(heights[k]) for k in ("ground_floor_m", "first_floor_m", "parapet_m"))
    road = Polygon(lay["outlines"]["road_ground"])
    first = Polygon(lay["outlines"]["first"])
    ssw = _rect(lay["plates"]["ssw"])
    out = [("Two storey wing", first, hg + hf + par),
           ("Single storey end of the road wing", road.difference(first), hg + par),
           ("SSW wing, kitchens", ssw, hg + par)]
    if "living" in lay["plates"]:
        out.append(("Living block, double height", _rect(lay["plates"]["living"]),
                    hg + hf + par))
    return [(n, grid_to_site(p), h) for n, p, h in out if not p.is_empty]


def villa_shadow(ms, sun) -> Polygon:
    return unary_union([shadow(p, h, sun) for _, p, h in ms])


def shade_fraction(ms, target_site: Polygon, when: pd.Timestamp) -> float:
    sun = sun_vector(when)
    if sun is None:
        return 1.0
    return villa_shadow(ms, sun).intersection(target_site).area / target_site.area


def assess(ms, target_site: Polygon, year: int = 2026) -> dict:
    a = load_massing()["assessment"]
    summer, winter, detail = [], [], {}
    for date in a["summer_dates"]:
        for hour in a["afternoon_hours"]:
            f = shade_fraction(ms, target_site, pd.Timestamp(f"{year}-{date} {hour:02d}:00", tz=TZ))
            summer.append(f)
            detail[f"{date} {hour:02d}:00"] = f
    for date in a["winter_dates"]:
        for hour in a["winter_midday_hours"]:
            winter.append(shade_fraction(ms, target_site,
                                         pd.Timestamp(f"{year}-{date} {hour:02d}:00", tz=TZ)))
    return {"summer_pm_shade": float(np.mean(summer)),
            "winter_midday_sun": 1.0 - float(np.mean(winter)), "detail": detail}


def candidates(lay: dict) -> list[tuple[str, Polygon, Polygon, str]]:
    """(name, pool, deck, note) in grid coordinates."""
    out = [("D-037, north of the living room, 10 m along the plot",
            _rect(lay["pool"]), _rect(lay["deck"]),
            "The current plan. Deck starts at the living room's north wall.")]
    lv = lay["plates"]["living"]
    env = site_to_grid(buildable_envelope())
    # East west alternative: the pool runs across the living room's frontage
    # toward the landscape plot, its deck 2 m either side, held inside the
    # envelope on the east.
    v0 = lv["v"][1] + 2.0
    pool = box(17.0, v0, 27.0, v0 + 4.0)
    deck = box(15.0, lv["v"][1], 27.4, v0 + 6.0)
    ground = Polygon(lay["outlines"]["ground"])
    if deck.within(env) and deck.buffer(-1e-6).disjoint(ground):
        out.append(("Alternative, east west across the living frontage", pool, deck,
                    "Pool 10 m along u, 2 m from the living room's glass, reaching "
                    "toward the landscape plot. Deck inside the envelope."))
    return out


def report() -> tuple[str, dict]:
    lay = yaml.safe_load(LAYOUTS.read_text(encoding="utf-8"))
    heights = load_massing()["heights"]
    ms = masses(lay, heights)
    lines = ["VJH-RPT-008  SHADE ON THE POOL DECK, AS PLANNED",
             "CONCEPT DESIGN, NOT FOR CONSTRUCTION", "",
             "Villa masses from brief/layouts.yaml, heights from brief/massing.yaml (D-030):"]
    for n, p, h in ms:
        lines.append(f"  {n:<40}{p.area:8.2f} m2 footprint, {h:5.2f} m to parapet")
    a = load_massing()["assessment"]
    lines += ["", f"Summer afternoons {a['summer_dates']} at {a['afternoon_hours']} h, "
                  f"winter midday {a['winter_dates']} at {a['winter_midday_hours']} h.",
              "Shade is the fraction of the pool and deck inside the villa's shadow.", ""]
    results = {}
    ref = score(next(o for o in options() if o.key == "C"))
    lines += [f"{'Phase 1 reference, option C blocks':<58}summer pm shade "
              f"{ref['summer_pm_shade'] * 100:5.1f} %   winter midday sun "
              f"{ref['winter_midday_sun'] * 100:5.1f} %", ""]
    for name, pool, deck, note in candidates(lay):
        target = grid_to_site(unary_union([pool, deck]))
        r = assess(ms, target)
        results[name] = r
        lines += [name, f"  {note}",
                  f"  pool u {pool.bounds[0]:.2f} to {pool.bounds[2]:.2f}, v {pool.bounds[1]:.2f} "
                  f"to {pool.bounds[3]:.2f}; deck {deck.area:.1f} m2 incl. pool",
                  f"  summer pm shade {r['summer_pm_shade'] * 100:5.1f} %   "
                  f"winter midday sun {r['winter_midday_sun'] * 100:5.1f} %"]
        lines += [f"    {k}  {v * 100:5.1f} %" for k, v in r["detail"].items()]
        lines.append("")
    best = max(results, key=lambda k: results[k]["summer_pm_shade"])
    cur = next(iter(results))
    lines += ["FINDING",
              f"  Best afternoon shade: {best}.",
              (f"  The current plan is the best of the candidates." if best == cur else
               f"  The current plan has {results[cur]['summer_pm_shade'] * 100:.1f} % against "
               f"{results[best]['summer_pm_shade'] * 100:.1f} % for the alternative."),
              "  The pool position is the owner's decision (D-037 is for review).", ""]
    return "\n".join(lines) + "\n", results


def main() -> int:
    text, _ = report()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(text)
    print(f"Wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
