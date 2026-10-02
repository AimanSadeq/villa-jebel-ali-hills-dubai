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
    vertices,
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


def test_site_yaml_still_flags_the_boundary_as_to_verify():
    """The Demarcation Certificate is still outstanding, so this stays true."""
    assert load_site()["boundary"]["to_verify"] is True


def test_orientation_and_location_are_verified_and_carry_their_evidence():
    """Verified against the DDA GIS on 2026-10-01. Guards against silent reversion."""
    site = load_site()

    orientation = site["orientation"]
    assert orientation["plan_up_is_true_north"] is True
    assert orientation["to_verify"] is False
    assert orientation["verified_on"] == "2026-10-01"
    assert abs(orientation["mean_bearing_error_deg"]) < 0.5, (
        "Plan-up is only true north while the measured bearing error stays small"
    )

    location = site["location"]
    assert location["to_verify"] is False
    assert 24.8 < location["latitude"] < 25.0
    assert 54.9 < location["longitude"] < 55.1


def test_boundary_vertices_carry_their_source_wgs84_position():
    """The local metric frame must always be reproducible from the source data."""
    for vertex in vertices():
        assert vertex.lonlat is not None, f"Vertex {vertex.id} has no WGS84 position"
        lon, lat = vertex.lonlat
        assert 54.96 < lon < 54.97
        assert 24.89 < lat < 24.90


def test_local_frame_matches_the_wgs84_source():
    """Re-project the stored lon/lat and confirm it reproduces the stored x/y."""
    import math

    verts = vertices()
    lat0 = sum(v.lat for v in verts) / len(verts)
    phi = math.radians(lat0)
    m_lat = 111132.92 - 559.82 * math.cos(2 * phi) + 1.175 * math.cos(4 * phi)
    m_lon = 111412.84 * math.cos(phi) - 93.5 * math.cos(3 * phi)
    origin = verts[0]

    for v in verts:
        x = (v.lon - origin.lon) * m_lon
        y = (v.lat - origin.lat) * m_lat
        assert abs(x - v.x) < 0.01, f"Vertex {v.id} x drifted from its WGS84 source"
        assert abs(y - v.y) < 0.01, f"Vertex {v.id} y drifted from its WGS84 source"


# GFA


def test_a_breach_of_the_cap_is_always_reported():
    """The invariant that matters: the cap is never exceeded SILENTLY, whether
    the breach shows in the estimate or in the measured plan."""
    from analysis.gfa_check import measured_layout, report  # noqa: PLC0415

    t = totals()
    _, fails, _ = report()
    over_estimate = t["scenarios"]["core"]["gross_low"] > t["cap_m2"]
    m = measured_layout()
    over_measured = m is not None and m["total"] > t["cap_m2"]
    assert fails == (over_estimate or over_measured)


def test_the_trim_still_needed_is_small_enough_to_be_a_design_question():
    """Guards against the program drifting further out of reach unnoticed."""
    t = totals()
    over = t["scenarios"]["core"]["gross_low"] - t["cap_m2"]
    assert over < 25.0, (
        f"The program is now {over:.2f} m2 over the cap at the low end of its "
        "ranges. That is past trimming and needs a rethink with the owner."
    )


def test_design_target_holds_a_margin_below_the_cap():
    t = totals()
    assert t["design_target_m2"] < t["cap_m2"]
    assert t["design_margin_m2"] > 0


def test_the_garage_counts_toward_gfa():
    """Owner decision 2026-10-01: count the parking as part of the GFA."""
    garage = next(r for r in rooms() if r.key == "garage")
    assert garage.counts
    assert not garage.unverified
    assert garage.already_gross, "A garage target is a footprint, not a net area"


def test_the_roof_enclosure_is_gone():
    """Owner decision 2026-10-01: no roof terrace and no roof enclosure."""
    keys = {r.key for r in rooms()}
    assert "roof_enclosure" not in keys
    assert "roof_terrace" not in keys


