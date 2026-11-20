// The world of "Banjir Bir London" as one three.js scene: sky + light rig (from the bridge short), the brewery hall
// (brick walls, open truss roof inside / tiled roof outside, three giant wooden vats with iron hoops that burst into
// flying staves), the back wall that gives way in blocks, the street of houses behind it, the beer flood (a height
// field recomputed every frame from story.ts floodH, foam in vertex colours), the court, the explanation vat, the
// buffet table, the iron tank of the aftermath, and the cast. update(id, f, camera) poses everything (pure in id + f).
import * as THREE from "three";
import { getInputProps } from "remotion";
import { Batch, boxGeo, V, lam, Kit, Ray, house, prop, setSight, quad, tri } from "./build";
import { rep, ctex, cobbleHD, grassHD, stoneHD, roofHD, brick, cloudHD, rng } from "./paint";
import { Pen } from "./toon";
import { LIGHTS, LOOK, LightPreset } from "./lights";
import { TONE, CHAR, twoTone, untone } from "./shade";
import { NOINK } from "./ink";
import { Pool, Actor, Fx, stage } from "./cast";
import { LADDER } from "./cast";
import {
  FPS, SHOTS, ShotDef, camAt, V3, VATS, Vat, HALL, STREET, T_B, T_HIT, T_W, T_SLIP, T_CLANG, SLIP_HOOP, floodH, foamAt, smooth, clamp01,
  COURT, DEMO_VAT, BUFFET, TANK, AFTER,
} from "./story";

export const loadKit = () => Promise.resolve({} as Kit); // no external models: every tree/bush is procedural

const SUN_SHOT: Record<number, { az?: number; el?: number }> = {};
const discTex = () => ctex("sunDisc", 128, 128, (g) => {
  const gr = g.createRadialGradient(64, 64, 58, 64, 64, 64); gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
});
const haloTex = () => ctex("sunHalo", 256, 256, (g) => {
  const im = g.createImageData(256, 256);
  for (let y = 0; y < 256; y++) for (let x = 0; x < 256; x++) {
    const u = Math.hypot(x - 127.5, y - 127.5) / 128;
    const a = (0.55 * Math.exp(-((u / 0.25) ** 2)) + 0.35 * Math.exp(-((u / 0.6) ** 2))) * (1 - Math.min(1, Math.max(0, (u - 0.8) / 0.2)));
    const i = (y * 256 + x) * 4; im.data[i] = im.data[i + 1] = im.data[i + 2] = 255; im.data[i + 3] = Math.round(255 * Math.min(1, a));
  }
  g.putImageData(im, 0, 0);
});
const smokeTex = () => ctex("smoke", 256, 256, (g) => {
  const p = new Pen(g);
  for (const [x, y, r, c] of [[90, 150, 60, "#8f8d96"], [150, 120, 70, "#a3a1aa"], [170, 165, 55, "#8f8d96"], [120, 100, 50, "#b4b2ba"]] as const) p.ell(x, y, r, r * 0.85, c, 0);
});
/** vertical oak staves with dark seams; 8 staves per tile */
const staveTex = () => ctex("staves", 1024, 512, (g, r) => {
  const cols = ["#b98352", "#ad7748", "#c28c58", "#a87245", "#b47e4e"];
  for (let i = 0; i < 8; i++) {
    g.fillStyle = cols[Math.floor(r() * cols.length)]; g.fillRect(i * 128, 0, 128, 512);
    g.strokeStyle = "rgba(90,50,25,0.25)"; g.lineWidth = 2;
    for (let k = 0; k < 6; k++) { const x = i * 128 + 10 + r() * 108; g.beginPath(); g.moveTo(x, 0); g.bezierCurveTo(x + 6, 170, x - 6, 340, x + 3, 512); g.stroke(); }
    g.fillStyle = "rgba(255,235,200,0.18)"; g.fillRect(i * 128 + 6, 0, 10, 512);
    g.fillStyle = "#3a2214"; g.fillRect(i * 128, 0, 5, 512);
  }
});
const signTex = (text: string, w: number, h: number, bg = "#2f4a3a", fg = "#f3e3b5") => ctex("sign" + text, w, h, (g) => {
  g.fillStyle = bg; g.fillRect(0, 0, w, h);
  g.strokeStyle = fg; g.lineWidth = h * 0.06; g.strokeRect(h * 0.08, h * 0.08, w - h * 0.16, h * 0.84);
  g.fillStyle = fg; g.font = `bold ${Math.round(h * 0.5)}px Georgia, serif`; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText(text, w / 2, h * 0.54);
});

/** every lens position of the street shots (houses that block one are left out) */
const sightLines = (): Ray[] => {
  const out: Ray[] = [];
  for (const s of SHOTS) {
    if (s.set !== "street" || s.id === 2) continue;
    for (let f = s.a - 8; f < s.b + 8; f += 2) {
      if ((s.id === 9 && f >= 1006) || (s.id === 14 && f >= 1796)) continue;
      const c = camAt(s.id, Math.max(0, f)), o = V(...c.pos), look = V(...c.look);
      const fw = look.clone().sub(o), len = fw.length();
      fw.normalize();
      const rt = fw.clone().cross(V(0, 1, 0)).normalize(), up = rt.clone().cross(fw);
      const ty = Math.tan((c.fov * Math.PI) / 360), tx = ty * (9 / 16);
      for (const [sx, sy] of [[0, 0], [-0.6, 0], [0.6, 0], [0, 0.6], [0, -0.4]])
        out.push({ o, d: fw.clone().addScaledVector(rt, sx * tx).addScaledVector(up, sy * ty), len, core: sx === 0 && sy === 0 });
    }
  }
  return out;
};

const flat = (x0: number, x1: number, z0: number, z1: number, y: number, tile: number) => {
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute([x0, y, z1, x1, y, z1, x1, y, z0, x0, y, z1, x1, y, z0, x0, y, z0], 3));
  g.setAttribute("normal", new THREE.Float32BufferAttribute([0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0], 3));
  const u = (x1 - x0) / tile, v = (z1 - z0) / tile;
  g.setAttribute("uv", new THREE.Float32BufferAttribute([0, 0, u, 0, u, v, 0, 0, u, v, 0, v], 2));
  return g;
};

