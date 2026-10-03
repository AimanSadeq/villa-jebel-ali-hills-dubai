"""Sketch VJH-SK-019: the garden plan from brief/garden.yaml (answers G1 to G4).

Drawn from the same landscape build the IFC uses (src/model/landscape.py),
so the sketch and the model cannot differ: terraces, lawns, beds, paths, the
boundary wall and gates, hedges, trees and palms, the BBQ area. Plot
orientation as the floor plans: road on the left, landscape plot on the
right, the carport end at the bottom.

Run: python src/drawings/sketch_garden.py   (after src/model/build_model.py)

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Polygon as MplPolygon, Rectangle  # noqa: E402
from shapely.geometry import Polygon  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model import landscape  # noqa: E402
from model.architecture import Model  # noqa: E402
from model.site import SQM_TO_SQFT  # noqa: E402

OUT_PDF = REPO_ROOT / "output" / "pdf" / "VJH-SK-019_Garden_Plan.pdf"
OUT_PNG = REPO_ROOT / "output" / "pdf" / "VJH-SK-019_Garden_Plan.png"
INK, MUTED, RED, WALL = "#1a1a1a", "#6b6b6b", "#b3261e", "#2b2b2b"
FILL = {"paving": "#d9d3c7", "step": "#cfc8ba", "path": "#e3dfd6", "lawn": "#b9d39a",
        "bed": "#c9b79b", "ground": "#e8e4dc", "steps": "#cfc8ba"}


def draw_poly(ax, g, **kw):
    for p in ([g] if g.geom_type == "Polygon" else list(getattr(g, "geoms", []))):
        if p.is_empty:
            continue
        ax.add_patch(MplPolygon(list(p.exterior.coords), closed=True, **kw))
        for r in p.interiors:
            ax.add_patch(MplPolygon(list(r.coords), closed=True, fc="white", ec="none", zorder=kw.get("zorder", 1)))


def main() -> int:
    m = Model()
    m.setup()
    m.footprints()
    obstacles = []
    spec = landscape.load()
    from model.massing import site_to_grid  # noqa: PLC0415
    from model.site import plot_polygon  # noqa: PLC0415
    plot = site_to_grid(plot_polygon())
    g = landscape.build(spec, plot, m.g_fp, m.carport, obstacles)

    fig = plt.figure(figsize=(16.5, 11.7))
    ax = fig.add_axes([0.02, 0.06, 0.62, 0.88])
    draw_poly(ax, plot, fc="#f4f1ea", ec=RED, lw=1.2, zorder=1)
    for s, poly in g.surfaces:
        draw_poly(ax, poly, fc=FILL.get(s["kind"], "#eee"), ec="#8c857a", lw=0.4, zorder=2)
    # House, carport and porch, as on the floor plans.
    draw_poly(ax, m.g_fp, fc="#ffffff", ec=WALL, lw=1.8, zorder=4)
    if m.carport is not None:
        draw_poly(ax, m.carport, fc="#f7f5f0", ec=WALL, lw=0.8, zorder=3)
        b = m.carport.bounds
        ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, "CARPORT\n3 cars", ha="center", va="center",
                fontsize=7, color=MUTED, zorder=5)
    gf = m.g_fp.bounds
    ax.text((gf[0] + gf[2]) / 2, (gf[1] + gf[3]) / 2, "VILLA\nground floor as built (D-051)",
            ha="center", va="center", fontsize=8, color=MUTED, zorder=5)
    # Wall, screen and gates.
    for it in g.items:
        if it.object_type == "Landscape: boundary wall":
            for p, _, _ in it.prisms:
                draw_poly(ax, p, fc=WALL, ec="none", zorder=6)
        if it.object_type == "Landscape: gate":
            for p, _, _ in it.prisms:
                b = p.bounds
                ax.plot([b[0] - 0.3, b[0] - 0.3], [b[1], b[3]], color=RED, lw=2.2, zorder=7)
                ax.text(b[0] - 0.6, (b[1] + b[3]) / 2, it.name.split(",")[0], rotation=90, ha="center",
                        va="center", fontsize=6, color=RED, zorder=7)
        if it.object_type == "Landscape: hedge":
            for p, _, _ in it.prisms:
                draw_poly(ax, p, fc="#6f9a55", ec="none", zorder=5)
        if it.object_type in ("Landscape: pergola",):
            b = Polygon().bounds
            for p, z0, h in it.prisms:
                draw_poly(ax, p, fc="#9a643a", ec="none", zorder=5, alpha=0.5)
        if it.object_type == "Landscape: furniture":
            for p, z0, h in it.prisms[:1]:
                draw_poly(ax, p, fc="none", ec="#7a5a3a", lw=0.6, zorder=6)
    for tr, sp in g.trees:
        r = sp["crown_m"] / 2
        palm = sp["kind"] == "palm"
        ax.add_patch(Circle((tr["u"], tr["v"]), r, fc="#8fbf6f" if not palm else "#a9c97a",
                            ec="#4d7a3a", lw=0.7, alpha=0.75, zorder=5))
        if palm:
            for k in range(8):
                import math
                a = k * math.pi / 4
                ax.plot([tr["u"], tr["u"] + r * math.cos(a)], [tr["v"], tr["v"] + r * math.sin(a)],
                        color="#4d7a3a", lw=0.5, zorder=5)
        ax.plot(tr["u"], tr["v"], "o", color="#4d3a2a", ms=2.5, zorder=6)
    # Garden doors.
    for d in m.lay.get("doors") or []:
        if d["b"] == "outside" and d["storey"] == "ground":
            ax.plot(d["u"], d["v"], "s", color=RED, ms=4, zorder=7)
            ax.text(d["u"] + 0.35, d["v"], d["no"], fontsize=6, color=RED, va="center", zorder=7)
    # Labels with sizes (rule 9 for the outdoor rooms: w x l, m2 and sq ft).
    for s, poly in g.surfaces:
        if s["kind"] in ("bed", "ground", "step", "steps") or poly.area < 4:
            continue
        b = poly.bounds
        w, l = sorted((b[2] - b[0], b[3] - b[1]))
        a = poly.area
        c = poly.representative_point()
        ax.text(c.x, c.y, f"{s['name']}\n{w:.2f} x {l:.2f} m, {a:.1f} m2 ({a * SQM_TO_SQFT:,.0f} sq ft)",
                ha="center", va="center", fontsize=5.6, color=INK, zorder=8,
                bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.25))
    ax.text(-0.9, (plot.bounds[1] + plot.bounds[3]) / 2, "SIDE 1  ROAD 18.30 m", rotation=90,
            ha="center", va="center", fontsize=7, color=MUTED)
    ax.text(plot.bounds[2] + 0.9, (plot.bounds[1] + plot.bounds[3]) / 2, "SIDE 3  LANDSCAPE PLOT 5130274",
            rotation=270, ha="center", va="center", fontsize=7, color=MUTED)
    ax.text((plot.bounds[0] + plot.bounds[2]) / 2, plot.bounds[1] - 0.9, "SIDE 2  NEIGHBOUR 5130123",
            ha="center", va="center", fontsize=7, color=MUTED)
    ax.text((plot.bounds[0] + plot.bounds[2]) / 2, plot.bounds[3] + 0.9, "SIDE 4  NEIGHBOUR 5130271",
            ha="center", va="center", fontsize=7, color=MUTED)
    ax.set_xlim(-2.5, plot.bounds[2] + 2.5)
    ax.set_ylim(-2.0, plot.bounds[3] + 2.0)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("GARDEN PLAN, answers G1 to G4   plot up is NNE, not north", loc="left", fontsize=11,
                 color=INK, fontweight="bold")

    x = 0.67
    fig.text(x, 0.93, "THE GARDEN", fontsize=13, color=INK, fontweight="bold")
    y = 0.905
    rows = [
        ("Back garden (G2, balanced)", "A 3.00 m paved terrace along the house links the three garden "
         "doors (G20 living, G21 Arabic kitchen, G22 dining); one step down to the lawn in front of the "
         "living room and dining; a planting bed with date palms, a ghaf and a sidr along the landscape plot."),
        ("BBQ area (G1)", "South corner by the Arabic kitchen door: a paved BBQ terrace with an open "
         "timber pergola 4.00 x 3.60 m, clear height 2.45 m under the beams, a 3.00 m BBQ counter and a "
         "table for six. Inside the 3 m setback line."),
        ("Front (G4)", "A sliding car gate into the carport; a pedestrian gate on the line of the stone "
         "portal, a 1.50 m path and three steps up to the entrance court inside the portal, at the porch "
         "level; lawn and date palms either side, a low hedge along the road wall."),
        ("Boundary wall (G3, D-011)", "2.40 m overall: solid to 1.20 m with a timber screen above on the "
         "road and landscape sides, solid full height against both neighbours. Whether a wall is allowed "
         "(DDA FAQ Q3) and its heights are TO VERIFY with Meraas (OI-14)."),
        ("Sides and service", "A paved service yard from the carport to the laundry and plant room doors "
         "and on to the BBQ terrace; a side path along the north wall with a hedge and frangipani; "
         "planting strips in the 3 m setbacks."),
        ("Levels", "Garden ground 0.45 m below the house floor (gate level, sheet A-09-001); terraces "
         "0.15 m below the floor, one 0.15 m step down to the lawn; carport floor 0.30 m below."),
        ("Plants", "Indicative species common in UAE residential gardens, native where possible (ghaf, "
         "sidr), for the landscape architect to confirm with the irrigation design (Phase 5)."),
    ]
    for head, body in rows:
        fig.text(x, y, head, fontsize=8.5, color=INK, fontweight="bold", va="top")
        y -= 0.016
        for line in textwrap.wrap(body, 78):
            fig.text(x, y, line, fontsize=7.5, color=INK, va="top")
            y -= 0.0135
        y -= 0.008
    y -= 0.004
    fig.text(x, y, "TREES AND PALMS", fontsize=8.5, color=INK, fontweight="bold", va="top")
    y -= 0.016
    counts: dict[str, int] = {}
    for _, sp in g.trees:
        counts[sp["name"]] = counts.get(sp["name"], 0) + 1
    for name, n in counts.items():
        fig.text(x, y, f"{n} x {name}", fontsize=7.5, color=INK, va="top")
        y -= 0.0135
    if g.report:
        y -= 0.008
        for r in g.report:
            fig.text(x, y, "- " + r, fontsize=7.5, color=RED, va="top")
            y -= 0.0135
    fig.text(0.975, 0.030, "CONCEPT DESIGN, NOT FOR CONSTRUCTION", fontsize=11, color=RED,
             ha="right", fontweight="bold")
    fig.text(0.975, 0.016, "Sketch VJH-SK-019   Garden plan, answers G1 to G4   Rev A   A3 landscape   "
             "drawn from brief/garden.yaml by src/drawings/sketch_garden.py", fontsize=7.5, color=MUTED, ha="right")
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, facecolor="white", dpi=200)
    fig.savefig(OUT_PNG, facecolor="white", dpi=110)
    plt.close(fig)
    print(f"PDF  {OUT_PDF.relative_to(REPO_ROOT)}")
    for r in g.report:
        print("NOTE", r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
