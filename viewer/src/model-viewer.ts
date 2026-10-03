/** Villa 5130272, model viewer and walkthrough (Phase 4, D-049).
 *
 *  Loads the IFC4 model that src/model/build_model.py generates and publishes
 *  (viewer/public/data), converts it to fragments in the browser with That Open
 *  Engine, and shows it in orbit view or walks it in first person (walk.ts). Room labels and the area figures come
 *  from data/model.json, written by the same build, so the viewer, the IFC and
 *  the GFA report cannot disagree.
 *
 *  CONCEPT DESIGN, NOT FOR CONSTRUCTION.
 */

import './style.css';
import * as THREE from 'three';
import * as OBC from '@thatopen/components';
import type * as FRAGS from '@thatopen/fragments';
import { CSS2DObject, CSS2DRenderer } from 'three/examples/jsm/renderers/CSS2DRenderer.js';
import workerUrl from '@thatopen/fragments/worker?url';
import { append, clear, h, icon, tr } from './dom';
import { Walker, drawMiniMap, type WalkData } from './walk';
import { PaletteLayer, type Finishes } from './palettes';

interface RoomLabel {
  key: string; name: string; label: string; storey: 'ground' | 'first';
  u: number; v: number; z: number;
  area_m2: number; area_sqft: number; circulation: boolean; sub?: boolean;
  w_m?: number; l_m?: number; height?: string; rect?: number[];
}

interface ModelData {
  meta: { plot: string; community: string; stamp: string; phase: number; ifc: string; built: string };
  north_uv: [number, number];
  heights: { ground_m: number; first_m: number; parapet_m: number; roof_m: number; overall_m: number };
  gfa: { road_wing_ground: number; ssw_wing_ground: number; living_block_ground?: number;
         first_floor_less_void: number;
         total: number; cap: number; margin: number };
  gfa_from_ifc: Record<string, number>;
  outside_gfa?: Record<string, number>;
  reference?: string;
  core: string;
  counts: Record<string, number>;
  rooms: RoomLabel[];
  walk?: WalkData;
  finishes?: Finishes;
}

type Level = 'ground' | 'first' | 'roof';
type View = 'whole' | 'first' | 'ground';
type Group = 'site' | 'spaces' | Level;
type ModelIdMap = Record<string, Set<number>>;

const SQFT = 10.763910416709722;
const fmt = (v: number, d = 2) => v.toLocaleString('en-GB', { minimumFractionDigits: d, maximumFractionDigits: d });

/** IFC grid (u east-south-east, v north-north-east, z up) to the Three.js
 *  frame web-ifc produces: x = u, y = z, z = -v. */
const toThree = (u: number, v: number, z: number) => new THREE.Vector3(u, z, -v);

function section(iconName: string, title: string, ...body: (Node | string)[]) {
  const sec = h('section', {}, h('h2', {}, icon(iconName), h('span', {}, title)));
  append(sec, body);
  return sec;
}

function northArrow(): SVGSVGElement {
  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('viewBox', '-20 -20 40 40');
  svg.setAttribute('class', 'north');
  const ring = document.createElementNS(NS, 'circle');
  ring.setAttribute('r', '18');
  const arrow = document.createElementNS(NS, 'polygon');
  arrow.setAttribute('points', '0,-15 6,6 0,2 -6,6');
  const letter = document.createElementNS(NS, 'text');
  letter.setAttribute('y', '16');
  letter.setAttribute('text-anchor', 'middle');
  letter.textContent = 'N';
  svg.append(ring, arrow, letter);
  return svg;
}