type Piece = { m: THREE.Matrix4 };
/** one wooden vat: intact mesh (staves + hoops + beer top) and its burst pieces (instanced) */
class VatRig {
  intact = new THREE.Group();
  hoops: THREE.Mesh[] = [];
  pieces: THREE.InstancedMesh;
  fallen: THREE.InstancedMesh;
  N: number;
  constructor(public v: Vat, root: THREE.Object3D, staveM: THREE.Material, ironM: THREE.Material, beerM: THREE.Material, foamM: THREE.Material, plankM: THREE.Material) {
    const { r, h } = v;
    this.N = Math.round((2 * Math.PI * r) / 0.75);
    const sm = staveM.clone() as THREE.MeshLambertMaterial;
    sm.map = rep(staveTex(), this.N / 8, 1); sm.onBeforeCompile = (staveM as THREE.MeshLambertMaterial).onBeforeCompile; sm.customProgramCacheKey = (staveM as THREE.MeshLambertMaterial).customProgramCacheKey;
    const body = new THREE.Mesh(new THREE.CylinderGeometry(r, r * 1.04, h, 64, 1, true).translate(0, h / 2, 0), sm);
    const rim = new THREE.Mesh(new THREE.TorusGeometry(r - 0.06, 0.09, 8, 64).rotateX(Math.PI / 2).translate(0, h, 0), plankM);
    const inner = new THREE.Mesh(new THREE.CylinderGeometry(r - 0.12, r - 0.12, 0.8, 48, 1, true).translate(0, h - 0.4, 0), new THREE.MeshBasicMaterial({ color: "#2a170b", side: THREE.BackSide }));
    const top = new THREE.Mesh(new THREE.CircleGeometry(r - 0.13, 48).rotateX(-Math.PI / 2).translate(0, h - 0.45, 0), beerM);
    const froth = new THREE.Mesh(new THREE.RingGeometry(r - 0.38, r - 0.12, 48).rotateX(-Math.PI / 2).translate(0, h - 0.44, 0), foamM);
    this.intact.add(body, rim, inner, top, froth);
    for (const y of v.hoops) {
      const rr = r * (1.04 - 0.04 * (y / h)) + 0.03;
      const hp = new THREE.Mesh(new THREE.TorusGeometry(rr, 0.075, 8, 72).rotateX(Math.PI / 2), ironM);
      hp.position.y = y; this.hoops.push(hp); root.add(hp);
    }
    this.intact.position.set(v.x, 0, v.z);
    this.hoops.forEach((hp) => hp.position.set(v.x, hp.position.y, v.z));
    this.intact.traverse((o) => { const m = o as THREE.Mesh; if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
    this.hoops.forEach((m) => { m.castShadow = true; m.receiveShadow = true; });
    root.add(this.intact);
    const pw = (2 * Math.PI * r) / this.N + 0.02;
    this.pieces = new THREE.InstancedMesh(new THREE.BoxGeometry(pw, h / 2, 0.16), plankM, this.N * 2);
    this.pieces.castShadow = true; this.pieces.receiveShadow = true; this.pieces.frustumCulled = false; this.pieces.visible = false;
    root.add(this.pieces);
    this.fallen = this.pieces; // alias (one mesh for all pieces)
  }
  /** pose for story time tau; tb = burst time (Infinity = never); slip = the slipping hoop index */
  pose(tau: number, tb: number, slip = -1, wobble = 0) {
    const { v } = this, { r, h } = v;
    const burst = tau >= tb;
    this.intact.visible = !burst;
    this.pieces.visible = burst;
    const s = 1 + wobble;
    this.intact.scale.set(s, 1, s);
    const q = new THREE.Quaternion(), e = new THREE.Euler(), m4 = new THREE.Matrix4(), p = V(0, 0, 0), one = V(1, 1, 1);
    this.hoops.forEach((hp, k) => {
      const y0 = v.hoops[k];
      if (!burst) {
        if (k === slip && tau >= T_SLIP) {
          const u = clamp01((tau - T_SLIP) / (T_CLANG - T_SLIP)), bounce = tau > T_CLANG ? 0.12 * Math.abs(Math.sin((tau - T_CLANG) * 14)) * Math.exp(-(tau - T_CLANG) * 6) : 0;
          hp.position.y = y0 + (0.12 - y0) * u * u + bounce;
          hp.rotation.set(0.06 * u, 0, 0.04 * u);
          hp.scale.setScalar(1 + 0.03 * u);
        } else { hp.position.y = y0; hp.rotation.set(0, 0, 0); hp.scale.setScalar(s); }
        return;
      }
      // after the burst: the hoops drop, open a little, land tilted
      const dt = tau - tb, fall = Math.min(1, (dt * dt * 4.9) / Math.max(0.1, y0));
      const yy = k === slip ? 0.12 : y0 + (0.08 + 0.05 * k - y0) * fall;
      hp.position.y = yy;
      hp.scale.setScalar(1 + 0.18 * Math.min(1, dt * 3));
      hp.rotation.set(0.12 * fall * Math.sin(k * 2.1), 0, 0.1 * fall * Math.cos(k * 1.7));
    });
    if (!burst) return;
    const dt = tau - tb, R = rng(Math.round(v.x * 13 + v.z * 7) + 99);
    for (let i = 0; i < this.N; i++) {
      const th = (2 * Math.PI * (i + 0.5)) / this.N, ox = Math.cos(th), oz = Math.sin(th);
      const ra = R(), rb = R(), rc = R();
      // lower half: hinges outward at its base and lies flat
      const phi = Math.min(Math.PI / 2 - 0.04, 0.5 * (10 + 8 * ra) * dt * dt);
      const tan = V(-oz, 0, ox), base = V(v.x + ox * r, 0, v.z + oz * r);
      q.setFromAxisAngle(tan, -phi).multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), -th + Math.PI / 2));
      const c = V(0, h / 4, 0).applyAxisAngle(tan, -phi).add(base);
      const fl = floodH(c.x, c.z, tau);
      if (phi > 1.2 && fl > 0.1) c.y = Math.max(c.y, fl + 0.02);
      this.pieces.setMatrixAt(i * 2, m4.compose(c, q, one));
      // upper half: flies outward, spins, lands flat (and floats)
      const vo = 5 + 4 * rb, vu = 2.5 + 3.5 * rc, T = (vu + Math.sqrt(vu * vu + 2 * 9.8 * (h * 0.75 - 0.1))) / 9.8, tl = Math.min(dt, T);
      p.set(v.x + ox * (r + vo * tl), h * 0.75 + vu * tl - 4.9 * tl * tl, v.z + oz * (r + vo * tl));
      const spin = (6 + 5 * ra) * tl;
      if (dt >= T) {
        const f2 = floodH(p.x, p.z, tau);
        p.y = Math.max(0.09, f2 > 0 ? f2 + 0.02 : 0.09);
        e.set(Math.PI / 2, th * 3.1, 0);
        q.setFromEuler(e);
      } else q.setFromAxisAngle(tan, -spin).multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), -th + Math.PI / 2));
      this.pieces.setMatrixAt(i * 2 + 1, m4.compose(p, q, one));
    }
    this.pieces.instanceMatrix.needsUpdate = true;
  }
}

