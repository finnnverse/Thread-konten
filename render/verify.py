import os, json, subprocess, sys
import scene as S, elements as E
F = sys.argv[1]; OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)
print(run(['ffprobe', '-v', 'error', '-count_frames', '-show_entries', 'format=duration:stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_read_frames,sample_rate,channels,duration', '-of', 'compact', F]).stdout)
r = run(['ffmpeg', '-hide_banner', '-i', F, '-vf', 'blackdetect=d=0.5:pix_th=0.10,freezedetect=n=0.003:d=1.5', '-af', 'volumedetect', '-f', 'null', '-']).stderr
for l in r.splitlines():
    if any(k in l for k in ('blackdetect', 'freeze_', 'max_volume', 'mean_volume')): print(l.strip())
r = run(['ffmpeg', '-hide_banner', '-i', F, '-af', 'loudnorm=I=-16:TP=-1:print_format=json', '-vn', '-f', 'null', '-']).stderr
m = json.loads(r[r.rindex('{'):r.rindex('}') + 1]); print('loudnorm input_i', m['input_i'], 'input_tp', m['input_tp'], 'lra', m['input_lra'])
times = {'t002_intro': 2.0}
for i, s in enumerate([S.S1, S.S2, S.S3, S.S4, S.S5, S.S6, S.S7], 1): times[f'bab{i}_start'] = s + .6
for e in S.EL + [S.DIAG_COUNTER]:
    if isinstance(e, E.Counter): times[f'counter_{e.v}'] = min(e.t1 - .05, e.t0 + e.spin + .3)
times.update({'dive_cairo': 52.3, 'dive_giza': 54.2, 'dive_suez': 81.4, 'dive_abusimbel': 117.6, 'penutup': S.SP + 2.5, 'endscreen': S.END0 + 2, 'last_frame': S.DUR - 1 / 30})
for k, t in sorted(times.items(), key=lambda x: x[1]):
    run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{t:.3f}', '-i', F, '-frames:v', '1', f'{OUT}/{t:07.2f}_{k}.png'])
print('extracted', len(times))
json.dump(times, open(f'{OUT}/times.json', 'w'), indent=0)
