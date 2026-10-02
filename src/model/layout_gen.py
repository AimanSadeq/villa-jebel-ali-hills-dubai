"""Generate the plan 2 room layout for Villa 5130272 and write brief/layouts.yaml.

Rooms are packed into bands. A band is a strip of a wing running along its
length; each room takes a slice of that length equal to its area over the band
depth. Small rooms that would come out absurdly thin are paired across the
depth instead. Areas come out right by construction.

The layout obeys the constraints a real section imposes, which the earlier
costing models did not:

  * The stair and lift core stacks: the first floor core sits directly over the
    ground floor core, so the master suite and the guest bedroom below it share
    one length.
  * The first floor may run over the single storey garage, but not past the end
    of the road wing.
  * The entrance foyer is double height, so the first floor leaves a void over
    it. The void is excluded from GFA, but it still takes plate.

The two band depths are searched, and GFA is then MEASURED from the generated
plates. That measured figure, not a coefficient, is what the cap is tested
against.

Room names and target areas come from brief/program.yaml.

Run: .\\.venv\\Scripts\\python.exe src/model/layout_gen.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analysis.gfa_check import rooms, totals  # noqa: E402
from model.massing import site_to_grid  # noqa: E402
from model.site import buildable_envelope  # noqa: E402

OUT = REPO_ROOT / "brief" / "layouts.yaml"

T_EXT = 0.25
T_INT = 0.15
CORRIDOR = 1.80            # DDA FAQs Building Q12, see OI-21

# Road wing south west external corner, plot grid metres.
U0, V0 = 3.05, 3.40
ROAD_MAX_EXT_LENGTH = 27.00      # envelope usable length, brief/massing.yaml
SSW_V = (3.40, 11.70)            # SSW wing, single storey, from the massing
SSW_INT_DEPTH = 7.80
U_EAST_LIMIT = 27.35             # buildable envelope, east side

GARAGE_DEPTH = 5.65              # 5.5 m car plus clearance, entered from the road
GARAGE_INTERNAL = 31.3           # 38 m2 gross footprint, see brief/program.yaml
# The first floor core must hold the dog-leg stair and the home lift side by
# side: two 0.90 m flights with 0.05 m between them, then 0.05 m and a 1.00 m
# lift shaft. Indicative sizes, TO VERIFY, OI-23. src/model/architecture.py
# builds the stair to the same figures and checks the fit again.
CORE_MIN_DEPTH = 2 * 0.90 + 0.05 + 0.05 + 1.00
MIN_VOID_LENGTH = 2.40           # below this a void reads as a slot, not a volume
MIN_OPEN_JOIN = 2.40             # an open join narrower than this reads as a doorway


@dataclass
class Rect:
    key: str
    u0: float
    u1: float
    v0: float
    v1: float

    @property
    def area(self) -> float:
        return (self.u1 - self.u0) * (self.v1 - self.v0)

    def poly(self):
        from shapely.geometry import box  # noqa: PLC0415
        return box(self.u0, self.v0, self.u1, self.v1)

    def as_dict(self) -> dict:
        return {"key": self.key, "u": [round(self.u0, 3), round(self.u1, 3)],
                "v": [round(self.v0, 3), round(self.v1, 3)],
                "area_m2": round(self.area, 2)}


def areas() -> dict[str, float]:
    out = {r.key: r.low_m2 for r in rooms()}
    # Ancillary rooms of the reference plan (D-040) carry their own targets.
    import yaml as _yaml  # noqa: PLC0415
    prog = _yaml.safe_load((REPO_ROOT / "brief" / "program.yaml").read_text(encoding="utf-8"))
    for a in prog.get("ancillary", []) or []:
        out.setdefault(a["key"], float(a.get("target_m2", 0.0)))
    return out


def _keys(slot) -> tuple:
    return slot if isinstance(slot, tuple) else (slot,)


def natural_length(slots: list, depth: float, a: dict) -> float:
    total = sum(sum(a[k] for k in _keys(s)) for s in slots)
    return total / depth + T_INT * (len(slots) - 1)


def pack(slots: list, u: tuple[float, float], v0: float, a: dict,
         grow_to: float | None = None, grow_key: str | None = None):
    """Pack slots along v. A slot is a key or a (key, key) pair split across u.

    If grow_to is given, the slot holding grow_key absorbs the extra length so
    the band ends exactly there. Returns the rectangles and the band's end.
    """
    depth = u[1] - u[0]
    lengths = [sum(a[k] for k in _keys(s)) / depth for s in slots]
    natural = sum(lengths) + T_INT * (len(slots) - 1)
    if grow_to is not None:
        extra = grow_to - v0 - natural
        if extra < -1e-9:
            raise ValueError("band cannot shrink to fit")
        for i, s in enumerate(slots):
            if grow_key in _keys(s):
                lengths[i] += extra
    out, v = [], v0
    for s, length in zip(slots, lengths):
        if isinstance(s, tuple):
            a0, a1 = a[s[0]], a[s[1]]
            split = u[0] + depth * a0 / (a0 + a1)
            out.append(Rect(s[0], u[0], split - T_INT / 2, v, v + length))
            out.append(Rect(s[1], split + T_INT / 2, u[1], v, v + length))
        else:
            out.append(Rect(s, u[0], u[1], v, v + length))
        v += length + T_INT
    return out, v - T_INT


# Room placement. These lists ARE the architecture; the search only sizes them.
# West band faces the road (WNW, the hot face); east band faces the courtyard,
# or, at its south end, the living room in the SSW wing.
CONFIGS = {
    # Kitchen and dining in the single storey SSW wing, as in VJH-MA-002.
    "ssw_kitchen_dining_living": {
        "G_WEST": ["guest_bedroom", "stair_lift_ground", "home_office",
                   "entrance_foyer"],
        "G_EAST": ["arabic_kitchen", ("pantry", "laundry"), "majlis",
                   ("plant_room", "guest_powder")],
        "G_STAFF": ["drivers_room", "maids_room"],
        "SSW_KITCHEN": ["show_kitchen", "dining"],
        "F_WEST": ["bedroom_2"],
        "F_EAST": ["bedroom_4", "linen_storage", "family_living", "bedroom_3"],
    },
    # Foyer straight after the stair core, so the void stacks over it, with the
    # office beyond it. Laundry joins the staff strip, near the staff zone as
    # CLAUDE.md section 4 asks.
    "foyer_after_stair": {
        "G_WEST": ["guest_bedroom", "stair_lift_ground", "entrance_foyer",
                   "home_office"],
        "G_EAST": ["arabic_kitchen", "pantry", "majlis",
                   ("plant_room", "guest_powder")],
        "G_STAFF": ["drivers_room", "maids_room", "laundry"],
        "SSW_KITCHEN": ["show_kitchen", "dining"],
        "F_WEST": ["bedroom_2"],
        "F_EAST": ["bedroom_4", "linen_storage", "family_living", "bedroom_3"],
    },
    "foyer_after_stair_laundry_east": {
        "G_WEST": ["guest_bedroom", "stair_lift_ground", "entrance_foyer",
                   "home_office"],
        "G_EAST": ["arabic_kitchen", ("pantry", "laundry"), "majlis",
                   ("plant_room", "guest_powder")],
        "G_STAFF": ["drivers_room", "maids_room"],
        "SSW_KITCHEN": ["show_kitchen", "dining"],
        "F_WEST": ["bedroom_2", "bedroom_3"],
        "F_EAST": ["bedroom_4", "linen_storage", "family_living"],
    },
    # As built in VJH-MA-002, but with a single height foyer: no void, so the
    # first floor runs continuously over the road wing.
    "original_single_height_foyer": {
        "G_WEST": ["guest_bedroom", "stair_lift_ground", "entrance_foyer",
                   ("home_office", "guest_powder")],
        "G_WEST_GROW": "home_office",
        "G_EAST": ["arabic_kitchen", "pantry", "majlis"],
        "G_EAST_GROW": "majlis",
        "G_STAFF": ["drivers_room", "maids_room", ("laundry", "plant_room")],
        "SSW_KITCHEN": ["show_kitchen", "dining"],
        "F_WEST": ["bedroom_2", "bedroom_3"],
        "F_EAST": ["bedroom_4", "linen_storage", "family_living"],
        "foyer_void": False,
    },
    # As original_single_height_foyer, with no driver's room (D-028). The maid's
    # room is paired with the outdoor bathroom across the staff strip, so the
    # bathroom lands on the courtyard face and takes its door from outside.
    "c_outdoor_bathroom": {
        "G_WEST": ["guest_bedroom", "stair_lift_ground", "entrance_foyer",
                   ("home_office", "guest_powder")],
        "G_WEST_GROW": "home_office",
        # The link hall connects the corridor straight to the dining room in the
        # single storey wing, so nobody reaches the family rooms through the
        # majlis or the Arabic kitchen.
        "G_EAST": ["arabic_kitchen", "pantry", "hall_link", "majlis"],
        "G_EAST_GROW": "majlis",
        # Laundry and plant first, maid and outdoor bathroom at the north end, so
        # the maid's room gets an outside wall for a window and its own entrance
        # (CLAUDE.md section 4), and the bathroom keeps its courtyard door.
        "G_STAFF": [("laundry", "plant_room"), ("maids_room", "outdoor_bathroom")],
        "SSW_KITCHEN": ["show_kitchen", "dining"],
        "F_WEST": ["bedroom_2", "bedroom_3"],
        "F_EAST": ["bedroom_4", "linen_storage", "family_living"],
        "foyer_void": False,
    },
    # As c_outdoor_bathroom, with the first floor planned around a central
    # family hall (D-032) under the owner's open-plan rule (D-033): no corridor
    # upstairs, every bedroom door opens off the hall. F_WEST and F_EAST are
    # not used by this first floor layout.
    "c_family_hall": {
        "G_WEST": ["guest_bedroom", "stair_lift_ground", "entrance_foyer",
                   ("home_office", "guest_powder")],
        "G_WEST_GROW": "home_office",
        "G_EAST": ["arabic_kitchen", "pantry", "hall_link", "majlis"],
        "G_EAST_GROW": "majlis",
        "G_STAFF": [("laundry", "plant_room"), ("maids_room", "outdoor_bathroom")],
        "SSW_KITCHEN": ["show_kitchen", "dining"],
        "F_WEST": [],
        "F_EAST": [],
        "first_layout": "family_hall",
        "foyer_void": False,
        # Band widths held at the plan approved in Phase 2 (5.10 west, 4.20
        # east), so the first floor change does not reshape the ground floor.
        # Left free, the search narrows the east band to 3.70 m to save area,
        # which makes the majlis a 3.7 m wide gallery.
        "bands": (5.10, 4.20),
    },
    # The owner's reference villa (D-038), transcribed in brief/reference_plan.yaml
    # and placed facing the road, mirrored so the carport takes the south end
    # (answer 7). Built by src/model/reference_plan.py; nothing is packed.
    "reference_mirrored": {"source": "reference_plan"},
    # Central hall plan, owner instruction 2026-10-02 (D-036): a big foyer in
    # the middle of the road wing, the majlis north of it (left on entering),
    # the dining south of it (right), the double height living room straight
    # ahead as a tall single storey block in the courtyard, and the kitchens in
    # the SSW wing beyond the dining. The first floor is the family hall plan.
    # The ground floor is built by build_central_hall; G_WEST and G_EAST are
    # not used.
    "c_central_hall": {
        "G_WEST": [], "G_EAST": [],
        "G_STAFF": [("laundry", "plant_room"), ("maids_room", "outdoor_bathroom")],
        "SSW_KITCHEN": ["arabic_kitchen", "show_kitchen"],   # south to north
        "F_WEST": [], "F_EAST": [],
        "first_layout": "family_hall",
        "ground_layout": "central_hall",
        "foyer_void": False,
        "living_depth_m": 6.00,          # along v; width follows from the area
        # The owner asked for a big foyer (D-036): the hall is held at this
        # depth across the full width, above its 19 m2 program target.
        "hall_depth_m": 3.50,
        # Pool: the Phase 1 position (u 18.50 to 22.50, 10 m along v) moved
        # north so the living room opens onto its deck. D-037, shade re-checked.
        "pool_u": (18.50, 22.50),
        "pool_length_m": 10.0,
        "deck_margin_m": {"side": 2.0, "south": 1.5, "north": 1.0},
    },
    "original_double_height_foyer": {
        "G_WEST": ["guest_bedroom", "stair_lift_ground", "entrance_foyer",
                   ("home_office", "guest_powder")],
        "G_WEST_GROW": "home_office",
        "G_EAST": ["arabic_kitchen", "pantry", "majlis"],
        "G_EAST_GROW": "majlis",
        "G_STAFF": ["drivers_room", "maids_room", ("laundry", "plant_room")],
        "SSW_KITCHEN": ["show_kitchen", "dining"],
        "F_WEST": ["bedroom_2", "bedroom_3"],
        "F_EAST": ["bedroom_4", "linen_storage", "family_living"],
        "foyer_void": True,
    },
    # The SSW wing holds the double height living room alone. Show kitchen and
    # dining move into the road wing, where the first floor above would
    # otherwise leave dead space below it. The show kitchen sits against the
    # living room it opens onto; dining follows it onto the courtyard face.
    # Laundry and plant fill the staff strip beside the garage, which is the
    # service zone CLAUDE.md asks the laundry to be near.
    "ssw_living_only": {
        "G_WEST": ["guest_bedroom", "stair_lift_ground", "entrance_foyer",
                   ("home_office", "guest_powder")],
        "G_WEST_GROW": "home_office",
        "G_EAST": [("arabic_kitchen", "pantry"), "show_kitchen", "dining",
                   "majlis"],
        "G_EAST_GROW": "majlis",
        "G_STAFF": ["drivers_room", "maids_room", ("laundry", "plant_room")],
        "SSW_KITCHEN": [],
        "F_WEST": ["bedroom_2", "bedroom_3"],
        "F_EAST": ["bedroom_4", "linen_storage", "family_living"],
    },
    # Massing option A. One two storey bar on the road edge, garden and pool on
    # the ESE side facing landscape plot 5130274. Living room and foyer are
    # both double height for the owner's high ceilings. Reception rooms face the
    # garden; the majlis sits on the road face beside the foyer, near the
    # entrance as CLAUDE.md asks; the master suite takes the south end full
    # width, over the guest bedroom and the kitchens.
    "A_bar": {
        "massing": "A",
        "G_WEST": ["guest_bedroom", "stair_lift_ground", "entrance_foyer",
                   "majlis", ("home_office", "guest_powder")],
        "G_WEST_GROW": "majlis",
        "G_EAST": [("arabic_kitchen", "pantry"), "show_kitchen", "dining",
                   "living"],
        "G_EAST_GROW": "dining",
        "G_STAFF": ["drivers_room", "maids_room", ("laundry", "plant_room")],
        "F_WEST": ["stair_lift_first", "bedroom_2", "bedroom_3"],
        "F_EAST": ["bedroom_4", "linen_storage", "family_living"],
        "voids": ["entrance_foyer", "living"],
        # Pool deck starts at grid u 18.50 in the Phase 1 option A massing.
        "u_east_max": 18.50,
    },
}
ACTIVE = "reference_mirrored"

F_WEST = ["stair_lift_first", "bedroom_2"]
F_EAST = ["bedroom_4", "linen_storage", "family_living"]
F_OVER_GARAGE = "bedroom_3"
SSW_LIVING = "living"


def family_hall_first(a: dict, uw: tuple, uc: tuple, ue: tuple, v1: float,
                      stair: "Rect") -> tuple[list, list, float]:
    """First floor around a central family hall, D-032.

    South to north, after the master suite:
      * the stair core (fixed: it stacks on the ground floor core), linen
        behind it, and a 1.80 m landing east of it where the top flight arrives;
        the master suite is entered from this landing, not from the family room;
      * bedroom 4 east of the landing, on the line it has today;
      * the family hall: open circulation over the stair and linen, then the
        family room itself across the full width, with the road facade on one
        side and the courtyard and pool on the other. No walls between them;
      * bedrooms 2 and 3 side by side across the rear, doors onto the hall.
    Every size comes from the program: the family room's depth is its target
    area over the full width, and the bedrooms' depth is theirs over half.
    """
    full = ue[1] - uw[0]
    linen = Rect("linen_storage", uw[0], uw[1], stair.v1 + T_INT,
                 stair.v1 + T_INT + a["linen_storage"] / (uw[1] - uw[0]))
    hall_v0 = linen.v1 + T_INT
    arm = Rect("hall_arm", uc[0], uc[1], v1, hall_v0)
    bed4 = Rect("bedroom_4", ue[0], ue[1], v1, v1 + a["bedroom_4"] / (ue[1] - ue[0]))
    fam_v0 = bed4.v1 + T_INT
    if fam_v0 - hall_v0 < CORRIDOR:
        raise ValueError("family hall too short beside bedroom 4")
    hall = Rect("family_hall", uw[0], uc[1], hall_v0, fam_v0)
    fam = Rect("family_living", uw[0], ue[1], fam_v0, fam_v0 + a["family_living"] / full)
    half = (full - T_INT) / 2
    r0 = fam.v1 + T_INT
    depth = max(a["bedroom_2"], a["bedroom_3"]) / half
    bed2 = Rect("bedroom_2", uw[0], uw[0] + half, r0, r0 + depth)
    bed3 = Rect("bedroom_3", uw[0] + half + T_INT, ue[1], r0, r0 + depth)
    return [linen, bed4, fam, bed2, bed3], [arm, hall], r0 + depth


def envelope_north_at(u0: float, u1: float) -> float:
    """Lowest v of the buildable envelope's north edge over a u range."""
    env = site_to_grid(buildable_envelope())
    xs = [x for x in (u0, u1)]
    ys = []
    from shapely.geometry import LineString
    for x in xs:
        cut = LineString([(x, 0.0), (x, 60.0)]).intersection(env)
        ys.append(cut.bounds[3])
    return min(ys)


