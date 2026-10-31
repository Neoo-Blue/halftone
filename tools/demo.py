#!/usr/bin/env python3
"""See every desk with nothing connected: python3 tools/demo.py, then open http://127.0.0.1:8096.

Every name, number and story here is made up. No job runs and nothing leaves this machine. The data lives in a temp
folder that is gone when you stop it. The README's screenshots come from this.
"""
import hashlib
import math
import os
import random
import struct
import sys
import tempfile
import time
import zlib
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path

os.environ["PAPER_DATA"] = tempfile.mkdtemp(prefix="paper-demo")
os.environ["PAPER_AUTH"] = "none"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "paper"))
import server as s  # noqa: E402
import settings  # noqa: E402

random.seed(7)
NOW = int(time.time())
HOUR = 3600
DAY = 86400
OUTLETS = ["The Courier", "Daily Dispatch", "Northern Post", "The Ledger", "Harbor Times", "Global Wire"]
HEADS = [
    ("Harbor cities agree to share a single flood barrier after decade of talks", "Ministers from four coastal states signed the plan overnight, ending a dispute that had stalled two earlier projects."),
    ("Central banks signal a slower path as prices cool across the region", "Three policy makers said the next move depends on wages, not energy."),
    ("Rail strike ends after overnight deal on pay and rosters", "Trains will return to full service by the weekend, the union said."),
    ("Record wheat harvest eases fears of a winter price spike", "Exporters expect the largest shipments in six years."),
    ("Mountain towns open winter shelters early as first storm arrives", "Forecasters expect a metre of snow above the tree line."),
    ("Port workers return as shipping lanes reopen after a week of closures", "Backlogs could take a month to clear."),
    ("New battery plant promises four thousand jobs by 2029", "Local leaders called it the largest investment in a generation."),
    ("Open model beats closed rivals on a new reasoning benchmark", "The weights were released under a permissive license this morning."),
    ("Researchers shrink a data center cooling loop to the size of a shoebox", "The prototype cut power use by a third in early tests."),
    ("Browser makers agree on a shared standard for passkeys across devices", "The change reaches stable releases early next year."),
    ("Security teams race to patch a flaw in a widely used logging library", "Attackers began scanning for it within hours of disclosure."),
    ("Telescope finds water vapour on a rocky world forty light years away", "The team will point the instrument back at it next spring."),
]


def png(seed, w=480, h=270):
    """A made-up picture: soft shapes in grey, which each theme then screens like everything else on the page."""
    r = random.Random(seed)
    spots = [(r.uniform(0, w), r.uniform(0, h), r.uniform(50, 170), r.uniform(.3, 1)) for _ in range(6)]
    rows = b""
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            v = .22 + .25 * y / h + sum(a * math.exp(-((x - sx) ** 2 + (y - sy) ** 2) / (2 * sr ** 2)) for sx, sy, sr, a in spots)
            row.append(min(255, int(255 * v)))
        rows += bytes(row)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b"")


def picture(name):
    url = f"https://demo.invalid/{name}.jpg"
    (s.CACHE / hashlib.sha256(url.encode()).hexdigest()).write_bytes(png(name))
    return url


def story(i, desks):
    title, deck = HEADS[i % len(HEADS)]
    url = f"https://demo.invalid/story/{i}"
    outlets = [{"src": o, "u": f"{url}/{o}"} for o in random.sample(OUTLETS, random.randint(1, 5))]
    return {"id": f"{i:012x}", "t": title, "u": url, "src": outlets[0]["src"], "ts": NOW - i * 1700, "first": NOW - i * 2000, "sum": deck, "img": None, "desks": desks, "outlets": outlets}


def news():
    stories = [story(i, ["world"] if i < 3 else ["business"] if i < 5 else ["us"] if i < 7 else ["ai", "tech"] if i < 9 else ["tech"] if i < 10 else ["security"] if i < 11 else ["science"]) for i in range(len(HEADS))]
    for i, c in enumerate(stories[:6] + stories[7:8]):
        c["img"] = picture(f"story{i}")
    lead = {**stories[0], "text": "<p>The agreement, reached after a night of talks, gives each city a seat on a joint board and a share of the upkeep. Engineers say the first section could close to shipping in a storm within four years.</p><p>Critics in the smaller ports said they would watch the costs closely.</p>"}
    return {"lead": lead, "tops": stories[1:5], "tech_lead": {**stories[7], "text": ""}, "stories": stories * 4, "feeds": 57, "total": 57, "outlets": 50}


