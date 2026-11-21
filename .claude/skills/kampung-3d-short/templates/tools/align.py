# Forced alignment without an ASR model: silences in the VO are matched to punctuation in the transcript (DP),
# words inside each speech chunk are spread by syllable count (Indonesian is syllable-timed).
import json, re, subprocess, sys, math
wav, txt, out = sys.argv[1:4]
spoken = open(txt).read().split()
def syl(w):
    w = re.sub(r"[^a-z]", "", w.lower())
    w = re.sub(r"(ai|au|oi)(?![aiueo])", "a", w)
    return max(1, len(re.findall(r"[aiueo]+", w)))
words = [{"w": w, "s": syl(w), "p": (3 if w[-1] in ".?!" else 2 if w[-1] in ",:;" else 1 if w.endswith("...") else 0)} for w in spoken]
for w in words:
    if w["w"].endswith("..."): w["p"] = 3
import wave, numpy as np
_w = wave.open(wav); _x = np.frombuffer(_w.readframes(_w.getnframes()), np.int16) / 32768; _sr = _w.getframerate()
dur = len(_x) / _sr
H = int(_sr * 0.01); _e = 20 * np.log10(np.sqrt(np.convolve(_x ** 2, np.ones(2 * H) / (2 * H), "same")[::H]) + 1e-9)
quiet = _e < -38
runs, i = [], 0
while i < len(quiet):
    if quiet[i]:
        j = i
        while j < len(quiet) and quiet[j]: j += 1
        runs.append((i * 0.01, j * 0.01)); i = j
    else: i += 1
t0 = runs[0][1] if runs and runs[0][0] == 0 else 0.0
t1 = runs[-1][0] if runs and runs[-1][1] >= dur - 0.02 else dur
gaps = [(a, b) for a, b in runs if b - a >= 0.12 and a > t0 and b < t1]
# speech chunks between gaps; DP: choose subset of gaps as word boundaries
N, G = len(words), len(gaps)
cum = [0]
for w in words: cum.append(cum[-1] + w["s"])
rate = cum[-1] / (t1 - t0 - sum(e - s for s, e in gaps))
INF = 1e18
# state: gap g used as boundary after word j. dp[g][j]
bounds = [t0] + [None] * G
import functools
ends = [g[0] for g in gaps] + [t1]; starts = [t0] + [g[1] for g in gaps]
@functools.lru_cache(None)
def best(g, j):  # chunk starts at starts[g], words from j; returns (cost, plan)
    if j == N: return (0 if g == G + 1 else INF, ())
    if g > G: return (INF, ())
    res = (INF, ())
    # option: skip gap g (merge chunk g with next) handled by letting chunk span several gaps
    for h in range(g, G + 1):  # chunk spans starts[g]..ends[h]
        span = ends[h] - starts[g] - sum(gaps[k][1] - gaps[k][0] for k in range(g, h))
        skipped = h - g
        for k in range(j + 1, N + 1):
            if h < G and k == N: continue
            if h == G and k != N: continue
            s = cum[k] - cum[j]
            r = s / max(span, 0.05)
            c = 4 * min(1, s / 8) * math.log(r / rate) ** 2 + (0 if words[k - 1]["p"] or k == N else 3) + 0.6 * skipped * 0
            # skipped gaps should not sit on strong punctuation: small penalty per skipped gap
            c += sum(0.3 + 8 * max(0, (gaps[x][1] - gaps[x][0]) - 0.15) for x in range(g, h))
            sub = best(h + 1, k)
            if sub[0] + c < res[0]: res = (sub[0] + c, ((g, h, j, k),) + sub[1])
    return res
cost, plan = best(0, 0)
outw = []
for g, h, j, k in plan:
    segs = [(starts[g], ends[g])] + [(starts[x], ends[x]) for x in range(g + 1, h + 1)]
    total = sum(b - a for a, b in segs); s = cum[k] - cum[j]
    def at(u):  # map fraction of speech time into real time across segments
        x = u * total
        for a, b in segs:
            if x <= b - a + 1e-9: return a + x
            x -= b - a
        return segs[-1][1]
    acc = 0
    for i in range(j, k):
        a = at(acc / s); acc += words[i]["s"]; b = at(acc / s)
        outw.append({"word": words[i]["w"], "start": round(a, 3), "end": round(b, 3)})
json.dump({"duration": dur, "words": outw}, open(out, "w"), ensure_ascii=False, indent=0)
print("cost", round(cost, 2), "rate", round(rate, 2), "syl/s; chunks:")
for g, h, j, k in plan:
    print(f"{starts[g]:6.2f}-{ends[h]:6.2f}  ", " ".join(w["w"] for w in words[j:k]))
