// Cast of "Banjir Bir London": the brewery workers, the clerk, the boss, townsfolk, the judge, the buffet man and
// the tax man, as lit flat cards in the 3D world (same card system as the bridge short), plus the 2D effects
// (beer splashes, pressure arrows, clang bursts, coins). stage(id, t, tau, cam) lists everything for one frame.
import * as THREE from "three";
import {
  Pen, bodyFront, bodySide, townsfolk, fxBurst, fxStars, fxCreak, fxShadow, fxContact, INK, SKINS,
  Outfit, Expr, FrontOpts, SideOpts, Prop,
} from "./toon";
import {
  FPS, D0, SHOTS, V3, smooth, clamp01, VATS, T_B, T_W, T_SLIP, T_CLANG, floodH, waveFront, COURT, DEMO, DEMO_VAT, BUFFET, TANK, AFTER, SLIP_HOOP,
} from "./story";
import { NOINK } from "./ink";
import { cardShade, blobMaterial, CARD_K } from "./cardshade";

// ---------------- canvas pool ----------------
type Entry = { cv: HTMLCanvasElement; tex: THREE.CanvasTexture; w: number; h: number };
export type Req = { key: string; w: number; h: number; k: number; draw: (p: Pen) => void; tex?: THREE.CanvasTexture };
const makeEntry = (w: number, h: number): Entry => {
  const cv = document.createElement("canvas");
  cv.width = w; cv.height = h;
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  return { cv, tex, w, h };
};
export class Pool {
  private live = new Map<string, Entry>();
  private free: Entry[] = [];
  private reqs: Req[] = [];
  req(key: string, w: number, h: number, k: number, draw: (p: Pen) => void) {
    const r: Req = { key: `${w}x${h}|${key}`, w, h, k, draw };
    this.reqs.push(r);
    return r;
  }
  flush() {
    const want = new Map<string, Req[]>();
    for (const r of this.reqs) { const l = want.get(r.key); if (l) l.push(r); else want.set(r.key, [r]); }
    for (const [key, e] of this.live) if (!want.has(key)) { this.live.delete(key); this.free.push(e); }
    for (const [key, rs] of want) {
      let e = this.live.get(key);
      if (!e) {
        const r = rs[0], i = this.free.findIndex((x) => x.w === r.w && x.h === r.h);
        e = i >= 0 ? this.free.splice(i, 1)[0] : makeEntry(r.w, r.h);
        const g = e.cv.getContext("2d")!;
        g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, e.w, e.h); g.setTransform(r.k, 0, 0, r.k, 0, 0);
        r.draw(new Pen(g));
        e.tex.needsUpdate = true;
        this.live.set(key, e);
      }
      for (const r of rs) r.tex = e.tex;
    }
    this.reqs = [];
  }
}

// ---------------- sprite meshes ----------------
const blank = (() => { const c = document.createElement("canvas"); c.width = c.height = 2; return new THREE.CanvasTexture(c); })();
export const SU = 0.00216; // metres per design unit: 1000 units = 2.16 m
export const SU_SWING = 2.3 / 1830; // swing canvas: rope of 1830 units = 2.3 m
const BODY = (() => { const g = new THREE.PlaneGeometry(600 * SU, 1000 * SU); g.translate(0, (975 - 500) * SU, 0); return g; })();
const CARD = new THREE.PlaneGeometry(1, 1);
/** world roots that hold actors (to find the scene's sun when world.ts does not pass it) */
const ROOTS = new Set<THREE.Object3D>();

/** lit flat character: cardShade() material, receives shadows (dims to the bright floor only), casts its silhouette
 *  when world.ts says so (golden). Drawn after the contact blobs (renderOrder 1). */
