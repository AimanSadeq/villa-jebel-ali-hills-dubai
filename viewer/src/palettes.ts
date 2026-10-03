/** Villa 5130272, interior palettes in the walkthrough (answers P1 to P4, D-052).
 *
 *  The model build exports, in data/model.json "finishes", every room's floor,
 *  wall faces and ceiling as quads tagged with a palette slot
 *  (src/model/finishes.py), and the three palettes of brief/palettes.yaml.
 *  This module turns them into one mesh per slot and level, and switches the
 *  slot materials when the palette changes. Textures are drawn here, in the
 *  browser, from the palette's pattern: no image files, nothing to license.
 *
 *  Grid coordinates (u, v, z) map to Three.js as x = u, y = z, z = -v.
 *
 *  CONCEPT DESIGN, NOT FOR CONSTRUCTION.
 */

import * as THREE from 'three';

type Pt = [number, number, number];
export interface Swatch { name: string; colour: string; pattern: string; roughness: number }
export interface Palette {
  key: string; name: string;
  flooring: Record<string, Swatch>; walls: Record<string, Swatch>;
  accents: Record<string, Swatch>; fixtures: Record<string, Swatch>;
}
export interface Finishes {
  quads: { slot: string; storey: 'ground' | 'first'; room: string; p: Pt[] }[];
  /** Furniture (src/model/furniture.py): boxes u0, u1, v0, v1, z0, z1. */
  boxes?: { slot: string; storey: 'ground' | 'first'; b: number[] }[];
  palettes: Palette[];
  note: string;
}

const TILE_M: Record<string, number> = {
  stone: 1.2, marble: 2.4, wood: 2.0, terrazzo: 1.2, concrete: 2.4, plain: 2.0, metal: 1.0,
};

