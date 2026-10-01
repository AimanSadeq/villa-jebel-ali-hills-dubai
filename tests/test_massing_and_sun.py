"""Automated checks for the Phase 1 sun study and massing options.

Run: .\\.venv\\Scripts\\python.exe -m pytest -q

These guard the findings that the Phase 1 recommendation rests on, so a later
change to the geometry or the brief cannot quietly invalidate it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis.sun_study import facade_exposure, location, sun_vector  # noqa: E402
from model.massing import (  # noqa: E402
    load_massing,
    option_shadow,
    options,
    shade_fraction,
    validate,
    wall_to_boundary,
)
from model.site import load_site  # noqa: E402

TZ = "Asia/Dubai"
ALL = options()


# Geometry


@pytest.mark.parametrize("option", ALL, ids=lambda o: o.key)
def test_option_sits_inside_the_buildable_envelope(option):
    problems = validate(option)
    assert not problems, "; ".join(problems)


@pytest.mark.parametrize("option", ALL, ids=lambda o: o.key)
def test_pool_is_the_size_the_brief_asks_for(option):
    """CLAUDE.md section 4: swimming pool, 10 x 4 m."""
    assert option.pool.area == pytest.approx(40.0, abs=0.5)


@pytest.mark.parametrize("option", ALL, ids=lambda o: o.key)
def test_every_wall_respects_the_three_metre_setback(option):
    setback = float(load_site()["regulations"]["setback_m"])
    for r in wall_to_boundary(option):
        assert r["distance_m"] >= setback - 1e-6, (
            f"option {option.key}: wall is {r['distance_m']:.2f} m from side "
            f"{r['side']} ({r['adjacency']}), inside the {setback} m setback"
        )


@pytest.mark.parametrize("option", ALL, ids=lambda o: o.key)
def test_ground_floor_is_close_to_the_footprint_target(option):
    target = float(load_massing()["targets"]["ground_footprint_m2"])
    assert option.ground.area == pytest.approx(target, abs=2.0)


# Shadows


@pytest.mark.parametrize("option", ALL, ids=lambda o: o.key)
def test_no_shadow_when_the_sun_is_below_the_horizon(option):
    midnight = pd.Timestamp("2026-06-21 00:00", tz=TZ)
    assert sun_vector(midnight) is None
    assert option_shadow(option, (0.0, 1.0, -0.1)).is_empty


@pytest.mark.parametrize("option", ALL, ids=lambda o: o.key)
def test_shadow_falls_away_from_the_sun(option):
    """A westerly afternoon sun must throw the shadow east of the villa."""
    when = pd.Timestamp("2026-08-21 16:00", tz=TZ)
    sun = sun_vector(when)
    assert sun is not None and sun[0] < 0, "16:00 August sun should be westerly"

    shade = option_shadow(option, sun)
    assert shade.centroid.x > option.ground.centroid.x, (
        "shadow centroid should sit east of the mass when the sun is in the west"
    )


def test_option_a_shades_the_pool_through_the_afternoon():
    """The Phase 1 recommendation rests on this."""
    a = next(o for o in ALL if o.key == "A")
    for hour in (16, 17, 18):
        when = pd.Timestamp(f"2026-08-21 {hour:02d}:00", tz=TZ)
        assert shade_fraction(a, when) > 0.9, (
            f"option A gives only {shade_fraction(a, when):.0%} pool shade at "
            f"{hour}:00 on 21 August"
        )


def test_option_b_does_not_shade_the_pool_in_the_afternoon():
    """The reason option B is rejected. If this ever passes, revisit the
    recommendation rather than deleting the test."""
    b = next(o for o in ALL if o.key == "B")
    for hour in (15, 16, 17, 18):
        when = pd.Timestamp(f"2026-08-21 {hour:02d}:00", tz=TZ)
        assert shade_fraction(b, when) < 0.05


def test_the_recommended_option_has_the_best_afternoon_shade():
    """Compared on the mean across the afternoon, which is what the
    recommendation rests on. At 17:00 alone both A and C are saturated at 100%,
    so a single hour cannot separate them."""
    hours = (15, 16, 17, 18)

    def mean_shade(option):
        return sum(
            shade_fraction(option, pd.Timestamp(f"2026-08-21 {h:02d}:00", tz=TZ))
            for h in hours
        ) / len(hours)

    ranked = sorted(ALL, key=mean_shade, reverse=True)
    assert ranked[0].key == "A"
    assert mean_shade(ranked[0]) > mean_shade(ranked[1])


# Sun study


def test_site_location_is_the_verified_one():
    loc = location()
    assert loc.latitude == pytest.approx(24.897528, abs=1e-5)
    assert loc.longitude == pytest.approx(54.964976, abs=1e-5)
    assert str(loc.tz) == TZ


def test_summer_noon_sun_is_nearly_overhead():
    """At 24.9 N the solstice sun passes within a few degrees of the zenith,
    which is why the roof and not the walls takes the midday load.

    Measured at solar noon, the daily maximum, which falls near 12:25 local
    rather than at 12:00 on the clock.
    """
    times = pd.date_range("2026-06-21 11:00", "2026-06-21 13:30",
                          freq="5min", tz=TZ)
    peak = location().get_solarposition(times)["apparent_elevation"].max()
    assert peak > 88.0, f"solstice solar noon altitude is only {peak:.2f} deg"


def test_the_landscape_plot_face_takes_its_heat_in_the_morning():
    """The core finding behind putting the garden and the glazing on side 3."""
    fe = {int(r["side"]): r for _, r in facade_exposure(freq="60min").iterrows()}
    east = fe[3]
    assert east["summer_morning_kwh_m2"] > 4 * east["summer_afternoon_kwh_m2"]


def test_the_road_face_is_the_hot_afternoon_one():
    fe = {int(r["side"]): r for _, r in facade_exposure(freq="60min").iterrows()}
    assert fe[1]["summer_afternoon_kwh_m2"] > 3 * fe[3]["summer_afternoon_kwh_m2"]
