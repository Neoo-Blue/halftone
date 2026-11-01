#!/usr/bin/env python3
"""The shapes behind the election map's zoom: python3 tools/usshapes.py <geo folder> <overlap.json.gz> <places.json.gz> web/us

One small file for each state, fetched when that state is opened, in the same projection as web/us-dots.json so a state
lines up with its dots as the map moves in. House districts, counties and towns, all public domain, from the Census Bureau.
"""
import gzip
import json
import re
import sys
from pathlib import Path

from usdots import place, rings

SKIP = re.compile(r"\s+(CDP|comunidad|zona urbana)$")
TYPE = re.compile(r"\s+(city|town|village|borough|municipality|city and borough|consolidated government.*|metro government.*|unified government.*|urban county.*)(\s*\(balance\))?$", re.I)


def flat(state, ring):
    return [round(v, 2) for p in ring for v in place(state, *p[:2])]


def bounds(all_rings):
    xs = [v for r in all_rings for v in r[::2]]
    ys = [v for r in all_rings for v in r[1::2]]
    return [min(xs), min(ys), max(xs), max(ys)]


def simple(name):
    return re.sub(r"\s+(county|parish|borough|census area|municipality|city and borough)$", "", name.lower())


def main(geo, overlap_file, places_file, target):
    geo, target = Path(geo), Path(target)
    target.mkdir(parents=True, exist_ok=True)
    states = {f["properties"]["id"]: f for f in json.load(open(geo / "us-states.json"))["features"]}
    house, counties = {}, {}
    for f in json.load(open(geo / "us-house.json"))["features"]:
        house.setdefault(f["properties"]["st"], []).append(f)
    for f in json.load(open(geo / "us-counties.json"))["features"]:
        counties.setdefault(f["properties"]["st"], []).append(f)
    overlap = json.load(gzip.open(overlap_file))
    places = json.load(gzip.open(places_file))
    for st, shape in sorted(states.items()):
        split = overlap.get(st, {})
        seats = []
        for f in sorted(house.get(st, []), key=lambda x: x["properties"]["n"]):
            p = f["properties"]
            drawn = [flat(st, r) for r in rings(f["geometry"])]
            seats.append({"k": f"H-{p['id']}", "n": p["n"], "at": [round(v, 2) for v in place(st, p["lon"], p["lat"])], "r": drawn, "box": bounds(drawn)})
        cos = []
        for f in sorted(counties.get(st, []), key=lambda x: x["properties"]["name"]):
            drawn = [flat(st, r) for r in rings(f["geometry"])]
            box = bounds(drawn)
            name = f["properties"]["name"]
            ids = split.get("c", {}).get(simple(name)) or split.get("ic", {}).get(simple(name)) or []
            cos.append({"n": name, "at": [round((box[0] + box[2]) / 2, 2), round((box[1] + box[3]) / 2, 2)], "r": drawn, "box": box, "k": [f"H-{i}" for i in ids]})
        towns = []
        for lat, lon, label in places.get(st, {}).get("p", {}).values():
            if not SKIP.search(label):
                towns.append([*(round(v, 2) for v in place(st, lon, lat)), TYPE.sub("", label)])
        line = [flat(st, r) for r in rings(shape["geometry"])]
        (target / f"{st}.json").write_text(json.dumps({"box": bounds(line), "line": line, "seats": seats, "cos": cos, "towns": sorted(towns, key=lambda t: t[2])}, separators=(",", ":")))


if __name__ == "__main__":
    main(*sys.argv[1:5])