def world():
    theaters = [("north_strait", "The Northern Strait", 61, 55, 20), ("high_plateau", "The High Plateau", 47, 34, 70), ("south_coast", "The South Coast", 38, -12, 40), ("river_delta", "The River Delta", 29, 18, 95), ("east_isles", "The East Isles", 22, 8, 125)]
    dots = []
    for tid, _, esc, lat, lon in theaters:
        for _ in range(esc * 2):
            dots.append({"la": round(lat + random.gauss(0, 5), 2), "lo": round(lon + random.gauss(0, 7), 2), "s": round(random.uniform(.3, .95), 2), "i": "demo", "k": random.choice("kke"), "t": "A made-up event", "ts": NOW - random.randint(0, DAY), "w": tid})
    for _ in range(24):
        dots.append({"la": round(random.uniform(-40, 60), 2), "lo": round(random.uniform(-150, 150), 2), "s": .7, "i": "demo", "k": "h", "t": "A made-up storm", "ts": NOW - HOUR, "w": None})
    rows = [{"id": t, "name": n, "esc": e, "lat": la, "lon": lo} for t, n, e, la, lo in theaters]
    wire = [{"i": f"{i:016x}", "t": h[0], "k": "k" if i % 3 else "e", "ts": NOW - i * 900, "s": .6, "place": None, "src": OUTLETS[i % 6], "w": "north_strait", "la": None, "lo": None, "cat": None} for i, h in enumerate(HEADS)]
    return {"index": 53, "assessed": 51, "headline": "Tension holds in the Northern Strait as talks resume", "ts": NOW - HOUR, "rationale": "Reports of incidents fell for a third day while shipping stayed below its weekly average.", "most": "Everything on this page is made up for the demo.",
            "forecast": [{"statement": "Talks resume within the week.", "probability": .72, "horizon": "7d"}, {"statement": "A new incident is reported in the strait.", "probability": .41, "horizon": "24h"}, {"statement": "Shipping returns to its weekly average.", "probability": .28, "horizon": "48h"}], "movers": [],
            "theaters": rows[:8], "all_theaters": rows, "alerts": [{"t": "The Northern Strait reached 61, up from 48. Now 58.", "ts": NOW - 5 * HOUR, "s": .7, "theater": "north_strait"}], "stories": wire, "dots": dots, "assets": {"vessels": 32000, "aircraft": 640, "satellites": 850},
            "markets": [], "space": {"kp": 2.7, "g": "none", "forecast": "none"}, "hazards": {"red": 2, "orange": 11}}


def media():
    add = lambda k, t, sub, i: {"kind": k, "key": str(i), "title": t, "sub": sub, "at": NOW - i * 7000, "art": f"/img/remote?u=https%3A%2F%2Fdemo.invalid%2Fposter{i}.jpg", "about": "A made-up title.", "res": "4k" if i == 2 else None}
    titles = [("movie", "The Long Lighthouse", "2026"), ("show", "Harbor Nights", "3 new episodes"), ("movie", "Salt Road", "2025"), ("show", "The Understudies", "S2 E4"), ("movie", "Paper Moons", "2026"), ("show", "Field Notes", "New season")]
    added = [add(k, t, sub, i + 1) for i, (k, t, sub) in enumerate(titles)]
    for i in range(1, 7):
        picture(f"poster{i}")
    day = datetime.now(timezone.utc)
    upcoming = [{"kind": "show", "id": i, "title": t, "sub": sub, "at": (day + timedelta(days=d)).isoformat()[:19] + "Z", "art": None, "have": False} for i, (t, sub, d) in enumerate([("Harbor Nights", "S3 E7: The Tide Table", 1), ("Field Notes", "S1 E2: Maps", 2), ("The Understudies", "S2 E5: Curtain", 4)])]
    return {"added": added, "upcoming": upcoming, "libraries": [{"title": "Movies", "count": 1840}, {"title": "TV Shows", "count": 312}], "requests": {"processing": 2, "pending": 1}, "machine": None}


