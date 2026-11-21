// Story engine for kampung-3d-short: everything is a pure function of time (seconds), so any frame renders alone.
import * as THREE from "three";
import { Expr, Pose } from "./cast3d";

export type V3 = [number, number, number];
export type CamKey = { t: number; pos: V3; look: V3; fov?: number };
export type Shot = { id: string; start: number; end: number; cams: CamKey[]; focus?: [number, number]; fade?: number; shake?: number; light?: "pagi" | "subuh" | "malam" };

/** One actor's timeline. Times in seconds. */
export type Track = {
  path?: { t: number; at: [number, number]; jump?: boolean }[]; // walk between points (auto walk cycle + facing); jump = appear there at t (shot cut)
  face?: { t: number; yaw: number }[]; // explicit facing when standing (radians, 0 = toward +z)
  lookAt?: { t: number; target: string | [number, number] | null }[]; // turn head toward an actor/point
  expr?: { t: number; e: Expr }[];
  pose?: { t: number; p: Pose }[];
  talk?: [number, number][]; // talking intervals
  hidden?: [number, number][]; // not in the scene during these intervals
  speed?: number; // walk cycle speed factor
};

export const ease = (x: number) => (x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x));
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
const angLerp = (a: number, b: number, k: number) => { let d = ((b - a + Math.PI) % (Math.PI * 2)) - Math.PI; if (d < -Math.PI) d += Math.PI * 2; return a + d * k; };

function stepKey<T extends { t: number }>(keys: T[] | undefined, t: number): { cur?: T; prev?: T } {
  if (!keys?.length) return {};
  let cur: T | undefined, prev: T | undefined;
  for (const k of keys) { if (k.t <= t) { prev = cur; cur = k; } }
  return { cur: cur ?? keys[0], prev };
}

export type ActorState = { x: number; z: number; yaw: number; walk: number; walkAmp: number; expr: Expr; pose: Pose; talk: number; blink: boolean; visible: boolean; headYaw: number };

export function sampleTrack(tr: Track, t: number, seed: number, resolve: (id: string, t: number) => [number, number] | null): ActorState {
  // position along path
  let x = 0, z = 0, moving = false, dir = 0, dist = 0;
  const P = tr.path ?? [{ t: 0, at: [0, 0] as [number, number] }];
  if (t <= P[0].t) { [x, z] = P[0].at; }
  else if (t >= P[P.length - 1].t) { [x, z] = P[P.length - 1].at; }
  else for (let i = 0; i < P.length - 1; i++) {
    const a = P[i], b = P[i + 1];
    if (t >= a.t && t < b.t) {
      if (b.jump) { [x, z] = a.at; break; }
      const k = (t - a.t) / (b.t - a.t);
      const dx = b.at[0] - a.at[0], dz = b.at[1] - a.at[1], len = Math.hypot(dx, dz);
      // constant speed with short accel/decel
      const kk = len > 0.01 ? Math.min(1, Math.max(0, (k - 0.08) / 0.84)) * 0.9 + ease(k) * 0.1 : 0;
      x = a.at[0] + dx * kk; z = a.at[1] + dz * kk;
      if (len > 0.05) { moving = true; dir = Math.atan2(dx, dz); dist = len * kk; }
      break;
    }
  }
  // distance walked so far (for a continuous walk phase)
  let walked = dist;
  for (let i = 0; i < P.length - 1 && P[i + 1].t <= t; i++) if (!P[i + 1].jump) walked += Math.hypot(P[i + 1].at[0] - P[i].at[0], P[i + 1].at[1] - P[i].at[1]);
  const fk = stepKey(tr.face, t);
  let yaw = fk.cur ? fk.cur.yaw : 0;
  if (fk.cur && fk.prev) yaw = angLerp(fk.prev.yaw, fk.cur.yaw, ease((t - fk.cur.t) / 0.35));
  if (moving) yaw = dir;
  // head turn toward a target
  let headYaw = 0;
  const lk = stepKey(tr.lookAt, t).cur;
  if (lk?.target) {
    const p = typeof lk.target === "string" ? resolve(lk.target, t) : lk.target;
    if (p) { const want = Math.atan2(p[0] - x, p[1] - z); headYaw = Math.max(-0.9, Math.min(0.9, angLerp(yaw, want, 1) - yaw)); headYaw *= ease((t - lk.t) / 0.3); }
  }
  const ek = stepKey(tr.expr, t).cur;
  const pk = stepKey(tr.pose, t);
  let pose: Pose = pk.cur?.p ?? {};
  if (pk.cur && pk.prev) {
    const k = ease((t - pk.cur.t) / 0.3);
    const a = pk.prev.p as Record<string, number>, b = pk.cur.p as Record<string, number>;
    const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
    const out: Record<string, number> = {};
    keys.forEach((key) => { if (key !== "look") out[key] = lerp(a[key] ?? 0, b[key] ?? 0, k); });
    pose = out as Pose;
  }
  const talking = (tr.talk ?? []).some(([a, b]) => t >= a && t < b);
  const talk = talking ? Math.abs(Math.sin(t * 13 + seed)) * (0.6 + 0.4 * Math.abs(Math.sin(t * 5.3 + seed * 2))) : 0;
  const bp = (t + seed * 1.37) % 3.6;
  const visible = !(tr.hidden ?? []).some(([a, b]) => t >= a && t < b);
  return { x, z, yaw, walk: walked * 4.2 * (tr.speed ?? 1), walkAmp: moving ? 0.55 : 0, expr: ek?.e ?? "netral", pose, talk, blink: bp < 0.12, visible, headYaw };
}

export function cameraAt(shot: Shot, t: number, cam: THREE.PerspectiveCamera) {
  const ks = shot.cams;
  let a = ks[0], b = ks[0], k = 0;
  for (let i = 0; i < ks.length - 1; i++) if (t >= ks[i].t) { a = ks[i]; b = ks[i + 1]; k = ease((t - a.t) / Math.max(0.001, b.t - a.t)); }
  if (t >= ks[ks.length - 1].t) { a = b = ks[ks.length - 1]; k = 0; }
  const p = a.pos.map((v, i) => lerp(v, b.pos[i], k)), l = a.look.map((v, i) => lerp(v, b.look[i], k));
  const s = shot.shake ?? 0;
  cam.position.set(p[0] + Math.sin(t * 1.3) * 0.02 + Math.sin(t * 23) * s, p[1] + Math.sin(t * 1.7) * 0.015 + Math.cos(t * 19) * s, p[2]);
  cam.lookAt(l[0], l[1], l[2]);
  cam.fov = lerp(a.fov ?? 32, b.fov ?? 32, k);
  cam.updateProjectionMatrix();
}

export type Word = { w: string; s: number; e: number };
/** the caption word on screen at time t: hold each word until the next starts (or 0.5 s after it ends) */
export function captionAt(words: Word[], t: number): { w: string; age: number } | null {
  for (let i = words.length - 1; i >= 0; i--) {
    const wd = words[i];
    if (t >= wd.s) {
      const until = i + 1 < words.length ? Math.min(words[i + 1].s, wd.e + 0.5) : wd.e + 0.5;
      return t < until ? { w: wd.w, age: t - wd.s } : null;
    }
  }
  return null;
}
