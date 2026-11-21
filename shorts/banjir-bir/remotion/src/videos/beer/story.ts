// "Banjir Bir London" (London Beer Flood, 1814): timeline of the short, timed to the VO word timings
// (shorts/banjir-bir/voice/words.json). Shots, story physics (hoop slip, vat bursts, domino, wall breach, wave),
// camera keys per shot and the lens (DOF) table. Same camera grammar as the bridge short: cuts on big jumps,
// smootherstep glides, every hold creeps in, flip kicks on impacts.
export const FPS = 30;
export const TOTAL = 1845;
export const D0 = 0; // ground height (build.ts houses sit on D0)
export type V3 = [number, number, number];

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const easeOut = (u: number) => 1 - (1 - clamp01(u)) ** 4;
export const lin = (pts: [number, number][], x: number) => {
  if (x <= pts[0][0]) return pts[0][1];
  for (let i = 1; i < pts.length; i++) if (x <= pts[i][0]) {
    const [x0, y0] = pts[i - 1], [x1, y1] = pts[i];
    return y0 + ((y1 - y0) * (x - x0)) / (x1 - x0);
  }
  return pts[pts.length - 1][1];
};

// ---------------- places ----------------
/** the brewery hall: x -16..16, z -28..0 (back wall to the street at z 0..0.6), walls 10 m */
export const HALL = { x0: -16, x1: 16, z0: -28, z1: 0, h: 10, wall: 0.6 };
/** the street behind the brewery runs along +z, |x| < STREET */
export const STREET = 5;
export type Vat = { x: number; z: number; r: number; h: number; hoops: number[] };
export const VATS: Vat[] = [
  { x: -6, z: -13, r: 3.4, h: 7.0, hoops: [0.55, 1.55, 2.55, 3.6, 4.6, 5.6, 6.6] },
  { x: 5, z: -17.5, r: 3.0, h: 6.4, hoops: [0.5, 1.5, 2.5, 3.5, 4.5, 5.5] },
  { x: 11.8, z: -6.5, r: 2.3, h: 5.4, hoops: [0.5, 1.5, 2.5, 3.5, 4.6] },
];
export const SLIP_HOOP = 3; // V1 hoop at 3.6 m
export const COURT: V3 = [60, 0, 0];
export const DEMO: V3 = [-60, 0, 0]; // explanation vat
export const DEMO_VAT: Vat = { x: -60, z: 0, r: 1.6, h: 4.6, hoops: [0.4, 1.2, 2.0, 2.8, 3.6, 4.3] };
export const BUFFET: V3 = [-60, 0, 40];
export const TANK: V3 = [-9.5, 0, -22]; // the iron tank that replaced the wooden vats (aftermath)

// ---------------- story events (story time tau, seconds) ----------------
export const T_SLIP = 532 / FPS, T_CLANG = 543 / FPS;
export const T_B = [711 / FPS, 800 / FPS, 842 / FPS]; // vat bursts
export const T_HIT = [760 / FPS, 835 / FPS];            // flying staves hit V2 / V3
export const T_W = 912 / FPS;                            // the back wall gives way
export const WAVE_V = 7;                                 // m/s down the street
export const AFTER = 200;                                // tau of the aftermath shots (everything drained)

