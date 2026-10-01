"""Sun study for Villa 5130272, Jebel Ali Hills, Dubai.

Sun paths, facade solar exposure, and shadow geometry for the massing options.

Site position and orientation are VERIFIED, not assumed: see docs/open-items.md
OI-04 and OI-06. Plan-up is true north to within -0.02 degrees.

Solar position: NREL SPA via pvlib.
Clear-sky irradiance: Ineichen and Perez model with the Linke turbidity
climatology bundled with pvlib. Clear-sky is the right basis for a Dubai shading
study, where the design problem is the cloudless day, not the average day.
Transposition to vertical surfaces: Perez 1990 sky diffuse model.

These are modelled figures for design comparison, not measured site data.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model.site import load_site, plot_polygon, sides  # noqa: E402

REPORT_OUT = REPO_ROOT / "output" / "reports" / "VJH-RPT-003_Sun_Study.txt"
CHART_OUT = REPO_ROOT / "output" / "pdf" / "VJH-SS-001_Sun_Study.pdf"

# Key dates for a Dubai study. Peak cooling season matters more than the
# equinoxes, so August is included alongside the solstices.
KEY_DATES = {
    "21 Jun, summer solstice": "06-21",
    "21 Aug, peak cooling": "08-21",
    "21 Mar, equinox": "03-21",
    "21 Dec, winter solstice": "12-21",
}

COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def compass(bearing: float) -> str:
    return COMPASS[int((bearing % 360) / 22.5 + 0.5) % 16]


@lru_cache(maxsize=1)
def location() -> pvlib.location.Location:
    loc = load_site()["location"]
    return pvlib.location.Location(
        latitude=float(loc["latitude"]),
        longitude=float(loc["longitude"]),
        tz=loc["timezone"],
        name=loc["name"],
    )


@lru_cache(maxsize=4)
def year_series(freq: str = "15min", year: int = 2026) -> pd.DatetimeIndex:
    loc = location()
    return pd.date_range(f"{year}-01-01", f"{year}-12-31 23:59", freq=freq, tz=loc.tz)


@lru_cache(maxsize=4)
def clearsky(freq: str = "15min", year: int = 2026) -> pd.DataFrame:
    """Clear-sky irradiance and solar position for a full year."""
    loc, times = location(), year_series(freq, year)
    sp = loc.get_solarposition(times)
    cs = loc.get_clearsky(times, model="ineichen")
    out = cs.join(sp[["apparent_zenith", "zenith", "azimuth", "apparent_elevation"]])
    out["up"] = out["apparent_elevation"] > 0
    # The Perez sky diffuse model needs extraterrestrial irradiance and relative
    # airmass as well as the three irradiance components.
    out["dni_extra"] = pvlib.irradiance.get_extra_radiation(times)
    out["airmass"] = pvlib.atmosphere.get_relative_airmass(out["apparent_zenith"])
    return out


# Facades


@dataclass(frozen=True)
class Facade:
    """A plot side, with the azimuth its outward face looks toward."""

    side_id: int
    adjacency: str
    azimuth: float          # degrees clockwise from true north
    length_m: float

    @property
    def compass(self) -> str:
        return compass(self.azimuth)


def facades() -> list[Facade]:
    """Outward normal azimuth of each plot side.

    Determined per side by stepping off the edge midpoint along a candidate
    normal and testing whether that point lands inside the plot, rather than by
    assuming a winding direction. plot_polygon normalises the ring to
    counter-clockwise, which reverses the vertex order given in site.yaml, so any
    method relying on the traversal order matching each side's own from and to
    silently misassigns every facade.
    """
    from shapely.geometry import Point

    poly = plot_polygon()
    out: list[Facade] = []
    for s in sides():
        dx, dy = s.end.x - s.start.x, s.end.y - s.start.y
        length = float(np.hypot(dx, dy))
        if length == 0:
            continue
        nx, ny = dy / length, -dx / length

        mx, my = (s.start.x + s.end.x) / 2.0, (s.start.y + s.end.y) / 2.0
        if poly.contains(Point(mx + nx * 0.5, my + ny * 0.5)):
            nx, ny = -nx, -ny   # that candidate pointed inward, so flip it

        az = float(np.degrees(np.arctan2(nx, ny)) % 360)
        out.append(Facade(s.id, s.adjacency, az, s.computed_length_m))
    return sorted(out, key=lambda f: f.side_id)


def irradiation_by_azimuth(
    azimuths: np.ndarray | None = None,
    tilt: float = 90.0,
    freq: str = "15min",
) -> pd.DataFrame:
    """Annual and summer clear-sky irradiation on vertical surfaces.

    Returns kWh/m2 per orientation. Summer is May to September inclusive, which
    is the Dubai cooling season.
    """
    if azimuths is None:
        azimuths = np.arange(0, 360, 10.0)

    cs = clearsky(freq)
    step_h = pd.Timedelta(freq).total_seconds() / 3600.0
    summer = cs.index.month.isin([5, 6, 7, 8, 9])

    rows = []
    for az in azimuths:
        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=tilt,
            surface_azimuth=float(az),
            solar_zenith=cs["apparent_zenith"],
            solar_azimuth=cs["azimuth"],
            dni=cs["dni"],
            ghi=cs["ghi"],
            dhi=cs["dhi"],
            dni_extra=cs["dni_extra"],
            airmass=cs["airmass"],
            model="perez-driesse",
        )
        total = poa["poa_global"].fillna(0.0)
        # Split the summer load by time of day. Peak cooling demand in Dubai is
        # late afternoon, when ambient air is hottest, so a kWh landing at 17:00
        # costs far more than the same kWh at 08:00.
        morning = summer & (cs.index.hour < 12)
        afternoon = summer & (cs.index.hour >= 15)
        rows.append({
            "azimuth": float(az),
            "compass": compass(az),
            "annual_kwh_m2": total.sum() * step_h / 1000.0,
            "summer_kwh_m2": total[summer].sum() * step_h / 1000.0,
            "peak_w_m2": float(total.max()),
            "summer_morning_kwh_m2": total[morning].sum() * step_h / 1000.0,
            "summer_afternoon_kwh_m2": total[afternoon].sum() * step_h / 1000.0,
        })
    return pd.DataFrame(rows)


def facade_exposure(freq: str = "15min") -> pd.DataFrame:
    """Solar exposure of this plot's actual facade orientations."""
    fs = facades()
    df = irradiation_by_azimuth(np.array([f.azimuth for f in fs]), freq=freq)
    df.insert(0, "side", [f.side_id for f in fs])
    df.insert(1, "adjacency", [f.adjacency for f in fs])
    df.insert(2, "length_m", [f.length_m for f in fs])
    return df


