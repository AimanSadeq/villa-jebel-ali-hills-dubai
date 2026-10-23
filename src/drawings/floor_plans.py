"""Ground and first floor plans for Villa 5130272, drawn from brief/layouts.yaml.

A1 landscape, both floors side by side at a true 1:100, plot up, so the entrance
side reads on the left and the courtyard on the right as in the Phase 1 sheets.

Every area on this sheet is measured from the generated geometry. The GFA table
is the measured figure, and any room that came out larger than its brief target
because it had to hold up the floor above is labelled as padding rather than
hidden.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from shapely.geometry import box  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from drawings.massing_sheets import GRID_BEARING, _g, _side_badge  # noqa: E402
from drawings.sketch_doors import draw_door  # noqa: E402
from model.heights import clear_heights, room_height_text  # noqa: E402
from model.massing import load_massing  # noqa: E402
from model.interiors import plan as plan_interiors  # noqa: E402
from model.site import SQM_TO_SQFT, buildable_envelope, plot_polygon, sides  # noqa: E402

LAYOUTS = REPO_ROOT / "brief" / "layouts.yaml"
PROGRAM = REPO_ROOT / "brief" / "program.yaml"
OUT = REPO_ROOT / "output" / "pdf" / "VJH-GA-001_Floor_Plans.pdf"

MM = 1 / 25.4
A1 = (841 * MM, 594 * MM)
SCALE = 100

INK = "#1a1a1a"
MUTED = "#6b6b6b"
WALL = "#262626"
BATH = "#e4ecf2"
DOOR = "#8a6a3f"
ROOM = "#f7f5f1"
SERVICE = "#eeebe5"
STAFF = "#e9e6f0"
PAD = "#fbe3d6"
CORR = "#ffffff"
VOID = "#dfe9f2"
POOL = "#2a7fb8"
DECK = "#ded3bd"
PLOT = "#b3261e"
ENV = "#b8860b"
GOOD = "#2e7d4f"
BAD = "#b3261e"
DIM = "#1f6f8b"

SERVICE_KEYS = {"arabic_kitchen", "pantry", "laundry", "plant_room", "garage", "wash",
                "guest_toilet", "office_toilet", "maids_toilet", "powder_toilet", "lift",
                "lift_first", "pantry_first", "master_toilet", "bedroom_2_toilet",
                "bedroom_3_toilet", "bedroom_4_toilet",
                "outdoor_bathroom",
                "stair_lift_ground", "stair_lift_first", "linen_storage",
                "guest_powder"}
STAFF_KEYS = {"maids_room", "drivers_room"}
STAIR_KEYS = {"stair_lift_ground", "stair_lift_first"}

SHORT = {
    "entrance_foyer": "FOYER", "guest_bedroom": "GUEST BED", "salon": "SALON",
    "guest_powder": "WC", "dining": "DINING", "show_kitchen": "KITCHEN",
    "arabic_kitchen": "ARABIC KIT", "pantry": "PANTRY", "laundry": "LAUNDRY",
    "home_office": "OFFICE", "maids_room": "MAID", "drivers_room": "DRIVER",
    "plant_room": "PLANT", "stair_lift_ground": "STAIR + LIFT",
    "stair_lift_first": "STAIR + LIFT", "garage": "CARPORT, 3 CARS",
    "living": "LIVING", "master_suite": "MASTER SUITE", "bedroom_2": "BED 2",
    "bedroom_3": "BED 3", "bedroom_4": "BED 4", "family_living": "FAMILY",
    "linen_storage": "LINEN",
    "outdoor_bathroom": "OUTDOOR WC + SHOWER\nexternal door",
    "lawn_court": "LAWN COURT\nopen to the sky", "wash": "WASH", "lift": "LIFT",
    "main_entrance": "MAIN\nENTRANCE", "guest_dress": "DRESS", "guest_toilet": "WC",
    "office_toilet": "WC", "maids_toilet": "WC", "powder_toilet": "WC",
    "master_dress": "DRESS", "master_toilet": "BATH", "bedroom_2_dress": "DRESS",
    "bedroom_2_toilet": "BATH", "bedroom_3_dress": "DRESS", "bedroom_3_toilet": "BATH",
    "bedroom_4_dress": "DRESS", "bedroom_4_toilet": "BATH", "pantry_first": "PANTRY",
    "lift_first": "LIFT", "family_sitting": "FAMILY\nSITTING",
    "show_kitchen": "ISLAND KITCHEN", "arabic_kitchen": "ARABIC KITCHEN",
    "family_living": "FAMILY ROOM", "arabic_kitchen_bay": "ARABIC KIT.", "laundry_bay": "LAUNDRY",
    "courtyard": "COURTYARD\nopen to the sky", "workspace": "WORKSPACE", "plant_room": "PLANT",
    "garage": "CARPORT, 2 CARS",
}
CIRC_NAMES = {"corridor": "GALLERY", "corridor_first": "CORRIDOR", "gallery": "GALLERY",
              "gallery_west": "GALLERY", "hall": "HALL, STAIR", "service_corridor": "SERVICE",
              "salon_lobby": "LOBBY", "guest_lobby": "LOBBY", "north_lobby": "LOBBY",
              "stair_hall": "STAIR HALL", "service_lobby": "SERVICE LOBBY",
              "service_steps": "STEPS", "service_passage": "PASSAGE", "landing": "LANDING",
              "lift_lobby": "LIFT LOBBY"}
VOID_NAMES = {"void_over_foyer": "VOID OVER FOYER", "void_over_entrance": "VOID OVER PORCH",
              "void_over_courtyard": "COURTYARD\nopen to the sky",
              "void_over_living": "VOID OVER LIVING\nAND KITCHEN"}


def _interiors(ax, interiors, storey):
    """En-suites, wardrobes and the master suite plan (D-034, D-035)."""
    for it in interiors.values():
        if it.storey != storey:
            continue
        for g in it.partitions:
            for poly in ([g] if g.geom_type == "Polygon" else list(g.geoms)):
                xs, ys = poly.exterior.xy
                _poly(ax, list(zip(xs, ys)), facecolor=WALL, edgecolor="none", zorder=6)
        for part in it.parts:
            b = part.poly.bounds
            w, l = b[2] - b[0], b[3] - b[1]
            if part.kind == "space":
                # Above the partitions: a sub-room enclosed on all sides is a
                # hole in the partition polygon, which _poly cannot draw.
                _poly(ax, list(part.poly.exterior.coords), facecolor=BATH,
                      edgecolor=WALL, lw=0.4, zorder=6.5)
                short = ("BATH" if "bathroom" in part.key or "shower" in part.name.lower()
                         else "WIR HERS" if "hers" in part.key else "WIR HIS")
                ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2,
                        f"{short}\n{part.poly.area:.1f} m2", ha="center", va="center",
                        fontsize=4.2, color=MUTED, zorder=7, rotation=90 if l > 1.6 * w else 0)
            else:
                _poly(ax, list(part.poly.exterior.coords), facecolor="none",
                      edgecolor=MUTED, lw=0.4, hatch="////", zorder=5)
                ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2,
                        "WR" if part.kind == "wardrobe" else "COFFEE",
                        ha="center", va="center", fontsize=3.8, color=MUTED, zorder=7,
                        rotation=90 if l > w else 0)
        for d in [it.entry] + it.doors if it.entry else it.doors:
            half = d.width / 2
            if d.along_u:
                ax.plot([d.u - half, d.u + half], [d.v, d.v], color=DOOR, lw=1.4, zorder=8)
            else:
                ax.plot([d.u, d.u], [d.v - half, d.v + half], color=DOOR, lw=1.4, zorder=8)


def _open_joins(ax, lay, storey):
    """Open joins (D-033, D-046) have no wall: fill the gap between the two
    rooms as floor and mark the edge with a dashed line, so it does not read
    as a partition."""
    floor = lay["floors"][storey]
    by = {r["key"]: r for r in floor["rooms"] + floor["circulation"]}
    for j in (lay.get("open_joins") or {}).get(storey, []):
        a, b = (by.get(k) for k in j.split("/"))
        if not a or not b:
            continue
        for ax_i, other in ((0, 1), (1, 0)):          # 0: u, 1: v
            ka, ko = ("u", "v")[ax_i], ("u", "v")[other]
            for p_, q_ in ((a, b), (b, a)):
                gap = q_[ka][0] - p_[ka][1]
                if not (-1e-6 <= gap <= 0.35):
                    continue
                lo, hi = max(a[ko][0], b[ko][0]), min(a[ko][1], b[ko][1])
                if hi - lo < 0.3:
                    continue
                # Grown by 0.05 m so the solid room outlines either side are
                # covered too: two open rooms that touch (the salon and the
                # dining) must not show a line that reads as a wall.
                g0, g1 = p_[ka][1] - 0.05, q_[ka][0] + 0.05
                lo, hi = lo + 0.02, hi - 0.02
                if ka == "u":
                    rect = Rectangle((g0, lo), g1 - g0, hi - lo)
                    line = ([(g0 + g1) / 2] * 2, [lo, hi])
                else:
                    rect = Rectangle((lo, g0), hi - lo, g1 - g0)
                    line = ([lo, hi], [(g0 + g1) / 2] * 2)
                rect.set(facecolor=ROOM, edgecolor="none", zorder=4.5)
                ax.add_patch(rect)
                ax.plot(*line, color=MUTED, lw=0.5, ls=(0, (4, 3)), zorder=4.6)


def _doors(ax, doors, storey, joins=()):
    """The door schedule (src/model/doors.py) as resolved by the layout, with
    swings and the schedule numbers. Openings that are open joins are drawn by
    _open_joins; only their number is shown."""
    joins = {frozenset(j.split("/")) for j in joins}
    for d in doors:
        if d["storey"] != storey:
            continue
        if d["kind"] == "open" and frozenset((d["a"], d["b"])) in joins:
            ax.text(d["u"], d["v"], d["no"], fontsize=4.6, color="white", ha="center",
                    va="center", weight="bold", zorder=9,
                    bbox=dict(boxstyle="round,pad=0.18", fc=BAD, ec="none"))
            continue
        t = d["wall_t"]
        if d["along_u"]:      # the door spans u in a wall across v
            draw_door(ax, "x", d["v"] - t / 2, d["v"] + t / 2, d["u"], d["width_m"],
                      d["kind"], d["swing"], d["no"])
        else:
            draw_door(ax, "y", d["u"] - t / 2, d["u"] + t / 2, d["v"], d["width_m"],
                      d["kind"], d["swing"], d["no"])


def load() -> tuple[dict, dict]:
    lay = yaml.safe_load(LAYOUTS.read_text(encoding="utf-8"))
    prog = yaml.safe_load(PROGRAM.read_text(encoding="utf-8"))
    targets = {}
    for floor in ("ground", "first"):
        for r in prog.get(floor, []) or []:
            targets[r["key"]] = r.get("target_m2") or r.get("target_min_m2")
    if "garage" not in targets or targets["garage"] is None:
        targets["garage"] = 31.3      # the generated plans' internal garage
    return lay, targets


def _poly(ax, coords, **kw):
    ax.add_patch(MplPolygon(coords, closed=True, **kw))


def _rect(ax, r, **kw):
    (u0, u1), (v0, v1) = r["u"], r["v"]
    ax.add_patch(Rectangle((u0, v0), u1 - u0, v1 - v0, **kw))


def _context(ax):
    xs, ys = _g(plot_polygon()).exterior.xy
    _poly(ax, list(zip(xs, ys)), facecolor="#fbfaf7", edgecolor="none", zorder=0)
    xs, ys = _g(buildable_envelope()).exterior.xy
    ax.plot(xs, ys, color=ENV, lw=0.6, ls=(0, (6, 3)), zorder=1)
    xs, ys = _g(plot_polygon()).exterior.xy
    ax.plot(xs, ys, color=PLOT, lw=1.3, zorder=1)


def _badges(ax):
    """Compact side labels just outside the plot, so nothing clips at 1:100."""
    spots = {1: (-1.6, 17.0, 90), 3: (32.4, 17.0, -90), 2: (15.3, -1.7, 0),
             4: (15.3, 35.3, 0)}
    for s in sides():
        x, y, rot = spots[s.id]
        role = ("ENTRANCE" if s.is_main_access else
                "COURTYARD SIDE" if s.id == 3 else "NEIGHBOUR")
        col = GOOD if s.id in (1, 3) else MUTED
        ax.text(x, y, f"SIDE {s.id}  {role}  {s.adjacency}", rotation=rot,
                ha="center", va="center", fontsize=6.4, color=col, zorder=9,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=col, lw=0.6))


def _room(ax, r, targets, padding_keys, centre=None, height=""):
    key = r["key"]
    fill = (PAD if key in padding_keys else
            STAFF if key in STAFF_KEYS else
            SERVICE if key in SERVICE_KEYS else ROOM)
    _rect(ax, r, facecolor=fill, edgecolor=WALL, lw=0.7, zorder=4)
    (u0, u1), (v0, v1) = r["u"], r["v"]
    w, l = u1 - u0, v1 - v0
    cx, cy = centre or ((u0 + u1) / 2, (v0 + v1) / 2)
    if key in STAIR_KEYS:
        n = max(int(l / 0.28), 4)
        for i in range(1, n):
            y = v0 + i * l / n
            ax.plot([u0 + 0.15, u0 + w * 0.55], [y, y], color=MUTED, lw=0.3, zorder=5)
        ax.add_patch(Rectangle((u0 + w * 0.62, v0 + 0.2), w * 0.32, min(1.6, l - 0.4),
                               facecolor="none", edgecolor=MUTED, lw=0.5, zorder=5))
    small = min(w, l) < 2.2
    fs = 4.6 if small else 5.6
    rot = 90 if (w < l and w < 2.4) else 0
    tgt = targets.get(key, r["area_m2"])
    # CLAUDE.md rule 9 (D-045): width x length, area in m2 and sq ft, height.
    lines = [SHORT.get(key, key.upper())]
    lines.append(f"{min(w, l):.2f} x {max(w, l):.2f} m")
    if small:
        lines.append(f"{r['area_m2']:.1f} m2")
        lines.append(f"({r['area_m2'] * SQM_TO_SQFT:,.0f} sq ft)")
        fs = 4.0
    else:
        lines.append(f"{r['area_m2']:.1f} m2 ({r['area_m2'] * SQM_TO_SQFT:,.0f} sq ft)")
    if height:
        lines.append(height.replace(" under the void, ", "\nunder void, ") if not small else
                     height.split(" under")[0])
    if key in padding_keys:
        lines.append(f"brief {tgt:.0f}, +{r['area_m2'] - tgt:.1f}")
    ax.text(cx, cy, "\n".join(lines), ha="center", va="center", fontsize=fs,
            color=BAD if key in padding_keys else INK, zorder=7, rotation=rot,
            linespacing=1.25)


def _circulation(ax, items):
    for r in items:
        _rect(ax, r, facecolor=CORR, edgecolor=WALL, lw=0.5, hatch="....",
              zorder=3)
        (u0, u1), (v0, v1) = r["u"], r["v"]
        w, l = u1 - u0, v1 - v0
        a = w * l
        ax.text((u0 + u1) / 2, (v0 + v1) / 2,
                f"{CIRC_NAMES.get(r['key'], r['key'].upper())} "
                f"{min(w, l):.2f} x {max(w, l):.2f} m, {a:.1f} m2 ({a * SQM_TO_SQFT:,.0f} sq ft)",
                ha="center", va="center", fontsize=4.0, color=MUTED,
                rotation=90 if l > w else 0, zorder=7)


def _outline(ax, coords, lw=2.2):
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    ax.plot(xs, ys, color=WALL, lw=lw, solid_joinstyle="miter", zorder=8)


def _facade_cuts(ax, coords):
    """Gaps where the facade removes the first floor wall over its full height
    (brief/facade.yaml cuts, answer R4): the porch opens to the road."""
    from shapely.geometry import LineString  # noqa: PLC0415

    from model.facade import load as load_facade  # noqa: PLC0415
    ring = LineString(coords)
    for c in load_facade().get("cuts", []) or []:
        if not (c["z"][0] <= 5.0 and c["z"][1] >= 8.7):
            continue
        gap = ring.intersection(box(c["u"][0], c["v"][0], c["u"][1], c["v"][1]))
        for g in getattr(gap, "geoms", [gap]):
            if g.is_empty or g.length < 0.1:
                continue
            xs, ys = g.xy
            ax.plot(xs, ys, color="white", lw=3.2, zorder=9, solid_capstyle="butt")
            ax.plot(xs, ys, color=WALL, lw=0.5, ls=(0, (4, 3)), zorder=9)
            ax.text(min(xs) - 0.35, sum(ys) / len(ys), "open to the road (R4)", rotation=90,
                    ha="center", va="center", fontsize=4.5, color=MUTED, zorder=9)


def _rect_outline(ax, plate, lw=2.2):
    (u0, u1), (v0, v1) = plate["u"], plate["v"]
    _outline(ax, [(u0, v0), (u1, v0), (u1, v1), (u0, v1), (u0, v0)], lw)


def _pool(ax, road_east, lay=None):
    prog = yaml.safe_load(PROGRAM.read_text(encoding="utf-8"))
    if any(r["key"] == "pool" for r in prog.get("removed", []) or []) and not (lay and lay.get("pool")):
        return False      # no pool, owner decision D-041
    spec = (lay if lay and lay.get("pool") else
            next(o for o in load_massing()["options"] if o["key"] == "C"))
    clash = spec["deck"]["u"][0] < road_east
    for part, fill, edge in (("deck", DECK, "#b8a888"), ("pool", POOL, "#1b5f8c")):
        (u0, u1), (v0, v1) = spec[part]["u"], spec[part]["v"]
        ax.add_patch(Rectangle((u0, v0), u1 - u0, v1 - v0, facecolor=fill,
                               edgecolor=edge, lw=0.6, zorder=2))
    (u0, u1), (v0, v1) = spec["pool"]["u"], spec["pool"]["v"]
    ax.text((u0 + u1) / 2, (v0 + v1) / 2, "POOL\n10 x 4", ha="center",
            va="center", fontsize=5.4, color="white", zorder=3)
    return clash


def _north(ax, x, y, size=2.4):
    import numpy as np
    a = np.radians(GRID_BEARING)
    dx, dy = -np.sin(a), np.cos(a)
    ax.annotate("", xy=(x + dx * size, y + dy * size),
                xytext=(x - dx * size * 0.4, y - dy * size * 0.4),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))
    ax.text(x + dx * (size + 1.2), y + dy * (size + 1.2), "N", ha="center",
            va="center", fontsize=7, color=INK)


def plan_axes(fig, left_mm, bottom_mm, w_mm, h_mm):
    ax = fig.add_axes([left_mm / 841, bottom_mm / 594, w_mm / 841, h_mm / 594])
    # True 1:100: 1 m of model space is 10 mm on the sheet.
    span_u, span_v = w_mm / 1000 * SCALE, h_mm / 1000 * SCALE
    cu, cv = 15.3, 16.6
    ax.set_xlim(cu - span_u / 2, cu + span_u / 2)
    ax.set_ylim(cv - span_v / 2, cv + span_v / 2)
    ax.set_aspect("equal")
    ax.axis("off")
    return ax


def build() -> Path:
    lay, targets = load()
    pad_keys = {p["key"] for p in lay.get("padding", [])}
    g = lay["gfa_measured"]
    over = g["margin"] < 0

    fig = plt.figure(figsize=A1)
    fig.patch.set_facecolor("white")
    fig.text(0.025, 0.958, "VILLA 5130272", fontsize=26, color=INK)
    fig.text(0.025, 0.938, "SAIH SHUAIB 1, JEBEL ALI HILLS, DUBAI", fontsize=8,
             color=MUTED)
    fig.text(0.025, 0.910, "FLOOR PLANS", fontsize=15, color=INK)
    fig.text(0.025, 0.893,
             "The courtyard villa of the redesign (D-060, the owner's handover and answers S1 "
             "to S7). Plot up, not north up.",
             fontsize=8, color=MUTED)
    if not over:
        fig.text(0.60, 0.950, f"INSIDE THE GFA CAP BY {g['margin']:.2f} m2",
                 fontsize=15, color=GOOD)
        fig.text(0.60, 0.930, "Measured from the drawn plan, outer face of the "
                 "external walls. For owner review.", fontsize=8, color=MUTED)
    if over:
        fig.text(0.60, 0.950, f"OVER THE GFA CAP BY {-g['margin']:.2f} m2",
                 fontsize=15, color=BAD)
        fig.text(0.60, 0.930,
                 "Shown so the owner can see the plan. Not a valid design until "
                 "this is closed.", fontsize=8, color=BAD)

    interiors = plan_interiors(lay)
    H = clear_heights(lay)
    doors = lay.get("doors") or []
    centres = {k: (it.main.representative_point().x, it.main.representative_point().y)
               for k, it in interiors.items()}

    # Ground floor
    axg = plan_axes(fig, 15, 70, 380, 420)
    _context(axg)
    clash = _pool(axg, lay["plates"]["road"]["u"][1], lay)
    _circulation(axg, lay["floors"]["ground"]["circulation"])
    for r in lay["floors"]["ground"]["rooms"]:
        _room(axg, r, targets, pad_keys, centre=centres.get(r["key"]),
              height=room_height_text(r, "ground", lay, H))
    _interiors(axg, interiors, "ground")
    _open_joins(axg, lay, "ground")
    _doors(axg, doors, "ground", (lay.get("open_joins") or {}).get("ground", []))
    _outline(axg, lay["outlines"]["road_ground"])
    if "ssw" in lay["plates"]:
        _rect_outline(axg, lay["plates"]["ssw"])
    if "living" in lay["plates"]:
        _rect_outline(axg, lay["plates"]["living"])
    if "carport" in lay["plates"]:
        _rect_outline(axg, lay["plates"]["carport"], lw=1.2)
        cp = lay["plates"]["carport"]
        axg.text((cp["u"][0] + cp["u"][1]) / 2, (cp["v"][0] + cp["v"][1]) / 2,
                 f"CARPORT, 2 CARS\nopen, outside GFA\n{cp['u'][1] - cp['u'][0]:.2f} x {cp['v'][1] - cp['v'][0]:.2f} m\n"
                 f"{(cp['u'][1] - cp['u'][0]) * (cp['v'][1] - cp['v'][0]):.1f} m2 ({(cp['u'][1] - cp['u'][0]) * (cp['v'][1] - cp['v'][0]) * 10.7639:.0f} sq ft)\nh 3.00 m",
                 ha="center", va="center", fontsize=4.2, color=MUTED)
    _badges(axg)
    axg.text(0.0, 1.005, f"GROUND FLOOR   clear height {H['ground']:.2f} m, double height "
             f"{H['double']:.2f} m", transform=axg.transAxes, fontsize=12, color=INK)
    axg.text(1.0, 1.005, "SCALE 1:100 AT A1", transform=axg.transAxes,
             fontsize=7, color=MUTED, ha="right")

    # First floor
    axf = plan_axes(fig, 405, 70, 380, 420)
    _context(axf)
    _outline(axf, lay["outlines"]["road_ground"], lw=0.6)          # ground, ghosted
    if "ssw" in lay["plates"]:
        _rect_outline(axf, lay["plates"]["ssw"], lw=0.6)
    for o in lay["floors"]["first"].get("outdoor", []) or []:
        _rect(axf, o, facecolor=DECK, edgecolor=WALL, lw=0.6, ls="--", zorder=3)
        ow, ol = sorted((o["u"][1] - o["u"][0], o["v"][1] - o["v"][0]))
        axf.text((o["u"][0] + o["u"][1]) / 2, (o["v"][0] + o["v"][1]) / 2,
                 o["key"].replace("_", " ").upper() + f"\n{ow:.2f} x {ol:.2f} m\n{o['area_m2']:.1f} m2 "
                 f"({o['area_m2'] * SQM_TO_SQFT:,.0f} sq ft)\nopen, not GFA",
                 ha="center", va="center", fontsize=4.6, color=MUTED, zorder=6)
    if "living" in lay["plates"]:
        lv = lay["plates"]["living"]
        _rect_outline(axf, lv, lw=0.6)
        axf.text((lv["u"][0] + lv["u"][1]) / 2, (lv["v"][0] + lv["v"][1]) / 2,
                 "ROOF OVER THE\nDOUBLE HEIGHT\nLIVING ROOM", ha="center",
                 va="center", fontsize=6, color=MUTED, zorder=6)
    if "ssw" in lay["plates"]:
        axf.text(*[(lay["plates"]["ssw"]["u"][0] + lay["plates"]["ssw"]["u"][1]) / 2,
                   (lay["plates"]["ssw"]["v"][0] + lay["plates"]["ssw"]["v"][1]) / 2],
                 "MASTER TERRACE\non the kitchen roof, D-035\nnot GFA (DDA Q25)",
                 ha="center", va="center", fontsize=6, color=MUTED, zorder=6)
    _circulation(axf, lay["floors"]["first"]["circulation"])
    for v in lay["floors"]["first"].get("voids", []):
        if v["area_m2"] < 0.01:
            continue
        _rect(axf, v, facecolor=VOID, edgecolor=WALL, lw=0.6, ls="--", zorder=4)
        (u0, u1), (v0, v1) = v["u"], v["v"]
        axf.plot([u0, u1], [v0, v1], color=MUTED, lw=0.4, zorder=5)
        axf.plot([u0, u1], [v1, v0], color=MUTED, lw=0.4, zorder=5)
        axf.text((u0 + u1) / 2, (v0 + v1) / 2,
                 f"{VOID_NAMES.get(v['key'], 'VOID')}\n{min(u1 - u0, v1 - v0):.2f} x "
                 f"{max(u1 - u0, v1 - v0):.2f} m, {v['area_m2']:.1f} m2 "
                 f"({v['area_m2'] * SQM_TO_SQFT:,.0f} sq ft)",
                 ha="center", va="center", fontsize=5.4, color=MUTED, zorder=6)
    for r in lay["floors"]["first"]["rooms"]:
        _room(axf, r, targets, pad_keys, centre=centres.get(r["key"]),
              height=room_height_text(r, "first", lay, H))
    _interiors(axf, interiors, "first")
    _open_joins(axf, lay, "first")
    _doors(axf, doors, "first", (lay.get("open_joins") or {}).get("first", []))
    _outline(axf, lay["outlines"]["first"])
    _facade_cuts(axf, lay["outlines"]["first"])
    _badges(axf)
    _north(axf, 31.0, 33.0)
    axf.text(0.0, 1.005, f"FIRST FLOOR   clear height {H['first']:.2f} m",
             transform=axf.transAxes, fontsize=12, color=INK)

    # GFA and notes
    x0, y = 0.025, 0.112
    fig.text(x0, y, "GFA, MEASURED FROM THE PLAN", fontsize=9, color=INK)
    ogv = g.get("outside_gfa_to_verify", {})
    rows = [("Ground floor", g["road_wing_ground"] + g["ssw_wing_ground"]
             + g.get("living_block_ground", 0.0)),
            ("First floor, less the voids", g["first_floor_less_void"]),
            ("Total", g["total"]),
            ("DDA cap", g["cap"]),
            ("Carport, outside GFA, TO VERIFY", ogv.get("carport_m2", 0.0)),
            ("Total if DDA counts the carport" + (", OVER THE CAP" if g["total"] + ogv.get(
                "carport_m2", 0.0) > g["cap"] else ""), g["total"] + ogv.get("carport_m2", 0.0)),
            ("Balconies, terraces, outside GFA, TO VERIFY",
             ogv.get("first_floor_balconies_terrace_m2", 0.0))]
    for i, (label, val) in enumerate(rows):
        fig.text(x0, y - 0.012 * (i + 1), label, fontsize=7.4, color=INK)
        fig.text(x0 + 0.19, y - 0.012 * (i + 1), f"{val:8.2f} m2", fontsize=7.4,
                 color=INK, ha="right", family="monospace")
    fig.text(x0, y - 0.012 * 8.4, "Margin to the cap", fontsize=8, color=BAD if over else GOOD)
    fig.text(x0 + 0.19, y - 0.012 * 8.4, f"{g['margin']:+8.2f} m2", fontsize=8,
             color=BAD if over else GOOD, ha="right", family="monospace")

    x1 = 0.255
    fig.text(x1, y, "NOTES", fontsize=9, color=INK)
    notes = [
        "The courtyard villa (D-060): the owner's handover of 2026-10-23 and answers S1 to S7. "
        "An open courtyard of about 22 m2 with a tree in the middle of the house (S2).",
        "Ground floor: double height foyer with the straight floating stair rising into it, "
        "hall, salon off its own lobby, guest suite off its own lobby, dining and family living "
        "along the garden.",
        "Service row behind the open two car carport: service corridor, maid's room and shower "
        "room, laundry, prep kitchen, show kitchen with the door to the BBQ terrace; plant room beside the carport.",
        "First floor: exactly three bedrooms, each with its own bathroom; the master over the dining "
        "with its walk-in wardrobe, shower bathroom and covered terrace; family lounge and workspace "
        "over the salon; gallery bridge over the foyer.",
        "The first floor is enclosed over the guest suite and the powder room (bedroom 2 and its "
        "lobby above). No fourth bedroom, no linen room, no gates (the handover).",
        "Doors numbered G01 to G21 and F01 to F12 as on the door schedule; fixed glass G12, G13, "
        "F11, F12 onto the courtyard. Every room is reached; the build checks it.",
        "Heights indicative, brief/massing.yaml (D-030, S6): h is clear height, floor to floor "
        "less 0.30 m slab and 0.15 m ceiling services zone. Stair headroom 2.20 m, OI-23.",
        "Carport and the master terrace outside GFA by owner decision D-039, TO VERIFY with DDA "
        "(OI-01). The courtyard, open to the sky, is not floor area.",
        "Walls: external 0.25 m, internal 0.15 m, indicative. Structure by a licensed structural "
        "engineer, not in scope.",
    ]
    if clash:
        notes.append("The pool deck from the Phase 1 massing clashes with the "
                     "widened road wing and must move east.")
    for i, n in enumerate(notes):
        fig.text(x1, y - 0.0105 * (i + 1), n, fontsize=6.6, color=MUTED)

    fig.text(0.975, 0.030, "CONCEPT DESIGN, NOT FOR CONSTRUCTION", fontsize=9,
             color=BAD, ha="right")
    fig.text(0.975, 0.016, "Drawing VJH-GA-001   The courtyard villa, D-061, handover and answers S1 to S7   Rev E   A1 landscape   "
             "true 1:100", fontsize=6.5, color=MUTED, ha="right")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, facecolor="white")
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    print(f"PDF  {build().relative_to(REPO_ROOT)}")