type Mats = Record<string, THREE.Material>;

export class World {
  root = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private hemi: THREE.HemisphereLight; private sun: THREE.DirectionalLight;
  private sky: THREE.Mesh; private skyMat: THREE.ShaderMaterial;
  private fog = new THREE.Fog("#bccbec", 25, 420);
  private sunDisc: THREE.Sprite; private sunHalo: THREE.Sprite;
  private sunCache = new Map<number, THREE.Vector3>();
  private cloudMaps: Record<"day" | "golden", THREE.Texture[]>;
  private clouds: THREE.Mesh[] = [];
  private smoke: { m: THREE.Mesh; mat: THREE.MeshLambertMaterial; top: V3; k: number }[] = [];
  private roof = new THREE.Group();
  private vats: VatRig[] = [];
  private demo: VatRig;
  private ladder = new THREE.Group();
  private blocks: { m: THREE.Mesh; x: number; y: number; k: number }[] = [];
  private flood: THREE.Mesh; private fx0 = -16; private fz0 = -28; private fstep = 0.5; private fnx: number; private fnz: number;
  private flyers: THREE.Mesh[] = [];
  private tank = new THREE.Group();
  private frustum = new THREE.Frustum();
  private m4 = new THREE.Matrix4(); private v = new THREE.Vector3(); private sph = new THREE.Sphere();