def sun_path(date_md: str, year: int = 2026, freq: str = "10min") -> pd.DataFrame:
    """Altitude and azimuth through one day, daylight hours only."""
    loc = location()
    times = pd.date_range(f"{year}-{date_md} 00:00", f"{year}-{date_md} 23:59",
                          freq=freq, tz=loc.tz)
    sp = loc.get_solarposition(times)
    return sp[sp["apparent_elevation"] > 0]


def daily_extremes() -> pd.DataFrame:
    """Sunrise, sunset, noon altitude and azimuth on the key dates."""
    loc = location()
    rows = []
    for label, md in KEY_DATES.items():
        day = pd.date_range(f"2026-{md}", periods=1, freq="D", tz=loc.tz)
        rs = loc.get_sun_rise_set_transit(day, method="spa")
        sp = sun_path(md)
        noon = sp["apparent_elevation"].idxmax()
        rows.append({
            "date": label,
            "sunrise": rs["sunrise"].iloc[0].strftime("%H:%M"),
            "sunset": rs["sunset"].iloc[0].strftime("%H:%M"),
            "daylight_h": (rs["sunset"].iloc[0] - rs["sunrise"].iloc[0]).total_seconds() / 3600,
            "noon_altitude": sp.loc[noon, "apparent_elevation"],
            "noon_azimuth": sp.loc[noon, "azimuth"],
            "sunrise_azimuth": sp["azimuth"].iloc[0],
            "sunset_azimuth": sp["azimuth"].iloc[-1],
        })
    return pd.DataFrame(rows)


def sun_vector(when: pd.Timestamp) -> tuple[float, float, float] | None:
    """Unit vector pointing from the ground toward the sun, in site x/y/z."""
    sp = location().get_solarposition(pd.DatetimeIndex([when]))
    alt = float(sp["apparent_elevation"].iloc[0])
    az = float(sp["azimuth"].iloc[0])
    if alt <= 0:
        return None
    a, z = np.radians(alt), np.radians(az)
    return (np.cos(a) * np.sin(z), np.cos(a) * np.cos(z), np.sin(a))


