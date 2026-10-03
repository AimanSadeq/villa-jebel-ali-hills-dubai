"""Furniture for every room (answer P5: A), indicative.

layout(m) furnishes each room and hall of the built model (architecture.Model)
by its type: beds and bedside tables, sofas facing the TV wall, the dining
table, the salon's facing sofas, kitchen runs and the island, desks,
wardrobes in the dress rooms, the bathrooms' basins, WCs, showers and the
master's bath. Every piece is checked against the room's walls, the door
swings, the passages through the open joins, the windows (nothing tall in
front of glass) and the other pieces; a piece that does not fit is left out
and reported, never forced.

Each piece is a list of boxes, each tagged with the palette slot it takes
(brief/palettes.yaml: accents.joinery, accents.textile, accents.highlight,
accents.worktop, fixtures.metal, fixtures.sanitary) or a fixed colour, so
the walkthrough colours the furniture from the chosen palette (D-052).

Sizes are common furniture sizes, indicative; they are not a specification.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

LINEN = "fixed.#f4f1ea"
SCREEN = "fixed.#121212"
GLASS = "fixed.#bcd3dd"
MIRROR = "fixed.#c9d4d8"
J, TX, HI, WT, ME, SA = ("accents.joinery", "accents.textile", "accents.highlight",
                         "accents.worktop", "fixtures.metal", "fixtures.sanitary")
SIDES = ("S", "N", "W", "E")


@dataclass
class Piece:
    name: str
    room: str
    storey: str
    ifc: str = "IfcFurniture"
    block: bool = True                       # stops the walker
    parts: list = field(default_factory=list)    # (slot, u0, u1, v0, v1, z0, z1)
    clear: list = field(default_factory=list)    # 2D boxes kept free in front of it
    side: str = ""                               # the wall it was placed against
    flip: bool = False                           # placed facing that wall (back away from it)

    def footprint(self) -> Polygon:
        """What stands on the floor and stops the walker: parts below 0.30 m
        and thicker than 2 cm (a wall hung vanity or a rug does not block)."""
        floor = [box(p[1], p[3], p[2], p[4]) for p in self.parts if p[5] < 0.3 and p[6] - p[5] > 0.02]
        return unary_union(floor) if floor else Polygon()

    def extent(self) -> Polygon:
        """The whole piece in plan, for the renders and the drawings."""
        return unary_union([box(p[1], p[3], p[2], p[4]) for p in self.parts]) if self.parts else Polygon()


class Room:
    """A room rectangle with a local frame per side: s along the wall, t into
    the room, measured from the wall face."""

    def __init__(self, key, storey, u0, u1, v0, v1):
        self.key, self.storey = key, storey
        self.u0, self.u1, self.v0, self.v1 = u0, u1, v0, v1
        self.poly = box(u0, v0, u1, v1)
        self.blocked: list[Polygon] = []          # door swings and passages
        self.windows: list[tuple[str, float, float, float]] = []   # side, s0, s1, sill
        self.wall_openings: list[tuple[str, float, float]] = []    # side, s0, s1: no wall there
        self.pieces: list[Piece] = []
        self.skipped: list[str] = []

    def length(self, side):
        return (self.u1 - self.u0) if side in ("S", "N") else (self.v1 - self.v0)

    def depth(self, side):
        return (self.v1 - self.v0) if side in ("S", "N") else (self.u1 - self.u0)

    def to_grid(self, side, s0, s1, t0, t1):
        if side == "S":
            return self.u0 + s0, self.u0 + s1, self.v0 + t0, self.v0 + t1
        if side == "N":
            return self.u1 - s1, self.u1 - s0, self.v1 - t1, self.v1 - t0
        if side == "W":
            return self.u0 + t0, self.u0 + t1, self.v1 - s1, self.v1 - s0
        return self.u1 - t1, self.u1 - t0, self.v0 + s0, self.v0 + s1      # E

    def side_of_point(self, u, v):
        d = {"S": abs(v - self.v0), "N": abs(v - self.v1), "W": abs(u - self.u0), "E": abs(u - self.u1)}
        return min(d, key=d.get)

    def s_of(self, side, u, v):
        return {"S": u - self.u0, "N": self.u1 - u, "W": self.v1 - v, "E": v - self.v0}[side]

    def free_wall(self, side):
        """Stretches of this side with wall and no door, opening or window."""
        L = self.length(side)
        cuts = [(a, b) for sd, a, b in self.wall_openings if sd == side]
        cuts += [(a, b) for sd, a, b, _ in self.windows if sd == side]
        out, s = [], 0.0
        for a, b in sorted(cuts):
            if a > s + 0.05:
                out.append((s, a))
            s = max(s, b)
        if L > s + 0.05:
            out.append((s, L))
        return out


def _place(room: Room, name, side, s_c, t_off, local, flip=False, ifc="IfcFurniture",
           block=True, clear=()):
    """Local parts (slot, s0, s1, t0, t1, z0, z1) around s = s_c, from t = t_off."""
    p = Piece(name, room.key, room.storey, ifc, block)
    p.flip = flip
    for slot, s0, s1, t0, t1, z0, z1 in local:
        if flip:
            t0, t1 = -t1, -t0
        u0, u1, v0, v1 = room.to_grid(side, s_c + s0, s_c + s1, t_off + t0, t_off + t1)
        p.parts.append((slot, u0, u1, v0, v1, z0, z1))
    for s0, s1, t0, t1 in clear:
        if flip:
            t0, t1 = -t1, -t0
        u0, u1, v0, v1 = room.to_grid(side, s_c + s0, s_c + s1, t_off + t0, t_off + t1)
        p.clear.append(box(u0, v0, u1, v1))
    return p


def _fits(room: Room, piece: Piece, others: list[Piece] | None = None) -> bool:
    inner = room.poly.buffer(0.005)
    fp = piece.footprint()
    allparts = unary_union([box(p[1], p[3], p[2], p[4]) for p in piece.parts])
    if not inner.contains(allparts):
        return False
    for c in piece.clear:
        if not inner.contains(c):
            return False
    for b in room.blocked:
        if fp.intersection(b).area > 1e-4:
            return False
    # Nothing taller than a window sill in front of the glass, within 0.6 m.
    for side, s0, s1, sill in room.windows:
        zone = box(*_xy(room.to_grid(side, s0, s1, 0.0, 0.6)))
        for p in piece.parts:
            if p[6] > sill + 0.02 and box(p[1], p[3], p[2], p[4]).intersection(zone).area > 1e-4:
                return False
    for o in (others if others is not None else room.pieces):
        ofp = o.footprint()
        if fp.intersection(ofp).area > 1e-4:
            return False
        for c in piece.clear:
            if c.intersection(ofp).area > 1e-4:
                return False
        for c in o.clear:
            if fp.intersection(c).area > 1e-4:
                return False
    return True


def _xy(g):
    u0, u1, v0, v1 = g
    return u0, v0, u1, v1


def _try(room: Room, name, cands, build, record=True, **kw):
    """Place the first candidate (side, s_c, t_off, flip) that fits."""
    for side, s_c, t_off, flip in cands:
        piece = _place(room, name, side, s_c, t_off, build(), flip=flip, **kw)
        if _fits(room, piece):
            piece.side = side
            room.pieces.append(piece)
            return piece
    if record:
        room.skipped.append(name)
    return None


def _any(room: Room, name, sides, cands_for, build, **kw):
    """Try each side in turn; report once if none fits."""
    for sd in sides:
        p = _try(room, name, cands_for(sd), build, record=False, **kw)
        if p:
            return p
    room.skipped.append(name)
    return None


def _run(room: Room, name, side, a, b, maker, min_len, **kw):
    """A run of joinery along [a, b] of a side, as long as fits."""
    L = round(b - a - 0.05, 2)
    while L >= min_len - 1e-6:
        cands = [(side, c, 0.0, False) for c in _along(room, side, L, prefer=(a + b) / 2)
                 if a + L / 2 - 1e-6 <= c <= b - L / 2 + 1e-6]
        p = _try(room, name.format(L=L), cands, lambda: maker(L), record=False, **kw)
        if p:
            return p
        L = round(L - 0.1, 2)
    return None


def _along(room: Room, side, width, prefer=None, step=0.1):
    """Centres along a side for a piece this wide, preferred first."""
    L = room.length(side)
    lo, hi = width / 2, L - width / 2
    if hi < lo:
        return []
    c = prefer if prefer is not None else L / 2
    c = min(max(c, lo), hi)
    out, k = [c], 1
    while True:
        a, b = c - k * step, c + k * step
        if a < lo and b > hi:
            break
        if a >= lo:
            out.append(a)
        if b <= hi:
            out.append(b)
        k += 1
    return out


# Pieces, in the local frame: s along the wall (centred on 0), t out from it.

def bed(w, L=2.10, stands=True):
    h = w / 2
    parts = [(J, -h, h, 0.08, 0.08 + L, 0.0, 0.30),
             (LINEN, -h + 0.03, h - 0.03, 0.10, L + 0.05, 0.30, 0.55),
             (HI, -h, h, L - 0.55, L + 0.06, 0.55, 0.58),
             (TX, -h - 0.05, h + 0.05, 0.0, 0.08, 0.0, 1.25)]
    n = 2 if w > 1.2 else 1
    pw = (w - 0.2) / n
    for i in range(n):
        a = -h + 0.1 + i * pw
        parts.append((LINEN, a + 0.03, a + pw - 0.03, 0.12, 0.55, 0.55, 0.72))
    if stands:
        for sg in (-1, 1):
            a, b = sorted((sg * (h + 0.05), sg * (h + 0.55)))
            parts += [(J, a, b, 0.02, 0.47, 0.0, 0.55),
                      (ME, (a + b) / 2 - 0.08, (a + b) / 2 + 0.08, 0.17, 0.33, 0.55, 0.95)]
    return parts


def sofa(L, d=0.95):
    h = L / 2
    return [(TX, -h, h, 0.0, d, 0.0, 0.42), (TX, -h, h, 0.0, 0.22, 0.42, 0.85),
            (TX, -h, -h + 0.18, 0.22, d, 0.42, 0.62), (TX, h - 0.18, h, 0.22, d, 0.42, 0.62),
            (HI, -h + 0.25, -h + 0.70, 0.22, 0.38, 0.42, 0.80),
            (HI, h - 0.70, h - 0.25, 0.22, 0.38, 0.42, 0.80)]


def armchair(w=0.85):
    h = w / 2
    return [(TX, -h, h, 0.0, w, 0.0, 0.42), (TX, -h, h, 0.0, 0.18, 0.42, 0.80),
            (TX, -h, -h + 0.14, 0.18, w, 0.42, 0.60), (TX, h - 0.14, h, 0.18, w, 0.42, 0.60)]


def table(L, d, top=0.74, slot=WT):
    h = L / 2
    return [(slot, -h, h, 0.0, d, top - 0.04, top), (ME, -h + 0.1, -h + 0.18, 0.1, d - 0.1, 0.0, top - 0.04),
            (ME, h - 0.18, h - 0.1, 0.1, d - 0.1, 0.0, top - 0.04)]


def coffee(L, d):
    h = L / 2
    return [(WT, -h, h, 0.0, d, 0.36, 0.40), (J, -h + 0.08, h - 0.08, 0.08, d - 0.08, 0.0, 0.36)]


def chair():
    return [(TX, -0.23, 0.23, 0.0, 0.48, 0.0, 0.46), (TX, -0.23, 0.23, 0.0, 0.07, 0.46, 0.92)]


def unit(L, d, hgt, slot=J):
    return [(slot, -L / 2, L / 2, 0.0, d, 0.0, hgt)]


def tv_unit(L=1.8):
    return [(J, -L / 2, L / 2, 0.0, 0.45, 0.0, 0.50),
            (SCREEN, -0.82, 0.82, 0.0, 0.05, 1.05, 2.0)]


def counter(L, d=0.62):
    return [(J, -L / 2, L / 2, 0.0, d - 0.02, 0.0, 0.86), (WT, -L / 2, L / 2, 0.0, d, 0.86, 0.90)]


def rug(L, d):
    return [(HI, -L / 2, L / 2, 0.0, d, 0.0, 0.012)]


# Rooms ---------------------------------------------------------------------

def furnish_bedroom(room: Room, w):
    """Bed against the best free wall, a TV unit or desk opposite."""
    cands = []
    walls = sorted(SIDES, key=lambda sd: -max([b - a for a, b in room.free_wall(sd)] or [0]))
    for sd in walls:
        for a, b in room.free_wall(sd):
            if b - a >= w + 1.1:
                for c in _along(room, sd, w + 1.1, prefer=(a + b) / 2):
                    if a + (w + 1.1) / 2 - 1e-6 <= c <= b - (w + 1.1) / 2 + 1e-6:
                        cands.append((sd, c, 0.0, False))
    bedp = _try(room, f"Bed, {w:.2f} m", cands, lambda: bed(w),
                clear=[(-w / 2, w / 2, 2.2, 2.85)])
    if bedp is None:
        return
    side = bedp.side
    opp = {"S": "N", "N": "S", "W": "E", "E": "W"}[side]
    _try(room, "TV unit", [(opp, c, 0.0, False) for c in _along(room, opp, 1.8)], lambda: tv_unit(1.8))
    others = [sd for sd in SIDES if sd not in (side, opp)]
    _any(room, "Desk and chair", others, lambda sd: [(sd, c, 0.0, False) for c in _along(room, sd, 1.2)],
         lambda: table(1.2, 0.55, 0.75, J) + [(TX, -0.23, 0.23, 0.65, 1.13, 0.0, 0.9)])


def furnish_master(room: Room, balcony_side="E"):
    furnish_bedroom(room, 1.93)
    # Private sitting area (FF3): a sofa and two armchairs facing it, by the
    # balcony where it fits.
    for sd in [balcony_side] + [x for x in SIDES if x != balcony_side]:
        L = room.length(sd)
        for c in _along(room, sd, 2.2):
            grp = [_place(room, "Sitting sofa", sd, c, 0.0, sofa(2.2)),
                   _place(room, "Sitting table", sd, c, 1.25, coffee(1.0, 0.6)),
                   _place(room, "Armchair", sd, c - 0.6, 2.95, armchair(), flip=True),
                   _place(room, "Armchair", sd, c + 0.6, 2.95, armchair(), flip=True)]
            if all(_fits(room, g) for g in grp) and not _overlap(grp):
                room.pieces += grp
                break
        else:
            continue
        break
    else:
        room.skipped.append("Private sitting group")
    # Coffee station (FF3): 1.80 m of joinery on a free wall.
    # Coffee station (FF3): the brief's 1.80 m on any free wall first; only
    # if no wall takes 1.80 m does it shrink, down to 1.20 m.
    maker = lambda n: counter(n, 0.6) + [(J, -n / 2, n / 2, 0.0, 0.35, 1.45, 2.2)]  # noqa: E731
    placed = None
    for min_len in (1.80, 1.20):
        for sd in SIDES:
            for a, b in room.free_wall(sd):
                if b - a >= min_len + 0.05:
                    placed = _run(room, "Coffee station, {L:.2f} m", sd, a, b, maker, min_len)
                    if placed:
                        break
            if placed:
                break
        if placed:
            break
    if placed is None:
        room.skipped.append("Coffee station")


def _overlap(group):
    for i, a in enumerate(group):
        for b in group[i + 1:]:
            if a.footprint().intersection(b.footprint()).area > 1e-4:
                return True
    return False


def furnish_group(room: Room, side, pieces_fn, step=0.2):
    """A group placed together along a side (sofa, table, chairs...)."""
    L = room.length(side)
    D = room.depth(side)
    for t_shift in [x * step for x in range(0, int(D / step))]:
        for c in _along(room, side, 1.0, step=step):
            grp = pieces_fn(side, c, t_shift)
            if all(_fits(room, g) for g in grp) and not _overlap(grp):
                room.pieces += grp
                return True
    return False


def furnish_living(room: Room, tv_side):
    _try(room, "TV unit", [(tv_side, c, 0.0, False) for c in _along(room, tv_side, 2.4)],
         lambda: tv_unit(2.4))

    def grp(side, c, t):
        a = 3.0 + t
        return [_place(room, "Sofa, 3.00 m", side, c, a + 0.95, sofa(3.0), flip=True),
                _place(room, "Coffee table", side, c, a - 0.85, coffee(1.3, 0.7)),
                _place(room, "Rug", side, c, a - 1.25, rug(3.0, 2.2), block=False)]
    if not furnish_group(room, tv_side, grp):
        room.skipped.append("Sofa group")


def furnish_dining(room: Room):
    long_side = "W" if room.length("W") >= room.length("S") else "S"
    L = room.length(long_side)
    n = max(2, min(5, int((L - 1.4) / 0.6)))
    tl = n * 0.6 + 0.2

    def grp(side, c, t):
        a = (room.depth(side) - 1.05) / 2 + t - 0.0
        g = [_place(room, f"Dining table, {2 * n + 2} seats", side, c, a, table(tl, 1.05))]
        for i in range(n):
            s = c - tl / 2 + 0.1 + 0.3 + i * 0.6
            g.append(_place(room, "Dining chair", side, s, a - 0.60, chair()))
            g.append(_place(room, "Dining chair", side, s, a + 1.65, chair(), flip=True))
        return g
    for t in (0.0, -0.2, 0.2, -0.4, 0.4):
        c = L / 2
        g = grp(long_side, c, t)
        if all(_fits(room, x) for x in g) and not _overlap(g):
            room.pieces += g
            break
    else:
        room.skipped.append("Dining table")


def furnish_salon(room: Room, feature_side):
    _try(room, "Console", [(feature_side, c, 0.0, False) for c in _along(room, feature_side, 2.0)],
         lambda: unit(2.0, 0.42, 0.80))
    axis = {"W": "S", "E": "S", "S": "W", "N": "W"}[feature_side]
    D = room.depth(axis)
    gap = 2.4                       # between the two sofa fronts

    def grp(side, c, t):
        b0 = t + 0.95 + gap + 0.95          # far sofa's back
        return [_place(room, "Salon sofa, 2.60 m", side, c, t, sofa(2.6)),
                _place(room, "Salon sofa, 2.60 m", side, c, b0, sofa(2.6), flip=True),
                _place(room, "Salon table", side, c, t + 0.95 + (gap - 0.9) / 2, coffee(1.6, 0.9)),
                _place(room, "Rug", side, c, t + 0.6, rug(3.2, gap + 0.7), block=False)]
    ts = [x * 0.1 for x in range(0, int((D - (gap + 1.9)) / 0.1) + 1)]
    for t in sorted(ts, key=lambda x: abs(x - (D - gap - 1.9) / 2)):
        for c in _along(room, axis, 2.6, step=0.2):
            g = grp(axis, c, t)
            if all(_fits(room, x) for x in g) and not _overlap(g):
                room.pieces += g
                return
    room.skipped.append("Salon sofas")


def furnish_kitchen(room: Room, island=True):
    runs = 0
    for sd in sorted(SIDES, key=lambda s: -max([b - a for a, b in room.free_wall(s)] or [0])):
        for a, b in room.free_wall(sd):
            L = b - a - 0.05
            if L < 1.2:
                continue
            p = _run(room, "Kitchen run, {L:.2f} m", sd, a, b,
                     lambda n: counter(n) + [(J, -n / 2, n / 2, 0.0, 0.35, 1.45, 2.25)], 1.2)
            if p is None:
                p = _run(room, "Kitchen counter, {L:.2f} m", sd, a, b, counter, 1.2)
            runs += bool(p)
            if runs >= 2:
                break
        if runs >= 2:
            break
    if island:
        for sd in ("S", "W"):
            D = room.depth(sd)
            L = min(3.0, room.length(sd) - 2.4)
            if L < 1.6:
                continue
            if _try(room, f"Island, {L:.2f} m", [(sd, c, D / 2 - 0.5 + k * 0.1, False)
                                                 for k in (0, -1, 1, -2, 2, -3, 3, -4, 4)
                                                 for c in _along(room, sd, L, step=0.2)],
                    lambda: counter(L, 1.0), record=False):
                break
        else:
            room.skipped.append("Island")


def furnish_dress(room: Room, island=False):
    long_sides = ("W", "E") if room.length("W") >= room.length("S") else ("S", "N")
    width = room.depth(long_sides[0])
    sides = long_sides if width >= 2.1 else long_sides[:1]
    for sd in sides:
        for a, b in room.free_wall(sd):
            L = b - a - 0.05
            if L >= 0.8:
                _run(room, "Wardrobes, {L:.2f} m", sd, a, b, lambda n: unit(n, 0.6, 2.4), 0.8)
    if island and width >= 3.0:
        sd = long_sides[0]
        _try(room, "Dressing island", [(sd, c, width / 2 - 0.4 + k * 0.1, False) for k in (0, -1, 1, -2, 2)
                                       for c in _along(room, sd, 1.6, step=0.2)],
             lambda: unit(1.6, 0.8, 0.9) + [(WT, -0.8, 0.8, 0.0, 0.8, 0.9, 0.93)])


def furnish_bath(room: Room, big=False, shower=True):
    """WC, basin vanity, shower; the master's bath also a tub and two basins."""
    entry = [sd for sd, a, b in room.wall_openings]
    order = [sd for sd in SIDES if sd not in entry] + [sd for sd in SIDES if sd in entry]
    if shower:
        sw = 1.2 if big else (0.9 if min(room.length("S"), room.length("W")) >= 1.8 else 0.8)
        _any(room, "Shower", order, lambda sd: [(sd, c, 0.0, False) for c in _along(room, sd, sw, step=0.15)],
             lambda: [(SA, -sw / 2, sw / 2, 0.0, 0.9, 0.0, 0.05), (GLASS, -sw / 2, sw / 2, 0.88, 0.9, 0.05, 2.0)],
             ifc="IfcSanitaryTerminal")
    if big:
        _any(room, "Bathtub", order, lambda sd: [(sd, c, 0.0, False) for c in _along(room, sd, 1.7, step=0.15)],
             lambda: [(SA, -0.85, 0.85, 0.0, 0.8, 0.0, 0.58)], ifc="IfcSanitaryTerminal")
    nb = 2 if big else 1
    vw = 1.6 if big else 0.8

    def vanity():
        return ([(J, -vw / 2, vw / 2, 0.0, 0.52, 0.30, 0.82), (WT, -vw / 2, vw / 2, 0.0, 0.55, 0.82, 0.86)]
                + [(SA, -vw / 2 + (i + 0.5) * vw / nb - 0.2, -vw / 2 + (i + 0.5) * vw / nb + 0.2,
                    0.1, 0.42, 0.86, 0.98) for i in range(nb)]
                + [(MIRROR, -vw / 2, vw / 2, 0.0, 0.02, 1.15, 2.0)])
    _any(room, f"Vanity, {nb} basin{'s' if nb > 1 else ''}", SIDES,
         lambda sd: [(sd, c, 0.0, False) for c in _along(room, sd, vw, step=0.15)], vanity,
         ifc="IfcSanitaryTerminal")
    _any(room, "WC", SIDES, lambda sd: [(sd, c, 0.0, False) for c in _along(room, sd, 0.5, step=0.1)],
         lambda: [(SA, -0.19, 0.19, 0.0, 0.62, 0.0, 0.42), (SA, -0.25, 0.25, 0.0, 0.12, 0.0, 1.0)],
         ifc="IfcSanitaryTerminal", clear=[(-0.35, 0.35, 0.62, 1.05)])