export class Actor {
  mesh: THREE.Mesh; mat: THREE.MeshLambertMaterial; dmat: THREE.MeshDepthMaterial; r: Req | null = null;
  constructor(parent: THREE.Object3D, geo: THREE.BufferGeometry = BODY) {
    this.mat = cardShade(new THREE.MeshLambertMaterial({ map: blank, alphaTest: 0.5, side: THREE.DoubleSide }));
    this.mat.alphaToCoverage = false; // A2C + MSAA left 1 px sky-depth seams on blurred far cards (POST)
    this.dmat = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: blank, alphaTest: 0.5, side: THREE.DoubleSide });
    this.mesh = new THREE.Mesh(geo, this.mat);
    this.mesh.customDepthMaterial = this.dmat;
    // rim width is in output pixels: tell the card shader the render height (1920 = 1080 x 1920 frame)
    this.mesh.onBeforeRender = (r) => { const rt = r.getRenderTarget(); CARD_K.uPx.value = (rt ? rt.height : r.domElement.height) / 1920; };
    this.mesh.castShadow = false; this.mesh.receiveShadow = true; this.mesh.visible = false;
    this.mesh.rotation.order = "YXZ"; this.mesh.renderOrder = 1; this.mesh.layers.set(NOINK);
    parent.add(this.mesh);
    ROOTS.add(parent);
  }
  bind() { const t = this.r?.tex; if (t) { this.mat.map = t; this.dmat.map = t; } }
}
/** unlit effect card: hard cut-out (ink drawings), soft see-through (dust, mist) or a multiply ground blob */
export class Fx {
  mesh: THREE.Mesh; mat: THREE.MeshBasicMaterial; soft: THREE.MeshBasicMaterial; blob: THREE.MeshBasicMaterial; r: Req | null = null;
  constructor(parent: THREE.Object3D) {
    this.mat = new THREE.MeshBasicMaterial({ map: blank, alphaTest: 0.5, side: THREE.DoubleSide });
    this.mat.alphaToCoverage = false; // A2C + MSAA left 1 px sky-depth seams on blurred far cards (POST)
    this.soft = new THREE.MeshBasicMaterial({ map: blank, transparent: true, depthWrite: false, side: THREE.DoubleSide });
    this.blob = blobMaterial(blank);
    this.mesh = new THREE.Mesh(CARD, this.mat);
    this.mesh.visible = false; this.mesh.layers.set(NOINK);
    parent.add(this.mesh);
  }
  use(soft: boolean) { this.mesh.material = soft ? this.soft : this.mat; }
  bind() {
    const t = this.r?.tex;
    if (!t) return;
    if (this.r!.key.includes("|blob|")) {
      // no mipmaps: at grazing views the mip chain averages the blob with its white surround and it fades out
      if (t.generateMipmaps) { t.generateMipmaps = false; t.minFilter = THREE.LinearFilter; t.needsUpdate = true; }
      this.blob.map = t; this.mesh.material = this.blob; this.mesh.renderOrder = 0.5;
    }
    else { this.mat.map = t; this.soft.map = t; this.mesh.renderOrder = 0; }
  }
}

// ---------------- placements ----------------
export type Place = {
  key: string; draw: (p: Pen) => void; x: number; y: number; z: number;
  scale?: number; mirror?: boolean; yaw?: number; geo?: "body" | "swing"; roll?: number; size?: [number, number, number];
};
export type FxPlace = { key: string; cw: number; ch: number; draw: (p: Pen) => void; x: number; y: number; z: number; w: number; h: number; flat?: boolean; rot?: number; soft?: boolean };
/** sun = world direction TOWARD the sun (optional: when absent the scene's shadow-casting light is used) */
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3; sun?: THREE.Vector3 };

const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const q = (v: number, n = 120) => Math.round(v * n) / n;
/** head-shape seed: 7 shapes, so marching soldiers in step still share canvases */
const seedOf = (i: number) => ((i * 5 + 3) % 7) + 1;
/** drawing resolution by distance: [canvas w, h, scale from the 600 x 1000 design]; sized for the 1440 x 2560 final */
const tier = (d: number): [number, number, number] =>
  d < 3.2 ? [1800, 3000, 3.0] : d < 6.5 ? [1080, 1800, 1.8] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4];

// ---------------- light ----------------
const SUN = new THREE.Vector3(0.5, 0.75, -0.4).normalize();
const tmp = new THREE.Vector3();
let LNAME: "day" | "golden" = "day";
const sunOf = (root: THREE.Object3D) => {
  let s: THREE.DirectionalLight | null = null;
  root.traverse((o) => { if (!s && o instanceof THREE.DirectionalLight && o.castShadow) s = o; });
  return s as THREE.DirectionalLight | null;
};
/** the sun of the world that is calling: the attached root whose sun target sits on this camera's view axis */
const findSun = (cam: CamInfo, out: THREE.Vector3) => {
  if (cam.sun) return out.copy(cam.sun).normalize();
  let best: THREE.DirectionalLight | null = null, err = Infinity;
  for (const r of ROOTS) {
    if (!r.parent) continue;
    const s = sunOf(r);
    if (!s) continue;
    const d = tmp.copy(s.target.position).sub(cam.pos), e = Math.abs(d.dot(cam.right)) / (d.length() || 1);
    if (e < err) { err = e; best = s; }
  }
  return best ? out.copy(best.position).sub(best.target.position).normalize() : out;
};
/** canvas angle the sun comes FROM on an upright card facing the camera, in 45-degree steps (small texture cache) */
const light2D = (cam: CamInfo, mirror: boolean) => {
  const sx = SUN.dot(cam.right) * (mirror ? -1 : 1), sy = -SUN.y;
  return Math.round(Math.atan2(sy, sx) / (Math.PI / 4)) * (Math.PI / 4);
};

/** front / side view and mirroring for someone at (x, z) walking along (dx, dz); fs = foreshortening of the walk */
const viewOf = (cam: CamInfo, x: number, z: number, dx: number, dz: number) => {
  const tx = cam.pos.x - x, tz = cam.pos.z - z, tl = Math.hypot(tx, tz) || 1;
  const c = (tx * dx + tz * dz) / tl;
  return { side: c < 0.57, mirror: dx * cam.right.x + dz * cam.right.z < 0, fs: Math.round(Math.sqrt(Math.max(0, 1 - c * c)) * 20) / 20 };
};