def test_nothing_is_left_unverified_in_the_gfa_tally():
    """Both open GFA questions are now settled by owner decision, so the check
    should have no RISK rows left to report."""
    assert [r.key for r in rooms() if r.unverified] == []


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
    """CLAUDE.md section 4: 2.2 to 2.5 times the other bedrooms, compared like
    with like, the bottom of each range against the bottom, the top against the
    top."""
    by_key = {r.key: r for r in rooms()}
    master = by_key["master_suite"]
    others = [by_key[k] for k in ("bedroom_2", "bedroom_3", "bedroom_4")]
    for end, m, o in (("minimum", master.low_m2, max(b.low_m2 for b in others)),
                      ("maximum", master.high_m2, max(b.high_m2 for b in others))):
        ratio = m / o
        assert 2.2 - 1e-9 <= ratio <= 2.5 + 1e-9, (
            f"At the {end} of the ranges the master is {ratio:.2f} times the "
            "largest bedroom; the brief asks for 2.2 to 2.5"
        )


def test_majlis_has_its_own_guest_powder_room():
    keys = {r.key for r in rooms()}
    assert {"majlis", "guest_powder"} <= keys


def test_guest_bedroom_is_the_only_bedroom_on_the_ground_floor():
    ground_bedrooms = [
        r for r in rooms() if r.floor == "ground" and "bedroom" in r.key
    ]
    assert [r.key for r in ground_bedrooms] == ["guest_bedroom"]


def test_stair_and_lift_land_on_every_level_they_serve():
    """Since the roof stop was removed, the lift serves ground and first only,
    and both still need a landing."""
    keys = {r.key for r in rooms()}
    assert {"stair_lift_ground", "stair_lift_first"} <= keys


# Facade orientation
#
# The plot polygon is normalised counter-clockwise, which reverses the vertex
# order given in site.yaml. Any facade normal derived from the traversal order
# is therefore misassigned. These tests pin the orientations to the words
# printed on the DDA plot plan, which is the one source that cannot drift.

_STATED_AZIMUTH = {
    "northwest": 315.0,
    "southwest": 225.0,
    "east": 90.0,
    "northeast": 45.0,
}


def test_facade_normals_point_away_from_the_plot():
    from shapely.geometry import Point

    from analysis.sun_study import facades  # noqa: PLC0415

    poly = plot_polygon()
    for f in facades():
        rad = __import__("math").radians(f.azimuth)
        nx, ny = __import__("math").sin(rad), __import__("math").cos(rad)
        centre = poly.centroid
        probe = Point(centre.x + nx * 1000, centre.y + ny * 1000)
        assert not poly.contains(probe)


def test_facade_azimuths_match_the_orientations_stated_on_the_dda_plan():
    """Side 1 is the road on the north-west face, and so on for all four."""
    from analysis.sun_study import facades  # noqa: PLC0415

    stated = {s["id"]: s["orientation"] for s in load_site()["sides"]}
    for f in facades():
        want = _STATED_AZIMUTH[stated[f.side_id]]
        diff = abs((f.azimuth - want + 180) % 360 - 180)
        assert diff < 45.0, (
            f"Side {f.side_id} ({f.adjacency}) computes as facing {f.azimuth:.0f} "
            f"degrees ({f.compass}), but the DDA plan calls it "
            f"{stated[f.side_id]}, about {want:.0f} degrees"
        )


def test_the_landscape_plot_side_faces_east():
    """Side 3 fronts landscape plot 5130274. The master suite orientation and
    the pool recommendation both depend on this being the east side."""
    from analysis.sun_study import facades  # noqa: PLC0415

    side3 = next(f for f in facades() if f.side_id == 3)
    assert "5130274" in side3.adjacency
    assert 67.5 <= side3.azimuth <= 157.5, (
        f"Side 3 faces {side3.azimuth:.0f} degrees, which is not easterly"
    )


# Route B trims, owner approved 2026-10-01


def _trimmed(kind=None):
    program = load_program()
    return [r for floor in ("ground", "first") for r in program[floor]
            if r.get("trimmed") and (kind is None or r["trimmed"] == kind)]


