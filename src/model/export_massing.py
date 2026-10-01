"""Export Phase 1 massing and sun data for the browser viewer.

Writes viewer/public/data/massing.json. The viewer renders from this file and
never recomputes anything, so what you see in the browser is the same geometry
and the same solar positions that produced the reports and the PDF sheets.

Sun positions are exported as a table rather than reimplemented in JavaScript.
A second implementation would be a second chance to be wrong.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis.massing_study import summarise  # noqa: E402
from analysis.sun_study import facade_exposure, location  # noqa: E402
from model.massing import load_massing, options, wall_to_boundary  # noqa: E402
from model.site import buildable_envelope, load_site, plot_polygon, sides  # noqa: E402

OUT = REPO_ROOT / "viewer" / "public" / "data" / "massing.json"

# Months sampled on the 21st, the convention used throughout the sun study.
MONTHS = list(range(1, 13))
HOURS = list(range(5, 21))


def ring(geom) -> list[list[float]]:
    return [[round(x, 3), round(y, 3)] for x, y in geom.exterior.coords[:-1]]


def _coords(seq) -> list[list[float]]:
    return [[round(x, 3), round(y, 3)] for x, y in list(seq)[:-1]]


def rings(geom) -> list[dict]:
    """Polygons as {shell, holes}.

    Holes matter: the pool deck is the deck area with the pool cut out of it, so
    exporting only the outer ring would bury the water inside the deck solid.
    """
    geoms = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    return [
        {"shell": _coords(g.exterior.coords),
         "holes": [_coords(i.coords) for i in g.interiors]}
        for g in geoms if not g.is_empty
    ]


def sun_table(year: int = 2026) -> list[dict]:
    """Altitude and azimuth for each month and hour, from the same pvlib call
    chain the reports use."""
    loc = location()
    out = []
    for month in MONTHS:
        stamps = pd.DatetimeIndex(
            [pd.Timestamp(f"{year}-{month:02d}-21 {h:02d}:00", tz=loc.tz)
             for h in HOURS]
        )
        sp = loc.get_solarposition(stamps)
        out.append({
            "month": month,
            "altitude": [round(float(v), 3) for v in sp["apparent_elevation"]],
            "azimuth": [round(float(v), 3) for v in sp["azimuth"]],
        })
    return out


def build() -> dict:
    site = load_site()
    m = load_massing()
    loc = location()

    opts = []
    for o in options():
        s = summarise(o)
        opts.append({
            "key": o.key,
            "name": o.name,
            "summary": o.summary,
            "ground": rings(o.ground),
            "first": rings(o.first),
            "garage": rings(o.garage),
            "pool": rings(o.pool),
            # The deck is drawn with the pool cut out, so the viewer can show
            # water in a real opening rather than a plane buried in the deck.
            "deck": rings(o.deck.difference(o.pool)),
            "driveway": rings(o.driveway),
            "wallToBoundary": [
                {
                    "side": r["side"],
                    "adjacency": r["adjacency"],
                    "distanceM": round(r["distance_m"], 2),
                    "isMainAccess": r["is_main_access"],
                    "meetsSetback": r["meets_setback"],
                    "from": [round(r["from_xy"][0], 3), round(r["from_xy"][1], 3)],
                    "to": [round(r["to_xy"][0], 3), round(r["to_xy"][1], 3)],
                }
                for r in wall_to_boundary(o)
            ],
            "metrics": {
                "groundM2": round(s["ground_m2"], 1),
                "firstM2": round(s["first_m2"], 1),
                "openGroundM2": round(s["open_ground_m2"], 1),
                "poolDeckM2": round(s["pool_deck_m2"], 1),
                "coolingPmShade": round(s["cooling_pm_shade"], 3),
                "coolingPmShadeMin": round(s["cooling_pm_shade_min"], 3),
                "winterMiddaySun": round(s["winter_midday_sun"], 3),
                "byHour": {str(k): round(v, 3) for k, v in s["by_hour"].items()},
                "poolNearestSide": s["pool_nearest_side"],
                "poolFaces": s["pool_faces"],
            },
        })

    recommended = max(opts, key=lambda o: o["metrics"]["coolingPmShade"])["key"]

    fe = facade_exposure()
    facade_rows = [{
        "side": int(r["side"]),
        "compass": r["compass"],
        "azimuth": round(float(r["azimuth"]), 1),
        "adjacency": r["adjacency"],
        "annual": round(float(r["annual_kwh_m2"])),
        "summerAm": round(float(r["summer_morning_kwh_m2"])),
        "summerPm": round(float(r["summer_afternoon_kwh_m2"])),
    } for _, r in fe.iterrows()]

    return {
        "meta": {
            "stamp": site["meta"]["stamp"],
            "plot": site["plot"]["number"],
            "community": site["plot"]["community"],
            "phase": 1,
            "note": "Generated by src/model/export_massing.py. Do not edit by hand.",
        },
        "site": {
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "timezone": loc.tz,
            "trueNorthVerified": site["orientation"]["to_verify"] is False,
            "plotAreaM2": site["plot"]["area_m2"],
            "maxGfaM2": site["regulations"]["max_gfa_m2"],
            "setbackM": site["regulations"]["setback_m"],
            "gridBearingDeg": m["grid"]["bearing_deg"],
        },
        "plot": ring(plot_polygon()),
        "envelope": ring(buildable_envelope()),
        "sides": [{
            "id": s.id,
            "adjacency": s.adjacency,
            "start": [round(s.start.x, 3), round(s.start.y, 3)],
            "end": [round(s.end.x, 3), round(s.end.y, 3)],
            "isMainAccess": s.is_main_access,
        } for s in sides()],
        "heights": {
            "ground": m["heights"]["ground_floor_m"],
            "first": m["heights"]["first_floor_m"],
            "parapet": m["heights"]["parapet_m"],
            "overall": m["heights"]["overall_m"],
        },
        "boundaryWall": {
            "heightM": m["boundary_wall"]["height_m"],
            # Per side: how much is solid, and how far the lighter screen goes.
            "bySide": {
                str(side): {
                    "solid": m["boundary_wall"][key]["solid_height_m"],
                    "screenTo": m["boundary_wall"][key]["screen_to_m"],
                    "treatment": " ".join(
                        m["boundary_wall"][key]["treatment"].split()),
                }
                for key, sides_list in (("road_side", [1]),
                                        ("neighbour_sides", [2, 4]),
                                        ("landscape_side", [3]))
                for side in sides_list
            },
        },
        "facades": facade_rows,
        "options": opts,
        "recommended": recommended,
        "sun": {"hours": HOURS, "months": MONTHS, "table": sun_table()},
    }


def main() -> int:
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    size = OUT.stat().st_size / 1024
    print(f"Wrote {OUT.relative_to(REPO_ROOT)}  ({size:.0f} kB)")
    print(f"  {len(data['options'])} options, recommended {data['recommended']}")
    print(f"  sun table {len(data['sun']['table'])} months x "
          f"{len(data['sun']['hours'])} hours")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