/** beer level inside the hall */
export const hallLevel = (tau: number) => {
  if (tau < T_B[0]) return -1;
  const fill = lin([[T_B[0], 0.0], [T_B[0] + 0.6, 0.3], [T_B[1], 0.7], [T_B[2], 1.05], [T_W, 1.45], [T_W + 3, 0.8], [T_W + 12, 0.4], [T_W + 30, 0.2]], tau);
  return tau > T_W + 40 ? -1 : fill;
};
export const waveFront = (tau: number) => 0.6 + WAVE_V * (tau - T_W);
/** flood surface height at (x, z) at story time tau; < 0 = no beer there */
export const floodH = (x: number, z: number, tau: number): number => {
  if (tau < T_B[0] || tau > T_W + 40) return -1;
  if (z < HALL.z1) {
    if (x < HALL.x0 || x > HALL.x1 || z < HALL.z0) return -1;
    let h = hallLevel(tau);
    VATS.forEach((v, i) => {
      const dt = tau - T_B[i];
      if (dt < 0) return;
      const d = Math.hypot(x - v.x, z - v.z);
      const A = (i === 0 ? 2.6 : 2.0) * Math.min(1, dt / 0.22) * Math.exp(-dt / 1.1);
      h += A * Math.exp(-((d / (v.r * 1.15)) ** 2));
      h += 1.1 * Math.exp(-(((d - v.r - 8 * dt) / 1.3) ** 2)) * Math.exp(-dt / 1.4);
    });
    return h;
  }
  if (tau < T_W || Math.abs(x) > STREET + 0.15) return -1;
  const dt = tau - T_W, R = waveFront(tau), u = R - z - 0.035 * x * x;
  if (u < 0) return -1;
  const crest = 5.4 * (0.8 + 0.2 * Math.exp(-dt / 4)), P = 1.7 * Math.exp(-dt / 18) + 0.35;
  const fade = 1 - smooth((dt - 28) / 10);
  const h = P * (1 - Math.exp(-u / 1.6)) + crest * (1 - Math.exp(-u / 0.75)) * Math.exp(-u / 4.2);
  // the gush right at the breach in the first second
  const gush = 2.6 * Math.exp(-dt / 0.7) * Math.exp(-(((z - 1.5) / 3) ** 2));
  const side = smooth((STREET + 0.15 - Math.abs(x)) / 0.9);
  return (h + gush) * fade * (0.35 + 0.65 * side);
};
/** foam: 0..1 near the wave front / ring crests */
export const foamAt = (x: number, z: number, tau: number) => {
  if (z >= HALL.z1 && tau >= T_W) {
    const u = waveFront(tau) - z - 0.035 * x * x;
    return u < 0 ? 0 : 0.9 * Math.exp(-(((u - 1.7) / 0.55) ** 2));
  }
  let f = 0;
  VATS.forEach((v, i) => {
    const dt = tau - T_B[i];
    if (dt < 0 || dt > 4) return;
    const d = Math.hypot(x - v.x, z - v.z);
    f = Math.max(f, Math.exp(-(((d - v.r - 8 * dt) / 0.6) ** 2)) * Math.exp(-dt / 1.2), d < v.r * 0.7 ? 0.7 * Math.exp(-dt / 0.6) : 0);
  });
  return f;
};

// ---------------- shots ----------------
export type Light = "day" | "golden";
export type Set = "street" | "hall" | "court" | "demo" | "buffet";
export type ShotDef = { id: number; a: number; b: number; light: Light; set: Set; tau: (t: number) => number; roof?: boolean; sunAz?: number; sunEl?: number };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 130, light: "day", set: "street", tau: (t) => 32.2 + t, roof: true },
  { id: 2, a: 130, b: 226, light: "day", set: "street", tau: (t) => t - 20, roof: true, sunAz: 120 },
  { id: 3, a: 226, b: 362, light: "day", set: "hall", tau: (t) => t },
  { id: 4, a: 362, b: 455, light: "day", set: "hall", tau: (t) => t },
  { id: 5, a: 455, b: 560, light: "day", set: "hall", tau: (t) => t },
  { id: 6, a: 560, b: 672, light: "day", set: "hall", tau: (t) => t },
  { id: 7, a: 672, b: 736, light: "day", set: "hall", tau: (t) => t },
  { id: 8, a: 736, b: 857, light: "day", set: "hall", tau: (t) => t },
  { id: 9, a: 857, b: 1068, light: "day", set: "street", tau: (t) => t, roof: true },
  { id: 10, a: 1068, b: 1255, light: "day", set: "court", tau: (t) => AFTER },
  { id: 11, a: 1255, b: 1465, light: "golden", set: "demo", tau: (t) => AFTER, sunAz: 70, sunEl: 16 },
  { id: 12, a: 1465, b: 1600, light: "golden", set: "buffet", tau: (t) => AFTER, sunAz: 70, sunEl: 16 },
  { id: 13, a: 1600, b: 1682, light: "day", set: "hall", tau: (t) => AFTER },
  { id: 14, a: 1682, b: TOTAL, light: "day", set: "street", tau: (t) => AFTER, roof: true },
];
export const XFADE: Record<number, number> = { 2: 0, 10: 8, 11: 10, 13: 8, 14: 8 };
export const FLASH_AT = 128;
export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number): { id: number; alpha: number }[] => {
  for (const s of SHOTS) {
    const x = XFADE[s.id];
    if (x && f >= s.a - x / 2 && f < s.a + x / 2) return [{ id: s.id - 1, alpha: 1 }, { id: s.id, alpha: (f - (s.a - x / 2) + 1) / (x + 1) }];
  }
  return [{ id: shotAt(f).id, alpha: 1 }];
};

