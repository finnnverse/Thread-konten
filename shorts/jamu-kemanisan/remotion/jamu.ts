// "Jamu yang Selalu Kemanisan" (Warga Kampung #1). VO 59.5 s, words from shorts/jamu-kemanisan/voice/words.json.
import * as THREE from "three";
import { StoryDef } from "./Kampung";
import { Shot, Track, Word, V3 } from "./engine";
import { Warga, clay, part } from "./cast3d";
import { DAPUR_X } from "./set";
import wordsJson from "./jamu_words.json";

const H = Math.PI / 2;
const DX = DAPUR_X;
// teras Mbah Sarni (see set.ts): amben at (2.28, 1.42), Mbah behind it at (2.8, 1.42) facing -x
const MBAH_TERAS: [number, number] = [2.82, 1.42];
const MBAH_DAPUR: [number, number] = [DX - 0.2, -2.35];
const LARAS_PINTU: [number, number] = [DX + 3.35, -0.55];
const LARAS_MEJA: [number, number] = [DX + 0.6, -2.35];

const at = (t: number, p: [number, number]) => ({ t, at: p });
/** jump instantly (shot cut) */
const jump = (t: number, p: [number, number]) => [{ t, at: p, jump: true }];

const words: Word[] = (wordsJson as { words: { word: string; start: number; end: number }[] }).words.map((w) => ({ w: w.word, s: w.start, e: w.end }));

const cam = (t: number, pos: V3, look: V3, fov = 38) => ({ t, pos, look, fov });

/** camera orbiting a target: yaw = direction from target to camera (0 = +z), dist in metres */
const orb = (t: number, tg: V3, yaw: number, dist: number, fov = 38, dy = 0.18): ReturnType<typeof cam> =>
  cam(t, [tg[0] + Math.sin(yaw) * dist, tg[1] + dy, tg[2] + Math.cos(yaw) * dist], tg, fov);

const SOBRI: [number, number] = [1.5, 1.45], LASTRI: [number, number] = [1.25, 2.35], GILANG: [number, number] = [0.45, 1.9],
  BAYU: [number, number] = [0.6, 2.95], LARAS_Q: [number, number] = [-0.2, 2.7];
const yawTo = (a: [number, number], b: [number, number]) => Math.atan2(b[0] - a[0], b[1] - a[1]);
const head = (p: [number, number], y = 1.5): V3 => [p[0], y, p[1]];

