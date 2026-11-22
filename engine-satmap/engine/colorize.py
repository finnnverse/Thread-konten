import os, sys, math, numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from basemap import LD, inv_lat
def lerp(a,b,t): return a+(b-a)*t[...,None]
def C(*c): return np.array(c,np.float32)
FOREST=C(34,70,36); RAIN=C(26,58,30); SAV=C(150,138,82); DRY=C(178,152,98); DES=C(156,98,60); MTN=C(112,98,80)
def noise(H,W,seed,oct=5,base=64):
    rng=np.random.default_rng(seed); out=np.zeros((H,W),np.float32); amp=1; tot=0
    for o in range(oct):
        s=max(2,base>>o); g=rng.random((H//s+3,W//s+3)).astype(np.float32)
        z=ndimage.zoom(g,s,order=3)[:H,:W]; out+=amp*z; tot+=amp; amp*=0.55
    return (out/tot-0.5)*2
def grids(meta,H,W):
    z,x0,y0,_,_=meta; n=256*2**z
    lon=(x0+np.arange(W)+0.5)/n*360-180
    lat=np.array([inv_lat(y0+i+0.5,z) for i in range(H)],np.float32)
    return np.meshgrid(lon.astype(np.float32),lat)
def aridity(LON,LAT,nz):
    A=np.full(LON.shape,0.08,np.float32)
    aus=(LAT<-10.8)&(LON>112)&(LON<155)
    a=np.clip((-LAT-12)/8,0.3,0.85)
    east=np.clip((LON-145.5)/2.5,0,1)*np.clip((-LAT-10)/3,0,1)*np.clip((-15+(-LAT))/-1+20,0,1)
    a=a*(1-0.65*east)
    A[aus]=a[aus]
    nt=(LON>115.8)&(LON<127.5)&(LAT<-7.6)&(LAT>-11.5)
    A[nt]=0.42
    kom=(LON>119.2)&(LON<119.9)&(LAT<-8.3)&(LAT>-8.95)
    A[kom]=0.62
    ej=(LON>111)&(LON<115.8)&(LAT<-6.5)&(LAT>-9)
    A[ej]=0.2
    A=ndimage.gaussian_filter(A,max(1,LON.shape[1]/400))
    return np.clip(A+nz*0.26,0,1)
def land_color(e,A,nz,shade):
    A=A*(1-0.6*np.clip((e-150)/800,0,1))
    t1=np.clip(A*2,0,1); t2=np.clip(A*2-1,0,1)
    c=lerp(lerp(FOREST,SAV,t1),DES,t2)
    wet=np.clip(1-A*3,0,1)*np.clip(nz+0.3,0,1)*0.5
    c=lerp(c,RAIN,wet)
    c=lerp(c,DRY,np.clip((A-0.4)*2,0,1)*np.clip(nz,0,1)*0.6)
    c=lerp(c,MTN,np.clip((e-900)/1400,0,1)*0.8)
    return c*shade[...,None]
SEA=[(0,C(72,168,176)),(12,C(44,140,168)),(40,C(28,118,160)),(120,C(20,88,138)),(400,C(16,62,110)),(1500,C(12,44,86)),(5000,C(9,30,62))]
def sea_color(d):
    c=np.zeros(d.shape+(3,),np.float32)
    for (d0,c0),(d1,c1) in zip(SEA,SEA[1:]):
        m=(d>=d0)&(d<d1); t=((d-d0)/(d1-d0))[m]; c[m]=c0+(c1-c0)*t[:,None]
    c[d>=SEA[-1][0]]=SEA[-1][1]; return c
def hill(e,z,lat,exag):
    px=156543.0*np.cos(np.radians(lat))/2**z
    gy,gx=np.gradient(e.astype(np.float32))
    gx=gx/px*exag; gy=gy/px*exag
    lx,ly,lz=-0.6,-0.6,0.53
    n=np.sqrt(gx*gx+gy*gy+1)
    s=(-gx*lx-gy*ly+lz)/n
    return s/lz
def run(name):
    meta=list(map(int,open(os.path.join(LD,name+'_meta.txt')).read().split()))
    e=np.load(os.path.join(LD,name+'_elev.npy')).astype(np.float32); H,W=e.shape; z=meta[0]
    e=np.clip(ndimage.median_filter(e,3),-11000,4200)
    LON,LAT=grids(meta,H,W)
    nz=noise(H,W,z,5,max(8,int(W/40)))*0.7+noise(H,W,z+9,3,6)*0.3
    A=aridity(LON,LAT,nz)
    ex={5:6.0,6:5.0,7:4.0,9:2.2,10:1.6}[z]
    hs=hill(np.clip(e,0,None),z,LAT,ex); shade=np.clip(0.55+0.5*hs,0.45,1.3)
    land=land_color(e,A,nz,shade*(1+0.06*nz))
    bh=hill(np.clip(e,None,0),z,LAT,ex*0.25); bshade=np.clip(0.8+0.25*bh,0.6,1.15)
    sea=sea_color(np.clip(-e,0,None))*bshade[...,None]*(1+0.03*nz[...,None])
    # coastal shallow glow
    island=e>0
    out=np.where(island[...,None],land,sea)
    # soft coast antialias
    out=ndimage.gaussian_filter(out,(0.6,0.6,0))
    # grade: slight haze + desat
    g=out.mean(-1,keepdims=True); out=g+(out-g)*0.92; out=out*0.95+C(8,14,22)*0.5
    Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save(os.path.join(LD,name+'_rgb.png'))
    # exposed shelf color (for sea-level drop)
    sh_shade=np.clip(0.7+0.4*hill(e,z,LAT,ex*0.6),0.5,1.2)
    shelf=land_color(np.zeros_like(e),np.clip(A*0.8+0.1,0,1),nz,sh_shade)
    g=shelf.mean(-1,keepdims=True); shelf=g+(shelf-g)*0.92; shelf=shelf*0.95+C(8,14,22)*0.5
    Image.fromarray(np.clip(shelf,0,255).astype(np.uint8)).save(os.path.join(LD,name+'_shelf.png'))
    np.save(os.path.join(LD,name+'_e.npy'),e.astype(np.float16))
    print(name,'ok')
if __name__=='__main__':
    for n in sys.argv[1:] or ['z5','z7','z9','z10']: run(n)