def build_central_hall(dw: float, de: float, a: dict, cfg: dict) -> dict:
    """Central hall ground floor, D-036. See the config comment."""
    from shapely.geometry import box
    from shapely.ops import unary_union

    a = dict(a)
    a["garage"] = GARAGE_INTERNAL
    W = dw + de + CORRIDOR + 2 * T_INT
    uw = (U0 + T_EXT, U0 + T_EXT + dw)
    uc = (uw[1] + T_INT, uw[1] + T_INT + CORRIDOR)
    ue = (uc[1] + T_INT, uc[1] + T_INT + de)
    vi = V0 + T_EXT
    half = T_INT / 2

    # South end, under the master suite: the guest bedroom on the road side,
    # the dining and pantry on the courtyard side, the entrance gallery between.
    L1 = max(a["guest_bedroom"] / dw, a["master_suite"] / W)
    guest = Rect("guest_bedroom", uw[0], uw[1], vi, vi + L1)
    south_east, _ = pack(["pantry", "dining"], ue, vi, a, grow_to=vi + L1,
                         grow_key="dining")
    v1 = vi + L1 + T_INT

    # The stair core stacks under the first floor core; the office beside it.
    stair = Rect("stair_lift_ground", uw[0], uw[1], v1, v1 + a["stair_lift_ground"] / dw)
    if stair.v1 - stair.v0 < CORE_MIN_DEPTH - 1e-9:
        raise ValueError("ground core too shallow for the stair and lift")
    office = Rect("home_office", ue[0], ue[1], stair.v0, stair.v1)
    if office.area < a["home_office"] - 1e-9:
        raise ValueError("office beside the stair is below its target")
    spine = Rect("corridor", uc[0], uc[1], vi, stair.v1)

    # Majlis zone north of the hall: the majlis across the width, the guest
    # powder room at its road end, both opening off the hall.
    Ln = (a["majlis"] + a["guest_powder"]) / (W - T_INT)
    pw = a["guest_powder"] / Ln

    # North block, single storey: garage beside the staff strip.
    u_gar = (uw[0], uw[0] + GARAGE_DEPTH)
    u_staff = (u_gar[1] + T_INT, ue[1])
    N = max(GARAGE_INTERNAL / GARAGE_DEPTH,
            natural_length(cfg["G_STAFF"], u_staff[1] - u_staff[0], a))

    # First floor, which sets the plate length.
    f_master = [Rect("master_suite", uw[0], ue[1], vi, vi + L1)]
    f_stair, _ = pack(["stair_lift_first"], uw, v1, a)
    if f_stair[0].v1 - f_stair[0].v0 < CORE_MIN_DEPTH - 1e-9:
        raise ValueError("first floor core too shallow for the stair and lift")
    f_rest, f_circ, f_end = family_hall_first(a, uw, uc, ue, v1, f_stair[0])

    hall_min = max(a["entrance_foyer"] / W, float(cfg.get("hall_depth_m", 0.0)))
    ground_need = stair.v1 + T_INT + hall_min + T_INT + Ln + T_INT + N
    road_int_end = max(ground_need, f_end)
    if road_int_end + T_EXT - V0 > ROAD_MAX_EXT_LENGTH + 1e-9:
        raise ValueError("road wing longer than the envelope allows")
    vN = road_int_end - N
    hall = Rect("entrance_foyer", uw[0], ue[1], stair.v1 + T_INT, vN - T_INT - Ln - T_INT)
    powder = Rect("guest_powder", uw[0], uw[0] + pw, hall.v1 + T_INT, vN - T_INT)
    majlis = Rect("majlis", uw[0] + pw + T_INT, ue[1], hall.v1 + T_INT, vN - T_INT)
    g_garage = [Rect("garage", u_gar[0], u_gar[1], vN, vN + N)]
    g_staff, _ = pack(cfg["G_STAFF"], u_staff, vN, a, grow_to=vN + N, grow_key="maids_room")
    road_ext = (U0, ue[1] + T_EXT, V0, road_int_end + T_EXT)

    # SSW wing: the kitchens, stacked south to north in one depth, beyond the
    # dining. The Arabic kitchen takes the south end with its service door.
    s_u0 = road_ext[1]
    s_vi = SSW_V[0] + T_EXT
    keys = cfg["SSW_KITCHEN"]
    k_w = sum(a[k] for k in keys) / (SSW_INT_DEPTH - T_INT * (len(keys) - 1))
    ssw_rooms, _ = pack(keys, (s_u0, s_u0 + k_w), s_vi, a,
                        grow_to=s_vi + SSW_INT_DEPTH, grow_key=keys[-1])
    ssw_ext = (s_u0, s_u0 + k_w + T_EXT, SSW_V[0], SSW_V[1])
    if ssw_ext[1] > U_EAST_LIMIT + 1e-9:
        raise ValueError("SSW wing escapes the envelope")
    dining = next(r for r in south_east if r.key == "dining")
    show = next(r for r in ssw_rooms if r.key == "show_kitchen")
    if min(dining.v1, show.v1) - max(dining.v0, show.v0) < MIN_OPEN_JOIN:
        raise ValueError("dining and show kitchen share too little wall")

    # Living room: a tall single storey block straight ahead of the hall,
    # sharing the SSW wing's north wall, open to the courtyard north and east.
    D = float(cfg["living_depth_m"])
    Lw = a["living"] / D
    living = Rect("living", s_u0, s_u0 + Lw, SSW_V[1], SSW_V[1] + D)
    living_ext = (s_u0, s_u0 + Lw + T_EXT, SSW_V[1] - T_EXT, SSW_V[1] + D + T_EXT)
    if living_ext[1] > U_EAST_LIMIT + 1e-9:
        raise ValueError("living block escapes the envelope")
    if min(hall.v1, living.v1) - max(hall.v0, living.v0) < MIN_OPEN_JOIN:
        raise ValueError("hall and living share too little wall")

    # Pool, north of the living room on its deck.
    pu = cfg["pool_u"]
    m = cfg["deck_margin_m"]
    pool_v0 = living_ext[3] + m["south"]
    pool = (pu[0], pu[1], pool_v0, pool_v0 + cfg["pool_length_m"])
    deck = (pu[0] - m["side"], pu[1] + m["side"], living_ext[3], pool[3] + m["north"])
    if deck[3] > envelope_north_at(deck[0], deck[1]) + 1e-9:
        raise ValueError("pool deck escapes the envelope to the north")
    if deck[0] < road_ext[1] - 1e-9:
        raise ValueError("pool deck runs into the road wing")

    def plate(e):
        return box(e[0], e[2], e[1], e[3])

    road_poly, ssw_poly, living_poly = plate(road_ext), plate(ssw_ext), plate(living_ext)
    first_poly = box(U0, V0, ue[1] + T_EXT, f_end + T_EXT)
    if not first_poly.buffer(-1e-6).within(road_poly):
        raise ValueError("first floor overhangs the ground floor")
    road_g = road_poly.area
    ssw_g = ssw_poly.difference(road_poly).area
    living_g = living_poly.difference(unary_union([road_poly, ssw_poly])).area
    first_g = first_poly.area
    void = Rect("void_over_foyer", uw[0], uw[0], v1, v1)
    stair_f = f_stair[0]
    first_ext = tuple(first_poly.bounds[k] for k in (0, 2, 1, 3))
    ground_poly = unary_union([road_poly, ssw_poly, living_poly])

    return {
        "params": {"dw": dw, "de": de, "W": W, "corridor": CORRIDOR},
        "ground": ([guest] + south_east + [stair, office, hall, powder, majlis]
                   + g_garage + g_staff + ssw_rooms + [living]),
        "ground_circulation": [spine],
        "first": f_master + f_stair + f_rest,
        "first_outline": [[round(x, 3), round(y, 3)] for x, y in first_poly.exterior.coords],
        "ground_outline": [[round(x, 3), round(y, 3)] for x, y in road_poly.exterior.coords],
        "footprint_outline": [[round(x, 3), round(y, 3)] for x, y in ground_poly.exterior.coords],
        "first_circulation": f_circ,
        "voids": [void],
        "plates": {"road": road_ext, "ssw": ssw_ext, "living": living_ext,
                   "first": first_ext},
        "pool": pool, "deck": deck,
        "gfa": {"road": road_g, "ssw": ssw_g, "living": living_g, "first": first_g,
                "void": 0.0, "total": road_g + ssw_g + living_g + first_g},
        "stair_offset": abs(stair.v0 - stair_f.v0),
    }


