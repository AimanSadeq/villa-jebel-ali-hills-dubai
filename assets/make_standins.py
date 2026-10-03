"""Stand-in textures and sky for testing the realism pipeline without network.

Writes synthetic (not photographic) texture maps and a gradient sky to
viewer/public/assets/ in exactly the layout fetch_assets.py produces, with
index.json marked "standin": true, so the viewer code can be exercised where
Poly Haven cannot be reached (the cloud sessions). They are NOT the real
assets: run assets/fetch_assets.py on the laptop to replace them.

    python assets/make_standins.py

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import yaml
from PIL import Image
from scipy import ndimage

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "assets" / "manifest.yaml"
OUT = REPO_ROOT / "viewer" / "public" / "assets"
N = 512
BASE = {"limestone_floor": (0.84, 0.78, 0.66), "travertine": (0.84, 0.76, 0.62), "marble_white": (0.93, 0.92, 0.90),
        "marble_black": (0.12, 0.12, 0.12), "oak_floor": (0.78, 0.63, 0.44), "walnut": (0.42, 0.28, 0.18),
        "terrazzo": (0.80, 0.79, 0.76), "concrete_smooth": (0.66, 0.65, 0.63), "plaster_white": (0.95, 0.94, 0.92),
        "paint_greige": (0.84, 0.81, 0.76), "fabric": (0.82, 0.78, 0.70), "leather": (0.55, 0.35, 0.22),
        "beige_render": (0.86, 0.80, 0.69), "split_face_stone": (0.76, 0.66, 0.50), "timber": (0.58, 0.40, 0.25),
        "lawn": (0.40, 0.56, 0.26), "soil": (0.40, 0.32, 0.24), "paving": (0.76, 0.74, 0.69),
        "terrace_stone": (0.82, 0.77, 0.68)}


def maps(key: str, seed: int):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:N, 0:N].astype(float)
    n1 = ndimage.gaussian_filter(rng.standard_normal((N, N)), 3)
    n2 = ndimage.gaussian_filter(rng.standard_normal((N, N)), 14)
    n = (n1 / np.abs(n1).max() + n2 / np.abs(n2).max()) / 2
    base = np.array(BASE.get(key, (0.7, 0.7, 0.7)))
    t = 1 + 0.10 * n
    if key in ("limestone_floor", "terrace_stone", "paving", "travertine"):
        t[(yy % 128) < 2] *= 0.8
        t[(xx % 256) < 2] *= 0.8
    if key in ("oak_floor", "walnut", "timber"):
        g = ndimage.gaussian_filter(rng.standard_normal((N, N)), (1, 30))
        t = 1 + 0.12 * np.sin(yy * 0.35 + 4 * g / np.abs(g).max())
        t[(yy % 64) < 2] *= 0.8
    if key in ("marble_white", "marble_black"):
        vein = np.abs(np.sin(xx * 0.03 + yy * 0.05 + 6 * n2 / np.abs(n2).max()))
        t = 1 + (0.9 if key == "marble_black" else -0.25) * np.clip(1 - vein * 8, 0, 1)
    if key == "terrazzo":
        for _ in range(900):
            cx, cy, r = rng.integers(0, N), rng.integers(0, N), rng.uniform(1, 5)
            m = (xx - cx) ** 2 + (yy - cy) ** 2 < r * r
            t[m] = rng.choice([0.5, 0.75, 1.15])
    if key == "lawn":
        t = 1 + 0.25 * n1 / np.abs(n1).max()
    diff = np.clip(base * t[..., None], 0, 1)
    rough = np.clip(0.6 + 0.2 * n, 0, 1)
    h = ndimage.gaussian_filter(t, 1)
    gy, gx = np.gradient(h)
    nor = np.stack([0.5 - 4 * gx, 0.5 + 4 * gy, np.ones_like(h)], -1)
    nor = np.clip(nor / np.linalg.norm(nor, axis=-1, keepdims=True) * 0.5 + 0.5, 0, 1)
    return diff, nor, rough


def write_hdr(path: Path, w: int = 512, h: int = 256, dusk: bool = False) -> None:
    """A gradient sky in Radiance RGBE, flat (uncompressed) scanlines."""
    y = np.linspace(1, -1, h)[:, None] * np.ones((1, w))
    up = np.clip(y, 0, 1)
    if dusk:
        rgb = np.stack([0.9 + 0.3 * (1 - up), 0.55 + 0.2 * up, 0.45 + 0.4 * up], -1) * (0.15 + 0.15 * up)[..., None]
    else:
        rgb = np.stack([0.45 + 0.3 * (1 - up), 0.62 + 0.2 * (1 - up), np.ones_like(up)], -1) * (0.35 + 0.35 * (1 - up))[..., None]
    rgb[y < 0] = [0.16, 0.15, 0.13]
    m = rgb.max(-1)
    e = np.where(m > 1e-32, np.ceil(np.log2(np.maximum(m, 1e-32))), 0)
    scale = np.where(m > 1e-32, 256.0 / np.exp2(e), 0)
    rgbe = np.zeros((h, w, 4), np.uint8)
    rgbe[..., :3] = np.clip(rgb * scale[..., None], 0, 255).astype(np.uint8)
    rgbe[..., 3] = np.where(m > 1e-32, e + 128, 0).astype(np.uint8)
    with open(path, "wb") as f:
        f.write(b"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n")
        f.write(f"-Y {h} +X {w}\n".encode())
        f.write(rgbe.tobytes())


def main() -> int:
    man = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    index = {"generated": date.today().isoformat(), "standin": True,
             "source": "Synthetic stand-ins from assets/make_standins.py, not the real assets",
             "hdri": {}, "textures": {}, "models": {}}
    (OUT / "hdri").mkdir(parents=True, exist_ok=True)
    for key, dusk in (("sky_day", False), ("sky_dusk", True)):
        p = OUT / "hdri" / f"standin_{key}.hdr"
        write_hdr(p, dusk=dusk)
        index["hdri"][key] = {"path": f"assets/hdri/{p.name}", "id": "standin"}
    for i, (key, spec) in enumerate(man["textures"].items()):
        folder = OUT / "textures" / f"standin_{key}"
        folder.mkdir(parents=True, exist_ok=True)
        diff, nor, rough = maps(key, i + 1)
        entry = {"id": f"standin_{key}", "scale_m": float(spec.get("scale_m", 2.0))}
        for mk, arr in (("diff", diff), ("nor", nor), ("rough", rough)):
            p = folder / f"{key}_{mk}.jpg"
            Image.fromarray((arr * 255).astype(np.uint8) if arr.ndim == 3 else
                            (arr * 255).astype(np.uint8)).convert("RGB").save(p, quality=85)
            entry[mk] = f"assets/textures/{folder.name}/{p.name}"
        index["textures"][key] = entry
    (OUT / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"stand-ins: {OUT.relative_to(REPO_ROOT)}/index.json ({len(index['textures'])} textures, 2 skies)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
