"""Sketch of both floors with all of answer 12 applied (12, 12a to 12e).

Ground floor: kitchen, double height living room and dining along the backyard
(12a option B); the salon in the lawn court's place, fully open to the dining
(12c), lined up with the dining's north wall (12d) and 7.50 m across (12e). First floor: the void over the living room, the family room above the
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
from drawings.sketch_doors import draw_all, place, unreached  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from model.reference_plan import _outline  # noqa: E402

PLAN = REPO_ROOT / "brief" / "reference_plan.yaml"
MASSING = REPO_ROOT / "brief" / "massing.yaml"
OUT_PDF = REPO_ROOT / "output" / "pdf" / "VJH-SK-013_Answer_12_Both_Floors.pdf"
OUT_PNG = REPO_ROOT / "output" / "pdf" / "VJH-SK-013_Answer_12_Both_Floors.png"
OUT_PNG_DOORS = REPO_ROOT / "output" / "pdf" / "VJH-SK-013_Answer_12_Door_Schedule.png"

# Open joins answer 12 closes: 12m walls the Arabic kitchen from the passage.
OPEN_GROUND_CLOSED = {"arabic_kitchen_bay/service_passage"}

# Open joins after answer 12 (no door, no wall): the reference's, with the
# garden room renamed, plus the new open room and the salon (12c).
OPEN_GROUND_NEW = ["show_kitchen/living", "salon/dining", "salon/living", "entrance_foyer/salon",
                   "entrance_foyer/living"]

CAP = 662.99
TV_WALL_T = 0.15
KITCHEN_VOID_X0 = None   # set in main once 12l is applied
TV_W = 1.90          # an 85 inch screen is about 1.9 m wide
DOUBLE_HEIGHT = {"entrance_foyer", "living", "main_entrance"}
VOID = "#dfe9f2"
NEW = "#e8f3ea"
OTHER = "#f4f2ee"

G_LABELS = {
    "garage": "Carport, 3 cars", "guest_bedroom": "Guest bed", "guest_toilet": "WC",
    "guest_dress": "Dress", "office_toilet": "WC", "home_office": "Office",
    "main_entrance": "Porch", "plant_room": "Plant", "outdoor_bathroom": "Out. bath",
    "service_lobby": "Serv. lobby", "entrance_foyer": "Foyer (double height)",
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
    "family_living": "Family room", "void_over_living": "Void over kitchen and living\n(double height)",
}


def clear_heights(plan: dict) -> dict:
    """Indicative clear heights (floor finish to ceiling), from brief/massing.yaml
    (D-030) and the reference levels. Not regulatory values."""
    h = yaml.safe_load(MASSING.read_text(encoding="utf-8"))["heights"]
    hg, hf = float(h["ground_floor_m"]), float(h["first_floor_m"])
    slab, serv = float(h["slab_m"]), float(h["services_zone_m"])
    lv = plan["levels"]
    return {"ground": hg - slab - serv, "first": hf - slab - serv,
            "double": hg + hf - slab - serv,
            "carport": float(lv["carport_roof_m"]) - float(lv["carport_ffl_above_gate_m"]) - slab,
            "ff_ground": hg, "ff_first": hf}


def room_height(r: dict, floor: str, H: dict) -> float | None:
    if r["kind"] in ("void", "balcony", "terrace"):
        return None
    if r["kind"] == "carport":
        return H["carport"]
    if floor == "ground" and r["key"] in DOUBLE_HEIGHT:
        return H["double"]
    return H[floor]


def dims_text(x0, x1, y0, y1, h=None, small=False) -> str:
    """Width x length (shorter side first), area in m2 and sq ft, clear height."""
    w, l = sorted((x1 - x0, y1 - y0))
    a = w * l
    if small:
        return f"{w:.2f} x {l:.2f} m\n{a:.1f} m\u00b2"
    out = f"{w:.2f} x {l:.2f} m\n{a:.1f} m\u00b2 ({a * SQFT:,.0f} sq ft)"
    if h is not None:
        out += f"\nclear height {h:.2f} m"
    return out


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
    # (the old 0.25 m wall line between them becomes floor). 12e: the salon
    # takes 1.50 m more from the dining, so it is 7.50 m across and the dining
    # 3.75 m. The line is open (12c), so GFA does not change.
    sd_line = round(c["y0"] + 6.00 + 1.50, 3)
    ground += [
        _r("show_kitchen", "room", k["x0"], k["x1"], y0, y1, True),
        _r("living", "room", k["x1"], split_ld, y0, y1, True),
        # 12g A: a solid TV wall between the living room and the dining, 0.15 m,
        # taken from the dining as the D-042 wall was; the living keeps a
        # 2.25 m opening into the salon.
        _r("dining", "room", round(split_ld + TV_WALL_T, 3), m["x1"], sd_line, y1, True),
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


def apply_12l(first: list) -> tuple[list, frozenset]:
    """12l, option A of VJH-SK-014: the first floor pantry and linen store
    become void over the island kitchen."""
    pantry = next(r for r in first if r["key"] == "pantry_first")
    out = [dict(r) for r in first if r["key"] not in ("pantry_first", "linen_storage")]
    v = next(r for r in out if r["key"] == "void_over_living")
    v["x0"] = pantry["x0"]
    return out, frozenset({"pantry_first", "linen_storage"})


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


def _living_tv(ax, rooms, x0, x1, y0, y1):
    """The TV wall (12g) at the living room's north end, the TV on it and a
    sofa facing it. Plot coords: (y, x)."""
    d = next(r for r in rooms if r["key"] == "dining")
    wy0, wy1 = d["y0"], d["y1"]
    ax.add_patch(Rectangle((wy0, x1), wy1 - wy0, TV_WALL_T, fc=WALL, ec=WALL, zorder=6))
    ty = (wy0 + wy1) / 2
    ax.add_patch(Rectangle((ty - TV_W / 2, x1 - 0.12), TV_W, 0.08, fc="#333333", ec="none", zorder=6))
    ax.text(ty, x1 - 0.25, f"TV {TV_W:.1f} m wide\non a {wy1 - wy0:.2f} m wall", ha="center", va="top",
            fontsize=4.6, color=CHANGED, zorder=6)
    kw = dict(fill=False, ec="#8a6a3f", lw=0.8, zorder=3)
    view = 3.40                                   # screen to sofa front
    sx = x1 - view - 0.9
    ax.add_patch(Rectangle((ty - 1.6, sx), 3.2, 0.9, **kw))        # sofa facing the TV
    ax.add_patch(Rectangle((ty - 0.6, sx + 1.3), 1.2, 0.7, **kw))  # coffee table
    ax.add_patch(Rectangle((y1 - 1.1, sx + 1.0), 0.9, 1.9, **kw))  # side sofa, garden side
    ax.annotate("", xy=(ty - 1.9, x1 - 0.1), xytext=(ty - 1.9, x1 - view),
                arrowprops=dict(arrowstyle="<->", color=CHANGED, lw=0.6), zorder=6)
    ax.text(ty - 2.0, x1 - view / 2, f"viewing {view:.2f} m", fontsize=4.6, color=CHANGED,
            va="center", ha="right", rotation=90, zorder=6)
    s = next(r for r in rooms if r["key"] == "salon")
    ax.text((y0 + s["y1"]) / 2, x1 - 0.25, f"{s['y1'] - y0:.2f} m open\nto the salon", ha="center",
            va="top", fontsize=4.6, color=CHANGED, zorder=6)


def _draw_floor(ax, rooms, outline, labels, title, floor, H):
    for r in rooms:
        x0, x1, y0, y1, kind = r["x0"], r["x1"], r["y0"], r["y1"], r["kind"]
        new = r.get("new", False)
        if kind == "void":
            fc, ls = VOID, "--"
        elif kind in ("carport", "porch", "balcony", "terrace"):
            fc, ls = "#ffffff", "--"
        elif r["key"] == "salon":
            fc, ls = SALON, (0, (4, 3))  # 12c and 12h: open to the dining and the foyer
        elif new and r["key"] in ("show_kitchen", "living", "dining"):
            fc, ls = OPEN, (0, (4, 3))  # one open room: no walls between (D-033)
        elif new:
            fc, ls = NEW, "-"
        else:
            fc, ls = OTHER, "-"
        ax.add_patch(Rectangle((y0, x0), y1 - y0, x1 - x0, fc=fc, ec=INK if new else MUTED,
                               lw=0.7 if new else 0.5, ls=ls, zorder=2 if new else 1))
        if floor == "ground" and r["key"] in ("show_kitchen", "dining", "salon"):
            _furniture(ax, r["key"], x0, x1, y0, y1, "B")
        if floor == "ground" and r["key"] == "living":
            _living_tv(ax, rooms, x0, x1, y0, y1)
        a = (x1 - x0) * (y1 - y0)
        name = {"show_kitchen": "Island kitchen", "living": "Living room (double height)",
                "dining": "Dining", "salon": "Salon (majlis)"}.get(r["key"], labels.get(r["key"]))
        if not name:
            continue
        name = name.replace("\n", " ")
        small = a < 9
        big = new and kind != "void" and not small
        h = room_height(r, floor, H)
        txt = name + "\n" + dims_text(x0, x1, y0, y1, h, small=small)
        if floor == "ground" and r["key"] == "show_kitchen" and KITCHEN_VOID_X0 is not None:
            # 12l: the void runs over the kitchen from KITCHEN_VOID_X0 north.
            low = KITCHEN_VOID_X0 - x0
            txt = txt.replace(f"clear height {h:.2f} m",
                              f"clear height {H['double']:.2f} m over most;\n{h:.2f} m under the gallery\nand the south {low:.2f} m")
        lx = x0 + 1.4 if (floor == "ground" and r["key"] == "living") else (x0 + x1) / 2
        ax.text((y0 + y1) / 2, lx, txt, ha="center", va="center",
                fontsize=6.2 if big else (3.6 if small else 4.5),
                color=INK if big else MUTED, weight="bold" if big else "normal", zorder=6,
                linespacing=1.25, bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.5))

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


NAMES = {"show_kitchen": "Island kitchen", "living": "Living room", "dining": "Dining",
         "salon": "Salon (majlis)", "outside": "outside", "family_living": "Family room",
         "corridor_first": "Gallery / corridor", "pantry": "Store",
         "service_steps": "Service steps", "service_passage": "Service passage",
         "guest_dress": "Guest dress", "guest_toilet": "Guest WC", "office_toilet": "Office WC",
         "maids_room": "Maid's room", "maids_toilet": "Maid's WC", "guest_powder": "Powder room",
         "outdoor_bathroom": "Outdoor bathroom", "plant_room": "Plant room",
         "bedroom_2_dress": "Bedroom 2 dress", "bedroom_2_toilet": "Bedroom 2 WC",
         "bedroom_3_dress": "Bedroom 3 dress", "bedroom_3_toilet": "Bedroom 3 WC",
         "bedroom_4_dress": "Bedroom 4 dress", "bedroom_4_toilet": "Bedroom 4 WC",
         "lift": "Lift", "lift_first": "Lift", "lift_lobby": "Lift lobby", "service_lobby": "Service lobby",
         "guest_bedroom": "Guest bedroom", "home_office": "Office", "entrance_foyer": "Foyer"}


def _name(k):
    n = NAMES.get(k) or G_LABELS.get(k) or F_LABELS.get(k) or k
    return n.replace("\n", " ").replace(" (double height)", "")


def door_schedule(doors: list[dict], rooms: list[dict]):
    kind_txt = {"single": "single leaf", "double": "double leaf", "sliding": "sliding glass",
                "open": "opening, no leaf", "lift": "lift door", "pivot": "pivot, glass above"}
    fig = plt.figure(figsize=(16.5, 11.7))
    fig.suptitle("Villa 5130272, answer 12: door schedule for sketch VJH-SK-013",
                 x=0.01, ha="left", fontsize=13, weight="bold")
    fig.text(0.01, 0.94, "Width x height in metres, indicative. Numbers match the tags on the plans. "
             "Source says where each door comes from; ASSUMED and TO DECIDE items need your answer.",
             fontsize=8.5, color=MUTED)
    rows = []
    for d in doors:
        wh = f"{d['w']:.2f} x {d['h']:.2f}" if d["h"] else f"{d['w']:.2f} wide"
        rows.append([d["no"], f"{_name(d['a'])}  to  {_name(d['b'])}", kind_txt[d["kind"]], wh, d["src"]])
    ax = fig.add_axes([0.01, 0.06, 0.96, 0.86])
    ax.axis("off")
    t = ax.table(cellText=rows, colLabels=["No.", "Between", "Type", "W x H (m)", "Source"],
                 colWidths=[0.04, 0.24, 0.11, 0.08, 0.50], loc="upper left", cellLoc="left")
    t.auto_set_font_size(False)
    t.set_fontsize(7.6)
    t.scale(1, 1.32)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor("#cfcac2")
        if r == 0:
            cell.set_facecolor("#ece8e1")
            cell.set_text_props(weight="bold")
        elif "ASSUMED" in rows[r - 1][4] or "TO DECIDE" in rows[r - 1][4]:
            cell.set_facecolor("#fbe3d6")
    fig.text(0.98, 0.012, "CONCEPT DESIGN, NOT FOR CONSTRUCTION.  VJH-SK-013, page 2",
             ha="right", fontsize=7.5, color=CHANGED)
    return fig


def main() -> int:
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    ground, first, notes = apply_answer_12(plan)
    untrimmed = measure(ground, first)
    first, removed_f = apply_12l(first)
    global KITCHEN_VOID_X0
    KITCHEN_VOID_X0 = next(r for r in first if r["key"] == "void_over_living")["x0"]
    notes = [n for n in notes if not n.startswith(("Pantry", "Linen"))]
    notes.append("12l: the first floor pantry and linen store become void over the island kitchen "
                 f"(VJH-SK-014 option A); before this trim {untrimmed['total']:.2f} m\u00b2.")
    H = clear_heights(plan)
    before = measure([dict(r) for r in plan["ground"]], [dict(r) for r in plan["first"]])
    after = measure(ground, first)

    fig = plt.figure(figsize=(16.5, 11.7))  # A3 landscape
    ax_g = fig.add_axes([0.01, 0.20, 0.48, 0.70])
    ax_f = fig.add_axes([0.50, 0.20, 0.48, 0.70])
    _draw_floor(ax_g, ground, after["g_poly"], G_LABELS,
                f"GROUND FLOOR   clear height {H['ground']:.2f} m, double height {H['double']:.2f} m", "ground", H)
    _draw_floor(ax_f, first, after["f_poly"], F_LABELS,
                f"FIRST FLOOR   clear height {H['first']:.2f} m   (placeholder except the coloured rooms)",
                "first", H)

    # Ground: the salon is open to the dining (12c): no wall drawn between them.
    s = next(r for r in ground if r["key"] == "salon")
    ax_g.plot([s["y1"], s["y1"]], [s["x0"], s["x1"]], color="white", lw=2.0, zorder=5)
    ax_g.plot([s["y1"], s["y1"]], [s["x0"], s["x1"]], color=MUTED, lw=0.8, ls=(0, (4, 3)), zorder=5)
    ax_g.text(s["y1"] - 0.15, s["x0"] + 0.6, "open to dining (12c)\nand foyer (12h)", ha="right", va="bottom",
              fontsize=4.6, color=CHANGED, zorder=6)
    fam = next(r for r in first if r["key"] == "family_living")

    # Doors, and a check that every room can be reached through them.
    doors_g, doors_f = place(ground, "ground"), place(first, "first", removed_f)
    draw_all(ax_g, doors_g)
    draw_all(ax_f, doors_f)
    old_names = {"family_sitting": "living"}
    joins_g = {frozenset(old_names.get(k, k) for k in j.split("/"))
               for j in plan["open_joins"]["ground"] if j not in OPEN_GROUND_CLOSED} | {
        frozenset(j.split("/")) for j in OPEN_GROUND_NEW}
    # 12m: the Arabic kitchen is walled from the service passage.
    bay = next(r for r in ground if r["key"] == "arabic_kitchen_bay")
    psg = next(r for r in ground if r["key"] == "service_passage")
    ax_g.add_patch(Rectangle((psg["y1"], bay["x0"]), bay["y0"] - psg["y1"], bay["x1"] - bay["x0"],
                             fc=WALL, ec=WALL, zorder=6))
    joins_f = {frozenset(j.split("/")) for j in plan["open_joins"]["first"]
               if not (set(j.split("/")) & removed_f)}
    outside = {d["a"] for d in doors_g if d["b"] == "outside"}
    lost_g = [k for k in unreached([r for r in ground if r["kind"] in ("room", "circulation")],
                                   doors_g, joins_g, "entrance_foyer") if k not in outside]
    lost_f = unreached([r for r in first if r["kind"] in ("room", "circulation")],
                       doors_f, joins_f, "stair_lift_first")
    if lost_g or lost_f:
        raise ValueError(f"rooms with no way in: ground {lost_g}, first {lost_f}")

    over = after["total"] - CAP
    verdict = (f"{over:.2f} m² ({over * SQFT:,.0f} sq ft) OVER the cap"
               if over > 0 else f"{-over:.2f} m² inside the cap")
    lines = [
        "GFA, measured the way the build measures it (carport, balconies, terraces outside, D-039, TO VERIFY):",
        f"   Today (built, commit 6322806):  ground {before['ground']:.2f} + first {before['first']:.2f} "
        f"= {before['total']:.2f} m²",
        f"   With answer 12:                 ground {after['ground']:.2f} + first {after['first']:.2f} "
        f"= {after['total']:.2f} m² ({after['total'] * SQFT:,.0f} sq ft): {verdict} of {CAP} m²",
        "",
        "Family room above the salon: "
        + dims_text(fam["x0"], fam["x1"], fam["y0"], fam["y1"], H["first"]).replace("\n", ", ") + "; "
        "the brief's target is 35 m².",
        "The gallery (corridor) along the void stays the route from the stair to bedroom 4; "
        "the kitchen and living room are double height beyond it.",
    ] + notes
    lines += ["",
              f"Heights (indicative, brief/massing.yaml, D-030): ground floor {H['ff_ground']:.2f} m floor to floor, "
              f"{H['ground']:.2f} m clear; first floor {H['ff_first']:.2f} m floor to floor, {H['first']:.2f} m clear;",
              f"double height (foyer, porch, living room, most of the island kitchen) {H['double']:.2f} m clear; carport {H['carport']:.2f} m clear. "
              "Clear = floor to floor less 0.30 m slab and 0.15 m ceiling services zone."]
    fig.text(0.03, 0.185, "\n".join(lines), ha="left", va="top", fontsize=7.6, color=INK,
             linespacing=1.45, family="DejaVu Sans Mono")

    fig.suptitle("Villa 5130272, answer 12 on both floors: for review before the build",
                 x=0.01, ha="left", fontsize=13, weight="bold")
    fig.text(0.01, 0.94, "Coloured rooms change with answer 12; grey rooms are as built. "
             "The first floor is still the reference's placeholder, to be designed floor by floor (D-038).",
             fontsize=8.5, color=MUTED)
    fig.text(0.98, 0.012, "CONCEPT DESIGN, NOT FOR CONSTRUCTION.  Decision sketch, indicative "
             "furniture.  Dimensions from brief/reference_plan.yaml.  VJH-SK-013",
             ha="right", fontsize=7.5, color=CHANGED)
    sched = door_schedule(doors_g + doors_f, ground + first)
    with PdfPages(OUT_PDF) as pdf:
        pdf.savefig(fig)
        pdf.savefig(sched)
    fig.savefig(OUT_PNG, dpi=130)
    sched.savefig(OUT_PNG_DOORS, dpi=130)
    print(f"Wrote {OUT_PDF.relative_to(REPO_ROOT)} and {OUT_PNG.name}")
    print(f"GFA before {before['total']:.2f}, after {after['total']:.2f} "
          f"(ground {after['ground']:.2f}, first {after['first']:.2f}, voids {after['voids']:.2f}); {verdict}")
    for line in notes:
        print("  " + line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