const shots: Shot[] = [
  // 1 "Sudah sebulan, jamu buatan Mbah Sarni rasanya aneh."
  { id: "botol", start: 0, end: 3.4, focus: [2, 1.2], cams: [orb(0, [2.38, 0.78, 1.4], -1.85, 1.35, 34, 0.25), orb(1.2, [2.38, 0.85, 1.4], -1.7, 1.6, 36, 0.3), orb(3.4, head(MBAH_TERAS, 1.4), -1.45, 3.9, 38)] },
  // 2 "Kemanisan. Kunyit asamnya seperti sirup,"
  { id: "gelas", start: 3.4, end: 6.0, focus: [2, 1.2], cams: [orb(3.4, [2.18, 0.68, 1.38], -1.75, 1.05, 34, 0.28), orb(6.0, [2.18, 0.68, 1.42], -1.6, 0.9, 32, 0.25)] },
  // 3 "beras kencurnya seperti permen."
  { id: "mbah_sajikan", start: 6.0, end: 8.6, focus: [2, 1.5], cams: [orb(6.0, head(MBAH_TERAS, 1.35), -1.15, 4.1), orb(8.6, head(MBAH_TERAS, 1.38), -1.2, 3.7)] },
  // 4 "Anehnya, warga Gang Mawar tetap antre setiap pagi."
  { id: "antre", start: 8.6, end: 12.3, focus: [1.2, 2.2], cams: [cam(8.6, [0.9, 2.7, -3.3], [1.4, 1.15, 2.0], 42), cam(12.3, [0.95, 2.5, -2.8], [1.4, 1.2, 2.0], 42)] },
  // 5 "Pak Sobri minum dua gelas."
  { id: "sobri", start: 12.3, end: 14.0, focus: [1.2, 1.5], cams: [orb(12.3, head(SOBRI), -1.75, 3.9), orb(14.0, head(SOBRI), -1.75, 3.5)] },
  // 6 "Bu Lastri bilang, 'Enak, Mbah, pas!'"
  { id: "lastri", start: 14.0, end: 17.15, focus: [1.5, 1.5], cams: [orb(14.0, head(LASTRI), 3.05, 3.9), orb(17.15, head(LASTRI), 3.05, 3.4, 36)] },
  // 7 "Bahkan Mas Gilang, yang tidak suka manis, ikut membeli."
  { id: "gilang", start: 17.15, end: 20.45, focus: [0.8, 2.5], cams: [orb(17.15, head(GILANG), -0.3, 3.9), orb(20.45, head(GILANG), -0.3, 3.4, 36)] },
  // 8 "Laras penasaran."
  { id: "laras", start: 20.45, end: 21.95, focus: [0.2, 3.2], cams: [orb(20.45, head(LARAS_Q), -0.5, 3.7), orb(21.95, head(LARAS_Q), -0.5, 3.3, 36)] },
  // 9 "Pagi itu, ia datang lebih awal"
  { id: "subuh", start: 21.95, end: 23.95, light: "subuh", focus: [1.5, 3], cams: [cam(21.95, [-0.9, 2.5, 10.0], [1.2, 1.0, 1.5], 40), cam(23.95, [-0.7, 2.3, 9.0], [1.4, 1.0, 1.0], 40)] },
  // 10 "dan mengintip ke dapur."
  { id: "intip", start: 23.95, end: 25.35, light: "subuh", focus: [DX + 1, -1], cams: [cam(23.95, [DX + 0.1, 1.7, 3.1], [DX + 3.1, 1.45, -0.6], 42), cam(25.35, [DX + 0.4, 1.7, 2.7], [DX + 3.1, 1.45, -0.6], 40)] },
  // 11 "Mbah Sarni sedang menuang gula."
  { id: "tuang", start: 25.35, end: 27.1, light: "subuh", focus: [DX, -1.5], cams: [cam(25.35, [DX + 0.55, 2.3, 1.95], [DX - 0.25, 1.15, -1.9], 38), cam(27.1, [DX + 0.45, 2.25, 1.55], [DX - 0.25, 1.15, -1.9], 36)] },
  // 12 "Banyak sekali."
  { id: "gula", start: 27.1, end: 28.15, light: "subuh", focus: [DX, -1.5], cams: [cam(27.1, [DX - 0.05, 1.6, -0.85], [DX - 0.35, 1.28, -1.55], 32), cam(28.15, [DX - 0.08, 1.58, -0.95], [DX - 0.35, 1.28, -1.55], 30)] },
  // 13 "Ia mendekatkan gelas takar ke matanya, menyipit, lalu menuang lagi."
  { id: "takar", start: 28.15, end: 32.4, light: "subuh", focus: [DX, -1.5], cams: [cam(28.15, [DX + 0.3, 1.72, 1.0], [DX - 0.2, 1.42, -2.35], 38), cam(32.4, [DX + 0.15, 1.68, 0.55], [DX - 0.2, 1.45, -2.35], 35)] },
  // 14 "Mata Mbah Sarni mulai rabun. Dan ia tidak mau ada yang tahu."
  { id: "rabun", start: 32.4, end: 36.8, light: "subuh", focus: [DX, -1.5], fade: 0.5, cams: [cam(32.4, [DX - 0.05, 1.64, 0.75], [DX - 0.2, 1.5, -2.35], 36), cam(36.8, [DX - 0.1, 1.62, 0.2], [DX - 0.2, 1.52, -2.35], 33)] },
  // 15 "Laras tidak bilang apa-apa."
  { id: "laras_pergi", start: 36.8, end: 38.45, light: "subuh", focus: [DX + 2, -1], cams: [cam(36.8, [DX + 0.9, 1.7, 2.3], [DX + 3.3, 1.45, -0.55], 38), cam(38.45, [DX + 1.1, 1.68, 2.0], [DX + 3.3, 1.45, -0.55], 36)] },
  // 16 "Malam itu, ia mengambil spidol merah."
  { id: "malam", start: 38.45, end: 41.0, light: "malam", fade: 0.5, focus: [DX, -1.5], cams: [cam(38.45, [DX + 0.95, 1.85, 2.0], [DX + 0.6, 1.25, -2.0], 38), cam(41.0, [DX + 0.9, 1.8, 1.6], [DX + 0.6, 1.28, -2.0], 36)] },
  // 17 "Diam-diam, ia menggambar garis tebal di setiap gelas takar Mbah."
  { id: "garis", start: 41.0, end: 44.95, light: "malam", focus: [DX, -1.5], cams: [cam(41.0, [DX + 0.45, 1.32, -0.15], [DX + 0.62, 0.98, -1.38], 34), cam(44.95, [DX + 0.78, 1.3, -0.3], [DX + 0.62, 0.98, -1.38], 32)] },
  // 18 "Besar. Jelas."
  { id: "jelas", start: 44.95, end: 46.75, light: "malam", focus: [DX, -1.5], cams: [cam(44.95, [DX + 0.7, 1.7, 0.95], [DX + 0.6, 1.48, -2.35], 36), cam(46.75, [DX + 0.68, 1.68, 0.65], [DX + 0.6, 1.5, -2.35], 34)] },
  // 19 "Besok paginya, jamu Mbah Sarni kembali pas."
  { id: "pas", start: 46.75, end: 49.55, light: "pagi", fade: 0.45, focus: [DX, -1.5], cams: [cam(46.75, [DX + 0.3, 1.72, 0.95], [DX - 0.2, 1.44, -2.35], 37), cam(49.55, [DX + 0.2, 1.7, 0.55], [DX - 0.2, 1.46, -2.35], 34)] },
  // 20 "Dan warga? Ternyata mereka sudah tahu sejak awal."
  { id: "tahu", start: 49.55, end: 52.9, focus: [1.2, 2], cams: [cam(49.55, [0.7, 2.2, -2.5], [1.1, 1.3, 2.1], 40), cam(52.9, [0.75, 2.1, -2.1], [1.1, 1.32, 2.1], 38)] },
  // 21 "Mereka hanya tidak ingin Mbah berhenti berjualan."
  { id: "jualan", start: 52.9, end: 55.75, focus: [2, 1.2], cams: [orb(52.9, head(MBAH_TERAS, 1.4), -2.4, 4.0), orb(55.75, head(MBAH_TERAS, 1.42), -2.4, 3.6, 36)] },
  // 22 "Kadang, yang membuat sesuatu terasa manis, bukan gulanya."
  { id: "akhir", start: 55.75, end: 60.0, fade: 0.5, focus: [1.2, 1.5], cams: [cam(55.75, [0.9, 2.4, -2.6], [1.3, 1.15, 2.0], 40), cam(60.0, [0.6, 4.3, -5.2], [1.3, 1.0, 1.8], 42)] },
];