// ---------------- life: blinks and reaction timing ----------------
/** reference expression and action changes land 0-3 f before the word onset */
const LEAD = 2 / FPS;
/** eyelid 0 open .. 1 shut. Reference: gaps 0.5-2.3 s, 4-frame blink half / shut / shut / half, plus a blink across
 *  every expression swap (the shut frames hide the swap) */
const LID = [0.5, 1, 1, 0.5];
const lidAt = (t: number, i: number, swaps: number[] = []) => {
  const f = Math.round(t * FPS);
  for (const ts of swaps) { const k = f - Math.round((ts - LEAD) * FPS) + 1; if (k >= 0 && k < 4) return LID[k]; }
  let s = Math.round(-60 * hh(i, 9));
  for (let n = 0; s <= f && n < 400; n++) {
    const k = f - s;
    if (k >= 0 && k < 4) return LID[k];
    s += Math.round(15 + 54 * hh(i * 31 + n, 13)); // next blink 0.5-2.3 s later
  }
  return 0;
};
const fkey = (o: object) => JSON.stringify(o, (_k, v) => (typeof v === "number" ? q(v) : v));

type Who = { i: number; o: Outfit; okey: string };
/** one character drawing in the 600 x 1000 design space, sized by distance, lit from the scene's sun */
const person = (cam: CamInfo, who: Who, x: number, y: number, z: number, view: { side: boolean; mirror: boolean }, fo: FrontOpts, so: SideOpts, scale = 1): Place & { tierKey: string } => {
  const d = cam.pos.distanceTo(tmp.set(x, y + 1.2, z)) / scale;
  const [w, h, k] = tier(d);
  const mirror = view.side && view.mirror, light = light2D(cam, mirror), seed = seedOf(who.i);
  const f2: FrontOpts = { ...fo, light, seed }, s2: SideOpts = { ...so, light, seed };
  const key = view.side ? `S|${who.okey}|${fkey(s2)}` : `F|${who.okey}|${fkey(f2)}`;
  return {
    key, x, y, z, scale, mirror, tierKey: `${w}`,
    draw: (p) => (view.side ? bodySide(p, who.o, s2) : bodyFront(p, who.o, f2)),
    size: [w, h, k],
  };
};

/** ground shadow under a standing / sitting card (review rounds 2-4), multiply, blue-violet: a TIGHT contact pool right under
 *  the feet (~.5 on screen at the core) so nobody floats, plus by day (cards cast no real shadow) a lighter soft tail
 *  stretched AWAY from the sun, length ~1.6 m / tan(sun elevation), capped. Golden: world.ts casts real card shadows. */
const CONTACT: Record<"day" | "golden", [number, number, number]> = { day: [0.2, 0.21, 0.33], golden: [0.24, 0.2, 0.33] };
const TAIL: [number, number, number] = [0.42, 0.44, 0.62];
const toSrgb = (v: number) => { const c = clamp01(v); return c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055; };
const hexOf = (c: [number, number, number], k: number) => "#" + c.map((v) => Math.round(255 * toSrgb(1 - (1 - v) * k)).toString(16).padStart(2, "0")).join("");
const blob = (out: Stage, x: number, y: number, z: number, sc = 1, k = 1) => {
  const hl = Math.hypot(SUN.x, SUN.z) || 1, ox = -SUN.x / hl, oz = -SUN.z / hl, rot = Math.atan2(-ox, -oz);
  if (LNAME === "day") {
    const el = Math.asin(Math.min(0.99, Math.max(0.1, SUN.y)));
    const len = Math.min(2.4, Math.max(0.5, 1.6 / Math.tan(el))) * sc, h = len + 0.55 * sc, c = 0.3 * h; // feet at v = .2 of the card
    const tc = hexOf(TAIL, k);
    out.fx.push({ key: `blob|shadow|${tc}`, cw: 128, ch: 256, draw: (p) => fxShadow(p, tc), x: x + ox * c, y: y + 0.018, z: z + oz * c,
      w: 0.72 * sc, h, flat: true, rot });
  }
  const cc = hexOf(CONTACT[LNAME], k);
  out.fx.push({ key: `blob|contact|${cc}`, cw: 128, ch: 128, draw: (p) => fxContact(p, cc), x: x + ox * 0.03 * sc, y: y + 0.022, z: z + oz * 0.03 * sc,
    w: 0.52 * sc, h: 0.4 * sc, flat: true, rot });
};

