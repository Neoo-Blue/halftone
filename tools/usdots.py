#!/usr/bin/env python3
"""The dots of the election map: python3 tools/usdots.py <states.geojson> web/us-dots.json

Each state's outline becomes the grid cells inside it, so the page can ink a state by how sure its race is. Alaska and
Hawaii move to the lower left, like on any map of the states. The states are public domain, from the Census Bureau.
"""
import json
import math
import sys

COLS, ROWS = 120, 76
WIDE, HIGH = 960, 610


def albers(lat1, lat2, lat0, lon0):
    """The equal-area conic that maps of the US are drawn in."""
    p1, p2, p0 = map(math.radians, (lat1, lat2, lat0))
    n = (math.sin(p1) + math.sin(p2)) / 2
    c = math.cos(p1) ** 2 + 2 * n * math.sin(p1)
    far = math.sqrt(c - 2 * n * math.sin(p0)) / n

    def project(lon, lat):
        turn = n * math.radians(lon - lon0)
        r = math.sqrt(max(0, c - 2 * n * math.sin(math.radians(lat)))) / n
        return r * math.sin(turn), far - r * math.cos(turn)
    return project


LOWER, ALASKA, HAWAII = albers(29.5, 45.5, 37.5, -96), albers(55, 65, 50, -154), albers(8, 18, 20.5, -157)


def place(state, lon, lat):
    if state == "AK":
        x, y = ALASKA(lon, lat)
        return 180 + x * 420, 530 - y * 420
    if state == "HI":
        x, y = HAWAII(lon if lon < 0 else lon - 360, lat)
        return 330 + x * 1000, 540 - y * 1000
    x, y = LOWER(lon, lat)
    return WIDE / 2 + x * 1180, HIGH / 2 - 20 - y * 1180


def rings(geometry):
    return [ring for poly in (geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]) for ring in poly]


def inside(x, y, ring):
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def main(source, target):
    features = json.load(open(source))["features"]
    shapes = {}
    for f in features:
        state = f["properties"]["id"]
        shapes[state] = [[place(state, *p[:2]) for p in r] for r in rings(f["geometry"])]
    cells, step = {}, WIDE / COLS
    centre = lambda c, r: ((c + .5 + (r % 2) / 2) * step, (r + .5) * step * .92)
    for state, drawn in shapes.items():
        box = [(min(p[0] for p in r), min(p[1] for p in r), max(p[0] for p in r), max(p[1] for p in r)) for r in drawn]
        for r in range(ROWS):
            for c in range(COLS):
                x, y = centre(c, r)
                if any(b[0] <= x <= b[2] and b[1] <= y <= b[3] and inside(x, y, ring) for b, ring in zip(box, drawn)):
                    cells[(c, r)] = state
    # DC and the smallest states can miss every cell, so each gets the one nearest its middle.
    for state, drawn in shapes.items():
        if state not in cells.values():
            big = max(drawn, key=len)
            mx, my = sum(p[0] for p in big) / len(big), sum(p[1] for p in big) / len(big)
            cells[min(((c, r) for r in range(ROWS) for c in range(COLS)), key=lambda k: (centre(*k)[0] - mx) ** 2 + (centre(*k)[1] - my) ** 2)] = state
    out = {}
    for (c, r), state in sorted(cells.items()):
        out.setdefault(state, []).extend((c, r))
    json.dump({"cols": COLS, "rows": ROWS, "states": out}, open(target, "w"), separators=(",", ":"))
    print(len(cells), "dots,", len(out), "states")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
