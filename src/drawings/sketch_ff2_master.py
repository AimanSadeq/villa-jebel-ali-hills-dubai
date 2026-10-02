"""Sketch VJH-SK-015: the master suite arranged to the brief inside its walls
(first floor answer FF2 A, 2026-10-02).

Reads the built first floor from brief/reference_plan.yaml (frame metres: x
along the road from the carport end, y from the road) and draws the master
suite at a large scale with its furniture: the bed zone, a private sitting area
by the balcony, a coffee station, his and hers walk-in wardrobes in the
dressing room, and a bathroom with a bathtub, a separate shower, two basins
and a WC. Nothing is written back to the brief; the walls do not move.

Furniture sizes are indicative. Plot orientation as the other sketches: road
on the left, backyard on the right, the carport end (south) at the bottom.

Run: python src/drawings/sketch_ff2_master.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import Circle, Ellipse, Rectangle  # noqa: E402
from shapely.geometry import box  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from drawings.sketch_doors import draw_door  # noqa: E402
from model.doors import resolve  # noqa: E402
from model.heights import clear_heights  # noqa: E402
from model.reference_plan import _outline  # noqa: E402

PLAN = REPO_ROOT / "brief" / "reference_plan.yaml"
LAYOUTS = REPO_ROOT / "brief" / "layouts.yaml"
OUT_PDF = REPO_ROOT / "output" / "pdf" / "VJH-SK-015_Master_Suite.pdf"
OUT_PNG = REPO_ROOT / "output" / "pdf" / "VJH-SK-015_Master_Suite.png"

SQFT = 10.7639
INK, MUTED, WALL, FURN, RED = "#1a1a1a", "#6b6b6b", "#262626", "#8a6a3f", "#b3261e"
SUITE, OTHER, BATH, OUT = "#fdf3dc", "#f4f2ee", "#e4ecf2", "#ffffff"


def R(ax, x0, x1, y0, y1, **kw):
    """A rectangle given in the plan frame (plot X = frame y, plot Y = frame x)."""
    kw.setdefault("fill", False)
    kw.setdefault("ec", FURN)
    kw.setdefault("lw", 0.8)
    kw.setdefault("zorder", 4)
    ax.add_patch(Rectangle((y0, x0), y1 - y0, x1 - x0, **kw))


def T(ax, x, y, text, size=6.0, color=FURN, **kw):
    ax.text(y, x, text, ha="center", va="center", fontsize=size, color=color, zorder=6,
            clip_on=True, **kw)


def label(ax, r, name, h, outside=False):
    x0, x1, y0, y1 = r["x0"], r["x1"], r["y0"], r["y1"]
    w, ln = sorted((x1 - x0, y1 - y0))
    a = w * ln
    txt = f"{name}\n{w:.2f} x {ln:.2f} m\n{a:.1f} m² ({a * SQFT:,.0f} sq ft)"
    txt += "\nopen, outside GFA" if outside else f"\nclear height {h:.2f} m"
    return txt


def draw_master_furniture(ax, by: dict):
    """The master suite's furniture as approved (FF2, FF3), in the plan frame."""
    m, dr, ba, bal = by["master_suite"], by["master_dress"], by["master_toilet"], by["balcony_master"]
    # Bedroom: bed zone toward the north wall, sitting area by the balcony.
    xb = m["x1"]
    R(ax, xb - 2.13, xb, 16.85, 18.78)                       # king bed 1.93 x 2.13
    R(ax, xb - 0.65, xb - 0.05, 16.95, 18.68, lw=0.5)        # pillows
    R(ax, xb - 0.50, xb, 16.30, 16.80)                       # bedside
    R(ax, xb - 0.50, xb, 18.83, 19.33)
    T(ax, xb - 1.35, 17.8, "BED", 6.5)
    R(ax, m["x0"] + 0.10, m["x0"] + 1.00, 17.20, 19.60)      # sofa
    for xc, yc in ((6.0, 17.4), (6.0, 19.4)):                # armchairs
        R(ax, xc - 0.40, xc + 0.40, yc - 0.40, yc + 0.40)
    ax.add_patch(Circle((18.4, 4.95), 0.45, fill=False, ec=FURN, lw=0.8, zorder=4))
    T(ax, 4.95, 20.05, "PRIVATE SITTING", 6.5)
    R(ax, 6.60, 8.40, m["y0"], m["y0"] + 0.60)               # coffee station
    T(ax, 7.5, m["y0"] + 0.30, "COFFEE STATION", 5.0)

    # Dressing room: his side and hers side, each a full run of wardrobes.
    R(ax, dr["x0"], dr["x0"] + 0.60, dr["y0"] + 0.15, dr["y1"] - 0.10, hatch="////")
    R(ax, dr["x1"] - 0.60, dr["x1"], dr["y0"] + 0.15, dr["y1"] - 0.10, hatch="////")
    R(ax, 4.65, 5.45, 11.70, 13.90)                          # dressing island
    T(ax, dr["x0"] + 0.85, 12.7, "HIS WIR, 4.3 m of wardrobes", 5.2,
      bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.3))
    T(ax, dr["x1"] - 0.85, 12.7, "HERS WIR, 4.3 m of wardrobes", 5.2,
      bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.3))
    T(ax, 5.05, 12.8, "island", 5.0, rotation=90)

    # Bathroom: tub under the window, walk-in shower, two basins, WC room.
    ax.add_patch(Ellipse((6.95, 4.20), 0.80, 1.70, fill=False, ec=FURN, lw=0.8, zorder=4))
    T(ax, 4.20, 6.95, "BATH", 5.5)
    R(ax, ba["x1"] - 1.20, ba["x1"], ba["y0"], ba["y0"] + 1.20)
    T(ax, ba["x1"] - 0.60, ba["y0"] + 0.60, "SHOWER", 5.0)
    R(ax, ba["x1"] - 0.60, ba["x1"], 8.00, 10.20)
    for yc in (8.55, 9.65):
        ax.add_patch(Ellipse((yc, ba["x1"] - 0.30), 0.40, 0.30, fill=False, ec=FURN, lw=0.6, zorder=4))
    T(ax, ba["x1"] - 0.30, 9.1, "2 BASINS", 4.6, rotation=90)
    # WC room: partitions with a 0.70 m door toward the basins.
    xw = ba["x0"] + 1.20
    ax.plot([8.75, 8.75], [ba["x0"], xw], color=WALL, lw=1.4, zorder=4)
    ax.plot([8.75, 9.10], [xw, xw], color=WALL, lw=1.4, zorder=4)
    ax.plot([9.80, ba["y1"]], [xw, xw], color=WALL, lw=1.4, zorder=4)
    draw_door(ax, "x", xw - 0.05, xw + 0.05, 9.45, 0.70, "single", 1, "")  # opens outward
    ax.add_patch(Ellipse((9.80, ba["x0"] + 0.45), 0.55, 0.38, fill=False, ec=FURN, lw=0.6, zorder=4))
    T(ax, ba["x0"] + 0.62, 9.3, "WC", 5.0)

    # Balcony furniture.
    for xc in (4.3, 5.6):
        R(ax, xc - 0.35, xc + 0.35, bal["y0"] + 0.25, bal["y0"] + 1.75)
    T(ax, 4.95, bal["y0"] + 1.0, "loungers", 5.0, rotation=90)