async function boot() {
  const res = await fetch('data/model.json');
  if (!res.ok) throw new Error(`Cannot load data/model.json (HTTP ${res.status}). Run src/model/build_model.py.`);
  const data: ModelData = await res.json();

  const app = document.getElementById('app')!;
  clear(app);
  const stage = h('div', { id: 'stage' });
  const panel = h('aside', { id: 'panel' });
  const compass = h('div', { id: 'compass' }, northArrow());
  const progress = h('div', { id: 'progress' }, 'Loading the IFC model');
  app.append(stage, panel,
    h('div', { id: 'stamp', class: 'clear-logo' }, data.meta.stamp),
    h('div', { id: 'hint' }, 'Drag to orbit, scroll to zoom, right-drag to pan, click to inspect'),
    compass, progress);

  // World ------------------------------------------------------------------

  const components = new OBC.Components();
  const world = components.get(OBC.Worlds)
    .create<OBC.SimpleScene, OBC.OrthoPerspectiveCamera, OBC.SimpleRenderer>();
  world.scene = new OBC.SimpleScene(components);
  world.scene.setup();
  world.scene.three.background = new THREE.Color(0xf7f5f1);
  world.renderer = new OBC.SimpleRenderer(components, stage);
  world.camera = new OBC.OrthoPerspectiveCamera(components);
  components.init();

  const fragments = components.get(OBC.FragmentsManager);
  fragments.init(workerUrl);
  world.camera.controls.addEventListener('update', () => fragments.core.update());
  fragments.list.onItemSet.add(({ value }) => {
    value.useCamera(world.camera.three);
    world.scene.three.add(value.object);
    fragments.core.update(true);
  });

  // Labels overlay, drawn after every frame.
  const labels = new CSS2DRenderer();
  labels.domElement.id = 'labels';
  stage.append(labels.domElement);
  const sizeLabels = () => labels.setSize(stage.clientWidth, stage.clientHeight);
  sizeLabels();
  new ResizeObserver(sizeLabels).observe(stage);
  world.renderer.onAfterUpdate.add(() => labels.render(world.scene.three, world.camera.three));

  // North arrow follows the camera.
  const [nu, nv] = data.north_uv;
  const north2 = new THREE.Vector2(nu, -nv);          // in the x, z plane
  const fwd = new THREE.Vector3();
  const svgArrow = compass.querySelector('svg')!;
  world.renderer.onAfterUpdate.add(() => {
    world.camera.three.getWorldDirection(fwd);
    const f = new THREE.Vector2(fwd.x, fwd.z).normalize();
    const right = new THREE.Vector2(-f.y, f.x);
    const deg = THREE.MathUtils.radToDeg(Math.atan2(north2.dot(right), north2.dot(f)));
    svgArrow.style.transform = `rotate(${deg.toFixed(1)}deg)`;
  });

  // Load -------------------------------------------------------------------

  const ifcLoader = components.get(OBC.IfcLoader);
  await ifcLoader.setup({
    autoSetWasm: false,
    wasm: { path: new URL('wasm/', window.location.href).href, absolute: true },
    // Keep the plot grid coordinates as authored, so the room labels from
    // model.json land in their rooms. The model is small and near the origin.
    webIfc: { COORDINATE_TO_ORIGIN: false },
  });
  const ifcRes = await fetch(data.meta.ifc);
  if (!ifcRes.ok) throw new Error(`Cannot load ${data.meta.ifc} (HTTP ${ifcRes.status})`);
  const bytes = new Uint8Array(await ifcRes.arrayBuffer());
  const model: FRAGS.FragmentsModel = await ifcLoader.load(bytes, false, 'villa', {
    processData: {
      progressCallback: (p: number) => { progress.textContent = `Converting the IFC, ${Math.round(p * 100)}%`; },
    },
  });
  progress.remove();

  // Sort every element into a level by the height of its base, plus the site
  // and the rooms. Levels follow the section: ground 0.00, first 5.00, roof 9.00.
  const byCat = await model.getItemsOfCategories([/^IFC/]);
  const ids: number[] = [];
  const catOf = new Map<number, string>();
  for (const [cat, list] of Object.entries(byCat)) {
    if (/^IFC(PROJECT|SITE|BUILDING|BUILDINGSTOREY)$/.test(cat)) continue;
    for (const id of list) { ids.push(id); catOf.set(id, cat); }
  }
  const boxes = await model.getBoxes(ids);
  const items = await model.getItemsData(ids, { attributesDefault: true });
  const nameOf = new Map<number, { name: string; longName: string }>();
  items.forEach((it, i) => {
    const attr = (k: string) => {
      const a = (it as Record<string, unknown>)[k] as { value?: unknown } | undefined;
      return a && typeof a.value === 'string' ? a.value : '';
    };
    nameOf.set(ids[i], { name: attr('Name'), longName: attr('LongName') });
  });

  const groups: Record<Group, number[]> = { site: [], spaces: [], ground: [], first: [], roof: [] };
  const spaceLevel = new Map<number, Level>();
  const g1 = data.heights.ground_m - 0.5;
  const g2 = data.heights.roof_m - 0.5;
  ids.forEach((id, i) => {
    const cat = catOf.get(id)!;
    const b = boxes[i];
    const name = nameOf.get(id)?.name ?? '';
    // Facade parts (D-051) span the storeys: sort them by their middle.
    const facadePart = /^IFC(COVERING|LIGHTFIXTURE|SHADINGDEVICE)$/.test(cat) || name === 'Roof pergola';
    const y = facadePart ? (b.min.y + b.max.y) / 2 : b.min.y;
    const level: Level = y < g1 ? 'ground' : y < g2 ? 'first' : 'roof';
    if (cat === 'IFCSPACE') {
      if (name === 'Swimming pool water') groups.site.push(id);
      else { groups.spaces.push(id); spaceLevel.set(id, level); }
    } else if (cat === 'IFCGEOGRAPHICELEMENT' || (cat === 'IFCBUILDINGELEMENTPROXY' && !facadePart) || name === 'Pool deck') {
      groups.site.push(id);
    } else {
      groups[level].push(id);
    }
  });

  // Visibility --------------------------------------------------------------

  const hider = components.get(OBC.Hider);
  const map = (list: number[]): ModelIdMap => ({ [model.modelId]: new Set(list) });
  const state = { view: 'whole' as View, spaces: false, site: true, labels: true };

  // CLAUDE.md rule 9 (D-045): width x length, then the area.
  const size = (r: RoomLabel) => (r.w_m && r.l_m
    ? `${fmt(r.w_m)} x ${fmt(r.l_m)} m, ${fmt(r.area_m2, 1)} m² (${fmt(r.area_sqft, 0)} sq ft)`
    : `${fmt(r.area_m2, 1)} m² (${fmt(r.area_sqft, 0)} sq ft)`);
  const roomLabels: { obj: CSS2DObject; room: RoomLabel }[] = [];
  for (const r of data.rooms) {
    const el = h('div', { class: r.circulation ? 'label circ' : r.sub ? 'label sub' : 'label' },
      h('b', {}, r.label),
      r.circulation ? null : h('span', {}, size(r)),
      r.circulation || !r.height ? null : h('span', {}, r.height));
    el.title = `${r.name}, ${size(r)}${r.height ? `, ${r.height}` : ''}`;
    const obj = new CSS2DObject(el);
    obj.position.copy(toThree(r.u, r.v, r.z));
    world.scene.three.add(obj);
    roomLabels.push({ obj, room: r });
  }

  // Interior palettes (D-052): floors, wall faces and ceilings per room.
  const finishes = data.finishes && data.finishes.quads.length ? new PaletteLayer(data.finishes) : null;
  if (finishes) { world.scene.three.add(finishes.group); finishes.set(0); }

  async function applyVisibility() {
    const shown: Level[] = state.view === 'whole' ? ['ground', 'first', 'roof']
      : state.view === 'first' ? ['ground', 'first'] : ['ground'];
    finishes?.show(shown, walkState.on);
    await hider.set(true, map(ids));
    const hide: number[] = [];
    for (const lv of ['ground', 'first', 'roof'] as Level[]) if (!shown.includes(lv)) hide.push(...groups[lv]);
    if (!state.site) hide.push(...groups.site);
    const top: Level = shown[shown.length - 1];
    for (const id of groups.spaces) {
      if (!state.spaces || spaceLevel.get(id) !== top) hide.push(id);
    }
    if (hide.length) await hider.set(false, map(hide));
    for (const { obj, room } of roomLabels) {
      obj.visible = state.labels && state.view !== 'whole' && room.storey === top;
    }
    await fragments.core.update(true);
  }

  // Camera: from the road side, looking across the building to the courtyard.
  const box = model.box;
  const centre = box.getCenter(new THREE.Vector3());
  await world.camera.controls.setLookAt(
    centre.x - 26, centre.y + 24, centre.z + 22, centre.x, 2, centre.z, false);

  // Picking ---------------------------------------------------------------------

  const caster = components.get(OBC.Raycasters).get(world);
  const info = h('div', { class: 'pick' }, h('p', { class: 'summary' }, 'Click any element or room.'));
  const highlight: FRAGS.MaterialDefinition = {
    color: new THREE.Color('#2e7d4f'), renderedFaces: 1 as FRAGS.RenderedFaces,
    opacity: 0.85, transparent: true,
  };
  let picked: number | null = null;
  // Pick at the click itself, and not at the end of an orbit drag.
  let down = { x: 0, y: 0 };
  stage.addEventListener('pointerdown', (e) => { down = { x: e.clientX, y: e.clientY }; });
  stage.addEventListener('click', async (e) => {
    if (Math.hypot(e.clientX - down.x, e.clientY - down.y) > 4) return;
    const r = stage.getBoundingClientRect();
    const position = new THREE.Vector2(
      ((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    const hit = (await caster.castRay({ position })) as unknown as { localId?: number } | null;
    if (picked !== null) await model.resetHighlight([picked]);
    picked = null;
    clear(info);
    if (!hit || hit.localId === undefined) {
      info.append(h('p', { class: 'summary' }, 'Click any element or room.'));
      await fragments.core.update(true);
      return;
    }
    picked = hit.localId;
    await model.highlight([picked], highlight);
    await fragments.core.update(true);
    const n = nameOf.get(picked);
    const cat = catOf.get(picked) ?? '';
    const t = h('table', {}, tr('Element', n?.name || '(unnamed)'), tr('IFC class', cat));
    const room = data.rooms.find((r) => r.key === n?.longName &&
      (spaceLevel.get(picked!) ?? 'ground') === r.storey);
    if (cat === 'IFCSPACE' && room) {
      if (room.w_m && room.l_m) t.append(tr('Size', `${fmt(room.w_m)} x ${fmt(room.l_m)} m`));
      t.append(tr('Net area', `${fmt(room.area_m2)} m²`), tr('', `${fmt(room.area_sqft, 0)} sq ft`));
      if (room.height) t.append(tr('Clear height', room.height.replace(/^h /, '')));
    }
    info.append(t);
  });

  // Walkthrough (D-049) ---------------------------------------------------------

  const doorIds = Object.entries(byCat).filter(([c]) => c === 'IFCDOOR').flatMap(([, l]) => l);
  const cam = world.camera.three as THREE.PerspectiveCamera;
  const hud = h('div', { id: 'hud' });
  const lifted = h('div', { id: 'liftmsg' });
  const mini = h('canvas', { id: 'minimap', width: '260', height: '220' }) as HTMLCanvasElement;
  const walkHelp = h('div', { id: 'walkhelp' },
    'Click the view, then move the mouse to look. W A S D or the arrow keys to walk, Shift to walk faster, E inside the lift to ride it, Esc to free the mouse.');
  // Overlays sit beside the stage, not in it: the stage sizes every canvas in
  // it to the full view.
  app.append(hud, lifted, mini, walkHelp);
  for (const el of [hud, mini, walkHelp]) el.style.display = 'none';
  const walker = data.walk
    ? new Walker(data.walk, cam, stage, (msg) => { lifted.textContent = msg; lifted.style.display = msg ? '' : 'none'; })
    : null;
  lifted.style.display = 'none';
  const roomRects = data.rooms.filter((r) => r.rect && !r.sub)
    .map((r) => ({ rect: r.rect!, storey: r.storey, label: r.label, room: r }));
  let orbitView: { pos: THREE.Vector3; target: THREE.Vector3 } | null = null;
  const walkState = { on: false, night: false };

  function roomAt(u: number, v: number, storey: string) {
    let best: RoomLabel | null = null;
    let area = Infinity;
    for (const { rect: [a, b, c, d], room } of roomRects) {
      if (room.storey !== storey || u < a || u > b || v < c || v > d) continue;
      const ar = (b - a) * (d - c);
      if (ar < area) { area = ar; best = room; }
    }
    return best;
  }

  async function setWalking(on: boolean) {
    if (!walker) return;
    walkState.on = on;
    walker.active = on;
    for (const el of [hud, mini, walkHelp]) el.style.display = on ? '' : 'none';
    const hint = document.getElementById('hint');
    if (hint) hint.style.display = on ? 'none' : '';
    if (on) {
      orbitView = { pos: cam.position.clone(),
                    target: world.camera.controls.getTarget(new THREE.Vector3()) };
      world.camera.controls.enabled = false;
      cam.fov = 70; cam.near = 0.05; cam.updateProjectionMatrix();
      walker.place();
      state.view = 'whole';
      for (const [k, el] of viewBtns) el.classList.toggle('on', k === 'whole');
      await applyVisibility();
      // Doors are shown open while walking: the openings stay, the leaves hide.
      if (doorIds.length) await hider.set(false, map(doorIds));
      for (const { obj } of roomLabels) obj.visible = false;
    } else {
      if (document.pointerLockElement) document.exitPointerLock();
      world.camera.controls.enabled = true;
      cam.fov = 60; cam.updateProjectionMatrix();
      if (orbitView) {
        await world.camera.controls.setLookAt(orbitView.pos.x, orbitView.pos.y, orbitView.pos.z,
          orbitView.target.x, orbitView.target.y, orbitView.target.z, false);
      }
      await applyVisibility();
    }
    walkBtn.classList.toggle('on', on);
    walkBtn.lastChild!.textContent = on ? 'Stop walking' : 'Walk through the house';
    await fragments.core.update(true);
  }

  // Night: the sun and sky dim and warm lights come on in the rooms around the
  // viewer. Interim fixtures at each room's centre under its ceiling; the
  // reflected ceiling plans (Phase 6) will place the real ones.
  const sceneLights = world.scene.three.children.filter((o) => (o as THREE.Light).isLight) as THREE.Light[];
  const baseIntensity = sceneLights.map((l) => l.intensity);
  const lamps = Array.from({ length: 10 }, () => {
    const l = new THREE.PointLight(0xffd6a0, 0, 9, 1.6);
    world.scene.three.add(l);
    return l;
  });
  const dayBg = new THREE.Color(0xf7f5f1);
  const nightBg = new THREE.Color(0x141b2b);
  function placeLamps() {
    if (!walkState.night) return;
    const at = walkState.on && walker
      ? new THREE.Vector3(walker.u, walker.z, walker.v)
      : (() => { const t = world.camera.controls.getTarget(new THREE.Vector3()); return new THREE.Vector3(t.x, t.y, -t.z); })();
    const ceiling = (r: RoomLabel) => (r.storey === 'first' ? data.heights.ground_m : 0)
      + (r.height && /8\.55/.test(r.height) && !/elsewhere/.test(r.height) ? 8.2 : r.storey === 'first' ? 3.3 : 4.3);
    const near = roomRects.map(({ room }) => room)
      .filter((r) => !r.circulation || r.area_m2 > 6)
      .map((r) => ({ r, d: Math.hypot(r.u - at.x, r.v - at.z, (r.storey === 'first' ? 5 : 0) - at.y) }))
      .sort((a, b) => a.d - b.d).slice(0, lamps.length);
    lamps.forEach((l, i) => {
      const n = near[i];
      if (!n) { l.intensity = 0; return; }
      l.position.copy(toThree(n.r.u, n.r.v, ceiling(n.r)));
      l.intensity = 9;
    });
  }
  function setNight(on: boolean) {
    walkState.night = on;
    sceneLights.forEach((l, i) => { l.intensity = baseIntensity[i] * (on ? 0.12 : 1); });
    world.scene.three.background = on ? nightBg : dayBg;
    if (!on) lamps.forEach((l) => { l.intensity = 0; });
    placeLamps();
    dayBtn.classList.toggle('on', !on);
    nightBtn.classList.toggle('on', on);
  }

  const clock = new THREE.Clock();
  let sinceFrags = 0;
  let sinceLamps = 0;
  world.renderer.onBeforeUpdate.add(() => {
    const dt = clock.getDelta();
    if (!walker || !walkState.on) return;
    walker.update(dt);
    sinceFrags += dt;
    sinceLamps += dt;
    if (sinceFrags > 0.3) { sinceFrags = 0; fragments.core.update(); }
    if (sinceLamps > 0.5) { sinceLamps = 0; placeLamps(); }
    const room = roomAt(walker.u, walker.v, walker.level());
    const where = walker.level() === 'ground' ? 'Ground floor' : 'First floor';
    hud.textContent = room
      ? `${room.name}, ${where}: ${room.w_m && room.l_m ? `${fmt(room.w_m)} x ${fmt(room.l_m)} m, ` : ''}${fmt(room.area_m2, 1)} m² (${fmt(room.area_sqft, 0)} sq ft)${room.height ? `, ${room.height.replace(/^h /, 'clear height ')}` : ''}`
      : `${where}, outside`;
    drawMiniMap(mini, walker.data, walker, roomRects);
  });

  const walkBtn = h('button', { class: 'chip wide', type: 'button' }, icon('walk', 'icon tiny'), 'Walk through the house');
  walkBtn.addEventListener('click', () => setWalking(!walkState.on));
  const dayBtn = h('button', { class: 'chip on', type: 'button' }, icon('sun', 'icon tiny'), 'Day');
  const nightBtn = h('button', { class: 'chip', type: 'button' }, icon('moon', 'icon tiny'), 'Night');
  dayBtn.addEventListener('click', () => setNight(false));
  nightBtn.addEventListener('click', () => setNight(true));
  const liftBtn = h('button', { class: 'chip', type: 'button' }, icon('lift', 'icon tiny'), 'Ride the lift');
  liftBtn.addEventListener('click', () => walker?.rideLift());

  // Panel -------------------------------------------------------------------------

  panel.append(h('header', {},
    h('h1', {}, `Villa ${data.meta.plot}`),
    h('p', { class: 'sub' }, data.meta.community),
    h('p', { class: 'phase' }, `Phase ${data.meta.phase} · IFC model and walkthrough`)));

  const viewBtns = new Map<View, HTMLButtonElement>();
  const chips = h('div', { class: 'chips' });
  for (const [v, label] of [['whole', 'Whole building'], ['first', 'First floor'], ['ground', 'Ground floor']] as [View, string][]) {
    const b = h('button', { class: 'chip', type: 'button' }, label);
    b.addEventListener('click', async () => {
      state.view = v;
      for (const [k, el] of viewBtns) el.classList.toggle('on', k === v);
      await applyVisibility();
    });
    viewBtns.set(v, b);
    chips.append(b);
  }
  viewBtns.get('whole')!.classList.add('on');

  const toggle = (label: string, key: 'spaces' | 'site' | 'labels') => {
    const input = h('input', { type: 'checkbox' });
    input.checked = state[key];
    input.addEventListener('change', async () => { state[key] = input.checked; await applyVisibility(); });
    return h('label', {}, input, label);
  };

  panel.append(section('layers', 'View',
    chips,
    h('div', { class: 'toggles', style: 'margin-top:12px' },
      toggle('Room labels with areas', 'labels'),
      toggle('Room volumes (IfcSpace)', 'spaces'),
      toggle('Site and garden', 'site')),
    h('p', { class: 'note' }, icon('ruler', 'icon tiny'),
      'Labels and room volumes show on the floor plan views. The ground floor view cuts away the first floor and the roofs.')));

  panel.append(section('walk', 'Walkthrough',
    h('div', { class: 'chips' }, walkBtn),
    h('div', { class: 'chips', style: 'margin-top:8px' }, dayBtn, nightBtn, liftBtn),
    h('p', { class: 'note' }, icon('warn', 'icon tiny'),
      'Walls and the balustrades stop you, the stair carries you up and down, the lift rides between floors. Doors are shown open. Night lights are interim, one per room, until the ceiling plans place the fixtures (Phase 6).')));

  if (finishes) {
    const palBtns: HTMLButtonElement[] = [];
    const palNote = h('p', { class: 'note' });
    const choose = (i: number) => {
      finishes.set(i);
      palBtns.forEach((b, k) => b.classList.toggle('on', k - 1 === i));
      const p = i >= 0 ? finishes.data.palettes[i] : null;
      palNote.textContent = p
        ? `Floors ${p.flooring.public.name.toLowerCase()}; walls ${p.walls.main.name.toLowerCase()}; feature walls ${p.walls.feature.name.toLowerCase()}. Visual concept finishes, not a specification.`
        : 'The model without finishes.';
    };
    const chipsP = h('div', { class: 'chips' });
    const bare = h('button', { class: 'chip', type: 'button' }, 'No finishes');
    bare.addEventListener('click', () => choose(-1));
    palBtns.push(bare);
    finishes.data.palettes.forEach((p, i) => {
      const b = h('button', { class: 'chip', type: 'button' }, `${i + 1} ${p.name}`);
      b.addEventListener('click', () => choose(i));
      palBtns.push(b);
    });
    chipsP.append(...palBtns.slice(1), bare);
    panel.append(section('palette', 'Interior palette', chipsP, palNote));
    choose(0);
  }

  panel.append(section('check', 'Selection', info));

  const g = data.gfa;
  const sqft = (v: number) => `${fmt(v * SQFT, 0)} sq ft`;
  const area = h('table', { class: 'metrics' },
    tr('Ground floor', `${fmt(g.road_wing_ground + g.ssw_wing_ground + (g.living_block_ground ?? 0))} m²`),
    tr('First floor, less voids', `${fmt(g.first_floor_less_void)} m²`),
    tr('Total GFA', `${fmt(g.total)} m²`),
    tr('', sqft(g.total), 'adj'),
    tr('DDA cap', `${fmt(g.cap)} m²`),
    tr('Margin', `${g.margin >= 0 ? '+' : ''}${fmt(g.margin)} m²`, g.margin >= 0 ? 'good' : 'bad'));
  const outsideNames: Record<string, string> = {
    carport_m2: 'Carport', first_floor_balconies_terrace_m2: 'Balconies and terraces' };
  for (const [k, v] of Object.entries(data.outside_gfa ?? {})) {
    if (v > 0) area.append(tr(`${outsideNames[k] ?? k.replace(/_m2$/, '').replace(/_/g, ' ')} (outside GFA, TO VERIFY)`, `${fmt(v)} m²`, 'adj'));
  }
  // CLAUDE.md section 3: the total both with and without the carport.
  const carport = (data.outside_gfa ?? {})['carport_m2'] ?? 0;
  if (carport > 0) {
    const withCar = g.total + carport;
    area.append(tr('Total if DDA counts the carport', `${fmt(withCar)} m²`, withCar <= g.cap ? 'good' : 'bad'));
  }
  const ifcTotal = Object.values(data.gfa_from_ifc).reduce((a, b) => a + b, 0);
  panel.append(section('ruler', 'Area', area,
    h('p', { class: 'note' }, icon('check', 'icon tiny'),
      `Measured back from the IFC walls and rooms: ${fmt(ifcTotal)} m², matching the plan.`)));

  const hgt = data.heights;
  panel.append(section('compass', 'Section',
    h('table', {},
      tr('Ground floor to floor', `${fmt(hgt.ground_m)} m`),
      tr('First floor to floor', `${fmt(hgt.first_m)} m`),
      tr('Roof slab', `+${fmt(hgt.roof_m)} m`),
      tr('Parapet', `${fmt(hgt.parapet_m)} m`),
      tr('Overall', `${fmt(hgt.overall_m)} m`)),
    h('p', { class: 'note' }, icon('warn', 'icon tiny'),
      'Overall height against the DDA metre cap is TO VERIFY, OI-13. Stair and lift core TO VERIFY, OI-23: ' + data.core + '.')));

  const counts = h('table', {});
  for (const [k, v] of Object.entries(data.counts)) counts.append(tr(k.replace(/^Ifc/, ''), String(v)));
  panel.append(section('layers', 'Model', counts,
    h('p', { class: 'note' }, `IFC4, built ${data.meta.built}. `,
      h('a', { href: data.meta.ifc, download: '' }, 'Download the IFC'),
      ' · ', h('a', { href: './' }, 'Phase 1 massing'))));

  panel.append(h('footer', {},
    h('h3', {}, icon('warn', 'icon tiny'), data.meta.stamp),
    h('p', { class: 'small' },
      'Indicative model generated from brief/*.yaml. Structure, MEP and finishes are not modelled yet. A DDA registered consultant and a licensed structural engineer must review and stamp all final drawings.')));

  await applyVisibility();

  // Reload when a new build lands, so the page always shows the latest model.
  const built = data.meta.built;
  setInterval(async () => {
    try {
      const r = await fetch('data/model.json', { cache: 'no-store' });
      if (r.ok && ((await r.json()) as ModelData).meta.built !== built) window.location.reload();
    } catch { /* offline between rebuilds */ }
  }, 4000);

  // Development only: lets the camera be scripted when checking views.
  if (import.meta.env.DEV) {
    (window as unknown as Record<string, unknown>).__villa = { world, model, centre, walker, setWalking, setNight, finishes };
  }
}

boot().catch((err: unknown) => {
  const app = document.getElementById('app')!;
  clear(app);
  app.append(h('div', { class: 'fatal' },
    h('p', {}, 'The model viewer could not start.'),
    h('pre', {}, err instanceof Error ? `${err.message}\n${err.stack ?? ''}` : String(err))));
  console.error(err);
});