/** The swatch drawn as a texture: its colour with the pattern over it. */
function patternTexture(pattern: string, seed: number, colour: string): THREE.Texture | null {
  if (pattern === 'plain' || pattern === 'metal') return null;
  const N = 512;
  const c = document.createElement('canvas');
  c.width = N; c.height = N;
  const g = c.getContext('2d')!;
  let s = seed * 9301 + 49297;
  const rnd = () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
  g.fillStyle = colour;
  g.fillRect(0, 0, N, N);
  const dark = new THREE.Color(colour).getHSL({ h: 0, s: 0, l: 0 }).l < 0.3;
  if (pattern === 'stone' || pattern === 'concrete') {
    for (let i = 0; i < 1600; i++) {
      const a = pattern === 'stone' ? 0.012 : 0.02;
      g.fillStyle = `rgba(${rnd() < 0.5 ? '0,0,0' : '255,255,255'},${a * rnd()})`;
      const r = 3 + rnd() * 22;
      g.beginPath(); g.arc(rnd() * N, rnd() * N, r, 0, Math.PI * 2); g.fill();
    }
    if (pattern === 'stone') {           // tile joints, one tile per repeat
      g.strokeStyle = 'rgba(0,0,0,0.18)'; g.lineWidth = 2;
      g.strokeRect(1, 1, N - 2, N - 2);
    }
  } else if (pattern === 'marble') {
    for (let i = 0; i < 14; i++) {
      g.strokeStyle = dark ? `rgba(235,235,230,${0.35 + rnd() * 0.4})` : `rgba(90,90,90,${0.15 + rnd() * 0.25})`;
      g.lineWidth = 0.6 + rnd() * 1.6;
      g.beginPath();
      let x = rnd() * N; let y = 0;
      g.moveTo(x, y);
      while (y < N) { x += (rnd() - 0.45) * 40; y += 12 + rnd() * 20; g.lineTo(x, y); }
      g.stroke();
    }
  } else if (pattern === 'wood') {
    for (let y = 0; y < N; y += 2) {
      const v = Math.sin(y * 0.18 + Math.sin(y * 0.031) * 3) * 0.06 + (rnd() - 0.5) * 0.03;
      g.fillStyle = v > 0 ? `rgba(255,255,255,${v})` : `rgba(0,0,0,${-v})`;
      g.fillRect(0, y, N, 2);
    }
    g.fillStyle = 'rgba(0,0,0,0.22)';
    for (let y = 0; y < N; y += N / 8) g.fillRect(0, y, N, 2);       // plank joints
  } else if (pattern === 'terrazzo') {
    for (let i = 0; i < 1400; i++) {
      const k = rnd();
      g.fillStyle = k < 0.45 ? 'rgba(60,60,60,0.65)' : k < 0.8 ? 'rgba(150,150,150,0.5)' : 'rgba(255,255,255,0.9)';
      g.beginPath(); g.arc(rnd() * N, rnd() * N, 1.5 + rnd() * 5, 0, Math.PI * 2); g.fill();
    }
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = THREE.RepeatWrapping; t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

function swatchOf(p: Palette, slot: string): Swatch | undefined {
  const [grp, key] = slot.split('.');
  return (p as unknown as Record<string, Record<string, Swatch>>)[grp]?.[key];
}

export class PaletteLayer {
  readonly group = new THREE.Group();
  readonly meshes: { mesh: THREE.Mesh; slot: string; storey: string; ceiling: boolean }[] = [];
  private readonly mats = new Map<string, THREE.MeshStandardMaterial>();
  private readonly tex = new Map<string, THREE.Texture | null>();
  current = -1;
  readonly data: Finishes;

  constructor(data: Finishes) {
    this.data = data;
    this.group.name = 'Interior finishes (palettes)';
    const buckets = new Map<string, { slot: string; storey: string; pos: number[]; uv: number[]; idx: number[] }>();
    for (const q of data.quads) {
      const k = `${q.slot}|${q.storey}`;
      if (!buckets.has(k)) buckets.set(k, { slot: q.slot, storey: q.storey, pos: [], uv: [], idx: [] });
      const b = buckets.get(k)!;
      const base = b.pos.length / 3;
      const [a, , c] = q.p;
      const flat = Math.abs(a[2] - c[2]) < 1e-6;
      for (const [u, v, z] of q.p) {
        b.pos.push(u, z, -v);
        // Planar UVs in metres: floors and ceilings by plan, walls along and up.
        if (flat) b.uv.push(u, v);
        else b.uv.push(Math.abs(q.p[3][0] - q.p[0][0]) > Math.abs(q.p[3][1] - q.p[0][1]) ? u : v, z);
      }
      b.idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
    }
    // Furniture boxes become six faces each, outward.
    for (const fb of data.boxes ?? []) {
      const [u0, u1, v0, v1, z0, z1] = fb.b;
      const faces: Pt[][] = [
        [[u0, v0, z1], [u1, v0, z1], [u1, v1, z1], [u0, v1, z1]],
        [[u0, v0, z0], [u0, v1, z0], [u1, v1, z0], [u1, v0, z0]],
        [[u0, v0, z0], [u1, v0, z0], [u1, v0, z1], [u0, v0, z1]],
        [[u1, v1, z0], [u0, v1, z0], [u0, v1, z1], [u1, v1, z1]],
        [[u0, v1, z0], [u0, v0, z0], [u0, v0, z1], [u0, v1, z1]],
        [[u1, v0, z0], [u1, v1, z0], [u1, v1, z1], [u1, v0, z1]],
      ];
      const k = `${fb.slot}|${fb.storey}|f`;
      if (!buckets.has(k)) buckets.set(k, { slot: fb.slot, storey: fb.storey, pos: [], uv: [], idx: [] });
      const bk = buckets.get(k)!;
      for (const f of faces) {
        const base = bk.pos.length / 3;
        const flat = f.every((p) => p[2] === f[0][2]);
        const alongU = f.every((p) => p[1] === f[0][1]);
        for (const [u, v, z] of f) { bk.pos.push(u, z, -v); bk.uv.push(flat ? u : alongU ? u : v, flat ? v : z); }
        bk.idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
      }
    }
    for (const b of buckets.values()) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(b.pos, 3));
      geo.setAttribute('uv', new THREE.Float32BufferAttribute(b.uv, 2));
      geo.setIndex(b.idx);
      geo.computeVertexNormals();
      const mat = this.material(b.slot);
      const mesh = new THREE.Mesh(geo, mat);
      mesh.name = `Finish, ${b.slot}, ${b.storey}`;
      mesh.renderOrder = 1;
      this.group.add(mesh);
      this.meshes.push({ mesh, slot: b.slot, storey: b.storey, ceiling: b.slot === 'walls.ceiling' });
    }
  }

  private material(slot: string): THREE.MeshStandardMaterial {
    if (!this.mats.has(slot)) {
      // Polygon offset keeps the finish in front of the wall face it lies on.
      this.mats.set(slot, new THREE.MeshStandardMaterial({
        side: THREE.FrontSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2,
      }));
    }
    return this.mats.get(slot)!;
  }

  /** Apply palette i (0 to 2), or -1 for the bare model. */
  set(i: number) {
    this.current = i;
    this.group.visible = i >= 0;
    if (i < 0) return;
    const p = this.data.palettes[i];
    this.mats.forEach((m, slot) => {
      if (slot.startsWith('fixed.')) {
        // Fixed colours: bed linen, screens, glass, mirrors.
        m.map = null; m.color.set(slot.slice(6)); m.roughness = slot === 'fixed.#121212' ? 0.2 : 0.5;
        m.needsUpdate = true;
        return;
      }
      const sw = swatchOf(p, slot);
      if (!sw) return;
      const key = `${sw.pattern}|${sw.colour}|${i}`;
      if (!this.tex.has(key)) this.tex.set(key, patternTexture(sw.pattern, i * 7 + sw.pattern.length, sw.colour));
      const t = this.tex.get(key) ?? null;
      if (t) {
        const r = 1 / (TILE_M[sw.pattern] ?? 2);
        t.repeat.set(r, r);
      }
      m.map = t;
      // The texture carries the colour; plain swatches take it as the material colour.
      m.color.set(t ? '#ffffff' : sw.colour);
      m.roughness = sw.roughness;
      m.metalness = 0;
      m.needsUpdate = true;
    });
  }

  /** Show the levels in view; ceilings only while walking. */
  show(levels: string[], walking: boolean) {
    for (const { mesh, storey, ceiling } of this.meshes) {
      mesh.visible = levels.includes(storey) && (!ceiling || walking);
    }
  }
}