def furnish_office(room: Room):
    _any(room, "Desk and chair", sorted(SIDES, key=lambda s: -sum(w[2] - w[1] for w in room.windows if w[0] == s)),
         lambda sd: [(sd, c, 0.9, True) for c in _along(room, sd, 1.8)],
         lambda: table(1.8, 0.8, 0.75, J) + [(TX, -0.25, 0.25, -0.65, -0.15, 0.0, 1.0)])
    for sd in SIDES:
        for a, b in room.free_wall(sd):
            if _run(room, "Bookshelves, {L:.2f} m", sd, a, b, lambda n: unit(n, 0.38, 2.2), 1.0):
                return


def furnish_family(room: Room):
    best = max(SIDES, key=lambda s: max([b - a for a, b in room.free_wall(s)] or [0]))
    furnish_living(room, best)


def furnish_maid(room: Room):
    _any(room, "Bed, 0.90 m", SIDES, lambda sd: [(sd, c, 0.0, False) for c in _along(room, sd, 0.9)],
         lambda: bed(0.9, 2.0, stands=False), clear=[(-0.45, 0.45, 2.1, 2.6)])
    _any(room, "Wardrobe", SIDES, lambda sd: [(sd, c, 0.0, False) for c in _along(room, sd, 1.0)],
         lambda: unit(0.8, 0.6, 2.2))