def main() -> int:
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    lay = yaml.safe_load(LAYOUTS.read_text(encoding="utf-8"))
    H = clear_heights(lay)
    first = plan["first"]
    by = {r["key"]: r for r in first}
    m, dr, ba, bal = by["master_suite"], by["master_dress"], by["master_toilet"], by["balcony_master"]

    fig = plt.figure(figsize=(16.5, 11.7))
    ax = fig.add_axes([0.02, 0.17, 0.70, 0.74])

    # Context: the first floor as built, grey; the suite coloured.
    for r in first:
        x0, x1, y0, y1 = r["x0"], r["x1"], r["y0"], r["y1"]
        if r["kind"] in ("balcony", "terrace"):
            fc, ls = OUT, "--"
        elif r["kind"] == "void":
            fc, ls = "#dfe9f2", "--"
        elif r["key"] in ("master_suite", "master_dress"):
            fc, ls = SUITE, "-"
        elif r["key"] == "master_toilet":
            fc, ls = BATH, "-"
        else:
            fc, ls = OTHER, "-"
        ax.add_patch(Rectangle((y0, x0), y1 - y0, x1 - x0, fc=fc, ec=MUTED, lw=0.5, ls=ls, zorder=1))
    body = _outline([box(r["x0"], r["y0"], r["x1"], r["y1"]) for r in first
                     if r["kind"] in ("room", "circulation", "void")])
    xs, ys = body.exterior.xy
    ax.plot(list(ys), list(xs), color=WALL, lw=2.6, zorder=5)
    for key, name in (("bedroom_2", "Bedroom 2"), ("bedroom_2_dress", "Dress"),
                      ("bedroom_2_toilet", "WC"), ("stair_lift_first", "Stair"),
                      ("corridor_first", "Corridor"), ("void_over_living", "Void over living")):
        r = by.get(key)
        if r:
            T(ax, (r["x0"] + r["x1"]) / 2, (r["y0"] + r["y1"]) / 2, name, 6, MUTED)

    # Doors as built, from the schedule.
    doors = resolve(first, [d for d in plan["doors"] if d["storey"] == "first"])
    for d in doors:
        draw_door(ax, d["axis"], d["lo"], d["hi"], d["c"], d["w"], d["kind"], d["s"], d["no"])

    draw_master_furniture(ax, by)

    # Labels (rule 9).
    for r, name, hh, out in ((m, "MASTER BEDROOM AND SITTING", H["first"], False),
                             (dr, "HIS AND HERS DRESSING", H["first"], False),
                             (ba, "MASTER BATH", H["first"], False),
                             (bal, "BALCONY", 0, True)):
        cx, cy = (r["x0"] + r["x1"]) / 2, (r["y0"] + r["y1"]) / 2
        if r is m:
            cx, cy = 8.6, 19.65
        if r is dr:
            cx = 5.05
            cy = 11.15
        if r is ba:
            cx, cy = 5.0, 8.2
        ax.text(cy, cx, label(ax, r, name, hh, out), ha="center", va="center", fontsize=6.4,
                color=INK, weight="bold", zorder=7, linespacing=1.25,
                bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.5))

    ax.text(5.2, 2.2, "ROAD (side 1)", ha="center", fontsize=7, color=MUTED, weight="bold")
    ax.text(22.5, 2.2, "BACKYARD", ha="center", fontsize=7, color="#2e7d4f", weight="bold")
    ax.annotate("", xy=(4.6, 12.2), xytext=(4.6, 10.6), arrowprops=dict(arrowstyle="-|>", color=INK))
    ax.text(4.6, 12.4, "N (plan, approximate)", ha="center", va="bottom", fontsize=6)
    for t in ax.texts:
        t.set_clip_on(True)
    ax.set_xlim(4.2, 23.6)
    ax.set_ylim(1.6, 13.2)
    ax.set_aspect("equal")
    ax.axis("off")

    suite = sum((r["x1"] - r["x0"]) * (r["y1"] - r["y0"]) for r in (m, dr, ba))
    notes = [
        f"Master suite {suite:.1f} m\u00b2 ({suite * SQFT:,.0f} sq ft) inside",
        "its existing walls; the brief asks 70 to 80 m\u00b2.",
        "",
        "Bed zone at the north wall, facing the",
        "backyard; the private sitting area by the",
        "balcony doors (F14).",
        "",
        "Coffee station: 1.80 m of counter with a",
        "small fridge, between the sitting area and",
        "the dressing room.",
        "",
        "Dressing room: his wardrobes along one",
        "wall, hers along the other, 4.3 m each,",
        "with a dressing island in the middle.",
        "",
        "Bathroom: bathtub under the window, walk-in",
        "shower 1.20 x 1.20 m, two basins, WC in its",
        "own small room with a door.",
        "",
        "Walls, doors and GFA unchanged (661.69 m\u00b2).",
        "Furniture indicative.",
    ]
    fig.text(0.74, 0.86, "\n".join(notes), ha="left", va="top", fontsize=8.2, color=INK,
             linespacing=1.6, wrap=True)
    fig.suptitle("Villa 5130272, first floor answer FF2: the master suite to the brief, inside its walls",
                 x=0.02, ha="left", fontsize=13, weight="bold")
    fig.text(0.02, 0.935, f"First floor, clear height {H['first']:.2f} m. Coloured: the master suite. "
             "Grey: the rest of the first floor as built.", fontsize=8.5, color=MUTED)
    fig.text(0.98, 0.012, "CONCEPT DESIGN, NOT FOR CONSTRUCTION.  Decision sketch, indicative "
             "furniture.  VJH-SK-015", ha="right", fontsize=7.5, color=RED)
    fig.savefig(OUT_PDF)
    fig.savefig(OUT_PNG, dpi=130)
    print(f"Wrote {OUT_PDF.relative_to(REPO_ROOT)}; suite {suite:.2f} m2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
