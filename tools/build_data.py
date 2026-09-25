# 白馬五竜：国土地理院DEM + OSM から ゲーム用データを生成
import json, math, struct, random
from dem import elev, xy, LAT0, LON0

OUT = '../out/'
osm = json.load(open('osm.json'))
W = {w['id']: w for w in osm['elements']}

def way(wid):
    return [xy(p['lat'], p['lon']) for p in W[wid]['geometry']]
def ll(lat, lon): return xy(lat, lon)
def nearest(pts, p):
    return min(range(len(pts)), key=lambda i: (pts[i][0]-p[0])**2 + (pts[i][1]-p[1])**2)

# ---------- ルート定義（OSMのウェイを連結） ----------
w744, w745, w739, w736, w764 = way(454570744), way(454570745), way(454570739), way(454570736), way(454570764)
alps2_bottom = ll(36.6609919, 137.8186999)
i_gp_join = nearest(w745, w744[-1])
i_gp_end = nearest(w745, alps2_bottom)
gp = w744 + w745[i_gp_join + 1:i_gp_end + 1]

i_cr_join = nearest(w745, w739[-1])
i_t_ex = nearest(w764, w736[-1])
cruise = w739 + w745[i_cr_join + 1:] + w764
expert = w736 + w764[i_t_ex + 1:]

ROUTES = [
    dict(id='cruise', name='アルプス平 ロングクルーズ', level='初・中級', frm='アルプス平（テレキャビン山頂）', to='とおみ',
         pts=cruise, split=('toomi', w764[0]),
         segs=[dict(name='パノラマコース', level='初・中級', len=850, avg=15, max=18, width=60, w=850),
               dict(name='スーパーコース', level='中・上級', len=450, avg=16, max=20, width=44, w=450),
               dict(name='チャンピオンダイナミックコース', level='中・上級', len=500, avg=21, max=23, width=50, w=500),
               dict(name='ウッディーコース', level='中級', len=800, avg=11, max=13, width=32, w=800),
               dict(name='とおみゲレンデ', level='初・中級', len=1500, avg=14, max=18, width=80, toomi=True)]),
    dict(id='grandprix', name='グランプリ', level='中・上級', frm='地蔵の頭', to='アルプス平',
         pts=gp, segs=[dict(name='グランプリコース', level='中・上級', len=900, avg=21, max=23, width=55, w=1)]),
    dict(id='expert', name='チャンピオンエキスパート', level='中・上級', frm='チャンピオン上部', to='とおみ',
         pts=expert, split=('toomi', w736[-1]),
         segs=[dict(name='チャンピオンエキスパートコース', level='中・上級', len=500, avg=30, max=35, width=44, w=1),
               dict(name='とおみゲレンデ', level='初・中級', len=1500, avg=14, max=18, width=80, toomi=True)]),
]

def resample(pts, step):
    out = [pts[0]]; acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0]-a[0], b[1]-a[1])
        if L == 0: continue
        t = step - acc
        while t <= L:
            out.append((a[0] + (b[0]-a[0]) * t / L, a[1] + (b[1]-a[1]) * t / L)); t += step
        acc = L - (t - step)
    out.append(pts[-1])
    return out

def smooth(pts, r, it):
    for _ in range(it):
        n = len(pts); new = []
        for i in range(n):
            k = min(r, i, n - 1 - i)
            xs = [pts[j][0] for j in range(i-k, i+k+1)]; zs = [pts[j][1] for j in range(i-k, i+k+1)]
            new.append((sum(xs)/len(xs), sum(zs)/len(zs)))
        pts = new
    return pts

allpts = [p for r in ROUTES for p in r['pts']]
MARGIN = 480
X0 = min(p[0] for p in allpts) - MARGIN; X1 = max(p[0] for p in allpts) + MARGIN
Z0 = min(p[1] for p in allpts) - MARGIN; Z1 = max(p[1] for p in allpts) + MARGIN
STEP = 4.0
NX = int((X1 - X0) / STEP) + 1; NZ = int((Z1 - Z0) / STEP) + 1
print('near grid', NX, NZ, NX * NZ)