// ================================================================ BEER cast
export type Stage = { places: Place[]; fx: FxPlace[] };
const WORKER = (v: number): Outfit => ({ jacket: ["#8a5a3a", "#6b7a4a", "#7a4f6a"][v % 3], pants: "#3b3f52", boots: "#4a3426", hat: "cap", cap: ["#5d6b4a", "#4a3a2a", "#3f5f8a"][v % 3], skin: SKINS[(v + 1) % 4] });
const CLERK: Outfit = { jacket: "#3f6fb5", pants: "#3b3f52", boots: "#4a3426", hat: "hair", hair: "#3a2a1e", skin: SKINS[2] };
const BOSS: Outfit = { jacket: "#3a2f45", pants: "#2f2f3a", boots: INK, hat: "tophat", moustache: "#4a3020", buttons: "#e8c45a", build: "stout", skin: SKINS[1] };
const JUDGE: Outfit = { jacket: "#22222c", pants: "#22222c", boots: INK, hat: "hair", hair: "#f4f1ea", build: "stout", skin: SKINS[0], buttons: "#f4f1ea" };
const TAXMAN: Outfit = { jacket: "#5a3b6a", pants: "#3b3f52", boots: INK, hat: "tophat", sash: "#c0353a", skin: SKINS[3] };
const EATER: Outfit = { jacket: "#c25a3a", pants: "#3b5b9a", boots: "#4a3426", hat: "hair", hair: "#2a201a", build: "stout", moustache: "#2a201a", waist: "#5a3b2a", skin: SKINS[1] };
const FOLK = [0, 1, 2, 3, 4, 5].map((v) => townsfolk(v));
const MUGMAN: Outfit = { jacket: "#2f5f6a", pants: "#3b3f52", boots: "#4a3426", hat: "cap", cap: "#8c3b4a", skin: SKINS[0] };

const front = (cam: CamInfo, o: Outfit, okey: string, i: number, x: number, y: number, z: number, fo: FrontOpts, scale = 1) =>
  person(cam, { i, o, okey }, x, y, z, { side: false, mirror: false }, fo, {}, scale);
/** someone at (x, z): floating in the beer when it is deeper than knee height there, else standing / running */
const inFlood = (x: number, z: number, tau: number) => floodH(x, z, tau);
const floater = (out: Stage, cam: CamInfo, t: number, o: Outfit, okey: string, i: number, x: number, z: number, h: number, prop: Prop = null, expr?: Expr) => {
  const bob = 0.06 * Math.sin(t * 2.3 + i * 1.7), tilt = (hh(i, 4) - 0.5) * 40 + 6 * Math.sin(t * 1.4 + i);
  const fo: FrontOpts = { mode: prop ? "stand" : "fall", expr: expr ?? (i % 3 ? "shock" : "dazed"), tilt: prop ? 4 * Math.sin(t * 1.3) : tilt, blink: lidAt(t, i), prop };
  out.places.push(front(cam, o, okey, i, x, h - 0.95 + bob, z, fo));
  out.fx.push({ key: `blob|contact|${FOAMRING}`, cw: 128, ch: 128, draw: (p) => fxContact(p, FOAMRING), x, y: h + 0.03, z, w: 1.2, h: 0.9, flat: true });
};
const FOAMRING = "#f1e2bd";

// ---- the street crowd (shots 1, 2, 9, 14): homes along the street, they flee down it when the wall goes ----
const HOMES: [number, number][] = [[-2.6, 9], [1.9, 11], [-0.8, 13.5], [3.1, 15], [-3.3, 17], [0.9, 19], [-1.9, 21.5], [2.6, 23.5], [-0.3, 25]];
const street = (out: Stage, cam: CamInfo, t: number, tau: number) => {
  HOMES.forEach(([x0, z0], k) => {
    const i = 300 + k, o = FOLK[k % 6], okey = `f${k % 6}`;
    const run = Math.max(0, tau - (T_W + 0.35 + 0.08 * k));
    // caught: where the front passed them (they ran at 3.4 m/s, the front comes at 7 m/s)
    const zRun = z0 + 3.4 * run;
    const h = inFlood(x0, zRun, tau);
    if (h > 0.55) {
      // drift with the beer a little after being caught
      const tc = (z0 - 0.6 + 3.4 * (T_W + 0.35 + 0.08 * k) - 3.4 * T_W) / (7 - 3.4) + T_W; // time the front reached them
      const zc = z0 + 3.4 * Math.max(0, tc - (T_W + 0.35 + 0.08 * k)), drift = 2.2 * Math.min(4, tau - tc);
      const zz = zc + drift;
      floater(out, cam, t, o, okey, i, x0 + 0.3 * Math.sin(tau + k), zz, Math.max(0.6, inFlood(x0, zz, tau)));
      return;
    }
    const shaking = tau > T_W - 1.0 && tau < T_W + 0.4;
    const expr: Expr = tau < T_W - 1.0 ? (["smile", "grin", "smile_closed", "neutral"] as Expr[])[k % 4] : "shock";
    const fo: FrontOpts = run > 0 ? { mode: "march", phase: (run * 2.4 + hh(k)) % 1, lift: 90, expr, blink: 0, look: 0 }
      : { mode: "stand", expr, blink: lidAt(t, i), look: shaking ? 0 : (k % 3) - 1 };
    out.places.push(front(cam, o, okey, i, x0, D0, zRun, fo));
    blob(out, x0, D0, zRun);
  });
  // the deadpan man with his mug: does not run
  const mx = 0.2, mz = 28, h = inFlood(mx, mz, tau);
  if (h > 0.55) floater(out, cam, t, MUGMAN, "mug", 350, mx, mz, h, "mug", "neutral");
  else {
    out.places.push(front(cam, MUGMAN, "mug", 350, mx, D0, mz, { mode: "stand", expr: "neutral", prop: "mug", blink: lidAt(t, 350) }));
    blob(out, mx, D0, mz);
  }
};

