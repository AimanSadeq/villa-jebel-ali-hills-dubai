# SETUP.md: Laptop setup for Villa 5130272

Laptop: Windows, Intel Core i7, 32 GB RAM, Intel Arc 140V GPU. Claude Code runs from the Claude Desktop app (Code tab).

Open **Windows Terminal** or **PowerShell** and run the steps in order. `winget` is built into Windows 11.

## Step 1: Core tools

```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
winget install --id Python.Python.3.12 -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id BlenderFoundation.Blender -e
```

Close and reopen the terminal, then check:

```powershell
git --version
gh --version
python --version
node --version
npm --version
```

## Step 2: Create the private GitHub repo

```powershell
gh auth login
mkdir C:\Projects
cd C:\Projects
gh repo create villa-5130272 --private --clone
cd villa-5130272
```

Copy into this folder: `CLAUDE.md`, `SETUP.md`, and the `reference` folder containing `5130272_-_Plot_Details.pdf`. Then:

```powershell
git add .
git commit -m "Project brief and plot reference"
git push
```

## Step 3: Python environment and libraries

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks the activate script, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

What each library does:

| Library | Purpose |
|---|---|
| ifcopenshell | Generates and reads the IFC building model; clash detection |
| ezdxf | Creates DXF drawings for AutoCAD; renders them to PDF |
| matplotlib | PDF drawing output and charts |
| shapely | Plot polygon, setbacks, area calculations |
| pyyaml | Reads the brief files (`program.yaml`, `site.yaml`) |
| pvlib | Sun positions for shading studies |
| pandas | Schedules and load calculation tables |
| pytest | Automated checks (GFA limit, setbacks) |

## Step 4: Viewer libraries

```powershell
npm create vite@latest viewer -- --template vanilla-ts
cd viewer
npm install three @thatopen/components @thatopen/components-front @thatopen/fragments web-ifc
npm install -D @types/three
cd ..
```

## Step 5: Blender + Bonsai (for renders and model inspection)

1. Open Blender.
2. Go to **Edit > Preferences > Get Extensions**, search **Bonsai**, and install it.
3. Go to **Edit > Preferences > System > Cycles Render Devices**, choose **oneAPI**, and tick the Intel Arc 140V. This lets Cycles render on your GPU.

## Step 6: Browser

Use **Chrome** or **Edge** (both support WebGPU on Windows). Keep the Intel Arc graphics driver updated through Intel's Driver & Support Assistant. To confirm WebGPU is active, open `chrome://gpu` and check that WebGPU shows "Hardware accelerated".

## Step 7: Recommended extensions

You run Claude Code in the Desktop app, so a code editor is optional. VS Code is still useful for reading files, viewing diffs, and previewing drawings.

```powershell
winget install --id Microsoft.VisualStudioCode -e
```

VS Code extensions (Extensions panel, search by name):

| Extension | Why |
|---|---|
| Python (Microsoft) | Run and debug the model scripts |
| Pylance (Microsoft) | Code intelligence for Python |
| ESLint | Checks the viewer code |
| YAML (Red Hat) | Validates `program.yaml` and `site.yaml` as you edit them |
| GitLens | See who changed what and when; compare design versions |
| PDF Preview (or vscode-pdf) | View drawing PDFs inside the editor |
| Markdown All in One | Read and edit `CLAUDE.md` and the reports |

Optional desktop tools:

| Tool | Why |
|---|---|
| Autodesk DWG TrueView (free) | Check DXF drawings exactly as the consultant will see them |
| BIMvision or Open IFC Viewer (free) | Independent check of the IFC model outside our own viewer |

## Step 8: Start Claude Code

1. Open the Claude Desktop app and go to the **Code** tab.
2. Open the folder `C:\Projects\villa-5130272`.
3. Type: `Read CLAUDE.md, SETUP.md and docs/decisions.md, confirm the setup is complete, then continue from the current phase and wait for my approval.`

Claude Code will check the installs, ask any remaining questions one at a time, and continue only after you approve.

## Notes

- Sizes: expect the repo to grow to a few GB once 3D assets and renders are added. Git LFS will be set up by Claude Code for large files (`git lfs install`).
- Backups: GitHub is your remote copy. Push at the end of every session.
- Performance: if the walkthrough feels slow, ask Claude Code to lower plant density or texture resolution; your 32 GB RAM and Arc 140V handle a single villa scene well.

## Walkthrough with real materials (D-056)

```
.\.venv\Scripts\Activate.ps1
python assets/fetch_assets.py          # once: photographs of real materials and skies, CC0 from Poly Haven
python src/model/build_model.py
npm run dev --prefix viewer            # then http://localhost:5173/model.html, reload after a fetch
```

The viewer's Realism section switches the photographic materials and the sky;
the Interior palette section switches the three palettes (brief/palettes.yaml).

## Twinmotion walkthrough (D-059)

```
.\.venv\Scripts\Activate.ps1
python src/model/build_model.py
python src/model/export_twinmotion.py
```

Then follow `docs/twinmotion-guide.md` (also copied to `output/twinmotion/README.md`):
import the palette's `.ifc`, assign the library materials by name, place the
furniture and plants from `VJH-TM-001_placements.csv`, set the six cameras
from `VJH-TM-001_cameras.csv`.

## Renders (Phase 7, brought forward by D-057)

Blender Cycles renders of the six views, from the model and the fetched
assets, on the laptop's Intel Arc GPU:

```
.\.venv\Scripts\Activate.ps1
python assets/fetch_assets.py                  # once: textures and skies
python src/model/build_model.py
pip install bpy pillow                         # Blender as a Python module (large) and the stamp writer, once
python renders/render_villa.py --all --device GPU --samples 256 --size 1920x1080
```

One view at test quality: `python renders/render_villa.py --view living --samples 32 --size 960x540`.
Output: `output/renders/VJH-R-00n_<view>.png`. The render script also runs inside
Blender: `blender -b -P renders/render_villa.py -- --view aerial`.
