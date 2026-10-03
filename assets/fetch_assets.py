"""Fetch the free CC0 assets of assets/manifest.yaml from Poly Haven.

Run on the laptop (the cloud sessions have no access to polyhaven.com):
    python assets/fetch_assets.py              textures and skies (stage 1)
    python assets/fetch_assets.py --models     also the 3D models (stage 2)
    python assets/fetch_assets.py --check      only list what it would fetch

Downloads go to viewer/public/assets/ (git ignored). The script writes
assets/LICENSES.md (every asset's page, author and licence, CC0 1.0) and
viewer/public/assets/index.json, which the viewer reads to know what it has.
Preferred asset ids are tried first; when none exists, the manifest's search
(categories and tags) picks the most downloaded match, so a renamed asset
never breaks the fetch. Re-running skips files already present.

Poly Haven API: https://api.polyhaven.com (assets list, files per asset).
Licence of every Poly Haven asset: CC0 1.0, https://polyhaven.com/license.

CONCEPT DESIGN, NOT FOR CONSTRUCTION.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "assets" / "manifest.yaml"
LICENSES = REPO_ROOT / "assets" / "LICENSES.md"
OUT = REPO_ROOT / "viewer" / "public" / "assets"
API = "https://api.polyhaven.com"
MAP_KEYS = {"diff": ("diffuse", "diff"), "nor": ("nor_gl",), "rough": ("rough",), "arm": ("arm",)}


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def download(url: str, path: Path) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"   {url.rsplit('/', 1)[-1]} -> {path.relative_to(REPO_ROOT)}")
    with urllib.request.urlopen(url, timeout=300) as r, open(path, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)


class Catalogue:
    def __init__(self):
        self.lists: dict[str, dict] = {}

    def assets(self, kind: str) -> dict:
        if kind not in self.lists:
            self.lists[kind] = get_json(f"{API}/assets?t={kind}")
        return self.lists[kind]

    def choose(self, spec: dict) -> tuple[str, dict] | None:
        kind = spec["search"]["type"]
        allv = self.assets(kind)
        for pid in spec.get("prefer", []) or []:
            if pid in allv:
                return pid, allv[pid]
        cats = set(spec["search"].get("categories", []) or [])
        tags = [t.lower() for t in spec["search"].get("tags", []) or []]
        best, score_best = None, (-1, -1)
        for aid, meta in allv.items():
            mcats = set(meta.get("categories", []) or [])
            mtags = {t.lower() for t in meta.get("tags", []) or []} | {aid.lower(), meta.get("name", "").lower()}
            if cats and not (cats & mcats):
                continue
            hits = sum(1 for t in tags if any(t in mt for mt in mtags))
            if tags and hits == 0:
                continue
            score = (hits, int(meta.get("download_count", 0)))
            if score > score_best:
                best, score_best = (aid, meta), score
        return best


def pick_file(files: dict, names: tuple[str, ...], res: str, fmt: str) -> str | None:
    for k, v in files.items():
        if k.lower() in names or any(k.lower().startswith(n) for n in names):
            by_res = v.get(res) or next(iter(v.values()), {})
            entry = by_res.get(fmt) or next(iter(by_res.values()), None)
            if entry and "url" in entry:
                return entry["url"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch the walkthrough's CC0 assets.")
    ap.add_argument("--models", action="store_true", help="Also fetch the stage 2 models.")
    ap.add_argument("--check", action="store_true", help="List the choices, download nothing.")
    args = ap.parse_args()
    man = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    res, hres = man["meta"]["resolution"], man["meta"]["hdri_resolution"]
    cat = Catalogue()
    index: dict = {"generated": date.today().isoformat(), "standin": False, "source": man["meta"]["source"],
                   "hdri": {}, "textures": {}, "models": {}}
    licences: list[tuple[str, str, str, str]] = []

    def record(key, aid, meta, kind):
        authors = ", ".join((meta.get("authors") or {}).keys()) or "Poly Haven"
        licences.append((key, kind, f"{aid} by {authors}", f"https://polyhaven.com/a/{aid}"))

    print("Skies")
    for key, spec in man["hdri"].items():
        ch = cat.choose(spec)
        if not ch:
            print(f"   {key}: nothing found, skipped")
            continue
        aid, meta = ch
        files = get_json(f"{API}/files/{aid}")
        url = pick_file(files, ("hdri",), hres, "hdr")
        print(f"   {key}: {aid}")
        if url and not args.check:
            path = OUT / "hdri" / f"{aid}_{hres}.hdr"
            download(url, path)
            index["hdri"][key] = {"path": f"assets/hdri/{path.name}", "id": aid}
        record(key, aid, meta, "HDRI sky")

    print("Textures")
    for key, spec in man["textures"].items():
        ch = cat.choose(spec)
        if not ch:
            print(f"   {key}: nothing found, skipped")
            continue
        aid, meta = ch
        files = get_json(f"{API}/files/{aid}")
        entry = {"id": aid, "scale_m": float(spec.get("scale_m", 2.0))}
        print(f"   {key}: {aid}")
        if not args.check:
            for mk, names in MAP_KEYS.items():
                url = pick_file(files, names, res, "jpg")
                if not url:
                    continue
                path = OUT / "textures" / aid / url.rsplit("/", 1)[-1]
                download(url, path)
                entry[mk] = f"assets/textures/{aid}/{path.name}"
            if "diff" in entry:
                index["textures"][key] = entry
        record(key, aid, meta, "texture")

    if args.models:
        print("Models")
        for key, spec in man["models"].items():
            ch = cat.choose(spec)
            if not ch:
                print(f"   {key}: nothing found, skipped")
                continue
            aid, meta = ch
            files = get_json(f"{API}/files/{aid}")
            gl = files.get("gltf", {})
            by_res = gl.get(res) or next(iter(gl.values()), {})
            entry = by_res.get("gltf") or next(iter(by_res.values()), None)
            print(f"   {key}: {aid}")
            if entry and "url" in entry and not args.check:
                folder = OUT / "models" / aid
                main_path = folder / entry["url"].rsplit("/", 1)[-1]
                download(entry["url"], main_path)
                for rel, inc in (entry.get("include") or {}).items():
                    download(inc["url"], folder / rel)
                index["models"][key] = {"path": f"assets/models/{aid}/{main_path.name}", "id": aid,
                                        "fits": spec.get("fits", [])}
            record(key, aid, meta, "3D model")

    if args.check:
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    lines = ["# Asset licences", "",
             "Free assets used by the walkthrough and the renders (CLAUDE.md section 8). Every asset",
             "below is from Poly Haven and released under CC0 1.0 (public domain dedication,",
             "https://polyhaven.com/license). Fetched by assets/fetch_assets.py from assets/manifest.yaml;",
             f"last fetch {date.today().isoformat()}. The files live in viewer/public/assets/ and are not",
             "committed.", "", "| Use | Kind | Asset | Page |", "|---|---|---|---|"]
    lines += [f"| {k} | {kind} | {who} | {url} |" for k, kind, who, url in licences]
    lines += ["", "CONCEPT DESIGN, NOT FOR CONSTRUCTION."]
    LICENSES.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"index: {OUT.relative_to(REPO_ROOT)}/index.json   licences: {LICENSES.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