// ---------------- camera ----------------
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Shot = Partial<Cam> & { pos: V3; look: V3 };
type Key = { f: number; dur?: number; cut?: boolean; s: (f: number) => Shot };
export const glide = (u: number) => { const x = clamp01(u); return x * x * x * (x * (6 * x - 15) + 10); };
const mix = (a: Cam, b: Cam, k: number): Cam => ({
  pos: a.pos.map((v, i) => v + (b.pos[i] - v) * k) as V3, look: a.look.map((v, i) => v + (b.look[i] - v) * k) as V3,
  fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k,
});
const full = (c: Shot): Cam => ({ fov: 40, roll: 0, ...c });
const run = (keys: Key[], f: number) => {
  let cur = full(keys[0].s(f));
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i];
    if (f < k.f) break;
    cur = k.cut ? full(k.s(f)) : mix(cur, full(k.s(f)), glide((f - k.f) / (k.dur ?? 24)));
  }
  return cur;
};
const pushK = (f: number, f0: number, rate: number, punch = 0, n = 35) => {
  const x = Math.max(0, f - f0);
  let s = rate * x;
  if (punch > rate) for (let i = 0; i < Math.min(x, n); i++) s += (punch - rate) * Math.max(0, Math.min(1, (i + 0.5) / 8, (n - i - 0.5) / 8));
  return Math.exp(-s);
};
const dolly = (pos: V3, look: V3, k: number, rest: Partial<Cam> = {}): Shot =>
  ({ pos: [look[0] + (pos[0] - look[0]) * k, look[1] + (pos[1] - look[1]) * k, look[2] + (pos[2] - look[2]) * k], look, ...rest });
const zoom = (pos: V3, look: V3, fov: number, k: number, rest: Partial<Cam> = {}): Shot =>
  ({ pos, look, fov: (360 / Math.PI) * Math.atan(Math.tan((fov * Math.PI) / 360) * k), ...rest });
const rolled = (s: (f: number) => Shot, roll: number) => (f: number): Shot => ({ ...s(f), roll });