def to_ll(x, z):
    lon = x / (111320 * math.cos(math.radians(LAT0))) + LON0
    lat = -z / 110574 + LAT0
    return lat, lon

H = [0.0] * (NX * NZ)
for j in range(NZ):
    for i in range(NX):
        lat, lon = to_ll(X0 + i * STEP, Z0 + j * STEP)
        e = elev(lat, lon)
        H[j * NX + i] = e if e is not None else 800.0

def blur(arr, nx, nz, r, passes):
    for _ in range(passes):
        tmp = [0.0] * (nx * nz)
        for j in range(nz):
            row = arr[j*nx:(j+1)*nx]; s = sum(row[0:r+1]) + row[0] * r
            for i in range(nx):
                tmp[j*nx+i] = s / (2*r+1)
                s += row[min(nx-1, i+r+1)] - row[max(0, i-r)]
        out = [0.0] * (nx * nz)
        for i in range(nx):
            col = tmp[i::nx]; s = sum(col[0:r+1]) + col[0] * r
            for j in range(nz):
                out[j*nx+i] = s / (2*r+1)
                s += col[min(nz-1, j+r+1)] - col[max(0, j-r)]
        arr = out
    return arr
H = blur(H, NX, NZ, 1, 2)   # 雪で地表の細かい凸凹がならされた状態

def hnear(x, z):
    fx = (x - X0) / STEP; fz = (z - Z0) / STEP
    i = max(0, min(NX - 2, int(fx))); j = max(0, min(NZ - 2, int(fz)))
    tx = fx - i; tz = fz - j
    a = H[j*NX+i]; b = H[j*NX+i+1]; c = H[(j+1)*NX+i]; d = H[(j+1)*NX+i+1]
    return (a*(1-tx)+b*tx)*(1-tz) + (c*(1-tx)+d*tx)*tz

# ---------- ルート中心線 ----------
routes_out = []
for r in ROUTES:
    pts = resample(r['pts'], 2.0)
    pts = smooth(pts, 12, 3)
    pts = resample(pts, 2.0)
    n = len(pts)
    ys = [hnear(x, z) for x, z in pts]
    # 区間の境目
    segs = r['segs']; bounds = []
    if 'split' in r:
        isplit = nearest(pts, r['split'][1])
        pre = [s for s in segs if not s.get('toomi')]
        tot = sum(s['w'] for s in pre); acc = 0
        for s in pre:
            bounds.append(int(round(acc / tot * isplit))); acc += s['w']
        bounds.append(isplit)
    else:
        bounds = [0]
    L3 = 0.0; maxs = 0.0
    for i in range(1, n):
        dh = math.hypot(pts[i][0]-pts[i-1][0], pts[i][1]-pts[i-1][1]); L3 += math.hypot(dh, ys[i]-ys[i-1])
    for i in range(5, n - 5):
        maxs = max(maxs, math.degrees(math.atan((ys[i-5] - ys[i+5]) / 20.0)))
    drop = ys[0] - ys[-1]; horiz = 2.0 * (n - 1)
    print(r['id'], 'samples', n, 'len3d', round(L3), 'drop', round(drop), 'avg', round(math.degrees(math.atan(drop / horiz)), 1), 'max', round(maxs, 1), 'bounds', bounds)
    routes_out.append(dict(id=r['id'], name=r['name'], level=r['level'], frm=r['frm'], to=r['to'],
        x=[round(p[0], 2) for p in pts], z=[round(p[1], 2) for p in pts],
        segStart=bounds, segs=[{k: v for k, v in s.items() if k not in ('w', 'toomi')} for s in segs],
        length=round(L3), topAlt=round(ys[0]), botAlt=round(ys[-1]), maxSlope=round(maxs)))

# ---------- 他のゲレンデ・リフト ----------
def inbox(p, m=0): return X0 - m <= p[0] <= X1 + m and Z0 - m <= p[1] <= Z1 + m
other_pistes = []
for w in osm['elements']:
    if w['tags'].get('piste:type') == 'downhill':
        pts = [xy(p['lat'], p['lon']) for p in w['geometry']]
        if any(inbox(p) for p in pts): other_pistes.append(resample(pts, 4.0))
