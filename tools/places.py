#!/usr/bin/env python3
"""Writes web/places.json, the names printed on the scene maps. From Natural Earth (public domain):
countries = ne_50m_admin_0_countries.geojson, cities = ne_50m_populated_places_simple.geojson.
Usage: tools/places.py countries.geojson cities.geojson
"""
import json
import sys

SEAS = [("Atlantic Ocean", 30, -40), ("Pacific Ocean", 12, -150), ("Pacific Ocean", 25, 160), ("Indian Ocean", -20, 80), ("Arctic Ocean", 80, 0), ("Southern Ocean", -60, 40), ("Mediterranean Sea", 35, 18), ("Black Sea", 43, 34), ("Red Sea", 20, 38), ("Persian Gulf", 26.5, 52), ("Arabian Sea", 15, 65),
        ("Bay of Bengal", 15, 88), ("South China Sea", 14, 114), ("Philippine Sea", 20, 130), ("East China Sea", 30, 125), ("Sea of Japan", 40, 135), ("Caribbean Sea", 15, -75), ("Gulf of Mexico", 25, -90), ("North Sea", 56, 3), ("Baltic Sea", 58, 20), ("Gulf of Aden", 12.5, 48),
        ("Caspian Sea", 41, 51), ("Coral Sea", -15, 155), ("Bering Sea", 58, -178), ("Gulf of Guinea", 2, 3), ("Tasman Sea", -38, 160), ("Hudson Bay", 60, -86), ("Sea of Okhotsk", 54, 150), ("Andaman Sea", 11, 96), ("Java Sea", -5, 112), ("Gulf of Alaska", 57, -145), ("Adriatic Sea", 43, 15), ("Aegean Sea", 38.5, 25)]
countries = json.load(open(sys.argv[1]))["features"]
cities = json.load(open(sys.argv[2]))["features"]
out = {
    "countries": sorted(([c["properties"]["NAME"], round(c["properties"]["LABEL_Y"], 2), round(c["properties"]["LABEL_X"], 2), int(c["properties"].get("LABELRANK") or 9)] for c in countries), key=lambda r: r[3]),
    "cities": [[c["properties"]["name"], round(c["properties"]["latitude"], 2), round(c["properties"]["longitude"], 2), int(c["properties"].get("scalerank") or 9) - 3 * int(c["properties"].get("adm0cap") or 0)]
               for c in sorted(cities, key=lambda c: -(c["properties"].get("pop_max") or 0))],
    "seas": SEAS,
}
json.dump(out, open("web/places.json", "w"), separators=(",", ":"), ensure_ascii=False)