// ---- hall roles ----
/** worker 1: at the base of V1 (shots 3, 5, 7), swept in 7-8 */
const worker1 = (out: Stage, cam: CamInfo, t: number, tau: number, id: number) => {
  const [x, z] = id === 3 ? [-1.4, -8.6] : id === 5 ? [-4.1, -8.0] : [-1.2, -6.4];
  const h = inFlood(x, z, tau);
  if (h > 0.55) { floater(out, cam, t, WORKER(0), "w0", 400, x + 0.8 * Math.min(2, tau - T_B[0]), z + 1.5 * Math.min(2, tau - T_B[0]), h); return; }
  let expr: Expr = id === 3 ? "smile_closed" : "neutral";
  if (id === 5 && tau > T_CLANG - 0.07) expr = "shock";
  if (id === 7) expr = tau < T_B[0] - 0.07 ? "nervous" : "shock";
  const fo: FrontOpts = { mode: "stand", expr, blink: expr === "shock" ? 0 : lidAt(t, 400), look: id === 3 ? -1 : 0, headTilt: id === 3 ? -8 : 0 };
  out.places.push(front(cam, WORKER(0), "w0", 400, x, D0, z, fo));
  blob(out, x, D0, z);
};
/** worker 2 on the ladder at V1's rim (shot 3b) */
export const LADDER = (() => { const v = VATS[0], a = Math.atan2(0.894, 0.447); return { x: v.x + (v.r + 0.25) * Math.cos(a), z: v.z + (v.r + 0.25) * Math.sin(a), a }; })();
const worker2 = (out: Stage, cam: CamInfo, t: number) => {
  out.places.push(front(cam, WORKER(1), "w1", 401, LADDER.x + 0.15, 5.15, LADDER.z + 0.35, { mode: "stand", expr: "grin", blink: lidAt(t, 401), wave: 0.4 }));
};
const office = (out: Stage, cam: CamInfo, t: number, id: number) => {
  const L = 2 / FPS;
  const clerkExpr: Expr = t < 577 / FPS - L ? "nervous" : t < 611 / FPS - L ? "shock" : "nervous";
  out.places.push(front(cam, CLERK, "clerk", 410, 9.7, D0, -24.4, { mode: "stand", expr: clerkExpr, prop: t < 600 / FPS ? "point" : null, blink: lidAt(t, 410) }));
  blob(out, 9.7, D0, -24.4);
  const bossExpr: Expr = t < 611 / FPS - L ? "smile" : t < 638 / FPS - L ? "smile_closed" : "relief";
  out.places.push(front(cam, BOSS, "boss", 411, 11.2, D0, -25.0, { mode: "stand", expr: bossExpr, prop: "mug", blink: lidAt(t, 411), facing: -1 }));
  blob(out, 11.2, D0, -25.0, 1.1);
};

// ---- court ----
const HITS = [1119 / FPS, 1133 / FPS];
const hammerK = (t: number) => {
  let k = 1;
  for (const th of HITS) {
    const n = (t - th) * FPS;
    if (n >= -11 && n < -7) k = Math.min(k, 1 - smooth((n + 11) / 4));
    else if (n >= -7 && n < 0) k = 0;
  }
  return k;
};
const court = (out: Stage, cam: CamInfo, t: number) => {
  const L = 2 / FPS, up = t > 1227 / FPS - L;
  const expr: Expr = t < 1104 / FPS - L ? "stern" : t < 1162 / FPS - L ? "neutral" : up ? "smile_closed" : "stern";
  const fo: FrontOpts = up ? { mode: "stand", expr, wave: 1, blink: lidAt(t, 420) } : { mode: "stand", expr, prop: ["hammer", q(hammerK(t), 30)], blink: lidAt(t, 420), facing: 1 };
  out.places.push(front(cam, JUDGE, "judge", 420, COURT[0], 0.35, COURT[2] + 1.8, fo));
  for (const th of HITS) if (t >= th && t < th + 5 / FPS) {
    const u = (t - th) / (5 / FPS);
    out.fx.push({ key: `burst${q(u, 30)}`, cw: 500, ch: 500, draw: (p) => fxBurst(p, q(u, 30)), x: COURT[0] + 0.7, y: 1.12, z: COURT[2] + 0.95, w: 0.8, h: 0.8 });
  }
};