// --- actor tracks -----------------------------------------------------------------------------------------------
const drink = { armRf: 2.05, armR: -0.38, headNod: -0.18 };
const drinkL = { armLf: 2.05, armL: -0.38, headNod: -0.18 };
const holdR = { armRf: 0.95, armR: 0.05 };
const holdL = { armLf: 0.95, armL: 0.05 };
const toast = { armRf: 2.5, armR: 0.25 };
const off: [number, number] = [-40, -40];

const tracks: Record<string, Track> = {
  mbah_sarni: {
    path: [at(0, MBAH_TERAS), ...jump(21.95, MBAH_DAPUR), ...jump(46.75, MBAH_DAPUR), ...jump(49.55, MBAH_TERAS)],
    face: [{ t: 0, yaw: -H }, { t: 8.6, yaw: -2.3 }, { t: 12.3, yaw: -H }, { t: 21.95, yaw: 0 }, { t: 49.55, yaw: -2.3 }, { t: 52.9, yaw: -2.0 }, { t: 55.75, yaw: -2.3 }],
    lookAt: [{ t: 0, target: null }],
    expr: [{ t: 0, e: "senyum" }, { t: 6.0, e: "tawa" }, { t: 7.0, e: "senyum" }, { t: 25.35, e: "netral" }, { t: 29.6, e: "sipit" }, { t: 31.2, e: "netral" }, { t: 32.4, e: "sedih" }, { t: 34.6, e: "senyum" },
      { t: 46.75, e: "sipit" }, { t: 47.3, e: "kaget" }, { t: 47.9, e: "senyum" }, { t: 48.7, e: "merem" }, { t: 49.55, e: "senyum" }, { t: 53.3, e: "tawa" }, { t: 55.75, e: "senyum" }],
    pose: [{ t: 0, p: {} }, { t: 6.1, p: { armRf: 1.25, armR: 0.0 } }, { t: 8.6, p: {} }, { t: 25.35, p: { armRf: 1.25, armR: -0.1 } }, { t: 26.0, p: { armRf: 1.05, armR: -0.1 } }, { t: 26.6, p: { armRf: 1.3, armR: -0.1 } },
      { t: 27.2, p: { armRf: 1.05, armR: -0.1 } }, { t: 27.8, p: { armRf: 1.3, armR: -0.1 } }, { t: 28.5, p: { armRf: 2.5, armR: -0.45, headNod: -0.05 } }, { t: 31.2, p: { armRf: 1.25, armR: -0.1 } },
      { t: 32.4, p: { headNod: 0.12 } }, { t: 34.6, p: {} }, { t: 46.75, p: { armRf: 2.5, armR: -0.45 } }, { t: 48.3, p: drink }, { t: 49.55, p: {} }, { t: 53.0, p: { armRf: 1.35, armR: 0.0 } }, { t: 55.75, p: drink }],
    talk: [[52.9, 54.0]],
    hidden: [[38.45, 46.75]],
  },
  pak_sobri: {
    path: [at(0, SOBRI)],
    face: [{ t: 0, yaw: H }, { t: 8.6, yaw: 2.2 }, { t: 12.3, yaw: -1.6 }, { t: 14.0, yaw: 2.2 }, { t: 49.55, yaw: 2.3 }, { t: 55.75, yaw: 2.4 }],
    expr: [{ t: 0, e: "senyum" }, { t: 12.4, e: "meringis" }, { t: 13.2, e: "tawa" }, { t: 13.5, e: "meringis" }, { t: 14.0, e: "senyum" }, { t: 51.4, e: "kedip" }, { t: 52.3, e: "senyum" }, { t: 56.0, e: "tawa" }],
    pose: [{ t: 0, p: {} }, { t: 12.35, p: drink }, { t: 13.15, p: { ...holdR, armL: 0.1 } }, { t: 13.45, p: { ...drinkL, armRf: 0.7 } }, { t: 14.0, p: {} }, { t: 49.55, p: holdR }, { t: 55.75, p: toast }],
    hidden: [[0, 8.6], [14.0, 17.15], [21.95, 49.55], [52.9, 55.75]],
  },
  bu_lastri: {
    path: [at(0, LASTRI)],
    face: [{ t: 0, yaw: 2.5 }, { t: 14.0, yaw: yawTo(LASTRI, MBAH_TERAS) }, { t: 17.15, yaw: 2.5 }, { t: 49.55, yaw: 2.5 }],
    expr: [{ t: 0, e: "senyum" }, { t: 14.0, e: "senyum" }, { t: 15.4, e: "tawa" }, { t: 16.3, e: "senyum" }, { t: 50.2, e: "kedip" }, { t: 51.0, e: "senyum" }, { t: 56.0, e: "tawa" }],
    pose: [{ t: 0, p: holdR }, { t: 15.3, p: { ...holdR, armLf: 1.6, armL: 0.5 } }, { t: 17.1, p: holdR }, { t: 55.75, p: toast }],
    talk: [[15.4, 17.1]],
    hidden: [[0, 8.6], [21.95, 49.55]],
  },
  mas_gilang: {
    path: [at(0, GILANG)],
    face: [{ t: 0, yaw: 2.6 }, { t: 17.15, yaw: -0.3 }, { t: 20.45, yaw: 2.6 }, { t: 49.55, yaw: 2.6 }],
    expr: [{ t: 0, e: "netral" }, { t: 17.6, e: "meringis" }, { t: 19.5, e: "kedip" }, { t: 20.45, e: "senyum" }, { t: 50.4, e: "tawa" }, { t: 51.4, e: "senyum" }],
    pose: [{ t: 0, p: holdR }, { t: 17.15, p: holdR }, { t: 17.7, p: { ...holdR, headNod: 0.1 } }, { t: 19.5, p: toast }, { t: 20.45, p: holdR }, { t: 55.75, p: toast }],
    hidden: [[0, 8.6], [12.3, 14.0], [20.45, 21.95], [21.95, 49.55]],
  },
  bayu: {
    path: [at(0, BAYU), ...jump(52.9, [1.75, 1.45]), ...jump(55.75, BAYU)],
    face: [{ t: 0, yaw: 2.7 }, { t: 52.9, yaw: H + 0.25 }, { t: 55.75, yaw: 2.7 }],
    expr: [{ t: 0, e: "senyum" }, { t: 53.2, e: "tawa" }],
    pose: [{ t: 0, p: {} }, { t: 53.2, p: { armRf: 1.3, armR: 0.0 } }, { t: 55.75, p: toast }],
    hidden: [[0, 8.6], [17.15, 21.95], [21.95, 49.55]],
  },
  laras: {
    path: [at(0, LARAS_Q), ...jump(21.95, [0.3, 7.2]), at(23.9, [2.0, 1.1]), ...jump(23.95, LARAS_PINTU), at(37.6, LARAS_PINTU), at(38.4, [DX + 4.6, 0.3]), ...jump(38.45, LARAS_MEJA), ...jump(46.75, [DX + 4.6, 0.3]),
      ...jump(49.55, LARAS_Q), ...jump(55.75, LARAS_Q)],
    face: [{ t: 0, yaw: 2.6 }, { t: 20.45, yaw: -0.5 }, { t: 21.9, yaw: 2.6 }, { t: 23.95, yaw: -H }, { t: 38.45, yaw: 0 }, { t: 49.55, yaw: 2.7 }],
    lookAt: [{ t: 0, target: null }, { t: 23.95, target: "mbah_sarni" }, { t: 38.45, target: null }],
    expr: [{ t: 0, e: "netral" }, { t: 20.45, e: "bingung" }, { t: 22.0, e: "netral" }, { t: 24.4, e: "kaget" }, { t: 25.3, e: "bingung" }, { t: 36.8, e: "sedih" }, { t: 38.45, e: "netral" },
      { t: 40.1, e: "senyum" }, { t: 41.0, e: "netral" }, { t: 44.95, e: "senyum" }, { t: 45.85, e: "tawa" }, { t: 49.55, e: "senyum" }, { t: 51.6, e: "tawa" }, { t: 52.4, e: "senyum" }],
    pose: [{ t: 0, p: {} }, { t: 23.95, p: { headTilt: -0.25, lean: 0.12 } }, { t: 36.8, p: { headNod: 0.15 } }, { t: 37.7, p: {} }, { t: 38.45, p: {} }, { t: 39.5, p: { armRf: 0.8, armR: 0.0 } },
      { t: 40.0, p: { armRf: 1.7, armR: -0.2 } }, { t: 41.0, p: { armRf: 1.15, armR: -0.4 } }, { t: 41.7, p: { armRf: 1.0, armR: -0.25 } }, { t: 42.4, p: { armRf: 1.15, armR: -0.05 } },
      { t: 43.1, p: { armRf: 1.0, armR: 0.1 } }, { t: 43.8, p: { armRf: 1.15, armR: 0.2 } }, { t: 44.5, p: { armRf: 1.0, armR: 0.25 } }, { t: 44.95, p: { armLf: 1.85, armL: -0.25 } }, { t: 46.75, p: {} },
      { t: 49.55, p: holdR }, { t: 55.75, p: toast }],
    hidden: [[0, 8.6], [17.15, 20.45]],
  },
  belang: {
    path: [at(0, [0.4, 6.5]), at(6.0, [0.4, 6.5]), at(8.6, [1.35, 2.6]), at(12.3, [1.35, 2.6]), ...jump(55.75, [1.2, 3.0])],
    face: [{ t: 0, yaw: Math.PI }, { t: 8.6, yaw: 0.6 }, { t: 55.75, yaw: 0.3 }],
    hidden: [[21.95, 49.55]],
  },
};
void off;

