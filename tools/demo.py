#!/usr/bin/env python3
"""See every desk with nothing connected: python3 tools/demo.py, then open http://127.0.0.1:8096.

Every name, number and story here is made up. No job runs and nothing leaves this machine. The data lives in a temp
folder that is gone when you stop it. The README's screenshots come from this.
"""
import hashlib
import json
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
LEANS = {"Northern Post": "left", "The Citizen": "left", "The Courier": "lean left", "Harbor Times": "lean left", "Global Wire": "center", "Daily Dispatch": "center", "The Ledger": "lean right", "Morning Bulletin": "lean right", "The Standard": "right", "Frontier Review": "right"}
OUTLETS = list(LEANS)
RENT = [("Northern Post", "Renters win a cap after a decade of rising bills"), ("The Citizen", "A rent cap at last for harbor families"), ("The Courier", "Council caps rents on harbor apartments at three percent a year"), ("Global Wire", "Council votes to limit yearly rent rises"),
        ("Daily Dispatch", "Harbor rent rises capped at three percent"), ("The Ledger", "Builders warn a rent cap will freeze new harbor projects"), ("The Standard", "The council's rent cap will choke the housing it promises"), ("Frontier Review", "Rent control returns, and the harbor will pay for it")]
HEADS = [
    ("Harbor cities agree to share a single flood barrier after decade of talks", "Ministers from four coastal states signed the plan overnight, ending a dispute that had stalled two earlier projects."),
    ("Talks resume in the Northern Strait after a nine-day pause", "Both sides moved ships back from the inner channel ahead of the round."),
    ("Council caps rents on harbor apartments at three percent a year", "The vote split the chamber and sets up a fight with builders."),
    ("Record wheat harvest eases fears of a winter price spike", "Exporters expect the largest shipments in six years."),
    ("Mountain towns open winter shelters early as first storm arrives", "Forecasters expect a metre of snow above the tree line."),
    ("Port workers return as shipping lanes reopen after a week of closures", "Backlogs could take a month to clear."),
    ("New battery plant promises four thousand jobs by 2029", "Local leaders called it the largest investment in a generation."),
    ("Open model beats closed rivals on a new reasoning benchmark", "The weights were released under a permissive license this morning."),
    ("Researchers shrink a data center cooling loop to the size of a shoebox", "The prototype cut power use by a third in early tests."),
    ("Browser makers agree on a shared standard for passkeys across devices", "The change reaches stable releases early next year."),
    ("Security teams race to patch a flaw in a widely used logging library", "Attackers began scanning for it within hours of disclosure."),
    ("Telescope finds water vapour on a rocky world forty light years away", "The team will point the instrument back at it next spring."),
    ("Ferry service to the outer islands doubles for the winter", "Two more boats join the route from December."),
    ("Dock workers vote on a four-year contract this week", "Union leaders called the offer the best in a generation."),
    ("Grain prices slip as ships return to the outer lanes", "Traders said the fall could reverse if talks stall."),
    ("Housing starts fall for a third straight month", "Builders blamed borrowing costs and a shortage of electricians."),
    ("City opens its first floating park beside the old customs house", "The park rises and falls with the tide."),
    ("Small chip maker wins a contract to supply harbor cranes", "The deal is worth more than its last two years of sales combined."),
    ("Solar output hits a record as spring comes early to the coast", "Grid operators paid some farms to switch off at noon."),
    ("Language model learns to say when it doesn't know", "Researchers said the change cut wrong answers by a third."),
    ("Regulators open an inquiry into a cloud outage that stopped payments", "The failure lasted six hours on a busy Friday."),
    ("Password manager patches a bug found by a teenager", "The company paid the largest bounty in its history."),
    ("Deep sea survey maps a mountain range nobody had seen", "The peaks rise more than two kilometers from the floor."),
    ("Bird flu vaccine for poultry clears its last trial", "Farmers could have it before the spring migration."),
]


LATER = (["us"], ["us"], ["business"], ["business"], ["us"], ["tech"], ["science"], ["ai", "tech"], ["tech"], ["security"], ["science"], ["science"])  # the desks of the later headlines


