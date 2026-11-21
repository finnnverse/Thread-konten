// The kampung set: one alley ("Gang Mawar") with houses on both sides, Bu Lastri's warung, Mbah Sarni's terrace,
// trees, a power pole, chickens, plus an indoor living-room set far away (x = ROOM_X). Built from code, same every video.
import * as THREE from "three";
import { clay, part, rbox, patternTex, shade } from "./cast3d";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

/** Bake every static mesh under root into one mesh per (material, shadow flags): hundreds of draw calls -> a few dozen.
 *  Objects with userData.dynamic (and their children) are left alone. */
export function freezeStatic(root: THREE.Object3D) {
  root.updateMatrixWorld(true);
  const buckets = new Map<string, { mat: THREE.Material; cast: boolean; recv: boolean; geos: THREE.BufferGeometry[]; order: number }>();
  const doomed: THREE.Mesh[] = [];
  const walk = (o: THREE.Object3D) => {
    if (o.userData.dynamic) return;
    if ((o as THREE.Mesh).isMesh && !(o as THREE.Mesh & { isInstancedMesh?: boolean }).isInstancedMesh) {
      const m = o as THREE.Mesh;
      const mat = m.material as THREE.Material;
      const key = `${mat.uuid}|${m.castShadow}|${m.receiveShadow}|${m.renderOrder}`;
      let g = m.geometry.index ? m.geometry.toNonIndexed() : m.geometry.clone();
      g.applyMatrix4(m.matrixWorld);
      const keep = ["position", "normal", "uv"];
      for (const a of Object.keys(g.attributes)) if (!keep.includes(a)) g.deleteAttribute(a);
      if (!g.attributes.uv) g.setAttribute("uv", new THREE.Float32BufferAttribute(new Float32Array(g.attributes.position.count * 2), 2));
      if (!g.attributes.normal) g.computeVertexNormals();
      g.clearGroups();
      let b = buckets.get(key);
      if (!b) { b = { mat, cast: m.castShadow, recv: m.receiveShadow, geos: [], order: m.renderOrder }; buckets.set(key, b); }
      b.geos.push(g);
      doomed.push(m);
    }
    o.children.forEach(walk);
  };
  root.children.forEach(walk);
  for (const m of doomed) { const kids = m.children.filter((c) => c.userData.dynamic); m.parent?.remove(m); kids.forEach((k) => root.add(k)); }
  // drop now-empty groups
  const prune = (o: THREE.Object3D) => { [...o.children].forEach(prune); if (o !== root && (o as THREE.Group).isGroup && !o.children.length && !o.userData.dynamic) o.parent?.remove(o); };
  prune(root);
  for (const b of buckets.values()) {
    const merged = new THREE.Mesh(mergeGeometries(b.geos, false)!, b.mat);
    merged.castShadow = b.cast; merged.receiveShadow = b.recv; merged.renderOrder = b.order;
    root.add(merged);
  }
}

export const ROOM_X = 60; // indoor set origin
export const DAPUR_X = 80; // kitchen set origin
export type Light = "pagi" | "subuh" | "malam";
export const FONT = "Nunito";

const rng = (seed: number) => () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };

const canvasTex = (w: number, h: number, draw: (g: CanvasRenderingContext2D) => void) => {
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  draw(c.getContext("2d")!);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
};

export const signTex = (text: string, bg: string, fg: string, w = 512, h = 160, sub?: string) => canvasTex(w, h, (g) => {
  g.fillStyle = bg; g.fillRect(0, 0, w, h);
  g.strokeStyle = fg; g.lineWidth = 8; g.strokeRect(10, 10, w - 20, h - 20);
  g.fillStyle = fg; g.textAlign = "center"; g.textBaseline = "middle";
  g.font = `900 ${Math.round(h * (sub ? 0.36 : 0.46))}px ${FONT}`;
  g.fillText(text, w / 2, sub ? h * 0.4 : h / 2, w - 40);
  if (sub) { g.font = `800 ${Math.round(h * 0.2)}px ${FONT}`; g.fillText(sub, w / 2, h * 0.74, w - 40); }
});

const tileTex = (base: string) => canvasTex(256, 256, (g) => {
  g.fillStyle = base; g.fillRect(0, 0, 256, 256);
  for (let y = 0; y < 8; y++) {
    g.fillStyle = shade(base, 0.78); g.fillRect(0, y * 32 + 26, 256, 6);
    for (let x = 0; x < 8; x++) { g.fillStyle = shade(base, 0.86 + ((x * 7 + y * 3) % 5) * 0.04); g.beginPath(); g.roundRect(x * 32 + (y % 2) * 16 + 2, y * 32 + 2, 28, 24, 6); g.fill(); }
  }
});
const pavingTex = () => canvasTex(512, 512, (g) => {
  g.fillStyle = "#b9aa95"; g.fillRect(0, 0, 512, 512);
  for (let y = 0; y < 16; y++) for (let x = 0; x < 8; x++) {
    const o = (y % 2) * 32;
    g.fillStyle = `hsl(${30 + ((x * 7 + y * 13) % 7)}, 14%, ${66 + ((x * 5 + y * 3) % 6)}%)`;
    g.beginPath(); g.roundRect(x * 64 + o + 3, y * 32 + 3, 58, 26, 6); g.fill();
  }
});
const grassTex = () => canvasTex(256, 256, (g) => {
  g.fillStyle = "#7fae4e"; g.fillRect(0, 0, 256, 256);
  const r = rng(7);
  for (let i = 0; i < 500; i++) { g.fillStyle = r() > 0.5 ? "#8cbc58" : "#6f9c43"; g.fillRect(r() * 256, r() * 256, 3, 6); }
});
const plankTex = (base: string) => canvasTex(256, 256, (g) => {
  g.fillStyle = base; g.fillRect(0, 0, 256, 256);
  for (let x = 0; x < 256; x += 32) { g.fillStyle = shade(base, 0.8); g.fillRect(x, 0, 4, 256); }
});

