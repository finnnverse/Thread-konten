import sys, time, subprocess, numpy as np, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.tiles import TileSource
from engine.geo import Countries
from engine.camera import Camera
from engine.maprender import MapRenderer, ring_mask, apply_opaque_fill, apply_tint_fill
from engine.text import draw_caption
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W,H,FPS=1080,1920,60; DUR=float(sys.argv[1]) if len(sys.argv)>1 else 8
from engine.destreak import CleanTiles
raw=TileSource(os.path.join(ROOT,"cache/s2_2016")); C=Countries(os.path.join(ROOT,"data"))
tiles=CleanTiles(raw,os.path.join(ROOT,"cache/s2_clean"),land=Countries(os.path.join(ROOT,"data"),"50m"))
cam=Camera([dict(t=0,lon=157,lat=46,width_km=1500,roll=-8,tilt=8),
            dict(t=1.2,lon=108,lat=50,width_km=9000,roll=2,tilt=12),
            dict(t=3.2,lon=100,lat=51,width_km=10500,roll=-2,tilt=12),
            dict(t=4.8,lon=175,lat=55,width_km=8000,roll=4,tilt=10),
            dict(t=6.4,lon=-100,lat=45,width_km=6000,roll=-3,tilt=10),
            dict(t=8,lon=-97,lat=42,width_km=4200,roll=-6,tilt=8)])
mr=MapRenderer(tiles)
RU=C.rings("RUS"); US=C.rings("USA",exclude_bbox=(-180,15,-129,75)); US=[r for r in US if r["lat"].mean()>22]
caps=[(0,0.9,"What would happen"),(0.9,2.0,"if a whole region"),(2.0,3.3,"lit up blue?"),(3.3,5.0,"and the other side"),(5.0,8,"turned red.")]
# prefetch
t0=time.time(); keys=set()
for f in range(0,int(DUR*FPS),3):
    M,s=cam.matrix(f/FPS); keys.update(mr.tiles_for(M,s))
print("tiles",len(keys),"new",tiles.prefetch(keys),f"{time.time()-t0:.1f}s")
out=os.path.join(ROOT,"out/test_map.mp4")
p=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",out],stdin=subprocess.PIPE)
t0=time.time(); import collections; prof=collections.Counter()
for f in range(int(DUR*FPS)):
    t=f/FPS; M,s=cam.matrix(t)
    a_=time.time(); img=mr.base(M,s); prof["base"]+=time.time()-a_; a_=time.time()
    img=apply_opaque_fill(img, ring_mask(cam,t,RU,W,H,select=lambda r: r["mainland"] or r["lat"].mean()<66,M=M), mr.noise(M))
    img=apply_opaque_fill(img, ring_mask(cam,t,RU,W,H,select=lambda r: (not r["mainland"]) and r["lat"].mean()>=66,M=M), mr.noise(M), color="#3FD0FF", inset_px=0)
    a=np.clip((t-5.6)/0.7,0,1); a=1-(1-a)**2
    img=apply_tint_fill(img, ring_mask(cam,t,US,W,H,M=M), amount=a)
    prof["fills"]+=time.time()-a_; a_=time.time()
    img*=mr.vignette
    for c0,c1,tx in caps:
        if c0<=t<c1: img=draw_caption(img,tx)
    prof["rest"]+=time.time()-a_; a_=time.time()
    p.stdin.write((np.clip(img,0,1)*255+0.5).astype(np.uint8).tobytes())
p.stdin.close(); p.wait(); print(dict(prof)); print(f"render {time.time()-t0:.1f}s for {int(DUR*FPS)} frames")