def build(dw: float, de: float, a: dict | None = None,
          cfg: dict | None = None) -> dict:
    cfg = cfg or CONFIGS[ACTIVE]
    if cfg.get("source") == "reference_plan":
        from model.reference_plan import build_layout  # noqa: PLC0415
        return build_layout()
    if cfg.get("massing") == "A":
        return build_bar(dw, de, a or areas(), cfg)
    if cfg.get("ground_layout") == "central_hall":
        return build_central_hall(dw, de, a or areas(), cfg)
    G_WEST, G_EAST, G_STAFF = cfg["G_WEST"], cfg["G_EAST"], cfg["G_STAFF"]
    SSW_KITCHEN = cfg["SSW_KITCHEN"]
    a = dict(a or areas())
    a["garage"] = GARAGE_INTERNAL
    # A link hall is circulation, not a room: it takes exactly one corridor
    # width of the band's length, whatever the band depth.
    a["hall_link"] = CORRIDOR * de
    W = dw + de + CORRIDOR + 2 * T_INT

    uw = (U0 + T_EXT, U0 + T_EXT + dw)
    uc = (uw[1] + T_INT, uw[1] + T_INT + CORRIDOR)
    ue = (uc[1] + T_INT, uc[1] + T_INT + de)
    vi = V0 + T_EXT

    # Stacking: the guest bedroom below and the master suite above share one
    # length, so the stair cores that follow them line up.
    L1 = max(a["guest_bedroom"] / dw, a["master_suite"] / W)

    a_g = dict(a)
    a_g["guest_bedroom"] = L1 * dw
    if cfg.get("stepped", False):
        # Each band ends where its rooms end and the outline steps. Rejected
        # wherever the first floor would then overhang, which is the test that
        # shows the padding in option C is structural, not template waste.
        g_west, west_end = pack(G_WEST, uw, vi, a_g)
        g_east, east_end = pack(G_EAST, ue, vi, a)
        B_end = max(west_end, east_end)
    else:
        # Both bands run to one line, and the nominated room in the shorter band
        # takes up the difference. That room comes out larger than its brief
        # target, and the excess is reported as padding.
        B_end = vi + max(natural_length(G_WEST, dw, a_g),
                         natural_length(G_EAST, de, a))
        g_west, west_end = pack(G_WEST, uw, vi, a_g, grow_to=B_end,
                                grow_key=cfg.get("G_WEST_GROW", "entrance_foyer"))
        g_east, east_end = pack(G_EAST, ue, vi, a, grow_to=B_end,
                                grow_key=cfg.get("G_EAST_GROW", "majlis"))

    # The link hall belongs with the circulation, not the rooms.
    links = [r for r in g_east if r.key == "hall_link"]
    g_east = [r for r in g_east if r.key != "hall_link"]

    # North block, single storey: garage beside the staff strip.
    vN = B_end + T_INT
    u_gar = (uw[0], uw[0] + GARAGE_DEPTH)
    u_staff = (u_gar[1] + T_INT, ue[1])
    if u_staff[1] - u_staff[0] < 2.6:
        raise ValueError("staff strip too narrow")
    N = max(GARAGE_INTERNAL / GARAGE_DEPTH,
            natural_length(G_STAFF, u_staff[1] - u_staff[0], a))
    g_garage = [Rect("garage", u_gar[0], u_gar[1], vN, vN + N)]
    g_staff, _ = pack(G_STAFF, u_staff, vN, a, grow_to=vN + N, grow_key="maids_room")
    road_int_end = vN + N
    road_ext = (U0, ue[1] + T_EXT, V0, road_int_end + T_EXT)
    if road_ext[3] - road_ext[2] > ROAD_MAX_EXT_LENGTH + 1e-9:
        raise ValueError("road wing longer than the envelope allows")

    # SSW wing, single storey, sized to its rooms at brief size.
    s_u0 = road_ext[1]                         # shares the road wing's east wall
    s_vi = SSW_V[0] + T_EXT
    if SSW_KITCHEN:
        k_w = sum(a[k] for k in SSW_KITCHEN) / (SSW_INT_DEPTH - T_INT * (len(SSW_KITCHEN) - 1))
        ssw_kitchen, _ = pack(SSW_KITCHEN, (s_u0, s_u0 + k_w), s_vi, a,
                              grow_to=s_vi + SSW_INT_DEPTH, grow_key=SSW_KITCHEN[-1])
        l_u0 = s_u0 + k_w + T_INT
    else:
        ssw_kitchen, l_u0 = [], s_u0
    l_w = a[SSW_LIVING] / SSW_INT_DEPTH
    ssw_living = [Rect(SSW_LIVING, l_u0, l_u0 + l_w, s_vi, s_vi + SSW_INT_DEPTH)]
    ssw_ext = (s_u0, l_u0 + l_w + T_EXT, SSW_V[0], SSW_V[1])
    if ssw_ext[1] > U_EAST_LIMIT + 1e-9:
        raise ValueError("SSW wing escapes the envelope")

    # First floor. The void over the double height foyer sits straight after
    # the stair core, so bedroom 2 can run on over the office and the garage
    # roof instead of the foyer stretching underneath it.
    f_master = [Rect("master_suite", uw[0], ue[1], vi, vi + L1)]
    v1 = vi + L1 + T_INT
    stair_g = next(r for r in g_west if r.key == "stair_lift_ground")
    foyer = next(r for r in g_west if r.key == "entrance_foyer")

    f_stair, s_end = pack(["stair_lift_first"], uw, v1, a)
    if f_stair[0].v1 - f_stair[0].v0 < CORE_MIN_DEPTH - 1e-9:
        raise ValueError("first floor core too shallow for the stair and lift")
    if cfg.get("foyer_void", True):
        if foyer.v0 < s_end:
            raise ValueError("foyer must follow the stair core")
        # The void runs from the end of the upper stair to the end of the
        # foyer's brief length, so it also opens over the tail of the stair hall.
        void = Rect("void_over_foyer", uw[0], uw[1], s_end + T_INT,
                    foyer.v0 + a["entrance_foyer"] / dw)
        if void.v1 - void.v0 < MIN_VOID_LENGTH:
            raise ValueError("void too short")
        if void.v1 > foyer.v1 + 1e-9:
            raise ValueError("void overruns the foyer")
        west_start = void.v1 + T_INT
    else:
        # Single height foyer: the first floor runs straight over it.
        void = Rect("void_over_foyer", uw[0], uw[0], s_end, s_end)   # zero area
        west_start = s_end + T_INT
    from shapely.geometry import box
    from shapely.ops import unary_union
    half = T_INT / 2
    if cfg.get("first_layout") == "family_hall":
        f_west_rest, f_circ, f_end = family_hall_first(a, uw, uc, ue, v1, f_stair[0])
        f_east = []
        if f_end > road_int_end + 1e-9:
            raise ValueError("first floor overruns the road wing")
        first_poly = box(U0, V0, ue[1] + T_EXT, f_end + T_EXT)
    else:
        f_west_rest, w_end = pack(cfg["F_WEST"], uw, west_start, a)
        f_east, e_end = pack(cfg["F_EAST"], ue, v1, a)
        f_end = max(w_end, e_end)
        if f_end > road_int_end + 1e-9:
            raise ValueError("first floor overruns the road wing")
        # The first floor steps back where a band ends early, leaving the roof
        # of what is below as open roof. Only what is built counts.
        pieces = [
            box(U0, V0, ue[1] + T_EXT, vi + L1 + half),                    # master
            box(U0, vi + L1, uw[1] + half, w_end + T_EXT),                 # west band
            box(uw[1], vi + L1, ue[0], f_end + T_EXT),                     # corridor
            box(ue[0] - half, vi + L1, ue[1] + T_EXT, e_end + T_EXT),      # east band
        ]
        first_poly = unary_union(pieces)
        f_circ = [Rect("corridor", uc[0], uc[1], v1, f_end)]
    g_corr = Rect("corridor", uc[0], uc[1], vi, B_end)

    def plate(e):
        return (e[1] - e[0]) * (e[3] - e[2])

    road_poly = unary_union([
        box(U0, V0, uw[1] + half, west_end + T_EXT),                 # west band
        box(uw[1], V0, ue[0], B_end + T_EXT),                        # corridor
        box(ue[0] - half, V0, ue[1] + T_EXT, east_end + T_EXT),      # east band
        box(U0, vN - T_INT, ue[1] + T_EXT, road_int_end + T_EXT),    # north block
    ])
    # The first floor may only sit where there is building below it.
    if not first_poly.buffer(-1e-6).within(road_poly):
        raise ValueError("first floor overhangs the ground floor")
    road_g, ssw_g = road_poly.area, plate(ssw_ext)
    first_g = first_poly.area - void.area
    stair_f = f_stair[0]
    first_ext = tuple(first_poly.bounds[k] for k in (0, 2, 1, 3))
    f_rooms = f_master + f_stair + f_west_rest + f_east

    return {
        "params": {"dw": dw, "de": de, "W": W, "corridor": CORRIDOR},
        "ground": g_west + g_east + g_garage + g_staff + ssw_kitchen + ssw_living,
        "ground_circulation": [g_corr] + links,
        "first": f_rooms,
        "first_outline": [[round(x, 3), round(y, 3)] for x, y in first_poly.exterior.coords],
        "ground_outline": [[round(x, 3), round(y, 3)] for x, y in road_poly.exterior.coords],
        "first_circulation": f_circ,
        "voids": [void],
        "plates": {"road": road_ext, "ssw": ssw_ext, "first": first_ext},
        "gfa": {"road": road_g, "ssw": ssw_g, "first": first_g,
                "void": void.area, "total": road_g + ssw_g + first_g},
        "stair_offset": abs(stair_g.v0 - stair_f.v0),
    }


