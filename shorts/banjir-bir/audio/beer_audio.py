# Soundtrack of "Banjir Bir London": original oom-pah polka score + synthesized SFX, ducked under the user's VO.
# Uses the skill's DSP kit (dsp.py / instruments.py / sfx_gen.py). Output: mix.wav (48 kHz, exact picture length).
import json, os, sys
import numpy as np
from dsp import SR, ns, tt, rng, dbg, lp, hp, bp, colored, fades, place, pan, st, widen, make_ir, convolve_st, integrated, true_peak, read_wav, write_wav
import instruments as I
import sfx_gen as G

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FPS, TOTAL = 30, 1845
DUR = TOTAL / FPS
F = lambda f: f / FPS
N = ns(DUR)
r = rng(14)

# ---------------------------------------------------------------- music
BPM = 116.0
BEAT = 60 / BPM
m = np.zeros((2, N))
def m2f(n): return 440.0 * 2 ** ((n - 69) / 12)
# F major oom-pah: tuba roots on beats 1/3, pizzicato chord on 2/4, glockenspiel tune on top
CH = {"F": (53, [65, 69, 72]), "C": (48, [64, 67, 70]), "Bb": (46, [62, 65, 70]), "Dm": (50, [62, 65, 69]), "Gm": (55, [62, 67, 70])}
PROG = ["F", "F", "C", "C", "Bb", "F", "C", "F"]
TUNE = [72, 74, 76, 72, 77, 76, 74, 72, 74, 76, 77, 79, 77, 76, 74, 72]  # two notes per bar
def oompah(t0, t1, vel=0.7, tune=True, fast=1.0, minor=False):
    b, t = 0, t0
    beat = BEAT / fast
    while t < t1 - 0.05:
        bar = b // 4
        ch = PROG[bar % len(PROG)] if not minor else ["Dm", "Dm", "Gm", "Dm", "C", "Dm", "Gm", "C"][bar % 8]
        root, tri = CH[ch]
        if b % 2 == 0:
            place(m, pan(I.brass(m2f(root - 12 + (7 if b % 4 == 2 else 0)), beat * 0.8, vel, r, "tuba"), -0.15), t, 0.9)
        else:
            for k, n in enumerate(tri): place(m, pan(I.pluck(m2f(n - 12), vel * 0.55, r, 0.4), 0.3), t + 0.004 * k, 0.5)
        if tune and b % 2 == 0:
            n = TUNE[(b // 2) % len(TUNE)] - (3 if minor and TUNE[(b // 2) % len(TUNE)] % 12 in (4, 9) else 0)
            place(m, pan(I.glock(m2f(n), vel * 0.5, r, 1.0), 0.2), t, 0.45)
        t += beat; b += 1
def stab(t, notes=(53, 57, 60, 65), vel=0.9, d=0.35, g=0.8):
    for k, n in enumerate(notes): place(m, pan(I.brass(m2f(n), d, vel, r, "stab"), (k - 1.5) * 0.25), t, g)
def roll(t0, t1, v0, v1):
    for (t, v) in I.snare_roll(t0, t1, v0, v1, r): place(m, pan(I.snare(v, r, 0.25), 0.1), t, 0.45)

# 1 hook: snare roll + tuba walking, hard stop on "bir." (3.37 s), punch at the flash
roll(0.0, 3.2, 0.25, 0.7)
for k, n in enumerate([41, 43, 45, 46, 48, 50, 52]): place(m, pan(I.brass(m2f(n), 0.3, 0.75, r, "tuba"), -0.1), 0.15 + k * 0.42, 0.8)
stab(3.36, (53, 57, 60, 65), 1.0, 0.25, 0.9)
place(m, pan(I.cymbal(0.6, r, 1.6), 0.2), F(128), 0.5)
# 2 proud brewery: bouncy oom-pah until the slip
oompah(F(128), F(530), 0.7)
# the slip: the band stops; pizzicato tension under the clerk
place(m, pan(I.timpani(m2f(41), 0.7, r, 1.5), 0), F(543), 0.8)
for k in range(10):
    n = [50, 53, 50, 53, 49, 52, 49, 52, 50, 53][k]
    place(m, pan(I.pluck(m2f(n), 0.55, r, 0.5), -0.2 + 0.04 * k), F(570) + k * BEAT, 0.6)
# "satu jam kemudian": low timpani heartbeat + rising roll into the burst
for k in range(4): place(m, pan(I.timpani(m2f(41), 0.5 + 0.1 * k, r, 1.0), 0), F(676) + k * 0.28, 0.6)
roll(F(690), F(711), 0.2, 0.9)
# chaos: fast minor polka with stabs on every hit
oompah(F(711), F(1068), 0.85, True, 1.25, minor=True)
for f, g in [(711, 1.0), (760, 0.6), (800, 0.9), (835, 0.5), (842, 0.9), (912, 1.0), (958, 0.8), (986, 0.8), (1014, 0.9)]:
    stab(F(f), (50, 53, 57, 62), 0.95, 0.3, 0.6 * g)
    place(m, pan(I.cymbal(0.5 * g, r, 1.4), 0.25), F(f), 0.35 * g)
# court: band stops on "Untungnya"; "ta-da" after the verdict, then the heavenly chord on "Tuhan"
stab(F(1135), (53, 57, 60, 65), 0.8, 0.22, 0.5); stab(F(1143), (55, 59, 62, 67), 0.8, 0.5, 0.5)
place(m, I.pad([m2f(n) for n in (65, 69, 72, 77)], 2.8, 0.55, r, 0.4, 1.2), F(1232), 0.7)
place(m, pan(I.glock(m2f(84), 0.6, r, 2.0), 0.3), F(1237), 0.45)
place(m, pan(I.triangle(0.5, r, 1.6), 0.4), F(1237), 0.3)
# explanation (golden): gentle vibes
for k in range(int((F(1462) - F(1258)) / BEAT)):
    n = [65, 69, 72, 69, 67, 70, 74, 70][k % 8]
    place(m, pan(I.vibes(m2f(n), 0.4, r, 1.2), -0.2 + 0.4 * (k % 2)), F(1258) + k * BEAT, 0.5)
    if k % 4 == 0: place(m, pan(I.brass(m2f(41 if (k // 4) % 2 == 0 else 48), BEAT * 1.8, 0.4, r, "soft"), -0.1), F(1258) + k * BEAT, 0.6)
# buffet: tiny waltz until the pop; silence; sad trombone-ish slide on "nyerah"
oompah(F(1465), F(1540), 0.55, True, 1.0)
for k, n in enumerate([58, 57, 56, 55]): place(m, pan(I.brass(m2f(n), 0.38 if k < 3 else 0.9, 0.6, r, "horn", fall=(-3.0 if k == 3 else 0.0)), 0), F(1576) + k * 0.36, 0.55)
# finale: the polka returns, button on the last frame
oompah(F(1600), F(1830), 0.75)
stab(F(1777), (60, 64, 67, 72), 0.9, 0.25, 0.5)
stab(DUR - 0.9, (53, 57, 60, 65), 1.0, 0.18, 0.8); stab(DUR - 0.62, (53, 57, 60, 65, 77), 1.0, 0.55, 0.9)
m = convolve_st(m, make_ir(1.1, 3)) * 0.75 + m * 0.6

# ---------------------------------------------------------------- SFX
s = np.zeros((2, N))
def sx(x, t, g=1.0, p=0.0):
    place(s, pan(x, p) if np.asarray(x).ndim == 1 else x, t, g)
def thump(d=0.6, f=55):
    t = tt(d); return np.sin(2 * np.pi * f * t * (1 - 0.3 * t)) * np.exp(-t / 0.18) * 0.9
def burst():
    n = ns(1.6); nz = colored(n, r, 0.8) * np.exp(-tt(1.6) / 0.35)
    th = thump(0.9, 48); y = lp(nz, 1800) * 0.8; y[: len(th)] += th
    return y
def pop():
    t = tt(0.12); return np.sin(2 * np.pi * (900 - 4000 * t) * t) * np.exp(-t / 0.02) * 0.8
def rush(d, rise=0.3):
    n = ns(d); x = colored(n, r, 0.5); env = np.minimum(1, tt(d) / rise) * np.exp(-np.maximum(0, tt(d) - (d - 0.8)) / 0.4)
    return lp(x, 2500) * env * 0.6
def jingle(d=0.9):
    y = np.zeros(ns(d))
    for k in range(14):
        c = G.clink(r, None, 0.15, 1.2); i = ns(r.uniform(0, d - 0.2)); y[i:i + len(c)] += c[: len(y) - i] * r.uniform(0.4, 0.9)
    return y
# whooshes into hard cuts / glides
for f in [128, 226, 283, 362, 455, 560, 672, 736, 857, 950, 1010, 1068, 1255, 1465, 1600, 1682]:
    sx(G.whoosh(0.5, r, 0.35), F(f) - 0.25, 0.22)
# hook: crowd panic + the wave rushing in
sx(rush(4.3, 0.5), 0.0, 0.5)
for k in range(5): sx(G.whoa(r), 0.4 + k * 0.6, 0.25, -0.5 + 0.25 * k)
sx(G.splash_big(r), F(98), 0.35)
# town ambience
sx(G.bird_chirps(3.2, r, 0.5), F(130), 0.2)
# vat creaks under the hoops; the slip + clang
sx(G.creak(1.2, r), F(380), 0.25, -0.2)
sx(G.creak(0.4, r, 300, 200), F(532), 0.4)
sx(G.hammer_hit(r, 1.4), F(543), 0.8); sx(G.clink(r, 1100, 0.6, 1.2), F(545), 0.6)
# office: a sip
sx(G.bubbles(0.4, r, 20), F(622), 0.15)
# the groan before the burst, the bursts, domino hits
sx(G.creak(1.3, r, 60, 140), F(672), 0.6); sx(G.timber_tear(r, 0.8), F(690), 0.6)
for f, g in [(711, 1.0), (800, 0.85), (842, 0.8)]:
    sx(burst(), F(f), 0.9 * g); sx(G.wood_crack(r), F(f), 0.7 * g); sx(G.splash_big(r), F(f) + 0.1, 0.6 * g)
for f in (760, 835): sx(G.wood_crack(r), F(f), 0.5); sx(thump(0.4, 80), F(f), 0.5)
sx(G.water_bed(4.5, r, 1.0, 1.4), F(720), 0.35)
# the wall: rumble, crumble, then the wave
sx(G.creak(1.2, r, 40, 90), F(880), 0.5); sx(G.rattle(1.0, r, 40, None, True), F(895), 0.3)
sx(burst(), F(912), 1.0); sx(G.rattle(1.8, r, 60, None, True), F(915), 0.5); sx(thump(1.0, 40), F(918), 0.8)
sx(rush(5.2, 0.4), F(918), 0.8)
for k in range(4): sx(G.whoa(r), F(960) + k * 0.45, 0.3, 0.3 - 0.2 * k)
sx(G.splash_big(r), F(1005), 0.6); sx(rush(2.0, 0.2), F(1010), 0.5)
# court: gavel knocks
for f in (1119, 1133): sx(G.hammer_hit(r, 0.7), F(f), 0.6)
# explanation: little pops as each arrow appears
for f in (1307, 1317, 1326, 1340, 1350, 1364): sx(pop(), F(f), 0.25)
sx(G.creak(0.8, r, 80, 60), F(1438), 0.3)
# the belt: pop + buckle ping, then the belt snap
sx(pop(), F(1542), 0.7); sx(G.clink(r, 2600, 0.4), F(1548), 0.5); sx(G.clink(r, 2400, 0.3), F(1580), 0.3)
sx(G.whoosh(0.4, r, 0.2, 800, 3000), F(1576), 0.3)
# aftermath: hammering the tank
for k in range(3): sx(G.hammer_hit(r, 0.5), F(1612) + k * 0.6, 0.25, 0.4)
# tax: footsteps, coins
for k in range(5): sx(G.stroll_step(r), F(1736) + k * 0.33, 0.25, -0.3)
sx(jingle(1.0), F(1777), 0.6)
s = convolve_st(s, make_ir(0.8, 9)) * 0.35 + s

# ---------------------------------------------------------------- voice + mix
x, sr = read_wav(os.path.join(ROOT, "voice", "voice.wav"))
v = st(x)
if v.shape[1] < N: v = np.pad(v, ((0, 0), (0, N - v.shape[1])))
v = v[:, :N]
words = json.load(open(os.path.join(ROOT, "voice", "words.json")))["words"]
speak = np.zeros(N)
for w in words: speak[ns(max(0, w["start"] - 0.08)):ns(w["end"] + 0.12)] = 1
k = ns(0.12); speak = np.convolve(speak, np.ones(k) / k, "same")
duck = dbg(-9 * speak)
LV = integrated(v)
gm = dbg((LV - 5) - integrated(m)) * duck
gs = dbg((LV - 6) - integrated(s))
mix = v + m * gm + s * gs
G0 = dbg(-14 - integrated(mix))
mix *= G0
lim = 0.89
mix = np.where(np.abs(mix) > lim * 0.8, np.sign(mix) * (lim * 0.8 + lim * 0.2 * np.tanh((np.abs(mix) - lim * 0.8) / (lim * 0.2))), mix)
mix = fades(mix, 0.005, 0.3)
write_wav(os.path.join(HERE, "mix.wav"), mix)
print("voice", round(LV, 1), "music", round(integrated(m * gm), 1), "sfx", round(integrated(s * gs), 1), "mix", round(integrated(mix), 1), "LUFS; peak", round(20 * np.log10(np.abs(mix).max()), 2))