// ---- explanation: pressure arrows on the demo vat ----
const ARROW_T = [1307, 1317, 1326, 1340, 1350, 1364].map((f) => f / FPS);
const demo = (out: Stage, cam: CamInfo, t: number) => {
  const v = DEMO_VAT, ys = [4.3, 3.5, 2.7, 1.9, 1.1, 0.4];
  const pulse = t > 1438 / FPS ? 1 + 0.12 * Math.sin((t - 1438 / FPS) * 18) * Math.exp(-(t - 1438 / FPS) * 1.2) : 1;
  ys.forEach((y, k) => {
    const a = clamp01((t - ARROW_T[k]) / 0.18);
    if (a <= 0) return;
    const pop = a < 1 ? 1.25 * a : 1;
    const len = (0.3 + 0.27 * (v.h - y)) * pop * (k >= 4 ? pulse : 1), th = 0.3 + 0.07 * (v.h - y);
    for (const s of [-1, 1]) {
      const rx = cam.right.x * s, rz = cam.right.z * s;
      out.fx.push({ key: `arrow${s}`, cw: 400, ch: 160, draw: (p) => fxArrow(p, s), x: v.x + rx * (v.r + 0.12 + len / 2), y, z: v.z + rz * (v.r + 0.12 + len / 2) - 0.2, w: len, h: th * pop });
    }
  });
};

// ---- the buffet belt ----
const buffet = (out: Stage, cam: CamInfo, t: number) => {
  const L = 2 / FPS, t1 = 1542 / FPS, t2 = 1576 / FPS;
  const expr: Expr = t < t1 - L ? (t % 1.2 < 0.6 ? "grin" : "smile_closed") : t < t2 - L ? "shock" : "relief";
  const beltOff = t < t1 - L ? 0 : t < t2 - L ? 0.5 : 1;
  const [x, z] = [BUFFET[0] + 0.2, BUFFET[2] - 0.1];
  out.places.push(front(cam, EATER, "eater", 430, x, D0, z, { mode: "stand", expr, beltOff, blink: lidAt(t, 430) }));
  // plates on the table edge
  for (const [dx, kind] of [[-1.05, 0], [-1.6, 1], [-2.15, 2]] as const)
    out.fx.push({ key: `plate${kind}`, cw: 300, ch: 200, draw: (p) => fxPlate(p, kind), x: BUFFET[0] + dx, y: 1.02, z: BUFFET[2] - 0.38, w: 0.55, h: 0.37 });
  const waist: V3 = [x + 0.0, 0.88, z - 0.15];
  if (t >= t1 && t < t1 + 6 / FPS) { const u = (t - t1) / (6 / FPS); out.fx.push({ key: `burst${q(u, 30)}`, cw: 500, ch: 500, draw: (p) => fxBurst(p, q(u, 30)), x: waist[0], y: waist[1], z: waist[2] - 0.05, w: 0.9, h: 0.9 }); }
  if (t >= t1 && t < t1 + 1.2) {
    const s = t - t1;
    out.fx.push({ key: "buckle", cw: 160, ch: 160, draw: fxBuckle, x: waist[0] + 1.6 * s, y: waist[1] + 2.4 * s - 4.9 * s * s, z: waist[2] - 0.6 * s, w: 0.16, h: 0.16, rot: 9 * s });
  }
  if (t >= t2 && t < t2 + 1.2) {
    const s = t - t2;
    out.fx.push({ key: "belt", cw: 400, ch: 120, draw: fxBelt, x: waist[0] - 1.4 * s, y: waist[1] + 2.0 * s - 4.9 * s * s, z: waist[2] - 0.4 * s, w: 0.9, h: 0.27, rot: -4 * s });
    if (s < 0.2) { const u = s / 0.2; out.fx.push({ key: `burst${q(u, 30)}`, cw: 500, ch: 500, draw: (p) => fxBurst(p, q(u, 30)), x: waist[0], y: waist[1], z: waist[2] - 0.05, w: 1.1, h: 1.1 }); }
  }
};