// --- props ---------------------------------------------------------------------------------------------------------
const glassM = () => new THREE.MeshStandardMaterial({ color: "#ffffff", roughness: 0.08, transparent: true, opacity: 0.35 });
function jamuGlass(color: string) {
  const g = new THREE.Group();
  part(g, new THREE.CylinderGeometry(0.06, 0.05, 0.14, 14, 1, true), glassM(), [0, 0.07, 0], 0.004);
  part(g, new THREE.CylinderGeometry(0.052, 0.046, 0.11, 14), clay(color, undefined, 0.3), [0, 0.06, 0], 0);
  return g;
}
type Cup = { g: THREE.Group; band: THREE.Mesh; r: number };
function takarCup(): Cup {
  const g = new THREE.Group(), r = 0.075;
  part(g, new THREE.CylinderGeometry(r, r * 0.9, 0.2, 18, 1, true), glassM(), [0, 0.1, 0], 0.005);
  part(g, new THREE.CylinderGeometry(r * 0.9, r * 0.9, 0.01, 18), glassM(), [0, 0.005, 0], 0);
  for (let i = 1; i <= 3; i++) part(g, new THREE.CylinderGeometry(r + 0.001, r + 0.001, 0.004, 18, 1, true), new THREE.MeshBasicMaterial({ color: "#7a8a96", transparent: true, opacity: 0.5 }), [0, 0.04 * i, 0], 0);
  const handle = part(g, new THREE.TorusGeometry(0.04, 0.01, 6, 12, Math.PI), glassM(), [r + 0.005, 0.11, 0], 0); handle.rotation.z = -H;
  const band = new THREE.Mesh(new THREE.CylinderGeometry(r + 0.004, r * 0.97 + 0.004, 0.028, 24, 1, true), new THREE.MeshStandardMaterial({ color: "#e0262a", roughness: 0.5, side: THREE.DoubleSide }));
  band.position.y = 0.12; g.add(band);
  return { g, band, r };
}
function setBand(c: Cup, k: number) {
  k = Math.max(0, Math.min(1, k));
  c.band.visible = k > 0.01;
  if (!c.band.visible) return;
  if (c.band.userData.k === Math.round(k * 24)) return;
  c.band.userData.k = Math.round(k * 24);
  c.band.geometry.dispose();
  c.band.geometry = new THREE.CylinderGeometry(c.r + 0.004, c.r * 0.97 + 0.004, 0.028, 24, 1, true, -H, Math.max(0.05, k * Math.PI * 2));
}
function spoon() {
  const g = new THREE.Group();
  part(g, new THREE.CylinderGeometry(0.008, 0.008, 0.22, 6), clay("#d9d4c8", undefined, 0.3), [0, 0.0, 0.1], 0).rotation.x = H;
  part(g, new THREE.SphereGeometry(0.03, 10, 8), clay("#d9d4c8", undefined, 0.3), [0, 0.0, 0.22], 0).scale.set(1, 0.4, 1.3);
  return g;
}
function marker() {
  const g = new THREE.Group();
  part(g, new THREE.CylinderGeometry(0.014, 0.014, 0.15, 8), clay("#d8262a"), [0, 0.02, 0.06], 0.004).rotation.x = H * 0.8;
  return g;
}

