# Soundtrack of "Jamu yang Selalu Kemanisan": gentle original score (guitar plucks, pad, music box) + small SFX,
# ducked under the user's VO, mastered to -11 LUFS. Output: mix.wav (48 kHz, exact picture length).
import json, os
import numpy as np
from dsp import SR, ns, tt, rng, dbg, lp, hp, bp, colored, fades, place, pan, st, make_ir, convolve_st, integrated, read_wav, write_wav
import instruments as I
import sfx_gen as G

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FPS, TOTAL = 30, 1795
DUR = TOTAL / FPS; N = ns(DUR); r = rng(21)
m = np.zeros((2, N)); s = np.zeros((2, N))
def m2f(n): return 440.0 * 2 ** ((n - 69) / 12)
BPM = 88.0; BEAT = 60 / BPM
CH = {"C": [48, 55, 60, 64, 67], "G": [43, 50, 55, 59, 62], "Am": [45, 52, 57, 60, 64], "F": [41, 48, 53, 57, 60], "Em": [40, 47, 52, 55, 59], "Dm": [38, 45, 50, 53, 57]}

def section(t0, t1, prog, vel=0.55, arp=True, padv=0.3, melody=None, mvel=0.4):
    bar = 4 * BEAT; t = t0; i = 0
    while t < t1 - 0.2:
        ch = CH[prog[i % len(prog)]]; d = min(bar, t1 - t)
        if padv > 0: place(m, I.pad([m2f(n + 12) for n in ch[2:]], d + 0.6, padv, r, 0.5, 0.8, 1200.0), t, 0.5)
        place(m, pan(I.pluck(m2f(ch[0]), vel, r, 1.6, 0.35), -0.1), t, 0.6)
        if arp:
            pat = [1, 2, 3, 4, 3, 2, 3, 4]
            for k, j in enumerate(pat):
                tk = t + k * BEAT / 2
                if tk < t1 - 0.05: place(m, pan(I.pluck(m2f(ch[j]), vel * (0.8 if k % 2 else 1.0), r, 0.9, 0.5), 0.25 - 0.06 * k), tk, 0.5)
        if melody:
            notes = melody[i % len(melody)]
            for k, n in enumerate(notes):
                if n and t + k * BEAT < t1 - 0.1: place(m, pan(I.musicbox(m2f(n), mvel, r, 1.4), 0.3), t + k * BEAT, 0.45)
        t += bar; i += 1

MEL_HAPPY = [[76, 0, 74, 72], [74, 0, 71, 0], [72, 0, 76, 79], [77, 0, 76, 0]]
MEL_SAD = [[76, 0, 72, 0], [77, 0, 76, 74], [72, 0, 0, 0], [71, 0, 74, 0]]
MEL_HOPE = [[72, 74, 76, 0], [79, 0, 77, 76], [76, 0, 74, 72], [74, 0, 0, 0]]
# 1 warm morning at the terrace
section(0.0, 21.95, ["C", "G", "Am", "F"], 0.5, True, 0.25, MEL_HAPPY)
# 2 dawn, curiosity: sparse plucks
section(21.95, 32.4, ["Am", "F", "Am", "G"], 0.42, True, 0.18, None)
# 3 the eyes: slow and tender
section(32.4, 38.45, ["F", "C", "Am", "G"], 0.38, False, 0.35, MEL_SAD, 0.35)
# 4 night, the plan: rising
section(38.45, 46.75, ["F", "G", "Em", "Am"], 0.45, True, 0.3, None)
# 5 morning again: full warmth to the end, final chord rings out
section(46.75, 58.4, ["C", "G", "Am", "F"], 0.55, True, 0.3, MEL_HOPE, 0.45)
for k, n in enumerate([48, 55, 60, 64, 67, 72]): place(m, pan(I.pluck(m2f(n), 0.55, r, 2.6, 0.4), -0.3 + 0.12 * k), 58.7 + k * 0.06, 0.6)
place(m, I.pad([m2f(n) for n in (60, 64, 67, 72)], 3.0, 0.35, r, 0.3, 1.5, 1400.0), 58.6, 0.5)
place(m, pan(I.glock(m2f(84), 0.4, r, 2.0), 0.2), 58.75, 0.3)
m = convolve_st(m, make_ir(1.4, 5)) * 0.4 + m

def sx(x, t, g=1.0, p=0.0):
    place(s, pan(x, p) if x.ndim == 1 else x, t, g)
