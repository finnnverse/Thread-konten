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



# ----------------------------------------------------------------------------- journey SFX (from map-journey-style)
def _env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))


def _hp_fft(x, cut):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= (f / cut) ** 2 / np.sqrt(1 + (f / cut) ** 4); return np.fft.irfft(X, len(x))


def _lp_fft(x, cut):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / np.sqrt(1 + (f / cut) ** 4); return np.fft.irfft(X, len(x))


def _st(y, pan=0.0):
    return np.stack([y * (1 - pan) , y * (1 + pan)], 1).astype(np.float32) * 0.7


def j_pop(freq=880):
    n = int(0.18 * SR); t = np.arange(n) / SR
    return _st((np.sin(2 * np.pi * freq * t) * 0.7 + np.sin(2 * np.pi * freq * 2 * t) * 0.2) * _env(n, 0.002, 0.05))


def j_pluck(freq=659.25):
    n = int(0.5 * SR); t = np.arange(n) / SR
    return _st(sum(np.sin(2 * np.pi * freq * k * t) / k ** 1.6 for k in range(1, 6)) * _env(n, 0.003, 0.14))


def j_ding(freq=1320):
    n = int(1.0 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2.76 * t) + 0.2 * np.sin(2 * np.pi * freq * 5.4 * t)
    return _st(s * _env(n, 0.002, 0.35) * 0.6)


def j_horn(f1=311, f2=392, dur=0.9):
    n = int(dur * SR); t = np.arange(n) / SR; saw = lambda f: 2 * ((t * f) % 1) - 1
    s = _lp_fft(saw(f1) + saw(f2) + 0.5 * saw(f1 * 2), 1800)
    return _st(s * np.minimum(1, t / 0.05) * np.minimum(1, (dur - t) / 0.15) * 0.25)


def j_clank(rng=None):
    rng = rng or np.random.default_rng(3); n = int(0.6 * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t) * a for f, a in [(220, 1), (571, .7), (1130, .5), (2340, .3)])
    return _st((s * _env(n, 0.001, 0.12) + rng.standard_normal(n) * _env(n, 0.001, 0.02) * 0.6) * 0.5)


def j_hiss(dur=0.5, rng=None):
    rng = rng or np.random.default_rng(4); n = int(dur * SR)
    return _st(_hp_fft(rng.standard_normal(n), 2500) * np.sin(np.pi * np.linspace(0, 1, n)) * 0.25, 0.2)


def j_riser(dur=1.0, rng=None):
    rng = rng or np.random.default_rng(5); n = int(dur * SR); t = np.arange(n) / SR
    f = 200 + 1400 * (t / dur) ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3 + _hp_fft(rng.standard_normal(n), 2000) * 0.15 * (t / dur)
    return _st(s * (t / dur) ** 1.5)


def j_impact():
    n = int(1.6 * SR); t = np.arange(n) / SR
    boom_ = np.sin(2 * np.pi * (55 + 40 * np.exp(-t * 12)) * t) * _env(n, 0.002, 0.45)
    sh = sum(np.sin(2 * np.pi * f * t) for f in (1568, 1976, 2349, 3136)) * _env(n, 0.003, 0.6) * 0.15
    return _st(boom_ * 0.9 + sh)


def j_thud():
    n = int(0.5 * SR); t = np.arange(n) / SR
    return _st(np.sin(2 * np.pi * (90 + 60 * np.exp(-t * 20)) * t) * _env(n, 0.002, 0.12)
               + np.sign(np.sin(2 * np.pi * 110 * t)) * _env(n, 0.002, 0.08) * 0.15)


def j_boing():
    n = int(0.45 * SR); t = np.arange(n) / SR
    f = 300 + 500 * np.exp(-t * 8) * (1 + 0.3 * np.sin(2 * np.pi * 14 * t))
    return _st(np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.003, 0.15) * 0.6)


def j_tick(freq=2400):
    """short UI click for small labels"""
    n = int(0.06 * SR); t = np.arange(n) / SR
    return _st((np.sin(2 * np.pi * freq * t) * 0.6 + np.sin(2 * np.pi * freq * 1.5 * t) * 0.3) * _env(n, 0.0005, 0.012))


def j_soft_ding(freq=1568):
    n = int(0.6 * SR); t = np.arange(n) / SR
    return _st((np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * freq * 2.0 * t)) * _env(n, 0.004, 0.18) * 0.5)


PENTA = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]

# ----------------------------------------------------------------------------- events from project
# which SFX each animation type gets (several options -> rotated so nothing repeats back to back)
SFX_MAP = {
    "card": [("alarm", 0.15, -16)],
    "neon": [("shimmer", 0.0, -20), ("hiss", 0.0, -20), ("riser_s", -0.35, -21)],
    "hero": [("hiss", -0.15, -19), ("riser_s", -0.4, -21)],
    "sticker": [("pop", 0.0, -19), ("jpop", 0.0, -20)],
    "bubble": [("boing", 0.05, -18)],
    "bursts": [("thud", 0.0, -14), ("impact_s", 0.0, -17)],
    "trail_impact": [("thud", 0.0, -15)],
    "rain": [("hiss", 0.0, -18)],
    "HL": [("pluck", 0.0, -17)], "Tint": [("pluck", 0.0, -18)],
    "Pin": [("ding", 0.0, -21)], "Check": [("ding_hi", 0.0, -18)], "Cross": [("thud", 0.0, -13)],
    "BigLabel": [("jpop", 0.0, -19), ("soft_ding", 0.0, -21), ("hiss", 0.0, -20)],
    "LeaderLabel": [("tick", 0.0, -20), ("tick_lo", 0.0, -20)], "Chip": [("soft_ding", 0.0, -20), ("tick", 0.0, -19)],
    "NeonArc": [("hiss", 0.0, -20)], "NeonLine": [("hiss", 0.0, -21)], "RouteGlow": [("riser_s", 0.0, -20)],
    "IceCube": [("clank", 0.0, -20)], "Snow": [("shimmer", 0.0, -22)], "FreezeSea": [("hiss", 0.0, -19)],
    "IceBridge": [("clank", 0.0, -19)], "SocialBadge": [("boing", 0.0, -19)], "Walker": [],
}


