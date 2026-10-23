"""The design board: one page that shows the current design (D-064).

Reads the viewer's model.json (rooms, heights, GFA), brief/layouts.yaml, the
seven concept renders in output/renders/finish_input/, the AI-finished image
links in output/renders/ai_links.yaml and the floor plan sheet, and writes
output/board/: index.html (a complete page for the laptop) and artifact.html
(the same content as a fragment for the hosted page), with the images in
output/board/img/. Rebuild after every design change; the hosted page is
republished from the fragment, so the owner sees the change on the right while
the conversation continues on the left.

Run: python src/drawings/design_board.py
"""
from __future__ import annotations

import html
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "viewer" / "public" / "data" / "model.json"
LAYOUTS = ROOT / "brief" / "layouts.yaml"
LINKS = ROOT / "output" / "renders" / "ai_links.yaml"
INPUTS = ROOT / "output" / "renders" / "finish_input"
PLAN_PDF = ROOT / "output" / "pdf" / "VJH-GA-001_Floor_Plans.pdf"
OUT = ROOT / "output" / "board"
IMG = OUT / "img"
STAMP = "CONCEPT DESIGN, NOT FOR CONSTRUCTION"
WALK_URL = "https://claude.ai/artifact/XG4m7W8hLSKzyAnA1nrVFL"

CIRC_NAMES = {
    "hall": "Hall", "gallery": "Gallery", "gallery_west": "Gallery bridge over the foyer",
    "north_lobby": "North lobby", "salon_lobby": "Salon lobby", "guest_lobby": "Guest lobby",
    "service_corridor": "Service corridor",
}

# The plan sheet (A1 landscape, both floors) rendered at 110 dpi: the two
# plan windows, in pixels of that rendering. Adjust if the sheet layout moves.
PLAN_DPI = 110
PLAN_CROPS = {"ground": (200, 480, 1600, 2200), "first": (1880, 480, 3300, 2200)}


