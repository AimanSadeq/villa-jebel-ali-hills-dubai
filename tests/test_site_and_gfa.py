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
