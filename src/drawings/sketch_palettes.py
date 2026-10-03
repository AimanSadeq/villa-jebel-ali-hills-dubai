"""Sketch VJH-SK-018: the three interior palettes proposed in brief/palettes.yaml
(answer P1), side by side, for the owner to choose from or adjust.

Each palette shows a living room vignette (floor, walls, feature wall,
joinery, sofa, accents, a pendant) and every swatch it sets, with its name.
Swatches are drawn from the colour, pattern and roughness the walkthrough will
use, so the sheet and the walkthrough cannot differ. Patterns are indicative.

Run: python src/drawings/sketch_palettes.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402
from scipy import ndimage  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
PALETTES = REPO_ROOT / "brief" / "palettes.yaml"
OUT_PDF = REPO_ROOT / "output" / "pdf" / "VJH-SK-018_Interior_Palettes.pdf"
OUT_PNG = REPO_ROOT / "output" / "pdf" / "VJH-SK-018_Interior_Palettes.png"
INK, MUTED, RED = "#1a1a1a", "#6b6b6b", "#b3261e"

ROWS = [
    ("FLOORS", [("flooring", "public", "Public rooms"), ("flooring", "kitchen", "Kitchens"),
                ("flooring", "bedrooms", "Bedrooms, office"), ("flooring", "wet", "Bathrooms"),
                ("flooring", "service", "Service, staff")]),
    ("WALLS AND CEILINGS", [("walls", "main", "Walls"), ("walls", "feature", "Feature walls"),
                            ("walls", "wet", "Bathroom walls"), ("walls", "ceiling", "Ceilings")]),
    ("ACCENTS", [("accents", "joinery", "Joinery"), ("accents", "worktop", "Worktops"),
                 ("accents", "textile", "Soft furnishings"), ("accents", "highlight", "Highlight")]),
    ("FIXTURES", [("fixtures", "metal", "Metalwork, taps, handles"),
                  ("fixtures", "sanitary", "Sanitary ware"), ("fixtures", "lighting", "Light colour")]),
]


def rgb(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255


def texture(sw: dict, w: int = 260, h: int = 130, seed: int = 0) -> np.ndarray:
    """A swatch image: the base colour with an indicative pattern."""
    rng = np.random.default_rng(seed)
    base = rgb(sw["colour"])
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    t = np.ones((h, w))
    p = sw.get("pattern", "plain")
    if p == "stone":
        n = ndimage.gaussian_filter(rng.standard_normal((h, w)), 6)
        t = 1 + 0.06 * n / (np.abs(n).max() + 1e-9)
        t[(yy % 65) < 1] *= 0.9              # tile joints
        t[(xx % 130) < 1] *= 0.9
    elif p == "marble":
        n = ndimage.gaussian_filter(rng.standard_normal((h, w)), 12)
        n = n / (np.abs(n).max() + 1e-9)
        vein = np.abs(np.sin((xx * 0.03 + yy * 0.05) + 6 * n))
        t = 1 - 0.22 * np.clip(1 - vein * 8, 0, 1) - 0.03 * n
    elif p == "wood":
        n = ndimage.gaussian_filter(rng.standard_normal((h, w)), (1, 25))
        n = n / (np.abs(n).max() + 1e-9)
        grain = np.sin(yy * 0.45 + 3 * n)
        t = 1 + 0.07 * grain
        t[(yy % 26) < 1] *= 0.85            # plank joints
    elif p == "terrazzo":
        t = 1 + 0.02 * ndimage.gaussian_filter(rng.standard_normal((h, w)), 3)
        img = base * t[..., None]
        for _ in range(240):
            cx, cy, r = rng.integers(0, w), rng.integers(0, h), rng.uniform(1, 3.5)
            m = (xx - cx) ** 2 + (yy - cy) ** 2 < r * r
            img[m] = rng.choice([0.45, 0.7, 1.12]) * base
        return np.clip(img, 0, 1)
    elif p == "concrete":
        n = ndimage.gaussian_filter(rng.standard_normal((h, w)), 2) + \
            ndimage.gaussian_filter(rng.standard_normal((h, w)), 10) * 2
        t = 1 + 0.05 * n / (np.abs(n).max() + 1e-9)
    elif p == "metal":
        n = ndimage.gaussian_filter(rng.standard_normal((h, w)), (0.5, 30))
        t = 1 + 0.06 * n / (np.abs(n).max() + 1e-9) + 0.12 * (1 - yy / h) - 0.06
    return np.clip(base * t[..., None], 0, 1)


def vignette(ax, pal: dict) -> None:
    """A living room in elevation: floor, wall, feature wall, joinery, sofa."""
    f, wl, a, fx = pal["flooring"], pal["walls"], pal["accents"], pal["fixtures"]
    W, H = 10.0, 5.0
    ax.imshow(texture(wl["main"], 400, 200, 1), extent=(0, W, 1.0, H), aspect="auto")
    ax.imshow(texture(wl["ceiling"], 400, 20, 2), extent=(0, W, H - 0.25, H), aspect="auto")
    ax.imshow(texture(wl["feature"], 200, 160, 3), extent=(3.2, 7.4, 1.0, H - 0.25), aspect="auto")
    ax.imshow(texture(f["public"], 400, 60, 4), extent=(0, W, 0, 1.0), aspect="auto")
    # Low joinery under the feature wall, a TV above it.
    ax.imshow(texture(a["joinery"], 200, 30, 5), extent=(3.6, 7.0, 1.0, 1.55), aspect="auto")
    ax.add_patch(Rectangle((4.3, 2.3), 2.0, 1.15, facecolor="#1f1f1f", edgecolor="#6b6b6b", lw=0.8))
    # Sofa and cushions, side table, lamp.
    tx = rgb(a["textile"]["colour"])
    ax.add_patch(Rectangle((0.5, 0.9), 2.4, 0.55, facecolor=tx * 0.92, edgecolor="none"))
    ax.add_patch(Rectangle((0.5, 1.45), 2.4, 0.45, facecolor=tx, edgecolor="none"))
    ax.add_patch(Rectangle((0.7, 1.4), 0.45, 0.4, facecolor=a["highlight"]["colour"], edgecolor="none"))
    ax.add_patch(Rectangle((2.15, 1.4), 0.45, 0.4, facecolor=a["highlight"]["colour"], edgecolor="none"))
    ax.add_patch(Rectangle((8.0, 0.9), 0.9, 0.5, facecolor=a["joinery"]["colour"], edgecolor="none"))
    ax.add_patch(Rectangle((8.4, 1.4), 0.08, 1.2, facecolor=fx["metal"]["colour"], edgecolor="none"))
    ax.add_patch(Rectangle((8.05, 2.55), 0.8, 0.45, facecolor=fx["lighting"]["colour"], edgecolor="none"))
    # Pendant over the sofa, with a warm glow.
    ax.plot([1.7, 1.7], [H - 0.25, 3.5], color=fx["metal"]["colour"], lw=1.2)
    ax.add_patch(Circle((1.7, 3.3), 0.75, facecolor=fx["lighting"]["colour"], alpha=0.35, edgecolor="none"))
    ax.add_patch(Rectangle((1.35, 3.25), 0.7, 0.28, facecolor=fx["metal"]["colour"], edgecolor="none"))
    # Skirting shadow line.
    ax.plot([0, W], [1.0, 1.0], color="#00000033", lw=0.8)
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")


def main() -> int:
    spec = yaml.safe_load(PALETTES.read_text(encoding="utf-8"))
    pals = spec["palettes"]
    fig = plt.figure(figsize=(23.4, 16.5))
    fig.patch.set_facecolor("white")
    fig.text(0.02, 0.965, "INTERIOR PALETTES, THREE OPTIONS", fontsize=16, color=INK, fontweight="bold")
    fig.text(0.02, 0.948, "Villa 5130272, Saih Shuaib 1, Jebel Ali Hills. Proposed for the owner to "
             "choose from or adjust (answer P1). Each becomes a switchable option in the walkthrough.",
             fontsize=9, color=MUTED)

    col_w, x0 = 0.31, 0.02
    for c, pal in enumerate(pals):
        x = x0 + c * (col_w + 0.015)
        fig.text(x, 0.915, f"{c + 1}  {pal['name'].upper()}", fontsize=14, color=INK, fontweight="bold")
        y = 0.900
        for line in textwrap.wrap(" ".join(pal["idea"].split()), 95):
            fig.text(x, y, line, fontsize=8, color=MUTED, va="top")
            y -= 0.012
        vignette(fig.add_axes([x, 0.66, col_w, 0.19]), pal)
        y = 0.64
        for title, items in ROWS:
            fig.text(x, y, title, fontsize=8.5, color=INK, fontweight="bold", va="top")
            y -= 0.016
            for i, (grp, slot, label) in enumerate(items):
                sw = pal[grp][slot]
                ax = fig.add_axes([x, y - 0.024, 0.055, 0.024])
                ax.imshow(texture(sw, seed=hash((c, grp, slot)) % 1000), aspect="auto")
                ax.set_xticks([])
                ax.set_yticks([])
                for s in ax.spines.values():
                    s.set_color("#8c857a")
                    s.set_linewidth(0.5)
                fig.text(x + 0.060, y - 0.003, label, fontsize=7.5, color=INK, fontweight="bold", va="top")
                fig.text(x + 0.060, y - 0.0135, textwrap.shorten(sw["name"], 72), fontsize=7.2,
                         color=MUTED, va="top")
                y -= 0.029
            y -= 0.006

    notes = [
        "Palette 1 is the owner's white, black and beige direction, replacing Sand and Oak (P2 C, P3 C). "
        "All three sit with the facade as built (D-048, D-051).",
        "Colours and patterns are visual concept finishes, not a specification. Products, slip "
        "resistance in wet areas and fire ratings are for the interior designer and the consultant.",
        "In the walkthrough the palettes switch with one button; textures will come from free CC0 "
        "libraries such as Poly Haven, recorded in assets/LICENSES.md.",
        "Feature walls: the TV wall between the living room and the dining (12g) and the salon's "
        "main wall. Data: brief/palettes.yaml; sheet: src/drawings/sketch_palettes.py.",
    ]
    y = 0.055
    for n in notes:
        fig.text(0.02, y, "- " + n, fontsize=8, color=INK)
        y -= 0.013
    fig.text(0.975, 0.030, "CONCEPT DESIGN, NOT FOR CONSTRUCTION", fontsize=11, color=RED,
             ha="right", fontweight="bold")
    fig.text(0.975, 0.016, "Sketch VJH-SK-018   Interior palettes, answers P1 to P3   Rev B   A2 landscape",
             fontsize=7.5, color=MUTED, ha="right")
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, facecolor="white", dpi=200)
    fig.savefig(OUT_PNG, facecolor="white", dpi=110)
    plt.close(fig)
    print(f"PDF  {OUT_PDF.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
