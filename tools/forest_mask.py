import struct, zlib, colorsys
X=list(range(115715,115722)); Y=list(range(51168,51173)); Z=17
def readbmp(fn):
    b=open(fn,'rb').read(); off=struct.unpack('<I',b[10:14])[0]; w,h=struct.unpack('<ii',b[18:26]); bpp=struct.unpack('<H',b[28:30])[0]
    row=((w*bpp//8)+3)//4*4; step=bpp//8; px=[]
    for y in range(abs(h)):
        yy=(abs(h)-1-y) if h>0 else y; r=b[off+yy*row: off+yy*row+w*step]
        px.append([(r[i*step+2],r[i*step+1],r[i*step]) for i in range(w)])
    return px
W=len(X)*256; H=len(Y)*256
img=[None]*H
for iy,y in enumerate(Y):
    tiles=[readbmp(f'p_17_{x}_{y}.bmp') for x in X]
    for j in range(256): img[iy*256+j]=[p for t in tiles for p in t[j]]
# 2x2 に縮小しつつ特徴量：彩度・明度・局所ばらつき
S=2; w=W//S; h=H//S
score=[[0.0]*w for _ in range(h)]
for j in range(h):
    for i in range(w):
        ps=[img[j*S+a][i*S+b] for a in range(S) for b in range(S)]
        r=sum(p[0] for p in ps)/4; g=sum(p[1] for p in ps)/4; bl=sum(p[2] for p in ps)/4
        hh,ss,vv=colorsys.rgb_to_hsv(r/255,g/255,bl/255)
        var=sum(abs(p[0]-r)+abs(p[1]-g)+abs(p[2]-bl) for p in ps)/4
        f=0.0
        f += (ss-0.28)*3.0          # 紅葉・緑の森は彩度が高い
        f += (0.52-vv)*2.0          # 森は暗め
        f += (var-18)/25            # 森は凹凸（ばらつき）が大きい
        score[j][i]=f
# 平滑化（ボックス 5x5 を2回）
def blur(a,r):
    h=len(a); w=len(a[0]); out=[[0.0]*w for _ in range(h)]
    for j in range(h):
        acc=0; row=a[j]; pre=[0]
        for v in row: pre.append(pre[-1]+v)
        for i in range(w):
            lo=max(0,i-r); hi=min(w,i+r+1); out[j][i]=(pre[hi]-pre[lo])/(hi-lo)
    out2=[[0.0]*w for _ in range(h)]
    for i in range(w):
        pre=[0]
        for j in range(h): pre.append(pre[-1]+out[j][i])
        for j in range(h):
            lo=max(0,j-r); hi=min(h,j+r+1); out2[j][i]=(pre[hi]-pre[lo])/(hi-lo)
    return out2
sm=blur(blur(score,3),3)
forest=[[1 if v>0 else 0 for v in row] for row in sm]
import json
json.dump({'z':Z,'x0':X[0]*256,'y0':Y[0]*256,'scale':S,'w':w,'h':h,'rows':[''.join('1' if c else '0' for c in row) for row in forest]}, open('forest_mask.json','w'))
# プレビュー：森＝濃緑、開けた所＝白
P=2
raw=b''.join(b'\x00'+bytes(c for i in range(0,w,P) for c in ((40,80,50) if forest[j][i] else (235,238,240))) for j in range(0,h,P))
def ch(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
open('mask_preview.png','wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',len(range(0,w,P)),len(range(0,h,P)),8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw,6))+ch(b'IEND',b''))
print('mask',w,h, 'forest ratio', sum(map(sum,forest))/(w*h))