const [V1, V2, V3_] = VATS;
const CAMS: Record<number, Key[]> = {
  // 1 hook (flash-forward): low in the street, the wave rolls at the lens; "bir." = deadpan floater CU
  1: [
    { f: 0, s: (f) => dolly([1.6, 1.3, 52], [0, 2.6, 30], pushK(f, 0, 0.002), { fov: 48, roll: -0.03 }) },
    { f: 52, dur: 30, s: (f) => dolly([1.2, 1.1, 50], [0, 2.9, 30], pushK(f, 52, 0.003), { fov: 46, roll: 0.035 }) },
    { f: 100, cut: true, s: (f) => dolly([0.9, 2.55, 31.6], [0, 2.05, 28], pushK(f, 100, 0.004), { fov: 34 }) },
  ],
  // 2 town aerial, punch on "kebanggaan"
  2: [
    { f: 130, s: (f) => zoom([30, 30, 66], [0, 6, -12], 40, pushK(f, 130, 0.002)) },
    { f: 205, dur: 20, s: (f) => zoom([30, 30, 66], [0, 7, -14], 40, pushK(f, 130, 0.002, 0.006, 30) * 0.8) },
  ],
  // 3 inside: up the giant vat, then down into it ("isinya ... bir hitam")
  3: [
    { f: 226, s: (f) => dolly([-1.2, 0.6, -3.6], [V1.x, 5.0, V1.z], pushK(f, 226, 0.0025), { fov: 52, roll: 0.04 }) },
    { f: 283, cut: true, s: (f) => dolly([-0.6, 11.2, -4.2], [V1.x + 1.0, 6.2, V1.z + 1.4], pushK(f, 283, 0.003), { fov: 46 }) },
    { f: 335, dur: 24, s: (f) => dolly([-1.2, 10.8, -5.2], [V1.x + 0.8, 6.4, V1.z + 0.9], pushK(f, 283, 0.003, 0.006, 30), { fov: 44, roll: -0.03 }) },
  ],
  // 4 the hoops: glide up the staves
  4: [
    { f: 362, s: (f) => dolly([-4.2, 1.6, -5.2], [V1.x + 0.3, 1.9, V1.z + V1.r], pushK(f, 362, 0.002), { fov: 40 }) },
    { f: 380, dur: 40, s: (f) => dolly([-4.2, 4.6, -5.4], [V1.x + 0.3, 5.0, V1.z + V1.r], pushK(f, 380, 0.002), { fov: 40 }) },
    { f: 426, dur: 18, s: (f) => dolly([-4.6, 4.4, -6.0], [V1.x + 0.3, 4.4, V1.z + V1.r], pushK(f, 426, 0.002, 0.006, 25), { fov: 38, roll: 0.04 }) },
  ],
  // 5 the slipping hoop: MS of the lower half, worker at the base
  5: [
    { f: 455, s: (f) => dolly([-3.4, 2.4, -4.0], [V1.x + 0.6, 2.4, V1.z + V1.r], pushK(f, 455, 0.002), { fov: 46 }) },
    { f: 528, dur: 14, s: (f) => dolly([-3.6, 1.6, -4.4], [V1.x + 0.6, 1.4, V1.z + V1.r], pushK(f, 528, 0.002), { fov: 46, roll: -0.04 }) },
  ],
  // 6 the clerk reports; the boss: "tenang"
  6: [
    { f: 560, s: (f) => dolly([8.2, 1.7, -19.6], [10.4, 1.45, -24.8], pushK(f, 560, 0.0025), { fov: 42 }) },
    { f: 605, cut: true, s: (f) => dolly([11.6, 1.75, -21.6], [11.2, 1.7, -24.8], pushK(f, 605, 0.002), { fov: 38 }) },
    { f: 628, dur: 22, s: rolled((f) => dolly([11.6, 1.75, -21.6], [11.2, 1.7, -24.8], pushK(f, 605, 0.002, 0.006, 30), { fov: 38 }), 0.05) },
  ],
  // 7 one hour later: the vat groans, then bursts
  7: [
    { f: 672, s: (f) => dolly([1.5, 3.0, -1.6], [V1.x, 3.6, V1.z], pushK(f, 672, 0.003), { fov: 48 }) },
    { f: 700, dur: 12, s: (f) => dolly([1.5, 3.0, -1.6], [V1.x, 3.6, V1.z], pushK(f, 672, 0.003, 0.008, 12) * 0.95, { fov: 48, roll: 0.03 }) },
  ],
  // 8 domino: V1 wreck + flying stave -> V2 ("menghantam"), V2 bursts ("pecah"), V3 ("lagi")
  8: [
    { f: 736, s: (f) => dolly([-12.5, 4.2, -5.2], [V2.x - 1, 2.8, V2.z], pushK(f, 736, 0.002), { fov: 50 }) },
    { f: 786, cut: true, s: (f) => dolly([-0.5, 3.8, -8.6], [V2.x, 2.8, V2.z], pushK(f, 786, 0.003), { fov: 50, roll: -0.04 }) },
    { f: 815, cut: true, s: (f) => dolly([3.0, 4.2, -1.6], [V3_.x, 2.4, V3_.z], pushK(f, 815, 0.003), { fov: 50, roll: 0.04 }) },
  ],
  // 9 street: the wall gives; the wave; aerial sweep
  9: [
    { f: 857, s: (f) => dolly([1.8, 2.4, 25], [0, 5.2, 0], pushK(f, 857, 0.002), { fov: 48 }) },
    { f: 905, dur: 10, s: (f) => dolly([1.8, 2.4, 25], [0, 5.2, 0], pushK(f, 857, 0.002, 0.008, 12) * 0.96, { fov: 48, roll: -0.03 }) },
    { f: 950, cut: true, s: (f) => dolly([0.9, 0.8, 34], [0, 3.8, 18], pushK(f, 950, 0.002), { fov: 52, roll: 0.03 }) },
    { f: 984, dur: 22, s: (f) => dolly([0.9, 0.7, 34], [0, 4.4, 18], pushK(f, 950, 0.002, 0.006, 25), { fov: 52, roll: -0.04 }) },
    { f: 1010, cut: true, s: (f) => dolly([1.5, 26, 58], [0, 0, 24], pushK(f, 1010, 0.002), { fov: 44 }) },
  ],
  // 10 the court: gavel, then "salah Tuhan" -> up to the sky
  10: [
    { f: 1064, s: (f) => dolly([COURT[0] + 0.8, 2.1, COURT[2] - 6.0], [COURT[0], 1.95, COURT[2] + 1.8], pushK(f, 1064, 0.002), { fov: 38 }) },
    { f: 1160, cut: true, s: (f) => dolly([COURT[0] - 0.4, 2.15, COURT[2] - 2.6], [COURT[0], 2.2, COURT[2] + 1.8], pushK(f, 1160, 0.002), { fov: 38 }) },
    { f: 1226, dur: 28, s: (f) => ({ pos: [COURT[0] - 0.4, 2.15, COURT[2] - 2.9], look: [COURT[0] + 0.5, 9, COURT[2] + 4], fov: 44, roll: 0.02 }) },
  ],
  // 11 golden: the pressure arrows on the demo vat
  11: [
    { f: 1250, s: (f) => dolly([DEMO[0], 2.4, -16], [DEMO[0], 2.3, 0], pushK(f, 1250, 0.0018), { fov: 44 }) },
    { f: 1397, dur: 30, s: (f) => dolly([DEMO[0] + 0.3, 1.5, -13.5], [DEMO[0], 1.4, 0], pushK(f, 1397, 0.002), { fov: 44, roll: 0.03 }) },
  ],
  // 12 golden: the buffet belt
  12: [
    { f: 1465, s: (f) => dolly([BUFFET[0] - 0.4, 1.25, BUFFET[2] - 5.4], [BUFFET[0] - 0.5, 1.05, BUFFET[2]], pushK(f, 1465, 0.0025), { fov: 38 }) },
    { f: 1538, cut: true, s: (f) => dolly([BUFFET[0] + 0.1, 1.1, BUFFET[2] - 3.4], [BUFFET[0] + 0.15, 1.0, BUFFET[2]], pushK(f, 1538, 0.002), { fov: 38, roll: -0.04 }) },
    { f: 1572, dur: 20, s: rolled((f) => dolly([BUFFET[0] + 0.1, 1.1, BUFFET[2] - 3.4], [BUFFET[0] + 0.15, 1.0, BUFFET[2]], pushK(f, 1538, 0.002), { fov: 38 }), 0.04) },
  ],
  // 13 aftermath: the new iron tank
  13: [{ f: 1596, s: (f) => dolly([0.5, 2.4, -3.0], [TANK[0], 3.0, TANK[2]], pushK(f, 1596, 0.0025), { fov: 46 }) }],
  // 14 the boss and the tax refund; crane out
  14: [
    { f: 1678, s: (f) => dolly([1.5, 1.75, 16.6], [0.8, 1.65, 12], pushK(f, 1678, 0.002), { fov: 36 }) },
    { f: 1736, cut: true, s: (f) => dolly([-0.2, 1.6, 18.2], [0, 1.45, 12], pushK(f, 1736, 0.002), { fov: 40 }) },
    { f: 1774, dur: 14, s: (f) => dolly([-0.2, 1.6, 18.2], [0, 1.45, 12], pushK(f, 1736, 0.002, 0.007, 20), { fov: 40, roll: 0.03 }) },
    { f: 1800, dur: 45, s: (f) => ({ pos: [5, 13, 28], look: [0, 1.2, 9], fov: 44, roll: 0 }) },
  ],
};
// impact kicks: [tau, gain]
const KICKS: [number, number][] = [[T_CLANG, 0.8], [T_B[0], 1.8], [T_HIT[0], 0.7], [T_B[1], 1.3], [T_HIT[1], 0.5], [T_B[2], 1.2], [T_W, 1.8],
  [1119 / FPS, 0.5], [1133 / FPS, 0.6], [1542 / FPS, 0.6], [1777 / FPS, 0.4]];
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) {
    const n = Math.floor((t - t0) * FPS + 1e-6);
    if (n >= 0 && n < 7) a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5;
  }
  return a;
};
export const camAt = (id: number, f: number): Cam => {
  const c = run(CAMS[id], f), a = kickAt(f / FPS);
  if (!a) return c;
  const d: V3 = [c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]];
  const L = Math.hypot(...d), h = Math.hypot(d[0], d[2]) || 1;
  const m = (3 / 640) * Math.tan((c.fov * Math.PI) / 360) * L * a;
  return { ...c, look: [c.look[0] - (d[2] / h) * m, c.look[1] + 0.6 * m, c.look[2] + (d[0] / h) * m], roll: c.roll + a * 0.004 };
};

