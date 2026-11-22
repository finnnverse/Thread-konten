"""Synthetic music pad + SFX track (fixed seed) and final mix with ffmpeg."""
import os, sys, json, math, subprocess, wave
import numpy as np
os.environ.setdefault('DUR', '182')
import scene as S
import elements as E

SR = 48000; DUR = S.DUR; N = SR * DUR
OUT = sys.argv[1]; VO = sys.argv[2]
rng = np.random.default_rng(20261122)


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d)


def lp(x, fc):
    # one-pole low-pass
    a = math.exp(-2 * math.pi * fc / SR); y = np.empty_like(x); s = 0.0
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x)


def bp_noise(n, f0, f1, q=1.5):
    from scipy.signal import butter, sosfilt
    x = rng.standard_normal(n)
    out = np.zeros(n); seg = 1024
    for i in range(0, n, seg):
        f = f0 + (f1 - f0) * (i / n)
        sos = butter(2, [max(30, f / q), min(SR / 2 - 100, f * q)], btype='band', fs=SR, output='sos')
        out[i:i + seg] = sosfilt(sos, x[i:i + seg])
    return out


def make(kind):
    t = lambda n: np.arange(n) / SR
    if kind in ('whoosh', 'swish'):
        n = int(SR * (1.0 if kind == 'whoosh' else .8))
        x = bp_noise(n, 300 if kind == 'whoosh' else 700, 2600 if kind == 'whoosh' else 4200, 1.6)
        e = np.sin(np.pi * np.clip(t(n) / (n / SR), 0, 1)) ** 2.2
        e = np.where(t(n) < .35, (t(n) / .35) ** 2, np.exp(-(t(n) - .35) / .22))
        return x * e
    if kind == 'pop':
        n = int(SR * .12); tt = t(n); f = 950 * np.exp(-tt * 28) + 260
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, .035)
    if kind == 'blip':
        n = int(SR * .14); tt = t(n)
        return (np.sin(2 * np.pi * 1320 * tt) * (tt < .06) + np.sin(2 * np.pi * 1760 * tt) * (tt >= .06)) * env(n, .002, .05) * .8
    if kind == 'tick':
        n = int(SR * 1.15); x = np.zeros(n); tt = 0.0; k = 0
        while tt < 1.05:
            i = int(tt * SR); m = int(SR * .012)
            x[i:i + m] += np.sin(2 * np.pi * 2400 * np.arange(m) / SR) * np.exp(-np.arange(m) / SR / .003) * (1 - tt * .5)
            tt += .045 + .12 * (tt / 1.05) ** 2; k += 1
        return x * .7
    if kind in ('impact', 'thump'):
        n = int(SR * .7); tt = t(n); f0 = 70 if kind == 'impact' else 95
        body = np.sin(2 * np.pi * np.cumsum(f0 + 60 * np.exp(-tt * 30)) / SR) * env(n, .002, .18)
        nz = lp(rng.standard_normal(n), 1800) * env(n, .001, .04)
        return body + nz * .6
    if kind == 'riser':
        n = int(SR * 1.2); tt = t(n)
        x = bp_noise(n, 400, 5000, 1.4) * .7 + np.sin(2 * np.pi * np.cumsum(200 + 900 * (tt / 1.2) ** 2) / SR) * .35
        return x * (tt / 1.2) ** 2.2 * np.where(tt > 1.15, (1.2 - tt) / .05, 1)
    if kind == 'ding':
        n = int(SR * 2.2); tt = t(n)
        return sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt / d) for f, a, d in ((1046.5, 1, .9), (2093, .4, .5), (2900, .25, .3), (3920, .12, .2))) * env(n, .003, 5)
    if kind == 'click':
        n = int(SR * .05); return lp(rng.standard_normal(n), 3500) * env(n, .0005, .008) * 1.5
    raise KeyError(kind)


VARIANT = {'pop': ['pop', 'blip'], 'whoosh': ['whoosh', 'swish'], 'impact': ['impact', 'thump']}
SAMPLES = {k: make(k) for k in ['whoosh', 'swish', 'pop', 'blip', 'tick', 'impact', 'thump', 'riser', 'ding', 'click']}
for k, v in SAMPLES.items(): SAMPLES[k] = v / np.abs(v).max()

# ---- schedule: no two onsets within 1.0 s (keep higher priority), no identical sound twice in a row
ev = sorted(set(E.SFX), key=lambda e: (e[0], -e[2]))
ev = [e for e in ev if 0 <= e[0] < DUR - .5]
kept = []
for e in sorted(ev, key=lambda e: -e[2]):
    if all(abs(e[0] - k[0]) >= 1.0 for k in kept): kept.append(e)