const WALLS = ["#f3e3c0", "#cfe6d4", "#f6cfb4", "#cfe0f0", "#efe6a8", "#e9d2e6"];
const TRIMS = ["#2f7d6d", "#b5502f", "#3e6aa8", "#7a5a2e", "#2f7d6d", "#a0463f"];

type HouseOpt = { side: -1 | 1; z: number; w: number; wall: string; trim: string; kind?: "rumah" | "warung" | "teras" };

export class KampungSet {
  readonly root = new THREE.Group();
  readonly sun: THREE.DirectionalLight;
  private hemi!: THREE.HemisphereLight; private fill!: THREE.DirectionalLight; private skyMat!: THREE.ShaderMaterial; private fog!: THREE.Fog;
  private lamps: THREE.PointLight[] = []; private lampGlow: THREE.MeshStandardMaterial[] = [];
  private light: Light = "pagi";
  private chickens: THREE.Group[] = [];
  private clouds: THREE.Group[] = [];
  readonly spots: Record<string, [number, number]> = {
    warung_depan: [-1.2, 1.5], warung_dalam: [-2.55, 1.5], teras_mbah: [3.4, 1.5], gerbang: [0, 9], gang_tengah: [0, -5], gang_ujung: [0, -20],
    ruang_tamu: [ROOM_X, 0],
  };