def events_from_project(spec, cam=None, whoosh_gap=5.0, max_whoosh_per_min=6, same_gap=1.2, min_gap=0.6, max_same_8s=2):
    """SFX plan with variety:
      - whoosh only on the biggest camera whips / tracked launches (>= whoosh_gap apart, capped per minute)
      - every animation type maps to a few candidate SFX (SFX_MAP); candidates rotate, plucks walk a
        pentatonic scale, the same SFX never plays twice within `same_gap` s and no two accents within
        `min_gap` s (lower priority one is dropped) -> no 'itu-itu saja' feeling
      - spec["sfx"] = extra manual events [[name, t, dB], ...]; any element/jfx can set "sfx": false."""
    ev = [("boom", 0.0, -8)]
    cand = []
    if cam is not None:
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
    limit = max(1, int(round(max_whoosh_per_min * spec.get("duration", 60) / 60))); chosen = []
    for pr, t in cand:
        if len(chosen) < limit and all(abs(t - c) >= whoosh_gap for c in chosen):
            chosen.append(t)
    ev += [("whoosh", t, -16) for t in sorted(chosen)]

    acc = []                                                   # (t, kind, priority)
    for e in spec.get("elements", []):
        if e.get("sfx") is False:
            continue
        ty = e["type"]
        if ty == "card": acc.append((e["t_in"], "card", 3))
        elif ty == "neon": acc.append((e["t_in"], "neon", 2))
        elif ty == "hero": acc.append((e["t_in"], "hero", 2))
        elif ty == "sticker" and e.get("t_in", -1) > 0: acc.append((e["t_in"], "bubble" if e.get("sprite") == "bubble" else "sticker", 1))
        elif ty == "bursts": acc.append((e["t0"], "bursts", 2))
        elif ty == "rain": acc.append((e["t0"], "rain", 1))
        elif ty == "trail" and e.get("impact"): acc.append((e["t0"] + e.get("dur", 1.3), "trail_impact", 1))
    for it in spec.get("jfx", []) or []:
        if it.get("sfx") is False:
            continue
        fx = it["fx"]; t0 = it.get("t0")
        if t0 is None:
            args = it.get("args", []); t0 = next((a for a in args[1:] if isinstance(a, (int, float))), None)
            if fx in ("BigLabel", "LeaderLabel", "Pin", "IceCube", "Cross") and len(args) >= 4: t0 = args[3] if fx not in ("Pin", "IceCube", "Cross") else args[2]
            if fx in ("NeonArc", "NeonLine", "IceBridge") and len(args) >= 3: t0 = args[2]
            if fx in ("Snow", "GridFinale", "Finale") and args: t0 = args[0]
            if fx in ("Check",) and len(args) >= 3: t0 = args[2]
        if t0 is None:
            continue
        if fx in ("GridFinale", "Finale"):
            tt = it.get("t_text", t0 + 0.7)
            ev.append(("riser", tt - 1.0, -16)); ev.append(("impact", tt, -11)); continue
        acc.append((float(t0), fx, 2 if fx in ("HL", "Tint", "Check", "Cross") else 1))
    acc.sort()
    rot = {}; last_by = {}; last_any = -9; pk = 0; out = []
    for t, kind, pr in acc:
        opts = SFX_MAP.get(kind, [])
        if not opts:
            continue
        k = rot.get(kind, 0); rot[kind] = k + 1
        for j in range(len(opts)):                             # pick an option not used in the last same_gap s
            name, off, gdb = opts[(k + j) % len(opts)]
            recent = sum(1 for o in out if o[0].rstrip("0123456789") == name and t - o[1] < 8.0)
            if t - last_by.get(name, -9) >= same_gap and recent < max_same_8s:
                break
        else:
            continue
        if t - last_any < min_gap and out and out[-1][3] >= pr:
            continue
        if t - last_any < min_gap and out:
            out.pop()
        if name == "pluck":
            name = f"pluck{pk % len(PENTA)}"; pk += 1
        out.append((name, t + off, gdb, pr)); last_by[opts[(k + j) % len(opts)][0]] = t; last_any = t
    ev += [(n, t, g) for n, t, g, _ in out]
    ev += [tuple(x) for x in spec.get("sfx", [])]
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
           "pop": lambda: pop(rng, rng.uniform(450, 650)), "shimmer": lambda: shimmer(rng=rng),
           "jpop": lambda: j_pop(rng.choice([880, 990, 1175])), "ding": lambda: j_ding(1320), "ding_hi": lambda: j_ding(1760),
           "horn": j_horn, "ship_horn": lambda: j_horn(147, 185, 1.2), "clank": lambda: j_clank(rng), "hiss": lambda: j_hiss(0.5, rng),
           "riser": lambda: j_riser(1.0, rng), "riser_s": lambda: j_riser(0.45, rng), "impact": j_impact,
           "impact_s": lambda: j_impact() * 0.6, "thud": j_thud, "boing": j_boing,
           "tick": lambda: j_tick(2400), "tick_lo": lambda: j_tick(1500), "soft_ding": lambda: j_soft_ding(rng.choice([1568, 1760, 1319]))}
    for i, f in enumerate(PENTA):
        lib[f"pluck{i}"] = (lambda f=f: j_pluck(f))
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
