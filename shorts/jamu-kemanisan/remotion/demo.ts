// Pipeline test (8 s): Bayu runs to the warung and asks Bu Lastri for candy.
import { StoryDef } from "./Kampung";
const H = Math.PI / 2;
export const DEMO: StoryDef = {
  total: 240,
  shots: [
    { id: "gang", start: 0, end: 3, focus: [0, 2], cams: [{ t: 0, pos: [1.0, 2.4, 10.5], look: [-0.6, 1.0, 1.5], fov: 40 }, { t: 3, pos: [0.6, 2.2, 8.4], look: [-0.9, 1.0, 1.5], fov: 40 }] },
    { id: "warung", start: 3, end: 5.6, focus: [-2, 1.5], cams: [{ t: 3, pos: [2.0, 1.9, 2.9], look: [-2.5, 1.45, 1.35], fov: 40 }, { t: 5.6, pos: [1.8, 1.85, 2.8], look: [-2.5, 1.5, 1.35], fov: 36 }] },
    { id: "bayu", start: 5.6, end: 8, focus: [-1.5, 1.5], cams: [{ t: 5.6, pos: [-2.0, 1.75, 4.7], look: [-0.7, 1.15, 1.6], fov: 40 }, { t: 8, pos: [-1.9, 1.7, 4.3], look: [-0.7, 1.15, 1.6], fov: 37 }] },
  ],
  tracks: {
    bayu: { path: [{ t: 0, at: [0.3, 5.8] }, { t: 2.6, at: [-0.7, 1.6] }], face: [{ t: 2.6, yaw: -H }], speed: 1.3,
      expr: [{ t: 0, e: "senyum" }, { t: 3.2, e: "senyum" }, { t: 6.4, e: "kaget" }, { t: 7.2, e: "bingung" }],
      pose: [{ t: 0, p: {} }, { t: 3.2, p: { armRf: 1.1, armR: 0.1 } }, { t: 5.2, p: {} }], talk: [[3.3, 4.4]] },
    bu_lastri: { path: [{ t: 0, at: [-2.6, 1.3] }], face: [{ t: 0, yaw: H }], lookAt: [{ t: 0, target: "bayu" }],
      expr: [{ t: 0, e: "senyum" }, { t: 4.6, e: "bingung" }], pose: [{ t: 0, p: {} }, { t: 4.6, p: { armLf: 0.9, armL: 0.2 } }], talk: [[4.6, 5.9]] },
    mbah_sarni: { path: [{ t: 0, at: [3.3, 0.8] }], face: [{ t: 0, yaw: -H }], lookAt: [{ t: 1.0, target: "bayu" }], expr: [{ t: 0, e: "senyum" }] },
    belang: { path: [{ t: 0, at: [1.6, 4] }, { t: 4, at: [-0.8, 0.2] }] },
  },
  words: [
    ["Bayu", 0.3, 0.6], ["lari", 0.65, 0.95], ["ke", 1.0, 1.1], ["warung", 1.15, 1.5], ["Bu", 1.55, 1.7], ["Lastri.", 1.75, 2.2],
    ["Bu,", 3.3, 3.5], ["beli", 3.6, 3.85], ["permen!", 3.9, 4.4], ["Lho,", 4.6, 4.9], ["uangnya", 5.0, 5.4], ["mana?", 5.45, 5.9],
  ].map(([w, s, e]) => ({ w: w as string, s: s as number, e: e as number })),
};