// ---- aftermath + the tax refund ----
const aftermath = (out: Stage, cam: CamInfo, t: number) => {
  out.places.push(front(cam, WORKER(2), "w2", 440, TANK[0] + 3.6, D0, TANK[2] + 3.4, { mode: "stand", expr: "smile_closed", blink: lidAt(t, 440) }));
  blob(out, TANK[0] + 3.6, D0, TANK[2] + 3.4);
};
const T_PAY = 1777 / FPS;
const refund = (out: Stage, cam: CamInfo, t: number) => {
  const L = 2 / FPS, paid = t >= T_PAY - L;
  const bossExpr: Expr = t < 1712 / FPS - L ? "smile" : t < 1758 / FPS - L ? "smile_closed" : paid ? (t > 1790 / FPS ? "laugh" : "grin") : "smile";
  out.places.push(front(cam, BOSS, "boss", 411, 0.8, D0, 12, { mode: "stand", expr: bossExpr, prop: paid ? "bag" : "mug", blink: lidAt(t, 411), facing: -1 }));
  blob(out, 0.8, D0, 12, 1.1);
  if (t > 1700 / FPS) {
    // the tax man walks in from the left, hands over the bag on "pajak"
    const xin = -0.9 - 3.2 * (1 - smooth((t - 1736 / FPS) / 0.9));
    const walking = t < 1736 / FPS + 0.9;
    const fo: FrontOpts = walking ? { mode: "stroll", phase: (t * 1.6) % 1, expr: "neutral", prop: "bag", blink: 0 } : { mode: "stand", expr: paid ? "smile_closed" : "neutral", prop: paid ? null : "bag", blink: lidAt(t, 450), facing: 1 };
    out.places.push(front(cam, TAXMAN, "tax", 450, xin, D0, 12.3, fo));
    blob(out, xin, D0, 12.3);
  }
  if (t >= T_PAY && t < T_PAY + 0.9) {
    const u = (t - T_PAY) / 0.9;
    out.fx.push({ key: `coins${q(u, 30)}`, cw: 500, ch: 500, draw: (p) => fxCoins(p, q(u, 30)), x: 0.55, y: 1.5, z: 11.7, w: 1.4, h: 1.4 });
  }
  // brown stains of the flood on the street
  for (const [x, z, s] of [[-2.5, 8, 2.2], [2.8, 14, 1.8], [-1.2, 18, 2.6], [1.5, 5, 1.6], [-3.2, 13, 1.4]] as const)
    out.fx.push({ key: "blob|contact|#b08a5a", cw: 128, ch: 128, draw: (p) => fxContact(p, "#b08a5a"), x, y: 0.015, z, w: s * 1.6, h: s, flat: true });
};

// ---- bursts: beer splashes ----
const splashes = (out: Stage, tau: number) => {
  VATS.forEach((v, i) => {
    const dt = tau - T_B[i];
    if (dt < 0 || dt > 1.3) return;
    const u = dt / 1.3;
    for (let k = 0; k < 5; k++) {
      const a = k * 1.256 + i, r = v.r * (0.6 + 0.5 * u);
      out.fx.push({ key: `bsplash${q(u, 30)}`, cw: 800, ch: 800, draw: (p) => fxBeerSplash(p, q(u, 30)), x: v.x + Math.cos(a) * r, y: 2.2 + 1.5 * u, z: v.z + Math.sin(a) * r, w: 6.5, h: 6.5 });
    }
    if (dt < 0.3) { const b = dt / 0.3; out.fx.push({ key: `burst${q(b, 30)}`, cw: 500, ch: 500, draw: (p) => fxBurst(p, q(b, 30), "#fff3b0", 12), x: v.x, y: v.h * 0.55, z: v.z + v.r + 0.3, w: 5, h: 5 }); }
  });
  const dw = tau - T_W;
  if (dw >= 0 && dw < 1.6) {
    const u = dw / 1.6;
    for (const [x, s] of [[-3.5, 1], [0, 1.3], [3.4, 1.1]] as const)
      out.fx.push({ key: `bsplash${q(u, 30)}`, cw: 800, ch: 800, draw: (p) => fxBeerSplash(p, q(u, 30)), x, y: 3.2 * s, z: 2.5 + 6 * u, w: 8 * s, h: 8 * s });
  }
};
/** the slipping hoop's clang + creaks before the bursts */
const clang = (out: Stage, t: number, tau: number, cam: CamInfo) => {
  const v = VATS[0];
  if (tau >= T_CLANG && tau < T_CLANG + 6 / FPS) {
    const u = (tau - T_CLANG) / (6 / FPS);
    out.fx.push({ key: `burst${q(u, 30)}`, cw: 500, ch: 500, draw: (p) => fxBurst(p, q(u, 30)), x: v.x + 1.2, y: 0.25, z: v.z + v.r + 0.2, w: 1.3, h: 1.3 });
  }
  const creak = (pts: V3[], size: number) => pts.forEach(([x, y, z], i) => {
    const u = q((t * 1.3 + i * 0.37) % 1, 30);
    out.fx.push({ key: `creak${u}`, cw: 300, ch: 300, draw: (p) => fxCreak(p, u), x, y, z, w: size, h: size, rot: i * 0.6 - 0.6 });
  });
  if (tau > 680 / FPS && tau < T_B[0]) creak([[v.x + 2.2, 4.4, v.z + v.r], [v.x - 1.6, 2.2, v.z + v.r + 0.3], [v.x + 0.6, 1.0, v.z + v.r + 0.2]], 1.0);
  if (tau > T_W - 1.3 && tau < T_W) creak([[-3.2, 6.5, 0.9], [2.8, 3.5, 0.9], [-1, 1.8, 0.9]], 1.3);
};

