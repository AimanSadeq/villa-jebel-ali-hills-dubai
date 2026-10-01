/** Three.js scene for the Phase 1 massing options.
 *
 *  Coordinate mapping: site x (east) to three X, site y (north) to three -Z.
 *  So north points toward -Z and the default camera looks roughly north.
 *
 *  Sun positions come from the exported table, not from a JavaScript solar
 *  library, so the shadows here agree with the reports exactly.
 *
 *  CONCEPT DESIGN, NOT FOR CONSTRUCTION.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import type { MassingData, MassingOption, Poly, Ring } from './types';

const COLOURS = {
  ground: 0xd8cfc0,
  plotLine: 0xb3261e,
  envelope: 0xb8860b,
  massGround: 0xf2f0ec,
  massFirst: 0xe8e4dd,
  garage: 0xcfc9bf,
  pool: 0x2a7fb8,
  deck: 0xded3bd,
  drive: 0xc9c5bd,
  wallSolid: 0xf0ede7,
  wallScreen: 0xbfb6a6,
  sky: 0xdfe8f0,
};

function trace(path: THREE.Shape | THREE.Path, ring: Ring) {
  ring.forEach(([x, y], i) => (i === 0 ? path.moveTo(x, y) : path.lineTo(x, y)));
  path.closePath();
}

function shapeFromPoly(poly: Poly): THREE.Shape {
  const shape = new THREE.Shape();
  trace(shape, poly.shell);
  for (const hole of poly.holes) {
    const path = new THREE.Path();
    trace(path, hole);
    shape.holes.push(path);
  }
  return shape;
}

/** Extrude a site-plane polygon upward. `base` lifts it off the ground. */
function extrude(polys: Poly[], height: number, base: number, material: THREE.Material) {
  const group = new THREE.Group();
  for (const poly of polys) {
    const geom = new THREE.ExtrudeGeometry(shapeFromPoly(poly), {
      depth: height,
      bevelEnabled: false,
    });
    // Shape lies in the XY plane and extrudes along +Z. Rotating -90 degrees
    // about X maps shape Y to -Z (north) and the extrusion to +Y (up).
    geom.rotateX(-Math.PI / 2);
    geom.translate(0, base, 0);
    const mesh = new THREE.Mesh(geom, material);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    group.add(mesh);
  }
  return group;
}

/** A side label drawn to a canvas and shown as a camera-facing sprite.
 *  Two lines: the side number, and what is on the other side of it. */
function makeLabel(number: string, role: string, sub: string, dist: string,
                   accent: boolean): THREE.Sprite {
  const W = 512, H = 196, dpr = 2;
  const cv = document.createElement('canvas');
  cv.width = W * dpr;
  cv.height = H * dpr;
  const g = cv.getContext('2d')!;
  g.scale(dpr, dpr);

  const ink = accent ? '#1d6b45' : '#2b2b2b';
  g.fillStyle = 'rgba(255,255,255,0.92)';
  g.strokeStyle = accent ? '#2e7d4f' : '#c6c0b4';
  g.lineWidth = 3;
  const r = 18;
  g.beginPath();
  g.moveTo(r, 2); g.lineTo(W - r, 2); g.quadraticCurveTo(W - 2, 2, W - 2, r);
  g.lineTo(W - 2, H - r); g.quadraticCurveTo(W - 2, H - 2, W - r, H - 2);
  g.lineTo(r, H - 2); g.quadraticCurveTo(2, H - 2, 2, H - r);
  g.lineTo(2, r); g.quadraticCurveTo(2, 2, r, 2);
  g.closePath(); g.fill(); g.stroke();

  // Side number in a filled disc on the left.
  g.fillStyle = ink;
  g.beginPath();
  g.arc(60, H / 2, 38, 0, Math.PI * 2);
  g.fill();
  g.fillStyle = '#ffffff';
  g.font = '600 46px ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText(number, 60, H / 2 + 2);

  g.textAlign = 'left';
  g.fillStyle = ink;
  g.font = '600 38px ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif';
  g.fillText(role, 116, H / 2 - 20);
  g.fillStyle = '#6b6b6b';
  g.font = '26px ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif';
  g.fillText(sub, 116, H / 2 + 18);
  g.fillStyle = '#1f6f8b';
  g.font = '600 28px ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif';
  g.fillText(dist, 116, H / 2 + 56);

  const tex = new THREE.CanvasTexture(cv);
  tex.anisotropy = 8;
  tex.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
    map: tex, transparent: true, depthTest: false, depthWrite: false,
  }));
  sprite.renderOrder = 20;
  sprite.scale.set(12.6, 4.8, 1);
  return sprite;
}

