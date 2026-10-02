"""Sketch VJH-SK-017: the four elevations with the facade proposal (answer R3).

The house is the IFC model as built (output/ifc/VJH-ARCH-001_Villa_5130272.ifc,
run src/model/build_model.py first); the facade elements are brief/facade.yaml
through src/model/facade.py, the same boxes the facade build will add. Each
elevation is drawn by projecting every triangle onto the facade plane with a
depth buffer, so what stands in front hides what is behind, recesses read
darker, and edges are drawn where surfaces change.

Run: python src/drawings/sketch_facade.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import ifcopenshell  # noqa: E402
import ifcopenshell.geom  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from scipy import ndimage  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model import facade  # noqa: E402

IFC = REPO_ROOT / "output" / "ifc" / "VJH-ARCH-001_Villa_5130272.ifc"
MASSING = REPO_ROOT / "brief" / "massing.yaml"
OUT_PDF = REPO_ROOT / "output" / "pdf" / "VJH-SK-017_Facade_Elevations.pdf"
OUT_PNG = REPO_ROOT / "output" / "pdf" / "VJH-SK-017_Facade_Elevations.png"

RES = 40                       # pixels per metre
GROUND_Z = -0.15               # finished ground at the gate level (architecture.build_site)
INK, MUTED, RED = "#1a1a1a", "#6b6b6b", "#b3261e"
SKIP = {"IfcSpace", "IfcOpeningElement", "IfcGeographicElement"}

# Elevations: forward direction, the screen's right in grid terms, and the
# summer sun on that face from the sun study (output/reports/VJH-RPT-003,
# kWh/m2, "This plot's facades").
VIEWS = {
    "W": dict(title="Road elevation (WNW, side 1)", fwd=(1, 0), right=(0, -1),
              sun="Summer 474 kWh/m2, of which 233 in the afternoon: the hottest face at the peak hour"),
    "E": dict(title="Garden elevation (ESE, side 3)", fwd=(-1, 0), right=(0, 1),
              sun="Summer 503 kWh/m2, 368 in the morning and 51 in the afternoon"),
    "S": dict(title="South elevation (SSW, side 2)", fwd=(0, 1), right=(1, 0),
              sun="Summer 414 kWh/m2 (110 am, 141 pm); highest annual, 1,344 kWh/m2"),
    "N": dict(title="North elevation (NNE, side 4)", fwd=(0, -1), right=(-1, 0),
              sun="Summer 368 kWh/m2, mostly morning (244 am, 51 pm)"),
}


def hexrgb(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255


def ifc_material(cls: str, name: str) -> str | None:
    n = name or ""
    if cls in SKIP:
        return None
    if cls == "IfcWindow":
        return "glass"
    if cls == "IfcDoor":
        if n.startswith("Front door"):
            return "timber"
        if n.startswith(("Garden door", "Balcony door")):
            return "glass"
        return "frame"
    if cls == "IfcRailing":
        return "railing"
    if cls in ("IfcStair", "IfcTransportElement"):
        return "interior"
    if cls == "IfcSlab" and "paving" in n.lower():
        return "paving"
    return "render"


def ifc_meshes() -> tuple[list[tuple[str, str, np.ndarray]], list[dict]]:
    """(material, name, triangles n x 3 x 3) per element, and the windows."""
    f = ifcopenshell.open(str(IFC))
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)
    it = ifcopenshell.geom.iterator(s, f, 4)
    meshes, windows = [], []
    if it.initialize():
        while True:
            sh = it.get()
            e = f.by_id(sh.id)
            mat = ifc_material(e.is_a(), e.Name)
            if mat:
                v = np.array(sh.geometry.verts).reshape(-1, 3)
                t = np.array(sh.geometry.faces).reshape(-1, 3)
                meshes.append((mat, e.Name or e.is_a(), v[t]))
                if e.is_a() == "IfcWindow":
                    lo, hi = v.min(0), v.max(0)
                    windows.append(dict(name=e.Name, u0=lo[0], u1=hi[0], v0=lo[1], v1=hi[1],
                                        z0=lo[2], z1=hi[2]))
            if not it.next():
                break
    return meshes, windows


def box_tris(b: facade.Box) -> np.ndarray:
    x = [b.u0, b.u1]
    y = [b.v0, b.v1]
    z = [b.z0, b.z1]
    c = np.array([[x[i], y[j], z[k]] for i in (0, 1) for j in (0, 1) for k in (0, 1)])
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    tris = []
    for q0, q1, q2, q3 in quads:
        tris += [[c[q0], c[q1], c[q2]], [c[q0], c[q2], c[q3]]]
    return np.array(tris)


class Raster:
    """A depth buffered orthographic projection onto one facade plane."""

    def __init__(self, view: dict, s_lim: tuple[float, float], z_lim: tuple[float, float]):
        self.fwd = np.array([*view["fwd"], 0.0])
        self.right = np.array([*view["right"], 0.0])
        self.s0, self.s1 = s_lim
        self.z0, self.z1 = z_lim
        self.W = int((self.s1 - self.s0) * RES)
        self.H = int((self.z1 - self.z0) * RES)
        self.depth = np.full((self.H, self.W), np.inf)
        self.ident = np.full((self.H, self.W), -1, int)
        self.shade = np.ones((self.H, self.W))
        self.s_at = (np.arange(self.W) + 0.5) / RES + self.s0
        self.z_at = self.z1 - (np.arange(self.H) + 0.5) / RES

    def project(self, p: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        s = p @ self.right
        return (s - self.s0) * RES, (self.z1 - p[..., 2]) * RES, p @ self.fwd

    def draw(self, tris: np.ndarray, ident: int, depth=None, idbuf=None, shade=None,
             cuts=()):
        depth = self.depth if depth is None else depth
        idbuf = self.ident if idbuf is None else idbuf
        shade = self.shade if shade is None else shade
        X, Y, D = self.project(tris)
        nrm = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        ln = np.linalg.norm(nrm, axis=1)
        for k in range(len(tris)):
            if ln[k] < 1e-12:
                continue
            n = nrm[k] / ln[k]
            facing = abs(n @ self.fwd)
            sh = 0.80 + 0.20 * facing if abs(n[2]) < 0.5 else 0.90
            xs, ys, ds = X[k], Y[k], D[k]
            x0, x1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), self.W - 1)
            y0, y1 = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())), self.H - 1)
            if x1 < x0 or y1 < y0:
                continue
            px, py = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(den) < 1e-9:
                # Seen edge on: a line, drawn as one pixel wide so thin parts show.
                continue
            a = ((ys[1] - ys[2]) * (px - xs[2]) + (xs[2] - xs[1]) * (py - ys[2])) / den
            b = ((ys[2] - ys[0]) * (px - xs[2]) + (xs[0] - xs[2]) * (py - ys[2])) / den
            c = 1 - a - b
            inside = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
            if not inside.any():
                continue
            d = a * ds[0] + b * ds[1] + c * ds[2]
            sl = (slice(y0, y1 + 1), slice(x0, x1 + 1))
            win = inside & (d < depth[sl] - 1e-4)
            for c in cuts:
                # Leave out what lies in a cut box (facade.yaml cuts).
                sw = px / RES + self.s0
                uu = sw * self.right[0] + d * self.fwd[0]
                vv = sw * self.right[1] + d * self.fwd[1]
                zz = self.z1 - py / RES
                win &= ~((uu > c["u"][0]) & (uu < c["u"][1]) & (vv > c["v"][0]) &
                         (vv < c["v"][1]) & (zz > c["z"][0]) & (zz < c["z"][1]))
            depth[sl][win] = d[win]
            idbuf[sl][win] = ident
            shade[sl][win] = sh


def render(key: str, meshes, fboxes, spec, s_lim, z_lim):
    view = VIEWS[key]
    r = Raster(view, s_lim, z_lim)
    mats = spec["materials"]
    items = []                       # (material, name, kind)
    rails = []
    for mat, name, tris in meshes:
        if mat == "railing":
            rails.append(tris)
            continue
        items.append((mat, name, "ifc"))
        r.draw(tris, len(items) - 1, cuts=spec.get("cuts", []))
    for b in fboxes:
        items.append((b.material, b.name, b.kind))
        r.draw(box_tris(b), len(items) - 1)

    colours = {k: hexrgb(v["colour"]) for k, v in mats.items()}
    colours.update(interior=hexrgb("#bdb7ad"), paving=hexrgb("#cfc8bb"))
    sky = hexrgb("#ffffff")
    img = np.tile(sky, (r.H, r.W, 1))
    hit = r.ident >= 0
    front = r.depth[hit].min() if hit.any() else 0
    recess = np.clip(r.depth - front, 0, 6)
    S, Z = np.meshgrid(r.s_at, r.z_at)
    for i, (mat, name, kind) in enumerate(items):
        m = r.ident == i
        if not m.any():
            continue
        col = colours.get(mat, colours["render"])
        if mat == "glass":
            t = np.clip((Z[m] % 4.5) / 4.5, 0, 1)[:, None]
            img[m] = col * (1 - 0.35 * t) + hexrgb("#a9bcc8") * 0.35 * t
            continue
        img[m] = col * (r.shade[m] * (1 - 0.035 * recess[m]))[:, None]
        if mat == "stone":
            # Split face courses: 0.25 m high, joints staggered, blocks toned.
            course = np.floor(Z[m] / 0.25)
            off = (course * 0.37) % 0.6
            joint = ((Z[m] % 0.25) < 0.012) | (((S[m] + off) % 0.6) < 0.012)
            blk = np.floor((S[m] + off) / 0.6)
            tone = 0.93 + 0.07 * ((np.sin(blk * 12.9898 + course * 78.233) * 43758.5453) % 1)
            px = img[m] * tone[:, None]
            px[joint] *= 0.82
            img[m] = px
    # Ground and below.
    gm = Z < GROUND_Z
    img[gm & ~hit] = hexrgb("#efebe4")

    # Edges where the element, the depth or the shading changes.
    e = np.zeros_like(hit)
    for ax in (0, 1):
        di = np.diff(r.ident, axis=ax) != 0
        dd = np.abs(np.diff(np.where(np.isinf(r.depth), 1e3, r.depth), axis=ax)) > 0.05
        ds = np.abs(np.diff(r.shade, axis=ax)) > 0.03
        ed = di | dd | ds
        if ax == 0:
            e[:-1] |= ed
        else:
            e[:, :-1] |= ed
    img[e] = img[e] * 0.35 + hexrgb("#2a2a2a") * 0.65

    # Glass balustrades, see-through: blended over what is behind them.
    rd = np.full((r.H, r.W), np.inf)
    ri = np.full((r.H, r.W), -1, int)
    rs = np.ones((r.H, r.W))
    for tris in rails:
        r.draw(tris, 0, depth=rd, idbuf=ri, shade=rs)
    vis = (ri >= 0) & (rd < r.depth - 1e-3)
    img[vis] = img[vis] * 0.70 + hexrgb("#b8ccd6") * 0.30
    edge_r = vis & ~ndimage.binary_erosion(vis)
    img[edge_r] = img[edge_r] * 0.5 + hexrgb("#5c7480") * 0.5

    # LED lines, where not hidden, with a soft glow.
    led = np.zeros((r.H, r.W))
    for ln in spec["led"]:
        pts = np.array(ln["points"], float)
        for p, q in zip(pts[:-1], pts[1:]):
            n = max(2, int(np.linalg.norm(q - p) * RES * 2))
            seg = p + (q - p) * np.linspace(0, 1, n)[:, None]
            X, Y, D = r.project(seg)
            ix, iy = X.astype(int), Y.astype(int)
            ok = (ix >= 0) & (ix < r.W) & (iy >= 0) & (iy < r.H)
            ix, iy, D = ix[ok], iy[ok], D[ok]
            seen = D <= r.depth[iy, ix] + 0.08
            led[iy[seen], ix[seen]] = 1
    if led.any():
        glow = ndimage.gaussian_filter(led, 2.0)
        glow = np.clip(glow / max(glow.max(), 1e-6), 0, 1)[..., None]
        img = img * (1 - 0.55 * glow) + hexrgb(mats["led"]["colour"]) * 0.55 * glow
        core = ndimage.binary_dilation(led > 0)
        img[core] = hexrgb("#fff1c9")

    # Ground line.
    gy = int((r.z1 - GROUND_Z) * RES)
    img[max(gy - 1, 0):gy + 2] = hexrgb("#1a1a1a")
    return np.clip(img, 0, 1), r, items


def callouts(r: Raster, items) -> list[tuple[int, float, float]]:
    """A numbered marker at the largest visible part of each proposal group."""
    groups = {1: "Entrance portal", 2: "Garden frame", 3: ("South eave", "South canopy"),
              4: "Carport pier", 5: ("Surround", "Fin"), 6: "Pergola"}
    out = []
    for no, pref in groups.items():
        ids = [i for i, (_, nm, k) in enumerate(items) if k != "ifc" and nm.startswith(pref)]
        if not ids:
            continue
        m = np.isin(r.ident, ids)
        if m.sum() < 30:
            continue
        lab, n = ndimage.label(m)
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        big = lab == (int(np.argmax(sizes)) + 1)
        yy, xx = np.nonzero(big)
        k = len(yy) // 2
        order = np.lexsort((xx, yy))
        yv, xv = yy[order][k], xx[order][k]
        out.append((no, r.s_at[xv], r.z_at[yv]))
    return out


def main() -> int:
    if not IFC.exists():
        print(f"Missing {IFC}; run src/model/build_model.py first.")
        return 1
    spec = facade.load()
    h = yaml.safe_load(MASSING.read_text(encoding="utf-8"))["heights"]
    meshes, windows = ifc_meshes()
    fboxes, notes = facade.boxes(windows, spec, facade.inside_from_layouts())
    outside = facade.check(fboxes)

    allp = np.concatenate([t.reshape(-1, 3) for _, _, t in meshes] +
                          [box_tris(b).reshape(-1, 3) for b in fboxes])
    z_lim = (-1.2, max(12.6, allp[:, 2].max() + 0.6))

    fig = plt.figure(figsize=(23.4, 16.5))
    fig.patch.set_facecolor("white")
    slots = {"W": [0.02, 0.60, 0.37, 0.33], "E": [0.40, 0.60, 0.37, 0.33],
             "S": [0.02, 0.24, 0.37, 0.33], "N": [0.40, 0.24, 0.37, 0.33]}
    for key, view in VIEWS.items():
        right = np.array([*view["right"], 0.0])
        sv = allp @ right
        s_lim = (sv.min() - 1.0, sv.max() + 1.0)
        img, r, items = render(key, meshes, fboxes, spec, s_lim, z_lim)
        ax = fig.add_axes(slots[key])
        ax.imshow(img, extent=(s_lim[0], s_lim[1], z_lim[0], z_lim[1]), origin="upper",
                  interpolation="lanczos")
        ax.set_xlim(s_lim[0], s_lim[1] + 5.0)
        ax.set_ylim(z_lim)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(view["title"], loc="left", fontsize=12, color=INK, fontweight="bold")
        ax.text(s_lim[0], z_lim[0] - 0.2, f"Sun on this face (VJH-RPT-003): {view['sun']}",
                fontsize=7.5, color=MUTED, va="top")
        # Levels on the right.
        xr = s_lim[1] + 0.2
        for z, lab in ((0.0, "+0.00 ground floor"), (float(h["ground_floor_m"]), "+5.00 first floor"),
                       (float(h["roof_slab_m"]), "+9.00 roof"),
                       (float(h["overall_m"]), "+10.20 parapet top"),
                       (spec["pergola"]["z_top"], f"+{spec['pergola']['z_top']:.2f} pergola top, TO VERIFY")):
            ax.plot([xr - 0.2, xr + 0.4], [z, z], color=INK, lw=0.7)
            ax.text(xr + 0.5, z, lab, fontsize=6.5, color=INK, va="center")
        # Scale bar, 5 m.
        x0 = s_lim[0] + 0.5
        for i in range(5):
            ax.add_patch(Rectangle((x0 + i, z_lim[0] + 0.25), 1, 0.18,
                                   facecolor=INK if i % 2 == 0 else "white", edgecolor=INK, lw=0.5))
        ax.text(x0 + 5.2, z_lim[0] + 0.34, "5 m", fontsize=6.5, va="center")
        for no, sx, zz in callouts(r, items):
            ax.annotate(str(no), (sx, zz), fontsize=8, color="white", ha="center", va="center",
                        fontweight="bold",
                        bbox=dict(boxstyle="circle,pad=0.25", facecolor=RED, edgecolor="white", lw=0.8))

    # Side panel: what each number is, materials, notes.
    x = 0.79
    fig.text(x, 0.93, "THE FACADE PROPOSAL", fontsize=12, color=INK, fontweight="bold")
    el = {e["name"]: e for e in spec["elements"]}
    pl, hw = spec["pergola"], spec["hot_windows"]
    portal = [el[k] for k in el if k.startswith("Entrance portal") and "soffit" not in k]
    frame = [el[k] for k in el if k.startswith("Garden frame") and "soffit" not in k]
    p_v = (min(e["v"][0] for e in portal), max(e["v"][1] for e in portal))
    p_in = (el["Entrance portal, south leg"]["v"][1], el["Entrance portal, north leg"]["v"][0])
    f_u = (min(e["u"][0] for e in frame), max(e["u"][1] for e in frame))
    band = el["Garden frame, bottom band"]
    eave = el["South eave, roof"]
    canopy = el["South canopy, ground floor"]
    top = max(e["z"][1] for e in portal)
    keyed = [
        (1, f"Entrance portal (road): warm split face stone frame, {p_v[1] - p_v[0]:.2f} m wide "
            f"outside and {p_in[1] - p_in[0]:.2f} m inside, from the ground to +{top:.2f} (the "
            "parapet top), around the double height porch and the 2.40 x 4.50 m pivot door with "
            "glass above (12i). Timber soffit, LED on the inner edge (render A-02-001)."),
        (2, f"Garden frame: stone box around the tall glass of the double height living room, "
            f"{f_u[1] - f_u[0]:.2f} m deep. Its bottom band shades the living room glass "
            f"{band['u'][1] - band['u'][0]:.2f} m deep. Timber soffits, LED on the inner edge "
            "(render A-02-101)."),
        (3, f"South (SSW) face: deep eaves, {eave['v'][1] - eave['v'][0]:.2f} m at the roof and "
            f"{canopy['v'][1] - canopy['v'][0]:.2f} m over the ground floor, timber soffits "
            "(the face with the most sun over the year)."),
        (4, "Carport: the three columns clad in stone, LED along the fascia (render A-02-001)."),
        (5, f"Windows on the hot faces (road and south): projecting render surrounds "
            f"{hw['surround_depth_m']:.2f} m deep, so the glass sits in a deep reveal; vertical "
            f"timber fins at {hw['fin_spacing_m']:.2f} m on the road face's windows "
            f"{hw['fins_min_width_m']:.2f} m wide or more, against the low afternoon sun."),
        (6, f"Roof pergola (R1 B, R2 A): open timber louvres on posts, "
            f"{pl['u'][1] - pl['u'][0]:.2f} x {pl['v'][1] - pl['v'][0]:.2f} m, above the garden "
            "frame, set back from the roof edge; no stair or lift to the roof (D-017), a hatch for "
            f"maintenance. Top +{pl['z_top']:.2f}, TO VERIFY (OI-28)."),
    ]
    y = 0.905
    for no, txt in keyed:
        fig.text(x, y, str(no), fontsize=8, color="white", fontweight="bold", ha="center", va="top",
                 bbox=dict(boxstyle="circle,pad=0.25", facecolor=RED, edgecolor="white"))
        y = _wrap(fig, x + 0.012, y, txt, 70)
        y -= 0.006
    y -= 0.008
    fig.text(x, y, "MATERIALS (visual concept finishes, not a specification)", fontsize=8.5,
             color=INK, fontweight="bold")
    y -= 0.018
    for k in ("render", "stone", "timber", "glass", "frame", "led"):
        m = spec["materials"][k]
        fig.patches.append(Rectangle((x, y - 0.004), 0.012, 0.010, transform=fig.transFigure,
                                     facecolor=m["colour"], edgecolor=INK, lw=0.5))
        fig.text(x + 0.017, y, m["label"], fontsize=7.5, color=INK, va="center")
        y -= 0.016
    y -= 0.008
    extra = [
        "The house is the IFC model as built (first floor D-050); the numbered parts are "
        "brief/facade.yaml, drawn over it. Nothing here is built in the 3D model yet.",
        *spec["changes_to_model"],
        "No GFA change: the facade parts are cladding, eaves and an open pergola.",
        f"Height: DDA FAQs Building Q29 may limit a G+1 villa to 8.40 m to its last point "
        f"(OI-13, open). The house is already {float(h['overall_m']):.2f} m to the parapet top "
        f"(D-030); the portal and the frame stay at that line, the pergola reaches "
        f"{pl['z_top']:.2f} m. TO VERIFY with the consultant.",
        "Whether DDA lets eaves, surrounds and cladding project into the 3 m setback is "
        "TO VERIFY (OI-29). Parapet 1.20 m, DDA FAQs Building Q34 (brief/massing.yaml).",
    ]
    if outside:
        extra.append("Outside the 3 m setback line: " + ", ".join(sorted(set(outside))) +
                     ". The carport already stands there (D-044, TO VERIFY).")
    extra += [n.replace("it would clash with the facade elements",
                        "the portal's north leg shades it instead") for n in notes]
    # Notes in two columns under the elevations.
    fig.text(0.02, 0.228, "NOTES", fontsize=8.5, color=INK, fontweight="bold")
    half = (len(extra) + 1) // 2
    for col, chunk in ((0.02, extra[:half]), (0.40, extra[half:])):
        yy = 0.211
        for txt in chunk:
            yy = _wrap(fig, col, yy, "- " + txt, 125)
            yy -= 0.004

    fig.text(0.975, 0.030, "CONCEPT DESIGN, NOT FOR CONSTRUCTION", fontsize=11, color=RED,
             ha="right", fontweight="bold")
    fig.text(0.975, 0.016, "Sketch VJH-SK-017   Facade elevations, answer R3   Rev A   "
             "A2 landscape, scale bar   Villa 5130272, Saih Shuaib 1, Jebel Ali Hills",
             fontsize=7.5, color=MUTED, ha="right")
    fig.text(0.02, 0.016, "Orthographic elevations drawn from the IFC model and brief/facade.yaml "
             "by src/drawings/sketch_facade.py. Edges, recess shading and LED glow are "
             "illustrative.", fontsize=7.5, color=MUTED)

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, facecolor="white", dpi=200)
    fig.savefig(OUT_PNG, facecolor="white", dpi=110)
    plt.close(fig)
    print(f"PDF  {OUT_PDF.relative_to(REPO_ROOT)}")
    print(f"PNG  {OUT_PNG.relative_to(REPO_ROOT)}")
    for n in notes:
        print("NOTE", n)
    print("outside envelope:", sorted(set(outside)))
    return 0


def _wrap(fig, x, y, text, width) -> float:
    import textwrap
    for line in textwrap.wrap(text, width):
        fig.text(x, y, line, fontsize=7.5, color=INK, va="top")
        y -= 0.0135
    return y


if __name__ == "__main__":
    sys.exit(main())
