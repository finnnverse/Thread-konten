"""Synthetic, copyright-free soundtrack + SFX + mix (measured targets from the reference):
 - music: dark cinematic pad + sub-bass, chord change every ~1.3 s (~92 BPM half-bar), wide stereo,
   ~-18 dB under VO, ducked 5 dB while VO speaks
 - SFX: whoosh on launches / whip moves (broadband 0.5-1.5 s), alarm ~1.3 kHz on warning cards,
   sub boom at 0 s, soft pops for stickers/bursts, shimmer for neon labels
 - master: -14 LUFS integrated, true peak <= -1 dBTP (ffmpeg loudnorm, 2-pass)
"""
import json, math, os, subprocess, tempfile, wave
import numpy as np

SR = 48000


def _adsr(n, a, r):
    e = np.ones(n, np.float32); A = max(1, int(a * SR)); R = max(1, int(r * SR))
    e[:A] = np.linspace(0, 1, A); e[-R:] *= np.linspace(1, 0, R); return e


def _lp(x, cutoff):
    """one-pole low-pass (vectorised via scipy if present)."""
    from scipy.signal import lfilter
    a = math.exp(-2 * math.pi * cutoff / SR); return lfilter([1 - a], [1, -a], x).astype(np.float32)


def _bp(x, lo, hi):
    from scipy.signal import butter, sosfilt
    sos = butter(2, [lo, hi], btype="band", fs=SR, output="sos"); return sosfilt(sos, x).astype(np.float32)


# ----------------------------------------------------------------------------- music
def music(duration, bpm=92, seed=0, key=50):
    rng = np.random.default_rng(seed); n = int(duration * SR); t = np.arange(n) / SR
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    prog = [[0, 3, 7], [-4, 0, 3], [-7, -4, 0], [-5, -1, 2]]          # i - VI - iv - V (minor, dark)
    seg = 60 / bpm * 2                                                  # chord every half bar (~1.3 s)
    for k in range(int(duration / seg) + 2):
        ch = prog[(k // 2) % 4]; s0 = int(k * seg * SR); s1 = min(n, int((k + 1) * seg * SR) + int(0.4 * SR))
        if s0 >= n:
            break
        tt = np.arange(s1 - s0) / SR; env = _adsr(s1 - s0, 0.35, 0.45)
        for j, iv in enumerate(ch):
            f = 440 * 2 ** ((key + iv - 69) / 12)
            for det, side in ((-0.12, L), (0.12, R)):
                ph = rng.uniform(0, 2 * np.pi)
                saw = 2 * ((tt * f * 2 ** (det / 12) + ph / 6.283) % 1) - 1
                side[s0:s1] += 0.06 * saw * env
        fb = 440 * 2 ** ((key + ch[0] - 12 - 69) / 12)                  # sub
        sub = np.sin(2 * np.pi * fb * tt) * env * 0.22
        L[s0:s1] += sub; R[s0:s1] += sub
    L, R = _lp(L, 900), _lp(R, 900)
    pulse = np.zeros(n, np.float32); beat = 60 / bpm / 2                # soft 8th ticks
    for k in range(int(duration / beat)):
        s = int(k * beat * SR); m = min(n - s, int(0.08 * SR))
        if m > 0:
            pulse[s:s + m] += _bp(rng.standard_normal(m).astype(np.float32), 2500, 6000) * np.exp(-np.arange(m) / (0.015 * SR)) * 0.05
    trem = 0.85 + 0.15 * np.sin(2 * np.pi * t * 0.25)
    return np.stack([(L + pulse * 0.8) * trem, (R + pulse * 0.6) * trem], 1)


# ----------------------------------------------------------------------------- sfx
def whoosh(dur=1.0, rng=None):
    rng = rng or np.random.default_rng(); n = int(dur * SR); x = rng.standard_normal(n).astype(np.float32)
    env = np.sin(np.linspace(0, np.pi, n)) ** 1.6
    lo = _bp(x, 300, 1500); hi = _bp(x, 1500, 9000)
    mix = np.linspace(0, 1, n) ** 0.8
    y = (lo * (1 - mix) + hi * mix) * env
    pan = np.linspace(-0.6, 0.6, n)
    return np.stack([y * (1 - pan) * 0.5, y * (1 + pan) * 0.5], 1)


def alarm(beeps=2, f=1300):
    out = []
    for k in range(beeps):
        n = int(0.22 * SR); tt = np.arange(n) / SR
        y = np.sign(np.sin(2 * np.pi * f * tt)) * 0.25 + np.sin(2 * np.pi * f * tt) * 0.5
        out.append(y * _adsr(n, 0.005, 0.03)); out.append(np.zeros(int(0.08 * SR)))
    y = _lp(np.concatenate(out).astype(np.float32), 5000); return np.stack([y, y], 1) * 0.6


def boom(dur=1.6, rng=None):
    rng = rng or np.random.default_rng(1); n = int(dur * SR); tt = np.arange(n) / SR
    f = 55 * np.exp(-tt * 1.2) + 28; ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-tt * 2.2) + _lp(rng.standard_normal(n).astype(np.float32), 400) * np.exp(-tt * 6) * 0.6
    return np.stack([y, y], 1) * 0.9


def pop(rng=None, f=520):
    n = int(0.12 * SR); tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * (f + 600 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 35)
    return np.stack([y, y], 1) * 0.5


def shimmer(dur=0.6, rng=None):
    rng = rng or np.random.default_rng(2); n = int(dur * SR); tt = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) for f in (2093, 2637, 3136, 4186)) * 0.12
    y *= _adsr(n, 0.05, dur * 0.7)
    return np.stack([y * 0.8, y], 1)