// ---------------- lens ----------------
export type Dof = { f: number; dur?: number; cInf: number; focus?: (f: number) => V3 };
export const DOF: Dof[] = [
  { f: 0, cInf: 0 },
  { f: 100, cInf: 14 },                                             // floater CU
  { f: 130, cInf: 0 },                                              // aerial
  { f: 226, cInf: 6 },                                              // up the vat
  { f: 283, cInf: 8 },                                              // into the vat
  { f: 362, cInf: 12 },                                             // hoops CU
  { f: 455, cInf: 10 },                                             // slip
  { f: 560, cInf: 10, focus: () => [10.4, 1.6, -24.6] },           // clerk + boss
  { f: 605, cInf: 13 },                                             // boss CU
  { f: 672, cInf: 0 },                                              // bursts, domino, wall, wave
  { f: 1068, cInf: 11, focus: () => [COURT[0], 2.1, COURT[2] + 1.8] },
  { f: 1226, dur: 28, cInf: 0 },
  { f: 1255, cInf: 5 },
  { f: 1465, cInf: 12, focus: () => [BUFFET[0] + 0.2, 1.2, BUFFET[2] - 0.1] },
  { f: 1600, cInf: 6 },
  { f: 1682, cInf: 13, focus: () => [0.8, 1.7, 12] },
  { f: 1736, cInf: 9, focus: () => [0, 1.6, 12.2] },
  { f: 1800, dur: 40, cInf: 0 },
];
export const dofAt = (f: number) => {
  let i = 0; while (i + 1 < DOF.length && f >= DOF[i + 1].f) i++;
  const d = DOF[i], p = DOF[Math.max(0, i - 1)];
  const k = d.dur ? Math.min(1, (f - d.f) / d.dur) : 1;
  return { cInf: p.cInf + (d.cInf - p.cInf) * k, focus: d.focus };
};