  constructor(scene: THREE.Scene) {
    scene.add(this.root);
    // sky dome
    const sky = new THREE.Mesh(new THREE.SphereGeometry(200, 32, 16), this.skyMat = new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false, fog: false,
      uniforms: { top: { value: new THREE.Color("#78b4e6") }, hor: { value: new THREE.Color("#f6e6c8") } },
      vertexShader: "varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",
      fragmentShader: "uniform vec3 top; uniform vec3 hor; varying vec3 vP; void main(){ float h = clamp(normalize(vP).y * 2.2, 0.0, 1.0); gl_FragColor = vec4(mix(hor, top, pow(h, 0.7)), 1.0); }",
    }));
    sky.userData.dynamic = true;
    this.root.add(sky);
    scene.fog = this.fog = new THREE.Fog("#f3e2c4", 35, 120);

    scene.add(this.hemi = new THREE.HemisphereLight("#fff1d6", "#8f7a5c", 1.25));
    this.sun = new THREE.DirectionalLight("#ffdfae", 2.7);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    this.sun.shadow.bias = -0.0004; this.sun.shadow.normalBias = 0.03; this.sun.shadow.radius = 5;
    Object.assign(this.sun.shadow.camera, { left: -9, right: 9, top: 9, bottom: -9, near: 1, far: 60 });
    scene.add(this.sun, this.sun.target);
    const fill = this.fill = new THREE.DirectionalLight("#cfe0ff", 0.6); fill.position.set(-8, 6, 10); scene.add(fill);
    this.setFocus(0, 0);

    this.ground();
    this.gang();
    const lots = [8.5, 1.5, -5.5, -12.5, -19.5, -26.5];
    lots.forEach((z, i) => {
      this.house({ side: -1, z, w: 5.8, wall: WALLS[i % 6], trim: TRIMS[i % 6], kind: z === 1.5 ? "warung" : "rumah" });
      this.house({ side: 1, z: z - 1.2, w: 5.6, wall: WALLS[(i + 3) % 6], trim: TRIMS[(i + 2) % 6], kind: z === 1.5 ? "teras" : "rumah" });
    });
    const r = rng(11);
    for (const z of [5, -2, -9, -16, -23]) for (const sx of [-1, 1]) this.mango(sx * (8.5 + r() * 2), z + r() * 1.5, 0.9 + r() * 0.4);
    for (const [x, z] of [[-2.55, 5.2], [2.55, -2.3], [-2.55, -9.2], [2.55, -15.6], [2.55, 5.9]]) this.banana(x, z);
    for (const z of [6.5, -6, -18.5]) this.pole(2.45, z);
    this.wires([6.5, -6, -18.5]);
    this.gate();
    for (const [x, z, a] of [[1.0, -2, 0.6], [-0.4, -3.2, 2.2], [0.8, 3.8, -1]]) this.chicken(x, z, a);
    for (let i = 0; i < 7; i++) this.cloud(-60 + i * 22 + r() * 6, 26 + r() * 10, -70 - r() * 30, 1.6 + r());
    this.room();
    this.dapur();
    freezeStatic(this.root);
  }

  /** time-of-day look: pagi (warm day), subuh (cool dawn), malam (night, lamps on) */
  setLight(l: Light) {
    this.light = l;
    const P = {
      pagi: { hs: "#fff1d6", hg: "#8f7a5c", hi: 1.25, sc: "#ffdfae", si: 2.7, fi: 0.6, top: "#78b4e6", hor: "#f6e6c8", fog: "#f3e2c4", lamp: 0 },
      subuh: { hs: "#c9d3ef", hg: "#5d5a6a", hi: 1.0, sc: "#ffbf94", si: 1.4, fi: 0.5, top: "#8199d0", hor: "#f2c3a4", fog: "#d8c3bd", lamp: 0.5 },
      malam: { hs: "#46599a", hg: "#14141d", hi: 0.28, sc: "#a9bcff", si: 0.18, fi: 0.08, top: "#0c1430", hor: "#283058", fog: "#161c38", lamp: 0.55 },
    }[l];
    this.hemi.color.set(P.hs); this.hemi.groundColor.set(P.hg); this.hemi.intensity = P.hi;
    this.sun.color.set(P.sc); this.sun.intensity = P.si; this.fill.intensity = P.fi;
    (this.skyMat.uniforms.top.value as THREE.Color).set(P.top); (this.skyMat.uniforms.hor.value as THREE.Color).set(P.hor);
    this.fog.color.set(P.fog);
    // lamps only exist (in the shader) when lit: unlit point lights still cost every pixel of every material
    this.lamps.forEach((lp) => { lp.intensity = (lp.userData.base as number) * P.lamp; lp.visible = P.lamp > 0; });
    this.lampGlow.forEach((m) => (m.emissiveIntensity = 0.2 + 2.2 * P.lamp));
  }

  /** move the sun's shadow box to follow the action */
  setFocus(x: number, z: number) {
    const low = this.light === "subuh";
    this.sun.position.set(x + (low ? 14 : 9), low ? 6 : 16, z + 11);
    this.sun.target.position.set(x, 0, z);
    this.sun.target.updateMatrixWorld();
  }

  tick(t: number) {
    this.chickens.forEach((c, i) => {
      const peck = Math.max(0, Math.sin(t * 3 + i * 2)) ** 6;
      (c.children[0] as THREE.Object3D).rotation.x = peck * 0.9;
      c.position.y = Math.abs(Math.sin(t * 6 + i)) * 0.01;
    });
    this.clouds.forEach((c, i) => { c.position.x += 0; c.position.x = (c.userData.x0 as number) + t * 0.25 * (1 + i * 0.1); });
  }

  private ground() {
    const gt = grassTex(); gt.wrapS = gt.wrapT = THREE.RepeatWrapping; gt.repeat.set(60, 60);
    const g = new THREE.Mesh(new THREE.PlaneGeometry(240, 240), new THREE.MeshStandardMaterial({ map: gt, roughness: 0.95 }));
    g.rotation.x = -Math.PI / 2; g.position.y = -0.01; g.receiveShadow = true; this.root.add(g);
  }

  private gang() {
    const pt = pavingTex(); pt.wrapS = pt.wrapT = THREE.RepeatWrapping; pt.repeat.set(2.2, 26);
    const p = new THREE.Mesh(new THREE.PlaneGeometry(4.4, 56), new THREE.MeshStandardMaterial({ map: pt, roughness: 0.9 }));
    p.rotation.x = -Math.PI / 2; p.position.set(0, 0.005, -14); p.receiveShadow = true; this.root.add(p);
    // gutters + yard strips
    const conc = clay("#a9a196", undefined, 0.95);
    for (const sx of [-1, 1]) {
      part(this.root, new THREE.BoxGeometry(0.25, 0.08, 56), clay("#8d857a"), [sx * 2.32, 0.02, -14], 0);
      const yard = new THREE.Mesh(new THREE.PlaneGeometry(0.6, 56), conc); yard.rotation.x = -Math.PI / 2; yard.position.set(sx * 2.75, 0.01, -14); yard.receiveShadow = true; this.root.add(yard);
    }
  }

  private house(o: HouseOpt) {
    const D = 5, H = 3.0, g = new THREE.Group();
    g.position.set(o.side * (3.05 + D / 2), 0, o.z);
    g.rotation.y = o.side < 0 ? Math.PI / 2 : -Math.PI / 2;
    this.root.add(g);
    const W = o.w;
    const wallM = clay(o.wall, undefined, 0.9), trimM = clay(o.trim);
    part(g, rbox(W, H, D, 0.03), wallM, [0, H / 2, 0], 0.02);
    part(g, rbox(W + 0.08, 0.4, D + 0.08, 0.2), clay(shade(o.wall, 0.7)), [0, 0.2, 0], 0.015);
    // gable roof along local x
    const sh = new THREE.Shape();
    const over = 0.5, front = o.kind === "rumah" ? 0.7 : 1.7;
    sh.moveTo(-(D / 2 + front), 0); sh.lineTo(0, 1.7); sh.lineTo(D / 2 + over, 0); sh.lineTo(D / 2 + over, -0.14); sh.lineTo(0, 1.56); sh.lineTo(-(D / 2 + front), -0.14);
    const rg = new THREE.ExtrudeGeometry(sh, { depth: W + 0.7, bevelEnabled: false });
    rg.translate(0, 0, -(W + 0.7) / 2); rg.rotateY(-Math.PI / 2);
    const tt = tileTex("#c0583a"); tt.wrapS = tt.wrapT = THREE.RepeatWrapping; tt.repeat.set(0.5, 0.5);
    const roof = part(g, rg, new THREE.MeshStandardMaterial({ map: tt, roughness: 0.85 }), [0, H, 0], 0.02);
    roof.scale.z = 1; roof.rotation.y = Math.PI; // front (+z) gets the long overhang
    // gable end walls (triangles)
    const tri = new THREE.Shape(); tri.moveTo(-D / 2, 0); tri.lineTo(0, 1.55); tri.lineTo(D / 2, 0);
    for (const sx of [-1, 1]) { const m = part(g, new THREE.ShapeGeometry(tri), wallM, [sx * (W / 2 - 0.01), H, 0], 0); m.rotation.y = Math.PI / 2; (m.material as THREE.Material).side = THREE.DoubleSide; }
    const F = D / 2 + 0.02;
    const r = rng(Math.round(o.z * 10 + o.side * 100 + 500));
    if (o.kind === "warung") return this.warung(g, W, F, trimM);
    // door + windows
    part(g, rbox(1.0, 2.1, 0.1, 0.1), clay(shade(o.trim, 0.85)), [-W * 0.25, 1.05 + 0.2, F], 0.012);
    part(g, rbox(1.16, 2.24, 0.06, 0.1), clay("#f4efe4"), [-W * 0.25, 1.1 + 0.2, F - 0.03], 0);
    part(g, new THREE.SphereGeometry(0.05, 10, 8), clay("#d9b24a", undefined, 0.3), [-W * 0.25 + 0.35, 1.2, F + 0.08], 0);
    for (const wx of [W * 0.12, W * 0.34]) this.window(g, wx, 1.75, F, o.trim);
    if (o.kind === "teras") {
      part(g, rbox(W, 0.16, 1.6, 0.2), clay("#c9a27a", plankTex("#c9a27a")), [0, 0.08, F + 0.8], 0.012);
      for (const px of [-W / 2 + 0.2, W / 2 - 0.2]) part(g, new THREE.CylinderGeometry(0.08, 0.08, H, 10), clay("#8b5a32"), [px, H / 2, F + 1.5], 0.01);
      // bamboo bench (amben) + jamu bottles
      part(g, rbox(1.7, 0.1, 0.7, 0.3), clay("#d7b46a", patternTex({ kind: "garis", base: "#d7b46a", accent: "#b9944c", repeat: 3 })), [W * 0.2, 0.55, F + 0.75], 0.01);
      for (const lx of [-0.75, 0.75]) for (const lz of [-0.28, 0.28]) part(g, new THREE.CylinderGeometry(0.04, 0.04, 0.5, 8), clay("#b9944c"), [W * 0.2 + lx, 0.28, F + 0.75 + lz], 0);
      const jamu = ["#e8b83a", "#b5652d", "#7aa63a", "#e07a2a"];
      jamu.forEach((c, i) => {
        part(g, new THREE.CylinderGeometry(0.07, 0.07, 0.26, 12), new THREE.MeshStandardMaterial({ color: c, roughness: 0.25, transparent: true, opacity: 0.9 }), [W * 0.2 - 0.45 + i * 0.3, 0.73, F + 0.65], 0.006);
        part(g, new THREE.CylinderGeometry(0.035, 0.035, 0.06, 8), clay("#f4efe4"), [W * 0.2 - 0.45 + i * 0.3, 0.89, F + 0.65], 0);
      });
      part(g, rbox(0.7, 0.5, 0.45, 0.3), clay("#b07c4a", plankTex("#b07c4a")), [W * 0.2 + 0.6, 0.92, F + 0.85], 0.01); // gendongan basket
    } else {
      part(g, rbox(W, 0.14, 0.9, 0.2), clay("#b8b0a2"), [0, 0.07, F + 0.45], 0.01);
    }
    for (let i = 0; i < 2; i++) if (r() > 0.3) this.pot(g, -W * 0.25 + (i ? 0.85 : -0.85), F + 0.4);
  }

  private window(g: THREE.Group, x: number, y: number, F: number, trim: string) {
    part(g, rbox(1.0, 1.1, 0.1, 0.1), clay("#f4efe4"), [x, y, F], 0.01);
    const glass = new THREE.MeshStandardMaterial({ color: "#5d7f9c", roughness: 0.2, emissive: "#2a3b4a", emissiveIntensity: 0.3 });
    part(g, new THREE.PlaneGeometry(0.82, 0.92), glass, [x, y, F + 0.055], 0);
    part(g, new THREE.BoxGeometry(0.04, 0.92, 0.02), clay("#f4efe4"), [x, y, F + 0.06], 0);
    part(g, new THREE.BoxGeometry(0.82, 0.04, 0.02), clay("#f4efe4"), [x, y, F + 0.06], 0);
    for (const sx of [-1, 1]) part(g, rbox(0.42, 1.1, 0.06, 0.15), clay(trim, patternTex({ kind: "garis", base: trim, accent: shade(trim, 0.8), repeat: 3 })), [x + sx * 0.74, y, F + 0.03], 0.008);
  }

  private pot(g: THREE.Object3D, x: number, z: number) {
    part(g, new THREE.CylinderGeometry(0.2, 0.15, 0.32, 14), clay("#b8643c"), [x, 0.16, z], 0.01);
    for (let i = 0; i < 5; i++) { const a = (i / 5) * Math.PI * 2; const l = part(g, new THREE.SphereGeometry(0.16, 10, 8), clay("#4f8f3a"), [x + Math.cos(a) * 0.1, 0.42 + (i % 2) * 0.08, z + Math.sin(a) * 0.1], 0.008); l.scale.set(0.6, 1.2, 0.6); l.rotation.z = Math.cos(a) * 0.5; }
  }

  private warung(g: THREE.Group, W: number, F: number, trimM: THREE.Material) {
    // fake interior: dark opening with shelves full of goods behind a blue plank counter
    part(g, new THREE.PlaneGeometry(W * 0.8, 1.9), clay("#5b4636"), [0.0, 1.55, F + 0.005], 0);
    const shelfM = clay("#8b5a32", plankTex("#8b5a32"));
    const r = rng(42);
    const goods = ["#e04848", "#f2c335", "#3f8fd8", "#4fb36a", "#f08a3a", "#ffffff", "#c94fa0"];
    for (let k = 0; k < 3; k++) {
      const y = 1.0 + k * 0.55;
      part(g, rbox(W * 0.78, 0.06, 0.3, 0.2), shelfM, [0, y, F + 0.14], 0.008);
      for (let x = -W * 0.36; x < W * 0.36; x += 0.16 + r() * 0.08) {
        const c = goods[Math.floor(r() * goods.length)], h = 0.16 + r() * 0.2;
        if (r() > 0.5) part(g, rbox(0.13, h, 0.13, 0.15), clay(c), [x, y + h / 2 + 0.03, F + 0.14], 0.006);
        else part(g, new THREE.CylinderGeometry(0.055, 0.055, h, 10), clay(c, undefined, 0.35), [x, y + h / 2 + 0.03, F + 0.14], 0.006);
      }
    }
    // hanging snack sachets
    for (let i = 0; i < 9; i++) part(g, new THREE.BoxGeometry(0.12, 0.2, 0.01), clay(goods[i % goods.length]), [-W * 0.36 + i * 0.1, 2.42 - (i % 3) * 0.06, F + 0.6], 0);
    // counter
    part(g, rbox(W * 0.86, 1.05, 0.7, 0.08), clay("#3f78b5", plankTex("#3f78b5")), [0, 0.52, F + 1.05], 0.015);
    part(g, rbox(W * 0.9, 0.08, 0.86, 0.3), clay("#d8a96a"), [0, 1.08, F + 1.05], 0.012);
    // jars + biscuit tin on the counter
    for (const [x, c] of [[-1.6, "#e8c84a"], [-1.25, "#e07a5a"], [1.3, "#8fd07a"]] as [number, string][]) {
      part(g, new THREE.CylinderGeometry(0.13, 0.13, 0.3, 14), new THREE.MeshStandardMaterial({ color: "#ffffff", roughness: 0.1, transparent: true, opacity: 0.45 }), [x, 1.27, F + 1.05], 0.006);
      part(g, new THREE.CylinderGeometry(0.1, 0.1, 0.18, 12), clay(c), [x, 1.21, F + 1.05], 0);
      part(g, new THREE.CylinderGeometry(0.14, 0.14, 0.05, 14), clay("#e04848"), [x, 1.44, F + 1.05], 0.006);
    }
    part(g, rbox(0.42, 0.06, 0.32, 0.3), clay("#f4efe4"), [0.4, 1.15, F + 1.0], 0.006); // ledger book
    // striped awning + sign
    const aw = part(g, new THREE.PlaneGeometry(W * 0.95, 1.4), new THREE.MeshStandardMaterial({ map: patternTex({ kind: "garis", base: "#e85a4a", accent: "#fff4e6", repeat: 2 }), side: THREE.DoubleSide, roughness: 0.8 }), [0, 2.75, F + 0.9], 0);
    aw.rotation.x = -1.0;
    const sign = part(g, rbox(2.6, 0.62, 0.08, 0.1), new THREE.MeshStandardMaterial({ map: signTex("WARUNG BU LASTRI", "#fff4dc", "#b5302a", 640, 160, "sedia sembako & jajanan"), roughness: 0.6 }), [0, 3.45, F + 0.05], 0.012);
    void sign; void trimM;
  }

  private mango(x: number, z: number, s: number) {
    const g = new THREE.Group(); g.position.set(x, 0, z); g.scale.setScalar(s); this.root.add(g);
    part(g, new THREE.CylinderGeometry(0.18, 0.28, 3.2, 10), clay("#7a5232"), [0, 1.6, 0], 0.02);
    const leaf = clay("#4e9a3e", undefined, 0.85), leaf2 = clay("#5fae48", undefined, 0.85);
    for (const [px, py, pz, r] of [[0, 3.8, 0, 1.6], [1.0, 3.3, 0.3, 1.1], [-1.0, 3.4, -0.2, 1.2], [0.3, 4.6, -0.3, 1.1], [-0.4, 3.2, 0.9, 1.0]]) part(g, new THREE.SphereGeometry(r, 18, 12), (px as number) > 0 ? leaf2 : leaf, [px, py, pz], 0.025);
    for (let i = 0; i < 6; i++) { const a = i * 1.1; part(g, new THREE.SphereGeometry(0.12, 10, 8), clay("#f2b437"), [Math.cos(a) * 1.3, 3.1 + (i % 3) * 0.3, Math.sin(a) * 1.3], 0); }
  }

  private banana(x: number, z: number) {
    const g = new THREE.Group(); g.position.set(x, 0, z); this.root.add(g);
    part(g, new THREE.CylinderGeometry(0.1, 0.16, 2.0, 10), clay("#8aa64a"), [0, 1.0, 0], 0.012);
    const lm = clay("#5aa53e", undefined, 0.8);
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2, piv = new THREE.Group(); piv.position.set(0, 2.0, 0); piv.rotation.y = a; g.add(piv);
      const l = part(piv, new THREE.SphereGeometry(0.5, 12, 8), lm, [0, 0.15, 0.6], 0.008); l.scale.set(0.35, 0.06, 1.5); l.rotation.x = 0.35 + (i % 2) * 0.25;
    }
  }

  private pole(x: number, z: number) {
    part(this.root, new THREE.CylinderGeometry(0.09, 0.12, 7, 10), clay("#9a9a96"), [x, 3.5, z], 0.012);
    part(this.root, rbox(1.2, 0.1, 0.1, 0.3), clay("#6a6a66"), [x, 6.6, z], 0.008);
  }
  private wires(zs: number[]) {
    const m = new THREE.MeshBasicMaterial({ color: "#2a2422" });
    for (const dx of [-0.5, 0, 0.5]) for (let i = 0; i < zs.length - 1; i++) {
      const a = new THREE.Vector3(2.45 + dx, 6.62, zs[i]), b = new THREE.Vector3(2.45 + dx, 6.62, zs[i + 1]);
      const mid = a.clone().lerp(b, 0.5); mid.y -= 0.6;
      this.root.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(a, mid, b), 20, 0.015, 4), m));
    }
  }
  private gate() {
    for (const sx of [-1, 1]) part(this.root, rbox(0.35, 3.4, 0.35, 0.15), clay("#f4efe4", patternTex({ kind: "garis", base: "#f4efe4", accent: "#d23b33", repeat: 3 })), [sx * 2.4, 1.7, 10], 0.015);
    part(this.root, rbox(5.4, 0.8, 0.2, 0.15), new THREE.MeshStandardMaterial({ map: signTex("GANG MAWAR", "#2f7d6d", "#fff6e0", 640, 120, "RT 03 / RW 05"), roughness: 0.6 }), [0, 3.5, 10], 0.015);
  }
  private chicken(x: number, z: number, a: number) {
    const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = a; g.userData.dynamic = true; this.root.add(g);
    const head = new THREE.Group(); head.position.set(0, 0.32, 0.12); g.add(head);
    part(head, new THREE.SphereGeometry(0.08, 12, 10), clay("#fbf5ea"), [0, 0.06, 0.04], 0.006);
    part(head, new THREE.ConeGeometry(0.025, 0.06, 6), clay("#f0a82a"), [0, 0.05, 0.13], 0).rotation.x = Math.PI / 2;
    part(head, rbox(0.03, 0.06, 0.08, 0.4), clay("#d8302a"), [0, 0.15, 0.04], 0);
    const b = part(g, new THREE.SphereGeometry(0.17, 14, 10), clay("#fbf5ea"), [0, 0.22, 0], 0.01); b.scale.set(0.9, 0.85, 1.15);
    part(g, new THREE.SphereGeometry(0.08, 10, 8), clay("#c9672e"), [0, 0.3, -0.18], 0.006).scale.set(0.6, 1.4, 1);
    for (const sx of [-1, 1]) part(g, new THREE.CylinderGeometry(0.012, 0.012, 0.1, 6), clay("#f0a82a"), [sx * 0.05, 0.05, 0], 0);
    g.children.unshift(g.children.splice(g.children.indexOf(head), 1)[0]); // keep head at index 0 for tick()
    this.chickens.push(g);
  }
  private cloud(x: number, y: number, z: number, s: number) {
    const g = new THREE.Group(); g.position.set(x, y, z); g.scale.setScalar(s); g.userData.x0 = x; g.userData.dynamic = true; this.root.add(g);
    const m = new THREE.MeshStandardMaterial({ color: "#ffffff", roughness: 1, emissive: "#ffffff", emissiveIntensity: 0.35, fog: false });
    for (const [px, py, r] of [[0, 0, 3], [3, -0.6, 2.2], [-3, -0.8, 2.3], [1.2, 1.4, 2.2], [-1.5, 1.0, 2]]) { const b = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), m); b.position.set(px, py, 0); b.scale.z = 0.6; g.add(b); }
    this.clouds.push(g);
  }

  /** indoor living room at (ROOM_X, 0, 0): back wall at z = -3, side wall at x = ROOM_X - 3.5, open toward +z */
  private room() {
    const g = new THREE.Group(); g.position.set(ROOM_X, 0, 0); this.root.add(g);
    const floorT = canvasTex(256, 256, (c) => { c.fillStyle = "#e9dcc6"; c.fillRect(0, 0, 256, 256); c.strokeStyle = "#cdbb9e"; c.lineWidth = 3; for (let i = 0; i <= 256; i += 64) { c.beginPath(); c.moveTo(i, 0); c.lineTo(i, 256); c.moveTo(0, i); c.lineTo(256, i); c.stroke(); } });
    floorT.wrapS = floorT.wrapT = THREE.RepeatWrapping; floorT.repeat.set(5, 5);
    const fl = new THREE.Mesh(new THREE.PlaneGeometry(9, 9), new THREE.MeshStandardMaterial({ map: floorT, roughness: 0.6 })); fl.rotation.x = -Math.PI / 2; fl.position.y = 0.01; fl.receiveShadow = true; g.add(fl);
    const wallM = clay("#cfe3d8", undefined, 0.95);
    part(g, new THREE.BoxGeometry(9, 3.4, 0.2), wallM, [0, 1.7, -3], 0);
    part(g, new THREE.BoxGeometry(0.2, 3.4, 9), wallM, [-3.5, 1.7, 0], 0);
    part(g, new THREE.BoxGeometry(9, 1.0, 0.22), clay("#7fb39b"), [0, 0.5, -2.99], 0);
    // window on back wall
    this.window(g, 1.6, 1.8, -2.89, "#2f7d6d");
    // sofa
    const sofaM = clay("#7c5a8a", undefined, 0.9);
    part(g, rbox(2.2, 0.45, 0.85, 0.3), sofaM, [-1.0, 0.42, -2.3], 0.015);
    part(g, rbox(2.2, 0.75, 0.25, 0.3), sofaM, [-1.0, 0.85, -2.65], 0.015);
    for (const sx of [-1, 1]) part(g, rbox(0.25, 0.6, 0.85, 0.3), sofaM, [-1.0 + sx * 1.1, 0.62, -2.3], 0.015);
    // low table + teapot & cups
    part(g, rbox(1.3, 0.08, 0.7, 0.3), clay("#9a6b40", plankTex("#9a6b40")), [-1.0, 0.45, -1.2], 0.012);
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) part(g, new THREE.CylinderGeometry(0.04, 0.04, 0.42, 8), clay("#7a5232"), [-1.0 + sx * 0.55, 0.21, -1.2 + sz * 0.28], 0);
    part(g, new THREE.SphereGeometry(0.13, 14, 10), clay("#f4efe4", undefined, 0.3), [-1.2, 0.6, -1.2], 0.008);
    for (const dx of [-0.6, -0.8]) part(g, new THREE.CylinderGeometry(0.05, 0.04, 0.09, 10), clay("#f4efe4", undefined, 0.3), [dx + 0.2 - 0.8 + 1.1, 0.54, -1.05], 0.005);
    // calendar, framed photo, wall clock
    part(g, rbox(0.6, 0.8, 0.03, 0.1), new THREE.MeshStandardMaterial({ map: signTex("2025", "#ffffff", "#c8302c", 256, 320), roughness: 0.7 }), [-2.6, 2.0, -2.88], 0.006);
    part(g, rbox(0.7, 0.55, 0.04, 0.1), clay("#6b4426"), [-0.6, 2.25, -2.88], 0.006);
    part(g, new THREE.PlaneGeometry(0.58, 0.43), clay("#d9c39a"), [-0.6, 2.25, -2.855], 0);
    part(g, new THREE.CylinderGeometry(0.22, 0.22, 0.05, 20), clay("#f4efe4"), [0.4, 2.6, -2.88], 0.006).rotation.x = Math.PI / 2;
    // room light
  }

  /** Mbah Sarni's kitchen at (DAPUR_X, 0, 0). Back wall z = -3.2, left wall x = DX-3.2, right wall x = DX+3.0 with a
   *  door gap at z -1.05..0.05. Work table (island) centred at (DX, 0.85, -1.5); the cook stands behind it at z ≈ -2.35. */
  private dapur() {
    const DX = DAPUR_X, g = new THREE.Group(); g.position.set(DX, 0, 0); this.root.add(g);
    const tegel = canvasTex(256, 256, (c) => { for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) { c.fillStyle = (x + y) % 2 ? "#c7533f" : "#e9d9bd"; c.fillRect(x * 64, y * 64, 64, 64); } });
    tegel.wrapS = tegel.wrapT = THREE.RepeatWrapping; tegel.repeat.set(4, 4);
    const fl = new THREE.Mesh(new THREE.PlaneGeometry(8, 8), new THREE.MeshStandardMaterial({ map: tegel, roughness: 0.55 })); fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0.01, -0.5); fl.receiveShadow = true; g.add(fl);
    const wallM = clay("#f2e3c6", undefined, 0.95), lowM = clay("#9cc9b4");
    part(g, new THREE.BoxGeometry(6.4, 3.2, 0.2), wallM, [-0.1, 1.6, -3.2], 0);
    part(g, new THREE.BoxGeometry(6.42, 0.9, 0.22), lowM, [-0.1, 0.45, -3.19], 0);
    part(g, new THREE.BoxGeometry(0.2, 3.2, 6), wallM, [-3.2, 1.6, -0.3], 0);
    // right wall with a door gap
    part(g, new THREE.BoxGeometry(0.2, 3.2, 2.1), wallM, [3.0, 1.6, -2.1], 0);
    part(g, new THREE.BoxGeometry(0.2, 3.2, 2.7), wallM, [3.0, 1.6, 1.4], 0);
    part(g, new THREE.BoxGeometry(0.2, 1.0, 1.1), wallM, [3.0, 2.7, -0.5], 0);
    for (const z of [-1.08, 0.08]) part(g, rbox(0.26, 2.2, 0.08, 0.3), clay("#8b5a32"), [3.0, 1.1, z], 0.008);
    // window over the back wall
    this.window(g, 1.7, 1.95, -3.09, "#2f7d6d");
    // shelf with jars behind the cook
    const shelfM = clay("#8b5a32", plankTex("#8b5a32"));
    for (const y of [1.55, 2.15]) part(g, rbox(2.2, 0.06, 0.32, 0.2), shelfM, [-1.2, y, -2.98], 0.008);
    const jarCols = ["#f2b437", "#e07a2a", "#c9a46a", "#7aa63a", "#f4efe4", "#b5652d"];
    jarCols.forEach((c, i) => {
      const x = -2.0 + (i % 3) * 0.75 + (i > 2 ? 0.3 : 0), y = i > 2 ? 2.18 : 1.58;
      part(g, new THREE.CylinderGeometry(0.11, 0.11, 0.26, 12), new THREE.MeshStandardMaterial({ color: "#ffffff", roughness: 0.1, transparent: true, opacity: 0.4 }), [x, y + 0.13, -2.95], 0.006);
      part(g, new THREE.CylinderGeometry(0.09, 0.09, 0.16, 10), clay(c), [x, y + 0.09, -2.95], 0);
      part(g, new THREE.CylinderGeometry(0.12, 0.12, 0.04, 12), clay("#c8302c"), [x, y + 0.28, -2.95], 0.005);
    });
    // stove (kompor) + kettle at the left wall
    part(g, rbox(0.9, 0.85, 0.7, 0.1), clay("#d8d2c4"), [-2.6, 0.43, -2.4], 0.012);
    part(g, new THREE.CylinderGeometry(0.2, 0.22, 0.26, 16), clay("#9aa0a6", undefined, 0.35), [-2.6, 1.0, -2.4], 0.01);
    // hanging pans
    for (let i = 0; i < 3; i++) { const pan = part(g, new THREE.CylinderGeometry(0.16 + i * 0.03, 0.14 + i * 0.03, 0.06, 16), clay("#6a6a66", undefined, 0.4), [-3.06, 1.9 + (i % 2) * 0.1, -1.6 + i * 0.45], 0.008); pan.rotation.z = Math.PI / 2; }
    // work table (island)
    const top = clay("#c99a62", plankTex("#c99a62"));
    part(g, rbox(2.6, 0.08, 0.9, 0.3), top, [0, 0.85, -1.5], 0.012);
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) part(g, rbox(0.08, 0.82, 0.08, 0.3), clay("#7a5232"), [sx * 1.2, 0.41, -1.5 + sz * 0.37], 0.008);
    part(g, rbox(2.4, 0.05, 0.8, 0.3), clay("#a07a4c"), [0, 0.25, -1.5], 0.008);
    // big pot of jamu + toples gula/kunyit/jahe on the table
    part(g, new THREE.CylinderGeometry(0.28, 0.24, 0.36, 20), clay("#b8bcc0", undefined, 0.3), [-0.35, 1.07, -1.55], 0.012);
    const jamu = new THREE.Mesh(new THREE.CircleGeometry(0.26, 24), clay("#e8a92e", undefined, 0.3)); jamu.rotation.x = -Math.PI / 2; jamu.position.set(-0.35, 1.2, -1.55); g.add(jamu);
    for (const [x, c, lab] of [[-1.05, "#f7f4ee", 0], [-0.8, "#f0a52a", 1], [-1.15, "#d8b27a", 2]] as [number, string, number][]) {
      const z = lab === 2 ? -1.8 : -1.45;
      part(g, new THREE.CylinderGeometry(0.12, 0.12, 0.3, 14), new THREE.MeshStandardMaterial({ color: "#ffffff", roughness: 0.1, transparent: true, opacity: 0.4 }), [x, 1.04, z], 0.006);
      part(g, new THREE.CylinderGeometry(0.1, 0.1, 0.22, 12), clay(c), [x, 1.0, z], 0);
    }
    // lamp over the table
    part(g, new THREE.CylinderGeometry(0.01, 0.01, 0.6, 6), clay("#2a2422"), [0.1, 2.9, -1.5], 0);
    part(g, new THREE.ConeGeometry(0.26, 0.2, 18, 1, true), clay("#2f7d6d"), [0.1, 2.55, -1.5], 0.008);
    const glow = new THREE.MeshStandardMaterial({ color: "#fff3c8", emissive: "#ffd27a", emissiveIntensity: 0.2 });
    this.lampGlow.push(glow);
    const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 10), glow); bulb.position.set(0.1, 2.45, -1.5); bulb.userData.dynamic = true; g.add(bulb);
    const lp = new THREE.PointLight("#ffcf8a", 0, 7, 1.4); lp.position.set(0.1, 2.3, -1.4); lp.userData.base = 5; g.add(lp); this.lamps.push(lp);
    const lp2 = new THREE.PointLight("#ffe0b0", 0, 9, 1.2); lp2.position.set(0.5, 2.2, 1.2); lp2.userData.base = 1.5; g.add(lp2); this.lamps.push(lp2);
    // calendar
    part(g, rbox(0.5, 0.66, 0.03, 0.1), new THREE.MeshStandardMaterial({ map: signTex("2026", "#ffffff", "#c8302c", 256, 320), roughness: 0.7 }), [0.4, 2.1, -3.08], 0.006);
  }
}
