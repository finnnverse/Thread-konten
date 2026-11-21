// Warga Kampung: the reusable 3D cast for kampung-3d-short.
// Design language "soft-blocky": pillow-shaped rounded-box heads, soft box torsos, capsule limbs with round mitten
// hands, chunky feet, a painted face (decal) that swaps expression, and a thin warm-brown inverted-hull outline.
// Everything is built from code (no downloaded models), so every video draws the exact same characters.
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import { DecalGeometry } from "three/examples/jsm/geometries/DecalGeometry.js";

export type Expr = "netral" | "senyum" | "tawa" | "sedih" | "nangis" | "kaget" | "marah" | "bingung" | "merem" | "sipit" | "kedip" | "meringis";
export const EXPRS: Expr[] = ["netral", "senyum", "tawa", "sedih", "nangis", "kaget", "marah", "bingung", "merem"];

export type PatternKind = "polos" | "batik" | "kotak" | "bunga" | "garis";
export type Pattern = { kind: PatternKind; base: string; accent: string; repeat?: number };
export type Hair = "pendek" | "jabrik" | "kuncir" | "konde" | "botak" | "belah";
export type Age = "anak" | "remaja" | "dewasa" | "lansia";

export interface Spec {
  id: string;
  name: string;
  desc: string;
  age: Age;
  skin: string;
  hair: Hair;
  hairColor: string;
  top: Pattern; // shirt / kebaya / jacket
  sleeves: "pendek" | "panjang";
  bottom: Pattern; // trousers / shorts / skirt / sarung
  bottomKind: "celana" | "celana-pendek" | "rok" | "sarung";
  shoes: string;
  belly?: number;
  hat?: "peci";
  hijab?: string;
  brow?: string;
  mustache?: string;
  beard?: string;
  wrinkles?: boolean;
  lashes?: boolean;
  freckles?: boolean;
  glasses?: boolean;
  cane?: boolean;
  backpack?: string;
  zipper?: string;
  stoop?: number;
}

export interface Pose {
  armL?: number; armR?: number; // raise sideways (rad)
  armLf?: number; armRf?: number; // raise forward (rad)
  headYaw?: number; headTilt?: number; headNod?: number;
  lean?: number;
  walk?: number; walkAmp?: number; // walk phase (rad) and swing amount
  bounce?: number;
  look?: [number, number]; // eye direction, -1..1
}

const OUTLINE = "#3b2417";
const PX = 512;

// ---------- materials ----------
export const clay = (color: string | THREE.Color, map?: THREE.Texture, rough = 0.72) =>
  new THREE.MeshStandardMaterial({ color: map ? "#ffffff" : color, map: map ?? null, roughness: rough, metalness: 0 });

const outlineMats = new Map<number, THREE.MeshBasicMaterial>();
export const outlineMat = (thick: number) => {
  let m = outlineMats.get(thick);
  if (m) return m;
  m = new THREE.MeshBasicMaterial({ color: OUTLINE, side: THREE.BackSide });
  m.onBeforeCompile = (s) => {
    s.vertexShader = s.vertexShader.replace("#include <begin_vertex>", `#include <begin_vertex>\n transformed += normalize(normal) * ${thick.toFixed(4)};`);
  };
  m.customProgramCacheKey = () => "kpOutline" + thick;
  outlineMats.set(thick, m);
  return m;
};