# ----------------------------------------------------------------------------- events from project
def events_from_project(spec, cam=None, whoosh_gap=5.0, max_whoosh_per_min=6):
    """SFX plan. Whoosh is reserved for the BIG moments only (largest camera whips / first launch),
    spaced >= whoosh_gap s apart and capped per minute, so it never becomes a constant wind noise.
    Other SFX are sparse accents."""
    ev = [("boom", 0.0, -8)]
    cand = []                                                  # (priority, t)
    if cam is not None:                                        # camera whip strength
        ts = np.arange(cam.t0, cam.t1, 1 / 30); sp = []
        for t in ts:
            a, b = cam.state(t), cam.state(t + 1 / 30)
            sp.append(math.hypot(b["mx"] - a["mx"], b["my"] - a["my"]) / math.exp(a["logw"]) * 30 + abs(b["logw"] - a["logw"]) * 30)
        sp = np.array(sp)
        for i in range(1, len(sp) - 1):
            if sp[i] > 2.2 and sp[i] >= sp[i - 1] and sp[i] >= sp[i + 1]:
                cand.append((float(sp[i]), float(ts[i] - 0.45)))
    for e in spec.get("elements", []):
        if e["type"] == "tracked":
            cand.append((5.0, e["t0"] - 0.1))
    cand.sort(reverse=True)
    limit = max(1, int(round(max_whoosh_per_min * spec.get("duration", 60) / 60)))
    chosen = []
    for pr, t in cand:
        if len(chosen) >= limit:
            break
        if all(abs(t - c) >= whoosh_gap for c in chosen):
            chosen.append(t)
    ev += [("whoosh", t, -16) for t in sorted(chosen)]
    for e in spec.get("elements", []):
        ty = e["type"]
        if ty == "card":
            ev.append(("alarm", e["t_in"] + 0.15, -16))
        elif ty == "neon" and e.get("sfx", True):
            ev.append(("shimmer", e["t_in"], -20))
    # one soft pop per group of stickers appearing together (not one per sticker)
    last = -9
    for t in sorted(e["t_in"] for e in spec.get("elements", []) if e["type"] == "sticker" and e.get("t_in", -1) > 0):
        if t - last > 1.5:
            ev.append(("pop", t, -19)); last = t
    return ev


def _place(buf, x, t, gain_db):
    s = int(max(0, t) * SR); n = min(len(x), len(buf) - s)
    if n > 0:
        buf[s:s + n] += x[:n] * 10 ** (gain_db / 20)


def read_wav(path):
    tmp = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "2", "-ar", str(SR), "-c:a", "pcm_s16le", tmp], check=True)
    w = wave.open(tmp); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32768; os.remove(tmp)
    return a


def write_wav(path, a):
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()


def build_mix(duration, events, vo_path=None, out_wav="mix.wav", music_db=-18, seed=0):
    n = int(duration * SR); rng = np.random.default_rng(seed)
    vo = np.zeros((n, 2), np.float32)
    if vo_path:
        v = read_wav(vo_path)[:n]; vo[:len(v)] = v
        vo *= 0.5 / max(1e-4, np.sqrt(np.mean(vo ** 2)) / 0.1)          # VO RMS ~ -20 dBFS before master
    m = music(duration, seed=seed)[:n]
    m *= 10 ** (music_db / 20) / max(1e-4, np.sqrt(np.mean(m ** 2)) / 0.1) * 0.5
    if vo_path:                                                       # sidechain ducking (5 dB)
        env = np.sqrt(np.convolve(vo[:, 0] ** 2, np.ones(int(0.05 * SR)) / int(0.05 * SR), "same"))
        env = _lp(env, 3.0); g = 1 - (1 - 10 ** (-5 / 20)) * np.clip(env / (np.percentile(env, 90) + 1e-6), 0, 1)
        m *= g[:, None]
    sfx = np.zeros((n, 2), np.float32)
    lib = {"whoosh": lambda: whoosh(rng.uniform(0.8, 1.3), rng), "alarm": alarm, "boom": lambda: boom(rng=rng),
           "pop": lambda: pop(rng, rng.uniform(450, 650)), "shimmer": lambda: shimmer(rng=rng)}
    for name, t, gdb in events:
        x = lib[name](); x = x / max(1e-4, np.abs(x).max()) * 0.5
        _place(sfx, x, t, gdb)
    mix = vo + m + sfx
    tmp = out_wav + ".pre.wav"; write_wav(tmp, mix * 0.7)
    loudnorm(tmp, out_wav); os.remove(tmp)
    return out_wav


def loudnorm(src, dst, I=-14.0, TP=-1.0, LRA=7):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    j = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-ar", str(SR), dst], check=True)


def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(r[r.rindex("{"):r.rindex("}") + 1]); return float(j["input_i"]), float(j["input_tp"])


def mux(video, audio, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
