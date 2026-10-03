/** Villa 5130272, real materials, sky and sun in the walkthrough (answer P7, D-056).
 *
 *  Reads viewer/public/assets/index.json, written by assets/fetch_assets.py
 *  on the laptop (photographs of real materials and real skies from Poly
 *  Haven, CC0; see assets/manifest.yaml and assets/LICENSES.md), or by
 *  assets/make_standins.py for testing. Provides:
 *    * Materials: MeshStandardMaterial per texture key, with the diffuse,
 *      normal and roughness maps repeated at their real size in metres;
 *    * the sky as the scene's background and light (HDRI), a sun with
 *      shadows at the sun study's position, filmic tone mapping;
 *    * ExteriorLayer: the facade parts and the garden surfaces drawn with
 *      the textures, in place of their plain IFC copies.
 *
 *  Without the index the viewer keeps its drawn textures and plain sky.
 *  Grid (u, v, z) to Three.js: x = u, y = z, z = -v.
 *
 *  CONCEPT DESIGN, NOT FOR CONSTRUCTION.
 */

import * as THREE from 'three';
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js';

export interface TextureEntry { id: string; scale_m: number; diff?: string; nor?: string; rough?: string; arm?: string }
export interface AssetIndex {
  generated: string; standin: boolean; source: string;
  hdri: Record<string, { path: string; id: string }>;
  textures: Record<string, TextureEntry>;
  models: Record<string, { path: string; id: string; fits: string[] }>;
}
export interface SunSpec { when: string; azimuth_deg: number; elevation_deg: number; dir_uvz: [number, number, number] }
export interface Exterior {
  facade: { name: string; kind: string; material: string; b: number[] }[];
  garden: { key: string; kind: string; z: number; rings: [number, number][][][] }[];
  hedges: { b: number[] }[];
  trees: { species: string; kind: string; u: number; v: number; height_m: number; trunk_m: number; crown_m: number }[];
  ground_z: number;
}

export async function loadAssetIndex(): Promise<AssetIndex | null> {
  try {
    const r = await fetch('assets/index.json', { cache: 'no-store' });
    if (!r.ok) return null;
    return (await r.json()) as AssetIndex;
  } catch { return null; }
}

/** Textured materials, one per texture key, shared. */
export class Materials {
  private readonly loader = new THREE.TextureLoader();
  private readonly cache = new Map<string, THREE.MeshStandardMaterial>();
  readonly index: AssetIndex;
  constructor(index: AssetIndex) { this.index = index; }

  has(key: string | undefined): boolean { return !!key && !!this.index.textures[key]?.diff; }

  private tex(path: string, srgb: boolean, scale: number): THREE.Texture {
    const t = this.loader.load(path);
    t.wrapS = THREE.RepeatWrapping; t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(1 / scale, 1 / scale);
    t.anisotropy = 8;
    if (srgb) t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }

  /** Apply the key's maps to a material (its colour becomes a light tint). */
  apply(m: THREE.MeshStandardMaterial, key: string, tint = '#ffffff', roughness?: number): void {
    const e = this.index.textures[key];
    if (!e?.diff) return;
    const s = e.scale_m || 2;
    m.map = this.tex(e.diff, true, s);
    m.normalMap = e.nor ? this.tex(e.nor, false, s) : null;
    m.roughnessMap = e.rough ? this.tex(e.rough, false, s) : null;
    m.color.set(tint);
    m.roughness = roughness ?? 1.0;
    m.metalness = 0;
    m.needsUpdate = true;
  }

  get(key: string, tint = '#ffffff', roughness?: number): THREE.MeshStandardMaterial {
    const k = `${key}|${tint}`;
    if (!this.cache.has(k)) {
      const m = new THREE.MeshStandardMaterial({ side: THREE.FrontSide });
      this.apply(m, key, tint, roughness);
      this.cache.set(k, m);
    }
    return this.cache.get(k)!;
  }
}