def pack_avoid(slots: list, u: tuple[float, float], v0: float, a: dict,
               blocks: list[tuple[float, float]]):
    """Pack slots along v, stepping each room past any blocked interval.

    Used on the first floor, where a double height room below leaves a void
    that no upper room may sit on.
    """
    depth = u[1] - u[0]
    out, v = [], v0
    for s in slots:
        keys = _keys(s)
        length = sum(a[k] for k in keys) / depth
        moved = True
        while moved:
            moved = False
            for b0, b1 in blocks:
                if v < b1 + T_INT - 1e-9 and v + length > b0 - T_INT + 1e-9:
                    v = b1 + T_INT
                    moved = True
        if isinstance(s, tuple):
            a0, a1 = a[s[0]], a[s[1]]
            split = u[0] + depth * a0 / (a0 + a1)
            out.append(Rect(s[0], u[0], split - T_INT / 2, v, v + length))
            out.append(Rect(s[1], split + T_INT / 2, u[1], v, v + length))
        else:
            out.append(Rect(s, u[0], u[1], v, v + length))
        v += length + T_INT
    return out, v - T_INT


def build_bar(dw: float, de: float, a: dict, cfg: dict) -> dict:
    """Massing option A: one two storey bar along the road edge, garden and
    pool to the east, no single storey wing. Every room listed in
    cfg["voids"] is double height and leaves a void on the first floor."""
    from shapely.geometry import box
    from shapely.ops import unary_union

    a = dict(a)
    a["garage"] = GARAGE_INTERNAL
    W = dw + de + CORRIDOR + 2 * T_INT
    uw = (U0 + T_EXT, U0 + T_EXT + dw)
    uc = (uw[1] + T_INT, uw[1] + T_INT + CORRIDOR)
    ue = (uc[1] + T_INT, uc[1] + T_INT + de)
    vi = V0 + T_EXT
    if ue[1] + T_EXT > cfg["u_east_max"] + 1e-9:
        raise ValueError("bar too wide: it reaches the pool deck")

    L1 = max(a["guest_bedroom"] / dw, a["master_suite"] / W)
    a_g = dict(a)
    a_g["guest_bedroom"] = L1 * dw
    B_end = vi + max(natural_length(cfg["G_WEST"], dw, a_g),
                     natural_length(cfg["G_EAST"], de, a))
    g_west, _ = pack(cfg["G_WEST"], uw, vi, a_g, grow_to=B_end,
                     grow_key=cfg["G_WEST_GROW"])
    g_east, _ = pack(cfg["G_EAST"], ue, vi, a, grow_to=B_end,
                     grow_key=cfg["G_EAST_GROW"])

    vN = B_end + T_INT
    u_gar = (uw[0], uw[0] + GARAGE_DEPTH)
    u_staff = (u_gar[1] + T_INT, ue[1])
    if u_staff[1] - u_staff[0] < 2.6:
        raise ValueError("staff strip too narrow")
    N = max(GARAGE_INTERNAL / GARAGE_DEPTH,
            natural_length(cfg["G_STAFF"], u_staff[1] - u_staff[0], a))
    g_garage = [Rect("garage", u_gar[0], u_gar[1], vN, vN + N)]
    g_staff, _ = pack(cfg["G_STAFF"], u_staff, vN, a, grow_to=vN + N,
                      grow_key=cfg["G_STAFF"][1])
    road_int_end = vN + N
    road_ext = (U0, ue[1] + T_EXT, V0, road_int_end + T_EXT)
    if road_ext[3] - road_ext[2] > ROAD_MAX_EXT_LENGTH + 1e-9:
        raise ValueError("bar longer than the envelope allows")

    # Voids: the full footprint of each double height room below.
    ground_rooms = {r.key: r for r in g_west + g_east}
    voids = [Rect(f"void_over_{k}", ground_rooms[k].u0, ground_rooms[k].u1,
                  ground_rooms[k].v0, ground_rooms[k].v1) for k in cfg["voids"]]
    for vd in voids:
        if vd.v0 < vi + L1 + T_INT - 1e-9:
            raise ValueError("a void falls under the master suite")

    def blocks(u):
        return [(vd.v0, vd.v1) for vd in voids if vd.u0 < u[1] and vd.u1 > u[0]]

    f_master = [Rect("master_suite", uw[0], ue[1], vi, vi + L1)]
    v1 = vi + L1 + T_INT
    f_west, w_end = pack_avoid(cfg["F_WEST"], uw, v1, a, blocks(uw))
    f_east, e_end = pack_avoid(cfg["F_EAST"], ue, v1, a, blocks(ue))
    f_end = max(w_end, e_end)
    if f_end > road_int_end + 1e-9:
        raise ValueError("first floor overruns the bar")

    stair_g = next(r for r in g_west if r.key == "stair_lift_ground")
    stair_f = next(r for r in f_west if r.key == "stair_lift_first")
    if abs(stair_g.v0 - stair_f.v0) > 1e-6:
        raise ValueError("stair cores do not stack")

    half = T_INT / 2
    outline = unary_union([
        box(U0, V0, ue[1] + T_EXT, vi + L1 + half),
        box(U0, vi + L1, uw[1] + half, w_end + T_EXT),
        box(uw[1], vi + L1, ue[0], f_end + T_EXT),
        box(ue[0] - half, vi + L1, ue[1] + T_EXT, e_end + T_EXT),
    ])
    road_poly = box(*[road_ext[k] for k in (0, 2, 1, 3)])
    if not outline.buffer(-1e-6).within(road_poly):
        raise ValueError("first floor overhangs the ground floor")
    void_union = unary_union([box(vd.u0, vd.v0, vd.u1, vd.v1) for vd in voids])
    first_g = outline.area - outline.intersection(void_union).area
    road_g = road_poly.area

    return {
        "params": {"dw": dw, "de": de, "W": W, "corridor": CORRIDOR},
        "ground": g_west + g_east + g_garage + g_staff,
        "ground_circulation": [Rect("corridor", uc[0], uc[1], vi, B_end)],
        "first": f_master + f_west + f_east,
        "first_circulation": [Rect("corridor", uc[0], uc[1], v1, f_end)],
        "first_outline": [[round(x, 3), round(y, 3)] for x, y in outline.exterior.coords],
        "ground_outline": [[round(x, 3), round(y, 3)] for x, y in road_poly.exterior.coords],
        "voids": voids,
        "plates": {"road": road_ext,
                   "first": tuple(outline.bounds[k] for k in (0, 2, 1, 3))},
        "gfa": {"road": road_g, "ssw": 0.0, "first": first_g,
                "void": sum(vd.area for vd in voids),
                "total": road_g + first_g},
        "stair_offset": abs(stair_g.v0 - stair_f.v0),
        "massing": "A",
    }