lifts = []
for w in osm['elements']:
    t = w['tags'].get('aerialway')
    if t in ('gondola', 'chair_lift'):
        pts = [xy(p['lat'], p['lon']) for p in w['geometry']]
        if all(inbox(p) for p in pts):
            lifts.append(dict(name=w['tags'].get('name', ''), type=t,
                              pts=[[round(x, 1), round(z, 1), round(hnear(x, z), 1)] for x, z in pts]))
print('lifts', [l['name'] for l in lifts])

# ---------- 木の配置 ----------
B = 24.0
buckets = {}
def addb(x, z, hw):
    buckets.setdefault((int(x // B), int(z // B)), []).append((x, z, hw))
for r, ro in zip(ROUTES, routes_out):
    xs, zs = ro['x'], ro['z']; segs = ro['segs']; sb = ro['segStart']
    for i in range(0, len(xs), 2):
        si = max(k for k in range(len(sb)) if sb[k] <= i)
        addb(xs[i], zs[i], segs[si]['width'] / 2 + 5)
for pts in other_pistes:
    for x, z in pts: addb(x, z, 20)
for l in lifts:
    for x, z in resample([(p[0], p[1]) for p in l['pts']], 4.0): addb(x, z, 7)
C = 60.0
near_route = set()
for ro in routes_out:
    for x, z in zip(ro['x'][::5], ro['z'][::5]):
        cx, cz = int(x // C), int(z // C)
        for a in range(-4, 5):
            for b in range(-4, 5): near_route.add((cx + a, cz + b))
random.seed(5)
trees = []
SP = 11.0
zz = Z0 + 20
while zz < Z1 - 20:
    xx = X0 + 20
    while xx < X1 - 20:
        x = xx + random.uniform(-4.5, 4.5); z = zz + random.uniform(-4.5, 4.5)
        if (int(x // C), int(z // C)) in near_route:
            ok = True; bx, bz = int(x // B), int(z // B)
            for a in (-2, -1, 0, 1, 2):
                for b in (-2, -1, 0, 1, 2):
                    for (px, pz, hw) in buckets.get((bx + a, bz + b), ()):
                        if (px - x) ** 2 + (pz - z) ** 2 < hw * hw: ok = False; break
                    if not ok: break
                if not ok: break
            if ok and random.random() < 0.85:
                trees += [round(x, 1), round(z, 1), round(hnear(x, z) - 0.3, 1), round(random.uniform(0.75, 1.35), 2)]
        xx += SP
    zz += SP
print('trees', len(trees) // 4)

# ---------- 遠景（z13 DEM, 60m） ----------
FLAT0, FLAT1, FLON0, FLON1 = 36.605, 36.725, 137.70, 137.895
FS = 60.0
fx0, fz0 = xy(FLAT1, FLON0); fx1, fz1 = xy(FLAT0, FLON1)
FNX = int((fx1 - fx0) / FS) + 1; FNZ = int((fz1 - fz0) / FS) + 1
F = []
for j in range(FNZ):
    for i in range(FNX):
        lat, lon = to_ll(fx0 + i * FS, fz0 + j * FS)
        e = elev(lat, lon)
        F.append(e if e is not None else 700.0)
print('far grid', FNX, FNZ)

with open(OUT + 'goryu-terrain.bin', 'wb') as f:
    f.write(struct.pack('<%dh' % len(H), *[int(round(h * 10)) for h in H]))
    f.write(struct.pack('<%dh' % len(F), *[int(round(h * 10)) for h in F]))
meta = dict(near=dict(x0=X0, z0=Z0, step=STEP, nx=NX, nz=NZ), far=dict(x0=fx0, z0=fz0, step=FS, nx=FNX, nz=FNZ),
            routes=routes_out, lifts=lifts, trees=trees,
            pistes=[[[round(p[0]), round(p[1])] for p in pts[::3]] for pts in other_pistes],
            origin=[LAT0, LON0])
json.dump(meta, open(OUT + 'goryu-course.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('done')