const texCache = new Map<string, THREE.CanvasTexture>();
export const patternTex = (p: Pattern) => {
  const key = JSON.stringify(p);
  const hit = texCache.get(key);
  if (hit) return hit;
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const g = c.getContext("2d")!;
  g.fillStyle = p.base;
  g.fillRect(0, 0, 256, 256);
  g.fillStyle = p.accent;
  g.strokeStyle = p.accent;
  if (p.kind === "batik") {
    // kawung-like motif: four petals around a dot, on a diagonal grid
    for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) {
      const cx = x * 64 + (y % 2) * 32 + 16, cy = y * 64 + 32;
      for (let k = 0; k < 4; k++) {
        g.save(); g.translate(cx, cy); g.rotate((k * Math.PI) / 2 + Math.PI / 4);
        g.beginPath(); g.ellipse(0, -13, 7, 12, 0, 0, Math.PI * 2); g.fill(); g.restore();
      }
      g.beginPath(); g.arc(cx, cy, 3, 0, Math.PI * 2); g.fillStyle = p.base; g.fill(); g.fillStyle = p.accent;
    }
  } else if (p.kind === "kotak") {
    g.globalAlpha = 0.55;
    for (let i = 0; i < 256; i += 64) { g.fillRect(i, 0, 26, 256); g.fillRect(0, i, 256, 26); }
    g.globalAlpha = 1; g.lineWidth = 3;
    for (let i = 13; i < 256; i += 64) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 256); g.moveTo(0, i); g.lineTo(256, i); g.stroke(); }
  } else if (p.kind === "bunga") {
    for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) {
      const cx = x * 64 + (y % 2) * 32 + 20, cy = y * 64 + 30;
      for (let k = 0; k < 5; k++) { const a = (k / 5) * Math.PI * 2; g.beginPath(); g.arc(cx + Math.cos(a) * 9, cy + Math.sin(a) * 9, 7, 0, Math.PI * 2); g.fill(); }
      g.beginPath(); g.arc(cx, cy, 5, 0, Math.PI * 2); g.fillStyle = "#f6c94a"; g.fill(); g.fillStyle = p.accent;
    }
  } else if (p.kind === "garis") {
    for (let i = 0; i < 256; i += 40) g.fillRect(0, i, 256, 16);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(p.repeat ?? 1, p.repeat ?? 1);
  t.anisotropy = 4;
  texCache.set(key, t);
  return t;
};
const patMat = (p: Pattern) => (p.kind === "polos" ? clay(p.base) : clay(p.base, patternTex(p)));

// ---------- mesh helpers ----------
export const rbox = (w: number, h: number, d: number, r = 0.3) => new RoundedBoxGeometry(w, h, d, 5, Math.min(w, h, d) * r);
export const capsule = (r: number, len: number) => new THREE.CapsuleGeometry(r, len, 6, 14);

export function part(parent: THREE.Object3D, geo: THREE.BufferGeometry, mat: THREE.Material, pos: [number, number, number] = [0, 0, 0], outline = 0.012) {
  const m = new THREE.Mesh(geo, mat);
  m.position.set(...pos);
  m.castShadow = true;
  m.receiveShadow = true;
  parent.add(m);
  if (outline > 0) {
    const o = new THREE.Mesh(geo, outlineMat(outline));
    m.add(o);
  }
  return m;
}

// ---------- face painting ----------
export const shade = (hex: string, k: number) => { const c = new THREE.Color(hex); c.multiplyScalar(k); return "#" + c.getHexString(); };