def png(seed, w=480, h=270):
    """A made-up picture of a harbor: sky, hills, water. It's in grey, and each theme screens it like everything else on the page."""
    r = random.Random(seed)
    sun, far, near, phase = r.uniform(.15, .85) * w, r.uniform(.30, .42), r.uniform(.46, .56), r.uniform(0, 6.28)
    rows = b""
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            u, v = x / w, y / h
            ridge = far + .05 * math.sin(u * 7 + phase) + .02 * math.sin(u * 23 + phase)
            shore = near + .03 * math.sin(u * 5 - phase) + .012 * math.sin(u * 31)
            if v > .62:
                ink = .52 + .3 * (v - .62) + .16 * math.sin(y / 2.2 + 3 * math.sin(x / 40 + phase))
            elif v > shore:
                ink = .18
            elif v > ridge:
                ink = .36
            else:
                ink = .95 - .55 * v - .5 * math.exp(-(((x - sun) / 46) ** 2 + ((y - h * .2) / 46) ** 2))
            row.append(max(0, min(255, int(255 * (1 - ink) * 1.05))))
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
    told = RENT if i == 2 else [(o, title) for o in random.sample(OUTLETS, random.randint(1, 7))]
    outlets = [{"src": o, "u": f"{url}/{o.lower().replace(' ', '-')}", "t": t, "ts": NOW - i * 1700 - n * 1500} for n, (o, t) in enumerate(told)]
    return {"id": f"{i:012x}", "t": title, "u": outlets[0]["u"], "src": outlets[0]["src"], "ts": NOW - i * 1700, "first": NOW - i * 2000, "sum": deck, "img": None, "desks": desks, "outlets": outlets}


def news():
    stories = [story(i, ["world"] if i < 3 else ["business"] if i < 5 else ["us"] if i < 7 else ["ai", "tech"] if i < 9 else ["tech"] if i < 10 else ["security"] if i < 11 else ["science"] if i < 12 else LATER[i - 12]) for i in range(len(HEADS))]
    for i, c in enumerate(stories[:6] + stories[7:8]):
        c["img"] = picture(f"story{i}")
    for c in stories:
        c["lean"] = s.sides.count(c["outlets"], s.own_leans())
    lead = {**stories[0], "text": "<p>The agreement, reached after a night of talks, gives each city a seat on a joint board and a share of the upkeep. Engineers say the first section could close to shipping in a storm within four years.</p><p>Critics in the smaller ports said they would watch the costs closely.</p>"}
    also = [{"u": c["u"], "t": c["t"], "src": c["src"], "n": len(c["outlets"]), "ts": c["ts"], "lean": c["lean"]} for c in stories[5:7] + stories[8:11]]
    only = lambda t, names, lean: {"u": f"https://demo.invalid/only/{abs(hash(t)) % 9999}", "t": t, "src": names[0], "n": len(names), "ts": NOW - 5 * HOUR, "lean": lean, "names": names}
    blind = {"l": [only("Tenants sue over mould in city-run towers", ["Northern Post", "The Citizen", "The Courier", "Harbor Times"], [4, 0, 0]), only("School meals fund runs out in March, report finds", ["The Citizen", "The Courier", "Harbor Times", "Northern Post"], [4, 0, 0])],
             "r": [only("Audit finds the transit agency overpaid on its new depot", ["The Standard", "Frontier Review", "The Ledger"], [0, 0, 3]), only("Small farms say the water rule will close them by spring", ["Frontier Review", "Morning Bulletin", "The Standard"], [0, 0, 3])]}
    trending = [{"name": n, "n": k} for n, k in (("Northern Strait", 9), ("Harbor", 7), ("Rent cap", 6), ("Battery plant", 4), ("Passkeys", 3))]
    return {"lead": lead, "tops": stories[1:5], "also": also, "tech_lead": {**stories[7], "text": ""}, "stories": stories, "blind": blind, "trending": trending, "feeds": 57, "total": 57, "outlets": 50}


