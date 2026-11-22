import os, math, sys, numpy as np, concurrent.futures as cf, subprocess
from PIL import Image
S=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TD=os.path.join(S,'tiles'); LD=os.path.join(S,'levels')
os.makedirs(TD,exist_ok=True); os.makedirs(LD,exist_ok=True)
URL='https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
def mx(lon,z): return (lon+180)/360*256*2**z
def my(lat,z):
    r=math.radians(lat); return (1-math.log(math.tan(r)+1/math.cos(r))/math.pi)/2*256*2**z
def inv_lat(y,z):
    n=math.pi-2*math.pi*y/(256*2**z); return math.degrees(math.atan(math.sinh(n)))
# name: z, lon0, lon1, latN, latS
LEVELS={'z5':(5,84,166,30,-56),'z6':(6,95,162,20,-48),'z7':(7,100,156,8,-30),'z9':(9,109.5,128.5,-0.5,-16.8),'z10':(10,117.6,122.4,-5.9,-11.4)}
def fetch(a):
    z,x,y=a; p=os.path.join(TD,f'{z}_{x}_{y}.png')
    if not os.path.exists(p) or os.path.getsize(p)<100:
        for i in range(4):
            r=subprocess.run(['curl','-s','-f','-m','40','-o',p,URL.format(z=z,x=x,y=y)])
            if r.returncode==0: break
    return p
def build(name):
    z,l0,l1,la,lb=LEVELS[name]
    x0,x1=int(mx(l0,z)//256),int(mx(l1,z)//256); y0,y1=int(my(la,z)//256),int(my(lb,z)//256)
    jobs=[(z,x,y) for x in range(x0,x1+1) for y in range(y0,y1+1)]
    with cf.ThreadPoolExecutor(16) as ex: list(ex.map(fetch,jobs))
    W=(x1-x0+1)*256; H=(y1-y0+1)*256; E=np.zeros((H,W),np.float32)
    for (zz,x,y) in jobs:
        a=np.asarray(Image.open(os.path.join(TD,f'{z}_{x}_{y}.png')).convert('RGB')).astype(np.float32)
        E[(y-y0)*256:(y-y0+1)*256,(x-x0)*256:(x-x0+1)*256]=a[...,0]*256+a[...,1]+a[...,2]/256-32768
    np.save(os.path.join(LD,name+'_elev.npy'),E.astype(np.float16))
    with open(os.path.join(LD,name+'_meta.txt'),'w') as f: f.write(f'{z} {x0*256} {y0*256} {W} {H}')
    print(name,W,H,len(jobs),'tiles',E.min(),E.max())
if __name__=='__main__':
    for n in sys.argv[1:] or LEVELS: build(n)
