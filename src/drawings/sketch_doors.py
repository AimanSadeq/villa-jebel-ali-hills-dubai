"""Door drawing for the decision sketches (VJH-SK-013, VJH-SK-014). The door
schedule itself lives in src/model/doors.py.

The plan the doors are drawn on: plot X = frame y, plot Y = frame x.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import math

from matplotlib.patches import Arc, Polygon as MplPolygon

from model.doors import FIRST, FIRST_EXT, GROUND, GROUND_EXT, place, shared_wall, unreached  # noqa: F401

DOOR = "#8a3f2a"
TAG = "#b3261e"

def _p(axis, n, t):
    """Plot point for a position n across the wall and t along it."""
    # axis "y": wall across frame y = plot X; door runs along frame x = plot Y.
    return (n, t) if axis == "y" else (t, n)


def _leaf(ax, axis, hinge_n, hinge_t, closed_t, s, r):
    h = _p(axis, hinge_n, hinge_t)
    o = _p(axis, hinge_n + s * r, hinge_t)
    c = _p(axis, hinge_n, closed_t)
    ax.plot([h[0], o[0]], [h[1], o[1]], color=DOOR, lw=0.9, zorder=8)
    a1 = math.degrees(math.atan2(o[1] - h[1], o[0] - h[0]))
    a2 = math.degrees(math.atan2(c[1] - h[1], c[0] - h[0]))
    t1, t2 = (a1, a2) if (a2 - a1) % 360 == 90 else (a2, a1)
    ax.add_patch(Arc(h, 2 * r, 2 * r, theta1=t1, theta2=t2, color=DOOR, lw=0.6, zorder=8))


def draw_door(ax, axis, lo, hi, c, w, kind, s, tag):
    """s = +1 if the leaf swings toward increasing frame coordinate on `axis`."""
    gap = [_p(axis, lo - 0.02, c - w / 2), _p(axis, hi + 0.02, c - w / 2),
           _p(axis, hi + 0.02, c + w / 2), _p(axis, lo - 0.02, c + w / 2)]
    ax.add_patch(MplPolygon(gap, closed=True, fc="white", ec="none", zorder=7))
    e = hi if s > 0 else lo
    if kind == "single":
        _leaf(ax, axis, e, c - w / 2, c + w / 2, s, w)
    elif kind == "double":
        _leaf(ax, axis, e, c - w / 2, c, s, w / 2)
        _leaf(ax, axis, e, c + w / 2, c, s, w / 2)
    elif kind == "pivot":
        # Pivot about a fifth of the way along: the long part swings in, the
        # short part out.
        tp = c - w / 2 + w / 5
        _leaf(ax, axis, e, tp, c + w / 2, s, 0.8 * w)
        _leaf(ax, axis, lo if s > 0 else hi, tp, c - w / 2, -s, 0.2 * w)
    elif kind in ("sliding", "lift"):
        m = (lo + hi) / 2
        for dn, t0, t1 in ((-0.04, c - w / 2, c + 0.05), (0.04, c - 0.05, c + w / 2)):
            p0, p1 = _p(axis, m + dn, t0), _p(axis, m + dn, t1)
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=DOOR, lw=1.1, zorder=8)
    else:  # open
        for t in (c - w / 2, c + w / 2):
            p0, p1 = _p(axis, lo, t), _p(axis, hi, t)
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=DOOR, lw=0.6, zorder=8)
    off = 0.55 if kind in ("single", "double", "pivot") else 0.35
    tx, ty = _p(axis, e + s * off, c + (0.0 if kind != "single" else 0.0))
    ax.text(tx, ty, tag, fontsize=4.6, color="white", ha="center", va="center", weight="bold",
            zorder=9, bbox=dict(boxstyle="round,pad=0.18", fc=TAG, ec="none"))


def draw_all(ax, doors: list[dict]):
    for d in doors:
        draw_door(ax, d["axis"], d["lo"], d["hi"], d["c"], d["w"], d["kind"], d["s"], d["no"])