def world():
    theaters = [("north_strait", "The Northern Strait", 61, 55, 20), ("high_plateau", "The High Plateau", 47, 34, 70), ("south_coast", "The South Coast", 38, -12, 40), ("river_delta", "The River Delta", 29, 18, 95), ("east_isles", "The East Isles", 22, 8, 125)]
    dots = []
    for tid, _, esc, lat, lon in theaters:
        for _ in range(esc * 2):
            dots.append({"la": round(lat + random.gauss(0, 5), 2), "lo": round(lon + random.gauss(0, 7), 2), "s": round(random.uniform(.3, .95), 2), "i": "demo", "k": random.choice("kke"), "t": "A made-up event", "ts": NOW - random.randint(0, DAY), "w": tid})
    for _ in range(24):
        dots.append({"la": round(random.uniform(-40, 60), 2), "lo": round(random.uniform(-150, 150), 2), "s": .7, "i": "demo", "k": "h", "t": "A made-up storm", "ts": NOW - HOUR, "w": None})
    rows = [{"id": t, "name": n, "esc": e, "lat": la, "lon": lo} for t, n, e, la, lo in theaters]
    rows.insert(1, {"id": "trade_talks", "name": "The Tariff Dispute", "esc": 55, "lat": None, "lon": None})  # a topic, with no place on the map
    wire = [{"i": f"{i:016x}", "t": h[0], "k": "k" if i % 3 else "e", "ts": NOW - i * 900, "s": .6, "place": None, "src": OUTLETS[i % 6], "w": "north_strait", "la": None, "lo": None, "cat": None} for i, h in enumerate(HEADS)]
    return {"index": 53, "assessed": 51, "headline": "Tension holds in the Northern Strait as talks resume", "ts": NOW - HOUR, "rationale": "Reports of incidents fell for a third day while shipping stayed below its weekly average.", "most": "Everything on this page is made up for the demo.",
            "forecast": [{"statement": "Talks resume within the week.", "probability": .72, "horizon": "7d"}, {"statement": "A new incident is reported in the strait.", "probability": .41, "horizon": "24h"}, {"statement": "Shipping returns to its weekly average.", "probability": .28, "horizon": "48h"}], "movers": [],
            "markets": [{"key": k, "label": n, "last": v, "pct": c, "unit": "", "why": ""} for k, n, v, c in (("crude", "Crude", 71.2, .4), ("gold", "Gold", 2411.0, -.6), ("copper", "Copper", 4.4, 1.1), ("wheat", "Wheat", 5.8, -.2), ("dollar", "Dollar index", 104.2, .1))], "theaters": rows[:8], "all_theaters": rows, "alerts": [{"t": "The Northern Strait reached 61, up from 48. Now 58.", "ts": NOW - 5 * HOUR, "s": .7, "theater": "north_strait"}], "stories": wire, "dots": dots, "assets": {"vessels": 32000, "aircraft": 640, "satellites": 850},
            "space": {"kp": 2.7, "g": "none", "forecast": "none"}, "hazards": {"red": 2, "orange": 11}}


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
    return {"name": name, "role": role, "ok": True, "cpu": cpu, "mem_used": mem * 32 * gb // 100, "mem_total": 32 * gb, "disk_used": disk * 2000 * gb // 100, "disk_total": 2000 * gb, "disk_mount": "/", "load": [cpu / 25, 1.1, .9], "cores": 8, "uptime": 19 * DAY, "temp": 41.0, "raid_degraded": 0, "failed_units": [],
            "containers": [{"name": "photos", "state": "running", "status": "Up 6 days (healthy)"}, {"name": "postgres", "state": "running", "status": "Up 19 days"}, {"name": "indexer", "state": "exited", "status": "Exited (0) 3 hours ago"}],
            "volumes": [{"mount": "/", "used": 60 * gb, "total": 240 * gb}, {"mount": "/volume1", "used": disk * 2000 * gb // 100, "total": 2000 * gb}], "top": [{"name": "photos-indexer", "cpu": 31.2, "mem": 6.1}, {"name": "postgres", "cpu": 8.4, "mem": 12.3}, {"name": "backupd", "cpu": 2.1, "mem": 1.8}]}


def history(name, cpu, disk, grows):
    """Thirty days of readings with a working day in them, a few a day for the old ones and every minute for the last hour."""
    rows = []
    for t in [NOW - i * 3600 for i in range(1, 30 * 24)] + [NOW - i * 60 for i in range(60)]:
        hour = math.sin((t % DAY) / DAY * 2 * math.pi)
        rows.append((name, t, max(1, cpu + 9 * hour + random.gauss(0, 3)), 60 + 4 * hour + random.gauss(0, 1), disk - (NOW - t) / DAY * grows, cpu / 20 + hour / 3, max(0, 2 + random.gauss(0, 1)), 2e6 + 1.5e6 * hour + random.uniform(0, 8e5), 6e5 + 3e5 * hour, 1e6 * random.random(), 2e6 * random.random(), 41 + 3 * hour))
    with s.db() as c:
        c.executemany("INSERT INTO metric VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)


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


# ---------------------------------------------------------------------- what would come from outside, made up as well
# Each stub stands where the paper would reach a stranger, so the whole page works and nothing leaves this machine.

RENT_BODY = """<p>The harbor council voted seven to four on Tuesday night to cap yearly rent rises at three percent on apartments older than ten years, the first limit of its kind in the city.</p>
<p>Supporters said the cap would keep long-time tenants near their work after five years of rises that outran wages. Opponents said it would drive builders away just as the city needs more homes.</p>
<h2>What the cap covers</h2>
<p>The rule applies to about 41,000 apartments in the harbor district. New buildings are exempt for their first ten years, and landlords can ask a review board for more when they pay for major repairs.</p>
<p>"Nobody here is asking for free housing," said Dana Reyes, who has rented the same two rooms on Quay Street for 19 years. "We're asking to know what next year costs."</p>
<h2>What builders say</h2>
<p>The Harbor Builders Group said three planned towers were now under review. "Money goes where the rules are steady," said its chair, Tomas Lind. "This tells it to go somewhere else."</p>
<p>The city's own analysis found that a cap of this size would slow new construction by a small amount over a decade, and that it could not say how large. The council has asked for a fresh estimate within a year.</p>
<h2>What happens next</h2>
<p>The cap takes effect in January unless opponents collect enough signatures to force a public vote. Both sides have said they expect that to happen.</p>"""
TAKES = {"contested": True, "subject": "The harbor rent cap", "case_for": "Supporters say a cap protects long-time tenants from sudden rises while the city builds more homes.", "case_against": "Opponents say a cap scares off builders and leaves fewer homes for everyone within a decade.",
         "agreed": "The council voted seven to four to cap yearly rent rises at three percent from January.", "stances": [{"i": i, "stance": x} for i, x in enumerate(("against", "against", "against", "neutral", "neutral", "neutral", "for", "for"))]}
CAMPS = [{"code": "NL", "label": "Norland's side"}, {"code": "CO", "label": "Costera's side"}]


def read_page(url):
    item = s.known_item(url) or {}
    body = RENT_BODY if "/story/2/" in url else "".join(f"<p>{p}</p>" for p in (item.get("sum", "Every word here is made up."), "This story is made up for the demo. On a real paper, the article opens here in a clean reader, with nothing but the words.", "Outlets, people and places in it are all invented, and the paper reached nothing outside this machine to show it."))
    return {"url": url, "site": item.get("src", "The Courier"), "title": item.get("t", "A made-up story"), "deck": item.get("sum", ""), "image": None, "author": "Mara Quinn", "published": item.get("ts", NOW), "body": body, "words": len(body.split())}


def asked(system, text, max_tokens=1500, cheap=False, schema=None):
    if system == s.TAKES_SYSTEM:
        return json.dumps(TAKES)
    if system != s.FIND_SYSTEM:
        return "This is the demo, so no AI read this. On a real paper the answer comes from what you're reading, with its sources."
    if "The reader now asks" in text:
        return json.dumps({"answer": "The two sides have agreed on a schedule and nothing else [3]. Shipping insurers are waiting for a second week without incidents before they cut rates [2].", "next": ["Who is mediating?", "What would reopen the lane?"]})
    if "Strait" not in text.split("Searched for:")[-1]:
        return json.dumps({"answer": "This is the demo, so this answer is made up [1]. A real one is written from the sources below, with a number on each claim.", "next": ["What else can it find?"]})
    return json.dumps({"answer": "Talks between Norland and Costera resumed on Monday after a nine-day pause [1]. Reported incidents fell for a third day, and shipping is back near its weekly average [2]. Both sides still claim the inner channel, and neither has said what it would give up [3].",
                       "next": ["What is each side asking for?", "How close is shipping to normal?", "Who is mediating the talks?"]})


def looked_up(query, most=8):
    return [{"t": f"{query}: a short history", "u": "https://example.org/history", "sum": "How the dispute began, and who has held what since."}, {"t": f"{query} shipping map", "u": "https://example.net/map", "sum": "Lanes, ports and the inner channel."}, {"t": f"Explaining the {query} talks", "u": "https://example.com/talks", "sum": "What each side has asked for."}]


def said(q, n=5):
    heads = [f"{q}: talks resume after a nine-day pause", f"Insurers watch {q} for a second calm week", f"Why {q} matters to grain prices", f"Ships return to {q} as reports of incidents fall", f"What Norland wants from {q}"]
    return [{"t": t, "u": f"https://demo.invalid/more/{i}", "src": OUTLETS[i], "sum": "A made-up line from the story.", "ts": NOW - i * 4 * HOUR} for i, t in enumerate(heads[:n])]


def priced(key, name, where, price, prev):
    wave = [round(prev * (1 + .03 * math.sin((i - 21) / 3) - (21 - i) / 300), 2) for i in range(22)]
    return {"kind": "market", "key": key, "name": name, "where": where, "price": price, "prev": prev, "currency": "USD", "closes": wave + [price], "href": f"/topic/{key}"}


def around(q):
    q = s.clean_query(q)
    low = q.lower()
    cards = [s.conflict_card(t) for t in s.theaters_on(q)]
    if "freight" in low or low == "hrbr":
        cards.append(priced("HRBR", "Harbor Freight Lines", "NYSE", 141.2, 139.9))
    elif "rangers" in low:
        cards.append(TEAM)
    elif "harbor city" in low:
        cards.append(TOWN)
    else:
        cards.append({"kind": "thing", "name": q.title(), "about": "Made up for the demo", "text": "A made-up channel between two made-up coasts, 140 km long and 22 km wide at its narrowest. About a fifth of the region's grain passes through it." if "strait" in low else f"{q.title()} would have its encyclopedia entry here: a paragraph on what it is, with a link to the rest.", "url": "https://demo.invalid/wiki"})
    odds = [{"t": "Do talks end in a signed deal by...?", "u": "https://demo.invalid/odds", "volume": 2400000, "lines": [{"t": "December 31", "pct": 18}, {"t": "March 31", "pct": 37}, {"t": "June 30", "pct": 56}]}, {"t": "New incident in the strait this month?", "u": "https://demo.invalid/odds2", "volume": 610000, "lines": [{"t": "Yes", "pct": 41}]}]
    talk = [{"t": f"Tracking {q} from public ship positions", "u": "https://demo.invalid/talk", "src": "Hacker News", "sum": "412 points, 188 comments", "ts": NOW - 6 * DAY}]
    return {"q": q, "cards": cards, "news": said(q), "talk": talk, "papers": [], "code": [], "odds": odds if "strait" in low else []}


def war(path, timeout=30):
    """What WARROOM would say about the made-up conflicts and the made-up storm."""
    if path.startswith("/intel"):
        return {"items": [{"headline": "Talks hold while each side tests the other", "body": "Reported incidents fell for a third day. Both sides moved ships back from the inner channel, though neither has said why. The next round is set for Thursday.", "bullets": ["Shipping is near its weekly average", "Neither side has given up a claim"], "ts": NOW - 2 * HOUR}]}
    if path.startswith("/events"):
        return {"items": REPORTS}
    if path.endswith("/history"):
        return HISTORY
    if path.endswith("/accounts"):
        return WHO
    if path.startswith("/hazards/"):
        return {"name": "MARIN-26", "kind": "cyclone", "severity_text": "A made-up tropical storm, with winds up to 190 km/h", "alert": "orange", "country": "The Bay Coast", "from_ts": NOW - 4 * DAY, "to_ts": NOW + DAY, "lat": 16.7, "lon": 81.0, "extra": {}}
    raise OSError("the demo has no WARROOM")


def corridor(points, width):
    """A band along a path, as [lon, lat] pairs."""
    side = [[lo, la + width] for la, lo, _ in points]
    return [*side, *([lo, la - width] for la, lo, _ in reversed(points)), side[0]]


def cyclone(_):
    path = [(11.5, 93.0, 65), (12.2, 91.2, 85), (12.9, 89.6, 110), (13.5, 88.0, 140), (14.1, 86.4, 165), (14.8, 84.9, 185), (15.4, 83.4, 190), (16.0, 82.0, 170), (16.7, 81.0, 130)]
    ahead = [(18.2, 80.8, 90), (19.8, 80.6, 65), (21.3, 81.0, 45)]
    track = [{"la": la, "lo": lo, "t": NOW - (len(path) - 1 - i) * 12 * HOUR, "v": v, "label": "Tropical storm", "fc": False} for i, (la, lo, v) in enumerate(path)]
    track += [{"la": la, "lo": lo, "t": NOW + (i + 1) * 12 * HOUR, "v": v, "label": "Tropical depression", "fc": True} for i, (la, lo, v) in enumerate(ahead)]
    return {"track": track, "areas": [{"level": 0, "rings": [corridor(path[-1:] + ahead, 1.3)]}, {"level": 1, "rings": [corridor(path, 1.5)]}, {"level": 3, "rings": [corridor(path[3:8], .6)]}],
            "impact": [["Peak winds", "190 km/h"], ["People in gale-force winds", "4,200,000"], ["People in hurricane-force winds", "310,000"], ["Storm surge", "up to 2.4 m"]], "countries": ["The Bay Coast"], "source": "Made up for the demo", "report": None}


TEAM = {"kind": "team", "key": "demo/city/1", "name": "Harbor Rangers", "standing": "2nd in City League", "record": "14-5", "last": {"mine": 101, "theirs": 96, "home": True, "vs": "Summit Comets", "state": "post", "at": NOW - DAY}, "next": {"home": False, "vs": "Bay Pilots", "at": NOW + 2 * DAY}, "href": "/topic/Harbor%20Rangers"}
TOWN = {"kind": "place", "key": "40.7,-74.0", "name": "Harbor City", "region": "Made Up, Nowhere", "tz": "UTC", "now": {"temp": 58, "sky": "Partly cloudy"}, "days": [{"t": NOW + i * DAY, "hi": 62 + i, "lo": 49 + i, "rain": (10, 70, 20, 40)[i]} for i in range(4)], "href": "/weather"}
ONLY = {"NL": [{"id": "1" * 16, "title": "Norland says it turned back two patrol boats at the inner channel", "voice": "Norland Press Office", "place": "Inner Channel", "ts": NOW - 3 * HOUR}], "CO": [{"id": "2" * 16, "title": "Costera says Norland drones crossed the line twice overnight", "voice": "Costera Daily", "place": "Skerry Point", "ts": NOW - 5 * HOUR}]}
WHO = {"hours": 72, "camps": CAMPS, "tally": {"reports": 66, "camps": {"NL": 33, "CO": 21}, "outside": 9, "unplaced": 3}, "only": ONLY, "agreed": [{"id": "3" * 16, "title": "Both sides confirm ships pulled back ahead of Thursday's talks", "voice": "Global Wire", "place": "The Strait", "ts": NOW - 7 * HOUR}],
       "accounts": {"sides": [{"side": "NL", "says": "Norland's channels say its patrols are protecting shipping, and that Costera's ships crossed the line first."}, {"side": "CO", "says": "Costera's outlets say Norland is using the talks as cover to hold the inner channel."}], "agreed": "Ships from both sides have moved back ahead of Thursday's round.", "contested": "Who crossed the line first, and who the inner channel belongs to."}}
HISTORY = {"began": "1998-03", "began_note": "The first shots came after a fishing boat was seized in the inner channel.", "summary": "A quarrel over a channel that became a standoff over who may use it, and for how long.", "eras": [
    {"name": "The fishing quarrel", "from": "1998", "to": "2009", "summary": "Boats, nets and a line nobody had drawn.", "events": [{"date": "1998-03-14", "title": "A fishing boat is seized in the inner channel", "detail": "Both coasts claim the water. Nobody is hurt, and nobody backs down.", "source": "https://example.org/1998"}, {"date": "2004-06", "title": "The first talks fail", "detail": "A map offered by mediators is rejected by both sides within a week.", "source": "https://example.org/2004"}]},
    {"name": "The line", "from": "2010", "to": "2021", "summary": "A patrol line, and the first shipping lanes closed.", "events": [{"date": "2012-09-02", "title": "A patrol line is declared", "detail": "Norland publishes the line and sends ships to hold it.", "source": "https://example.org/2012"}, {"date": "2018", "title": "Insurers price the strait as a war zone", "detail": "Freight costs through the channel double in a month.", "source": "https://example.org/2018"}]},
    {"name": "The standoff", "from": "2022", "to": "now", "summary": "Drones, closures and talks that keep stopping.", "events": [{"date": "2022-11-20", "title": "The channel closes for 40 days", "detail": "The longest closure so far, ended by a grain deal.", "source": "https://example.org/2022"}, {"date": "2026-10-19", "title": "Talks resume, then pause", "detail": "A nine-day pause after an overnight incident.", "source": "https://example.org/2026"}]}]}
REPORTS = [{"id": f"{i + 16:016x}", "title": t, "domain": "kinetic" if i % 3 else "economic", "ts": NOW - i * 5 * HOUR, "severity": .35 + (i % 5) / 8, "place": p, "lat": la, "lon": lo, "source": "rss_osint", "category": "shipping"} for i, (t, p, la, lo) in enumerate((
    ("Patrol boats shadow a grain convoy through the outer lanes", "Outer Lanes", 56.2, 19.1), ("Overnight drone crossing reported near Skerry Point", "Skerry Point", 55.1, 21.3), ("Insurers hold rates steady for a second week", "The Strait", 55.4, 19.9), ("Ships pull back from the inner channel ahead of talks", "Inner Channel", 54.8, 20.5), ("Fishing fleet stays in port after a warning from both coasts", "Port Hale", 54.2, 18.7), ("Radar site comes back online after a two-day outage", "North Head", 57.0, 21.0)))]


def demo_world():
    """Where a real paper would fetch, the demo answers. Anything else that tries to reach out simply fails."""
    def nowhere(*_, **__):
        raise OSError("the demo stays on this machine")
    s.ai.ask, s.ai.web_search = asked, looked_up
    s.read_page, s.around, s.war, s.hazard_depth, s.outside_at = read_page, around, war, cyclone, nowhere
    follows = [priced("HRBR", "Harbor Freight Lines", "NYSE", 141.2, 139.9), TEAM, TOWN, {**s.conflict_card({"id": "north_strait", "name": "The Northern Strait", "esc": 61})},
               {"kind": "topic", "key": "Battery plant", "name": "Battery plant", "rows": [{"t": "New battery plant promises four thousand jobs by 2029", "u": "https://demo.invalid/story/6", "src": "Global Wire", "ts": NOW - 3 * HOUR}, {"t": "Second site named for the battery plant's suppliers", "u": "https://demo.invalid/more/9", "src": "The Ledger", "ts": NOW - 9 * HOUR}], "href": "/topic/Battery%20plant"}]
    cards = [{**c, "id": s.follow_id(c["kind"], c["key"]), "at": NOW} for c in follows]
    s.remember("follows", [{k: c[k] for k in ("id", "kind", "key", "name")} for c in cards])
    for i in range(20):  # a month of reading, so Both sides can say which way it leaned
        s.note_read(f"https://demo.invalid/old/{i}", "An older story", ("Harbor Times", "The Courier", "Northern Post", "Global Wire", "The Ledger")[i % 5 if i % 2 else 0])
    s.save("following", {"cards": cards})
    s.save("editor", {"text": "A calmer morning in the strait, a fight over rents at home, and a battery plant that wants four thousand people. Read the harbor story first: it's the one that will cost someone money by January.", "at": NOW - 40 * 60})


def main():
    s.init_db()
    s.check = lambda section: {"ok": True, "text": "This is the demo, so nothing was really tested."}
    settings.update({"PAPER_TZ": "America/New_York", "PAPER_SINCE": str((datetime.now(timezone.utc) - timedelta(days=211)).date()), "PLEX_URL": "http://demo.invalid", "PLEX_TOKEN": "demo", "PVE_URL": "http://demo.invalid", "PVE_TOKEN": "demo",
                     "PROBES": [{"group": "Sites", "name": n, "url": "http://demo.invalid/"} for n in ("My Shop", "The Club")] + [{"group": "At home", "name": n, "url": "http://demo.invalid/"} for n in ("Router", "Photos", "Backups")],
                     "MAIL_TENANT": "demo", "MAIL_CLIENT_ID": "demo", "MAIL_CLIENT_SECRET": "demo", "MAILBOXES": [{"address": "you@shop.example", "label": "Shop"}], "MONEY_URL": "http://demo.invalid", "COMMONS_URL": "http://demo.invalid", "TWILIO_ACCOUNT": "demo", "TWILIO_KEY": "demo", "TWILIO_SECRET": "demo", "WEATHER_PLACE": "Harbor City",
                     "PRODUCTS": [{"key": "shop", "name": "My Shop", "host": "shop.example"}, {"key": "club", "name": "The Club", "host": "club.example"}],
                     "AI_KEY": "demo", "OUTLET_LEANS": [{"name": n, "lean": v} for n, v in LEANS.items()]})
    s.save("news", news())
    s.save("world", world())
    s.save("media", media())
    s.save("playing", [{"title": "Harbor Nights, S3 E6", "who": "Sam", "state": "playing", "pct": 41, "device": "Living room", "mode": "direct play"}])
    s.save("probes", [{"group": g, "name": n, "url": "", "up": True, "gated": False, "status": 200, "ms": random.randint(30, 400), "error": None, "day": 100.0, "week": 99.9} for g, n in (("Sites", "My Shop"), ("Sites", "The Club"), ("At home", "Router"), ("At home", "Photos"), ("At home", "Backups"))])
    s.save("machines", {"hosts": [machine("Proxmox", "Containers", 14, 62, 48), machine("NAS", "Backups", 6, 31, 71)], "guests": [{"id": 101 + i, "type": "lxc", "name": n, "status": "running", "cpu": 3, "cores": 2, "mem": 2 ** 30, "maxmem": 2 ** 32, "disk": 0, "maxdisk": 2 ** 34, "uptime": 19 * DAY} for i, n in enumerate(("media", "photos", "paper"))],
                        "history": [{"t": NOW - i * 900, "cpu": 12 + 6 * math.sin(i / 9), "mem": 60, "io": 1} for i in range(96, 0, -1)]})
    s.save("storage", {"pools": [{"name": "tank", "size": 4 * 10 ** 12, "alloc": 2 * 10 ** 12, "health": "ONLINE", "frag": 8}], "disks": [], "backups": [{"at": NOW - 6 * HOUR, "ok": True, "status": "OK"}], "failed_tasks": [], "autostart": []})
    history("Proxmox", 14, 48, 0.02)
    history("NAS", 6, 71, 1.0)
    teams = [("Harbor", "Rangers", "101", "96"), ("Summit", "Comets", "88", "93"), ("Bay", "Pilots", "24", "17")]
    s.save("sports", [{"key": "nba", "name": "City League", "games": [{"state": "in" if i == 0 else "post", "status": "Q3 4:12" if i == 0 else "Final", "at": NOW, "home": {"name": h, "abbr": h[:3], "score": a, "record": "4-1", "won": True}, "away": {"name": v, "abbr": v[:3], "score": b, "record": "2-3", "won": False}, "note": "A made-up game.", "venue": None} for i, (h, v, a, b) in enumerate(teams)]}])
    s.save("weather", {"place": "Harbor City", "region": "Made Up", "country": "Nowhere", "lat": 40.7, "lon": -74, "tz": "UTC", "units": "F", "speed": "mph", "now": {"temp": 58, "feels": 55, "sky": "Partly cloudy", "wind": 9, "humidity": 62}, "rain_at": NOW + 9 * HOUR,
                       "hours": [{"t": NOW + i * HOUR, "temp": round(56 + 7 * math.sin(i / 24 * 6.28), 1), "rain": max(0, min(100, (i - 6) * 9 if i < 16 else 90 - (i - 16) * 8)), "sky": "Partly cloudy"} for i in range(48)],
                       "days": [{"t": NOW + i * DAY, "hi": 62 + i, "lo": 49 + i // 2, "sky": ("Partly cloudy", "Rain", "Overcast")[i % 3], "rain": (20, 70, 30)[i % 3], "rise": NOW, "set": NOW + 11 * HOUR} for i in range(7)]})
    spent = []
    for i in range(60):
        wave, day = 1 + .6 * math.sin(i / 3), (datetime.now(timezone.utc) - timedelta(days=i)).date().isoformat()
        spent += [{"day": day, "who": "Coding plan", "model": "claude-sonnet-5-5", "qty": 9e7 * wave, "unit": "tokens", "worth": 41 * wave, "charged": 0}, {"day": day, "who": "Research agent", "model": "claude-opus-5-5", "qty": 2e7 * wave, "unit": "tokens", "worth": 12 * wave, "charged": 0},
                  {"day": day, "who": "This paper", "model": "claude-haiku-5-5", "qty": 3e5, "unit": "tokens", "worth": .11, "charged": .11}, {"day": day, "who": "LiveKit", "model": "calls", "qty": 240 * wave, "unit": "minutes", "worth": 2.4 * wave, "charged": 0}]
    s.save("costs", [{"name": "Twilio", "cents": 2140, "per": "month", "note": "From Twilio, last month"}])
    made_up = [{"symbol": "HRBR", "shares": "40", "buy": "112.50", "tape": "yes"}, {"symbol": "SMMT", "shares": "12", "buy": "302.10", "tape": "yes"}, {"symbol": "BAY-USD", "shares": "0.4", "buy": "", "tape": "yes"}, {"symbol": "PILT", "shares": "", "buy": "", "tape": "yes"}]
    prices = {"HRBR": ("Harbor Freight Lines", 141.2, 139.9), "SMMT": ("Summit Foods", 284.75, 288.1), "BAY-USD": ("Bay Coin", 8120.0, 8010.0), "PILT": ("Pilot Air", 54.3, 53.6)}
    settings.update({"HOLDINGS": made_up})
    s.save("portfolio", {**s.invest.report(s.invest.typed(made_up), {k: {"name": n, "price": p, "prev": b, "currency": "USD"} for k, (n, p, b) in prices.items()}, {"USD": 1.0}), "missing": []})
    s.save("usage", {**s.usage.report([{**r, "source": "ledger"} for r in spent], s.utc_day()), "missing": []})
    s.save("feed", feed())
    s.save("mail", {"read": 1, "failed": [], "triage_error": None})
    mail()
    s.set_costs([("Hosting", 4000, "month"), ("Email", 1200, "month"), ("Domains", 3600, "year"), ("Ads", None, "month")])
    demo_world()
    print("The demo is at http://127.0.0.1:8096. Every word of it is made up.", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8096), s.Handler).serve_forever()


if __name__ == "__main__":
    main()
