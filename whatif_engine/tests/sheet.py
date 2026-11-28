import sys,subprocess,os
from PIL import Image,ImageDraw
vid,out=sys.argv[1],sys.argv[2]; ts=[float(x) for x in sys.argv[3].split(',')]; ref=len(sys.argv)>4
W,H=270,480; o=Image.new('RGB',(W*len(ts),H*(2 if ref else 1))); d=ImageDraw.Draw(o); tmp=out+'.png'
for i,t in enumerate(ts):
    subprocess.run(["ffmpeg","-v","error","-y","-ss",str(t),"-i",vid,"-frames:v","1",tmp]); o.paste(Image.open(tmp).resize((W,H)),(i*W,0)); d.text((i*W+4,4),f"{t}s",fill='yellow')
    if ref:
        rt=[float(x) for x in sys.argv[4].split(',')][i]
        subprocess.run(["ffmpeg","-v","error","-y","-ss",str(rt),"-i",sys.argv[5],"-frames:v","1",tmp]); o.paste(Image.open(tmp).resize((W,H)),(i*W,H)); d.text((i*W+4,H+4),f"REF {rt}s",fill='yellow')
os.remove(tmp); o.save(out)