function drawFace(g: CanvasRenderingContext2D, s: Spec, e: Expr, look: [number, number], blink: boolean, talk = 0) {
  g.clearRect(0, 0, PX, PX);
  const ink = "#24150e", lip = "#5b1f16", brow = s.brow ?? s.hairColor;
  const skin = s.skin;
  const EY = 246, EX = 96;
  g.lineCap = "round"; g.lineJoin = "round";

  // blush
  g.fillStyle = "rgba(235,96,96,0.32)";
  for (const sx of [-1, 1]) { g.beginPath(); g.ellipse(256 + sx * 150, 318, 44, 26, 0, 0, Math.PI * 2); g.fill(); }
  if (s.freckles) { g.fillStyle = shade(skin, 0.7); for (const sx of [-1, 1]) for (const [dx, dy] of [[-14, -6], [6, 4], [20, -10], [-2, 12]]) { g.beginPath(); g.arc(256 + sx * (150 + dx), 300 + dy, 4, 0, Math.PI * 2); g.fill(); } }
  if (s.wrinkles) {
    g.strokeStyle = shade(skin, 0.72); g.lineWidth = 5;
    for (const sx of [-1, 1]) { for (const dy of [-10, 6]) { g.beginPath(); g.moveTo(256 + sx * 140, EY + dy); g.lineTo(256 + sx * 162, EY + dy - 8); g.stroke(); } }
    g.beginPath(); g.moveTo(200, 110); g.quadraticCurveTo(256, 100, 312, 110); g.stroke();
  }

  // eyes
  const closedHappy = e === "tawa" || e === "merem" || blink;
  const [lx, ly] = look;
  for (const sx of [-1, 1]) {
    const x = 256 + sx * EX;
    if (e === "sipit") {
      g.strokeStyle = ink; g.lineWidth = 14; g.beginPath(); g.moveTo(x - 32, EY + 4); g.quadraticCurveTo(x, EY - 6, x + 32, EY + 4); g.stroke();
      g.lineWidth = 6; g.beginPath(); g.moveTo(x + sx * 34, EY - 2); g.lineTo(x + sx * 46, EY - 12); g.moveTo(x + sx * 34, EY + 8); g.lineTo(x + sx * 48, EY + 10); g.stroke();
      continue;
    }
    if ((e === "kedip" && sx < 0) || (e === "meringis" && !blink)) {
      g.strokeStyle = ink; g.lineWidth = 15; g.beginPath();
      if (e === "kedip") g.arc(x, EY + 18, 30, Math.PI * 1.12, Math.PI * 1.88);
      else { g.moveTo(x - sx * 30, EY - 12); g.lineTo(x + sx * 10, EY + 4); g.lineTo(x - sx * 30, EY + 20); }
      g.stroke();
      continue;
    }
    if (closedHappy) {
      g.strokeStyle = ink; g.lineWidth = 15; g.beginPath();
      if (blink && e !== "tawa" && e !== "merem") { g.moveTo(x - 30, EY + 6); g.quadraticCurveTo(x, EY + 18, x + 30, EY + 6); }
      else g.arc(x, EY + 18, 30, Math.PI * 1.12, Math.PI * 1.88);
      g.stroke();
      continue;
    }
    const big = e === "kaget" ? 1.4 : 1.2;
    const rx = 30 * big, ry = 42 * big;
    // sclera ring gives the eyes a "glassy bead" read on dark skin
    g.fillStyle = "#fffaf0"; g.beginPath(); g.ellipse(x, EY, rx + 9, ry + 9, 0, 0, Math.PI * 2); g.fill();
    g.fillStyle = ink; g.beginPath(); g.ellipse(x + lx * 8, EY + ly * 8, rx, ry, 0, 0, Math.PI * 2); g.fill();
    g.fillStyle = "#ffffff";
    g.beginPath(); g.arc(x + lx * 8 + 10, EY + ly * 8 - 15, 11 * big, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.arc(x + lx * 8 - 9, EY + ly * 8 + 16, 5, 0, Math.PI * 2); g.fill();
    // lids (skin-coloured shapes laid over the eye)
    g.fillStyle = skin;
    if (e === "sedih" || e === "nangis") { g.beginPath(); g.moveTo(x - 50, EY - 60); g.lineTo(x + 50, EY - 60); g.lineTo(x + sx * 46, EY - 34 + 26); g.lineTo(x - sx * 46, EY - 34 - 6); g.closePath(); g.fill(); }
    if (e === "marah") { g.beginPath(); g.moveTo(x - 50, EY - 60); g.lineTo(x + 50, EY - 60); g.lineTo(x - sx * 46, EY - 34 + 30); g.lineTo(x + sx * 46, EY - 34 - 4); g.closePath(); g.fill(); }
    if (e === "netral" && s.age === "lansia") { g.fillRect(x - 50, EY - 62, 100, 40); }
    if (s.lashes) { g.strokeStyle = ink; g.lineWidth = 7; for (const k of [0, 1]) { g.beginPath(); g.moveTo(x + sx * (22 + k * 10), EY - 32 + k * 12); g.lineTo(x + sx * (38 + k * 12), EY - 44 + k * 10); g.stroke(); } }
  }

  // brows: [innerY, outerY] per expression, + arch
  const B: Record<Expr, [number, number, number]> = {
    netral: [158, 158, 6], senyum: [150, 154, 10], tawa: [140, 146, 12], sedih: [132, 168, -4], nangis: [128, 166, -6],
    kaget: [118, 122, 14], marah: [186, 146, -2], bingung: [150, 150, 6], merem: [154, 156, 8], sipit: [176, 160, -2], kedip: [146, 152, 10], meringis: [176, 150, 0],
  };
  g.strokeStyle = brow; g.lineWidth = s.age === "lansia" ? 20 : 17;
  for (const sx of [-1, 1]) {
    let [iy, oy, arch] = B[e];
    if (e === "bingung") { if (sx < 0) { iy -= 26; oy -= 22; } else { iy += 10; oy += 4; } }
    const ix = 256 + sx * 46, ox = 256 + sx * 136;
    g.beginPath(); g.moveTo(ix, iy); g.quadraticCurveTo((ix + ox) / 2, (iy + oy) / 2 - arch, ox, oy); g.stroke();
  }

  // mustache (drawn before the mouth so an open mouth can overlap it)
  if (s.mustache) {
    g.fillStyle = s.mustache;
    for (const sx of [-1, 1]) { g.beginPath(); g.moveTo(256, 296); g.quadraticCurveTo(256 + sx * 60, 268, 256 + sx * 96, 314); g.quadraticCurveTo(256 + sx * 56, 318, 256, 316); g.fill(); }
  }

  // mouth
  const MY = 352;
  g.strokeStyle = lip; g.fillStyle = lip; g.lineWidth = 12;
  if (talk > 0 && e !== "tawa" && e !== "nangis" && e !== "kaget") {
    // speaking: open mouth, its corners follow the expression
    const up = e === "senyum" || e === "merem" ? -10 : e === "sedih" || e === "marah" ? 10 : 0;
    const w = 34, h = 14 + talk * 22;
    g.beginPath(); g.moveTo(256 - w, MY + up); g.quadraticCurveTo(256, MY - 10, 256 + w, MY + up); g.quadraticCurveTo(256, MY + h * 1.6, 256 - w, MY + up); g.fill();
    g.save(); g.clip(); g.fillStyle = "#e0707a"; g.beginPath(); g.ellipse(256, MY + h * 1.3, 24, 12, 0, 0, Math.PI * 2); g.fill(); g.restore();
  } else if (e === "meringis") { g.fillStyle = "#fffaf0"; g.beginPath(); g.roundRect(206, MY - 10, 100, 30, 12); g.fill(); g.lineWidth = 7; g.beginPath(); g.roundRect(206, MY - 10, 100, 30, 12); g.stroke(); g.beginPath(); g.moveTo(206, MY + 5); g.lineTo(306, MY + 5); g.stroke(); }
  else if (e === "netral" || e === "merem" || e === "sipit") { g.beginPath(); g.moveTo(226, MY); g.quadraticCurveTo(256, MY + (e === "merem" ? 14 : 6), 286, MY); g.stroke(); }
  else if (e === "senyum" || e === "kedip") { g.beginPath(); g.arc(256, MY - 34, 52, Math.PI * 0.2, Math.PI * 0.8); g.stroke(); }
  else if (e === "tawa" || e === "nangis") {
    g.beginPath();
    if (e === "tawa") { g.moveTo(190, MY - 12); g.quadraticCurveTo(256, MY + 100, 322, MY - 12); g.closePath(); }
    else { g.moveTo(212, MY + 28); g.quadraticCurveTo(256, MY - 30, 300, MY + 28); g.quadraticCurveTo(256, MY + 44, 212, MY + 28); }
    g.fill();
    g.save(); g.clip();
    g.fillStyle = "#e0707a"; g.beginPath(); g.ellipse(256, MY + 52, 40, 22, 0, 0, Math.PI * 2); g.fill();
    if (e === "tawa") { g.fillStyle = "#fffaf0"; g.fillRect(180, MY - 14, 152, 16); }
    g.restore();
  } else if (e === "sedih") { g.beginPath(); g.arc(256, MY + 40, 40, Math.PI * 1.22, Math.PI * 1.78); g.stroke(); }
  else if (e === "kaget") { g.beginPath(); g.ellipse(256, MY + 8, 22, 30, 0, 0, Math.PI * 2); g.fill(); }
  else if (e === "marah") {
    g.fillStyle = "#fffaf0"; g.beginPath(); g.roundRect(214, MY - 6, 84, 26, 8); g.fill();
    g.lineWidth = 7; g.beginPath(); g.roundRect(214, MY - 6, 84, 26, 8); g.stroke();
    g.beginPath(); for (const x of [242, 270]) { g.moveTo(x, MY - 6); g.lineTo(x, MY + 20); } g.moveTo(214, MY + 7); g.lineTo(298, MY + 7); g.stroke();
  } else if (e === "bingung") { g.beginPath(); g.moveTo(222, MY + 6); g.bezierCurveTo(240, MY - 10, 258, MY + 22, 276, MY + 2); g.lineTo(292, MY - 4); g.stroke(); }

  if (s.beard) { g.fillStyle = s.beard; g.beginPath(); g.moveTo(222, 400); g.quadraticCurveTo(256, 500, 290, 400); g.quadraticCurveTo(256, 418, 222, 400); g.fill(); }

  if (e === "nangis") {
    g.fillStyle = "rgba(120,190,255,0.92)";
    for (const sx of [-1, 1]) { const x = 256 + sx * EX; g.beginPath(); g.moveTo(x - 12, EY + 30); g.quadraticCurveTo(x - 18, 380, x - 8, 470); g.lineTo(x + 10, 470); g.quadraticCurveTo(x + 16, 380, x + 12, EY + 30); g.fill(); }
  }
  if (e === "bingung") {
    g.fillStyle = "rgba(140,205,255,0.95)"; g.beginPath(); g.moveTo(418, 90); g.quadraticCurveTo(450, 140, 436, 160); g.arc(418, 150, 20, 0.3, Math.PI - 0.3, false); g.quadraticCurveTo(396, 130, 418, 90); g.fill();
  }
}

// ---------- the character ----------
type Limb = { pivot: THREE.Group };

export class Warga {
  readonly group = new THREE.Group();
  readonly spec: Spec;
  private body = new THREE.Group();
  private headPivot = new THREE.Group();
  private armL!: Limb; private armR!: Limb;
  readonly hands: { L: THREE.Group; R: THREE.Group } = { L: new THREE.Group(), R: new THREE.Group() }; private legL!: Limb; private legR!: Limb;
  private faceMat!: THREE.MeshStandardMaterial;
  private faceTex = new Map<string, THREE.CanvasTexture>();
  private hipY = 0;
  private stoop = 0;
  readonly height: number;

  constructor(spec: Spec) {
    this.spec = spec;
    const s = spec;
    const kid = s.age === "anak", teen = s.age === "remaja", old = s.age === "lansia";
    const skin = clay(s.skin);
    const topM = patMat(s.top);
    const botM = patMat(s.bottom);
    const shoeM = clay(s.shoes, undefined, 0.6);

    const legLen = kid ? 0.26 : teen ? 0.4 : old ? 0.36 : 0.42;
    const footH = 0.1;
    const tw = kid ? 0.52 : teen ? 0.56 : 0.64, th = kid ? 0.44 : teen ? 0.56 : 0.6, td = kid ? 0.36 : 0.42;
    const hw = kid ? 0.86 : 0.9, hh = kid ? 0.78 : 0.8, hd = kid ? 0.74 : 0.76;
    this.hipY = legLen + footH;
    this.stoop = s.stoop ?? 0;
    this.group.add(this.body);

    // legs
    const legR = kid ? 0.07 : 0.078;
    const mkLeg = (sx: number): Limb => {
      const pivot = new THREE.Group();
      pivot.position.set(sx * tw * 0.23, this.hipY, 0);
      this.body.add(pivot);
      const short = s.bottomKind === "celana-pendek";
      const hidden = s.bottomKind === "rok" || s.bottomKind === "sarung";
      if (short) {
        part(pivot, capsule(legR * 1.45, legLen * 0.25), botM, [0, -legLen * 0.2, 0]);
        part(pivot, capsule(legR, legLen * 0.62), skin, [0, -legLen * 0.62, 0]);
      } else if (!hidden) part(pivot, capsule(legR * 1.08, legLen - 0.02), botM, [0, -legLen / 2, 0]);
      else part(pivot, capsule(legR * 0.9, legLen * 0.5), skin, [0, -legLen * 0.72, 0], 0);
      part(pivot, rbox(0.19, footH, 0.28, 0.4), shoeM, [0, -legLen - footH / 2 + 0.01, 0.05]);
      return { pivot };
    };
    this.legL = mkLeg(1); this.legR = mkLeg(-1);

    // skirt / sarung
    if (s.bottomKind === "rok" || s.bottomKind === "sarung") {
      const len = this.hipY - footH * 0.4;
      const g = new THREE.CylinderGeometry(tw * 0.5, tw * 0.6, len, 28, 1, true);
      const sk = part(this.body, g, botM.clone(), [0, this.hipY - len / 2 + 0.06, 0]);
      sk.scale.z = td / tw * 1.25;
      (sk.material as THREE.MeshStandardMaterial).side = THREE.DoubleSide;
      if (s.bottomKind === "sarung") part(this.body, rbox(tw * 1.02, 0.08, td * 1.1, 0.45), botM, [0, this.hipY + 0.05, 0]);
    }

    // torso
    const torsoY = this.hipY + th / 2;
    part(this.body, rbox(tw, th, td, 0.32), topM, [0, torsoY, 0]);
    if (s.belly) { const b = part(this.body, new THREE.SphereGeometry(0.28, 24, 16), topM, [0, torsoY - 0.07, td * 0.18]); b.scale.set(tw * 1.55, 1.05, s.belly); }
    if (s.zipper) part(this.body, rbox(0.05, th * 0.96, 0.02, 0.4), clay(s.zipper), [0, torsoY, td / 2 + (s.belly ? 0.06 : 0.005)], 0);
    if (s.top.kind === "polos" && s.age === "anak") {
      // school uniform: red-white badge on the pocket
      part(this.body, rbox(0.1, 0.06, 0.02, 0.3), clay("#c8302c"), [-tw * 0.22, torsoY + th * 0.22, td / 2 + 0.005], 0);
    }
    if (s.backpack) { part(this.body, rbox(tw * 0.85, th * 0.95, 0.2, 0.3), clay(s.backpack), [0, torsoY + 0.02, -td / 2 - 0.09]); }

    // arms
    const armLen = kid ? 0.34 : 0.46;
    const armR0 = kid ? 0.062 : 0.07;
    const mkArm = (sx: number): Limb => {
      const pivot = new THREE.Group();
      pivot.position.set(sx * (tw / 2 + armR0 * 0.6), this.hipY + th - 0.09, 0);
      this.body.add(pivot);
      if (s.sleeves === "panjang") part(pivot, capsule(armR0 * 1.12, armLen - 0.04), topM, [0, -armLen / 2, 0]);
      else {
        part(pivot, capsule(armR0 * 1.35, armLen * 0.2), topM, [0, -armLen * 0.14, 0]);
        part(pivot, capsule(armR0, armLen * 0.62), skin, [0, -armLen * 0.58, 0]);
      }
      part(pivot, new THREE.SphereGeometry(armR0 * 1.38, 18, 14), skin, [0, -armLen - 0.02, 0]);
      const anchor = sx > 0 ? this.hands.L : this.hands.R;
      anchor.position.set(0, -armLen - 0.02, 0); pivot.add(anchor);
      return { pivot };
    };
    this.armL = mkArm(1); this.armR = mkArm(-1);
    if (s.cane) {
      const cane = new THREE.Group();
      cane.position.set(0, -armLen - 0.02, 0.02);
      this.armR.pivot.add(cane);
      const wood = clay("#7a4a26");
      part(cane, new THREE.CylinderGeometry(0.022, 0.022, this.hipY + th - 0.09 - armLen + 0.02, 10), wood, [0, -(this.hipY + th - 0.09 - armLen) / 2, 0.06], 0.008);
      const hook = part(cane, new THREE.TorusGeometry(0.06, 0.022, 8, 16, Math.PI), wood, [0, 0.04, 0.0], 0.008);
      hook.rotation.y = Math.PI / 2;
    }

    // head
    this.headPivot.position.set(0, this.hipY + th - 0.02, 0);
    this.body.add(this.headPivot);
    const head = new THREE.Group();
    head.position.y = hh / 2 + 0.03;
    this.headPivot.add(head);
    const headMesh = part(head, rbox(hw, hh, hd, 0.36), skin, [0, 0, 0], 0.014);
    for (const sx of [-1, 1]) { const ear = part(head, new THREE.SphereGeometry(0.085, 14, 10), skin, [sx * hw / 2, -0.02, -0.02], 0.01); ear.scale.set(0.5, 1, 0.8); }
    const nose = part(head, new THREE.SphereGeometry(0.06, 16, 12), clay(shade(s.skin, 0.93)), [0, -0.06, hd / 2 - 0.005], 0);
    nose.scale.set(1, 0.85, 0.7);

    // painted face (decal projected on the front of the head)
    headMesh.updateMatrixWorld(true);
    const decalGeo = new DecalGeometry(headMesh, new THREE.Vector3(0, 0, hd / 2), new THREE.Euler(0, 0, 0), new THREE.Vector3(hw * 0.98, hh * 0.98, hd * 0.6));
    // DecalGeometry bakes the mesh's world matrix: the head is still unparented here, so its coordinates are head-local
    this.faceMat = new THREE.MeshStandardMaterial({ transparent: true, roughness: 0.55, polygonOffset: true, polygonOffsetFactor: -4, depthWrite: false });
    const face = new THREE.Mesh(decalGeo, this.faceMat);
    face.position.copy(headMesh.position).sub(headMesh.position);
    head.add(face);
    face.renderOrder = 2;

    // hair / hats / hijab
    const hairM = clay(s.hairColor, undefined, 0.85);
    const top = hh / 2;
    if (s.hijab) {
      const hm = clay(s.hijab, undefined, 0.8);
      part(head, rbox(hw + 0.12, hh + 0.12, hd + 0.02, 0.4), hm, [0, 0.04, -0.1], 0.014);
      const drape = part(head, new THREE.CylinderGeometry(hw * 0.48, tw * 0.66, 0.36, 28), hm, [0, -hh / 2 - 0.08, -0.06]);
      drape.scale.z = 0.8;
    } else {
      if (s.hair === "pendek" || s.hair === "jabrik" || s.hair === "kuncir" || s.hair === "belah" || s.hair === "konde") {
        // hair cap: a slightly larger pillow hugging the top of the head (stops above the brows), plus the back of the head
        const capH = s.hat ? 0.0 : 0.3;
        if (capH) part(head, rbox(hw + 0.05, capH, hd + 0.05, 0.42), hairM, [0, top - capH / 2 + 0.035, -0.012], 0.012);
        part(head, rbox(hw + 0.05, hh * 0.7, hd * 0.55, 0.42), hairM, [0, top - hh * 0.35 + 0.02, -hd * 0.24], 0.012);
      }
      if (s.hair === "belah") { const sw = part(head, rbox(hw * 0.62, 0.12, 0.2, 0.45), hairM, [hw * 0.14, top - 0.02, hd / 2 - 0.08], 0.01); sw.rotation.z = -0.12; }
      if (s.hair === "jabrik") {
        const cone = new THREE.ConeGeometry(0.1, 0.2, 10);
        for (let i = 0; i < 7; i++) { const a = (i / 6 - 0.5) * 1.5; const c = part(head, cone, hairM, [Math.sin(a) * hw * 0.42, top + 0.08, Math.cos(a) * 0.05 - 0.04], 0.01); c.rotation.z = -a * 0.6; c.rotation.x = -0.25; }
      }
      if (s.hair === "kuncir") {
        part(head, new THREE.SphereGeometry(0.06, 10, 8), clay("#e4475b"), [0, top - 0.06, -hd / 2 - 0.08], 0.008);
        const tail = part(head, capsule(0.1, 0.32), hairM, [0, top - 0.3, -hd / 2 - 0.14], 0.012); tail.rotation.x = 0.35;
      }
      if (s.hair === "konde") part(head, new THREE.SphereGeometry(0.19, 20, 14), hairM, [0, top - 0.05, -hd / 2 - 0.12], 0.012);
      if (s.hair === "botak") for (const sx of [-1, 1]) { const tuft = part(head, rbox(0.07, 0.2, hd * 0.5, 0.48), hairM, [sx * (hw / 2 - 0.012), 0.06, -hd * 0.18], 0.008); tuft.rotation.z = sx * 0.05; }
    }
    if (s.hat === "peci") part(head, rbox(hw * 0.9, 0.24, hd * 0.86, 0.22), clay("#1d1a1c", undefined, 0.95), [0, top + 0.06, -0.02], 0.012);
    if (s.glasses) {
      const fm = clay("#2b2220", undefined, 0.4);
      for (const sx of [-1, 1]) part(head, new THREE.TorusGeometry(0.115, 0.016, 8, 24), fm, [sx * hw * 0.18, 0.02, hd / 2 + 0.035], 0);
      part(head, new THREE.CylinderGeometry(0.012, 0.012, 0.07, 6), fm, [0, 0.05, hd / 2 + 0.035], 0).rotation.z = Math.PI / 2;
      const lens = new THREE.MeshStandardMaterial({ color: "#ffffff", transparent: true, opacity: 0.18, roughness: 0.1 });
      for (const sx of [-1, 1]) part(head, new THREE.CircleGeometry(0.11, 24), lens, [sx * hw * 0.18, 0.02, hd / 2 + 0.034], 0);
    }

    this.height = this.hipY + th + hh + 0.05;
    this.setExpr("netral");
    this.pose({});
  }

  setExpr(e: Expr, opt: { blink?: boolean; look?: [number, number]; talk?: number } = {}) {
    const look: [number, number] = [Math.round((opt.look?.[0] ?? 0) * 2) / 2, Math.round((opt.look?.[1] ?? 0) * 2) / 2];
    const talk = Math.round((opt.talk ?? 0) * 2) / 2;
    const key = `${e}|${opt.blink ? 1 : 0}|${look[0]},${look[1]}|${talk}`;
    let t = this.faceTex.get(key);
    if (!t) {
      const c = document.createElement("canvas");
      c.width = c.height = PX;
      drawFace(c.getContext("2d")!, this.spec, e, look, !!opt.blink, talk);
      t = new THREE.CanvasTexture(c);
      t.colorSpace = THREE.SRGBColorSpace;
      t.anisotropy = 4;
      this.faceTex.set(key, t);
    }
    if (this.faceMat.map !== t) { this.faceMat.map = t; this.faceMat.needsUpdate = true; }
  }

  pose(p: Pose) {
    const w = p.walk ?? 0, amp = p.walkAmp ?? 0;
    const swing = Math.sin(w) * amp;
    this.legL.pivot.rotation.x = swing;
    this.legR.pivot.rotation.x = -swing;
    this.armL.pivot.rotation.set(-(p.armLf ?? 0) - swing * 0.8, 0, 0.12 + (p.armL ?? 0));
    this.armR.pivot.rotation.set(-(p.armRf ?? 0) + swing * 0.8, 0, -0.12 - (p.armR ?? 0));
    this.headPivot.rotation.set((p.headNod ?? 0) + this.stoop * 0.4, p.headYaw ?? 0, p.headTilt ?? 0);
    this.body.rotation.x = (p.lean ?? 0) + this.stoop;
    this.body.position.y = (p.bounce ?? 0) + Math.abs(Math.cos(w)) * amp * 0.06;
  }
}

// ---------- Si Belang, the kampung cat ----------
export class Kucing {
  readonly group = new THREE.Group();
  private tail: THREE.Group;
  private faceMat: THREE.MeshStandardMaterial;
  readonly height = 0.62;
  constructor(base = "#e8963f", belly = "#fff3e0") {
    const fur = clay(base, patternTex({ kind: "garis", base, accent: shade(base, 0.72), repeat: 1 }));
    const white = clay(belly);
    const body = part(this.group, rbox(0.34, 0.3, 0.6, 0.42), fur, [0, 0.28, 0]);
    part(this.group, rbox(0.26, 0.2, 0.1, 0.4), white, [0, 0.27, 0.27], 0.01);
    for (const [x, z] of [[-0.11, 0.2], [0.11, 0.2], [-0.11, -0.2], [0.11, -0.2]]) part(this.group, capsule(0.05, 0.12), fur, [x, 0.1, z], 0.01);
    for (const [x, z] of [[-0.11, 0.22], [0.11, 0.22], [-0.11, -0.18], [0.11, -0.18]]) part(this.group, new THREE.SphereGeometry(0.055, 12, 8), white, [x, 0.04, z], 0.008);
    const head = new THREE.Group(); head.position.set(0, 0.5, 0.3); this.group.add(head);
    const hm = part(head, rbox(0.4, 0.32, 0.32, 0.42), fur, [0, 0, 0], 0.012);
    for (const sx of [-1, 1]) { const ear = part(head, new THREE.ConeGeometry(0.075, 0.14, 4), fur, [sx * 0.12, 0.19, -0.02], 0.01); ear.rotation.y = Math.PI / 4; }
    part(head, rbox(0.18, 0.1, 0.06, 0.45), white, [0, -0.07, 0.15], 0);
    hm.updateMatrixWorld(true);
    this.faceMat = new THREE.MeshStandardMaterial({ transparent: true, roughness: 0.5, polygonOffset: true, polygonOffsetFactor: -4, depthWrite: false });
    const c = document.createElement("canvas"); c.width = c.height = 256;
    const g = c.getContext("2d")!; g.lineCap = "round";
    for (const sx of [-1, 1]) {
      g.fillStyle = "#9ad04a"; g.beginPath(); g.ellipse(128 + sx * 52, 110, 24, 28, 0, 0, Math.PI * 2); g.fill();
      g.fillStyle = "#1c120c"; g.beginPath(); g.ellipse(128 + sx * 52, 112, 8, 22, 0, 0, Math.PI * 2); g.fill();
      g.fillStyle = "#fff"; g.beginPath(); g.arc(128 + sx * 52 + 8, 100, 6, 0, Math.PI * 2); g.fill();
      g.strokeStyle = "#3b2417"; g.lineWidth = 3; for (const dy of [-6, 6]) { g.beginPath(); g.moveTo(128 + sx * 40, 170 + dy); g.lineTo(128 + sx * 110, 160 + dy * 2.2); g.stroke(); }
    }
    g.fillStyle = "#e46f82"; g.beginPath(); g.moveTo(116, 150); g.lineTo(140, 150); g.lineTo(128, 164); g.fill();
    g.strokeStyle = "#3b2417"; g.lineWidth = 5; g.beginPath(); g.arc(116, 168, 12, 0, Math.PI * 0.9); g.moveTo(152, 168); g.arc(140, 168, 12, 0, Math.PI * 0.9); g.stroke();
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; this.faceMat.map = t;
    const face = new THREE.Mesh(new DecalGeometry(hm, new THREE.Vector3(0, 0, 0.16), new THREE.Euler(), new THREE.Vector3(0.38, 0.3, 0.2)), this.faceMat);
    face.renderOrder = 2; head.add(face);
    this.tail = new THREE.Group(); this.tail.position.set(0, 0.36, -0.3); this.group.add(this.tail);
    const curve = new THREE.CatmullRomCurve3([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0.12, -0.12), new THREE.Vector3(0, 0.32, -0.12), new THREE.Vector3(0.05, 0.42, 0)]);
    part(this.tail, new THREE.TubeGeometry(curve, 20, 0.04, 8, false), fur, [0, 0, 0], 0.01);
    void body;
  }
  pose(t: number) { this.tail.rotation.z = Math.sin(t * 2.2) * 0.35; }
}
