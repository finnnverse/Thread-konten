import os, sys, wave, math, importlib.util, subprocess, numpy as np
from scipy import signal
SR = 48000
def env(n, a, d):
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def note(f): return 440 * 2 ** ((f - 69) / 12)
def lp(x, fc, o=2): b, a = signal.butter(o, fc / (SR / 2)); return signal.lfilter(b, a, x)
def hp(x, fc, o=2): b, a = signal.butter(o, fc / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def bp(x, f0, f1): b, a = signal.butter(2, [f0 / (SR / 2), f1 / (SR / 2)], 'band'); return signal.lfilter(b, a, x)
rng = np.random.default_rng(1)
def sfx(name):
    n = lambda s: int(s * SR); t = lambda s: np.arange(n(s)) / SR
    if name == 'pop':
        f = 900 * np.exp(-t(0.12) * 18) + 300; ph = np.cumsum(2 * np.pi * f / SR); return np.sin(ph) * env(n(.12), .002, .04) * 0.8
    if name == 'pluck':
        out = np.zeros(n(.75))
        for k, m in enumerate([81, 88]):
            x = (np.sin(2 * np.pi * note(m) * t(.6)) + 0.3 * np.sin(2 * np.pi * 4 * note(m) * t(.6))) * env(n(.6), .003, .18)
            out[n(.07) * k:n(.07) * k + len(x)] += x
        return out * 0.45
    if name == 'tick':
        return np.sin(2 * np.pi * 2200 * t(.05)) * env(n(.05), .001, .012) * 0.5
    if name == 'ding':
        x = sum(np.sin(2 * np.pi * note(m) * t(1.2)) * w for m, w in [(84, 1), (91, .5), (96, .3)])
        return x * env(n(1.2), .003, .35) * 0.4
    if name == 'whoosh':
        x = rng.standard_normal(n(.45)); e = np.sin(np.pi * np.linspace(0, 1, n(.45))) ** 2
        return bp(x, 400, 3500) * e * 0.35
    if name == 'splash':
        x = rng.standard_normal(n(.5)); return bp(x, 800, 6000) * env(n(.5), .01, .12) * 0.5
    if name == 'bonk':
        f = 220 * np.exp(-t(.25) * 6) + 120; return np.sin(np.cumsum(2 * np.pi * f / SR)) * env(n(.25), .002, .08) * 0.9
    if name in ('thud', 'stamp'):
        f = 110 * np.exp(-t(.5) * 5) + 45; x = np.sin(np.cumsum(2 * np.pi * f / SR)) * env(n(.5), .002, .18)
        nz = lp(rng.standard_normal(n(.5)), 1800) * env(n(.5), .001, .03)
        return (x + nz * (1.5 if name == 'stamp' else 0.5)) * 0.9
    if name == 'rewind':
        d = 1.6; f = 1200 - 900 * np.linspace(0, 1, n(d)) + 200 * np.sin(2 * np.pi * 14 * t(d))
        x = signal.sawtooth(np.cumsum(2 * np.pi * f / SR)) * 0.25 + bp(rng.standard_normal(n(d)), 1000, 5000) * 0.3
        return lp(x, 4000) * np.sin(np.pi * np.linspace(0, 1, n(d))) * 0.4
    if name in ('sweep_down', 'sweep_up'):
        d = 1.4; f = np.linspace(500, 120, n(d)) if name == 'sweep_down' else np.linspace(120, 500, n(d))
        x = np.sin(np.cumsum(2 * np.pi * f / SR)) + 0.4 * bp(rng.standard_normal(n(d)), 200, 1200)
        return x * np.sin(np.pi * np.linspace(0, 1, n(d))) * 0.3
    if name == 'sad':
        out = np.zeros(n(1.4))
        for i, m in enumerate([67, 66, 65]):
            x = signal.square(2 * np.pi * note(m - 12) * t(.4), .3) * env(n(.4), .01, .2)
            out[n(.3 * i):n(.3 * i) + len(x)] += lp(x, 1500)
        return out * 0.22
    if name == 'bubble':
        f = 400 + 900 * t(.18) / .18; return np.sin(np.cumsum(2 * np.pi * f / SR)) * env(n(.18), .003, .06) * 0.6
    raise KeyError(name)
def music(dur, bpm=96):
    N = int(dur * SR); out = np.zeros(N + SR * 14); beat = 60 / bpm
    prog = [(50, [62, 65, 69]), (46, [62, 65, 70]), (53, [60, 65, 69]), (48, [60, 64, 67])]
    bar = 4 * beat; i = 0; tt = 0.0
    arp = [0, 1, 2, 1, 2, 0, 1, 2]
    while tt < dur + 1:
        root, ch = prog[i % 4]; s0 = int(tt * SR); L = int(2 * bar * SR); tl = np.arange(L) / SR
        pad = sum(np.sin(2 * np.pi * note(m) * tl + k) + 0.25 * np.sin(4 * np.pi * note(m) * tl) for k, m in enumerate(ch))
        pad *= np.minimum(1, tl / 0.6) * np.minimum(1, (L / SR - tl) / 0.6) * 0.05
        bass = np.sin(2 * np.pi * note(root - 12) * tl) * 0.11 * (0.6 + 0.4 * np.cos(2 * np.pi * tl / beat))
        out[s0:s0 + L] += pad + bass
        for k in range(16):
            m = ch[arp[k % 8]] + 12; st = s0 + int(k * beat / 2 * SR); nn = int(0.5 * SR); tn = np.arange(nn) / SR
            x = (np.sin(2 * np.pi * note(m) * tn) + 0.2 * np.sin(2 * np.pi * 3.01 * note(m) * tn)) * np.exp(-tn / 0.16) * 0.07
            out[st:st + nn] += x
        # soft shaker
        for k in range(16):
            st = s0 + int((k + 0.5) * beat / 2 * SR); nn = int(.05 * SR)
            out[st:st + nn] += hp(rng.standard_normal(nn), 6000) * np.exp(-np.arange(nn) / SR / .015) * 0.015
        tt += 2 * bar; i += 1
    out = lp(out[:N], 7000)
    fo = int(2.0 * SR); out[-fo:] *= np.linspace(1, 0, fo)
    return out
def read_wav(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if w.getnchannels() == 2: a = a.reshape(-1, 2).mean(1)
    assert w.getframerate() == SR; return a
def write_wav(p, x):
    x = np.clip(x, -1, 1); w = wave.open(p, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype(np.int16).tobytes()); w.close()
if __name__ == '__main__':
    proj = os.path.abspath(sys.argv[1])
    sp = importlib.util.spec_from_file_location('video', os.path.join(proj, 'video.py')); V = importlib.util.module_from_spec(sp); sp.loader.exec_module(V)
    vo = read_wav(os.path.join(proj, 'vo.wav')); N = int(V.TAIL * SR)
    vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
    m = music(V.TAIL)
    e = np.convolve(np.abs(vo), np.ones(int(.3 * SR)) / int(.3 * SR), 'same')
    duck = 1 - 0.45 * np.clip(e / 0.05, 0, 1)
    fx = np.zeros(N)
    for t, nm in V.SFX:
        x = sfx(nm); s0 = int(t * SR); L = min(len(x), N - s0)
        if L > 0: fx[s0:s0 + L] += x[:L]
    mix = vo * 1.0 + m * 0.55 * duck + fx * 0.32
    write_wav(os.path.join(proj, 'mix_raw.wav'), mix * 0.8)
    print('mix ok')