def search(step: float = 0.05, cfg: dict | None = None) -> dict:
    cfg = cfg or CONFIGS[ACTIVE]
    if cfg.get("source") == "reference_plan":
        return build(0.0, 0.0, cfg=cfg)
    if "bands" in cfg:
        return build(*cfg["bands"], cfg=cfg)
    best = None
    if cfg.get("ground_layout") == "central_hall":
        # The internal width is held at the approved 11.40 m; only the split
        # between the road side band and the courtyard side band is searched.
        W = 11.40
        for i in range(int((5.60 - 4.60) / step) + 1):
            dw = round(4.60 + i * step, 3)
            de = round(W - dw - CORRIDOR - 2 * T_INT, 3)
            try:
                lay = build(dw, de, cfg=cfg)
            except ValueError:
                continue
            if best is None or lay["gfa"]["total"] < best["gfa"]["total"]:
                best = lay
        if best is None:
            raise RuntimeError("no central hall layout satisfies every constraint")
        return best
    for i in range(int((6.40 - 3.80) / step) + 1):
        dw = round(3.80 + i * step, 3)
        for j in range(int((6.40 - 3.00) / step) + 1):
            de = round(3.00 + j * step, 3)
            try:
                lay = build(dw, de, cfg=cfg)
            except ValueError:
                continue
            if best is None or lay["gfa"]["total"] < best["gfa"]["total"]:
                best = lay
    if best is None:
        raise RuntimeError("no layout satisfies every constraint")
    return best


