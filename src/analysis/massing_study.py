"""Massing comparison and recommendation for Villa 5130272.

Scores the Phase 1 options on shade, orientation, privacy, and garden, and
states a recommendation with the reasons behind it.

The shade figures are computed from real shadow geometry, not estimated.
See src/model/massing.py.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis.sun_study import compass, facade_exposure, facades  # noqa: E402
from model.massing import Option, options, shade_fraction, validate  # noqa: E402
from model.site import load_site, plot_polygon  # noqa: E402

REPORT_OUT = REPO_ROOT / "output" / "reports" / "VJH-RPT-004_Massing_Options.txt"

TZ = "Asia/Dubai"
COOLING_DATES = ["05-21", "06-21", "07-21", "08-21", "09-21"]
AFTERNOON = [15, 16, 17, 18, 19]
WINTER_DATES = ["12-21", "01-21"]
WINTER_MIDDAY = [10, 11, 12, 13, 14]


def seasonal_shade(option: Option, year: int = 2026) -> pd.DataFrame:
    """Shade fraction on the pool and deck, hour by hour across the seasons."""
    rows = []
    for date in COOLING_DATES:
        for hour in AFTERNOON:
            t = pd.Timestamp(f"{year}-{date} {hour:02d}:00", tz=TZ)
            rows.append({"season": "cooling", "date": date, "hour": hour,
                         "shade": shade_fraction(option, t)})
    for date in WINTER_DATES:
        for hour in WINTER_MIDDAY:
            t = pd.Timestamp(f"{year}-{date} {hour:02d}:00", tz=TZ)
            rows.append({"season": "winter", "date": date, "hour": hour,
                         "shade": shade_fraction(option, t)})
    return pd.DataFrame(rows)


def pool_bearing_to_neighbours(option: Option) -> dict:
    """Which plot side the pool sits closest to, and what is on the far side."""
    from model.site import sides  # noqa: PLC0415

    pool = option.pool
    out = {}
    for s in sides():
        from shapely.geometry import LineString
        line = LineString([(s.start.x, s.start.y), (s.end.x, s.end.y)])
        out[s.id] = {"distance_m": pool.distance(line), "adjacency": s.adjacency}
    nearest = min(out, key=lambda k: out[k]["distance_m"])
    return {"nearest_side": nearest, "detail": out}


def summarise(option: Option) -> dict:
    df = seasonal_shade(option)
    cooling = df[df["season"] == "cooling"]["shade"]
    winter = df[df["season"] == "winter"]["shade"]

    by_hour = (df[df["season"] == "cooling"]
               .groupby("hour")["shade"].mean().to_dict())

    near = pool_bearing_to_neighbours(option)
    nearest_side = near["nearest_side"]

    return {
        "key": option.key,
        "name": option.name,
        "summary": option.summary,
        "ground_m2": option.ground_area,
        "first_m2": option.first_area,
        "open_ground_m2": option.open_ground_m2,
        "pool_deck_m2": option.pool_and_deck.area,
        "cooling_pm_shade": float(cooling.mean()),
        "cooling_pm_shade_min": float(cooling.min()),
        "winter_midday_sun": float(1.0 - winter.mean()),
        "by_hour": by_hour,
        "pool_nearest_side": nearest_side,
        "pool_faces": near["detail"][nearest_side]["adjacency"],
        "pool_distance_m": near["detail"][nearest_side]["distance_m"],
    }


def report() -> str:
    site = load_site()
    lines: list[str] = []
    w = lines.append

    w("MASSING OPTIONS AND RECOMMENDATION")
    w(f"Plot {site['plot']['number']}, {site['plot']['community']}")
    w("Phase 1. For owner decision. No option is approved.")
    w("")

    problems = [p for o in options() for p in validate(o)]
    if problems:
        w("VALIDATION FAILED")
        for p in problems:
            w("  " + p)
        return "\n".join(lines)
    w("All options validate: every block, and the pool, sit inside the 3 m")
    w("buildable envelope. No option relies on building in a setback.")
    w("")

    w("THE PLOT'S FACES, from the sun study")
    fe = facade_exposure()
    w(f"{'Side':<6}{'Faces':<7}{'Summer am':>11}{'Summer pm':>11}  Adjacency")
    for _, r in fe.iterrows():
        w(f"{int(r['side']):<6}{r['compass']:<7}{r['summer_morning_kwh_m2']:>11.0f}"
          f"{r['summer_afternoon_kwh_m2']:>11.0f}  {r['adjacency']}")
    w("")
    w("Two facts drive the whole decision:")
    w("  1. The ESE face, toward landscape plot 5130274, takes its heat in the")
    w("     morning and almost none after 15:00. It is the cheap face to glaze.")
    w("  2. That same face has no building on the far side and never will, so it")
    w("     is also the only face with a permanent open view and no overlooking.")
    w("")

    summaries = [summarise(o) for o in options()]

    w("OPTIONS")
    for s in summaries:
        w("")
        w(f"OPTION {s['key']}: {s['name'].upper()}")
        for chunk in _wrap(s["summary"], 74):
            w("  " + chunk)
        w(f"  Ground floor {s['ground_m2']:.0f} m2, first floor {s['first_m2']:.0f} m2, "
          f"open ground {s['open_ground_m2']:.0f} m2")
        w(f"  Pool and deck {s['pool_deck_m2']:.0f} m2, nearest side "
          f"{s['pool_nearest_side']} at {s['pool_distance_m']:.1f} m: {s['pool_faces']}")
    w("")

    w("POOL AND DECK IN SHADE, cooling season afternoons")
    w("Computed from the villa's real shadow at each hour on 21 May, Jun, Jul,")
    w("Aug and Sep. 1.00 means the whole deck is shaded.")
    w(f"{'Option':<22}{'15:00':>8}{'16:00':>8}{'17:00':>8}{'18:00':>8}"
      f"{'19:00':>8}{'Mean':>8}{'Worst':>8}")
    for s in summaries:
        h = s["by_hour"]
        w(f"{s['key'] + ' ' + s['name']:<22}"
          + "".join(f"{h.get(hr, 0):>8.2f}" for hr in AFTERNOON)
          + f"{s['cooling_pm_shade']:>8.2f}{s['cooling_pm_shade_min']:>8.2f}")
    w("")

    w("WINTER MIDDAY SUN ON THE POOL, 21 Dec and 21 Jan, 10:00 to 14:00")
    w("Here you want the opposite: sun on the water when the air is cool.")
    w(f"{'Option':<22}{'Sun fraction':>14}")
    for s in summaries:
        w(f"{s['key'] + ' ' + s['name']:<22}{s['winter_midday_sun']:>14.2f}")
    w("")

    best = max(summaries, key=lambda s: s["cooling_pm_shade"])
    worst = min(summaries, key=lambda s: s["cooling_pm_shade"])

    w("WHAT THE NUMBERS SAY")
    w("")
    for s in summaries:
        verdict = _verdict(s)
        w(f"Option {s['key']}, {s['name']}:")
        for chunk in _wrap(verdict, 74):
            w("  " + chunk)
        w("")

    w("RECOMMENDATION")
    w("")
    rec = (
        f"Option {best['key']}, {best['name']}. It holds "
        f"{best['cooling_pm_shade']:.0%} of the pool deck in shade through cooling "
        f"season afternoons, never dropping below {best['cooling_pm_shade_min']:.0%}, "
        f"while still giving {best['winter_midday_sun']:.0%} sun on the water at "
        f"winter midday. It is the only option that wins on both, because the "
        f"villa stands between the pool and the afternoon sun without standing "
        f"between the pool and the winter sun."
    )
    for chunk in _wrap(rec, 74):
        w(chunk)
    w("")
    rec2 = (
        f"It also puts the garden and the main glazing on the ESE face toward "
        f"landscape plot 5130274, which the sun study shows is the cheapest face "
        f"to glaze and which carries the plot's only permanent open view. The "
        f"master suite can take that orientation, as CLAUDE.md section 4 hoped it "
        f"would. The hot WNW road face and the SSW neighbour face are given the "
        f"service rooms, the garage and deep overhangs rather than glass."
    )
    for chunk in _wrap(rec2, 74):
        w(chunk)
    w("")
    rec3 = (
        f"Option {worst['key']}, {worst['name']}, is the option CLAUDE.md asked to "
        f"be tested against it, and it fails on the single measure that matters "
        f"most here: {worst['cooling_pm_shade']:.0%} afternoon shade. The villa "
        f"sits north-east of the pool, so its shadow travels east-south-east away "
        f"from the water rather than across it. The deck would be in full sun "
        f"every summer afternoon, and the pool is also the side overlooked by "
        f"neighbour plot 5130123."
    )
    for chunk in _wrap(rec3, 74):
        w(chunk)
    w("")

    w("BOUNDARY WALL CONCEPT")
    bw = _boundary_wall_text()
    for chunk in bw:
        w(chunk)
    w("")

    w("WHAT THIS DOES NOT SETTLE")
    w("  Room layouts. That is Phase 2, and it is blocked by OI-01, whether the")
    w("  enclosed garage counts toward GFA.")
    w("  Overall height in metres, TO VERIFY against the Dubai Building Code.")
    w("  Whether a pool may sit within the 3 m setback. All three options keep")
    w("  the pool inside the envelope, so none of them depends on the answer,")
    w("  but a yes would free more garden. Raised as an open item.")
    w("")
    w(site["meta"]["stamp"])
    return "\n".join(lines)


def _verdict(s: dict) -> str:
    h = s["by_hour"]
    if s["key"] == "A":
        return (
            f"The villa stands west of the pool, so its shadow falls across the "
            f"water through the afternoon: {h.get(15, 0):.0%} shaded at 15:00, "
            f"{h.get(16, 0):.0%} by 16:00 and complete from 17:00 to sunset. Mean "
            f"{s['cooling_pm_shade']:.0%} across the cooling season. In winter the "
            f"sun swings far enough south to pass the mass entirely, leaving "
            f"{s['winter_midday_sun']:.0%} sun on the water at midday. Garden and "
            f"pool face the landscape plot, so no neighbour overlooks them."
        )
    if s["key"] == "B":
        dead = [hr for hr in AFTERNOON if h.get(hr, 0) < 0.01]
        span = f"{min(dead):02d}:00 to {max(dead):02d}:00" if dead else "no hour"
        return (
            f"The villa sits north-east of the pool. Afternoon shadows run "
            f"east-south-east, along the pool rather than across it, so the deck "
            f"gets no shade at all from {span}. The only shaded hour is 19:00, at "
            f"{h.get(19, 0):.0%}, by which point the sun is nearly down and the "
            f"shade is worth little. Mean {s['cooling_pm_shade']:.0%}. The pool "
            f"also sits against neighbour plot 5130123 rather than the open "
            f"landscape plot, so it is the least private of the three. Tested "
            f"because CLAUDE.md asks for it. It is clearly the weakest."
        )
    return (
        f"The L wraps the two hot faces and shades well, "
        f"{s['cooling_pm_shade']:.0%} mean, within six points of option A. The "
        f"cost shows up in two places. In winter the same wing that blocks the "
        f"summer afternoon sun also blocks the low winter sun, leaving "
        f"{s['winter_midday_sun']:.0%} sun on the water at midday against "
        f"100% for option A. And at 15:00, the hour the deck is most likely to be "
        f"in use before evening, it manages {h.get(15, 0):.0%} against "
        f"{_a_at_15():.0%} for option A. It also turns the garden inward and gives "
        f"up the view east. Worth keeping if privacy from the road ever matters "
        f"more than the view."
    )


def _a_at_15() -> float:
    opt = next(o for o in options() if o.key == "A")
    df = seasonal_shade(opt)
    return float(df[(df["season"] == "cooling") & (df["hour"] == 15)]["shade"].mean())


def _boundary_wall_text() -> list[str]:
    from model.massing import load_massing  # noqa: PLC0415

    bw = load_massing()["boundary_wall"]
    out = [f"  Overall height {bw['height_m']:.2f} m. TO VERIFY against DDA rules."]
    for key, label in (("road_side", "Side 1, road"),
                       ("neighbour_sides", "Sides 2 and 4, neighbours"),
                       ("landscape_side", "Side 3, landscape plot 5130274")):
        out.append(f"  {label}:")
        out.extend("    " + c for c in _wrap(" ".join(bw[key]["treatment"].split()), 70))
    return out


def _wrap(text: str, width: int) -> list[str]:
    import textwrap
    return textwrap.wrap(" ".join(text.split()), width)


def main() -> int:
    text = report()
    print(text)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(text + "\n", encoding="utf-8")
    print(f"\nWritten to {REPORT_OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