kept.sort()
final = []; last = None
for t, kind, pr in kept:
    opts = VARIANT.get(kind, [kind])
    snd = opts[0]
    if snd == last:
        alt = [o for o in opts if o != last]
        if alt: snd = alt[0]
        else: continue  # cannot vary (e.g. tick/riser twice) -> drop
    final.append((t, snd)); last = snd

# ---- levels relative to the voice
def read_wav(p):
    d = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(d, np.float32).astype(np.float64)
vo = read_wav(VO)
vo_peak = np.percentile(np.abs(vo), 99.9)
GAIN = {'whoosh': -14, 'swish': -15, 'pop': -15, 'blip': -17, 'tick': -18, 'impact': -12, 'thump': -13, 'riser': -15, 'ding': -13, 'click': -16}
sfx = np.zeros(N)
for t, k in final:
    s = SAMPLES[k] * vo_peak * 10 ** (GAIN[k] / 20)
    i = int(round(t * SR)); j = min(N, i + len(s))
    sfx[i:j] += s[:j - i]

# ---- music pad (A minor-ish progression, 8 s per chord)
tt = np.arange(N) / SR
chords = [(57, 60, 64), (53, 57, 60), (48, 55, 60, 64), (55, 59, 62)]
mus = np.zeros((N, 2))
for ci in range(int(DUR / 8) + 1):
    notes = chords[ci % 4]; a0 = ci * 8 * SR; a1 = min(N, a0 + 9 * SR)
    if a0 >= N: break
    seg_t = np.arange(a1 - a0) / SR
    e = np.minimum(1, seg_t / 1.5) * np.minimum(1, np.maximum(0, (9 - seg_t)) / 1.5)
    for ni, m in enumerate(notes):
        f = 440 * 2 ** ((m - 69) / 12)
        for ch, det in ((0, -.12), (1, .12)):
            ph = 2 * np.pi * f * (1 + det / 100) * seg_t
            v = (np.sin(ph) + .35 * np.sin(2 * ph + .3) + .15 * np.sin(3 * ph)) * e
            mus[a0:a1, ch] += v * .16
    bass = 440 * 2 ** ((notes[0] - 12 - 69) / 12)
    mus[a0:a1] += (np.sin(2 * np.pi * bass * seg_t) * e * .22)[:, None]
lfo = .8 + .2 * np.sin(2 * np.pi * tt / 6.3)
mus *= lfo[:, None]
for ch in range(2): mus[:, ch] = lp(mus[:, ch], 1400)
mus = mus / np.abs(mus).max() * vo_peak * 10 ** (-17 / 20)

def write(p, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1: x = np.stack([x, x], 1)
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype('<i2').tobytes())
write(f'{OUT}/sfx.wav', sfx); write(f'{OUT}/music.wav', mus)
json.dump([{'t': round(t, 3), 'frame': round(t * 30), 'sfx': k} for t, k in final], open(f'{OUT}/sfx_log.json', 'w'), indent=0)
print('sfx events', len(final), 'of', len(ev), 'requested; avg gap', round((final[-1][0] - final[0][0]) / max(1, len(final) - 1), 2))

# ---- mix
D = DUR
fc = (f"[0:a]aresample={SR},aformat=channel_layouts=stereo,adelay=500|500,apad=whole_dur={D},atrim=0:{D}[vo];"
      f"[vo]asplit=2[vo1][key];"
      f"[1:a]atrim=0:{D}[m0];[m0][key]sidechaincompress=threshold=0.02:ratio=8:attack=40:release=600:makeup=1[md];"
      f"[md]afade=t=out:st={D - 2.5}:d=2.5[mf];"
      f"[2:a]atrim=0:{D}[sx];"
      f"[vo1][mf][sx]amix=inputs=3:normalize=0:duration=first[mix]")
pre = f'{OUT}/premix.wav'
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', VO, '-i', f'{OUT}/music.wav', '-i', f'{OUT}/sfx.wav', '-filter_complex', fc, '-map', '[mix]', '-ar', str(SR), pre], check=True)
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', pre, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
m = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
ln = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
      f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', pre, '-af', ln + f',aresample={SR}', '-ar', str(SR), '-t', str(D), f'{OUT}/final_audio.wav'], check=True)
print('audio done')
