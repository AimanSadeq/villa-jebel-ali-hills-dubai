"""Phase 1 graphic sheets for Villa 5130272.

Two sheets, both A2 landscape:
  VJH-MA-001  Massing options, three site plans with real cast shadows, the
              shade comparison, and the recommendation.
  VJH-SS-001  Sun study, sun paths, facade exposure rose, and the am/pm split.

These are analysis graphics rather than CAD drawings, so they are drawn with
matplotlib. The CAD deliverables come from ezdxf in Phase 6.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis.massing_study import AFTERNOON, seasonal_shade  # noqa: E402
from analysis.sun_study import (  # noqa: E402
    KEY_DATES,
    facade_exposure,
    irradiation_by_azimuth,
    sun_path,
    sun_vector,
)
from model.massing import (  # noqa: E402
    load_massing, option_shadow, options, site_to_grid, wall_to_boundary,
)
from model.site import buildable_envelope, plot_polygon, sides  # noqa: E402

MASSING_OUT = REPO_ROOT / "output" / "pdf" / "VJH-MA-001_Massing_Options.pdf"
SUN_OUT = REPO_ROOT / "output" / "pdf" / "VJH-SS-001_Sun_Study.pdf"

MM = 1 / 25.4
A2 = (594 * MM, 420 * MM)

INK = "#1a1a1a"
MUTED = "#6b6b6b"
FAINT = "#c8c8c8"
PLOT_LINE = "#b3261e"
ENVELOPE = "#b8860b"
MASS_G = "#9aa3ab"
MASS_1 = "#5d676f"
POOL = "#2a7fb8"
DECK = "#ded3bd"
SHADOW = "#2f3b45"
DRIVE = "#d9d9d9"
GOOD = "#2e7d4f"
DIMCOL = "#1f6f8b"
BAD = "#b3261e"

STAMP = "CONCEPT DESIGN, NOT FOR CONSTRUCTION"
SHADOW_WHEN = pd.Timestamp("2026-08-21 16:00", tz="Asia/Dubai")


# Plans are drawn in the plot's own grid rather than north up, so the plot reads
# as a rectangle with the entrance on one side and the backyard on the other,
# instead of as a rotated diamond. The north arrow is rotated to match, so the
# true orientation is still on the sheet.
GRID_BEARING = float(load_massing()["grid"]["bearing_deg"])


def _g(geom):
    """Site geometry into the plot grid frame."""
    return site_to_grid(geom, GRID_BEARING)


def _poly_xy(geom):
    """Exterior rings of a Polygon or MultiPolygon, as (xs, ys) pairs."""
    geoms = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    return [g.exterior.xy for g in geoms if not g.is_empty]


def _fill(ax, geom, **kw):
    for xs, ys in _poly_xy(geom):
        ax.add_patch(MplPolygon(np.column_stack([xs, ys]), closed=True, **kw))


def _outline(ax, geom, **kw):
    for xs, ys in _poly_xy(geom):
        ax.plot(xs, ys, **kw)


def _side_badge(ax, x, y, number, role, sub, accent):
    """Numbered side marker, placed just outside the boundary it labels."""
    col = GOOD if accent else INK
    ax.add_patch(FancyBboxPatch(
        (x - 4.6, y - 2.4), 9.2, 4.8,
        boxstyle="round,pad=0.25,rounding_size=0.8",
        linewidth=0.7, edgecolor=col if accent else "#c6c0b4",
        facecolor="white", zorder=14))
    ax.add_patch(Circle((x, y + 1.15), 1.05, facecolor=col,
                        edgecolor="none", zorder=15))
    ax.text(x, y + 1.15, str(number), ha="center", va="center",
            color="white", fontsize=6.5, zorder=16)
    ax.text(x, y - 0.55, role, ha="center", va="center", color=col,
            fontsize=6, zorder=16)
    ax.text(x, y - 1.8, sub, ha="center", va="center", color=MUTED,
            fontsize=4.6, zorder=16)


def _dimensions(ax, option):
    """Wall to boundary distances, drawn where each one was measured."""
    from shapely.geometry import Point

    for r in wall_to_boundary(option):
        a = _g(Point(*r["from_xy"]))
        b = _g(Point(*r["to_xy"]))
        if r["distance_m"] < 0.05:
            continue

        ax.annotate("", xy=(b.x, b.y), xytext=(a.x, a.y),
                    arrowprops=dict(arrowstyle="<|-|>", color=DIMCOL, lw=0.7,
                                    shrinkA=0, shrinkB=0,
                                    mutation_scale=7), zorder=12)
        mx, my = (a.x + b.x) / 2, (a.y + b.y) / 2
        horizontal = abs(b.x - a.x) >= abs(b.y - a.y)
        ax.text(mx, my + (0.95 if horizontal else 0), f"{r['distance_m']:.2f} m",
                ha="center", va="bottom" if horizontal else "center",
                rotation=0 if horizontal else 90,
                fontsize=5.6, color=DIMCOL, zorder=13,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none",
                          alpha=0.88))


def _side_labels(ax, option):
    """Numbered badges on all four sides, naming the entrance and the backyard."""
    from analysis.massing_study import pool_bearing_to_neighbours

    garden_side = pool_bearing_to_neighbours(option)["nearest_side"]
    # In the grid frame side 1 is the left edge, 3 the right, 2 the bottom,
    # 4 the top. See brief/massing.yaml.
    place = {1: (-6.0, 17.0), 3: (36.6, 17.0), 2: (15.3, -4.4), 4: (15.3, 38.0)}

    for s in sides():
        x, y = place[s.id]
        if s.is_main_access:
            role, accent = "ENTRANCE", True
        elif s.id == garden_side:
            role, accent = "BACKYARD, POOL", True
        else:
            role, accent = "NEIGHBOUR", False
        _side_badge(ax, x, y, s.id, role, s.adjacency, accent)


def _plan_panel(ax, option, show_shadow=True):
    plot, env = plot_polygon(), buildable_envelope()

    _fill(ax, _g(plot), facecolor="#fbfaf7", edgecolor="none", zorder=0)
    _outline(ax, _g(env), color=ENVELOPE, lw=0.9, ls=(0, (6, 3)), zorder=2)

    if show_shadow:
        sun = sun_vector(SHADOW_WHEN)
        if sun is not None:
            shade = option_shadow(option, sun).intersection(plot)
            if not shade.is_empty:
                _fill(ax, _g(shade), facecolor=SHADOW, alpha=0.30,
                      edgecolor="none", zorder=5.5)

    _fill(ax, _g(option.driveway), facecolor=DRIVE, edgecolor=MUTED, lw=0.4, zorder=3)
    _fill(ax, _g(option.deck), facecolor=DECK, edgecolor="#b8a888", lw=0.5, zorder=4)
    _fill(ax, _g(option.pool), facecolor=POOL, edgecolor="#1b5f8c", lw=0.7, zorder=5)
    _fill(ax, _g(option.ground), facecolor=MASS_G, edgecolor=INK, lw=0.9, zorder=6)
    _fill(ax, _g(option.first), facecolor=MASS_1, edgecolor=INK, lw=0.9, zorder=7)
    _outline(ax, _g(option.garage), color="#ffffff", lw=0.9, ls=(0, (3, 2)), zorder=8)
    _outline(ax, _g(plot), color=PLOT_LINE, lw=1.6, zorder=9)

    c = _g(option.pool).centroid
    ax.text(c.x, c.y, "POOL", ha="center", va="center", color="white",
            fontsize=5.5, zorder=10)
    g = _g(option.garage).centroid
    ax.text(g.x, g.y, "GARAGE", ha="center", va="center", color="white",
            fontsize=5, zorder=10)

    _dimensions(ax, option)
    _side_labels(ax, option)

    ax.set_aspect("equal")
    ax.set_xlim(-11.5, 42.5)
    ax.set_ylim(-8.0, 42.0)
    ax.axis("off")


def _north_arrow(ax, x, y, size=3.2):
    """True north, rotated into the plot grid frame.

    The plans are drawn plot up, so north is not straight up the sheet. It sits
    GRID_BEARING degrees anticlockwise from vertical.
    """
    a = np.radians(GRID_BEARING)
    dx, dy = -np.sin(a), np.cos(a)
    ax.annotate("", xy=(x + dx * size, y + dy * size),
                xytext=(x - dx * size * 0.4, y - dy * size * 0.4),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.1))
    ax.text(x + dx * (size + 1.5), y + dy * (size + 1.5), "N",
            ha="center", va="center", fontsize=7, color=INK)
    ax.text(x, y - size - 1.2, "Plot up, not north up",
            ha="center", va="center", fontsize=5.0, color=MUTED)


def massing_sheet() -> Path:
    from analysis.massing_study import summarise  # noqa: PLC0415

    opts = options()
    sums = {s["key"]: s for s in (summarise(o) for o in opts)}

    fig = plt.figure(figsize=A2)
    fig.patch.set_facecolor("white")

    fig.text(0.035, 0.955, "VILLA 5130272", fontsize=24, color=INK, weight="light")
    fig.text(0.035, 0.932, "SAIH SHUAIB 1, JEBEL ALI HILLS, DUBAI",
             fontsize=8, color=MUTED)
    fig.text(0.035, 0.905, "MASSING OPTIONS", fontsize=14, color=INK)
    fig.text(0.035, 0.888,
             "Phase 1. Pool and garden position. For owner decision, none approved.",
             fontsize=7.5, color=MUTED)
    fig.text(0.70, 0.952,
             f"Shadows cast at {SHADOW_WHEN.strftime('%d %b, %H:%M')} local, "
             "peak cooling season.\nComputed from the villa mass, not indicative.",
             fontsize=7, color=MUTED, va="top")

    best = max(sums.values(), key=lambda s: s["cooling_pm_shade"])

    for i, opt in enumerate(opts):
        ax = fig.add_axes([0.035 + i * 0.317, 0.455, 0.295, 0.40])
        _plan_panel(ax, opt)
        s = sums[opt.key]
        chosen = opt.key == best["key"]

        ax.text(0.0, 1.045, f"OPTION {opt.key}", transform=ax.transAxes,
                fontsize=12, color=INK)
        ax.text(0.165, 1.047, opt.name.upper(), transform=ax.transAxes,
                fontsize=10, color=GOOD if chosen else MUTED)
        if chosen:
            ax.text(0.165, 1.005, "RECOMMENDED", transform=ax.transAxes,
                    fontsize=7.5, color=GOOD)
        ax.text(0.0, -0.02,
                f"Summer afternoon shade on pool  {s['cooling_pm_shade']:.0%}",
                transform=ax.transAxes, fontsize=7.5,
                color=GOOD if s["cooling_pm_shade"] > 0.5 else BAD)
        ax.text(0.0, -0.055,
                f"Winter midday sun on pool  {s['winter_midday_sun']:.0%}",
                transform=ax.transAxes, fontsize=7.5, color=MUTED)
        ax.text(0.0, -0.09,
                f"Pool faces side {s['pool_nearest_side']}: {s['pool_faces']}",
                transform=ax.transAxes, fontsize=7.5, color=MUTED)
        if i == 0:
            _north_arrow(ax, 37.5, 31.0)

    # Shade through the afternoon
    ax1 = fig.add_axes([0.035, 0.115, 0.26, 0.24])
    for opt in opts:
        s = sums[opt.key]
        ys = [s["by_hour"].get(h, 0) * 100 for h in AFTERNOON]
        chosen = opt.key == best["key"]
        ax1.plot(AFTERNOON, ys, marker="o", ms=4,
                 lw=2.2 if chosen else 1.2,
                 color=GOOD if chosen else (BAD if s["cooling_pm_shade"] < 0.3 else MUTED),
                 label=f"{opt.key} {opt.name}")
    ax1.set_xticks(AFTERNOON)
    ax1.set_xticklabels([f"{h}:00" for h in AFTERNOON], fontsize=7)
    ax1.set_ylim(-4, 104)
    ax1.set_ylabel("Pool and deck in shade, %", fontsize=7.5, color=INK)
    ax1.set_title("Shade through the cooling season afternoon",
                  fontsize=9, color=INK, loc="left")
    ax1.tick_params(labelsize=7)
    ax1.grid(alpha=0.25, lw=0.5)
    ax1.legend(fontsize=6.5, frameon=False, loc="lower right")
    for sp in ("top", "right"):
        ax1.spines[sp].set_visible(False)

    # Facade exposure of the plot's four sides
    ax2 = fig.add_axes([0.355, 0.115, 0.26, 0.24])
    fe = facade_exposure()
    idx = np.arange(len(fe))
    ax2.bar(idx - 0.19, fe["summer_morning_kwh_m2"], 0.38,
            label="Summer morning", color="#8fb8d4")
    ax2.bar(idx + 0.19, fe["summer_afternoon_kwh_m2"], 0.38,
            label="Summer afternoon", color=BAD)
    ax2.set_xticks(idx)
    ax2.set_xticklabels([f"Side {int(r['side'])}\n{r['compass']}"
                         for _, r in fe.iterrows()], fontsize=7)
    ax2.set_ylabel("kWh/m2 on the wall", fontsize=7.5, color=INK)
    ax2.set_title("Where the heat lands, and when", fontsize=9, color=INK, loc="left")
    ax2.tick_params(labelsize=7)
    ax2.grid(alpha=0.25, lw=0.5, axis="y")
    ax2.legend(fontsize=6.5, frameon=False)
    for sp in ("top", "right"):
        ax2.spines[sp].set_visible(False)
    ax2.text(0.02, -0.30,
             "Side 3, the landscape plot face, takes its heat in the morning and\n"
             "almost none after 15:00. It is the cheap face to glaze, and the only\n"
             "one with a permanent open view and no overlooking.",
             transform=ax2.transAxes, fontsize=6.8, color=MUTED, va="top")

    # Recommendation
    ax3 = fig.add_axes([0.675, 0.115, 0.29, 0.24])
    ax3.axis("off")
    ax3.text(0, 1.0, "RECOMMENDATION", fontsize=10, color=INK, va="top")
    ax3.text(0, 0.90, f"OPTION {best['key']}, {best['name'].upper()}",
             fontsize=13, color=GOOD, va="top")
    body = (
        f"Holds {best['cooling_pm_shade']:.0%} of the pool deck in shade through\n"
        f"cooling season afternoons, complete from 17:00, and never\n"
        f"below {best['cooling_pm_shade_min']:.0%} at any hour tested. Still gives\n"
        f"{best['winter_midday_sun']:.0%} sun on the water at winter midday.\n\n"
        "The only option that wins on both, because the villa\n"
        "stands between the pool and the afternoon sun without\n"
        "standing between the pool and the winter sun.\n\n"
        "Garden and main glazing face landscape plot 5130274:\n"
        "the cheapest face to glaze and the plot's only permanent\n"
        "open view. The master suite can take that orientation.\n"
        "The hot road and neighbour faces take the service rooms,\n"
        "the garage and deep overhangs rather than glass."
    )
    ax3.text(0, 0.76, body, fontsize=7.4, color=INK, va="top", linespacing=1.55)

    legend = [
        Line2D([], [], color=PLOT_LINE, lw=1.6, label="Plot boundary"),
        Line2D([], [], color=ENVELOPE, lw=0.9, ls=(0, (6, 3)),
               label="3 m setback, buildable envelope"),
        Line2D([], [], marker="s", ls="none", ms=7, mfc=MASS_G, mec=INK,
               label="Ground floor"),
        Line2D([], [], marker="s", ls="none", ms=7, mfc=MASS_1, mec=INK,
               label="First floor over"),
        Line2D([], [], marker="s", ls="none", ms=7, mfc=POOL, mec="#1b5f8c",
               label="Pool, 10 x 4 m"),
        Line2D([], [], marker="s", ls="none", ms=7, mfc=DECK, mec="#b8a888",
               label="Deck"),
        Line2D([], [], marker="s", ls="none", ms=7, mfc=SHADOW, alpha=0.4,
               mec="none", label="Cast shadow, 21 Aug 16:00"),
        Line2D([], [], color=DIMCOL, lw=0.7, marker="|", ms=6,
               label="Wall to boundary, metres"),
    ]
    fig.legend(handles=legend, loc="lower left", bbox_to_anchor=(0.035, 0.035),
               ncol=4, fontsize=7, frameon=False)

    fig.text(0.965, 0.035, STAMP, fontsize=8, color=PLOT_LINE, ha="right")
    fig.text(0.965, 0.018,
             "Drawing VJH-MA-001   Phase 1   Rev A   A2 landscape",
             fontsize=6.5, color=MUTED, ha="right")

    MASSING_OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(MASSING_OUT, facecolor="white")
    plt.close(fig)
    return MASSING_OUT


def sun_sheet() -> Path:
    fig = plt.figure(figsize=A2)
    fig.patch.set_facecolor("white")

    fig.text(0.035, 0.955, "VILLA 5130272", fontsize=24, color=INK, weight="light")
    fig.text(0.035, 0.932, "SAIH SHUAIB 1, JEBEL ALI HILLS, DUBAI",
             fontsize=8, color=MUTED)
    fig.text(0.035, 0.905, "SUN STUDY", fontsize=14, color=INK)
    fig.text(0.035, 0.888,
             "24.897528 N, 54.964976 E, Asia/Dubai. True north verified against "
             "the DDA GIS.", fontsize=7.5, color=MUTED)

    # Sun paths, polar, north up, clockwise, altitude as radius
    ax = fig.add_axes([0.05, 0.30, 0.40, 0.52], projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    colours = ["#b3261e", "#d98324", "#2e7d4f", "#2a7fb8"]
    for (label, md), col in zip(KEY_DATES.items(), colours):
        sp = sun_path(md)
        ax.plot(np.radians(sp["azimuth"]), 90 - sp["apparent_elevation"],
                color=col, lw=1.8, label=label)
    # Hour marks on the summer path
    sp = sun_path("06-21", freq="60min")
    for t, row in sp.iterrows():
        ax.plot(np.radians(row["azimuth"]), 90 - row["apparent_elevation"],
                "o", ms=2.5, color=INK)
        if t.hour % 3 == 0:
            ax.text(np.radians(row["azimuth"]), 90 - row["apparent_elevation"] - 4,
                    f"{t.hour}:00", fontsize=6, color=MUTED, ha="center")
    ax.set_rlim(0, 90)
    ax.set_rgrids([15, 30, 45, 60, 75], labels=["75d", "60d", "45d", "30d", "15d"],
                  fontsize=6, color=MUTED, angle=202)
    ax.set_thetagrids(range(0, 360, 45),
                      ["N", "NE", "E", "SE", "S", "SW", "W", "NW"], fontsize=8)
    ax.grid(alpha=0.3, lw=0.5)
    ax.set_title("Sun paths. Centre is overhead, edge is the horizon.",
                 fontsize=9, color=INK, pad=18)
    ax.legend(fontsize=7, frameon=False, loc="upper left",
              bbox_to_anchor=(-0.18, 1.12))

    # Annual irradiation rose with this plot's facades marked
    ax2 = fig.add_axes([0.50, 0.30, 0.40, 0.52], projection="polar")
    ax2.set_theta_zero_location("N")
    ax2.set_theta_direction(-1)
    allaz = irradiation_by_azimuth()
    th = np.radians(np.append(allaz["azimuth"].values, allaz["azimuth"].values[0]))
    ann = np.append(allaz["annual_kwh_m2"].values, allaz["annual_kwh_m2"].values[0])
    pm = np.append(allaz["summer_afternoon_kwh_m2"].values,
                   allaz["summer_afternoon_kwh_m2"].values[0])
    ax2.plot(th, ann, color=MUTED, lw=1.6, label="Annual total")
    ax2.fill(th, ann, color=MUTED, alpha=0.12)
    ax2.plot(th, pm * 4, color=BAD, lw=1.8, label="Summer afternoon, x4")
    ax2.fill(th, pm * 4, color=BAD, alpha=0.15)

    fe = facade_exposure()
    for _, r in fe.iterrows():
        ax2.plot([np.radians(r["azimuth"])], [r["annual_kwh_m2"]], "o",
                 ms=8, color=INK, zorder=5)
        ax2.text(np.radians(r["azimuth"]), r["annual_kwh_m2"] + 230,
                 f"Side {int(r['side'])}\n{r['compass']}", fontsize=7,
                 ha="center", va="center", color=INK)
    ax2.set_thetagrids(range(0, 360, 45),
                       ["N", "NE", "E", "SE", "S", "SW", "W", "NW"], fontsize=8)
    ax2.tick_params(labelsize=6)
    ax2.grid(alpha=0.3, lw=0.5)
    ax2.set_title("Solar exposure on a vertical wall, kWh/m2.\n"
                  "Afternoon trace scaled x4 to show its shape.",
                  fontsize=9, color=INK, pad=18)
    ax2.legend(fontsize=7, frameon=False, loc="upper right",
               bbox_to_anchor=(1.22, 1.12))

    # Findings
    ax3 = fig.add_axes([0.05, 0.065, 0.90, 0.19])
    ax3.axis("off")
    ax3.text(0, 1.0, "WHAT THIS MEANS FOR THE DESIGN", fontsize=10, color=INK,
             va="top")
    fe_by = {int(r["side"]): r for _, r in fe.iterrows()}
    text = (
        f"At 24.9 N the summer sun passes almost overhead at noon, 88.5 degrees on "
        f"21 June, so at midday the roof takes the load and the walls are in their "
        f"own shadow.\n"
        f"The real problem is the low afternoon sun in the west, which strikes "
        f"glass nearly head on while the air is at its hottest.\n\n"
        f"Side 1, the road face at WNW, takes "
        f"{fe_by[1]['summer_afternoon_kwh_m2']:.0f} kWh/m2 in summer afternoons, "
        f"{fe_by[1]['summer_afternoon_kwh_m2'] / fe_by[3]['summer_afternoon_kwh_m2']:.1f} "
        f"times what side 3 takes. It needs deep overhangs and recessed glazing, "
        f"and it is where the garage and service rooms belong.\n"
        f"Side 3, the landscape plot face at ESE, takes "
        f"{fe_by[3]['summer_morning_kwh_m2']:.0f} kWh/m2 in the morning but only "
        f"{fe_by[3]['summer_afternoon_kwh_m2']:.0f} in the afternoon. Morning heat "
        f"is cheap: the air is still cool and the cooling plant is not yet loaded. "
        f"It is the face to open up."
    )
    ax3.text(0, 0.84, text, fontsize=8, color=INK, va="top", linespacing=1.6)

    fig.text(0.965, 0.035, STAMP, fontsize=8, color=PLOT_LINE, ha="right")
    fig.text(0.965, 0.018,
             "Drawing VJH-SS-001   Phase 1   Rev A   A2 landscape",
             fontsize=6.5, color=MUTED, ha="right")

    SUN_OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SUN_OUT, facecolor="white")
    plt.close(fig)
    return SUN_OUT


def main() -> int:
    for path in (sun_sheet(), massing_sheet()):
        print(f"PDF  {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