/** Sky, environment light, sun with shadows and tone mapping. */
export class Sky {
  readonly sun: THREE.DirectionalLight;
  private readonly scene: THREE.Scene;
  private readonly renderer: THREE.WebGLRenderer;
  private day: THREE.Texture | null = null;
  private dusk: THREE.Texture | null = null;
  private readonly plainBg: THREE.Color;
  /** The viewer's own lights (That Open's ambient and directional), dimmed
   *  while the sky lights the scene so nothing is lit twice. */
  baseLights: { light: THREE.Light; intensity: number }[] = [];
  on = false;

  private readonly centre: THREE.Vector3;

  constructor(scene: THREE.Scene, renderer: THREE.WebGLRenderer, centre: THREE.Vector3, sun: SunSpec, plainBg: THREE.Color) {
    this.scene = scene; this.renderer = renderer; this.plainBg = plainBg; this.centre = centre.clone();
    // Shadow maps must be on before the shaders compile: three.js builds its
    // programs without shadow code otherwise, and a later switch shows nothing.
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    const light = new THREE.DirectionalLight(0xfff2dc, 0);
    light.castShadow = true;
    light.shadow.mapSize.set(2048, 2048);
    const c = light.shadow.camera;
    c.left = -32; c.right = 32; c.top = 32; c.bottom = -32; c.near = 1; c.far = 160;
    c.updateProjectionMatrix();          // the default frustum is only 10 m wide
    light.shadow.bias = -0.0004;
    light.shadow.normalBias = 0.02;
    scene.add(light, light.target);
    this.sun = light;
    this.place(sun);
  }

  /** Put the sun at a sun study position (dir_uvz points at the sun). */
  place(sun: SunSpec): void {
    const [du, dv, dz] = sun.dir_uvz;
    const c = this.centre;
    this.sun.position.set(c.x + du * 60, c.y + dz * 60, c.z - dv * 60);
    this.sun.target.position.copy(c);
    this.sun.target.updateMatrixWorld();
  }

  async load(index: AssetIndex): Promise<void> {
    const loader = new RGBELoader();
    const one = async (key: string) => {
      const p = index.hdri[key]?.path;
      if (!p) return null;
      const t = await loader.loadAsync(p);
      t.mapping = THREE.EquirectangularReflectionMapping;
      return t;
    };
    [this.day, this.dusk] = await Promise.all([one('sky_day'), one('sky_dusk')]);
  }

  /** Turn the real sky and sun on or off; night swaps to the dusk sky. */
  set(on: boolean, night: boolean): void {
    this.on = on;
    const r = this.renderer;
    r.toneMapping = on ? THREE.ACESFilmicToneMapping : THREE.NoToneMapping;
    r.toneMappingExposure = on ? (night ? 0.5 : 0.45) : 1.0;
    const sky = night ? (this.dusk ?? this.day) : this.day;
    if (on && sky) {
      this.scene.background = sky;
      this.scene.environment = sky;
      this.scene.backgroundIntensity = night ? 0.35 : 0.9;
      this.scene.environmentIntensity = night ? 0.12 : 0.6;
    } else {
      this.scene.environment = null;
      if (!night) this.scene.background = this.plainBg;
    }
    // Balanced against the sky's light so the shadows read and the render stays off-white.
    this.sun.intensity = on ? (night ? 0.0 : 10) : 0;
    this.sun.visible = on;
    // Materials compiled before the sky arrived pick up the environment map.
    this.scene.traverse((o) => {
      const m = (o as THREE.Mesh).material as THREE.Material | THREE.Material[] | undefined;
      if (!m) return;
      for (const mm of Array.isArray(m) ? m : [m]) mm.needsUpdate = true;
    });
    for (const { light, intensity } of this.baseLights) {
      light.intensity = on ? intensity * (night ? 0.08 : 0.15) : intensity * (night ? 0.12 : 1);
    }
  }
}

const GARDEN_TEX: Record<string, string> = {
  lawn: 'lawn', bed: 'soil', ground: 'soil', paving: 'terrace_stone', step: 'terrace_stone', path: 'paving',
};
const FACADE_TEX: Record<string, string> = { stone: 'split_face_stone', timber: 'timber', render: 'beige_render' };