def fmt(x: float, nd: int = 2) -> str:
    return f"{x:,.{nd}f}"


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def plan_images() -> dict[str, str]:
    """Render the plan sheet to img/plan_sheet.jpg and crop the two floors."""
    IMG.mkdir(parents=True, exist_ok=True)
    out: dict[str, str] = {}
    if not PLAN_PDF.exists():
        return out
    try:
        subprocess.run(["pdftoppm", "-r", str(PLAN_DPI), "-jpeg", "-jpegopt", "quality=85",
                        "-singlefile", str(PLAN_PDF), str(IMG / "plan_sheet")],
                       check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        try:
            import fitz  # PyMuPDF, if pdftoppm is not installed
            page = fitz.open(PLAN_PDF)[0]
            page.get_pixmap(dpi=PLAN_DPI).save(IMG / "plan_sheet.jpg")
        except Exception:  # noqa: BLE001
            return out
    out["sheet"] = "img/plan_sheet.jpg"
    try:
        from PIL import Image
        im = Image.open(IMG / "plan_sheet.jpg")
        for key, box in PLAN_CROPS.items():
            im.crop(box).save(IMG / f"plan_{key}.jpg", quality=85)
            out[key] = f"img/plan_{key}.jpg"
    except Exception:  # noqa: BLE001
        pass
    return out


def room_rows(rooms: list[dict], storey: str) -> str:
    rows = []
    for r in sorted((r for r in rooms if r["storey"] == storey and not r.get("sub")),
                    key=lambda r: (bool(r.get("circulation")), -r["area_m2"])):
        name = CIRC_NAMES.get(r["key"], r["name"])
        size = f"{fmt(r['w_m'])} x {fmt(r['l_m'])}" if r.get("w_m") and r.get("l_m") else ""
        height = (r.get("height") or "").replace("h ", "")
        rows.append(
            f"<tr><td>{esc(name)}</td><td class='num'>{size}</td>"
            f"<td class='num'>{fmt(r['area_m2'], 1)}</td><td class='num'>{fmt(r['area_sqft'], 0)}</td>"
            f"<td class='num'>{esc(height)}</td></tr>")
    return "\n".join(rows)


def build() -> tuple[str, str]:
    data = json.loads(MODEL.read_text(encoding="utf-8"))
    layouts = yaml.safe_load(LAYOUTS.read_text(encoding="utf-8"))
    links = yaml.safe_load(LINKS.read_text(encoding="utf-8")) if LINKS.exists() else {"views": {}}
    gfa = layouts["gfa_measured"]
    outside = gfa.get("outside_gfa_to_verify", {})
    heights = data["heights"]
    plans = plan_images()

    # Copy the seven view inputs beside the page.
    views = []
    for key, v in links["views"].items():
        src = INPUTS / v["source"]
        if src.exists():
            shutil.copy(src, IMG / src.name)
        views.append((key, v, f"img/{src.name}" if src.exists() else ""))

    cards = []
    for n, (key, v, img) in enumerate(views, 1):
        pic = f"<img src='{img}' alt='{esc(v['title'])}, concept render' loading='lazy'>" if img else ""
        link = (f"<a class='btn' href='{esc(v['url'])}' target='_blank' rel='noopener'>AI-finished image</a>"
                if v.get("url") else "<span class='muted'>AI-finished image not made yet</span>")
        cards.append(
            f"<figure class='view' id='view-{esc(key)}'>{pic}"
            f"<figcaption><span class='eyebrow'>View {n} of {len(views)}, {esc(v['sun'])}</span>"
            f"<strong>{esc(v['title'])}</strong>{link}</figcaption></figure>")

    built = data["meta"].get("built", "")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    plan_block = ""
    if plans:
        g = plans.get("ground", plans.get("sheet"))
        f = plans.get("first", plans.get("sheet"))
        plan_block = f"""
<div class='plans'>
  <figure><img src='{g}' alt='Ground floor plan' loading='lazy'>
    <figcaption><strong>Ground floor</strong> clear height {fmt(heights['ground_m'] - 0.45)} m, double height over the foyer and the courtyard {fmt(heights['ground_m'] + heights['first_m'] - 0.45)} m</figcaption></figure>
  <figure><img src='{f}' alt='First floor plan' loading='lazy'>
    <figcaption><strong>First floor</strong> clear height {fmt(heights['first_m'] - 0.45)} m</figcaption></figure>
</div>
<p class='note'>Drawing VJH-GA-001 Rev E, scale 1:100 at A1, plot up (north is the arrow on the sheet). <a href='{plans.get('sheet', '')}' target='_blank' rel='noopener'>Whole sheet</a>. Room sizes are width x length in metres, then m2 and sq ft; heights are clear heights.</p>"""

    body = f"""
<header class='top'>
  <div>
    <p class='eyebrow'>Plot 5130272, Saih Shuaib 1, Jebel Ali Hills, Dubai</p>
    <h1>Villa 5130272 Design Board</h1>
    <p class='lede'>The courtyard villa of the redesign (D-060, D-061): white render, a charcoal stone entrance box two storeys tall, an open courtyard with an olive tree in the middle of the house, the garden to the east. This page is rebuilt after every change you ask for.</p>
  </div>
  <dl class='facts'>
    <div><dt>Gross floor area</dt><dd>{fmt(gfa['total'])} m2</dd><dd class='sub'>of {fmt(gfa['cap'])} m2 allowed, margin {fmt(gfa['margin'])} m2</dd></div>
    <div><dt>Ground, first</dt><dd>{fmt(gfa['road_wing_ground'])} + {fmt(gfa['first_floor_less_void'])} m2</dd><dd class='sub'>courtyard {fmt(gfa.get('courtyard_open_to_sky_m2', 0))} m2 and voids {fmt(gfa.get('first_floor_voids', 0))} m2 not counted</dd></div>
    <div><dt>Outside GFA, to verify</dt><dd>{fmt(outside.get('carport_m2', 0))} m2 carport</dd><dd class='sub'>{fmt(outside.get('first_floor_balconies_terrace_m2', 0))} m2 master terrace (OI-01)</dd></div>
    <div><dt>Heights</dt><dd>{fmt(heights['ground_m'])} and {fmt(heights['first_m'])} m floor to floor</dd><dd class='sub'>{fmt(heights['overall_m'])} m overall with the parapet, G+1</dd></div>
  </dl>
</header>

<section id='views'>
  <h2>The seven views</h2>
  <p class='note'>Each card shows the concept render from the model. The button opens the AI-finished version in your Canva account: an impression painted over that render, so it keeps the composition closely but not exactly.</p>
  <div class='grid'>{''.join(cards)}</div>
</section>

<section id='plans'>
  <h2>Plans</h2>{plan_block}
</section>

<section id='rooms'>
  <h2>Rooms</h2>
  <div class='tables'>
    <div><h3>Ground floor</h3><div class='scroll'><table><thead><tr><th>Room</th><th class='num'>w x l (m)</th><th class='num'>m2</th><th class='num'>sq ft</th><th class='num'>Clear height</th></tr></thead><tbody>{room_rows(data['rooms'], 'ground')}</tbody></table></div></div>
    <div><h3>First floor</h3><div class='scroll'><table><thead><tr><th>Room</th><th class='num'>w x l (m)</th><th class='num'>m2</th><th class='num'>sq ft</th><th class='num'>Clear height</th></tr></thead><tbody>{room_rows(data['rooms'], 'first')}</tbody></table></div></div>
  </div>
</section>

<section id='walk'>
  <h2>Walk through the model</h2>
  <p>The browser walkthrough is the checking tool for rooms, routes, the stair and the lift. It shows flat colours, not real materials. <a class='btn' href='{WALK_URL}' target='_blank' rel='noopener'>Open the walkthrough</a></p>
  <p class='note'>In its Walkthrough panel, "Go to a room" sets you down in any room. On the laptop: npm run dev --prefix viewer, then localhost:5173/model.html.</p>
</section>

<section id='next'>
  <h2>Waiting on you</h2>
  <p><strong>R1.</strong> Does the courtyard villa, as the seven views and the plans show it, go in the right direction? Say what to change, room by room or view by view, and the board updates after each change.</p>
</section>

<footer>
  <p><strong>{STAMP}</strong></p>
  <p class='note'>Model built {esc(built)}, board generated {now}. Regulatory values are not invented: anything unverified is marked TO VERIFY in docs/open-items.md. A DDA-registered consultant and a licensed structural engineer must review, complete and stamp all final drawings.</p>
</footer>
"""

    style = """
<style>
/* Layout: one column of sections, a facts strip in the header, a two-column grid for the views and plans on wide screens. */
:root {
  --bg: #f6f3ee; --bg-2: #ecE7df; --fg: #1f1d1a; --muted: #6b665e; --line: #d8d2c8;
  --accent: #52703f; --accent-ink: #ffffff; --stamp: #b4332a;
  --display: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --body: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --mono: "IBM Plex Mono", "Consolas", monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #17191b; --bg-2: #22262a; --fg: #e8e4dd; --muted: #a39d93; --line: #353a40;
  --accent: #9bb882; --accent-ink: #141a10; --stamp: #f07a6e; color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #17191b; --bg-2: #22262a; --fg: #e8e4dd; --muted: #a39d93; --line: #353a40;
  --accent: #9bb882; --accent-ink: #141a10; --stamp: #f07a6e; color-scheme: dark; }
html { background: var(--bg); }
body { margin: 0; background: var(--bg); color: var(--fg); font-family: var(--body); font-size: 15px; line-height: 1.5;
  padding-block: 24px 48px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
main, header.top, section, footer { max-width: 1180px; margin-inline: auto; }
h1, h2, h3 { font-family: var(--display); text-wrap: balance; line-height: 1.15; margin: 0 0 8px; }
h1 { font-size: clamp(26px, 4vw, 38px); font-weight: 600; letter-spacing: -0.01em; }
h2 { font-size: clamp(20px, 2.6vw, 26px); font-weight: 600; margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--line); }
h3 { font-size: 16px; font-weight: 600; margin-top: 12px; }
p { margin: 0 0 10px; max-width: 70ch; }
a { color: var(--accent); }
.eyebrow { font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); display: block; margin-bottom: 6px; }
.lede { font-size: 17px; max-width: 64ch; }
.note, .muted { color: var(--muted); font-size: 14px; }
.facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 20px 0 0; padding: 14px 16px; background: var(--bg-2); border-radius: 8px; }
.facts div { min-width: 0; }
.facts dt { font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); }
.facts dd { margin: 2px 0 0; font-family: var(--mono); font-variant-numeric: tabular-nums; font-size: 18px; }
.facts dd.sub { font-family: var(--body); font-size: 13px; color: var(--muted); }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 18px; }
.view { margin: 0; min-width: 0; display: flex; flex-direction: column; gap: 8px; }
.view img, .plans img { width: 100%; max-width: 100%; height: auto; display: block; border-radius: 6px; border: 1px solid var(--line); background: var(--bg-2); }
figcaption { display: flex; flex-direction: column; gap: 6px; align-items: flex-start; }
figcaption strong { font-weight: 600; }
.btn { display: inline-block; padding: 7px 12px; border-radius: 999px; background: var(--accent); color: var(--accent-ink); text-decoration: none; font-weight: 600; font-size: 14px; }
.btn:hover, .btn:focus-visible { filter: brightness(1.08); outline: 2px solid var(--fg); outline-offset: 2px; }
.plans { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }
.plans figure { margin: 0; min-width: 0; }
.tables { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; }
.tables > div { min-width: 0; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
.num { text-align: right; font-family: var(--mono); font-variant-numeric: tabular-nums; white-space: nowrap; }
th.num { font-family: var(--body); }
footer { margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--line); }
footer strong { color: var(--stamp); letter-spacing: 0.04em; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
"""
    head = ("<title>Villa 5130272 Design Board</title>\n"
            "<meta name=\"claude:viewport-fit-sides\" content=\"cover\">\n"
            "<link rel=\"stylesheet\" href=\"https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono&display=swap\">\n")
    fragment = head + style + body
    full = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            + head + style + "</head>\n<body>\n" + body + "</body>\n</html>\n")
    return full, fragment


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    full, fragment = build()
    (OUT / "index.html").write_text(full, encoding="utf-8")
    (OUT / "artifact.html").write_text(fragment, encoding="utf-8")
    n = len(list(IMG.glob("*.jpg")))
    print(f"Design board written: {OUT / 'index.html'} ({n} images in {IMG})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
