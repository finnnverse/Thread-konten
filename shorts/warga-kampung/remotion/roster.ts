// The fixed kampung cast. Reuse these ids in every story so the characters stay identical across videos.
import { Spec } from "./cast3d";

export const ROSTER: Spec[] = [
  {
    id: "mbah_sarni", name: "Mbah Sarni", desc: "Nenek 70-an, penjual jamu. Lembut, suka menasihati.", age: "lansia",
    skin: "#b47650", hair: "konde", hairColor: "#d9d3cc", brow: "#cfc8c0",
    top: { kind: "polos", base: "#a98bc9", accent: "#a98bc9" }, sleeves: "panjang",
    bottom: { kind: "batik", base: "#6b3f22", accent: "#d9a55a", repeat: 2 }, bottomKind: "rok",
    shoes: "#7a4a2c", wrinkles: true, stoop: 0.08,
  },
  {
    id: "pak_sobri", name: "Pak Sobri", desc: "Ketua RT 50-an. Kumis tebal, suaranya keras tapi hatinya baik.", age: "dewasa",
    skin: "#a5683f", hair: "pendek", hairColor: "#1f1a17", hat: "peci", mustache: "#1f1a17",
    top: { kind: "batik", base: "#8a4b1c", accent: "#f0c27a", repeat: 2 }, sleeves: "pendek",
    bottom: { kind: "polos", base: "#3d3d46", accent: "#3d3d46" }, bottomKind: "celana",
    shoes: "#2a2523", belly: 0.9,
  },
  {
    id: "bu_lastri", name: "Bu Lastri", desc: "Pemilik warung 40-an. Cerewet, tahu semua gosip kampung.", age: "dewasa",
    skin: "#c88a5c", hair: "pendek", hairColor: "#2a1d16", hijab: "#2f9c8f", lashes: true,
    top: { kind: "bunga", base: "#e3788a", accent: "#fff1c9", repeat: 2 }, sleeves: "panjang",
    bottom: { kind: "bunga", base: "#e3788a", accent: "#fff1c9", repeat: 3 }, bottomKind: "rok",
    shoes: "#8a5a3a",
  },
  {
    id: "bayu", name: "Bayu", desc: "Anak SD kelas 3. Penasaran, banyak tanya, larinya kencang.", age: "anak",
    skin: "#b3743f", hair: "jabrik", hairColor: "#1b1512",
    top: { kind: "polos", base: "#f5f3ee", accent: "#f5f3ee" }, sleeves: "pendek",
    bottom: { kind: "polos", base: "#c8302c", accent: "#c8302c" }, bottomKind: "celana-pendek",
    shoes: "#1f1c1c", backpack: "#3f78c9",
  },
  {
    id: "laras", name: "Laras", desc: "Remaja SMA. Pintar, sering jadi penengah.", age: "remaja",
    skin: "#cf9866", hair: "kuncir", hairColor: "#3a2418", lashes: true, freckles: true,
    top: { kind: "polos", base: "#f2b631", accent: "#f2b631" }, sleeves: "pendek",
    bottom: { kind: "polos", base: "#3e5f8f", accent: "#3e5f8f" }, bottomKind: "celana",
    shoes: "#f2efe8",
  },
  {
    id: "mas_gilang", name: "Mas Gilang", desc: "Pemuda 25-an, montir bengkel. Santai, suka bercanda.", age: "dewasa",
    skin: "#ad7146", hair: "belah", hairColor: "#16120f",
    top: { kind: "polos", base: "#e8742a", accent: "#e8742a" }, sleeves: "panjang", zipper: "#f4ede2",
    bottom: { kind: "polos", base: "#7b6a4a", accent: "#7b6a4a" }, bottomKind: "celana",
    shoes: "#5a3a24",
  },
  {
    id: "kakek_wiryo", name: "Kakek Wiryo", desc: "Kakek 75-an, veteran. Pendiam, jalan pakai tongkat.", age: "lansia",
    skin: "#98603f", hair: "botak", hairColor: "#ece8e2", brow: "#e6e1da", beard: "#f1ede7", glasses: true, wrinkles: true,
    top: { kind: "polos", base: "#f1eee6", accent: "#f1eee6" }, sleeves: "pendek",
    bottom: { kind: "kotak", base: "#2f6b4a", accent: "#c9b27a", repeat: 2 }, bottomKind: "sarung",
    shoes: "#6a4630", cane: true, stoop: 0.14,
  },
];
export const KUCING = { id: "belang", name: "Si Belang", desc: "Kucing oranye kampung. Muncul di setiap video, suka mencuri ikan." };
export const byId = (id: string) => ROSTER.find((r) => r.id === id)!;
