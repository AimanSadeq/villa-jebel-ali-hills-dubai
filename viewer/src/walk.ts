/** Villa 5130272, first person walkthrough (D-049).
 *
 *  Walks the model at eye height on the zones that src/model/architecture.py
 *  exports in data/model.json (walk_data): flat zones for each level, the
 *  stair flights as ramps between them, door openings joining the rooms. A
 *  position is allowed only where the walker's footprint (a circle of
 *  radius_m) stands on zones at about the same height, so walls stop the
 *  walker, stairs carry it up and down, and voids and balcony edges cannot be
 *  walked off. The lift rides between levels.
 *
 *  Grid coordinates: u east-south-east, v north-north-east, z up. Three.js
 *  frame as web-ifc produces it: x = u, y = z, z = -v.
 *
 *  CONCEPT DESIGN, NOT FOR CONSTRUCTION.
 */

import * as THREE from 'three';

type Pt = [number, number];
export interface Zone {
  name: string; kind: 'flat' | 'ramp'; rings: Pt[][];
  z?: number; p0?: Pt; z0?: number; p1?: Pt; z1?: number;
}
export interface WalkData {
  eye_m: number; radius_m: number; step_m: number; zones: Zone[];
  lift: { rings: Pt[][]; levels: number[] };
  start: { u: number; v: number; z: number };
  levels: Record<string, number>;
}

function inRing(ring: Pt[], u: number, v: number): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [ui, vi] = ring[i];
    const [uj, vj] = ring[j];
    if ((vi > v) !== (vj > v) && u < ((uj - ui) * (v - vi)) / (vj - vi) + ui) inside = !inside;
  }
  return inside;
}

export function inRings(rings: Pt[][], u: number, v: number): boolean {
  if (!rings.length || !inRing(rings[0], u, v)) return false;
  for (let k = 1; k < rings.length; k++) if (inRing(rings[k], u, v)) return false;
  return true;
}

function zoneZ(z: Zone, u: number, v: number): number {
  if (z.kind === 'flat') return z.z ?? 0;
  const [a, b] = [z.p0!, z.p1!];
  const du = b[0] - a[0];
  const dv = b[1] - a[1];
  const t = Math.min(1, Math.max(0, ((u - a[0]) * du + (v - a[1]) * dv) / (du * du + dv * dv)));
  return z.z0! + t * (z.z1! - z.z0!);
}

const KEYS = ['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
  'ShiftLeft', 'ShiftRight'];

export class Walker {
  u: number; v: number; z: number;
  yaw = 0; pitch = 0;
  active = false;
  riding: { from: number; to: number; t: number } | null = null;
  private keys = new Set<string>();
  private readonly ring: Pt[];

  readonly data: WalkData;
  readonly camera: THREE.PerspectiveCamera;
  readonly dom: HTMLElement;
  readonly onLift: (msg: string) => void;

  constructor(data: WalkData, camera: THREE.PerspectiveCamera, dom: HTMLElement,
              onLift: (msg: string) => void = () => {}) {
    this.data = data; this.camera = camera; this.dom = dom; this.onLift = onLift;
    this.u = data.start.u; this.v = data.start.v; this.z = data.start.z;
    // Face the house: the start is on the road side of the porch.
    this.yaw = -Math.PI / 2;
    const r = data.radius_m;
    this.ring = Array.from({ length: 8 }, (_, i) => [
      r * Math.cos((i * Math.PI) / 4), r * Math.sin((i * Math.PI) / 4)] as Pt);
    window.addEventListener('keydown', (e) => {
      if (!this.active) return;
      if (KEYS.includes(e.code)) { this.keys.add(e.code); e.preventDefault(); }
      if (e.code === 'KeyE') this.rideLift();
    });
    window.addEventListener('keyup', (e) => this.keys.delete(e.code));
    dom.addEventListener('click', () => {
      if (this.active && document.pointerLockElement !== dom) dom.requestPointerLock?.();
    });
    document.addEventListener('mousemove', (e) => {
      if (!this.active || document.pointerLockElement !== dom) return;
      this.look(e.movementX, e.movementY);
    });
  }

  look(dx: number, dy: number) {
    this.yaw -= dx * 0.0022;
    this.pitch = Math.min(1.35, Math.max(-1.35, this.pitch - dy * 0.0022));
  }

  /** Heights of the zones under (u, v) within a step of the current height. */
  private support(u: number, v: number, zNow: number): number | null {
    let best: number | null = null;
    for (const zone of this.data.zones) {
      if (!inRings(zone.rings, u, v)) continue;
      const zc = zoneZ(zone, u, v);
      if (Math.abs(zc - zNow) > this.data.step_m) continue;
      if (best === null || Math.abs(zc - zNow) < Math.abs(best - zNow)) best = zc;
    }
    return best;
  }

  /** The height the walker would stand at, or null if its footprint does
   *  not fit: every point of the circle must stand on a zone too. */
  standAt(u: number, v: number, zNow = this.z): number | null {
    const zc = this.support(u, v, zNow);
    if (zc === null) return null;
    for (const [du, dv] of this.ring) if (this.support(u + du, v + dv, zc) === null) return null;
    return zc;
  }

  inLift(): boolean { return inRings(this.data.lift.rings, this.u, this.v); }

  level(): 'ground' | 'first' { return this.z < (this.data.levels.first ?? 5) / 2 ? 'ground' : 'first'; }

