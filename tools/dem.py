import math, glob, json
def load(kind, z):
    tiles={}
    for f in glob.glob(f"{kind}_{z}_*.txt"):
        _,_,x,y=f[:-4].split('_')[-4:] if kind=='dem5a' else ('','',*f[:-4].split('_')[-2:])
        x,y=int(f[:-4].split('_')[-2]),int(f[:-4].split('_')[-1])
        rows=[[float(v) if v not in ('e','') else None for v in l.strip().split(',')] for l in open(f) if l.strip()]
        tiles[(x,y)]=rows
    return tiles
T5=load('dem5a',15); T13=load('dem',13)
def px(lat,lon,z):
    n=2**z; x=(lon+180)/360*n; y=(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
    return x*256,y*256
def raw(tiles,z,X,Y):
    t=tiles.get((X//256,Y//256))
    if not t: return None
    return t[Y%256][X%256]
def elev(lat,lon):
    for tiles,z in ((T5,15),(T13,13)):
        X,Y=px(lat,lon,z); X-=0.5; Y-=0.5
        x0,y0=int(math.floor(X)),int(math.floor(Y)); fx,fy=X-x0,Y-y0
        v=[raw(tiles,z,x0,y0),raw(tiles,z,x0+1,y0),raw(tiles,z,x0,y0+1),raw(tiles,z,x0+1,y0+1)]
        if None in v: continue
        return (v[0]*(1-fx)+v[1]*fx)*(1-fy)+(v[2]*(1-fx)+v[3]*fx)*fy
    return None
LAT0,LON0=36.6630,137.8250
def xy(lat,lon):  # local meters: x east, z south
    return (lon-LON0)*111320*math.cos(math.radians(LAT0)), -(lat-LAT0)*110574