def to_yaml(lay: dict) -> dict:
    t = totals()
    g = lay["gfa"]
    return {
        "meta": {
            "stamp": "CONCEPT DESIGN, NOT FOR CONSTRUCTION",
            "phase": 2,
            "massing_option": lay.get("massing", "C"),
            "plan_direction": {"C": "plan2", "A": "bar"}.get(lay.get("massing", "C"), "reference"),
            "note": "Generated by src/model/layout_gen.py. Do not edit by hand.",
            "corridor_m": CORRIDOR,
            "wall_external_m": T_EXT,
            "wall_internal_m": T_INT,
        },
        "params": {k: round(v, 3) for k, v in lay["params"].items()},
        "plates": {k: {"u": [round(e[0], 3), round(e[1], 3)],
                       "v": [round(e[2], 3), round(e[3], 3)]}
                   for k, e in lay["plates"].items()},
        "gfa_measured": {
            "road_wing_ground": round(g["road"], 2),
            "ssw_wing_ground": round(g["ssw"], 2),
            "living_block_ground": round(g.get("living", 0.0), 2),
            "first_floor_less_void": round(g["first"], 2),
            "void_over_foyer": round(g["void"], 2),
            "total": round(g["total"], 2),
            "cap": t["cap_m2"],
            "margin": round(t["cap_m2"] - g["total"], 2),
            # Reported, outside GFA by owner decision D-039, TO VERIFY (OI-01).
            "outside_gfa_to_verify": {
                "carport_m2": round(g.get("carport", 0.0), 2),
                "lawn_court_m2": round(g.get("lawn_court", 0.0), 2),
                "first_floor_balconies_terrace_m2": round(g.get("first_outdoor", 0.0), 2),
            },
        },
        "outlines": {
            "road_ground": lay["ground_outline"],
            "ground": lay.get("footprint_outline", lay["ground_outline"]),
            "first": lay["first_outline"],
        },
        "reference": lay.get("reference", ""),
        "open_joins": lay.get("open_joins", {}),
        "room_links": lay.get("room_links", []),
        "external_doors": lay.get("external_doors", []),
        "doors": lay.get("doors", []),
        "double_height": lay.get("double_height", []),
        "open_to_sky": lay.get("open_to_sky", []),
        "porches": lay.get("porches", []),
        "levels": lay.get("levels", {}),
        "pool": ({"u": [round(lay["pool"][0], 3), round(lay["pool"][1], 3)],
                  "v": [round(lay["pool"][2], 3), round(lay["pool"][3], 3)]}
                 if "pool" in lay else None),
        "deck": ({"u": [round(lay["deck"][0], 3), round(lay["deck"][1], 3)],
                  "v": [round(lay["deck"][2], 3), round(lay["deck"][3], 3)]}
                 if "deck" in lay else None),
        "padding": [
            {"key": r.key, "over_target_m2": round(r.area - tgt, 2)}
            for r in lay["ground"] + lay["first"]
            for tgt in [GARAGE_INTERNAL if (r.key == "garage" and lay.get("massing", "C") != "R")
                        else areas().get(r.key, 0)]
            if r.area - tgt > 0.5
        ],
        "floors": {
            "ground": {"rooms": [r.as_dict() for r in lay["ground"]],
                       "circulation": [r.as_dict() for r in lay["ground_circulation"]]},
            "first": {"rooms": [r.as_dict() for r in lay["first"]],
                      "circulation": [r.as_dict() for r in lay["first_circulation"]],
                      "voids": [r.as_dict() for r in lay["voids"]],
                      "outdoor": [r.as_dict() for r in lay.get("first_outdoor", [])]},
        },
    }


