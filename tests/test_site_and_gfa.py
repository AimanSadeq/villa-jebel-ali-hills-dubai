"""Automated checks for the Villa 5130272 site geometry and GFA limit.

Run: .\\.venv\\Scripts\\python.exe -m pytest -q

These tests guard the two hard constraints from CLAUDE.md: the 3 m setbacks on
all sides and the 662.99 m2 GFA cap.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis.gfa_check import load_program, rooms, totals  # noqa: E402
from model.site import (  # noqa: E402
    area_check,
    buildable_envelope,
    load_site,
    plot_polygon,
    sides,
)

# Tolerances. The boundary coordinates are scaled from the DDA plan, which is
# for illustration only, so exact agreement is not expected or required.
PLOT_AREA_TOL_PCT = 0.5
SIDE_LENGTH_TOL_PCT = 1.0


# Site geometry


def test_plot_polygon_is_valid_and_closed():
    poly = plot_polygon()
    assert poly.is_valid
    assert poly.area > 0
    assert len(poly.exterior.coords) == 6  # five vertices plus the closing point


def test_plot_area_matches_official_dda_figure():
    a = area_check()
    assert abs(a["plot_area_deviation_pct"]) < PLOT_AREA_TOL_PCT, (
        f"Computed plot area {a['computed_plot_area_m2']:.2f} m2 deviates "
        f"{a['plot_area_deviation_pct']:.3f}% from the official "
        f"{a['official_plot_area_m2']:.2f} m2"
    )


@pytest.mark.parametrize("side", sides(), ids=lambda s: f"side_{s.id}")
def test_side_length_matches_dda_plan(side):
    assert abs(side.deviation_pct) < SIDE_LENGTH_TOL_PCT, (
        f"Side {side.id} computes to {side.computed_length_m:.2f} m against "
        f"{side.stated_length_m:.2f} m stated on the plan"
    )


def test_envelope_respects_the_setback_everywhere():
    """No point of the envelope may sit closer to the boundary than the setback."""
    site = load_site()
    setback = float(site["regulations"]["setback_m"])
    plot, env = plot_polygon(site), buildable_envelope(site)

    assert env.within(plot), "Buildable envelope escapes the plot boundary"

    distance = plot.exterior.distance(env)
    assert distance >= setback - 1e-6, (
        f"Envelope comes within {distance:.4f} m of the boundary, "
        f"closer than the {setback} m setback"
    )


def test_envelope_is_a_single_piece():
    """A split envelope would change the design problem, so flag it loudly."""
    assert not area_check()["envelope_is_split"]


def test_gfa_not_the_setbacks_is_the_binding_constraint():
    a = area_check()
    assert a["binding_constraint"] == "GFA"
    assert a["max_gfa_m2"] < a["geometric_capacity_m2"]


def test_site_yaml_flags_provisional_data_as_to_verify():
    site = load_site()
    assert site["boundary"]["to_verify"] is True
    assert site["orientation"]["to_verify"] is True
    assert site["location"]["to_verify"] is True


# GFA


def test_confirmed_gfa_areas_stay_under_the_cap():
    """The hard limit. Never exceed 662.99 m2 with areas known to count."""
    t = totals()
    core = t["scenarios"]["core"]
    assert core["gross_high"] <= t["cap_m2"], (
        f"Confirmed GFA areas reach {core['gross_high']:.2f} m2 against a cap of "
        f"{t['cap_m2']:.2f} m2"
    )


def test_design_target_holds_a_margin_below_the_cap():
    t = totals()
    assert t["design_target_m2"] < t["cap_m2"]
    assert t["design_margin_m2"] > 0


def test_unverified_areas_are_tracked_separately():
    """Garage and roof enclosure must never be silently folded into the total."""
    keys = {r.key for r in rooms() if r.unverified}
    assert keys == {"garage", "roof_enclosure"}


def test_voids_are_excluded_from_gfa():
    """CLAUDE.md section 3: double-height voids do not add upper-floor area."""
    program = load_program()
    assert program["voids"], "Voids must be listed so they are never double counted"
    for void in program["voids"]:
        assert void["gfa"] == "excluded"


def test_every_room_declares_its_gfa_treatment():
    for room in rooms():
        assert room.gfa in {"counts", "unverified", "excluded"}, (
            f"{room.key} has an unrecognised gfa value: {room.gfa}"
        )


def test_master_suite_is_much_larger_than_the_other_bedrooms():
    """CLAUDE.md section 4: 2.2 to 2.5 times the other bedrooms."""
    by_key = {r.key: r for r in rooms()}
    master = by_key["master_suite"]
    others = [by_key[k] for k in ("bedroom_2", "bedroom_3", "bedroom_4")]

    ratio_low = master.low_m2 / max(o.high_m2 for o in others)
    ratio_high = master.high_m2 / min(o.low_m2 for o in others)
    assert ratio_low >= 2.0, (
        f"Master suite at its minimum is only {ratio_low:.2f} times the largest "
        "other bedroom. The brief asks for 2.2 to 2.5."
    )
    assert ratio_high <= 2.7


def test_majlis_has_its_own_guest_powder_room():
    keys = {r.key for r in rooms()}
    assert {"majlis", "guest_powder"} <= keys


def test_guest_bedroom_is_the_only_bedroom_on_the_ground_floor():
    ground_bedrooms = [
        r for r in rooms() if r.floor == "ground" and "bedroom" in r.key
    ]
    assert [r.key for r in ground_bedrooms] == ["guest_bedroom"]


def test_stair_and_lift_land_on_every_level_they_serve():
    """The elevator serves ground, first, and roof, so each needs a landing."""
    keys = {r.key for r in rooms()}
    assert {"stair_lift_ground", "stair_lift_first", "roof_enclosure"} <= keys
