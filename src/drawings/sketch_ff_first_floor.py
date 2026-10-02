"""Sketch VJH-SK-016: the whole first floor with the owner's answers FF1 to
FF7, for review before the first floor build.

The geometry comes from src/model/assemble_reference.py with the first floor
answers switched on (assemble(first_floor=True)), the same step the build will
run, so the sketch and the build cannot differ. Nothing is written back to the
brief. Furniture is indicative; the master suite's is VJH-SK-015's.

Plot orientation as the other sketches: road on the left, backyard on the
right, the carport end (south) at the bottom.

Run: python src/drawings/sketch_ff_first_floor.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from shapely.geometry import box  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from drawings.sketch_12_floors import measure  # noqa: E402
from drawings.sketch_doors import draw_door  # noqa: E402
from drawings.sketch_ff2_master import (BATH, FURN, INK, MUTED, OTHER, OUT, R, RED, SQFT, SUITE,  # noqa: E402
                                        WALL, T, draw_master_furniture)
from model.assemble_reference import assemble  # noqa: E402
from model.doors import resolve  # noqa: E402
from model.heights import clear_heights  # noqa: E402
from model.reference_plan import _outline  # noqa: E402

LAYOUTS = REPO_ROOT / "brief" / "layouts.yaml"
OUT_PDF = REPO_ROOT / "output" / "pdf" / "VJH-SK-016_First_Floor.pdf"
OUT_PNG = REPO_ROOT / "output" / "pdf" / "VJH-SK-016_First_Floor.png"
CAP = 662.99

NAMES = {
    "master_suite": "Master bedroom and sitting", "master_dress": "His and hers dressing",
    "master_toilet": "Master bath", "bedroom_2": "Bedroom 2", "bedroom_2_dress": "Dress",
    "bedroom_2_toilet": "Bath", "bedroom_3": "Bedroom 3", "bedroom_3_dress": "Dress",
    "bedroom_3_toilet": "Bath", "bedroom_4": "Bedroom 4", "bedroom_4_dress": "Dress",
    "bedroom_4_toilet": "Bath", "family_living": "Family room", "gallery": "Gallery",
    "stair_lift_first": "Stair", "lift_first": "Lift", "landing": "Landing",
    "lift_lobby": "Lift lobby", "corridor_first": "Corridor",
    "void_over_foyer": "Void over foyer", "void_over_entrance": "Void over porch",
    "void_over_living": "Void over living room and kitchen",
    "balcony_master": "Balcony", "balcony_bedroom_4": "Balcony",
    "terrace_over_carport": "Roof over carport", "terrace_over_carport_side": "Roof",
}
CHANGED = {"bedroom_4", "family_living", "gallery", "corridor_first", "void_over_living"}


def main() -> int:
    plan, _ = assemble(answer_12=True, first_floor=True)
    before, _ = assemble(answer_12=True, first_floor=False)
    lay = yaml.safe_load(LAYOUTS.read_text(encoding="utf-8"))
    H = clear_heights(lay)
    ground, first = plan["ground"], plan["first"]
    by = {r["key"]: r for r in first}
    m_now = measure(before["ground"], before["first"])["total"]
    m_new = measure(ground, first)["total"]

    fig = plt.figure(figsize=(16.5, 11.7))
    ax = fig.add_axes([0.01, 0.10, 0.70, 0.82])
    for r in first:
        x0, x1, y0, y1 = r["x0"], r["x1"], r["y0"], r["y1"]
        k = r["key"]
        if r["kind"] in ("balcony", "terrace"):
            fc, ls = OUT, "--"
        elif r["kind"] == "void":
            fc, ls = "#dfe9f2", "--"
        elif k.startswith("master"):
            fc, ls = (BATH if k == "master_toilet" else SUITE), "-"
        elif k in ("family_living", "gallery"):
            fc, ls = "#e8f3ea", "-"
        elif k.endswith("toilet"):
            fc, ls = BATH, "-"
        else:
            fc, ls = OTHER, "-"
        ax.add_patch(Rectangle((y0, x0), y1 - y0, x1 - x0, fc=fc, ec=INK if k in CHANGED else MUTED,
                               lw=0.9 if k in CHANGED else 0.5, ls=ls, zorder=1))
    body = _outline([box(r["x0"], r["y0"], r["x1"], r["y1"]) for r in first
                     if r["kind"] in ("room", "circulation", "void")])
    xs, ys = body.exterior.xy
    ax.plot(list(ys), list(xs), color=WALL, lw=2.6, zorder=5)

    # FF5: the family room and the gallery are one room: no wall between them.
    fam, gal = by["family_living"], by["gallery"]
    ax.add_patch(Rectangle((fam["y0"] + 0.02, gal["x1"] - 0.03), fam["y1"] - fam["y0"] - 0.04,
                           fam["x0"] - gal["x1"] + 0.06, fc="#e8f3ea", ec="none", zorder=2))
    ax.plot([fam["y0"], fam["y1"]], [(gal["x1"] + fam["x0"]) / 2] * 2, color=MUTED, lw=0.6,
            ls=(0, (4, 3)), zorder=3)

    doors = resolve(first, [d for d in plan["doors"] if d["storey"] == "first"])
    for d in doors:
        draw_door(ax, d["axis"], d["lo"], d["hi"], d["c"], d["w"], d["kind"], d["s"], d["no"])

    draw_master_furniture(ax, by)
    # Bedrooms: a bed against the dressing room wall, wardrobes with linen.
    for room, dress, bed in (("bedroom_2", "bedroom_2_dress", "x0"), ("bedroom_3", "bedroom_3_dress", "x1"),
                             ("bedroom_4", "bedroom_4_dress", "x1")):
        r, dr = by[room], by[dress]
        yc = (r["y0"] + r["y1"]) / 2
        if bed == "x0":
            R(ax, r["x0"], r["x0"] + 2.10, yc - 0.90, yc + 0.90)
            T(ax, r["x0"] + 1.1, yc, "BED", 6)
        else:
            R(ax, r["x1"] - 2.10, r["x1"], yc - 0.90, yc + 0.90)
            T(ax, r["x1"] - 1.1, yc, "BED", 6)
        long_x = (dr["x1"] - dr["x0"]) >= (dr["y1"] - dr["y0"])
        if long_x:
            R(ax, dr["x0"] + 0.1, dr["x1"] - 0.1, dr["y0"], dr["y0"] + 0.60, hatch="////")
        else:
            R(ax, dr["x0"], dr["x0"] + 0.60, dr["y0"] + 0.1, dr["y1"] - 0.1, hatch="////")
    # Family room: sofa, armchairs and a TV, looking over the foyer.
    R(ax, fam["x0"] + 0.6, fam["x0"] + 3.6, fam["y1"] - 1.0, fam["y1"] - 0.1)
    R(ax, fam["x0"] + 0.6, fam["x0"] + 1.5, fam["y0"] + 1.4, fam["y1"] - 1.0)
    R(ax, fam["x0"] + 2.0, fam["x0"] + 3.2, fam["y0"] + 2.0, fam["y0"] + 3.0)
    R(ax, fam["x1"] - 0.15, fam["x1"] - 0.05, fam["y0"] + 1.4, fam["y0"] + 3.4, fc="#333333")
    T(ax, fam["x1"] - 0.45, fam["y0"] + 2.4, "TV", 5.5)

    def lab(key, size=6.0, bold=False, where=None):
        r = by[key]
        w, ln = sorted((r["x1"] - r["x0"], r["y1"] - r["y0"]))
        a = w * ln
        txt = f"{NAMES.get(key, key)}\n{w:.2f} x {ln:.2f} m\n{a:.1f} m² ({a * SQFT:,.0f} sq ft)"
        if r["kind"] in ("balcony", "terrace"):
            txt += "\nopen, outside GFA"
        elif r["kind"] != "void":
            txt += f"\nh {H['first']:.2f} m"
        cx, cy = where or ((r["x0"] + r["x1"]) / 2, (r["y0"] + r["y1"]) / 2)
        ax.text(cy, cx, txt, ha="center", va="center", fontsize=size, color=INK,
                weight="bold" if bold else "normal", zorder=7, linespacing=1.2, clip_on=True,
                bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.4))

    lab("master_suite", 6.4, True, (8.6, 19.65))
    lab("master_dress", 5.6, True, (5.05, 11.15))
    lab("master_toilet", 5.6, True, (5.0, 8.2))
    for k in ("bedroom_2", "bedroom_3", "bedroom_4"):
        r = by[k]
        lab(k, 6.4, True, ((r["x0"] + r["x1"]) / 2, (r["y0"] + r["y1"]) / 2 + 1.3))
    lab("family_living", 6.4, True, ((fam["x0"] + fam["x1"]) / 2 + 0.3, fam["y0"] + 1.0))
    lab("gallery", 5.0, False)
    for k in ("bedroom_2_dress", "bedroom_2_toilet", "bedroom_3_dress", "bedroom_3_toilet",
              "bedroom_4_dress", "bedroom_4_toilet", "landing", "lift_lobby", "lift_first",
              "corridor_first", "void_over_living", "void_over_foyer", "void_over_entrance",
              "balcony_master", "balcony_bedroom_4", "stair_lift_first"):
        if k in by:
            lab(k, 4.6)

    ax.text(4.2, 28.2, "ROAD (side 1)", ha="center", fontsize=7, color=MUTED, weight="bold")
    ax.text(22.0, 28.2, "BACKYARD", ha="center", fontsize=7, color="#2e7d4f", weight="bold")
    ax.set_xlim(2.8, 24.2)
    ax.set_ylim(1.8, 28.8)
    ax.set_aspect("equal")
    ax.axis("off")

    fam_a = sum((by[k]["x1"] - by[k]["x0"]) * (by[k]["y1"] - by[k]["y0"]) for k in ("family_living", "gallery"))
    b4 = by["bedroom_4"]
    notes = [
        f"GFA {m_new:.2f} m² ({m_new * SQFT:,.0f} sq ft), {CAP - m_new:.2f} m²",
        f"inside the {CAP} m² cap (today {m_now:.2f} m²).",
        "",
        "FF2, FF3: master suite as sketch VJH-SK-015:",
        "sitting area, coffee station, his and hers",
        "dressing, bath with tub and separate shower.",
        "",
        "FF4: no linen store; linen in the built-in",
        "wardrobes of the dressing rooms (hatched).",
        "",
        f"FF5: family room open to the gallery, about",
        f"{fam_a:.1f} m² ({fam_a * SQFT:,.0f} sq ft), over the foyer void",
        "through the glass balustrade; door F13 gone.",
        "Bedroom 3 opens off it (F06).",
        "",
        "FF6: margin kept, no step back.",
        "",
        f"FF7: the wall at the end of the living room",
        "void stands on the TV wall: bedroom 4",
        f"{b4['x1'] - b4['x0']:.2f} x {b4['y1'] - b4['y0']:.2f} m.",
        "",
        "Unchanged from the reference placeholder:",
        "bedrooms 2 and 3 and every other wall.",
        f"Clear height {H['first']:.2f} m throughout.",
    ]
    fig.text(0.73, 0.88, "\n".join(notes), ha="left", va="top", fontsize=8.6, color=INK, linespacing=1.5)
    fig.suptitle("Villa 5130272, the first floor with answers FF1 to FF7: for review before the build",
                 x=0.01, ha="left", fontsize=13, weight="bold")
    fig.text(0.01, 0.94, "Bold outlines: what the answers change. Coloured: master suite, family room, "
             "baths. Furniture indicative.", fontsize=8.5, color=MUTED)
    fig.text(0.98, 0.012, "CONCEPT DESIGN, NOT FOR CONSTRUCTION.  Decision sketch.  VJH-SK-016",
             ha="right", fontsize=7.5, color=RED)
    fig.savefig(OUT_PDF)
    fig.savefig(OUT_PNG, dpi=130)
    print(f"Wrote {OUT_PDF.relative_to(REPO_ROOT)}: GFA {m_now:.2f} -> {m_new:.2f}, "
          f"family room with gallery {fam_a:.2f} m2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