def main() -> int:
    lay = search()
    data = to_yaml(lay)
    OUT.write_text(yaml.safe_dump(data, sort_keys=False, width=88), encoding="utf-8")
    g, p, a = data["gfa_measured"], data["params"], areas()
    print(f"Wrote {OUT.relative_to(REPO_ROOT)}")
    if p.get("dw"):
        print(f"  bands: west {p['dw']:.2f}, corridor {p['corridor']:.2f}, "
              f"east {p['de']:.2f}, internal width {p['W']:.2f} m")
    else:
        o = g["outside_gfa_to_verify"]
        print(f"  reference plan placed, front at u {p['front_u']:.2f}, mirrored {p['mirror']}; "
              f"outside GFA (TO VERIFY): carport {o['carport_m2']:.2f}, lawn court "
              f"{o['lawn_court_m2']:.2f}, first floor outdoor {o['first_floor_balconies_terrace_m2']:.2f} m2")
    print(f"  GFA measured: road {g['road_wing_ground']:.2f} + SSW "
          f"{g['ssw_wing_ground']:.2f} + living {g['living_block_ground']:.2f} + first "
          f"{g['first_floor_less_void']:.2f} (void {g['void_over_foyer']:.2f} "
          f"excluded) = {g['total']:.2f} m2")
    print(f"  cap {g['cap']:.2f}, margin {g['margin']:+.2f} m2")
    print(f"  stair cores stack to within {lay['stair_offset']:.3f} m")
    for floor in ("ground", "first"):
        print(f"  {floor}:")
        for r in data["floors"][floor]["rooms"]:
            tgt = (GARAGE_INTERNAL if (r["key"] == "garage" and data["meta"]["massing_option"] != "R")
                   else a.get(r["key"], 0))
            w, l = r["u"][1] - r["u"][0], r["v"][1] - r["v"][0]
            print(f"    {r['key']:<20}{w:6.2f} x{l:6.2f} = {r['area_m2']:6.2f}"
                  f"   target {tgt:5.1f}  {r['area_m2'] - tgt:+6.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
