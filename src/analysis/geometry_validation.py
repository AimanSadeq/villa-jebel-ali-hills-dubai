"""Geometry validation of the courtyard villa (D-060): the owner's handover
acceptance tests as geometric assertions, the areas, the private garden
measured from the plan, and the open constraints. Writes
output/reports/geometry_validation.md and the floor overlay sheet
output/plans/floor_overlay.pdf.

Every line is PASS, FAIL or TO VERIFY. A FAIL exits non-zero.

Run: python src/analysis/geometry_validation.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402
from shapely.geometry import Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model.massing import site_to_grid  # noqa: E402
from model.site import buildable_envelope, plot_polygon, sqft  # noqa: E402

LAY = yaml.safe_load((REPO_ROOT / "brief" / "layouts.yaml").read_text(encoding="utf-8"))
PROG = yaml.safe_load((REPO_ROOT / "brief" / "program.yaml").read_text(encoding="utf-8"))
GARDEN = yaml.safe_load((REPO_ROOT / "brief" / "garden.yaml").read_text(encoding="utf-8"))
REPORT = REPO_ROOT / "output" / "reports" / "geometry_validation.md"
OVERLAY = REPO_ROOT / "output" / "plans" / "floor_overlay.pdf"
STAMP = "CONCEPT DESIGN, NOT FOR CONSTRUCTION"


def rb(r):
    return box(r["u"][0], r["v"][0], r["u"][1], r["v"][1])


def rooms(floor):
    f = LAY["floors"][floor]
    return {r["key"]: rb(r) for r in f["rooms"] + f["circulation"]}


def largest_rectangle(poly: Polygon, step: float = 0.25) -> tuple[float, float, float, float]:
    """The largest axis aligned rectangle inside a polygon, by a grid search
    (the garden is nearly axis aligned in the plot grid)."""
    b = poly.bounds
    best = (0.0, b[0], b[1], 0.0, 0.0)
    import numpy as np
    us = np.arange(b[0], b[2], step)
    vs = np.arange(b[1], b[3], step)
    for u0 in us:
        for v0 in vs:
            if not poly.contains(box(u0, v0, u0 + step, v0 + step)):
                continue
            for u1 in us[us > u0 + 2][::-1]:
                for v1 in vs[vs > v0 + 2][::-1]:
                    if (u1 - u0) * (v1 - v0) <= best[0]:
                        break
                    if poly.contains(box(u0, v0, u1, v1)):
                        best = ((u1 - u0) * (v1 - v0), u0, v0, u1 - u0, v1 - v0)
                        break
    return best[1], best[2], best[3], best[4]


def main() -> int:
    lines = ["# Geometry validation, Villa 5130272, the courtyard villa (D-060)", "",
             f"{STAMP}. Generated {date.today().isoformat()} by src/analysis/geometry_validation.py "
             "from brief/layouts.yaml (the plan), brief/program.yaml, brief/garden.yaml and brief/site.yaml.", "",
             "| Check | Result | Measure |", "|---|---|---|"]
    fails = 0

    def row(name, ok, measure, verify=False):
        nonlocal fails
        status = "TO VERIFY" if verify else ("PASS" if ok else "FAIL")
        if not ok and not verify:
            fails += 1
        lines.append(f"| {name} | {status} | {measure} |")

    g, f = rooms("ground"), rooms("first")
    ff = LAY["floors"]["first"]
    voids = {v["key"]: rb(v) for v in ff["voids"]}
    outdoor = {o["key"]: rb(o) for o in ff["outdoor"]}
    env = site_to_grid(buildable_envelope())
    plot = site_to_grid(plot_polygon())

    # 1. The former defect: enclosed over the guest suite and the powder room.
    target = unary_union([g["guest_bedroom"], g["guest_toilet"], g["guest_powder"]])
    enclosed = unary_union(list(f.values())).buffer(0.08, join_style=2).buffer(-0.08, join_style=2)
    cover = target.intersection(enclosed).area / target.area
    opens = unary_union(list(voids.values()) + list(outdoor.values()))
    over = opens.intersection(target).area
    row("First floor enclosed over the guest suite and the powder room", cover > 0.999 and over < 1e-6,
        f"{cover:.1%} covered by first floor rooms; {over:.2f} m2 under a void or terrace "
        f"(the other assistant's images showed a planted roof here; this plan has bedroom 2 and its lobby above)")
    # 2. Three bedrooms, three bathrooms, no linen room, no fourth bedroom.
    beds = sorted(k for k in f if (k.startswith("bedroom_") or k == "master_suite") and not any(x in k for x in ("dress", "toilet")))
    baths = sorted(k for k in f if k.endswith("_toilet"))
    row("Exactly three bedrooms upstairs", beds == ["bedroom_2", "bedroom_3", "master_suite"], ", ".join(beds))
    row("Three dedicated en-suite bathrooms", baths == ["bedroom_2_toilet", "bedroom_3_toilet", "master_toilet"], ", ".join(baths))
    row("No linen room, no fourth bedroom", "linen_storage" not in f and "bedroom_4" not in f,
        "removed on record in brief/program.yaml")
    # 3. Master: walk-in from the bedroom, shower bathroom from the walk-in.
    pairs = {frozenset((d["a"], d["b"])) for d in LAY["doors"] if d["kind"] != "fixed"}
    row("Master walk-in wardrobe integrated, shower only bathroom",
        frozenset(("master_suite", "master_dress")) in pairs and frozenset(("master_dress", "master_toilet")) in pairs,
        f"walk-in {f['master_dress'].area:.1f} m2 and bathroom {f['master_toilet'].area:.1f} m2 off the bedroom "
        f"{f['master_suite'].area:.1f} m2; fittings {', '.join(PROG['interiors']['master_suite']['bathroom']['fittings'])}")
    # 4. Voids kept: courtyard open, foyer double height.
    court = g["courtyard"]
    row("Courtyard open to the sky, about 22 m2", LAY["open_to_sky"] == ["courtyard"] and voids["void_over_courtyard"].equals(court),
        f"{court.bounds[2] - court.bounds[0]:.2f} x {court.bounds[3] - court.bounds[1]:.2f} m, {court.area:.1f} m2 ({sqft(court.area):.0f} sq ft)")
    row("Foyer double height, not infilled", LAY["double_height"] == ["entrance_foyer"] and voids["void_over_foyer"].contains(g["entrance_foyer"].buffer(-0.01)),
        f"void over the foyer {voids['void_over_foyer'].area:.1f} m2, including the stair's upper flight")
    # 5. No gates, open carport.
    c = LAY["plates"]["carport"]
    cw, cd = sorted((c["u"][1] - c["u"][0], c["v"][1] - c["v"][0]))
    row("No vehicle gate, no pedestrian gate", GARDEN["wall"]["gates"] == [] and "road" in GARDEN["wall"]["open_sides"],
        "road side open with a planted edge (brief/garden.yaml); whether Meraas requires a wall or gate is open, OI-14")
    row("Open carport, two cars", cw >= 5.5 and cd >= 5.0, f"{c['u'][1] - c['u'][0]:.1f} x {c['v'][1] - c['v'][0]:.1f} m, "
        f"{(c['u'][1] - c['u'][0]) * (c['v'][1] - c['v'][0]):.1f} m2; two bays of 2.5 x 5.5 m fit; exact SUV size pending")
    # 6. Family living to the garden.
    d15 = next(d for d in LAY["doors"] if d["a"] == "living" and d["b"] == "outside")
    row("Family living opens to the private garden", d15["kind"] == "sliding", f"door {d15['no']}, {d15['width_m']:.1f} m sliding, under the ground floor canopy")
    # 7. One coordinate system, overlap of the two floors.
    gfp, ffp = Polygon(LAY["outlines"]["ground"]), Polygon(LAY["outlines"]["first"])
    cant = ffp.difference(gfp).area
    row("Both floors in one grid, first floor on the ground floor", cant < 0.01,
        f"first floor outline {ffp.area:.1f} m2 inside the ground outline {gfp.area:.1f} m2; cantilever {cant:.2f} m2")
    # 8. Setbacks.
    row("Everything behind the 3 m setback lines", env.buffer(0.01).contains(gfp) and env.buffer(0.01).contains(ffp) and env.buffer(0.01).contains(rb(c)),
        "ground and first outlines, the terrace and the carport inside the envelope")
    # 9. Areas.
    m = LAY["gfa_measured"]
    row("GFA inside the DDA cap", m["total"] <= m["cap"], f"{m['total']:.2f} m2 measured against {m['cap']:.2f} m2, margin {m['margin']:.2f} m2")
    lo, hi = PROG["meta"]["target_enclosed_m2"]
    row("Enclosed area near the handover's 450 to 500 m2", lo <= m["total"] <= hi + 10,
        f"{m['total']:.2f} m2 enclosed over G+1: ground {m['road_wing_ground']:.2f}, first {m['first_floor_less_void']:.2f}; "
        f"courtyard {m['courtyard_open_to_sky_m2']:.2f} and voids {m['first_floor_voids']:.2f} m2 not counted")
    o = m["outside_gfa_to_verify"]
    row("Carport and terrace counted outside GFA", True, f"carport {o['carport_m2']:.2f} m2, master terrace "
        f"{o['first_floor_balconies_terrace_m2']:.2f} m2; whether DDA counts them is open, OI-01", verify=True)
    # 10. The private garden, measured.
    inner = plot.buffer(-float(GARDEN["wall"]["thickness_m"]), join_style=2)
    east = inner.intersection(box(gfp.bounds[2], -5, 50, 50)).difference(gfp.buffer(0.01))
    u0, v0, w, d = largest_rectangle(east)
    row("Private garden east of the house, measured from the plan", east.area >= 240,
        f"{east.area:.1f} m2 ({sqft(east.area):.0f} sq ft) contiguous, bounded by the house, the two neighbours and the landscape plot; "
        f"largest clear rectangle {w:.1f} x {d:.1f} m = {w * d:.0f} m2 at u {u0:.1f}, v {v0:.1f}; "
        f"depth from the house {east.bounds[2] - gfp.bounds[2]:.1f} m, length along the house {gfp.bounds[3] - gfp.bounds[1]:.1f} m. "
        "The earlier boards' 12 x 20 m was not measured; this is.")
    front = inner.intersection(box(-5, -5, gfp.bounds[0], 50)).difference(rb(c).buffer(0.01))
    row("Front garden, measured", True, f"{front.area:.1f} m2 between the road and the house, less the driveway")
    # 11. Stair and code checks, open.
    s = LAY["stair"]
    row("Stair: 28 risers of 179 mm, going 270 mm, straight in two flights", True,
        "headroom 2.20 m over the landing under the gallery; riser, going, headroom and the 1.20 m width "
        "against the Dubai Building Code and the UAE Fire and Life Safety Code, OI-23", verify=True)
    row("Floor to floor 5.00 and 4.00 m, parapet 1.20 m, 10.20 m overall", True,
        "DDA FAQ Q29 may cap the height in metres, OI-13", verify=True)
    row("Carport treatment, SUV swept path, demarcation certificate", True,
        "exact SUV dimensions pending; the plot boundary is the DDA GIS geometry until the certificate arrives, OI-03", verify=True)
    row("Internal bathrooms and the closed prep kitchen", True,
        "mechanical extract rates, OI-25; the prep kitchen takes light and air from the courtyard window, OI-15", verify=True)

    lines += ["", "## Room schedule, measured", "",
              "| Floor | Room | w x l (m) | m2 | sq ft |", "|---|---|---|---|---|"]
    names = {r["key"]: r["name"] for fl in ("ground", "first") for r in PROG[fl]}
    names.update({a["key"]: a["name"] for a in PROG["ancillary"]})
    for fl in ("ground", "first"):
        for r in LAY["floors"][fl]["rooms"] + LAY["floors"][fl]["circulation"]:
            w, l = sorted((r["u"][1] - r["u"][0], r["v"][1] - r["v"][0]))
            lines.append(f"| {fl} | {names.get(r['key'], r['key'].replace('_', ' '))} | {w:.2f} x {l:.2f} | {r['area_m2']:.1f} | {sqft(r['area_m2']):.0f} |")
    lines += ["", "Clear heights: ground floor 4.55 m (foyer 8.55 m under its void), first floor 3.55 m (brief/massing.yaml, D-030).",
              "", f"RESULT: {'PASS' if fails == 0 else f'FAIL ({fails})'}. {STAMP}."]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # The overlay sheet: both floors in one frame, the designated area marked.
    OVERLAY.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    ax.set_aspect("equal")
    for poly, c_, lw in ((plot, "#b3261e", 1.0), (env, "#b8860b", 0.8)):
        ax.plot(*poly.exterior.xy, color=c_, lw=lw, ls="--" if poly is env else "-")
    for k, r in g.items():
        ax.add_patch(plt.Polygon(list(r.exterior.coords), fill=False, ec="#1f6f8b", lw=0.8))
    for k, r in f.items():
        ax.add_patch(plt.Polygon(list(r.exterior.coords), fill=True, fc="#ffb84d", alpha=0.25, ec="#b36b00", lw=0.8))
    for k, r in voids.items():
        ax.add_patch(plt.Polygon(list(r.exterior.coords), fill=True, fc="#9ecae1", alpha=0.4, ec="#1f6f8b", lw=0.8))
    for part in (target.geoms if hasattr(target, "geoms") else [target]):
        ax.add_patch(plt.Polygon(list(part.exterior.coords), fill=False, ec="#2e7d4f", lw=2.5))
    ax.text(target.centroid.x, target.bounds[1] - 0.5, "guest suite and powder room:\nenclosed above (bedroom 2 and its lobby)",
            ha="center", va="top", fontsize=7, color="#2e7d4f")
    ax.text(court.centroid.x, court.centroid.y, "courtyard\nopen to sky", ha="center", va="center", fontsize=7)
    ax.add_patch(plt.Polygon(list(rb(c).exterior.coords), fill=False, ec="#555", lw=0.8, ls=":"))
    ax.set_title("Villa 5130272, floor overlay: ground floor (blue outlines), first floor (orange), voids (light blue). "
                 "Plot grid metres, plot up.", fontsize=8)
    ax.text(0.01, 0.01, STAMP, transform=ax.transAxes, fontsize=8, color="#b3261e")
    ax.set_xlim(-2, 33); ax.set_ylim(-2, 36)
    fig.savefig(OVERLAY, dpi=150); plt.close(fig)
    print(f"wrote {REPORT.relative_to(REPO_ROOT)} and {OVERLAY.relative_to(REPO_ROOT)}: {'PASS' if fails == 0 else 'FAIL'}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
