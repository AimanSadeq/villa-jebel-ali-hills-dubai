"""Indicative clear heights of the rooms, for every label that shows a room
size (CLAUDE.md working rule 9, D-045): the floor plans, the viewer and the
reports. Values from brief/massing.yaml (D-030) and the reference levels; not
regulatory values.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

from shapely.geometry import box

from model.massing import load_massing


def clear_heights(lay: dict) -> dict:
    """Indicative clear heights, brief/massing.yaml (D-030): floor to floor less
    the slab and the ceiling services zone. Not regulatory values."""
    h = load_massing()["heights"]
    hg, hf = float(h["ground_floor_m"]), float(h["first_floor_m"])
    slab, serv = float(h.get("slab_m", 0.30)), float(h.get("services_zone_m", 0.15))
    lv = lay.get("levels", {})
    carport = (float(lv["carport_roof_m"]) - float(lv["carport_ffl_above_gate_m"]) - slab
               if lv else hg - slab - serv)
    return {"ground": hg - slab - serv, "first": hf - slab - serv,
            "double": hg + hf - slab - serv, "carport": carport}


def room_height_text(r: dict, storey: str, lay: dict, H: dict) -> str:
    """CLAUDE.md rule 9: the clear height on every room label."""
    key = r["key"]
    if storey == "ground" and key == "garage":
        return f"h {H['carport']:.2f} m"
    if storey == "ground" and key in (lay.get("double_height") or []):
        return f"h {H['double']:.2f} m"
    if storey == "ground":
        voids = [v for v in lay["floors"]["first"].get("voids", []) if v["area_m2"] > 0.01]
        room = box(r["u"][0], r["v"][0], r["u"][1], r["v"][1])
        under = sum(room.intersection(box(v["u"][0], v["v"][0], v["u"][1], v["v"][1])).area
                    for v in voids)
        if under > 0.95 * room.area:
            return f"h {H['double']:.2f} m"
        if under > 0.30 * room.area:
            return f"h {H['double']:.2f} m under the void, {H['ground']:.2f} m elsewhere"
    return f"h {H[storey]:.2f} m"
