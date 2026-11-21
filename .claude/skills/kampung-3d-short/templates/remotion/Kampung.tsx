// kampung-3d-short renderer: one story = shots (camera keys) + actor tracks + caption words, all in seconds.
// Look: soft warm daylight, NeutralToneMapping, PCF soft shadows, MSAA; one-word captions; crossfades between shots.
import React, { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import { AbsoluteFill, continueRender, delayRender, getInputProps, useCurrentFrame, useVideoConfig } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import nunito900 from "@fontsource/nunito/files/nunito-latin-900-normal.woff2";
import nunito800 from "@fontsource/nunito/files/nunito-latin-800-normal.woff2";
import { Warga, Kucing } from "./cast3d";
import { ROSTER } from "./roster";
import { KampungSet, FONT } from "./set";
import { Shot, Track, Word, sampleTrack, cameraAt, captionAt } from "./engine";

export type StoryDef = {
  total: number; // frames
  shots: Shot[];
  tracks: Record<string, Track>; // roster ids + "belang" for the cat
  words: Word[];
  extra?: (set: KampungSet, scene: THREE.Scene, cast: Record<string, Warga>) => (t: number) => void; // per-story props
};

const prop = () => getInputProps() as { dpr?: number; aa?: boolean; shadow?: "basic" | "pcf" | "soft" | "off"; smap?: number };
const dpr = () => prop().dpr;

const useFonts = () => {
  const [ok, setOk] = useState(false);
  const [h] = useState(() => delayRender("fonts"));
  useEffect(() => {
    Promise.all([new FontFace(FONT, `url(${nunito900})`, { weight: "900" }).load(), new FontFace(FONT, `url(${nunito800})`, { weight: "800" }).load()])
      .then((fs) => { fs.forEach((f) => document.fonts.add(f)); setOk(true); continueRender(h); });
  }, [h]);
  return ok;
};

const Inner: React.FC<{ story: StoryDef; shot: Shot }> = ({ story, shot }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const { camera, scene, gl } = useThree();
  gl.toneMapping = THREE.NeutralToneMapping;
  gl.toneMappingExposure = 1.05;
  const sh = prop().shadow ?? "pcf";
  gl.shadowMap.enabled = sh !== "off";
  gl.shadowMap.type = sh === "basic" ? THREE.BasicShadowMap : sh === "soft" ? THREE.PCFSoftShadowMap : THREE.PCFShadowMap;
  const w = useMemo(() => {
    const set = new KampungSet(scene);
    if (prop().smap) set.sun.shadow.mapSize.set(prop().smap!, prop().smap!);
    const cast: Record<string, Warga> = {};
    for (const s of ROSTER) if (story.tracks[s.id]) { cast[s.id] = new Warga(s); scene.add(cast[s.id].group); }
    const cat = story.tracks.belang ? new Kucing() : null;
    if (cat) scene.add(cat.group);
    const extra = story.extra?.(set, scene, cast);
    return { set, cast, cat, extra };
  }, [scene, story]);

  const states: Record<string, ReturnType<typeof sampleTrack>> = {};
  const ids = Object.keys(story.tracks);
  const resolve = (id: string, tt: number): [number, number] | null => {
    const tr = story.tracks[id]; if (!tr) return null;
    const s = sampleTrack(tr, tt, 0, () => null); return [s.x, s.z];
  };
  ids.forEach((id, i) => { states[id] = sampleTrack(story.tracks[id], t, i * 1.7 + 0.3, resolve); });
  for (const [id, wg] of Object.entries(w.cast)) {
    const s = states[id];
    wg.group.visible = s.visible;
    wg.group.position.set(s.x, 0, s.z);
    wg.group.rotation.y = s.yaw;
    wg.pose({ ...s.pose, walk: s.walk, walkAmp: s.walkAmp, headYaw: (s.pose.headYaw ?? 0) + s.headYaw });
    wg.setExpr(s.expr, { blink: s.blink, talk: s.talk, look: s.pose.look });
  }
  if (w.cat) {
    const s = states.belang;
    w.cat.group.visible = s.visible; w.cat.group.position.set(s.x, s.walkAmp ? Math.abs(Math.sin(s.walk * 1.5)) * 0.03 : 0, s.z); w.cat.group.rotation.y = s.yaw; w.cat.pose(t);
  }
  w.set.tick(t);
  w.extra?.(t);
  w.set.setLight(shot.light ?? "pagi");
  const fc = shot.focus ?? [0, 0];
  w.set.setFocus(fc[0], fc[1]);
  cameraAt(shot, t, camera as THREE.PerspectiveCamera);
  return null;
};

const ShotView: React.FC<{ story: StoryDef; shot: Shot; alpha: number }> = ({ story, shot, alpha }) => {
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill style={{ opacity: alpha }}>
      <ThreeCanvas width={width} height={height} shadows gl={{ antialias: prop().aa ?? false, powerPreference: "high-performance" }} {...(dpr() ? { dpr: dpr() } : {})}>
        <Inner story={story} shot={shot} />
      </ThreeCanvas>
    </AbsoluteFill>
  );
};

const Caption: React.FC<{ words: Word[]; t: number }> = ({ words, t }) => {
  const c = captionAt(words, t);
  const { width } = useVideoConfig();
  if (!c) return null;
  const word = c.w.toLowerCase().replace(/[.,!?;:"“”()]/g, "");
  const pop = 1 + 0.14 * Math.max(0, 1 - c.age / 0.12);
  const px = width / 1080;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center" }}>
      <div style={{
        position: "absolute", top: `${63}%`, transform: `translateY(-50%) scale(${pop})`,
        fontFamily: FONT, fontWeight: 900, fontSize: 74 * px, color: "#ffffff", letterSpacing: 0.5 * px,
        WebkitTextStroke: `${9 * px}px #2b1a10`, paintOrder: "stroke fill",
        textShadow: `0 ${4 * px}px ${10 * px}px rgba(0,0,0,0.35)`,
      }}>{word}</div>
    </AbsoluteFill>
  );
};

export const makeShort = (story: StoryDef): React.FC => () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ok = useFonts();
  const t = f / fps;
  if (!ok) return null;
  const i = Math.max(0, story.shots.findIndex((s) => t >= s.start && t < s.end));
  const cur = story.shots[i], prev = story.shots[i - 1];
  const fade = cur.fade ?? 0.33;
  const over = prev && t < cur.start + fade ? 1 - (t - cur.start) / fade : 0;
  return (
    <AbsoluteFill style={{ background: "#f3e2c4" }}>
      <ShotView key="base" story={story} shot={cur} alpha={1} />
      {over > 0 ? <ShotView key="over" story={story} shot={prev} alpha={over} /> : null}
      <Caption words={story.words} t={t} />
    </AbsoluteFill>
  );
};