function ringToPoints(ring: Ring, y: number): THREE.Vector3[] {
  const pts = ring.map(([x, yy]) => new THREE.Vector3(x, y, -yy));
  pts.push(pts[0].clone());
  return pts;
}

export class MassingScene {
  readonly scene = new THREE.Scene();
  readonly camera: THREE.PerspectiveCamera;
  readonly controls: OrbitControls;
  private renderer!: THREE.WebGLRenderer;
  private sun = new THREE.DirectionalLight(0xfff4e0, 2.6);
  private hemi = new THREE.HemisphereLight(0xbcd4e6, 0xb8a98c, 1.1);
  // Weak opposing fill so shadowed faces keep their form without washing out
  // the real sun shadow, which is the whole point of the view.
  private fill = new THREE.DirectionalLight(0xdfe8f0, 0.35);
  private optionGroup = new THREE.Group();
  private wallGroup = new THREE.Group();
  private labelGroup = new THREE.Group();
  private envelopeLine!: THREE.Line;
  private data!: MassingData;
  private centre = new THREE.Vector3();
  private container: HTMLElement;

  constructor(container: HTMLElement) {
    this.container = container;
    this.camera = new THREE.PerspectiveCamera(45, 1, 0.5, 2000);
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;
    container.appendChild(this.renderer.domElement);

    this.scene.background = new THREE.Color(COLOURS.sky);
    this.scene.fog = new THREE.Fog(COLOURS.sky, 150, 420);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.maxPolarAngle = Math.PI / 2 - 0.03;
    this.controls.minDistance = 15;
    this.controls.maxDistance = 260;

    this.scene.add(this.hemi);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    const c = this.sun.shadow.camera as THREE.OrthographicCamera;
    c.left = -55; c.right = 55; c.top = 55; c.bottom = -55;
    c.near = 1; c.far = 400;
    this.sun.shadow.bias = -0.0006;
    this.sun.shadow.normalBias = 0.03;
    this.scene.add(this.sun, this.sun.target);
    this.scene.add(this.fill);
    this.scene.add(this.optionGroup, this.wallGroup, this.labelGroup);

    addEventListener('resize', () => this.resize());
  }

  build(data: MassingData) {
    this.data = data;

    const xs = data.plot.map((p) => p[0]);
    const ys = data.plot.map((p) => p[1]);
    this.centre.set(
      (Math.min(...xs) + Math.max(...xs)) / 2,
      0,
      -(Math.min(...ys) + Math.max(...ys)) / 2,
    );

    // Ground. Large enough to catch the long low-sun shadows.
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(600, 600),
      new THREE.MeshStandardMaterial({ color: COLOURS.ground, roughness: 1 }),
    );
    ground.rotateX(-Math.PI / 2);
    ground.position.copy(this.centre);
    ground.position.y = -0.02;
    ground.receiveShadow = true;
    this.scene.add(ground);

