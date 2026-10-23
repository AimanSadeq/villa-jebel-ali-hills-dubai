"""Flood fill over the exported walk zones (D-049): the rooms the walker reaches
from the front door, the same rule the viewer applies (walk.ts standAt).

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""
import json, math
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from pathlib import Path
m = json.load((Path(__file__).resolve().parents[1] / "viewer" / "public" / "data" / "model.json").open())
w = m["walk"]
zones = []
for z in w["zones"]:
    rings = z["rings"]
    poly = Polygon(rings[0], rings[1:])
    zones.append((z, poly))
R, STEP = w["radius_m"], w["step_m"]
def z_at(zone, u, v):
    if zone["kind"] == "flat": return zone["z"]
    (a, b), (c, d) = zone["p0"], zone["p1"]
    du, dv = c - a, d - b
    t = max(0, min(1, ((u - a) * du + (v - b) * dv) / (du * du + dv * dv)))
    return zone["z0"] + t * (zone["z1"] - zone["z0"])
def support(u, v, znow):
    best = None
    for z, poly in zones:
        if not poly.contains(Point(u, v)): continue
        zc = z_at(z, u, v)
        if abs(zc - znow) > STEP: continue
        if best is None or abs(zc - znow) < abs(best - znow): best = zc
    return best
ring = [(R * math.cos(i * math.pi / 4), R * math.sin(i * math.pi / 4)) for i in range(8)]
def stand(u, v, znow):
    zc = support(u, v, znow)
    if zc is None: return None
    for du, dv in ring:
        if support(u + du, v + dv, zc) is None: return None
    return zc
G = 0.3          # grid step; 0.2 is exact but three minutes, 0.3 under a minute
start = (w["start"]["u"], w["start"]["v"], w["start"]["z"])
# Grid keys count steps from the start: a plain round(v / G) lands on .5 for
# some starts and Python rounds halves to even, merging neighbouring rows.
# The third key is the height in half metres, so a flight passing over a
# walkable floor (the straight stair's lower flight, D-060) is not merged
# with the floor beneath it.
key = lambda u, v, z: (round((u - start[0]) / G), round((v - start[1]) / G), round(z / 0.5))
seen = {key(*start): start}
frontier = [start]
while frontier:
    u, v, z = frontier.pop()
    for du, dv in ((G, 0), (-G, 0), (0, G), (0, -G)):
        nu, nv = u + du, v + dv
        nz = stand(nu, nv, z)
        if nz is None: continue
        k = key(nu, nv, nz)
        if k in seen: continue
        seen[k] = (nu, nv, nz); frontier.append((nu, nv, nz))
# lift: ground to first in the shaft
lift = Polygon(w["lift"]["rings"][0])
reached_pts = list(seen.values())
rooms = [r for r in m["rooms"] if r.get("rect") and not r.get("sub")]
missing = []
for r in rooms:
    a, b, c, d = r["rect"]
    lv = 1 if r["storey"] == "first" else 0
    if not any(a <= u <= b and c <= v <= d and (0 if z < 2.5 else 1) == lv for u, v, z in reached_pts):
        missing.append((r["storey"], r["key"]))


def reached_rooms():
    out = set()
    for r in rooms:
        a, b, c, d = r["rect"]
        lv = 1 if r["storey"] == "first" else 0
        if any(a <= u <= b and c <= v <= d and (0 if z < 2.5 else 1) == lv for u, v, z in reached_pts):
            out.add((r["storey"], r["key"]))
    return out