def report(freq: str = "15min") -> str:
    site = load_site()
    loc, lines = location(), []
    w = lines.append

    w("SUN STUDY")
    w(f"Plot {site['plot']['number']}, {site['plot']['community']}")
    w(f"Site {loc.latitude:.6f} N, {loc.longitude:.6f} E, {loc.tz}")
    w(f"Orientation: plan-up is true north, VERIFIED, mean bearing error "
      f"{site['orientation']['mean_bearing_error_deg']:+.2f} deg")
    w("")
    w("Method: NREL SPA solar position. Ineichen clear-sky irradiance with the")
    w("pvlib Linke turbidity climatology. Perez-Driesse transposition to vertical")
    w(f"surfaces. {freq} timesteps through a full year.")
    w("Clear-sky, not typical-year: the design case in Dubai is the cloudless day.")
    w("Modelled figures for design comparison, not measured site data.")
    w("")

    w("SUN GEOMETRY ON KEY DATES")
    w(f"{'Date':<24}{'Sunrise':>8}{'Sunset':>8}{'Daylight':>10}"
      f"{'Noon alt':>10}{'Rise azi':>10}{'Set azi':>9}")
    for _, r in daily_extremes().iterrows():
        w(f"{r['date']:<24}{r['sunrise']:>8}{r['sunset']:>8}{r['daylight_h']:>9.1f}h"
          f"{r['noon_altitude']:>9.1f}d{r['sunrise_azimuth']:>9.1f}d"
          f"{r['sunset_azimuth']:>8.1f}d")
    w("")
    w("At 24.9 N the summer sun passes nearly overhead, so at noon it is roofs and")
    w("not walls that take the load. The problem is the low afternoon sun in the")
    w("west, which strikes glass almost head on while the air is at its hottest.")
    w("")

    w("SOLAR EXPOSURE BY ORIENTATION, vertical surface, kWh/m2")
    allaz = irradiation_by_azimuth(freq=freq).sort_values("annual_kwh_m2",
                                                          ascending=False)
    w(f"{'Facing':<8}{'Azimuth':>9}{'Annual':>10}{'Summer':>10}"
      f"{'Summer pm':>11}{'Peak W/m2':>11}")
    for _, r in allaz.head(6).iterrows():
        w(f"{r['compass']:<8}{r['azimuth']:>8.0f}d{r['annual_kwh_m2']:>10.0f}"
          f"{r['summer_kwh_m2']:>10.0f}{r['summer_afternoon_kwh_m2']:>11.0f}"
          f"{r['peak_w_m2']:>11.0f}")
    w("   ...")
    for _, r in allaz.tail(3).iterrows():
        w(f"{r['compass']:<8}{r['azimuth']:>8.0f}d{r['annual_kwh_m2']:>10.0f}"
          f"{r['summer_kwh_m2']:>10.0f}{r['summer_afternoon_kwh_m2']:>11.0f}"
          f"{r['peak_w_m2']:>11.0f}")
    w("")
    best = allaz.iloc[-1]
    worst = allaz.iloc[0]
    w(f"Worst orientation: {worst['compass']} at {worst['annual_kwh_m2']:.0f} kWh/m2 "
      f"annual, {worst['summer_kwh_m2']:.0f} in summer.")
    w(f"Best orientation:  {best['compass']} at {best['annual_kwh_m2']:.0f} kWh/m2 "
      f"annual, {best['summer_kwh_m2']:.0f} in summer.")
    w(f"Ratio worst to best: {worst['annual_kwh_m2'] / best['annual_kwh_m2']:.2f} to 1.")
    w("")

    w("THIS PLOT'S FACADES")
    w(f"{'Side':<6}{'Faces':<7}{'Azi':>6}{'Len':>7}{'Annual':>8}{'Summer':>8}"
      f"{'Sum am':>8}{'Sum pm':>8}  Adjacency")
    fe = facade_exposure(freq=freq)
    for _, r in fe.iterrows():
        w(f"{int(r['side']):<6}{r['compass']:<7}{r['azimuth']:>5.0f}d"
          f"{r['length_m']:>6.1f}m{r['annual_kwh_m2']:>8.0f}{r['summer_kwh_m2']:>8.0f}"
          f"{r['summer_morning_kwh_m2']:>8.0f}{r['summer_afternoon_kwh_m2']:>8.0f}"
          f"  {r['adjacency']}")
    w("")
    w("Totals alone are misleading. Peak cooling demand in Dubai is late")
    w("afternoon, when ambient air is at its hottest, so a kWh arriving at 17:00")
    w("costs the plant far more than the same kWh at 08:00. Read the am and pm")
    w("columns, not the summer total.")
    w("")

    by_side = {int(r["side"]): r for _, r in fe.iterrows()}
    east, road = by_side[3], by_side[1]
    w(f"Side 3, the landscape plot face, takes "
      f"{east['summer_morning_kwh_m2']:.0f} kWh/m2 in summer mornings against "
      f"only {east['summer_afternoon_kwh_m2']:.0f} in the afternoons.")
    w(f"Side 1, the road face, takes {road['summer_afternoon_kwh_m2']:.0f} kWh/m2 "
      f"in summer afternoons, "
      f"{road['summer_afternoon_kwh_m2'] / max(east['summer_afternoon_kwh_m2'], 1e-9):.1f} "
      f"times side 3.")
    w("")
    w("So the east face, which is also the face with the permanent open view and")
    w("no overlooking neighbour, is the cheap one to glaze. The west and")
    w("south-west faces are the expensive ones and need deep shading.")
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