/** The facade parts and garden surfaces with real textures. */
export class ExteriorLayer {
  readonly group = new THREE.Group();

  constructor(ext: Exterior, mats: Materials) {
    this.group.name = 'Exterior, real materials';
    // Facade boxes by material.
    const byMat = new Map<string, THREE.BoxGeometry[]>();
    for (const f of ext.facade) {
      if (f.material === 'led') continue;
      const [u0, u1, v0, v1, z0, z1] = f.b;
      const g = new THREE.BoxGeometry(u1 - u0, z1 - z0, v1 - v0);
      g.translate((u0 + u1) / 2, (z0 + z1) / 2, -(v0 + v1) / 2);
      // Box UVs run 0 to 1 per face: scale them to metres so the texture repeats properly.
      const uv = g.attributes.uv as THREE.BufferAttribute;
      const sizes = [[v1 - v0, z1 - z0], [v1 - v0, z1 - z0], [u1 - u0, v1 - v0], [u1 - u0, v1 - v0], [u1 - u0, z1 - z0], [u1 - u0, z1 - z0]];
      for (let i = 0; i < uv.count; i++) {
        const face = Math.floor(i / 4);
        uv.setXY(i, uv.getX(i) * sizes[face][0], uv.getY(i) * sizes[face][1]);
      }
      if (!byMat.has(f.material)) byMat.set(f.material, []);
      byMat.get(f.material)!.push(g);
    }
    for (const [mat, geos] of byMat) {
      const key = FACADE_TEX[mat];
      if (!key || !mats.has(key)) continue;
      for (const g of geos) {
        const mesh = new THREE.Mesh(g, mats.get(key));
        mesh.castShadow = true; mesh.receiveShadow = true;
        this.group.add(mesh);
      }
    }
    // Garden surfaces: polygons with holes, triangulated, UVs in metres.
    for (const s of ext.garden) {
      const key = GARDEN_TEX[s.kind];
      if (!key || !mats.has(key)) continue;
      for (const rings of s.rings) {
        const outer = rings[0].map(([u, v]) => new THREE.Vector2(u, v));
        const holes = rings.slice(1).map((r) => r.map(([u, v]) => new THREE.Vector2(u, v)));
        const tris = THREE.ShapeUtils.triangulateShape(outer, holes);
        const pts = outer.concat(...holes);
        const pos: number[] = []; const uv: number[] = [];
        for (const p of pts) { pos.push(p.x, s.z + 0.004, -p.y); uv.push(p.x, p.y); }
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
        geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
        geo.setIndex(tris.flat());
        geo.computeVertexNormals();
        const mesh = new THREE.Mesh(geo, mats.get(key, s.kind === 'ground' ? '#cfc6b8' : '#ffffff'));
        mesh.receiveShadow = true;
        mesh.material.polygonOffset = true; mesh.material.polygonOffsetFactor = -1; mesh.material.polygonOffsetUnits = -1;
        this.group.add(mesh);
      }
    }
    // Hedges: boxes with the lawn texture, darkened.
    if (mats.has('lawn')) {
      const hedge = mats.get('lawn', '#6f9a55');
      for (const h of ext.hedges) {
        const [u0, u1, v0, v1, z0, z1] = h.b;
        const g = new THREE.BoxGeometry(u1 - u0, z1 - z0, v1 - v0);
        g.translate((u0 + u1) / 2, (z0 + z1) / 2, -(v0 + v1) / 2);
        const mesh = new THREE.Mesh(g, hedge);
        mesh.castShadow = true; mesh.receiveShadow = true;
        this.group.add(mesh);
      }
    }
  }
}

/** Let the IFC meshes cast and receive shadows (they are created as tiles load). */
export function enableShadows(root: THREE.Object3D): void {
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (m.isMesh && !(m.castShadow && m.receiveShadow)) { m.castShadow = true; m.receiveShadow = true; }
  });
}
