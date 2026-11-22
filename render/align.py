import re, json, subprocess, sys
AUD = sys.argv[1]; SCRIPT = sys.argv[2]; OUT = sys.argv[3]
txt = open(SCRIPT).read()
secs = re.findall(r'\[(INTRO|BAB \d|PENUTUP)\]\n(.+?)(?=\n\n\[|\Z)', txt, re.S)
words = []
for name, body in secs:
    for w in body.split():
        words.append({'sec': name, 'w': w})
def syl(w): return max(1, len(re.findall(r'[aiueoAIUEO]', w)))
# pauses
log = subprocess.run(['ffmpeg', '-hide_banner', '-i', AUD, '-af', 'silencedetect=noise=-35dB:d=0.25', '-f', 'null', '-'], capture_output=True, text=True).stderr
ss = [float(x) for x in re.findall(r'silence_start: ([0-9.]+)', log)]
se = [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', log)]
dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', AUD]))
pauses = list(zip(ss, se))
# speech intervals
iv = []; t = 0
if pauses and pauses[0][0] < 0.05: t = pauses[0][1]; pauses = pauses[1:]
for a, b in pauses:
    if a > t: iv.append((t, a))
    t = b
if t < dur: iv.append((t, dur))
speech = sum(b - a for a, b in iv)
def s2t(s):  # speech clock -> real time
    for a, b in iv:
        if s <= b - a: return a + s
        s -= b - a
    return iv[-1][1]
# boundary candidates: words ending with sentence punctuation get weight; snap to pauses
tot = sum(syl(w['w']) for w in words); acc = 0
for w in words:
    w['s0'] = acc / tot * speech; acc += syl(w['w']); w['s1'] = acc / tot * speech
# refine: anchor sentence ends to pauses using DP over sentence ends
ends = [i for i, w in enumerate(words) if re.search(r'[.?!:]$', w['w'])]
P = [(a, b) for a, b in pauses]
# pause speech-clock position
pc = []; s = 0; j = 0
for a, b in iv:
    s += b - a; pc.append(s)  # pause after interval k at speech-clock s
pc = pc[:-1]
# DP: assign each sentence end to pause index or None, monotone
import math
n, m = len(ends), len(pc)
INF = 1e9
best = [[INF] * (m + 1) for _ in range(n + 1)]; bk = [[None] * (m + 1) for _ in range(n + 1)]
best[0][0] = 0
for i in range(n):
    pred = words[ends[i]]['s1']
    for k in range(m + 1):
        if best[i][k] >= INF: continue
        # skip pauses (unassigned pause cost)
        # option: no pause for this end
        c = best[i][k] + 1.2
        if c < best[i + 1][k]: best[i + 1][k] = c; bk[i + 1][k] = (k, None)
        for k2 in range(k, min(m, k + 6)):
            c = best[i][k] + abs(pc[k2] - pred) + 0.5 * (k2 - k)
            if c < best[i + 1][k2 + 1]: best[i + 1][k2 + 1] = c; bk[i + 1][k2 + 1] = (k, k2)
k = min(range(m + 1), key=lambda k: best[n][k] + 0.5 * (m - k))
assign = [None] * n; i = n
while i > 0:
    pk, k2 = bk[i][k]; assign[i - 1] = k2; k = pk; i -= 1
# anchors in speech clock: (word index end, speech clock)
anchors = [(-1, 0.0)]
for i, k2 in enumerate(assign):
    if k2 is not None: anchors.append((ends[i], pc[k2]))
anchors.append((len(words) - 1, speech))
for (i0, s0), (i1, s1) in zip(anchors, anchors[1:]):
    seg = words[i0 + 1:i1 + 1]; sy = sum(syl(w['w']) for w in seg) or 1; a = 0
    for w in seg:
        w['s0'] = s0 + a / sy * (s1 - s0); a += syl(w['w']); w['s1'] = s0 + a / sy * (s1 - s0)
for w in words:
    w['t0'] = round(s2t(w['s0'] + 1e-4), 3); w['t1'] = round(s2t(w['s1'] - 1e-4), 3)
json.dump({'dur': dur, 'words': [{'sec': w['sec'], 'w': w['w'], 't0': w['t0'], 't1': w['t1']} for w in words]}, open(OUT, 'w'), ensure_ascii=False, indent=0)
cur = None
for w in words:
    if w['sec'] != cur: cur = w['sec']; print(cur, w['t0'])
print('dur', dur, 'speech', round(speech, 2), 'assigned', sum(a is not None for a in assign), '/', n, 'pauses', m)
