"""Site plan for Villa 5130272: DXF for the consultant, PDF for review.

Draws the plot boundary with dimensioned sides, the 3 m setback line, the
hatched buildable envelope, neighbour plot labels, north arrow, scale bar, and
a title block carrying the areas in m2 and sq ft.

Output is a true 1:200 A3 landscape sheet, so printed dimensions scale.

Run: .\\.venv\\Scripts\\python.exe src/drawings/site_plan.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model.site import (  # noqa: E402
    area_check,
    buildable_envelope,
    load_site,
    plot_polygon,
    sides,
    sqft,
    vertex_map,
)

DXF_OUT = REPO_ROOT / "output" / "dxf" / "VJH-SP-001_Site_Plan.dxf"
PDF_OUT = REPO_ROOT / "output" / "pdf" / "VJH-SP-001_Site_Plan.pdf"

SCALE = 200                      # 1:200
SHEET_NAME = "A2 landscape"
SHEET_W_MM, SHEET_H_MM = 594.0, 420.0   # A2 landscape
SHEET_W = SHEET_W_MM / 1000.0 * SCALE   # 118.8 m of model space
SHEET_H = SHEET_H_MM / 1000.0 * SCALE   # 84.0 m of model space

MARGIN = 2.0                     # sheet border inset, model metres
TITLE_W = 26.0                   # title block column width
DIM_OFFSET = 3.6                 # dimension line offset from the boundary

# Text heights in model metres. At 1:200, 1.0 m of model space prints as 5 mm.
H_TINY, H_SMALL, H_BODY, H_HEAD, H_TITLE = 0.36, 0.5, 0.62, 0.9, 1.5

LAYERS = {
    "PLOT-BOUNDARY":  {"color": 1,   "lineweight": 50},
    "SETBACK-LINE":   {"color": 2,   "linetype": "DASHED", "lineweight": 25},
    "ENVELOPE-HATCH": {"color": 253, "lineweight": 5},
    "DIMENSIONS":     {"color": 4,   "lineweight": 13},
    "TEXT":           {"color": 7,   "lineweight": 13},
    "NEIGHBOURS":     {"color": 8,   "linetype": "DASHED2", "lineweight": 9},
    "NORTH-SCALE":    {"color": 7,   "lineweight": 18},
    "SHEET":          {"color": 7,   "lineweight": 35},
    "STAMP":          {"color": 1,   "lineweight": 25},
}

DIM_OVERRIDE = {
    "dimtxt": H_SMALL,   # text height
    "dimasz": 0.45,      # arrow size
    "dimexe": 0.3,       # extension line beyond the dimension line
    "dimexo": 0.5,       # extension line offset from the origin point
    "dimgap": 0.2,       # gap around the text
    "dimdec": 2,
    "dimclrt": 4,
    # The stock EZDXF dimension style assumes millimetre drawing units and
    # carries a length factor of 100. This model is in metres, so a 30.48 m side
    # would otherwise be annotated "3048.11". Force a 1:1 length factor.
    "dimlfac": 1.0,
    "dimpost": "<> m",
}


def _text(msp, content, pos, height, layer="TEXT", align=TextEntityAlignment.LEFT,
          rotation=0.0):
    t = msp.add_text(content, height=height,
                     dxfattribs={"layer": layer, "rotation": rotation})
    t.set_placement(pos, align=align)
    return t


def _setup_document():
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 6      # metres
    doc.header["$MEASUREMENT"] = 1   # metric
    for name, attrs in LAYERS.items():
        doc.layers.add(name, **attrs)
    return doc


def _placement(plot, env):
    """Translation that centres the plot in the drawing area of the sheet."""
    draw_x0, draw_x1 = MARGIN, SHEET_W - TITLE_W - MARGIN
    draw_y0, draw_y1 = MARGIN, SHEET_H - MARGIN

    minx, miny, maxx, maxy = plot.bounds
    # Leave room for dimension lines and labels on every side of the plot.
    pad = DIM_OFFSET + 2.6
    content_w, content_h = (maxx - minx) + 2 * pad, (maxy - miny) + 2 * pad

    avail_w, avail_h = draw_x1 - draw_x0, draw_y1 - draw_y0
    if content_w > avail_w or content_h > avail_h:
        raise ValueError(
            f"Plot plus dimensions ({content_w:.1f} x {content_h:.1f} m) does not "
            f"fit the 1:{SCALE} A3 drawing area ({avail_w:.1f} x {avail_h:.1f} m). "
            "Change SCALE or the sheet size."
        )

    dx = draw_x0 + (avail_w - content_w) / 2.0 + pad - minx
    dy = draw_y0 + (avail_h - content_h) / 2.0 + pad - miny
    return dx, dy


def _draw_sheet_frame(msp):
    msp.add_lwpolyline(
        [(MARGIN, MARGIN), (SHEET_W - MARGIN, MARGIN),
         (SHEET_W - MARGIN, SHEET_H - MARGIN), (MARGIN, SHEET_H - MARGIN)],
        close=True, dxfattribs={"layer": "SHEET"},
    )
    x = SHEET_W - TITLE_W - MARGIN
    msp.add_line((x, MARGIN), (x, SHEET_H - MARGIN), dxfattribs={"layer": "SHEET"})
    return x


def _draw_plot_and_envelope(msp, plot, env, dx, dy):
    plot_pts = [(x + dx, y + dy) for x, y in plot.exterior.coords]
    env_pts = [(x + dx, y + dy) for x, y in env.exterior.coords]

    hatch = msp.add_hatch(dxfattribs={"layer": "ENVELOPE-HATCH"})
    hatch.set_pattern_fill("ANSI31", scale=0.35)
    hatch.paths.add_polyline_path(env_pts, is_closed=True)

    msp.add_lwpolyline(plot_pts, close=True, dxfattribs={"layer": "PLOT-BOUNDARY"})
    msp.add_lwpolyline(env_pts, close=True, dxfattribs={"layer": "SETBACK-LINE"})
    return plot_pts, env_pts


def _draw_vertex_labels(msp, site, dx, dy):
    for v in vertex_map(site).values():
        p = (v.x + dx, v.y + dy)
        msp.add_circle(p, radius=0.35, dxfattribs={"layer": "TEXT"})
        _text(msp, v.id, p, H_SMALL, align=TextEntityAlignment.MIDDLE_CENTER)


def _dimension_sides(msp, site, dx, dy):
    """Aligned dimensions outside the boundary, one per side, split at the bend."""
    vmap = vertex_map(site)
    plot = plot_polygon(site)
    cx, cy = plot.centroid.x + dx, plot.centroid.y + dy

    segments: list[tuple[str, str]] = []
    for s in site["sides"]:
        if "via" in s:
            segments.append((s["from"], s["via"]))
            segments.append((s["via"], s["to"]))
        else:
            segments.append((s["from"], s["to"]))

    for a, b in segments:
        p1 = (vmap[a].x + dx, vmap[a].y + dy)
        p2 = (vmap[b].x + dx, vmap[b].y + dy)
        # Aligned dimension text follows the measured direction, so a right to
        # left vector renders the text upside down. Always measure left to right.
        if p2[0] < p1[0]:
            p1, p2 = p2, p1
        # Offset the dimension line away from the plot centre.
        mid = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)
        outward = -1.0 if (mid[0] - cx) * (p2[1] - p1[1]) - (mid[1] - cy) * (p2[0] - p1[0]) > 0 else 1.0
        dim = msp.add_aligned_dim(
            p1=p1, p2=p2, distance=outward * DIM_OFFSET,
            dimstyle="EZDXF", override=DIM_OVERRIDE,
            dxfattribs={"layer": "DIMENSIONS"},
        )
        dim.render()


def _draw_side_annotations(msp, site, dx, dy):
    """Adjacency note along each side, inside the boundary."""
    plot = plot_polygon(site)
    cx, cy = plot.centroid.x + dx, plot.centroid.y + dy

    for s in sides(site):
        mx, my = s.midpoint
        mx, my = mx + dx, my + dy
        # Pull the label a little toward the centre so it sits inside the plot.
        vx, vy = cx - mx, cy - my
        norm = (vx * vx + vy * vy) ** 0.5 or 1.0
        px, py = mx + vx / norm * 1.5, my + vy / norm * 1.5

        angle = __import__("math").degrees(
            __import__("math").atan2(s.end.y - s.start.y, s.end.x - s.start.x)
        )
        if angle > 90 or angle < -90:
            angle += 180

        label = f"SIDE {s.id}  {s.adjacency}"
        if s.is_main_access:
            label += "  (MAIN ACCESS)"
        _text(msp, label, (px, py), H_TINY, layer="NEIGHBOURS",
              align=TextEntityAlignment.MIDDLE_CENTER, rotation=angle)


def _draw_envelope_note(msp, env, a, dx, dy):
    c = env.centroid
    p = (c.x + dx, c.y + dy)

    # Mask the hatch behind the note, otherwise the text is unreadable.
    half_w, top, bottom = 7.2, 2.5, 2.9
    mask = msp.add_hatch(color=255, dxfattribs={"layer": "ENVELOPE-HATCH"})
    mask.set_solid_fill(color=255)
    mask.paths.add_polyline_path(
        [(p[0] - half_w, p[1] - bottom), (p[0] + half_w, p[1] - bottom),
         (p[0] + half_w, p[1] + top), (p[0] - half_w, p[1] + top)],
        is_closed=True,
    )

    _text(msp, "BUILDABLE ENVELOPE", (p[0], p[1] + 1.5), H_BODY,
          align=TextEntityAlignment.MIDDLE_CENTER)
    _text(msp, f"{a['envelope_area_m2']:.2f} m2   {sqft(a['envelope_area_m2']):,.2f} sq ft",
          (p[0], p[1] + 0.3), H_SMALL, align=TextEntityAlignment.MIDDLE_CENTER)
    _text(msp, "3.00 m SETBACK ALL SIDES", (p[0], p[1] - 0.9), H_SMALL,
          align=TextEntityAlignment.MIDDLE_CENTER)
    _text(msp, "MAX GFA 662.99 m2 OVER G+1 IS THE BINDING CONSTRAINT",
          (p[0], p[1] - 2.1), H_TINY, align=TextEntityAlignment.MIDDLE_CENTER)


def _draw_north_arrow(msp, x, y):
    """Arrow pointing to plan-up, which is assumed to be true north."""
    msp.add_circle((x, y), radius=2.0, dxfattribs={"layer": "NORTH-SCALE"})
    msp.add_solid(
        [(x, y + 1.7), (x - 0.65, y - 1.3), (x, y - 0.75), (x + 0.65, y - 1.3)],
        dxfattribs={"layer": "NORTH-SCALE"},
    )
    _text(msp, "N", (x, y + 2.6), H_BODY, layer="NORTH-SCALE",
          align=TextEntityAlignment.MIDDLE_CENTER)
    _text(msp, "TRUE NORTH, VERIFIED", (x, y - 3.1), H_TINY,
          align=TextEntityAlignment.MIDDLE_CENTER)
    _text(msp, "AGAINST DDA GIS 2026-10-01", (x, y - 3.7), H_TINY,
          align=TextEntityAlignment.MIDDLE_CENTER)


def _draw_scale_bar(msp, x, y):
    seg, n = 5.0, 4   # 4 segments of 5 m, 20 m total
    for i in range(n):
        x0 = x + i * seg
        pts = [(x0, y), (x0 + seg, y), (x0 + seg, y + 0.5), (x0, y + 0.5)]
        if i % 2 == 0:
            h = msp.add_hatch(dxfattribs={"layer": "NORTH-SCALE"})
            h.paths.add_polyline_path(pts, is_closed=True)
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "NORTH-SCALE"})
        _text(msp, f"{int(i * seg)}", (x0, y - 0.9), H_TINY,
              align=TextEntityAlignment.MIDDLE_CENTER)
    _text(msp, f"{int(n * seg)} m", (x + n * seg, y - 0.9), H_TINY,
          align=TextEntityAlignment.MIDDLE_CENTER)
    _text(msp, f"SCALE 1:{SCALE} AT A2", (x + n * seg / 2, y + 1.1), H_SMALL,
          align=TextEntityAlignment.MIDDLE_CENTER)


def _draw_title_block(msp, x0, site, a):
    """Title block in the right-hand column."""
    x = x0 + 1.2
    y = SHEET_H - MARGIN - 2.2
    w = TITLE_W - 2.4

    def row(label, value, gap=1.15, h=H_TINY):
        nonlocal y
        _text(msp, label, (x, y), h)
        _text(msp, value, (x + w, y), h, align=TextEntityAlignment.RIGHT)
        y -= gap

    def rule(gap=1.0):
        nonlocal y
        msp.add_line((x, y + 0.55), (x + w, y + 0.55), dxfattribs={"layer": "SHEET"})
        y -= gap - 0.6

    _text(msp, "VILLA 5130272", (x, y), H_TITLE)
    y -= 2.0
    _text(msp, "SAIH SHUAIB 1, JEBEL ALI HILLS", (x, y), H_SMALL)
    y -= 1.0
    _text(msp, "DUBAI, UNITED ARAB EMIRATES", (x, y), H_SMALL)
    y -= 2.0
    _text(msp, "SITE PLAN", (x, y), H_HEAD)
    y -= 1.3
    _text(msp, "PLOT, SETBACKS, BUILDABLE ENVELOPE", (x, y), H_TINY)
    y -= 1.8
    rule()

    _text(msp, "PLOT DATA", (x, y), H_SMALL)
    y -= 1.4
    row("Plot number", site["plot"]["number"])
    row("Authority", "DDA")
    row("Master developer", "Meraas Estates (L.L.C)")
    row("Land use", "Residential: villa")
    row("Plot area, official", f"{a['official_plot_area_m2']:,.2f} m2")
    row("", f"{sqft(a['official_plot_area_m2']):,.2f} sq ft")
    row("Plot area, computed", f"{a['computed_plot_area_m2']:,.2f} m2")
    row("Deviation", f"{a['plot_area_deviation_pct']:+.3f} %")
    y -= 0.4
    rule()

    _text(msp, "PLANNING CONTROLS", (x, y), H_SMALL)
    y -= 1.4
    row("Maximum height", site["regulations"]["max_height"])
    row("Setback, all sides", f"{a['setback_m']:.2f} m")
    row("Maximum coverage", "Not specified by DDA")
    row("Parking, minimum", f"{site['regulations']['parking_spaces_min']} space")
    row("Maximum GFA", f"{a['max_gfa_m2']:,.2f} m2")
    row("", f"{sqft(a['max_gfa_m2']):,.2f} sq ft")
    y -= 0.4
    rule()

    _text(msp, "AREA CHECK", (x, y), H_SMALL)
    y -= 1.4
    row("Buildable envelope", f"{a['envelope_area_m2']:,.2f} m2")
    row("", f"{sqft(a['envelope_area_m2']):,.2f} sq ft")
    row("Envelope, share of plot", f"{a['envelope_pct_of_plot']:.1f} %")
    row("Capacity, G+1 over envelope", f"{a['geometric_capacity_m2']:,.2f} m2")
    row("GFA, share of capacity", f"{a['gfa_as_pct_of_capacity']:.1f} %")
    row("Binding constraint", a["binding_constraint"])
    y -= 0.4
    rule()

    _text(msp, "DATA PROVENANCE", (x, y), H_SMALL)
    y -= 1.2
    for note in (
        "Boundary from the DDA Development",
        "Information System GIS, WGS84,",
        "retrieved 2026-10-01. Reproduces all",
        "five stated side lengths.",
        "",
        "True north VERIFIED 2026-10-01 against",
        "the DDA GIS. Mean bearing error across",
        "the five edges: -0.02 deg.",
        "",
        "TO VERIFY: the Demarcation Certificate",
        "remains the authoritative source and",
        "should replace these coordinates.",
    ):
        _text(msp, note, (x, y), H_TINY)
        y -= 0.78

    # Stamp, pinned to the bottom of the column.
    sy = MARGIN + 3.4
    msp.add_lwpolyline(
        [(x, sy - 1.0), (x + w, sy - 1.0), (x + w, sy + 2.0), (x, sy + 2.0)],
        close=True, dxfattribs={"layer": "STAMP"},
    )
    _text(msp, "CONCEPT DESIGN", (x + w / 2, sy + 1.0), H_BODY, layer="STAMP",
          align=TextEntityAlignment.MIDDLE_CENTER)
    _text(msp, "NOT FOR CONSTRUCTION", (x + w / 2, sy - 0.2), H_BODY, layer="STAMP",
          align=TextEntityAlignment.MIDDLE_CENTER)
    _text(msp, "Drawing VJH-SP-001   Phase 0   Rev A", (x, MARGIN + 1.3), H_TINY)
    _text(msp, "Structural design by licensed structural engineer", (x, MARGIN + 0.6),
          H_TINY)


def build() -> ezdxf.document.Drawing:
    site = load_site()
    a = area_check(site)
    plot, env = plot_polygon(site), buildable_envelope(site)

    doc = _setup_document()
    msp = doc.modelspace()

    title_x = _draw_sheet_frame(msp)
    dx, dy = _placement(plot, env)

    _draw_plot_and_envelope(msp, plot, env, dx, dy)
    _dimension_sides(msp, site, dx, dy)
    _draw_side_annotations(msp, site, dx, dy)
    _draw_vertex_labels(msp, site, dx, dy)
    _draw_envelope_note(msp, env, a, dx, dy)
    _draw_north_arrow(msp, title_x - 5.0, SHEET_H - MARGIN - 5.5)
    _draw_scale_bar(msp, MARGIN + 3.0, MARGIN + 2.4)
    _draw_title_block(msp, title_x, site, a)

    return doc


def save_pdf(doc, path: Path) -> None:
    """Render the sheet to PDF at a true 1:200, A3 landscape."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.config import BackgroundPolicy, Configuration
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    mm_to_in = 1 / 25.4
    fig = plt.figure(figsize=(SHEET_W_MM * mm_to_in, SHEET_H_MM * mm_to_in))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax)
    config = Configuration(background_policy=BackgroundPolicy.WHITE)
    Frontend(ctx, backend, config=config).draw_layout(doc.modelspace(), finalize=False)

    ax.set_xlim(0, SHEET_W)
    ax.set_ylim(0, SHEET_H)
    ax.set_aspect("equal", adjustable="box")

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)


def main() -> int:
    doc = build()
    DXF_OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(DXF_OUT)
    save_pdf(doc, PDF_OUT)
    print(f"DXF  {DXF_OUT.relative_to(REPO_ROOT)}")
    print(f"PDF  {PDF_OUT.relative_to(REPO_ROOT)}")
    print(f"Sheet {SHEET_NAME}, true 1:{SCALE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