def test_every_trim_records_the_brief_figure_it_came_from():
    """Any trimmed room, whatever the reason, must keep the CLAUDE.md target
    beside its new one, so the trim stays visible and reversible rather than
    quietly becoming the brief."""
    trimmed = _trimmed()
    assert trimmed, "No trims recorded in brief/program.yaml"
    for room in trimmed:
        if "target_min_m2" in room:          # a ranged room, trimmed at its floor
            assert "brief_target_min_m2" in room, f"{room['key']} lost its brief figure"
            assert room["target_min_m2"] < room["brief_target_min_m2"]
        else:
            assert "brief_target_m2" in room, f"{room['key']} lost its brief figure"
            assert room["target_m2"] < room["brief_target_m2"]
        assert room.get("trim_note"), f"{room['key']} has no reason recorded"


def test_every_trim_names_which_decision_it_came_from():
    known = {"route_b", "owner_2_cars", "trim_t2"}
    for room in _trimmed():
        assert room["trimmed"] in known, (
            f"{room['key']} is tagged '{room['trimmed']}', which is not a "
            "recorded decision"
        )


def test_route_b_trims_total_thirteen_square_metres():
    saved = sum(r["brief_target_m2"] - r["target_m2"] for r in _trimmed("route_b"))
    assert saved == 13, f"Route B should save 13 m2 net, not {saved}"


def test_the_two_car_garage_saves_seventeen_square_metres():
    saved = sum(r["brief_target_m2"] - r["target_m2"]
                for r in _trimmed("owner_2_cars"))
    assert saved == 17, f"Dropping to two cars should save 17 m2, not {saved}"


def test_route_b_touched_no_principal_room():
    """Route B was chosen precisely because it touches no principal room. The
    garage is excluded from this check: the owner reduced it separately and
    deliberately on 2026-10-02."""
    principal = {"living", "majlis", "dining", "show_kitchen", "guest_bedroom",
                 "sunroom", "home_office", "master_suite", "bedroom_2",
                 "bedroom_3", "bedroom_4", "family_living"}
    trimmed = {r["key"] for r in _trimmed("route_b")}
    assert not (trimmed & principal), (
        f"Route B trimmed a principal room: {sorted(trimmed & principal)}"
    )


def test_the_program_fits_the_cap_at_the_minimum_of_every_range():
    """The hard limit. 662.99 m2 is the DDA cap and is not negotiable."""
    t = totals()
    core = t["scenarios"]["core"]
    assert core["gross_low"] <= t["cap_m2"], (
        f"Low end reaches {core['gross_low']:.2f} m2 against a "
        f"{t['cap_m2']:.2f} m2 cap"
    )


def test_a_real_margin_is_still_held_back_below_the_cap():
    """The design target is a self-imposed safety margin, not a regulation, so
    sitting above it is a judgement call rather than a breach. What must not
    happen is the margin vanishing: GFA is remeasured by the consultant to the
    outside face of external walls, and a plan with no margin is a plan that
    gets redesigned at submission."""
    t = totals()
    held = t["cap_m2"] - t["scenarios"]["core"]["gross_low"]
    assert held >= 5.0, (
        f"Only {held:.2f} m2 of margin is left below the cap. D-005 recommends "
        f"{t['cap_m2'] - t['design_target_m2']:.2f} m2."
    )


def test_the_net_to_gross_factor_is_measured_not_assumed():
    """A-01 promised this would be replaced by measurement at Phase 2."""
    site = load_site()
    targets = site["targets"]
    assert "net_to_gross_measured_on" in targets, (
        "The net to gross factor is still an assumption"
    )
    assert targets["net_to_gross_factor"] > targets["net_to_gross_previous"], (
        "Measurement came in below the assumption, which would be a surprise "
        "worth investigating rather than accepting"
    )


def test_the_garage_is_sized_for_two_cars():
    """Owner decision 2026-10-02."""
    garage = next(r for r in rooms() if r.key == "garage")
    assert garage.low_m2 == 38
    program = load_program()
    spec = next(r for r in program["ground"] if r["key"] == "garage")
    assert spec["cars"] == 2
    assert spec["brief_target_m2"] == 55
