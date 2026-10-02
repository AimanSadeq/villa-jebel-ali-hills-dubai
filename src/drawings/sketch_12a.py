"""Sketch for ground floor question 12a: the two ways to arrange the back.

Both options apply answer 12 (the salon takes the lawn court's place, the lawn
court is removed, the dining faces the backyard, the living room grows). They
differ only in the order of the rooms along the backyard. Every other room is
read unchanged from brief/reference_plan.yaml. This is a decision sketch, not
the model: nothing here is written back to the brief.

Plan turned so the road is on the left and the backyard on the right, carport
end (south) at the bottom. Frame metres as in brief/reference_plan.yaml.

Run: python src/drawings/sketch_12a.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402
from shapely.geometry import box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN = REPO_ROOT / "brief" / "reference_plan.yaml"
OUT_PDF = REPO_ROOT / "output" / "pdf" / "VJH-SK-012_Question_12a_Options.pdf"
OUT_PNG = REPO_ROOT / "output" / "pdf" / "VJH-SK-012_Question_12a_Options.png"

SQFT = 10.7639
T_EXT = 0.25

INK, MUTED, WALL = "#1a1a1a", "#6b6b6b", "#262626"
OPEN = "#fdf3dc"      # the open shared room (D-033)
SALON = "#e6eef7"
CHANGED = "#b3261e"
OTHER = "#f4f2ee"
CARPORT = "#ffffff"
FURN = "#8a6a3f"

# Rooms answer 12 changes; everything else is drawn as built.
REPLACED = {"show_kitchen", "family_sitting", "dining", "salon", "lawn_court"}

LABELS = {
    "garage": "Carport, 3 cars", "guest_bedroom": "Guest bed", "guest_toilet": "WC",
    "guest_dress": "Dress", "office_toilet": "WC", "home_office": "Office",
    "main_entrance": "Porch", "plant_room": "Plant", "outdoor_bathroom": "Out. bath",
    "service_lobby": "Serv. lobby", "entrance_foyer": "Foyer (double height)",
    "lift": "Lift", "maids_toilet": "WC", "wash": "Wash", "stair_hall": "Stair hall",
    "maids_room": "Maid", "guest_powder": "Powder", "stair_lift_ground": "Stair",
    "pantry": "Store", "laundry": "Laundry", "arabic_kitchen": "Arabic kitchen",
}


def _area(x0, x1, y0, y1):
    return (x1 - x0) * (y1 - y0)


def options(g: dict) -> dict:
    """The back strip, x along the road (south to north), y0..y1 its depth."""
    k, m, c = g["show_kitchen"], g["salon"], g["lawn_court"]
    y0, y1 = k["y0"], k["y1"]
    xk0, xk1, xend = k["x0"], k["x1"], m["x1"]
    salon = ("salon", "Salon", c["x0"], c["x1"], c["y0"], c["y1"])
    a_split = round(xk1 + 3.60, 2)
    b_split = round(xend - 6.00, 2)
    return {
        "A": {
            "title": "Option A (recommended): kitchen, dining, then a large living room",
            "rooms": [
                ("show_kitchen", "Island kitchen", xk0, xk1, y0, y1),
                ("dining", "Dining", xk1, a_split, y0, y1),
                ("living", "Living room", a_split, xend, y0, y1),
                salon,
            ],
            "notes": [
                "Dining sits next to the kitchen: short serving route.",
                "Living room takes the freed north corner (garden glass; north side faces the neighbour).",
                "Dining for 12 at 3.6 m wide: about 1.2 m from table edge to wall.",
            ],
        },
        "B": {
            "title": "Option B: kitchen, living room, then a large dining room in the corner",
            "rooms": [
                ("show_kitchen", "Island kitchen", xk0, xk1, y0, y1),
                ("living", "Living room", xk1, b_split, y0, y1),
                ("dining", "Dining", b_split, xend, y0, y1),
                salon,
            ],
            "notes": [
                "Dining room 6 x 6 m in the corner (garden glass; north side faces the neighbour).",
                "Living room smaller; food crosses the living room to reach the dining.",
                "Living room sits next to the kitchen.",
            ],
        },
    }


def _furniture(ax, key, x0, x1, y0, y1, opt):
    """Indicative furniture only, to judge the space. Plot coords: (y, x)."""
    w, d = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    kw = dict(fill=False, ec=FURN, lw=0.8, zorder=3)
    if key == "show_kitchen":
        ax.add_patch(Rectangle((y1 - 0.65, x0 + 0.3), 0.65, w - 0.6, **kw))   # counter
        ax.add_patch(Rectangle((cy - 0.5, cx - 1.2), 1.0, 2.4, **kw))         # island
    elif key == "dining":
        # Table for 12 (about 1.1 x 3.8 m), long side along the room's longer side.
        tl, tw = 3.8, 1.1
        if d >= w:  # long side across the depth (plot x)
            ax.add_patch(Rectangle((cy - tl / 2, cx - tw / 2), tl, tw, **kw))
            seats = [(cy - tl / 2 + 0.35 + i * 0.62, cx + s * (tw / 2 + 0.3))
                     for i in range(5) for s in (-1, 1)]
            seats += [(cy - tl / 2 - 0.3, cx), (cy + tl / 2 + 0.3, cx)]
        else:       # long side along the road (plot y)
            ax.add_patch(Rectangle((cy - tw / 2, cx - tl / 2), tw, tl, **kw))
            seats = [(cy + s * (tw / 2 + 0.3), cx - tl / 2 + 0.35 + i * 0.62)
                     for i in range(5) for s in (-1, 1)]
            seats += [(cy, cx - tl / 2 - 0.3), (cy, cx + tl / 2 + 0.3)]
        for sy, sx in seats:
            ax.add_patch(Circle((sy, sx), 0.2, **kw))
    elif key == "living":
        # L sofa facing the garden glass plus a second seat group if there is room.
        ax.add_patch(Rectangle((y0 + 1.0, x0 + 0.8), 0.9, 3.2, **kw))
        ax.add_patch(Rectangle((y0 + 1.0, x0 + 0.8), 3.0, 0.9, **kw))
        ax.add_patch(Rectangle((y0 + 2.4, x0 + 2.2), 1.2, 1.0, **kw))       # table
        if w >= 8.0:
            ax.add_patch(Rectangle((y0 + 1.0, x1 - 3.6), 0.9, 2.8, **kw))
            ax.add_patch(Rectangle((y0 + 3.6, x1 - 3.6), 0.9, 2.8, **kw))
    elif key == "salon":
        ax.add_patch(Rectangle((y0 + 0.4, x0 + 0.4), 0.8, w - 0.8, **kw))
        ax.add_patch(Rectangle((y1 - 1.2, x0 + 0.4), 0.8, w - 0.8, **kw))
        ax.add_patch(Rectangle((y0 + 1.2, x1 - 1.2), d - 2.4, 0.8, **kw))


def _label(ax, x0, x1, y0, y1, text, size=6.0, area=True, weight="normal", color=INK):
    a = _area(x0, x1, y0, y1)
    s = text + (f"\n{a:.1f} m² ({a * SQFT:,.0f} sq ft)" if area else "")
    ax.text((y0 + y1) / 2, (x0 + x1) / 2, s, ha="center", va="center", fontsize=size,
            color=color, weight=weight, zorder=6,
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.6))


def draw_option(ax, plan: dict, opt: dict, letter: str):
    g = {r["key"]: r for r in plan["ground"]}
    body = []
    for r in plan["ground"]:
        if r["key"] in REPLACED:
            continue
        x0, x1, y0, y1 = r["x0"], r["x1"], r["y0"], r["y1"]
        fc = CARPORT if r["kind"] in ("carport", "porch") else OTHER
        ls = "--" if r["kind"] in ("carport", "porch") else "-"
        ax.add_patch(Rectangle((y0, x0), y1 - y0, x1 - x0, fc=fc, ec=MUTED, lw=0.5, ls=ls))
        if r["kind"] in ("room", "circulation"):
            body.append(box(x0, y0, x1, y1))
        if r["key"] in LABELS:
            small = _area(x0, x1, y0, y1) < 9
            _label(ax, x0, x1, y0, y1, LABELS[r["key"]], size=4.6 if small else 5.4,
                   area=not small and r["kind"] != "carport", color=MUTED)

    for key, name, x0, x1, y0, y1 in opt["rooms"]:
        is_salon = key == "salon"
        ax.add_patch(Rectangle((y0, x0), y1 - y0, x1 - x0, fc=SALON if is_salon else OPEN,
                               ec=INK, lw=0.6, zorder=2))
        body.append(box(x0, y0, x1, y1))
        _furniture(ax, key, x0, x1, y0, y1, letter)
        _label(ax, x0, x1, y0, y1, name, size=7.2, weight="bold")

    # Open joins inside the back strip: dashed, no wall (D-033).
    strip = [r for r in opt["rooms"] if r[0] != "salon"]
    for a, b in zip(strip, strip[1:]):
        ax.plot([a[4], a[5]], [a[3], a[3]], ls=(0, (4, 3)), color=MUTED, lw=0.8, zorder=3)

    # Salon walls and its door from the foyer (answer 10: guests enter by the main door).
    s = [r for r in opt["rooms"] if r[0] == "salon"][0]
    ax.add_patch(Rectangle((s[4], s[2]), s[5] - s[4], s[3] - s[2], fill=False, ec=WALL,
                           lw=2.2, zorder=4))
    dy = (s[4] + s[5]) / 2
    ax.plot([dy - 0.8, dy + 0.8], [s[2], s[2]], color="white", lw=3.0, zorder=5)
    ax.text(dy, s[2] - 0.35, "double doors from foyer", ha="center", va="top",
            fontsize=4.6, color=CHANGED, zorder=6)

    # Exterior wall line around the body.
    outline = unary_union([b.buffer(0.13, join_style=2) for b in body]).buffer(
        -0.13 + T_EXT, join_style=2)
    polys = getattr(outline, "geoms", [outline])
    for p in polys:
        xs, ys = p.exterior.xy
        ax.plot(list(ys), list(xs), color=WALL, lw=2.6, zorder=4)

    # Garden glass along the back.
    k = g["show_kitchen"]
    yb = k["y1"] + T_EXT / 2
    ax.plot([yb, yb], [k["x0"] + 0.3, g["salon"]["x1"] - 0.3], color="#2a7fb8", lw=2.0, zorder=5)

    # Dimensions of the back strip.
    yd = k["y1"] + 1.1
    for key, name, x0, x1, y0, y1 in strip:
        ax.annotate("", xy=(yd, x0), xytext=(yd, x1),
                    arrowprops=dict(arrowstyle="<->", color=CHANGED, lw=0.7))
        ax.text(yd + 0.25, (x0 + x1) / 2, f"{x1 - x0:.2f} m", rotation=90, ha="left",
                va="center", fontsize=5.6, color=CHANGED)
    xn = g["salon"]["x1"] + T_EXT + 0.6
    ax.annotate("", xy=(k["y0"], xn), xytext=(k["y1"], xn),
                arrowprops=dict(arrowstyle="<->", color=CHANGED, lw=0.7))
    ax.text((k["y0"] + k["y1"]) / 2, xn + 0.2, "6.00 m deep", ha="center", va="bottom",
            fontsize=5.6, color=CHANGED)

    ax.text(-0.8, 13.5, "ROAD (side 1)", rotation=90, ha="center", va="center",
            fontsize=7, color=MUTED, weight="bold")
    ax.text(k["y1"] + 3.4, 13.5, "BACKYARD (about 9.2 m deep, no pool, D-041)",
            rotation=90, ha="center", va="center", fontsize=7, color="#2e7d4f", weight="bold")
    # North arrow (approximate, plan frame).
    ax.annotate("", xy=(-0.4, 27.4), xytext=(-0.4, 25.6),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))
    ax.text(-0.4, 27.7, "N", ha="center", va="bottom", fontsize=7, weight="bold")

    ax.set_title(opt["title"], fontsize=9.5, weight="bold", loc="left")
    ax.set_xlim(-1.6, 26.0)
    ax.set_ylim(-1.6, 28.6)
    ax.set_aspect("equal")
    ax.axis("off")


def plan_before_12() -> dict:
    """The plan before answer 12 was built (D-046)."""
    import sys  # noqa: PLC0415
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from model.assemble_reference import assemble  # noqa: PLC0415
    return assemble(answer_12=False)[0]


def main() -> int:
    plan = plan_before_12()
    g = {r["key"]: r for r in plan["ground"]}
    opts = options(g)

    fig = plt.figure(figsize=(16.5, 11.7))  # A3 landscape
    for i, letter in enumerate(("A", "B")):
        ax = fig.add_axes([0.02 + i * 0.49, 0.17, 0.47, 0.76])
        draw_option(ax, plan, opts[letter], letter)
        rooms = {r[0]: r for r in opts[letter]["rooms"]}
        lines = []
        for key in ("show_kitchen", "dining", "living", "salon"):
            _, name, x0, x1, y0, y1 = rooms[key]
            a = _area(x0, x1, y0, y1)
            lines.append(f"{name}: {x1 - x0:.2f} x {y1 - y0:.2f} m = {a:.1f} m² "
                         f"({a * SQFT:,.0f} sq ft)")
        txt = "\n".join(lines + [""] + ["• " + n for n in opts[letter]["notes"]])
        fig.text(0.04 + i * 0.49, 0.155, txt, ha="left", va="top", fontsize=8.2, color=INK,
                 linespacing=1.5)

    c = g["lawn_court"]
    ca = _area(c["x0"], c["x1"], c["y0"], c["y1"])
    fig.suptitle("Villa 5130272, ground floor, question 12a: arranging the back after answer 12",
                 x=0.02, ha="left", fontsize=13, weight="bold")
    fig.text(0.02, 0.935,
             f"Same in both: the salon takes the lawn court's place, "
             f"{ca:.1f} m² ({ca * SQFT:,.0f} sq ft), closed, entered from the foyer. "
             "Kitchen, dining and living form one open room along the backyard (D-033). "
             "GFA is the same for both options; enclosing the court is question 12b.",
             fontsize=8.5, color=MUTED)
    fig.text(0.98, 0.015, "CONCEPT DESIGN, NOT FOR CONSTRUCTION.  Decision sketch, "
             "indicative furniture, not to scale on screen.  Dimensions from "
             "brief/reference_plan.yaml.  VJH-SK-012", ha="right", fontsize=7.5, color=CHANGED)
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF)
    fig.savefig(OUT_PNG, dpi=130)
    print(f"Wrote {OUT_PDF.relative_to(REPO_ROOT)} and {OUT_PNG.name}")
    for letter, o in opts.items():
        for r in o["rooms"]:
            print(letter, r[0], f"{r[3] - r[2]:.2f} x {r[5] - r[4]:.2f} = "
                  f"{_area(r[2], r[3], r[4], r[5]):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