/** keep a hand prop upright in world space (plus a tilt), whatever the arm is doing */
const qa = new THREE.Quaternion(), qb = new THREE.Quaternion(), eul = new THREE.Euler();
function upright(prop: THREE.Object3D, owner: Warga, tilt = 0) {
  owner.group.updateMatrixWorld(true);
  prop.parent!.getWorldQuaternion(qa);
  eul.set(tilt, owner.group.rotation.y, 0, "YXZ");
  qb.setFromEuler(eul);
  prop.quaternion.copy(qa.invert().multiply(qb));
}

const inRange = (t: number, ...r: [number, number][]) => r.some(([a, b]) => t >= a && t < b);

const extra: StoryDef["extra"] = (_set, scene, cast) => {
  // teras: two glasses + a heap of sugar on the amben
  const teras = new THREE.Group(); scene.add(teras);
  const gk = jamuGlass("#f0b42e"); gk.position.set(2.2, 0.6, 1.12); teras.add(gk);
  const gb = jamuGlass("#f4ecd8"); gb.position.set(2.16, 0.6, 1.32); teras.add(gb);
  part(teras, new THREE.CylinderGeometry(0.12, 0.08, 0.06, 16), clay("#2f7d6d"), [2.14, 0.63, 1.62], 0.005);
  part(teras, new THREE.ConeGeometry(0.11, 0.12, 16), clay("#fbf8f2", undefined, 0.9), [2.14, 0.71, 1.62], 0.004);
  const sp = spoon(); sp.position.set(2.1, 0.74, 1.5); sp.rotation.set(0.4, 0.9, 0); teras.add(sp);

  // dapur: growing sugar heap in the pot + three measuring cups
  const heap = part(scene, new THREE.ConeGeometry(0.2, 0.12, 20), clay("#fbf8f2", undefined, 0.9), [DX - 0.35, 1.2, -1.55], 0.004);
  const cups = [[DX + 0.4, -1.38], [DX + 0.62, -1.25], [DX + 0.84, -1.4]].map(([x, z]) => { const c = takarCup(); c.g.position.set(x, 0.89, z); scene.add(c.g); return c; });

  // hand props
  const hp = <T extends THREE.Object3D>(who: string, side: "L" | "R", obj: T) => { cast[who].hands[side].add(obj); return obj; };
  const mbahGlass = hp("mbah_sarni", "R", jamuGlass("#f0b42e"));
  const mbahSpoon = hp("mbah_sarni", "R", spoon());
  const mbahCup = takarCup(); hp("mbah_sarni", "R", mbahCup.g);
  const glasses: [string, "L" | "R", THREE.Group][] = [
    ["pak_sobri", "R", jamuGlass("#f0b42e")], ["pak_sobri", "L", jamuGlass("#f4ecd8")], ["bu_lastri", "R", jamuGlass("#f0b42e")],
    ["mas_gilang", "R", jamuGlass("#f4ecd8")], ["bayu", "R", jamuGlass("#f0b42e")], ["laras", "R", jamuGlass("#f4ecd8")],
  ];
  glasses.forEach(([w, s, g]) => hp(w, s, g));
  const larasMarker = hp("laras", "R", marker());
  const larasCup = takarCup(); hp("laras", "L", larasCup.g);

  return (t: number) => {
    // sugar heap grows while Mbah pours
    const k = Math.max(0, Math.min(1, (t - 25.4) / 6.8));
    heap.visible = t >= 25.4 && t < 46.75; heap.scale.set(0.4 + k * 0.6, 0.2 + k * 1.2, 0.4 + k * 0.6); heap.position.y = 1.23 + 0.06 * (0.2 + k * 1.2);
    // red lines drawn on the cups one by one (41.6 .. 44.6)
    cups.forEach((c, i) => setBand(c, t < 41.6 ? 0 : (t - (41.6 + i * 1.0)) / 0.9));
    setBand(mbahCup, t >= 46.75 ? 1 : 0); setBand(larasCup, 1);

    const sh = (o: THREE.Object3D, who: string, on: boolean, tilt = 0) => { o.visible = on; if (on) upright(o, cast[who], tilt); };
    sh(mbahGlass, "mbah_sarni", inRange(t, [6.0, 8.6], [48.1, 49.55], [52.9, 60]), t >= 48.3 && t < 49.55 ? -0.7 : 0);
    sh(mbahSpoon, "mbah_sarni", inRange(t, [25.35, 28.2]), -0.25 + Math.sin(t * 9) * 0.25);
    sh(mbahCup.g, "mbah_sarni", inRange(t, [28.2, 32.4], [46.75, 48.1]), t > 31.2 && t < 32.4 ? -1.2 : 0);
    const drinking = (who: string, a: number, b: number) => (t >= a && t < b ? -0.8 : 0);
    sh(glasses[0][2], "pak_sobri", inRange(t, [8.6, 14.0], [49.55, 60]), drinking("pak_sobri", 12.4, 13.15));
    sh(glasses[1][2], "pak_sobri", inRange(t, [13.15, 14.0]), drinking("pak_sobri", 13.5, 14.0));
    sh(glasses[2][2], "bu_lastri", inRange(t, [8.6, 21.95], [49.55, 60]));
    sh(glasses[3][2], "mas_gilang", inRange(t, [8.6, 21.95], [49.55, 60]));
    sh(glasses[4][2], "bayu", inRange(t, [53.3, 60]));
    sh(glasses[5][2], "laras", inRange(t, [49.55, 60]));
    sh(larasMarker, "laras", inRange(t, [39.5, 44.95]), -0.9);
    sh(larasCup.g, "laras", inRange(t, [44.95, 46.75]));
  };
};

export const JAMU: StoryDef = { total: 1795, shots, tracks, words, extra };
