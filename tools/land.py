#!/usr/bin/env python3
"""Rasterize world-atlas land-50m.json (curl it from jsdelivr) to web/land.png, the globe's mask. With a width and a path (land-10m.json 5400 web/land-sharp.png) it makes the sharper map the scenes zoom into."""
import json, sys
from PIL import Image, ImageDraw

W, H, SCALE = int(sys.argv[2]) if len(sys.argv) > 2 else 1024, int(sys.argv[2]) // 2 if len(sys.argv) > 2 else 512, 4 if len(sys.argv) < 3 else 2  # supersampled, then shrunk for soft coastlines
topo = json.load(open(sys.argv[1]))
sx, sy = topo["transform"]["scale"]; tx, ty = topo["transform"]["translate"]
arcs = []
for arc in topo["arcs"]:
    x = y = 0; pts = []
    for dx, dy in arc:
        x += dx; y += dy
        pts.append((x * sx + tx, y * sy + ty))
    arcs.append(pts)

def ring(ids):
    out = []
    for i in ids:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        out += a[1:] if out else a
    return [((lon + 180) / 360 * W * SCALE, (90 - lat) / 180 * H * SCALE) for lon, lat in out]

img = Image.new("L", (W * SCALE, H * SCALE), 0); d = ImageDraw.Draw(img)
for g in topo["objects"]["land"]["geometries"]:
    polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
    for poly in polys:
        d.polygon(ring(poly[0]), fill=255)
        for hole in poly[1:]:
            d.polygon(ring(hole), fill=0)
img.resize((W, H), Image.LANCZOS).convert("1").save(sys.argv[3], optimize=True) if len(sys.argv) > 3 else img.resize((W, H), Image.LANCZOS).save("web/land.png", optimize=True)