def furnish_laundry(room: Room):
    _any(room, "Washer and dryer, counter", SIDES, lambda sd: [(sd, c, 0.0, False) for c in _along(room, sd, 1.4)],
         lambda: [(SA, -0.68, -0.08, 0.0, 0.6, 0.0, 0.85), (SA, 0.08, 0.68, 0.0, 0.6, 0.0, 0.85),
                  (WT, -0.7, 0.7, 0.0, 0.62, 0.85, 0.89)])


def furnish_pantry(room: Room):
    for sd in SIDES:
        for a, b in room.free_wall(sd):
            L = b - a - 0.05
            if L >= 0.8:
                _run(room, "Pantry shelves, {L:.2f} m", sd, a, b, lambda n: unit(n, 0.45, 2.2), 0.8)


def furnish_foyer(room: Room):
    _any(room, "Console and mirror", SIDES, lambda sd: [(sd, c, 0.0, False) for c in _along(room, sd, 1.8)],
         lambda: unit(1.8, 0.4, 0.85) + [(MIRROR, -0.6, 0.6, 0.0, 0.02, 1.2, 2.3)])


def layout(m) -> tuple[list[Piece], list[str]]:
    """Furniture for the built model m (architecture.Model)."""
    lay = m.lay
    pieces: list[Piece] = []
    report: list[str] = []
    rects = {}
    for storey, rooms in (("ground", m.g_rooms + m.g_circ), ("first", m.f_rooms + m.f_circ)):
        for r in rooms:
            rects[(storey, r.key)] = Room(r.key, storey, r.u0, r.u1, r.v0, r.v1)
    # Door swings and openings.
    for d in lay.get("doors") or []:
        for k in (d["a"], d["b"]):
            room = rects.get((d["storey"], k))
            if room is None:
                continue
            w = d["width_m"]
            side = room.side_of_point(d["u"], d["v"])
            s = room.s_of(side, d["u"], d["v"])
            depth = {"single": max(w, 0.9), "double": max(w / 2, 0.9), "lift": 1.5}.get(d["kind"], 1.0)
            room.blocked.append(box(*_xy(room.to_grid(side, s - w / 2 - 0.05, s + w / 2 + 0.05, 0, depth))))
            room.wall_openings.append((side, s - w / 2 - 0.05, s + w / 2 + 0.05))
    # Open joins: a passage 1.0 m deep along each join, and no wall there.
    for storey in ("ground", "first"):
        for _, g in m.bridges[storey]:
            for (st, k), room in rects.items():
                if st != storey or room.poly.distance(g) > 0.02:
                    continue
                gb = g.bounds
                c = ((gb[0] + gb[2]) / 2, (gb[1] + gb[3]) / 2)
                side = room.side_of_point(*c)
                if side in ("S", "N"):
                    a, b = sorted((room.s_of(side, gb[0], c[1]), room.s_of(side, gb[2], c[1])))
                else:
                    a, b = sorted((room.s_of(side, c[0], gb[1]), room.s_of(side, c[0], gb[3])))
                room.wall_openings.append((side, a, b))
                room.blocked.append(box(*_xy(room.to_grid(side, a, b, 0, 1.0))))
    # Windows.
    for w in m.window_boxes:
        st = "first" if w["z0"] >= m.HG - 0.01 else "ground"
        cu, cv = (w["u0"] + w["u1"]) / 2, (w["v0"] + w["v1"]) / 2
        for (s2, k), room in rects.items():
            if s2 != st or room.poly.buffer(0.2).distance(box(w["u0"], w["v0"], w["u1"], w["v1"])) > 0:
                continue
            if room.poly.distance(box(w["u0"], w["v0"], w["u1"], w["v1"])) > 0.2:
                continue
            side = room.side_of_point(cu, cv)
            if side in ("S", "N"):
                a, b = sorted((room.s_of(side, w["u0"], cv), room.s_of(side, w["u1"], cv)))
            else:
                a, b = sorted((room.s_of(side, cu, w["v0"]), room.s_of(side, cu, w["v1"])))
            room.windows.append((side, a, b, w["z0"] - m.elev[st]))
    from model.finishes import load as load_palettes  # noqa: PLC0415
    feature = {f["room"]: f["side"] for f in (load_palettes().get("feature_walls") or [])}
    for (storey, key), room in rects.items():
        if key in ("master_suite",):
            furnish_master(room)
        elif key.startswith("bedroom_") and not any(x in key for x in ("dress", "toilet")) or key == "guest_bedroom":
            furnish_bedroom(room, 1.60)
        elif key == "maids_room":
            furnish_maid(room)
        elif "dress" in key:
            furnish_dress(room, island=(key == "master_dress"))
        elif key == "master_toilet":
            furnish_bath(room, big=True)
        elif key == "wash":
            _any(room, "Vanity, 1 basin", SIDES, lambda sd: [(sd, c, 0.0, False) for c in _along(room, sd, 0.8, step=0.15)],
                 lambda: [(J, -0.4, 0.4, 0.0, 0.52, 0.30, 0.82), (WT, -0.4, 0.4, 0.0, 0.55, 0.82, 0.86),
                          (SA, -0.2, 0.2, 0.1, 0.42, 0.86, 0.98), (MIRROR, -0.4, 0.4, 0.0, 0.02, 1.15, 2.0)],
                 ifc="IfcSanitaryTerminal")
        elif "powder" in key:
            furnish_bath(room, shower=False)
        elif any(x in key for x in ("toilet", "outdoor_bathroom")):
            furnish_bath(room)
        elif key == "living":
            furnish_living(room, feature.get("living", "N"))
        elif key == "dining":
            furnish_dining(room)
        elif key == "salon":
            furnish_salon(room, feature.get("salon", "W"))
        elif key == "family_living":
            furnish_family(room)
        elif key == "show_kitchen":
            furnish_kitchen(room, island=True)
        elif key == "arabic_kitchen":
            furnish_kitchen(room, island=False)
        elif key == "pantry":
            furnish_pantry(room)
        elif key == "laundry":
            furnish_laundry(room)
        elif key == "home_office":
            furnish_office(room)
        elif key == "entrance_foyer":
            furnish_foyer(room)
        else:
            continue
        pieces += room.pieces
        report += [f"{key}: {s} does not fit, left out" for s in room.skipped]
    return pieces, report