  rideLift() {
    if (this.riding) return;
    if (!this.inLift()) { this.onLift('Step into the lift to ride it.'); return; }
    const lv = this.data.lift.levels;
    const to = this.level() === 'ground' ? lv[lv.length - 1] : lv[0];
    this.riding = { from: this.z, to, t: 0 };
    this.onLift(`Lift to the ${to > 0 ? 'first' : 'ground'} floor`);
  }

  teleport(u: number, v: number, z: number, yaw?: number) {
    this.u = u; this.v = v; this.z = z;
    if (yaw !== undefined) this.yaw = yaw;
    this.place();
  }

  /** Move by a step in grid metres, sliding along walls. Returns true if it moved. */
  move(du: number, dv: number): boolean {
    for (const [a, b] of [[du, dv], [du, 0], [0, dv]] as Pt[]) {
      if (a === 0 && b === 0) continue;
      const z = this.standAt(this.u + a, this.v + b);
      if (z !== null) { this.u += a; this.v += b; this.z = z; return true; }
    }
    return false;
  }

  update(dt: number) {
    if (!this.active) return;
    dt = Math.min(dt, 0.1);
    if (this.riding) {
      const r = this.riding;
      r.t = Math.min(1, r.t + dt / 4.0);
      const e = r.t < 0.5 ? 2 * r.t * r.t : 1 - (-2 * r.t + 2) ** 2 / 2;
      this.z = r.from + (r.to - r.from) * e;
      if (r.t >= 1) { this.riding = null; this.onLift(''); }
    } else {
      const k = (c: string) => this.keys.has(c);
      const fwd = (k('KeyW') || k('ArrowUp') ? 1 : 0) - (k('KeyS') || k('ArrowDown') ? 1 : 0);
      const side = (k('KeyD') || k('ArrowRight') ? 1 : 0) - (k('KeyA') || k('ArrowLeft') ? 1 : 0);
      if (k('ArrowLeft') && !k('KeyA')) this.yaw += dt * 1.6;
      if (k('ArrowRight') && !k('KeyD')) this.yaw -= dt * 1.6;
      if (fwd || side) {
        const speed = (k('ShiftLeft') || k('ShiftRight') ? 3.0 : 1.4) * dt;
        // Forward in the grid: three -z is +v, rotated by the yaw.
        const fu = -Math.sin(this.yaw);
        const fv = Math.cos(this.yaw);
        const ru = Math.cos(this.yaw);
        const rv = Math.sin(this.yaw);
        const n = Math.hypot(fwd, side);
        this.move(((fu * fwd + ru * side) / n) * speed, ((fv * fwd + rv * side) / n) * speed);
      }
    }
    this.place();
  }

  place() {
    this.camera.position.set(this.u, this.z + this.data.eye_m, -this.v);
    this.camera.rotation.set(this.pitch, this.yaw, 0, 'YXZ');
    this.camera.updateMatrixWorld();
  }
}

/** A small plan of the current level with the walker on it. */
export function drawMiniMap(canvas: HTMLCanvasElement, data: WalkData, w: Walker,
                            rooms: { rect: number[]; storey: string; label: string }[]) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const lvl = w.level();
  const zLevel = data.levels[lvl] ?? 0;
  const zones = data.zones.filter((z) => z.kind === 'ramp' || Math.abs((z.z ?? 0) - zLevel) < 0.5);
  let [u0, v0, u1, v1] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const r of rooms) {
    u0 = Math.min(u0, r.rect[0]); u1 = Math.max(u1, r.rect[1]);
    v0 = Math.min(v0, r.rect[2]); v1 = Math.max(v1, r.rect[3]);
  }
  const pad = 2;
  u0 -= pad; v0 -= pad; u1 += pad; v1 += pad;
  const W = canvas.width;
  const H = canvas.height;
  const s = Math.min(W / (u1 - u0), H / (v1 - v0));
  const X = (u: number) => (u - u0) * s + (W - (u1 - u0) * s) / 2;
  const Y = (v: number) => H - ((v - v0) * s + (H - (v1 - v0) * s) / 2);
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(255,255,255,0.92)';
  ctx.fillRect(0, 0, W, H);
  ctx.lineWidth = 1;
  for (const r of rooms.filter((q) => q.storey === lvl)) {
    ctx.fillStyle = '#f2efe9';
    ctx.strokeStyle = '#8c857a';
    const [a, b, c, d] = r.rect;
    ctx.fillRect(X(a), Y(d), (b - a) * s, (d - c) * s);
    ctx.strokeRect(X(a), Y(d), (b - a) * s, (d - c) * s);
  }
  ctx.strokeStyle = '#1f6f8b';
  for (const z of zones) {
    if (z.kind !== 'ramp') continue;
    ctx.beginPath();
    z.rings[0].forEach(([u, v], i) => (i ? ctx.lineTo(X(u), Y(v)) : ctx.moveTo(X(u), Y(v))));
    ctx.closePath();
    ctx.stroke();
  }
  // The walker and the way it faces.
  const fu = -Math.sin(w.yaw);
  const fv = Math.cos(w.yaw);
  ctx.fillStyle = '#b3261e';
  ctx.beginPath();
  ctx.moveTo(X(w.u + fu * 1.2), Y(w.v + fv * 1.2));
  ctx.lineTo(X(w.u - fv * 0.5), Y(w.v + fu * 0.5));
  ctx.lineTo(X(w.u + fv * 0.5), Y(w.v - fu * 0.5));
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = '#1a1a1a';
  ctx.font = '11px system-ui, sans-serif';
  ctx.fillText(lvl === 'ground' ? 'Ground floor' : 'First floor', 6, 14);
}
