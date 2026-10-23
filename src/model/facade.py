"""The facade proposal of brief/facade.yaml as boxes (answers F1, F2, R1 to R3).

boxes(windows) returns every facade element as an axis aligned box in the plot
building grid: the named elements, the surrounds and fins of the windows on
the hot faces, and the roof pergola. The sketch VJH-SK-017 draws them over the
IFC model; the facade build will put the same boxes in the IFC, so the two
cannot differ.

windows: dicts with name and the window's bounding box (u0, u1, v0, v1, z0,
z1), as read from the IFC. A window on a hot face is one the model names
"hot" (src/model/architecture.py sizes windows by orientation).

check() lists every box outside the buildable envelope and every window
surround dropped because it would clash with a named element.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

FACADE = REPO_ROOT / "brief" / "facade.yaml"
T_EXT = 0.25
CENTRE_UV = (12.5, 18.3)        # inside the house, to tell the faces apart
OPEN_AIR = {"garage", "main_entrance", "courtyard"}   # the open carport, porch and court


@dataclass
class Box:
    name: str
    material: str
    kind: str
    u0: float
    u1: float
    v0: float
    v1: float
    z0: float
    z1: float

    def overlaps(self, o: "Box", tol: float = 0.005) -> bool:
        return (self.u0 < o.u1 - tol and o.u0 < self.u1 - tol and
                self.v0 < o.v1 - tol and o.v0 < self.v1 - tol and
                self.z0 < o.z1 - tol and o.z0 < self.z1 - tol)


def load(path: Path = FACADE) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def face_of(w: dict, inside=None) -> tuple[str, float]:
    """The face a window looks out of (W, E, S or N) and the wall's outer face.

    inside(u, v, z) tells whether a point is in a room; the window looks out
    on the side that is not. Without it, the side away from the house centre.
    """
    cu, cv = CENTRE_UV
    zm = (w["z0"] + w["z1"]) / 2
    if (w["u1"] - w["u0"]) < (w["v1"] - w["v0"]):          # in a wall along v
        mid, vm = (w["u0"] + w["u1"]) / 2, (w["v0"] + w["v1"]) / 2
        west = mid < cu
        if inside is not None:
            west = not inside(mid - 0.6, vm, zm) and inside(mid + 0.6, vm, zm) or (
                west and not inside(mid - 0.6, vm, zm))
        return ("W", mid - T_EXT / 2) if west else ("E", mid + T_EXT / 2)
    mid, um = (w["v0"] + w["v1"]) / 2, (w["u0"] + w["u1"]) / 2
    south = mid < cv
    if inside is not None:
        south = not inside(um, mid - 0.6, zm) and inside(um, mid + 0.6, zm) or (
            south and not inside(um, mid - 0.6, zm))
    return ("S", mid - T_EXT / 2) if south else ("N", mid + T_EXT / 2)


def _named(spec: dict) -> list[Box]:
    return [Box(e["name"], e["material"], e["kind"], *e["u"], *e["v"], *e["z"])
            for e in spec["elements"]]


def _surround(w: dict, hw: dict, inside=None) -> list[Box]:
    face, plane = face_of(w, inside)
    d, b = hw["surround_depth_m"], hw["surround_border_m"]
    mat = hw["surround_material"]
    z0, z1 = w["z0"], w["z1"]
    name = f"Surround, {w['name']}"
    out: list[Box] = []
    if face in ("W", "E"):
        a0, a1 = (plane - d, plane) if face == "W" else (plane, plane + d)
        s0, s1 = w["v0"], w["v1"]
        mk = lambda t0, t1, h0, h1, nm=name, m=mat, k="surround": Box(nm, m, k, a0, a1, t0, t1, h0, h1)  # noqa: E731
    else:
        a0, a1 = (plane - d, plane) if face == "S" else (plane, plane + d)
        s0, s1 = w["u0"], w["u1"]
        mk = lambda t0, t1, h0, h1, nm=name, m=mat, k="surround": Box(nm, m, k, t0, t1, a0, a1, h0, h1)  # noqa: E731
    out += [mk(s0 - b, s1 + b, z1, z1 + b), mk(s0 - b, s1 + b, z0 - b, z0),
            mk(s0 - b, s0, z0, z1), mk(s1, s1 + b, z0, z1)]
    if face in hw["fins_on_faces"] and s1 - s0 >= hw["fins_min_width_m"]:
        sp, t, fd = hw["fin_spacing_m"], hw["fin_thickness_m"], hw["fin_depth_m"]
        n = int((s1 - s0) // sp)
        gap = (s1 - s0 - n * sp) / 2
        # The fins sit in the reveal, 0.10 m in from the surround's face.
        f0, f1 = (plane - 0.10 - fd, plane - 0.10) if face in ("W", "S") else (plane + 0.10, plane + 0.10 + fd)
        for i in range(1, n):
            c = s0 + gap + i * sp
            if face in ("W", "E"):
                out.append(Box(f"Fin, {w['name']}", hw["fin_material"], "fin",
                               f0, f1, c - t / 2, c + t / 2, z0, z1))
            else:
                out.append(Box(f"Fin, {w['name']}", hw["fin_material"], "fin",
                               c - t / 2, c + t / 2, f0, f1, z0, z1))
    return out


def _pergola(p: dict) -> list[Box]:
    (u0, u1), (v0, v1) = p["u"], p["v"]
    zb, zt, s, bd = p["z_base"], p["z_top"], p["post_m"], p["beam_depth_m"]
    mat = p["material"]
    out: list[Box] = []

    def stations(a0: float, a1: float) -> list[float]:
        n = max(1, -(-(a1 - a0 - s) // p["post_spacing_max_m"]))
        return [a0 + i * (a1 - a0 - s) / n for i in range(int(n) + 1)]

    sp, t, ld = p["louvre_spacing_m"], p["louvre_thickness_m"], p["louvre_depth_m"]
    zl = zt - ld                     # louvres on top of the beams
    for pu in stations(u0, u1):
        for pv in (v0, v1 - s):
            out.append(Box("Pergola post", mat, "pergola", pu, pu + s, pv, pv + s, zb, zl - bd))
    for pv in stations(v0, v1)[1:-1]:
        for pu in (u0, u1 - s):
            out.append(Box("Pergola post", mat, "pergola", pu, pu + s, pv, pv + s, zb, zl - bd))
    out += [Box("Pergola beam", mat, "pergola", u0, u1, v0, v0 + s, zl - bd, zl),
            Box("Pergola beam", mat, "pergola", u0, u1, v1 - s, v1, zl - bd, zl),
            Box("Pergola beam", mat, "pergola", u0, u0 + s, v0, v1, zl - bd, zl),
            Box("Pergola beam", mat, "pergola", u1 - s, u1, v0, v1, zl - bd, zl)]
    if p["louvres_run_along"] == "u":
        c = v0 + sp / 2
        while c < v1:
            out.append(Box("Pergola louvre", mat, "pergola", u0, u1, c - t / 2, c + t / 2, zl, zt))
            c += sp
    else:
        c = u0 + sp / 2
        while c < u1:
            out.append(Box("Pergola louvre", mat, "pergola", c - t / 2, c + t / 2, v0, v1, zl, zt))
            c += sp
    return out


def boxes(windows: list[dict], spec: dict | None = None,
          inside=None) -> tuple[list[Box], list[str]]:
    """All facade boxes, and notes on the surrounds left out. inside: see face_of."""
    spec = spec or load()
    named = _named(spec)
    out = list(named)
    notes: list[str] = []
    hw = spec.get("hot_windows")
    for w in windows:
        if hw is None or "hot" not in w["name"]:
            continue
        sur = _surround(w, hw, inside)
        if any(b.overlaps(n) for b in sur for n in named):
            notes.append(f"No surround on '{w['name']}': it would clash with the facade elements.")
            continue
        out += sur
    if spec.get("pergola"):
        out += _pergola(spec["pergola"])
    return out, notes


def inside_from_layouts(path: Path | None = None):
    """inside(u, v, z) from the rooms and halls of brief/layouts.yaml."""
    lay = yaml.safe_load((path or REPO_ROOT / "brief" / "layouts.yaml").read_text(encoding="utf-8"))
    rects = {f: [(r["u"], r["v"]) for r in lay["floors"][f]["rooms"] + lay["floors"][f]["circulation"]
                 if r["key"] not in OPEN_AIR] for f in ("ground", "first")}

    def inside(u: float, v: float, z: float) -> bool:
        f = "ground" if z < 5.0 else "first"
        return any(a[0] <= u <= a[1] and b[0] <= v <= b[1] for a, b in rects[f])
    return inside


def check(bx: list[Box]) -> list[str]:
    """Boxes outside the buildable envelope (3 m setback), named once each."""
    from shapely.geometry import box as sbox

    from model.massing import site_to_grid
    from model.site import buildable_envelope
    env = site_to_grid(buildable_envelope()).buffer(0.01)
    seen, out = set(), []
    for b in bx:
        if not env.contains(sbox(b.u0, b.v0, b.u1, b.v1)) and b.name not in seen:
            seen.add(b.name)
            out.append(b.name)
    return out
