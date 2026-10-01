"""Generate the plan 2 room layout for Villa 5130272 and write brief/layouts.yaml.

Rooms are packed into bands rather than placed by hand. A band is a strip of a
wing running along its length; each room takes a slice of that length equal to
its target area divided by the band depth. Small rooms that would come out
absurdly thin are paired into a sub-band that splits across the depth instead.

Doing it this way means the areas come out right by construction, and the only
judgement left is which room goes in which band and in what order, which is the
architectural decision.

Run: .\\.venv\\Scripts\\python.exe src/model/layout_gen.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis.gfa_check import rooms  # noqa: E402

OUT = REPO_ROOT / "brief" / "layouts.yaml"

T_EXT = 0.25        # external wall
T_INT = 0.15        # internal partition

# Wing footprints in the plot grid, sized by src/analysis/plan_feasibility.py
# for plan direction 2 with the two car garage.
ROAD_WING = {"u": [3.05, 13.45], "v": [3.40, 30.40]}     # 10.40 x 27.00
SSW_WING = {"u": [13.45, 27.35], "v": [3.40, 11.70]}     # 13.90 x  8.30
FIRST_FLOOR = {"u": [3.05, 13.45], "v": [3.40, 28.43]}   # 10.40 x 25.03


@dataclass
class Slot:
    """One entry in a band: a single room, or a pair split across the depth."""
    keys: list[str]
    label: str = ""
    grow: bool = False          # absorb leftover length in the band

    @property
    def is_pair(self) -> bool:
        return len(self.keys) == 2


@dataclass
class Band:
    name: str
    u: list[float]              # depth range
    v: list[float]              # length range
    slots: list[Slot] = field(default_factory=list)
    note: str = ""

    @property
    def depth(self) -> float:
        return self.u[1] - self.u[0]

    @property
    def length(self) -> float:
        return self.v[1] - self.v[0]


# A garage target is a gross footprint, including its share of the surrounding
# walls, where every other room target is a net internal area. Packing it at 38
# would hand it the wall thickness twice. 31.3 m2 internal sits inside a 6.15 x
# 6.05 m footprint, which is the 38 m2 gross the program carries. It still holds
# two DDA standard bays: 5.55 m of width is 2.78 m each against a 2.50 m minimum.
GROSS_TARGETS = {"garage": 31.3}


def targets() -> dict[str, float]:
    out = {r.key: r.low_m2 for r in rooms()}
    out.update(GROSS_TARGETS)
    return out


def gross_targets() -> dict[str, float]:
    """The figures the GFA check uses, before the internal conversion above."""
    return {r.key: r.low_m2 for r in rooms()}


def pack(band: Band, area: dict[str, float]) -> tuple[list[dict], float]:
    """Lay the band's slots out along its length. Returns rooms and slack."""
    needed = sum(area[k] for s in band.slots for k in s.keys)
    span = needed / band.depth
    partitions = T_INT * max(len(band.slots) - 1, 0)
    slack = band.length - span - partitions
    if slack < -1e-6:
        raise ValueError(
            f"band {band.name!r} is {-slack:.2f} m short: it needs "
            f"{span + partitions:.2f} m of length and has {band.length:.2f} m"
        )

    out: list[dict] = []
    v = band.v[0]
    for i, slot in enumerate(band.slots):
        slot_area = sum(area[k] for k in slot.keys)
        length = slot_area / band.depth
        if slot.grow:
            length += slack          # one slot may absorb the leftover
        if slot.is_pair:
            # Split across the depth, proportionally, so neither room is a slot.
            a0, a1 = (area[k] for k in slot.keys)
            d0 = band.depth * a0 / (a0 + a1)
            out.append({"key": slot.keys[0],
                        "u": [band.u[0], round(band.u[0] + d0 - T_INT / 2, 3)],
                        "v": [round(v, 3), round(v + length, 3)]})
            out.append({"key": slot.keys[1],
                        "u": [round(band.u[0] + d0 + T_INT / 2, 3), band.u[1]],
                        "v": [round(v, 3), round(v + length, 3)]})
        else:
            out.append({"key": slot.keys[0],
                        "u": [band.u[0], band.u[1]],
                        "v": [round(v, 3), round(v + length, 3)]})
        v += length + (T_INT if i < len(band.slots) - 1 else 0.0)
    return out, slack


def internal(wing: dict) -> dict:
    return {"u": [wing["u"][0] + T_EXT, wing["u"][1] - T_EXT],
            "v": [wing["v"][0] + T_EXT, wing["v"][1] - T_EXT]}