/** everything with a face (and the 2D effects) in shot `id` at time t / story time tau */
export const stage = (id: number, t: number, tau: number, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  const s = SHOTS[id - 1];
  LNAME = s.light;
  findSun(cam, SUN);
  if (s.set === "street" && id !== 14) street(out, cam, t, tau);
  if (id === 3 || id === 5 || id === 7 || id === 8) worker1(out, cam, t, tau, id === 8 ? 7 : id);
  if (id === 3 && t > 283 / FPS) worker2(out, cam, t);
  if (id === 8) { const h = inFlood(-3.6, -9.2, tau); if (h > 0.55) floater(out, cam, t, WORKER(1), "w1", 401, -3.6 + 0.6 * Math.sin(t), -9.2, h); }
  if (id === 6) office(out, cam, t, id);
  if (id === 10) court(out, cam, t);
  if (id === 11) demo(out, cam, t);
  if (id === 12) buffet(out, cam, t);
  if (id === 13) aftermath(out, cam, t);
  if (id === 14) refund(out, cam, t);
  if (s.set === "hall" || s.set === "street") { splashes(out, tau); clang(out, t, tau, cam); }
  return out;
};

// ================================================================ effect drawings (design units = canvas px / k)
const BEER = "#4a2a14", BEER2 = "#6b3d1c", FOAM = "#f3e6c4", FOAM2 = "#e2cfa2";
/** beer splash: brown sheet with cream foam lumps, rising then breaking up (t 0..1); base of the drawing = surface */
export const fxBeerSplash = (p: Pen, t: number) => {
  const g = p.g, cx = 400, base = 700, s = 0.4 + 0.6 * Math.sqrt(t), fade = t > 0.75 ? (1 - t) / 0.25 : 1;
  g.globalAlpha = Math.max(0, fade);
  const rnd = (k: number) => { const v = Math.sin(k * 91.7) * 43758.5; return v - Math.floor(v); };
  for (let k = 0; k < 9; k++) {
    const a = -Math.PI / 2 + (k - 4) * 0.28, L = (220 + 160 * rnd(k)) * s, w = 34 + 20 * rnd(k + 9);
    const x1 = cx + Math.cos(a) * L, y1 = base + Math.sin(a) * L + 260 * t * t;
    p.line([[cx + (k - 4) * 12, base], [x1, y1]], k % 2 ? BEER : BEER2, w * (1 - 0.4 * t));
    p.ell(x1, y1, w * 0.9, w * 0.8, FOAM, 6);
  }
  p.ell(cx, base - 20, 230 * s, 70 * s, BEER2, 8);
  for (let k = 0; k < 7; k++) p.ell(cx - 180 * s + k * 60 * s, base - 70 * s - 20 * rnd(k + 3), 46 * s, 34 * s, k % 2 ? FOAM : FOAM2, 6);
  g.globalAlpha = 1;
};
export const fxArrow = (p: Pen, dir: number) => {
  const pts: [number, number][] = [[20, 55], [260, 55], [260, 15], [385, 80], [260, 145], [260, 105], [20, 105]];
  p.poly(dir > 0 ? pts : pts.map(([x, y]) => [400 - x, y] as [number, number]), "#e8462e", 10);
};
export const fxPlate = (p: Pen, kind: number) => {
  p.ell(150, 150, 135, 34, "#f4f1ea", 7);
  if (kind === 0) { p.ell(150, 118, 80, 46, "#f7f3e8", 7); p.ell(130, 100, 26, 22, "#3f8f3c", 5); }        // rice
  else if (kind === 1) { p.ell(150, 110, 70, 42, "#c8743a", 7); p.line([[205, 90], [250, 55]], "#f4f1ea", 16); } // chicken
  else { p.ell(120, 116, 44, 30, "#e2453c", 6); p.ell(180, 114, 44, 32, "#f0a83a", 6); }                      // sambal + egg
};
export const fxBuckle = (p: Pen) => { p.poly([[30, 30], [130, 30], [130, 130], [30, 130]], "#e8c45a", 10); p.poly([[60, 60], [100, 60], [100, 100], [60, 100]], "#5a3b2a", 6); };
export const fxBelt = (p: Pen) => p.line([[20, 60], [130, 40], [260, 80], [380, 55]], "#5a3b2a", 34);
export const fxCoins = (p: Pen, t: number) => {
  for (let k = 0; k < 10; k++) {
    const a = -Math.PI / 2 + (k - 4.5) * 0.3, r = 60 + 200 * t;
    const x = 250 + Math.cos(a) * r, y = 260 + Math.sin(a) * r + 300 * t * t;
    p.ell(x, y, 24, 22, "#f2c84b", 6);
    p.ell(x - 6, y - 6, 7, 6, "#fff3b0", 0);
  }
};