    // Plot boundary, drawn just above the ground so it is never z-fought.
    this.scene.add(
      new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(ringToPoints(data.plot, 0.04)),
        new THREE.LineBasicMaterial({ color: COLOURS.plotLine }),
      ),
    );

    this.envelopeLine = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(ringToPoints(data.envelope, 0.05)),
      new THREE.LineDashedMaterial({ color: COLOURS.envelope, dashSize: 1.2, gapSize: 0.8 }),
    );
    this.envelopeLine.computeLineDistances();
    this.scene.add(this.envelopeLine);

    this.buildWalls();
    this.showOption(data.options.find((o) => o.key === data.recommended)!);

    this.setView('aerial');
    this.resize();
  }

  private buildWalls() {
    this.wallGroup.clear();
    const solidMat = new THREE.MeshStandardMaterial({ color: COLOURS.wallSolid, roughness: 0.9 });
    const screenMat = new THREE.MeshStandardMaterial({
      color: COLOURS.wallScreen,
      roughness: 0.8,
      transparent: true,
      opacity: 0.3,
      depthWrite: false,
    });

    for (const side of this.data.sides) {
      const spec = this.data.boundaryWall.bySide[String(side.id)];
      if (!spec) continue;
      const [x0, y0] = side.start;
      const [x1, y1] = side.end;
      const len = Math.hypot(x1 - x0, y1 - y0);
      const mid = new THREE.Vector3((x0 + x1) / 2, 0, -(y0 + y1) / 2);
      // A rotation of theta about Y maps the box's +X axis to
      // (cos theta, 0, -sin theta). The side runs (dx, 0, -dy) in three
      // coordinates, so sin theta = dy and theta = atan2(dy, dx).
      const angle = Math.atan2(y1 - y0, x1 - x0);

      const add = (h: number, base: number, mat: THREE.Material) => {
        if (h <= 0.001) return;
        const m = new THREE.Mesh(new THREE.BoxGeometry(len, h, 0.25), mat);
        m.position.set(mid.x, base + h / 2, mid.z);
        m.rotation.y = angle;
        m.castShadow = true;
        m.receiveShadow = true;
        this.wallGroup.add(m);
      };
      add(spec.solid, 0, solidMat);
      add(spec.screenTo - spec.solid, spec.solid, screenMat);
    }
  }

  /** Side number labels, placed outside each boundary and facing the camera.
   *  The role text is derived, not hard-coded: the entrance is the side the DDA
   *  plan marks as main access, and the garden is whichever side this option
   *  puts the pool against. */
  private buildLabels(option: MassingOption) {
    this.labelGroup.clear();
    const gardenSide = option.metrics.poolNearestSide;
    const dist = new Map(option.wallToBoundary.map((w) => [w.side, w.distanceM]));

    for (const side of this.data.sides) {
      const [x0, y0] = side.start;
      const [x1, y1] = side.end;
      const mid = new THREE.Vector3((x0 + x1) / 2, 0, -(y0 + y1) / 2);

      // Outward normal: the perpendicular that points away from the plot centre.
      const dir = new THREE.Vector3(x1 - x0, 0, -(y1 - y0)).normalize();
      let n = new THREE.Vector3(-dir.z, 0, dir.x);
      if (mid.clone().add(n).distanceTo(this.centre) < mid.distanceTo(this.centre)) {
        n.negate();
      }

      let role: string;
      let accent = false;
      if (side.isMainAccess) {
        role = 'ENTRANCE';
        accent = true;
      } else if (side.id === gardenSide) {
        role = 'BACKYARD, POOL';
        accent = true;
      } else {
        role = 'NEIGHBOUR';
      }

      const d = dist.get(side.id);
      const sprite = makeLabel(
        String(side.id), role, side.adjacency,
        d === undefined ? '' : `${d.toFixed(2)} m from wall`, accent);
      sprite.position.copy(mid).addScaledVector(n, 6.5).setY(4.2);
      this.labelGroup.add(sprite);
    }
  }

  setLabelsVisible(v: boolean) { this.labelGroup.visible = v; }

  /** Direction of the plot's own grid, as a unit vector in three coordinates.
   *  Used to square the plot to the screen so the entrance and backyard sides
   *  read as front and back rather than as corners of a diamond. */
  private gridUp(): THREE.Vector3 {
    const b = THREE.MathUtils.degToRad(this.data.site.gridBearingDeg);
    return new THREE.Vector3(Math.sin(b), 0, -Math.cos(b)).normalize();
  }

  /** Snap the camera to a named view. */
  setView(kind: 'aerial' | 'plan' | 'entrance') {
    const up = this.gridUp();                      // toward side 4, NNE
    const across = new THREE.Vector3(-up.z, 0, up.x); // perpendicular, toward side 3

    this.controls.target.copy(this.centre);
    if (kind === 'plan') {
      // Straight down, with the plot grid squared to the screen. A tiny tilt
      // off vertical keeps the orbit controls out of their gimbal case.
      this.camera.up.copy(up);
      this.camera.position.copy(this.centre)
        .addScaledVector(up, -0.001)
        .setY(96);
    } else {
      this.camera.up.set(0, 1, 0);
      if (kind === 'entrance') {
        // From over the road, so the entrance face is toward the viewer.
        this.camera.position.copy(this.centre)
          .addScaledVector(across, -52)
          .addScaledVector(up, -14)
          .setY(34);
      } else {
        // From over the landscape plot, so the backyard and pool are in front.
        this.camera.position.copy(this.centre)
          .addScaledVector(across, 50)
          .addScaledVector(up, -30)
          .setY(40);
      }
    }
    this.camera.lookAt(this.controls.target);
    this.controls.update();
  }

  showOption(option: MassingOption) {
    this.buildLabels(option);
    this.optionGroup.clear();
    const h = this.data.heights;

    const matG = new THREE.MeshStandardMaterial({ color: COLOURS.massGround, roughness: 0.85 });
    const matF = new THREE.MeshStandardMaterial({ color: COLOURS.massFirst, roughness: 0.85 });
    const matGar = new THREE.MeshStandardMaterial({ color: COLOURS.garage, roughness: 0.9 });

    this.optionGroup.add(extrude(option.deck, 0.12, 0.0,
      new THREE.MeshStandardMaterial({ color: COLOURS.deck, roughness: 1 })));
    this.optionGroup.add(extrude(option.driveway, 0.1, 0.0,
      new THREE.MeshStandardMaterial({ color: COLOURS.drive, roughness: 1 })));

    // The deck is 0.12 m thick with the pool cut out of it, so the water sits
    // just below the deck top and reads through the opening.
    const water = extrude(option.pool, 0.02, 0.085, new THREE.MeshStandardMaterial({
      color: COLOURS.pool, roughness: 0.15, metalness: 0.1,
    }));
    water.traverse((o) => { if (o instanceof THREE.Mesh) o.castShadow = false; });
    this.optionGroup.add(water);

    // Ground storey, then the first floor on top, then the parapet band.
    this.optionGroup.add(extrude(option.ground, h.ground, 0, matG));
    this.optionGroup.add(extrude(option.first, h.first, h.ground, matF));
    this.optionGroup.add(extrude(option.first, h.parapet, h.ground + h.first, matG));
    this.optionGroup.add(extrude(option.garage, 0.02, h.ground + 0.01, matGar));
  }

  /** Place the sun from an altitude and azimuth in degrees. */
  setSun(altitudeDeg: number, azimuthDeg: number) {
    const alt = THREE.MathUtils.degToRad(Math.max(altitudeDeg, -5));
    const az = THREE.MathUtils.degToRad(azimuthDeg);
    const d = 180;
    this.sun.target.position.copy(this.centre);
    this.fill.position.set(this.centre.x - 60, 40, this.centre.z - 70);
    this.sun.position.set(
      this.centre.x + d * Math.cos(alt) * Math.sin(az),
      d * Math.sin(alt),
      this.centre.z - d * Math.cos(alt) * Math.cos(az),
    );

    const up = altitudeDeg > 0;
    // Warmer and dimmer as the sun drops, and off entirely below the horizon.
    const t = THREE.MathUtils.clamp(altitudeDeg / 35, 0, 1);
    this.sun.intensity = up ? 0.5 + 2.4 * t : 0;
    this.sun.color.setHSL(0.09 - 0.03 * t, 0.55 - 0.35 * t, 0.55 + 0.15 * t);
    this.hemi.intensity = up ? 0.95 + 0.7 * t : 0.40;
    this.fill.intensity = up ? 0.30 + 0.25 * t : 0.12;

    const night = new THREE.Color(0x253140);
    const day = new THREE.Color(COLOURS.sky);
    const col = up ? night.clone().lerp(day, 0.25 + 0.75 * t) : night;
    (this.scene.background as THREE.Color).copy(col);
    (this.scene.fog as THREE.Fog).color.copy(col);
  }

  setEnvelopeVisible(v: boolean) { this.envelopeLine.visible = v; }
  setWallsVisible(v: boolean) { this.wallGroup.visible = v; }

  resize() {
    const { clientWidth: w, clientHeight: hh } = this.container;
    if (!w || !hh) return;
    this.camera.aspect = w / hh;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, hh, false);
  }

  start() {
    const loop = () => {
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
      requestAnimationFrame(loop);
    };
    loop();
  }
}
