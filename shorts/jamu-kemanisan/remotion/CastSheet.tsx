// Character-sheet stills for the kampung cast (not a video): frame = charIndex*20 + slot.
// slot 0 front, 1 three-quarter (waving), 2 back three-quarter, 10..18 face close-ups (one per expression).
// frame 200 = group lineup.
import React, { useMemo } from "react";
import * as THREE from "three";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { Warga, Kucing, EXPRS } from "./cast3d";
import { ROSTER } from "./roster";

export const SHEET_W = 1080, SHEET_H = 1350;

const groundTex = () => {
  const c = document.createElement("canvas"); c.width = c.height = 512;
  const g = c.getContext("2d")!;
  g.fillStyle = "#d9c7a6"; g.fillRect(0, 0, 512, 512);
  for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) {
    const o = (y % 2) * 32;
    g.fillStyle = `hsl(${32 + ((x * 7 + y * 13) % 6)}, 30%, ${70 + ((x * 5 + y * 3) % 5)}%)`;
    g.beginPath(); g.roundRect(x * 64 + o + 3, y * 64 + 3, 58, 58, 8); g.fill();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(12, 12); t.anisotropy = 8;
  return t;
};

const Inner: React.FC = () => {
  const f = useCurrentFrame();
  const { camera, scene, gl } = useThree();
  gl.toneMapping = THREE.NeutralToneMapping;
  gl.toneMappingExposure = 1.05;
  const set = useMemo(() => {
    scene.background = new THREE.Color("#f1e2c6");
    scene.fog = new THREE.Fog("#f1e2c6", 28, 60);
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ map: groundTex(), roughness: 0.9 }));
    ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
    scene.add(new THREE.HemisphereLight("#fff3dc", "#9c7b5a", 1.3));
    const sun = new THREE.DirectionalLight("#ffe0b0", 2.6);
    sun.position.set(4, 7, 6); sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02; sun.shadow.radius = 6;
    Object.assign(sun.shadow.camera, { left: -6, right: 6, top: 6, bottom: -6, near: 1, far: 30 });
    scene.add(sun);
    const fill = new THREE.DirectionalLight("#cfe0ff", 0.7); fill.position.set(-5, 3, 4); scene.add(fill);
    const rim = new THREE.DirectionalLight("#fff0d8", 1.2); rim.position.set(-2, 5, -6); scene.add(rim);
    const cast = ROSTER.map((s) => { const w = new Warga(s); scene.add(w.group); return w; });
    const cat = new Kucing(); scene.add(cat.group);
    return { cast, cat };
  }, [scene]);

  const cam = camera as THREE.PerspectiveCamera;
  cam.fov = 28; cam.near = 0.1; cam.far = 80;
  const all = [...set.cast.map((w) => w.group), set.cat.group];
  const ci = Math.floor(f / 20), slot = f % 20;

  if (f >= 200) {
    // lineup: back row adults & elders, front row kids + cat
    const order = ["kakek_wiryo", "mbah_sarni", "pak_sobri", "bayu", "bu_lastri", "laras", "mas_gilang"];
    const ex = { kakek_wiryo: "senyum", mbah_sarni: "senyum", pak_sobri: "tawa", bayu: "tawa", bu_lastri: "senyum", laras: "senyum", mas_gilang: "merem" } as const;
    set.cast.forEach((w) => {
      const i = order.indexOf(w.spec.id);
      w.group.visible = true; w.group.position.set((i - 3) * 1.02, 0, Math.abs(i - 3) * -0.12); w.group.rotation.y = -(i - 3) * 0.07;
      w.setExpr(ex[w.spec.id as keyof typeof ex]);
      w.pose(w.spec.id === "bayu" ? { armR: 2.0, armRf: 0.5 } : w.spec.id === "mas_gilang" ? { armL: 0.5, armLf: 0.6 } : {});
    });
    set.cat.group.visible = true; set.cat.group.position.set(-0.5, 0, 1.0); set.cat.group.rotation.y = 0.6; set.cat.pose(0.4);
    cam.fov = 30;
    cam.position.set(0, 2.6, 20); cam.lookAt(0, 0.95, 0);
  } else {
    all.forEach((g, i) => { g.visible = i === ci; g.position.set(0, 0, 0); g.rotation.set(0, 0, 0); });
    if (ci < set.cast.length) {
      const w = set.cast[ci];
      const H = w.height;
      if (slot < 10) {
        const yaw = slot === 0 ? 0 : slot === 1 ? 0.62 : 2.5;
        w.group.rotation.y = yaw;
        w.setExpr(slot === 1 ? "senyum" : "netral");
        w.pose(slot === 1 ? (w.spec.cane ? { armL: 2.0, armLf: 0.5, headTilt: -0.1 } : { armR: 2.0, armRf: 0.5, headTilt: 0.1 }) : {});
        const d = (H * 0.62) / Math.tan(THREE.MathUtils.degToRad(14));
        cam.position.set(0, H * 0.62, d); cam.lookAt(0, H * 0.5, 0);
      } else {
        const e = EXPRS[(slot - 10) % EXPRS.length];
        w.setExpr(e); w.pose(e === "tawa" ? { headTilt: 0.08 } : e === "sedih" || e === "nangis" ? { headNod: 0.12 } : e === "bingung" ? { headTilt: -0.12 } : {});
        w.group.rotation.y = 0.18;
        const hy = H - 0.42;
        cam.position.set(0.1, hy + 0.05, 3.5); cam.lookAt(0, hy - 0.02, 0);
      }
    } else {
      set.cat.group.rotation.y = slot === 0 ? 0.25 : 1.1; set.cat.pose(slot * 0.7);
      cam.position.set(0, 0.7, 3.4); cam.lookAt(0, 0.35, 0);
    }
  }
  cam.updateProjectionMatrix();
  return null;
};

export const CastSheet: React.FC = () => (
  <AbsoluteFill style={{ background: "#f1e2c6" }}>
    <ThreeCanvas width={SHEET_W} height={SHEET_H} shadows gl={{ antialias: true }}>
      <Inner />
    </ThreeCanvas>
  </AbsoluteFill>
);