def machine(name, role, cpu, mem, disk):
    gb = 2 ** 30
    return {"name": name, "role": role, "ok": True, "cpu": cpu, "mem_used": mem * 32 * gb // 100, "mem_total": 32 * gb, "disk_used": disk * 2000 * gb // 100, "disk_total": 2000 * gb, "disk_mount": "/", "load": [cpu / 25, 1.1, .9], "cores": 8, "uptime": 19 * DAY, "temp": None, "raid_degraded": 0, "failed_units": []}


def feed():
    day = lambda ago: str((datetime.now(s.zone()) - timedelta(days=ago)).date())
    sales = [{"site": random.choice(["shop", "shop", "club"]), "cents": random.choice([1900, 2900, 4900]), "renewal": 0, "day": day(a), "created": NOW - a * DAY} for a in range(1, 80) for _ in range(random.randint(0, 3))]
    return {"now": NOW, "older": {"cents": 120000}, "sales": sales, "refunds": [{"site": "shop", "cents": 1900, "day": day(4)}], "spend": [{"day": day(a), "cents": 1400} for a in range(0, 60, 3)],
            "subs": [{"site": "club", "status": "active", "monthly": 1200}] * 14, "visitors": [{"site": k, "day": day(a), "n": random.randint(40, 180)} for k in ("shop", "club") for a in range(60)], "abandoned": [{"site": "shop", "created": NOW - a * DAY} for a in range(0, 30, 2)]}


def mail():
    rows = [("Priya N.", "priya@example.com", "Refund for a double charge", "Asks why their card was charged twice.", "customer", 1), ("Card network", "alerts@example.net", "Dispute opened on charge 4417", "A chargeback needs an answer in seven days.", "money", 1),
            ("Registrar", "domains@example.org", "shop.example expires in 9 days", "A domain renewal failed.", "security", 1), ("Sam at Northwind", "sam@example.com", "Bulk order for our team", "A company wants forty seats.", "customer", 1), ("Newsletter", "news@example.com", "Five growth hacks", "", "noise", 0)]
    with s.db() as c:
        for i, (sender, addr, subject, why, cat, want) in enumerate(rows):
            c.execute("INSERT INTO mail (id, box, gid, sender, addr, subject, preview, received, unread, junk, triaged, cat, important, why) VALUES (?, 'you@shop.example', ?, ?, ?, ?, '', ?, 1, 0, 1, ?, ?, ?)", (f"{i:024x}", str(i), sender, addr, subject, NOW - i * 5000, cat, want, why))


def main():
    s.init_db()
    settings.update({"PAPER_TZ": "America/New_York", "PAPER_SINCE": str((datetime.now(timezone.utc) - timedelta(days=211)).date()), "PLEX_URL": "http://demo.invalid", "PLEX_TOKEN": "demo", "PVE_URL": "http://demo.invalid", "PVE_TOKEN": "demo",
                     "PROBES": [{"group": "Sites", "name": n, "url": "http://demo.invalid/"} for n in ("My Shop", "The Club")] + [{"group": "At home", "name": n, "url": "http://demo.invalid/"} for n in ("Router", "Photos", "Backups")],
                     "MAIL_TENANT": "demo", "MAIL_CLIENT_ID": "demo", "MAIL_CLIENT_SECRET": "demo", "MAILBOXES": [{"address": "you@shop.example", "label": "Shop"}], "MONEY_URL": "http://demo.invalid",
                     "PRODUCTS": [{"key": "shop", "name": "My Shop", "host": "shop.example"}, {"key": "club", "name": "The Club", "host": "club.example"}]})
    s.save("news", news())
    s.save("world", world())
    s.save("media", media())
    s.save("playing", [{"title": "Harbor Nights, S3 E6", "who": "Sam", "state": "playing", "pct": 41, "device": "Living room", "mode": "direct play"}])
    s.save("probes", [{"group": g, "name": n, "url": "", "up": True, "gated": False, "status": 200, "ms": random.randint(30, 400), "error": None, "day": 100.0, "week": 99.9} for g, n in (("Sites", "My Shop"), ("Sites", "The Club"), ("At home", "Router"), ("At home", "Photos"), ("At home", "Backups"))])
    s.save("machines", {"hosts": [machine("Proxmox", "Containers", 14, 62, 48), machine("NAS", "Backups", 6, 31, 71)], "guests": [{"id": 101 + i, "type": "lxc", "name": n, "status": "running", "cpu": 3, "cores": 2, "mem": 2 ** 30, "maxmem": 2 ** 32, "disk": 0, "maxdisk": 2 ** 34, "uptime": 19 * DAY} for i, n in enumerate(("media", "photos", "paper"))],
                        "history": [{"t": NOW - i * 900, "cpu": 12 + 6 * math.sin(i / 9), "mem": 60, "io": 1} for i in range(96, 0, -1)]})
    s.save("storage", {"pools": [{"name": "tank", "size": 4 * 10 ** 12, "alloc": 2 * 10 ** 12, "health": "ONLINE", "frag": 8}], "disks": [], "backups": [{"at": NOW - 6 * HOUR, "ok": True, "status": "OK"}], "failed_tasks": [], "autostart": []})
    s.save("feed", feed())
    s.save("mail", {"read": 1, "failed": [], "triage_error": None})
    mail()
    s.set_costs([("Hosting", 4000, "month"), ("Email", 1200, "month"), ("Domains", 3600, "year"), ("Ads", None, "month")])
    print("The demo is at http://127.0.0.1:8096. Every word of it is made up.", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8096), s.Handler).serve_forever()


if __name__ == "__main__":
    main()
