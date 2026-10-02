"""Sketch of both floors with all of answer 12 applied (12, 12a, 12b, 12c, 12d).

Ground floor: kitchen, double height living room and dining along the backyard
(12a option B); the salon in the lawn court's place, fully open to the dining
(12c), lined up with the dining's north wall and 6.00 m across (12d). First floor: the void over the living room, the family room above the
salon off the gallery (12b); everything else is still the reference's
placeholder first floor.

GFA is measured here the way src/model/reference_plan.py measures the build
(outline of each floor less its voids, carport and balconies outside, D-039),
so the figure on the sheet is the one the rebuild would report, before any
first floor trims. Nothing is written back to the brief.

Run: python src/drawings/sketch_12_floors.py

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

from drawings.sketch_12a import (CHANGED, INK, MUTED, OPEN, SALON, SQFT, WALL,  # noqa: E402
                                 _furniture, _label)
from model.reference_plan import _outline  # noqa: E402

PLAN = REPO_ROOT / "brief" / "reference_plan.yaml"
OUT_PDF = REPO_ROOT / "output" / "pdf" / "VJH-SK-013_Answer_12_Both_Floors.pdf"
OUT_PNG = REPO_ROOT / "output" / "pdf" / "VJH-SK-013_Answer_12_Both_Floors.png"

CAP = 662.99
VOID = "#dfe9f2"
NEW = "#e8f3ea"
OTHER = "#f4f2ee"

G_LABELS = {
    "garage": "Carport, 3 cars", "guest_bedroom": "Guest bed", "guest_toilet": "WC",
    "guest_dress": "Dress", "office_toilet": "WC", "home_office": "Office",
    "main_entrance": "Porch", "plant_room": "Plant", "outdoor_bathroom": "Out. bath",
    "service_lobby": "Serv. lobby", "entrance_foyer": "Foyer\n(double height)",
    "lift": "Lift", "maids_toilet": "WC", "wash": "Wash", "stair_hall": "Stair hall",
    "maids_room": "Maid", "guest_powder": "Powder", "stair_lift_ground": "Stair",
    "pantry": "Store", "laundry": "Laundry", "arabic_kitchen": "Arabic kitchen",
}
F_LABELS = {
    "master_suite": "Master bedroom", "master_dress": "Master dress", "master_toilet": "Master bath",
    "bedroom_2": "Bedroom 2", "bedroom_2_dress": "Dress", "bedroom_2_toilet": "WC",
    "bedroom_3": "Bedroom 3", "bedroom_3_dress": "Dress", "bedroom_3_toilet": "WC",
    "bedroom_4": "Bedroom 4", "bedroom_4_dress": "Dress", "bedroom_4_toilet": "WC",
    "linen_storage": "Linen", "pantry_first": "Pantry", "stair_lift_first": "Stair",
    "lift_first": "Lift", "landing": "Landing", "lift_lobby": "Lobby",
    "corridor_first": "Gallery / corridor", "gallery": "Gallery",
    "void_over_foyer": "Void over foyer", "void_over_entrance": "Void over porch",
    "balcony_master": "Balcony", "balcony_bedroom_4": "Balcony",
    "terrace_over_carport": "Terrace over carport", "terrace_over_carport_side": "Terr.",
    "family_living": "Family room", "void_over_living": "Void over living\n(double height)",
}


def _r(key, kind, x0, x1, y0, y1, new=False):
    return {"key": key, "kind": kind, "x0": x0, "x1": x1, "y0": y0, "y1": y1, "new": new}


def apply_answer_12(plan: dict) -> tuple[list, list, list[str]]:
    g = {r["key"]: r for r in plan["ground"]}
    f = {r["key"]: r for r in plan["first"]}
    k, m, c = g["show_kitchen"], g["majlis"], g["lawn_court"]
    y0, y1 = k["y0"], k["y1"]
    split_ld = round(m["x1"] - 6.00, 2)  # 12a B: dining 6 x 6 in the north corner

    ground = [dict(r) for r in plan["ground"]
              if r["key"] not in {"show_kitchen", "family_sitting", "dining", "majlis", "lawn_court"}]
    # 12d C: the salon's north wall lines up with the dining's, and the open
    # salon/dining line moves toward the backyard so the salon is 6.00 m across
    # (the old 0.25 m wall line between them becomes floor). The dining is
    # 6.00 x 5.25 m.
    sd_line = round(c["y0"] + 6.00, 3)
    ground += [
        _r("show_kitchen", "room", k["x0"], k["x1"], y0, y1, True),
        _r("living", "room", k["x1"], split_ld, y0, y1, True),
        _r("dining", "room", split_ld, m["x1"], sd_line, y1, True),
        _r("salon", "room", c["x0"], m["x1"], c["y0"], sd_line, True),
    ]

    # First floor. The void over the living room keeps the gallery (corridor)
    # along its road side as the route to bedroom 4; it spans from the kitchen
    # line to bedroom 4's wall, on the first floor plate's own rear line.
    corr, fam_old = f["corridor_first"], f["family_living"]
    void = _r("void_over_living", "void", k["x1"], corr["x1"], corr["y1"], fam_old["y1"], True)
    first = []
    notes = []
    for r in plan["first"]:
        key = r["key"]
        if key in ("family_living", "lawn_court_open"):
            continue
        if key == "balcony_family":
            notes.append("The family balcony goes with the old family room: its place becomes "
                         "the void's glass; a shading canopy there is a first floor question.")
            continue
        r = dict(r)
        if key in ("pantry_first", "linen_storage") and r["x1"] > void["x0"] - 0.15:
            notes.append(f"{F_LABELS[key]} trimmed {r['x1'] - (void['x0'] - 0.15):.2f} m to clear the void.")
            r["x1"] = round(void["x0"] - 0.15, 3)
            r["new"] = True
        first.append(r)
    cv = f["lawn_court_open"]
    first += [void, _r("family_living", "room", cv["x0"], cv["x1"], cv["y0"], cv["y1"], True)]
    return ground, first, notes


def measure(ground: list, first: list) -> dict:
    B = lambda r: box(r["x0"], r["y0"], r["x1"], r["y1"])  # noqa: E731
    g_body = _outline([B(r) for r in ground if r["kind"] in ("room", "service", "circulation")])
    f_in = [r for r in first if r["kind"] in ("room", "circulation", "void")]
    f_body = _outline([B(r) for r in f_in])
    voids = sum(B(r).area for r in f_in if r["kind"] == "void")
    out = {"ground": g_body.area, "first": f_body.area - voids, "voids": voids,
           "g_poly": g_body, "f_poly": f_body}
    out["total"] = out["ground"] + out["first"]
    return out


def _draw_floor(ax, rooms, outline, labels, title, floor):
    for r in rooms:
        x0, x1, y0, y1, kind = r["x0"], r["x1"], r["y0"], r["y1"], r["kind"]
        new = r.get("new", False)
        if kind == "void":
            fc, ls = VOID, "--"
        elif kind in ("carport", "porch", "balcony", "terrace"):
            fc, ls = "#ffffff", "--"
        elif r["key"] == "salon":
            fc, ls = SALON, "-"
        elif new and r["key"] in ("show_kitchen", "living", "dining"):
            fc, ls = OPEN, (0, (4, 3))  # one open room: no walls between (D-033)
        elif new:
            fc, ls = NEW, "-"
        else:
            fc, ls = OTHER, "-"
        ax.add_patch(Rectangle((y0, x0), y1 - y0, x1 - x0, fc=fc, ec=INK if new else MUTED,
                               lw=0.7 if new else 0.5, ls=ls, zorder=2 if new else 1))
        if floor == "ground" and r["key"] in ("show_kitchen", "living", "dining", "salon"):
            _furniture(ax, r["key"], x0, x1, y0, y1, "B")
        a = (x1 - x0) * (y1 - y0)
        name = {"show_kitchen": "Island kitchen", "living": "Living room\n(double height)",
                "dining": "Dining", "salon": "Salon (majlis)"}.get(r["key"], labels.get(r["key"]))
        if not name:
            continue
        small = a < 9
        big = new and kind != "void"
        _label(ax, x0, x1, y0, y1, name, size=6.8 if big else (4.4 if small else 5.2),
               area=not small and kind not in ("carport",), weight="bold" if big else "normal",
               color=INK if big else MUTED)

    xs, ys = outline.exterior.xy
    ax.plot(list(ys), list(xs), color=WALL, lw=2.6, zorder=4)

    ax.text(-0.8, 13.5, "ROAD (side 1)", rotation=90, ha="center", va="center",
            fontsize=7, color=MUTED, weight="bold")
    ax.text(24.2, 13.5, "BACKYARD", rotation=90, ha="center", va="center", fontsize=7,
            color="#2e7d4f", weight="bold")
    ax.annotate("", xy=(-0.4, 27.4), xytext=(-0.4, 25.6),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))
    ax.text(-0.4, 27.7, "N", ha="center", va="bottom", fontsize=7, weight="bold")
    ax.set_title(title, fontsize=10, weight="bold", loc="left")
    ax.set_xlim(-1.6, 25.0)
    ax.set_ylim(-1.0, 28.6)
    ax.set_aspect("equal")
    ax.axis("off")


def main() -> int:
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    ground, first, notes = apply_answer_12(plan)
    before = measure([dict(r) for r in plan["ground"]], [dict(r) for r in plan["first"]])
    after = measure(ground, first)

    fig = plt.figure(figsize=(16.5, 11.7))  # A3 landscape
    ax_g = fig.add_axes([0.01, 0.20, 0.48, 0.70])
    ax_f = fig.add_axes([0.50, 0.20, 0.48, 0.70])
    _draw_floor(ax_g, ground, after["g_poly"], G_LABELS, "GROUND FLOOR", "ground")
    _draw_floor(ax_f, first, after["f_poly"], F_LABELS, "FIRST FLOOR (placeholder except the changes in colour)",
                "first")

    # Ground: the salon is open to the dining (12c): no wall drawn between them.
    s = next(r for r in ground if r["key"] == "salon")
    ax_g.plot([s["y1"], s["y1"]], [s["x0"], s["x1"]], color="white", lw=2.0, zorder=5)
    ax_g.plot([s["y1"], s["y1"]], [s["x0"], s["x1"]], color=MUTED, lw=0.8, ls=(0, (4, 3)), zorder=5)
    ax_g.text(s["y1"], s["x0"] - 0.15, "open to dining (12c)", ha="center", va="top",
              fontsize=5, color=CHANGED, zorder=6)
    # First: the family room door off the gallery.
    fam = next(r for r in first if r["key"] == "family_living")
    ax_f.text((fam["y0"] + fam["y1"]) / 2, fam["x0"] - 0.15, "door off the gallery", ha="center",
              va="top", fontsize=5, color=CHANGED, zorder=6)

    over = after["total"] - CAP
    verdict = (f"{over:.2f} m² ({over * SQFT:,.0f} sq ft) OVER the cap"
               if over > 0 else f"{-over:.2f} m² inside the cap")
    fam_a = (fam["x1"] - fam["x0"]) * (fam["y1"] - fam["y0"])
    lines = [
        "GFA, measured the way the build measures it (carport, balconies, terraces outside, D-039, TO VERIFY):",
        f"   Today (built, commit 6322806):  ground {before['ground']:.2f} + first {before['first']:.2f} "
        f"= {before['total']:.2f} m²",
        f"   With answer 12:                 ground {after['ground']:.2f} + first {after['first']:.2f} "
        f"= {after['total']:.2f} m² ({after['total'] * SQFT:,.0f} sq ft): {verdict} of {CAP} m²",
        "",
        f"Family room above the salon: {fam_a:.1f} m² ({fam_a * SQFT:,.0f} sq ft); "
        "the brief's target is 35 m².",
        "The gallery (corridor) along the void stays the route from the stair to bedroom 4; "
        "the living room is double height beyond it.",
    ] + notes
    fig.text(0.03, 0.185, "\n".join(lines), ha="left", va="top", fontsize=8.4, color=INK,
             linespacing=1.55, family="DejaVu Sans Mono")

    fig.suptitle("Villa 5130272, answer 12 on both floors: for review before the build",
                 x=0.01, ha="left", fontsize=13, weight="bold")
    fig.text(0.01, 0.94, "Coloured rooms change with answer 12; grey rooms are as built. "
             "The first floor is still the reference's placeholder, to be designed floor by floor (D-038).",
             fontsize=8.5, color=MUTED)
    fig.text(0.98, 0.012, "CONCEPT DESIGN, NOT FOR CONSTRUCTION.  Decision sketch, indicative "
             "furniture.  Dimensions from brief/reference_plan.yaml.  VJH-SK-013",
             ha="right", fontsize=7.5, color=CHANGED)
    fig.savefig(OUT_PDF)
    fig.savefig(OUT_PNG, dpi=130)
    print(f"Wrote {OUT_PDF.relative_to(REPO_ROOT)} and {OUT_PNG.name}")
    print(f"GFA before {before['total']:.2f}, after {after['total']:.2f} "
          f"(ground {after['ground']:.2f}, first {after['first']:.2f}, voids {after['voids']:.2f}); {verdict}")
    for line in notes:
        print("  " + line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
