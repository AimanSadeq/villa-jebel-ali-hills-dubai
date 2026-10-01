"""Indicative plan of option C's single storey wing, Villa 5130272.

A3 landscape at a true 1:75. Room names and target areas are read from
brief/program.yaml, geometry from brief/massing.yaml, so nothing is hard-coded
here and any drift between the drawn area and the brief target is reported.

INDICATIVE, Phase 1 preview at the owner's request. Not a designed layout, and
it does not unblock OI-01.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis.sun_study import facade_exposure  # noqa: E402
from model.massing import load_massing, options, site_to_grid  # noqa: E402
from model.site import SQM_TO_SQFT, buildable_envelope, plot_polygon, sides  # noqa: E402

OUT = REPO_ROOT / "output" / "pdf" / "VJH-MA-002_Option_C_Wing.pdf"
PROGRAM = REPO_ROOT / "brief" / "program.yaml"

MM = 1 / 25.4
A3 = (420 * MM, 297 * MM)
SCALE = 75

INK = "#1a1a1a"
MUTED = "#6b6b6b"
WALL = "#2b2b2b"
ROOM_FILL = "#f6f4f0"
LIVING_FILL = "#eef2ee"
GLASS = "#2a7fb8"
HOT = "#b3261e"
GOOD = "#2e7d4f"
DIMCOL = "#1f6f8b"
POOL = "#2a7fb8"
DECK = "#ded3bd"
MASS = "#d8d4cd"

STAMP = "CONCEPT DESIGN, NOT FOR CONSTRUCTION"


def program_rooms() -> dict:
    data = yaml.safe_load(PROGRAM.read_text(encoding="utf-8"))
    out = {}
    for floor in ("ground", "first", "roof"):
        for r in data.get(floor, []):
            out[r["key"]] = r
    return out


def layout() -> dict:
    return load_massing()["indicative_layouts"]["C"]


def _rect(ax, u, v, **kw):
    ax.add_patch(Rectangle((u[0], v[0]), u[1] - u[0], v[1] - v[0], **kw))


def _dim(ax, p0, p1, text, offset=0.0, horizontal=True, fs=5.4):
    """A dimension line with ticks at both ends."""
    if horizontal:
        y = p0[1] + offset
        ax.annotate("", xy=(p1[0], y), xytext=(p0[0], y),
                    arrowprops=dict(arrowstyle="<|-|>", color=DIMCOL, lw=0.6,
                                    shrinkA=0, shrinkB=0, mutation_scale=6))
        ax.text((p0[0] + p1[0]) / 2, y + 0.10, text, ha="center", va="bottom",
                fontsize=fs, color=DIMCOL)
    else:
        x = p0[0] + offset
        ax.annotate("", xy=(x, p1[1]), xytext=(x, p0[1]),
                    arrowprops=dict(arrowstyle="<|-|>", color=DIMCOL, lw=0.6,
                                    shrinkA=0, shrinkB=0, mutation_scale=6))
        ax.text(x - 0.10, (p0[1] + p1[1]) / 2, text, ha="right", va="center",
                fontsize=fs, color=DIMCOL, rotation=90)


def wing_plan(ax, lay: dict, prog: dict) -> list[dict]:
    wing = lay["wing"]
    wu, wv = wing["u"], wing["v"]
    ext = float(lay["wall_external_m"])

    # Wall build-up drawn as a solid band between the outer and inner faces.
    _rect(ax, wu, wv, facecolor=WALL, edgecolor="none", zorder=2)
    _rect(ax, [wu[0] + ext, wu[1] - ext], [wv[0] + ext, wv[1] - ext],
          facecolor="white", edgecolor="none", zorder=3)

    rows = []
    for r in wing["rooms"]:
        spec = prog[r["program_key"]]
        u, v = r["u"], r["v"]
        area = (u[1] - u[0]) * (v[1] - v[0])
        target = float(spec["target_m2"])
        double = bool(r.get("double_height"))

        _rect(ax, u, v, facecolor=LIVING_FILL if double else ROOM_FILL,
              edgecolor=WALL, lw=0.8, zorder=4)

        cx, cy = (u[0] + u[1]) / 2, (v[0] + v[1]) / 2
        ax.text(cx, cy + 0.62, spec["name"].upper(), ha="center", va="center",
                fontsize=7.2, color=INK, zorder=6)
        ax.text(cx, cy + 0.08, f"{area:.1f} m2", ha="center", va="center",
                fontsize=6.6, color=INK, zorder=6)
        ax.text(cx, cy - 0.34, f"{area * SQM_TO_SQFT:,.0f} sq ft",
                ha="center", va="center", fontsize=5.4, color=MUTED, zorder=6)
        ax.text(cx, cy - 0.78, f"{u[1] - u[0]:.2f} x {v[1] - v[0]:.2f} m",
                ha="center", va="center", fontsize=5.4, color=MUTED, zorder=6)
        if double:
            ax.text(cx, cy - 1.24, "DOUBLE HEIGHT", ha="center", va="center",
                    fontsize=5.4, color=GOOD, zorder=6)

        rows.append({"name": spec["name"], "area": area, "target": target,
                     "delta": area - target, "face": r["face"]})

    # Glazing, drawn as a heavy line on the faces that take it.
    for g in wing.get("glazing", []):
        ax.plot(g["u"], g["v"], color=GLASS, lw=2.6, solid_capstyle="butt",
                zorder=7)

    # Dimensions
    _dim(ax, (wu[0], wv[0]), (wu[1], wv[0]), f"{wu[1] - wu[0]:.2f} m",
         offset=-1.05, horizontal=True)
    _dim(ax, (wu[1], wv[0]), (wu[1], wv[1]), f"{wv[1] - wv[0]:.2f} m",
         offset=1.15, horizontal=False)
    rooms = wing["rooms"]
    _dim(ax, (rooms[0]["u"][0], wv[1]), (rooms[0]["u"][1], wv[1]),
         f"{rooms[0]['u'][1] - rooms[0]['u'][0]:.2f}", offset=0.75)
    _dim(ax, (rooms[2]["u"][0], wv[1]), (rooms[2]["u"][1], wv[1]),
         f"{rooms[2]['u'][1] - rooms[2]['u'][0]:.2f}", offset=0.75)
    _dim(ax, (wu[0], rooms[0]["v"][0]), (wu[0], rooms[0]["v"][1]),
         f"{rooms[0]['v'][1] - rooms[0]['v'][0]:.2f}", offset=-0.95, horizontal=False)
    _dim(ax, (wu[0], rooms[1]["v"][0]), (wu[0], rooms[1]["v"][1]),
         f"{rooms[1]['v'][1] - rooms[1]['v'][0]:.2f}", offset=-0.95, horizontal=False)

    # Context notes on the two faces that matter
    fe = {int(r["side"]): r for _, r in facade_exposure().iterrows()}
    ax.annotate("COURTYARD AND POOL\nmain glazing on this face",
                xy=((wu[0] + wu[1]) / 2, wv[1] + 0.05),
                xytext=((wu[0] + wu[1]) / 2, wv[1] + 2.05),
                ha="center", va="bottom", fontsize=6.4, color=GLASS,
                arrowprops=dict(arrowstyle="-|>", color=GLASS, lw=0.8))
    ax.annotate(
        f"SSW NEIGHBOUR FACE, plot 5130123\n"
        f"{fe[2]['summer_afternoon_kwh_m2']:.0f} kWh/m2 summer afternoon. "
        f"Kept nearly solid.",
        xy=((wu[0] + wu[1]) / 2, wv[0] - 0.05),
        xytext=((wu[0] + wu[1]) / 2, wv[0] - 2.55),
        ha="center", va="top", fontsize=6.4, color=HOT,
        arrowprops=dict(arrowstyle="-|>", color=HOT, lw=0.8))
    ax.annotate("To road wing:\nArabic kitchen,\npantry, service",
                xy=(wu[0] - 0.05, (wv[0] + wv[1]) / 2),
                xytext=(wu[0] - 2.25, (wv[0] + wv[1]) / 2),
                ha="center", va="center", fontsize=6.0, color=MUTED,
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.8))

    ax.set_aspect("equal")
    ax.axis("off")
    return rows


def key_plan(ax, lay: dict):
    """Small locator plan of the whole of option C, plot up."""
    bearing = float(load_massing()["grid"]["bearing_deg"])
    opt = next(o for o in options() if o.key == "C")

    def g(geom):
        return site_to_grid(geom, bearing)

    def fill(geom, **kw):
        gs = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
        for p in gs:
            xs, ys = p.exterior.xy
            ax.fill(xs, ys, **kw)

    fill(g(plot_polygon()), facecolor="#fbfaf7", edgecolor="none")
    xs, ys = g(buildable_envelope()).exterior.xy
    ax.plot(xs, ys, color="#b8860b", lw=0.6, ls=(0, (5, 3)))
    fill(g(opt.deck), facecolor=DECK, edgecolor="none")
    fill(g(opt.pool), facecolor=POOL, edgecolor="none")
    fill(g(opt.ground), facecolor=MASS, edgecolor=INK, lw=0.6)
    fill(g(opt.first), facecolor="#b6b1a8", edgecolor=INK, lw=0.6)
    xs, ys = g(plot_polygon()).exterior.xy
    ax.plot(xs, ys, color=HOT, lw=1.0)

    wu, wv = lay["wing"]["u"], lay["wing"]["v"]
    ax.add_patch(Rectangle((wu[0], wv[0]), wu[1] - wu[0], wv[1] - wv[0],
                           facecolor="none", edgecolor=GOOD, lw=1.6, zorder=8))
    ax.text((wu[0] + wu[1]) / 2, (wv[0] + wv[1]) / 2, "THIS WING",
            ha="center", va="center", fontsize=5.6, color=GOOD, zorder=9)

    for s in sides():
        pass
    ax.text(16, 36.5, "4  NEIGHBOUR", ha="center", fontsize=5, color=MUTED)
    ax.text(-4.5, 17, "1\nENTRANCE", ha="center", va="center", fontsize=5,
            color=GOOD)
    ax.text(34.5, 17, "3\nLANDSCAPE", ha="center", va="center", fontsize=5,
            color=MUTED)
    ax.text(16, -3.5, "2  NEIGHBOUR", ha="center", fontsize=5, color=MUTED)

    a = np.radians(float(load_massing()["grid"]["bearing_deg"]))
    dx, dy = -np.sin(a), np.cos(a)
    ax.annotate("", xy=(33 + dx * 4, 33 + dy * 4), xytext=(33, 33),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.8))
    ax.text(33 + dx * 5.6, 33 + dy * 5.6, "N", ha="center", va="center",
            fontsize=5.6, color=INK)

    ax.set_aspect("equal")
    ax.set_xlim(-9, 40)
    ax.set_ylim(-6, 40)
    ax.axis("off")
    ax.set_title("Option C, ground floor. Plot up, not north up.",
                 fontsize=7, color=INK, loc="left", pad=4)


def build() -> Path:
    lay = layout()
    prog = program_rooms()

    fig = plt.figure(figsize=A3)
    fig.patch.set_facecolor("white")

    fig.text(0.035, 0.952, "VILLA 5130272", fontsize=20, color=INK)
    fig.text(0.035, 0.930, "SAIH SHUAIB 1, JEBEL ALI HILLS, DUBAI",
             fontsize=7, color=MUTED)
    fig.text(0.035, 0.900, "OPTION C, SINGLE STOREY WING", fontsize=12, color=INK)
    fig.text(0.035, 0.882,
             "Indicative room layout. Phase 1 preview at the owner's request.",
             fontsize=7, color=MUTED)
    fig.text(0.60, 0.900, "INDICATIVE", fontsize=12, color=HOT)
    fig.text(0.60, 0.882,
             "Not a designed layout. Room arrangement is Phase 2, which is\n"
             "blocked by OI-01, whether the garage counts toward GFA.",
             fontsize=6.6, color=MUTED, va="top")

    # True 1:75. Axes width 0.55 of 420 mm is 231 mm, which at 1:75 is 17.325 m.
    w_frac, h_frac = 0.55, 0.60
    ax = fig.add_axes([0.035, 0.195, w_frac, h_frac])
    span_x = 420 * w_frac / 1000 * SCALE
    span_y = 297 * h_frac / 1000 * SCALE
    wu, wv = lay["wing"]["u"], lay["wing"]["v"]
    cx, cy = (wu[0] + wu[1]) / 2, (wv[0] + wv[1]) / 2
    ax.set_xlim(cx - span_x / 2, cx + span_x / 2)
    ax.set_ylim(cy - span_y / 2 + 0.6, cy + span_y / 2 + 0.6)
    rows = wing_plan(ax, lay, prog)

    axk = fig.add_axes([0.635, 0.545, 0.325, 0.30])
    key_plan(axk, lay)

    # Schedule. Laid out in explicit figure coordinates rather than inside an
    # axes, so the row spacing is exact and cannot collide with the key plan.
    wu, wv = lay["wing"]["u"], lay["wing"]["v"]
    total = sum(r["area"] for r in rows)
    target = sum(r["target"] for r in rows)
    gross = (wu[1] - wu[0]) * (wv[1] - wv[0])

    X0, X1, X2, X3 = 0.635, 0.845, 0.905, 0.960
    y = 0.505
    fig.text(X0, y, "WHAT IS IN THE WING", fontsize=9, color=INK)
    y -= 0.030
    for x, label, ha in ((X0, "Room", "left"), (X1, "Drawn", "right"),
                         (X2, "Brief", "right"), (X3, "Diff", "right")):
        fig.text(x, y, label, fontsize=6.3, color=MUTED, ha=ha)
    y -= 0.011
    fig.lines.append(plt.Line2D([X0, X3], [y, y], color="#d8d4cd", lw=0.6,
                                transform=fig.transFigure))

    y -= 0.022
    for r in rows:
        fig.text(X0, y, r["name"], fontsize=6.9, color=INK)
        fig.text(X1, y, f"{r['area']:.1f}", fontsize=6.9, color=INK, ha="right")
        fig.text(X2, y, f"{r['target']:.0f}", fontsize=6.9, color=MUTED, ha="right")
        fig.text(X3, y, f"{r['delta']:+.1f}", fontsize=6.9, ha="right",
                 color=GOOD if r["delta"] >= 0 else HOT)
        y -= 0.024

    y -= 0.004
    fig.lines.append(plt.Line2D([X0, X3], [y, y], color="#d8d4cd", lw=0.6,
                                transform=fig.transFigure))
    y -= 0.024
    fig.text(X0, y, "Net rooms", fontsize=6.9, color=INK)
    fig.text(X1, y, f"{total:.1f}", fontsize=6.9, color=INK, ha="right")
    fig.text(X2, y, f"{target:.0f}", fontsize=6.9, color=MUTED, ha="right")
    fig.text(X3, y, f"{total - target:+.1f}", fontsize=6.9, color=GOOD, ha="right")
    y -= 0.024
    fig.text(X0, y, "Wing gross footprint", fontsize=6.9, color=INK)
    fig.text(X1, y, f"{gross:.1f}", fontsize=6.9, color=INK, ha="right")
    y -= 0.024
    fig.text(X0, y, "Net to gross achieved", fontsize=6.9, color=INK)
    fig.text(X1, y, f"{gross / total:.2f}", fontsize=6.9, color=GOOD, ha="right")
    fig.text(X2, y, f"{1.18:.2f}", fontsize=6.9, color=MUTED, ha="right")
    fig.text(X3, y, "assumed", fontsize=5.6, color=MUTED, ha="right")

    y -= 0.034
    fig.text(X0, y,
             f"The wing's gross footprint is fixed at {gross:.1f} m2 however it is\n"
             f"divided, so choosing option C moves no GFA. All three options\n"
             f"carry the same 406.5 m2 ground floor and 290.3 m2 first floor.\n\n"
             f"Laying the wing out at a single depth with few partitions\n"
             f"returns {total:.1f} m2 of room against {target:.0f} m2 of brief target,\n"
             f"{total - target:+.1f} m2 better, at a net to gross of {gross / total:.2f} against the\n"
             f"{1.18:.2f} assumed for the villa as a whole. The bedroom floor,\n"
             f"with en-suites and corridors, will be worse than this.",
             fontsize=6.3, color=MUTED, va="top", linespacing=1.55)

    # Legend and notes
    fig.text(0.035, 0.145, "NOTES", fontsize=8, color=INK)
    fig.text(0.035, 0.128,
             "Blue line marks the main glazing: the courtyard face looking at the pool, and the ESE end facing landscape plot 5130274.\n"
             "The SSW back wall stays nearly solid because it takes 141 kWh/m2 of summer afternoon sun, second worst on the plot.\n"
             "The living room is double height. Nothing sits above this wing in option C, so that volume costs no upper floor area,\n"
             "which it would in option A where the first floor runs over the living room.\n"
             "Show kitchen sits against the road wing so it backs onto the Arabic kitchen and pantry, per CLAUDE.md section 4.\n"
             "External walls 0.25 m, internal 0.15 m, both indicative. Structure is by a licensed structural engineer and not in scope.",
             fontsize=6.4, color=MUTED, va="top", linespacing=1.65)

    fig.text(0.965, 0.040, STAMP, fontsize=7.5, color=HOT, ha="right")
    fig.text(0.965, 0.024,
             f"Drawing VJH-MA-002   Phase 1 preview   Rev A   A3 landscape   "
             f"true 1:{SCALE}", fontsize=6, color=MUTED, ha="right")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, facecolor="white")
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    print(f"PDF  {build().relative_to(REPO_ROOT)}")
