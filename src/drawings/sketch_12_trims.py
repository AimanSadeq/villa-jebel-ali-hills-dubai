"""Sketch VJH-SK-014: two first floor trims that bring answer 12 inside the
GFA cap.

Answer 12 as approved on sketch VJH-SK-013 measures 673.48 m2, 10.49 m2 over
the 662.99 m2 cap. GFA is measured as the build measures it (each floor's
outline less its voids; balconies and terraces outside, D-039, TO VERIFY), so
only trims that move an outside wall, add void, or turn floor into an open
balcony count. Making a room smaller inside the same walls saves nothing.

  A  The first floor pantry and linen store become void over the island
     kitchen (the kitchen goes double height with the living room).
  B  Bedrooms 2 and 3 (and bedroom 3's WC) step back 1.00 m from the road;
     the strips become open recesses that shade the road face.

The ground floor is unchanged in both. Nothing is written back to the brief.

Run: python src/drawings/sketch_12_trims.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from drawings.sketch_12_floors import (CAP, CHANGED, F_LABELS, INK, MUTED, PLAN, SQFT,  # noqa: E402
                                       _draw_floor, apply_answer_12, clear_heights, dims_text,
                                       plan_before_12,
                                       measure)
from drawings.sketch_doors import draw_all, place, unreached  # noqa: E402

OUT_PDF = REPO_ROOT / "output" / "pdf" / "VJH-SK-014_First_Floor_Trims.pdf"
OUT_PNG = REPO_ROOT / "output" / "pdf" / "VJH-SK-014_First_Floor_Trims.png"

STEP_BACK = 1.00   # option B, metres


def _by(rooms, key):
    return next(r for r in rooms if r["key"] == key)


def option_a(first: list) -> tuple[list, frozenset, list[str]]:
    f = copy.deepcopy(first)
    pantry, linen = _by(f, "pantry_first"), _by(f, "linen_storage")
    f = [r for r in f if r["key"] not in ("pantry_first", "linen_storage")]
    v = _by(f, "void_over_living")
    v["x0"], v["new"] = pantry["x0"], True
    notes = [
        f"Pantry ({dims_text(pantry['x0'], pantry['x1'], pantry['y0'], pantry['y1'], small=True).replace(chr(10), ', ')}) "
        f"and linen store ({dims_text(linen['x0'], linen['x1'], linen['y0'], linen['y1'], small=True).replace(chr(10), ', ')}) "
        "are removed; the void runs over the island kitchen too.",
        "The island kitchen becomes double height with the living room (8.55 m clear over most of it).",
        "The brief's 6 m² linen store has to find a new place (for example cupboards in the master or bedroom "
        "dressing rooms), decided with the first floor.",
        "The coffee station of the reference pantry moves into the master suite, as the brief asks.",
    ]
    return f, frozenset({"pantry_first", "linen_storage"}), notes


def option_b(first: list) -> tuple[list, frozenset, list[str]]:
    f = copy.deepcopy(first)
    notes = []
    for key in ("bedroom_2", "bedroom_3", "bedroom_3_toilet"):
        r = _by(f, key)
        r["y0"], r["new"] = round(r["y0"] + STEP_BACK, 3), True
    b2, b3, t3 = _by(f, "bedroom_2"), _by(f, "bedroom_3"), _by(f, "bedroom_3_toilet")
    f.append({"key": "recess_bedroom_2", "kind": "balcony", "x0": b2["x0"], "x1": b2["x1"],
              "y0": round(b2["y0"] - STEP_BACK, 3), "y1": b2["y0"], "new": True})
    f.append({"key": "recess_bedroom_3", "kind": "balcony", "x0": b3["x0"], "x1": t3["x1"],
              "y0": round(b3["y0"] - STEP_BACK, 3), "y1": b3["y0"], "new": True})
    for key, name in (("bedroom_2", "Bedroom 2"), ("bedroom_3", "Bedroom 3"), ("bedroom_3_toilet", "Bedroom 3 WC")):
        r = _by(f, key)
        notes.append(f"{name}: {dims_text(r['x0'], r['x1'], r['y0'], r['y1'], small=True).replace(chr(10), ', ')}")
    s2 = sum((r["x1"] - r["x0"]) * (r["y1"] - r["y0"]) for r in f
             if r["key"] in ("bedroom_2", "bedroom_2_dress", "bedroom_2_toilet"))
    s3 = sum((r["x1"] - r["x0"]) * (r["y1"] - r["y0"]) for r in f
             if r["key"] in ("bedroom_3", "bedroom_3_dress", "bedroom_3_toilet"))
    notes.append("Bedroom 3 WC gets tight at that size: WC, basin and shower only, no bath.")
    notes.append(f"Suites (room, dress, WC): bedroom 2 {s2:.1f} m², bedroom 3 {s3:.1f} m²; "
                 "the brief asks 30 to 35 m².")
    notes.append(f"The {STEP_BACK:.2f} m strips on the road face become open recesses (balcony or shading ledge), "
                 "outside GFA (D-039, TO VERIFY). They shade the bedroom glass on the hot road face, as the brief "
                 "asks for south and west faces.")
    return f, frozenset(), notes


LABELS = {**F_LABELS, "recess_bedroom_2": "Recess", "recess_bedroom_3": "Recess",
          "void_over_living": "Void over living\n(double height)"}


def main() -> int:
    plan = plan_before_12()
    ground, first, _ = apply_answer_12(plan)
    H = clear_heights(plan)
    base = measure(ground, first)
    joins_f = {frozenset(j.split("/")) for j in plan["open_joins"]["first"]}

    fig = plt.figure(figsize=(16.5, 11.7))
    for i, (letter, fn, title) in enumerate((
            ("A", option_a, "OPTION A: pantry and linen become void over the kitchen"),
            ("B", option_b, f"OPTION B: bedrooms 2 and 3 step back {STEP_BACK:.2f} m from the road"))):
        f, removed, notes = fn(first)
        m = measure(ground, f)
        labels = dict(LABELS)
        if letter == "A":
            labels["void_over_living"] = "Void over kitchen\nand living (double height)"
        ax = fig.add_axes([0.01 + i * 0.49, 0.25, 0.48, 0.63])
        _draw_floor(ax, f, m["f_poly"], labels,
                    f"{title}\nFIRST FLOOR   clear height {H['first']:.2f} m", "first", H)
        doors = place(f, "first", removed)
        draw_all(ax, doors)
        lost = unreached([r for r in f if r["kind"] in ("room", "circulation")], doors,
                         {j for j in joins_f if not (j & removed)}, "stair_lift_first")
        if lost:
            raise ValueError(f"option {letter}: rooms with no way in: {lost}")
        under = CAP - m["total"]
        head = (f"GFA {m['total']:.2f} m² ({m['total'] * SQFT:,.0f} sq ft): saves "
                f"{base['total'] - m['total']:.2f} m², {under:.2f} m² "
                f"({under * SQFT:,.0f} sq ft) inside the {CAP} m² cap")
        fig.text(0.03 + i * 0.49, 0.235, head + "\n\n" + "\n".join("• " + n for n in notes),
                 ha="left", va="top", fontsize=7.6, color=INK, linespacing=1.5, wrap=True)
        print(f"option {letter}: {m['total']:.2f} m2, saves {base['total'] - m['total']:.2f}, "
              f"{under:.2f} inside the cap")

    fig.suptitle("Villa 5130272, answer 12: two ways to bring the first floor inside the GFA cap",
                 x=0.01, ha="left", fontsize=13, weight="bold")
    fig.text(0.01, 0.94,
             f"Ground floor as approved on VJH-SK-013 in both. Before trimming: {base['total']:.2f} m², "
             f"{base['total'] - CAP:.2f} m² over. Coloured rooms change; grey rooms are the reference "
             "placeholder first floor. GFA measured as the build measures it.",
             fontsize=8.5, color=MUTED)
    fig.text(0.98, 0.012, "CONCEPT DESIGN, NOT FOR CONSTRUCTION.  Decision sketch.  VJH-SK-014",
             ha="right", fontsize=7.5, color=CHANGED)
    fig.savefig(OUT_PDF)
    fig.savefig(OUT_PNG, dpi=130)
    print(f"Wrote {OUT_PDF.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