def ground_bands() -> list[Band]:
    r = internal(ROAD_WING)      # u 3.30 to 13.20, v 3.65 to 30.15
    s = internal(SSW_WING)       # u 13.70 to 27.10, v 3.65 to 11.45

    # The garage sits full depth at the north end, next to the driveway, so the
    # banded part of the road wing stops short of it.
    band_v_top = 24.45

    return [
        Band("Road wing, west band", [r["u"][0], 8.90], [r["v"][0], band_v_top],
             [Slot(["guest_bedroom"]),
              Slot(["laundry", "guest_powder"], "service pair"),
              Slot(["home_office"]),
              Slot(["stair_lift_ground"]),
              Slot(["entrance_foyer"], grow=True)],
             note="Road side, WNW. The hot face, so the rooms that need least "
                  "glazing and the entrance, which is shaded by its own recess."),
        Band("Road wing, east band", [9.00, r["u"][1]], [r["v"][0], band_v_top],
             [Slot(["arabic_kitchen"]),
              Slot(["pantry"]),
              Slot(["sunroom"]),
              Slot(["majlis"], grow=True),
              Slot(["plant_room"])],
             note="Courtyard side, ESE. The cheap face to glaze, so the rooms "
                  "that want light and a view onto the pool."),
        Band("Road wing, north block", [r["u"][0], 8.95], [24.60, r["v"][1]],
             [Slot(["garage"], grow=True)],
             note="Two bays, entered from the driveway on the road face."),
        Band("Road wing, staff strip", [9.10, r["u"][1]], [24.60, r["v"][1]],
             [Slot(["drivers_room"]), Slot(["maids_room"], grow=True)],
             note="Staff zone beside the garage, with its own service access."),
        Band("SSW wing, west", [s["u"][0], 20.75], [s["v"][0], s["v"][1]],
             [Slot(["show_kitchen"]), Slot(["dining"], grow=True)],
             note="Show kitchen backs onto the Arabic kitchen across the wing "
                  "junction. Dining opens to the courtyard."),
        Band("SSW wing, east", [20.90, s["u"][1]], [s["v"][0], s["v"][1]],
             [Slot(["living"], grow=True)],
             note="Living room, double height, open on two faces."),
    ]


def first_bands() -> list[Band]:
    f = internal(FIRST_FLOOR)    # u 3.30 to 13.20, v 3.65 to 28.18
    master_top = 10.78
    return [
        Band("First floor, master suite", [f["u"][0], f["u"][1]],
             [f["v"][0], master_top],
             [Slot(["master_suite"], grow=True)],
             note="Full depth at the south end, so it reads as a suite rather "
                  "than a bedroom off a corridor."),
        Band("First floor, west band", [f["u"][0], 7.60], [master_top, f["v"][1]],
             [Slot(["bedroom_2"]), Slot(["bedroom_3"]),
              Slot(["stair_lift_first"], grow=True)],
             note="Road side. Bedrooms here take deep reveals on the WNW face."),
        Band("First floor, east band", [9.00, f["u"][1]], [master_top, f["v"][1]],
             [Slot(["bedroom_4"]), Slot(["family_living"]),
              Slot(["linen_storage"], grow=True)],
             note="Courtyard side, overlooking the pool. Family living is set "
                  "away from the master suite for the acoustic separation "
                  "CLAUDE.md section 4 asks for."),
    ]


def corridor(name: str, u: list[float], v: list[float]) -> dict:
    return {"name": name, "u": [round(x, 3) for x in u],
            "v": [round(x, 3) for x in v],
            "area_m2": round((u[1] - u[0]) * (v[1] - v[0]), 2)}


def build() -> dict:
    area = targets()
    out: dict = {
        "meta": {
            "stamp": "CONCEPT DESIGN, NOT FOR CONSTRUCTION",
            "phase": 2,
            "massing_option": "C",
            "plan_direction": "plan2",
            "note": "Generated by src/model/layout_gen.py. Do not edit by hand. "
                    "Room names and target areas come from brief/program.yaml.",
            "wall_external_m": T_EXT,
            "wall_internal_m": T_INT,
        },
        "wings": {"road": ROAD_WING, "ssw": SSW_WING, "first": FIRST_FLOOR},
        "floors": {},
    }

    for floor, bands in (("ground", ground_bands()), ("first", first_bands())):
        placed, band_meta = [], []
        for b in bands:
            rs, slack = pack(b, area)
            placed.extend(rs)
            band_meta.append({"name": b.name, "depth_m": round(b.depth, 3),
                              "slack_m": round(slack, 3), "note": b.note})
        out["floors"][floor] = {"bands": band_meta, "rooms": placed}

    # Circulation. Plan 2's whole point: a short service spine on the ground,
    # a full corridor only upstairs where bedrooms demand one.
    out["floors"]["ground"]["circulation"] = [
        corridor("Service spine", [8.90, 9.00], [3.65, 24.45]),
    ]
    out["floors"]["first"]["circulation"] = [
        corridor("Bedroom corridor", [7.60, 9.00], [10.72, 28.18]),
    ]
    return out


def main() -> int:
    data = build()
    OUT.write_text(yaml.safe_dump(data, sort_keys=False, width=88),
                   encoding="utf-8")
    area = targets()
    print(f"Wrote {OUT.relative_to(REPO_ROOT)}")
    for floor in ("ground", "first"):
        rs = data["floors"][floor]["rooms"]
        net = sum((r["u"][1] - r["u"][0]) * (r["v"][1] - r["v"][0]) for r in rs)
        tgt = sum(area[r["key"]] for r in rs)
        print(f"  {floor:<8}{len(rs):>3} rooms   drawn {net:7.2f} m2   "
              f"target {tgt:7.2f} m2   {net - tgt:+6.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
