# usage: python3 tools/asr_words.py vo16k.wav words_raw.json [model_dir]  -> [[start,end,word],...]
# English VO: NVIDIA Parakeet TDT 0.6B v2 int8 (sherpa-onnx, GitHub release; Hugging Face is often blocked):
#   curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2 | tar xj -C models/
#   pip install sherpa-onnx ; ffmpeg -i vo.mp3 -ac 1 -ar 16000 vo16k.wav
import sys,json,sherpa_onnx as so,numpy as np,wave
d=sys.argv[3] if len(sys.argv)>3 else "models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
r=so.OfflineRecognizer.from_transducer(encoder=f"{d}/encoder.int8.onnx",decoder=f"{d}/decoder.int8.onnx",joiner=f"{d}/joiner.int8.onnx",tokens=f"{d}/tokens.txt",model_type="nemo_transducer",num_threads=4)
w=wave.open(sys.argv[1]); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; sr=16000
e=np.array([np.sqrt(np.mean(a[i:i+800]**2)) for i in range(0,len(a),800)])
cuts=[0]
while len(a)-cuts[-1]>27*sr:
    lo=(cuts[-1]+18*sr)//800; hi=(cuts[-1]+27*sr)//800; cuts.append(int((lo+np.argmin(e[lo:hi]))*800))
cuts.append(len(a)); words=[]
for c0,c1 in zip(cuts,cuts[1:]):
    s=r.create_stream(); s.accept_waveform(sr,a[c0:c1]); r.decode_stream(s); R=s.result
    cur=None
    for t,st in zip(R.tokens,R.timestamps):
        if t.startswith(' ') or t.startswith('▁') or cur is None:
            if cur: words.append(cur)
            cur=[round(c0/sr+st,2),t.strip(' ▁')]
        else: cur[1]+=t
    if cur: words.append(cur)
# end time: until next word start or energy drop
for i,wd in enumerate(words):
    nxt=words[i+1][0] if i+1<len(words) else len(a)/sr
    j=int(wd[0]*sr/800)+2; k=int(nxt*sr/800)
    while j<k and e[j]>0.02: j+=1
    wd.insert(1, round(min(nxt, j*800/sr),2))
json.dump(words,open(sys.argv[2],'w'),ensure_ascii=False)
print(len(words)); print(" ".join(f"{w[0]:.2f}:{w[2]}" for w in words))