def hiss(d, lo=2500, hi=7000):
    y = bp(colored(ns(d), r, 0.0), lo, hi); e = np.minimum(1, tt(d) / 0.03) * np.minimum(1, (d - tt(d)) / 0.08); return y * e * 0.5
def squeak(d):
    t = tt(d); f = 1800 + 500 * np.sin(2 * np.pi * 3 * t)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25 + bp(colored(ns(d), r, 0.0), 2000, 5000) * 0.3
    return tone * np.minimum(1, t / 0.02) * np.minimum(1, (d - t) / 0.05)
def cricket(d):
    t = tt(d); g = (np.sin(2 * np.pi * 28 * t) > 0.3) * (np.sin(2 * np.pi * 0.9 * t) > -0.2)
    return np.sin(2 * np.pi * 4300 * t) * g * 0.15
def rooster():
    t = tt(1.3); f = np.interp(t, [0, 0.15, 0.4, 0.9, 1.3], [500, 750, 820, 700, 420])
    y = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.2 + np.sin(4 * np.pi * np.cumsum(f) / SR) * 0.3
    return lp(y, 2500) * np.minimum(1, t / 0.05) * np.minimum(1, (1.3 - t) / 0.3) * 0.5

# morning ambience: birds on the terrace scenes
for t0, d in [(0.0, 8.6), (8.6, 13.4), (49.55, 10.2)]: sx(G.bird_chirps(d, r, 0.5), t0, 0.22, 0.3)
# glasses on the amben, sips
for t in (3.5, 4.9, 6.2, 12.4, 13.5, 16.0, 19.6, 48.6, 53.3, 56.0, 56.2, 56.4): sx(G.clink(r, r.uniform(2400, 3200), 0.25, 1.0), t, 0.35, r.uniform(-0.3, 0.3))
for t in (12.6, 13.7, 48.8): sx(G.bubbles(0.35, r, 18), t, 0.2)
# dawn: rooster, soft steps
sx(rooster(), 22.1, 0.3, -0.4)
for k in range(5): sx(G.stroll_step(r), 22.4 + k * 0.38, 0.18, 0.2)
# sugar: spoonfuls hiss into the pot
for t in (25.7, 26.3, 26.9, 27.5, 31.5): sx(hiss(0.45, 3000, 8000), t, 0.3)
for t in (25.6, 26.2, 26.8, 27.4): sx(G.clink(r, 3600, 0.12, 0.8), t, 0.2)
# night: crickets + marker strokes
sx(cricket(8.3), 38.45, 0.12, 0.5)
for t in (41.6, 42.6, 43.6): sx(squeak(0.7), t, 0.35, 0.1)
# soft whooshes into the time jumps
for t in (21.95, 38.45, 46.75): sx(G.whoosh(0.6, r, 0.3), t - 0.3, 0.15)
s = convolve_st(s, make_ir(0.6, 8)) * 0.3 + s

x, sr = read_wav(os.path.join(ROOT, "voice", "vo.wav"))
v = st(x)
v = np.pad(v, ((0, 0), (0, max(0, N - v.shape[1]))))[:, :N]
words = json.load(open(os.path.join(ROOT, "voice", "words.json")))["words"]
speak = np.zeros(N)
for w in words: speak[ns(max(0, w["start"] - 0.08)):ns(w["end"] + 0.12)] = 1
k = ns(0.15); speak = np.convolve(speak, np.ones(k) / k, "same")
duck = dbg(-8 * speak)
LV = integrated(v)
gm = dbg((LV - 5) - integrated(m)) * duck
gs = dbg((LV - 8) - integrated(s))
mix = v + m * gm + s * gs
mix *= dbg(-11 - integrated(mix))
lim = 0.89
mix = np.where(np.abs(mix) > lim * 0.8, np.sign(mix) * (lim * 0.8 + lim * 0.2 * np.tanh((np.abs(mix) - lim * 0.8) / (lim * 0.2))), mix)
mix = fades(mix, 0.005, 0.6)
write_wav(os.path.join(HERE, "mix.wav"), mix)
print("voice", round(LV, 1), "music", round(integrated(m * gm), 1), "sfx", round(integrated(s * gs), 1), "mix", round(integrated(mix), 1), "LUFS; peak", round(20 * np.log10(np.abs(mix).max()), 2))