  constructor(kit: Kit) {
    const R = this.root, M: Mats = {};
    // ---- sky + light (bridge rig) ----
    this.skyMat = new THREE.ShaderMaterial({
      uniforms: { c0: { value: new THREE.Color() }, c1: { value: new THREE.Color() }, c2: { value: new THREE.Color() },
        c3: { value: new THREE.Color() }, c4: { value: new THREE.Color() }, e: { value: new THREE.Vector4() } },
      vertexShader: "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
      fragmentShader: `uniform vec3 c0, c1, c2, c3, c4; uniform vec4 e; varying vec3 vP;
        void main(){ float el = asin(clamp(normalize(vP).y, -1.0, 1.0));
          vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el));
          c = mix(c, c2, smoothstep(e.x, e.y, el));
          c = mix(c, c3, smoothstep(e.y, e.z, el));
          c = mix(c, c4, smoothstep(e.z, e.w, el));
          gl_FragColor = vec4(c, 1.0); }`,
      side: THREE.BackSide, depthWrite: false, fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(1100, 48, 24), this.skyMat);
    this.sky.renderOrder = -1; this.sky.frustumCulled = false; this.sky.layers.set(NOINK);
    R.add(this.sky);
    this.sunDisc = new THREE.Sprite(new THREE.SpriteMaterial({ map: discTex(), color: new THREE.Color(6.0, 4.4, 2.4), fog: false, depthWrite: false }));
    this.sunHalo = new THREE.Sprite(new THREE.SpriteMaterial({ map: haloTex(), color: new THREE.Color(1, 1, 1), fog: false, depthWrite: false, depthTest: true, transparent: true, blending: THREE.AdditiveBlending }));
    this.sunDisc.renderOrder = -0.5; this.sunHalo.renderOrder = 5;
    for (const m of [this.sunDisc, this.sunHalo]) { m.frustumCulled = false; m.layers.set(NOINK); R.add(m); }
    this.hemi = new THREE.HemisphereLight("#cfe6ff", "#6c5c8c", 1.1);
    this.sun = new THREE.DirectionalLight("#fff0d6", 2.6);
    this.sun.castShadow = true;
    { const sz = (getInputProps() as { post?: { shadow?: number } }).post?.shadow ?? 4096; this.sun.shadow.mapSize.set(sz, sz); }
    R.add(this.hemi, this.sun, this.sun.target);
    this.cloudMaps = { day: [0, 1, 2, 3].map((k) => cloudHD(k, LOOK.day.cloud)), golden: [0, 1, 2, 3].map((k) => cloudHD(k, LOOK.golden.cloud)) };
    for (let i = 0; i < 11; i++) {
      const a = (i / 11) * Math.PI * 2 + 0.3, d = 600 + (i % 3) * 60;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: this.cloudMaps.day[i % 4], color: new THREE.Color(1.1, 1.1, 1.1), transparent: true, depthWrite: false, fog: false }));
      const w = 130 + (i % 4) * 30;
      m.position.set(Math.cos(a) * d, 110 + (i % 4) * 45, Math.sin(a) * d); m.scale.set(w, w / 2, 1);
      m.layers.set(NOINK); this.clouds.push(m); R.add(m);
    }
    // a cloud right above the court for "salah Tuhan"
    {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: this.cloudMaps.day[1], color: new THREE.Color(1.15, 1.15, 1.15), transparent: true, depthWrite: false, fog: false }));
      m.position.set(COURT[0] + 8, 70, COURT[2] + 40); m.scale.set(60, 30, 1); m.layers.set(NOINK); this.clouds.push(m); R.add(m);
    }

    // ---- materials ----
    M.grass = lam("grassHD", () => ({ map: grassHD() }));
    M.cobble = lam("cobbleHD", () => ({ map: cobbleHD() }));
    M.flag = lam("flagHD", () => ({ map: stoneHD("flagHD", ["#cbbfa9", "#c1b49d", "#d3c8b3", "#b9ab93"], "#8f8270") }));
    M.brick = lam("brickWall", () => ({ map: brick() }));
    M.wood = lam("woodBeam", () => ({ color: "#8a5a36" }));
    M.dark = lam("darkWood", () => ({ color: "#5a3b26" }));
    M.plank = lam("plank", () => ({ color: "#b07a48" }));
    M.iron = twoTone(new THREE.MeshPhongMaterial({ color: "#3d414c", specular: "#8a8a8a", shininess: 60 }), 0.15);
    M.steel = twoTone(new THREE.MeshPhongMaterial({ color: "#8a9099", specular: "#c0c0c0", shininess: 40 }), 0.15);
    M.beer = lam("beerTop", () => ({ color: "#24120a" }));
    M.foam = lam("foamTop", () => ({ color: "#efe0ba" }));
    M.stave = lam("staveM", () => ({ map: staveTex() }));
    M.white = lam("whiteStone", () => ({ color: "#efe6d4" }));
    M.cloth = lam("cloth", () => ({ color: "#f4efe2" }));
    M.roof = lam("roofBrew", () => ({ map: roofHD("#8f97a8", true), side: THREE.DoubleSide }));

    // ---- ground ----
    const b = new Batch();
    b.add(flat(-700, 700, -700, 700, -0.03, 4), M.grass);
    b.add(flat(-STREET, STREET, HALL.z1, 110, 0, 3), M.cobble);                  // the street
    b.add(flat(-30, 30, HALL.z1 - 0.01, HALL.z1 + 3.2, -0.005, 3), M.cobble);    // the lane along the back wall
    b.add(flat(HALL.x0, HALL.x1, HALL.z0, HALL.z1, 0, 2.2), M.flag);             // hall floor
    b.add(flat(COURT[0] - 14, COURT[0] + 14, COURT[2] - 14, COURT[2] + 3, 0, 3), M.cobble);
    // ---- hall walls (the breach part of the back wall is separate blocks) ----
    const { x0, x1, z0, z1, h, wall } = HALL;
    b.add(boxGeo(V(x0 - wall, 0, z0 - wall), V(x0, h, z1 + wall), 1.4), M.brick);
    b.add(boxGeo(V(x1, 0, z0 - wall), V(x1 + wall, h, z1 + wall), 1.4), M.brick);
    b.add(boxGeo(V(x0, 0, z0 - wall), V(x1, h, z0), 1.4), M.brick);
    b.add(boxGeo(V(x0, 0, z1), V(-STREET, h, z1 + wall), 1.4), M.brick);
    b.add(boxGeo(V(STREET, 0, z1), V(x1, h, z1 + wall), 1.4), M.brick);
    b.add(boxGeo(V(x0 - wall, h - 0.6, z1 - 0.1), V(x1 + wall, h, z1 + wall + 0.1), 1.4), M.brick); // lintel over the breach
    // trusses inside
    for (let z = -3.5; z > z0; z -= 4) {
      b.add(boxGeo(V(x0, h - 0.7, z - 0.18), V(x1, h - 0.35, z + 0.18)), M.wood);
      b.add(boxGeo(V(-0.18, h - 0.35, z - 0.15), V(0.18, h + 4.5, z + 0.15)), M.wood);
    }
    // barrels + sacks along the walls
    const keg = new THREE.CylinderGeometry(0.42, 0.42, 1.0, 16).translate(0, 0.5, 0);
    for (let i = 0; i < 9; i++) b.add(keg, M.plank, new THREE.Matrix4().makeTranslation(x0 + 1.0 + (i % 3) * 0.9, (i >= 6 ? 1.0 : 0), -26.5 + Math.floor(i / 3) * 0.9 - (i >= 6 ? 1.8 : 0)));
    for (let i = 0; i < 6; i++) b.add(keg, M.plank, new THREE.Matrix4().makeTranslation(x1 - 1.0 - (i % 2) * 0.9, 0, -3 - Math.floor(i / 2) * 0.9));
    // the boss's desk
    b.add(boxGeo(V(10.4, 0, -24.35), V(12.0, 0.95, -23.75)), M.dark);
    // ---- court: columns + pediment in front of a big house ----
    for (let i = 0; i < 4; i++) b.add(new THREE.CylinderGeometry(0.35, 0.4, 8, 16).translate(0, 4, 0), M.white, new THREE.Matrix4().makeTranslation(COURT[0] - 6 + i * 4, 0, COURT[2] + 3.6));
    b.add(boxGeo(V(COURT[0] - 7.5, 8, COURT[2] + 3), V(COURT[0] + 7.5, 8.8, COURT[2] + 4.4)), M.white);
    b.add(tri(V(COURT[0] - 7.5, 8.8, COURT[2] + 3.0), V(COURT[0] + 7.5, 8.8, COURT[2] + 3.0), V(COURT[0], 11.2, COURT[2] + 3.0)), M.white);
    b.add(boxGeo(V(COURT[0] - 1.25, 0, COURT[2] + 0.75), V(COURT[0] + 1.25, 0.97, COURT[2] + 1.25)), M.dark);       // judge's desk
    b.add(boxGeo(V(COURT[0] - 1.35, 0.97, COURT[2] + 0.7), V(COURT[0] + 1.35, 1.05, COURT[2] + 1.3)), M.wood);
    b.add(boxGeo(V(COURT[0] - 1.6, 0, COURT[2] + 1.3), V(COURT[0] + 1.6, 0.35, COURT[2] + 2.6)), M.wood); // dais
    // ---- buffet table ----
    b.add(boxGeo(V(BUFFET[0] - 2.75, 0, BUFFET[2] - 0.35), V(BUFFET[0] - 0.65, 0.95, BUFFET[2] + 0.35)), M.cloth);
    b.build(R);

    // ---- houses, trees (culled on the street sight lines) ----
    const hb = new Batch(), r = rng(7);
    setSight(sightLines());
    const pick = <T,>(a: T[]) => a[Math.floor(r() * a.length) % a.length];
    for (const sx of [-1, 1]) {
      let z = 3.6;
      while (z < 104) {
        const w = pick([7, 9]), hh = pick([7, 8.4, 9.8]);
        house(hb, sx * (STREET + 4), z + w / 2, sx < 0 ? Math.PI / 2 : -Math.PI / 2, w, 8, hh, Math.floor(r() * 8));
        z += w + 0.3;
      }
      // second row + around the brewery
      let z2 = -40;
      while (z2 < 100) {
        const w = pick([7, 9]), hh = pick([7, 8.4, 9.8]);
        if (z2 > 4 || z2 < -34) house(hb, sx * (STREET + 17 + r() * 2), z2 + w / 2, sx < 0 ? Math.PI / 2 : -Math.PI / 2, w, 8, hh, Math.floor(r() * 8));
        z2 += w + 1 + r() * 3;
      }
      for (let z3 = -26; z3 < 0; z3 += 9) house(hb, sx * 23, z3 + 4, sx < 0 ? Math.PI / 2 : -Math.PI / 2, 8, 8, 8.4, Math.floor(r() * 8));
    }
    for (let x = -40; x <= 40; x += 10) house(hb, x, -44, 0, 9, 8, pick([7, 8.4, 9.8]), Math.floor(r() * 8));
    setSight([]);
    // court building, explanation + buffet backdrops (never culled)
    house(hb, COURT[0], COURT[2] + 9, Math.PI, 18, 10, 9.8, 7);
    for (const dx of [-16, 16]) house(hb, COURT[0] + dx, COURT[2] + 9, Math.PI, 9, 8, 8.4, Math.floor(r() * 8));
    house(hb, BUFFET[0], BUFFET[2] + 9, Math.PI, 12, 10, 8.4, 1);
    house(hb, BUFFET[0] - 11, BUFFET[2] + 9, Math.PI, 9, 8, 7, 4);
    house(hb, BUFFET[0] + 11, BUFFET[2] + 9, Math.PI, 9, 8, 9.8, 6);
    const trees = ["tree_oak", "tree_default", "tree_detailed", "tree_fat", "tree-high-round"];
    for (let i = 0; i < 90; i++) {
      const x = (r() - 0.5) * 300, z = (r() - 0.5) * 300;
      if (Math.abs(x) < 34 && z > -50 && z < 110) continue;
      if (Math.hypot(x - COURT[0], z - COURT[2]) < 22 || Math.hypot(x - DEMO_VAT.x, z - DEMO_VAT.z) < 14 || Math.hypot(x - BUFFET[0], z - BUFFET[2]) < 16) continue;
      prop(hb, kit, pick(trees), x, 0, z, 7 + r() * 4, r() * 6);
    }
    for (const [x, z, n] of [[DEMO_VAT.x - 9, DEMO_VAT.z + 12, "tree_oak"], [DEMO_VAT.x + 8, DEMO_VAT.z + 15, "tree_fat"], [DEMO_VAT.x - 2, DEMO_VAT.z + 22, "tree_default"],
      [COURT[0] - 12, COURT[2] + 2, "tree_oak"], [COURT[0] + 12, COURT[2] + 1, "tree_detailed"], [BUFFET[0] - 7, BUFFET[2] + 3, "tree_fat"], [BUFFET[0] + 7, BUFFET[2] + 2.5, "tree_oak"]] as const)
      prop(hb, kit, n, x, 0, z, 8, x);
    hb.build(R);
    setSight([]);

    // ---- brewery roof (outside shots only), gable + sign, chimney ----
    const rb = new Batch(), o = 0.5, rh = 6;
    rb.add(quad(V(x0 - wall - o, h - 0.2, z1 + wall + o), V(0, h + rh, z1 + wall + o), V(0, h + rh, z0 - wall - o), V(x0 - wall - o, h - 0.2, z0 - wall - o), 8, 8), M.roof);
    rb.add(quad(V(0, h + rh, z1 + wall + o), V(x1 + wall + o, h - 0.2, z1 + wall + o), V(x1 + wall + o, h - 0.2, z0 - wall - o), V(0, h + rh, z0 - wall - o), 8, 8), M.roof);
    rb.add(tri(V(x0 - wall, h, z0 - wall), V(x1 + wall, h, z0 - wall), V(0, h + rh, z0 - wall)), M.brick);
    rb.build(this.roof);
    R.add(this.roof);
    const gable = new Batch();
    gable.add(tri(V(x0 - wall, h, z1 + wall), V(x1 + wall, h, z1 + wall), V(0, h + rh, z1 + wall)), M.brick);
    gable.add(tri(V(x1 + wall, h, z1), V(x0 - wall, h, z1), V(0, h + rh, z1)), M.brick);
    gable.build(R);
    const sign = new THREE.Mesh(new THREE.PlaneGeometry(10, 1.6), new THREE.MeshBasicMaterial({ map: signTex("HORSE SHOE BREWERY", 1600, 256), color: 0xe8e8e8 }));
    sign.position.set(0, h + 1.6, z1 + wall + 0.03); sign.layers.set(NOINK); R.add(sign);
    const cb = new Batch(), chim = lam("chimneyB", () => ({ map: rep(brick(), 2, 8) })), soot = lam("soot", () => ({ color: "#4a3442" }));
    cb.add(new THREE.CylinderGeometry(1.0, 1.4, 26, 14, 1, true), chim, new THREE.Matrix4().makeTranslation(12, 13, -32));
    cb.add(new THREE.CylinderGeometry(1.2, 1.15, 1.3, 14), soot, new THREE.Matrix4().makeTranslation(12, 26.3, -32));
    cb.build(R);
    const smokeT = smokeTex();
    for (let k = 0; k < 7; k++) {
      const mat = new THREE.MeshLambertMaterial({ map: smokeT, transparent: true, depthWrite: false });
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat); m.layers.set(NOINK);
      this.smoke.push({ m, mat, top: [12, 27, -32], k: k / 7 }); R.add(m);
    }

    // ---- the breach blocks (back wall, |x| < STREET) ----
    const bw = (2 * STREET) / 5, bh = (h - 0.6) / 5;
    for (let row = 0; row < 5; row++) for (let col = 0; col < 5; col++) {
      const g = boxGeo(V(-bw / 2, -bh / 2, -wall / 2), V(bw / 2, bh / 2, wall / 2), 1.4, true);
      const m = new THREE.Mesh(g, M.brick); m.castShadow = true; m.receiveShadow = true;
      const x = -STREET + bw * (col + 0.5), y = bh * (row + 0.5);
      m.position.set(x, y, z1 + wall / 2);
      this.blocks.push({ m, x, y, k: row * 5 + col }); R.add(m);
    }

    // ---- vats ----
    VATS.forEach((v) => this.vats.push(new VatRig(v, R, M.stave, M.iron, M.beer, M.foam, M.plank)));
    this.demo = new VatRig(DEMO_VAT, R, M.stave, M.iron, M.beer, M.foam, M.plank);
    // flying staves (V1 -> V2, V2 -> V3)
    for (let i = 0; i < 2; i++) { const m = new THREE.Mesh(new THREE.BoxGeometry(0.8, 3.2, 0.16), M.plank); m.castShadow = true; m.visible = false; this.flyers.push(m); R.add(m); }
    // ladder on V1
    {
      const lb = new Batch(), top = V(LADDER.x, 7.3, LADDER.z), dir = V(Math.cos(LADDER.a), 0, Math.sin(LADDER.a)), base = top.clone().addScaledVector(dir, 1.4).setY(0);
      const side = V(-dir.z, 0, dir.x).multiplyScalar(0.3);
      const rail = (a: THREE.Vector3, c: THREE.Vector3) => {
        const g = new THREE.BoxGeometry(0.08, a.distanceTo(c), 0.08);
        g.applyMatrix4(new THREE.Matrix4().compose(a.clone().add(c).multiplyScalar(0.5), new THREE.Quaternion().setFromUnitVectors(V(0, 1, 0), c.clone().sub(a).normalize()), V(1, 1, 1)));
        return g;
      };
      for (const s of [-1, 1]) lb.add(rail(base.clone().addScaledVector(side, s), top.clone().addScaledVector(side, s)), M.wood);
      for (let k = 1; k < 18; k++) { const p = base.clone().lerp(top, k / 18); lb.add(rail(p.clone().addScaledVector(side, -1), p.clone().addScaledVector(side, 1)), M.wood); }
      lb.build(this.ladder); R.add(this.ladder);
    }
    // the iron tank of the aftermath
    {
      const tb = new Batch();
      tb.add(new THREE.CylinderGeometry(3.0, 3.0, 6.5, 48).translate(0, 3.25, 0), M.steel);
      for (let k = 0; k < 6; k++) tb.add(new THREE.TorusGeometry(3.03, 0.05, 6, 64).rotateX(Math.PI / 2).translate(0, 0.5 + k * 1.1, 0), M.iron);
      tb.add(new THREE.SphereGeometry(3.0, 32, 10, 0, Math.PI * 2, 0, Math.PI / 2).scale(1, 0.3, 1).translate(0, 6.5, 0), M.steel);
      tb.build(this.tank);
      this.tank.position.set(TANK[0], 0, TANK[2]); R.add(this.tank);
    }

    // ---- the beer flood: height field over the hall + street ----
    this.fnx = Math.round((HALL.x1 - HALL.x0) / this.fstep) + 1;
    this.fnz = Math.round((110 - HALL.z0) / this.fstep) + 1;
    const n = this.fnx * this.fnz, pos = new Float32Array(n * 3), col = new Float32Array(n * 3), idx: number[] = [];
    for (let j = 0; j < this.fnz; j++) for (let i = 0; i < this.fnx; i++) {
      const k = j * this.fnx + i;
      pos[k * 3] = this.fx0 + i * this.fstep; pos[k * 3 + 1] = -1; pos[k * 3 + 2] = this.fz0 + j * this.fstep;
      if (i < this.fnx - 1 && j < this.fnz - 1) { const a = k, c = k + 1, d = k + this.fnx, e = k + this.fnx + 1; idx.push(a, d, c, c, d, e); }
    }
    const fg = new THREE.BufferGeometry();
    fg.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    fg.setAttribute("color", new THREE.BufferAttribute(col, 3));
    fg.setIndex(idx);
    const fm = twoTone(new THREE.MeshLambertMaterial({ vertexColors: true }));
    { // beer keeps its own colour in shade: half self-lit (cartoon liquid), the two-tone light only models the form
      const base = fm.onBeforeCompile;
      fm.onBeforeCompile = (sh, rd) => {
        base.call(fm, sh, rd);
        sh.fragmentShader = sh.fragmentShader.replace("#include <opaque_fragment>", "outgoingLight = mix(outgoingLight, diffuseColor.rgb * 1.25, 0.55);\n#include <opaque_fragment>");
      };
      fm.customProgramCacheKey = () => "beerFlood1";
    }
    this.flood = new THREE.Mesh(fg, fm);
    this.flood.receiveShadow = true; this.flood.castShadow = false; this.flood.frustumCulled = false;
    R.add(this.flood);
  }

  private shotSun(id: number, s: ShotDef, L: LightPreset) {
    let v = this.sunCache.get(id);
    if (v) return v;
    let fx = 0, fz = 0;
    for (let f = s.a; f < s.b; f += 3) {
      const c = camAt(id, f), x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2], n = Math.hypot(x, z) || 1;
      fx += x / n; fz += z / n;
    }
    const n = Math.hypot(fx, fz) || 1; fx /= n; fz /= n;
    const az = THREE.MathUtils.degToRad(s.sunAz ?? SUN_SHOT[id]?.az ?? L.az), el = THREE.MathUtils.degToRad(s.sunEl ?? SUN_SHOT[id]?.el ?? L.el);
    const hx = fx * Math.cos(az) - fz * Math.sin(az), hz = fz * Math.cos(az) + fx * Math.sin(az);
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    this.sunCache.set(id, v);
    return v;
  }
  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene) {
    const t = f / FPS, s = SHOTS[id - 1], tau = s.tau(t), L = LIGHTS[s.light];
    const c = camAt(id, f);
    cam.position.set(...c.pos); cam.up.set(0, 1, 0); cam.lookAt(...c.look); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = 0.2; cam.far = 1500; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    const focus = V(...c.look), dist = cam.position.distanceTo(focus);
    cam.layers.enable(NOINK);
    // ---- light rig ----
    const K = LOOK[s.light], sunDir = this.shotSun(id, s, L);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set(L.ground); this.hemi.intensity = L.hemiI;
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    let Rr = THREE.MathUtils.clamp(dist * 1.15 + 9, 14, 95);
    if (s.set === "hall") Rr = Math.max(Rr, 24);
    if (s.light === "golden") Rr = Math.max(Rr, 26);
    this.sun.position.copy(focus).addScaledVector(sunDir, 220); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 20; sc.far = 480; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12);
    TONE.uLitCol.value.set(...L.lit); TONE.uShadeCol.value.set(...L.shade); TONE.uShadeLift.value.set(...L.lift);
    TONE.uLambert.value = L.lambert; TONE.uSideK.value = L.sideK; TONE.uTerm.value = L.term; TONE.uBounce.value.set(...K.bounce); TONE.uSat.value = K.sat;
    CHAR.uCharTint.value.set(...L.charTint); CHAR.uCharShade.value = L.charShade; CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad; CHAR.uSideTint.value.set(...L.sideTint);
    const su = this.skyMat.uniforms;
    K.sky.c.forEach((hx, i) => untone(hx, su["c" + i].value));
    const e = K.sky.e.map((deg) => THREE.MathUtils.degToRad(deg));
    su.e.value.set(e[1], e[2], e[3], e[4]);
    this.sky.position.copy(cam.position);
    untone(L.fog, this.fog.color); this.fog.near = L.fogNear; this.fog.far = L.fogFar;
    scene.fog = this.fog; scene.background = null;
    const showSun = s.light === "golden";
    this.sunDisc.visible = this.sunHalo.visible = showSun;
    if (showSun) {
      this.sunDisc.position.copy(cam.position).addScaledVector(sunDir, 900);
      this.sunDisc.scale.setScalar(2 * 900 * Math.tan(THREE.MathUtils.degToRad(1.7)));
      this.sunHalo.position.copy(this.sunDisc.position); this.sunHalo.scale.setScalar(2 * 900 * Math.tan(THREE.MathUtils.degToRad(24)));
      (this.sunHalo.material as THREE.SpriteMaterial).color.set(L.sunDisc).multiplyScalar(1.3);
    }
    for (let i = 0; i < this.clouds.length; i++) {
      const m = this.clouds[i], mat = m.material as THREE.MeshBasicMaterial;
      m.lookAt(cam.position.x, m.position.y, cam.position.z);
      mat.map = this.cloudMaps[s.light][i % 4];
    }
    for (const sm of this.smoke) {
      const u = (t * 0.11 + sm.k) % 1, sz = 3 + u * 9;
      sm.m.position.set(sm.top[0] - u * 18, sm.top[1] + u * 13 + u * u * 4, sm.top[2] + u * 3);
      sm.m.scale.set(sz, sz, 1); sm.m.quaternion.copy(cam.quaternion);
      sm.mat.opacity = 0.85 * (1 - u) ** 1.2;
    }
    // ---- brewery: roof outside only, vats, ladder, breach, flood ----
    this.roof.visible = !!s.roof;
    const after = tau >= AFTER - 1;
    this.vats.forEach((vr, i) => {
      const tb = T_B[i], wob = i === 0 && tau > 680 / FPS && tau < tb ? 0.006 * Math.sin(tau * 47) * smooth((tau - 680 / FPS) / 0.6) : i === 1 && tau > T_HIT[0] && tau < tb ? 0.006 * Math.sin(tau * 51) : 0;
      vr.pose(tau, tb, i === 0 ? SLIP_HOOP : -1, wob);
    });
    this.demo.pose(tau, Infinity);
    this.ladder.visible = tau < T_B[0];
    this.tank.visible = after;
    // the flying staves
    const fly = [[0, 1, T_B[0] + 0.25, T_HIT[0]], [1, 2, T_B[1] + 0.1, T_HIT[1]]] as const;
    fly.forEach(([a, bI, t0, t1], k) => {
      const m = this.flyers[k], A = VATS[a], B = VATS[bI];
      if (tau < t0 || after) { m.visible = false; return; }
      m.visible = true;
      const dx = B.x - A.x, dz = B.z - A.z, dl = Math.hypot(dx, dz), ux = dx / dl, uz = dz / dl;
      const p0 = V(A.x + ux * (A.r + 0.4), A.h * 0.7, A.z + uz * (A.r + 0.4)), p1 = V(B.x - ux * (B.r + 0.25), B.h * 0.5, B.z - uz * (B.r + 0.25));
      if (tau < t1) {
        const u = (tau - t0) / (t1 - t0);
        m.position.copy(p0).lerp(p1, u); m.position.y += 3.2 * 4 * u * (1 - u);
        m.rotation.set(u * 9, Math.atan2(ux, uz), u * 4);
      } else {
        const d = tau - t1, fl = floodH(p1.x - ux * 0.6, p1.z - uz * 0.6, tau);
        m.position.set(p1.x - ux * (0.3 + 0.5 * Math.min(1, d)), Math.max(fl > 0 ? fl + 0.05 : 0.09, p1.y - 4.9 * d * d), p1.z - uz * (0.3 + 0.5 * Math.min(1, d)));
        m.rotation.set(Math.min(Math.PI / 2, 1.5 + d * 2), Math.atan2(ux, uz), 0);
      }
    });
    // breach blocks: shake, bulge, then blow out into the street
    const R0 = rng(5);
    for (const bl of this.blocks) {
      const ra = R0(), rb = R0(), rc = R0(), row = Math.floor(bl.k / 5);
      const t0 = T_W + 0.05 * row * 0 + 0.03 * ((bl.k * 7) % 5);
      const m = bl.m;
      if (tau < t0) {
        const sh = tau > T_W - 1.0 ? 0.035 * Math.sin(tau * 60 + bl.k) + 0.25 * smooth((tau - (T_W - 1.0)) / 1.0) * Math.exp(-(((bl.x / 4) ** 2) + ((bl.y - 3) / 4) ** 2)) : 0;
        m.position.set(bl.x, bl.y, HALL.z1 + HALL.wall / 2 + sh); m.rotation.set(0, 0, 0); m.visible = true;
        continue;
      }
      const d = tau - t0, vz = 9 + 5 * ra - row * 0.6, vy = 1.5 + 3 * rb, vx = (bl.x / STREET) * (1.5 + 2 * rc);
      const y = bl.y + vy * d - 4.9 * d * d;
      m.position.set(bl.x + vx * d, y, HALL.z1 + HALL.wall / 2 + vz * d);
      m.rotation.set((2 + 4 * ra) * d, (rb - 0.5) * 3 * d, (rc - 0.5) * 4 * d);
      m.visible = y > -2.5 && !after;
    }
    this.poseFlood(tau);
    // ---- cast + effects ----
    const right = V(0, 0, 0).setFromMatrixColumn(cam.matrixWorld, 0);
    const st = stage(id, t, tau, { pos: cam.position, right });
    this.frustum.setFromProjectionMatrix(this.m4.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse));
    const tint = s.light === "golden" ? "#ffcf9e" : "#ffffff";
    let ai = 0;
    const used: Actor[] = [];
    for (const p of st.places) {
      const sc2 = p.scale ?? 1;
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y + 1.1 * sc2, p.z), 3.5))) continue;
      const a = this.actor(ai++);
      const [w, hgt, k] = p.size ?? [300, 500, 0.5];
      a.r = this.pool.req(p.key, w, hgt, k, p.draw);
      a.mesh.visible = true;
      a.mesh.position.set(p.x, p.y, p.z);
      a.mesh.rotation.set(0, p.yaw ?? Math.atan2(cam.position.x - p.x, cam.position.z - p.z), p.roll ?? 0);
      a.mesh.scale.set(p.mirror ? -sc2 : sc2, sc2, sc2);
      if (a.mat.emissiveMap) a.mat.emissive.set(tint);
      a.mesh.castShadow = L.actorShadow;
      used.push(a);
    }
    for (let i = ai; i < this.actors.length; i++) this.actors[i].mesh.visible = false;
    let fi = 0;
    const fused: Fx[] = [];
    for (const p of st.fx) {
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y, p.z), Math.max(p.w, p.h)))) continue;
      const ef = this.fx(fi++);
      ef.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw);
      ef.use(!!p.soft);
      ef.mesh.visible = true;
      ef.mesh.position.set(p.x, p.y, p.z);
      if (p.flat) ef.mesh.rotation.set(-Math.PI / 2, 0, p.rot ?? 0);
      else { ef.mesh.quaternion.copy(cam.quaternion); ef.mesh.rotateZ(p.rot ?? 0); }
      ef.mesh.scale.set(p.w, p.h, 1);
      fused.push(ef);
    }
    for (let i = fi; i < this.fxs.length; i++) this.fxs[i].mesh.visible = false;
    this.pool.flush();
    for (const a of used) a.bind();
    for (const ef of fused) ef.bind();
    return focus;
  }

  private poseFlood(tau: number) {
    const on = tau >= T_B[0] && tau < T_W + 40;
    this.flood.visible = on;
    if (!on) return;
    const g = this.flood.geometry, pos = g.attributes.position.array as Float32Array, col = g.attributes.color.array as Float32Array;
    const body = new THREE.Color("#8a4c22"), deep = new THREE.Color("#5e3114"), foam = new THREE.Color("#f4e6c2"), tmp = new THREE.Color();
    const vn = (x: number, z: number) => { const a = Math.sin(x * 2.3 + z * 1.1 + tau * 1.7) * Math.sin(z * 2.9 - x * 0.7 - tau * 2.3) + 0.5 * Math.sin(x * 5.1 - z * 4.3 + tau * 3.1); return a; };
    for (let j = 0; j < this.fnz; j++) for (let i = 0; i < this.fnx; i++) {
      const k = j * this.fnx + i, x = pos[k * 3], z = pos[k * 3 + 2];
      const hgt = floodH(x, z, tau);
      pos[k * 3 + 1] = hgt > 0.02 ? hgt : -0.6;
      const fo = hgt > 0.02 ? foamAt(x, z, tau) : 0;
      const streak = 0.5 + 0.5 * Math.sin(x * 1.7 + z * 0.9 + tau * 3) * Math.sin(z * 1.3 - tau * 2);
      const patch = smooth((vn(x, z) - 0.75) / 0.25) * 0.75;
      tmp.copy(deep).lerp(body, streak).lerp(foam, Math.min(1, Math.max(fo * 1.2, patch)));
      col[k * 3] = tmp.r; col[k * 3 + 1] = tmp.g; col[k * 3 + 2] = tmp.b;
    }
    g.attributes.position.needsUpdate = true; g.attributes.color.needsUpdate = true;
    g.computeVertexNormals();
  }
}
