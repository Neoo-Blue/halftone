"""Election watch: the next US election first, the world's as they come, and nothing at all when nothing is on.

WARROOM follows every race and the world's calendar. This turns numbers into what a reader wants to know: which seat
decides each chamber, what's likely to change hands, where the signals disagree, what to watch and when, and on the night
what a trailing candidate still needs. All of it is sums on the race data, so it's right at every stage and costs nothing.
Everything that decides what's shown is worked out from the dates on every read, so the desk leaves on its own however
old the last snapshot is.

Candidates, parties and countries are strangers' words, so only known fields survive, as plain text.
"""
import re
import unicodedata
from collections import Counter
from datetime import date, timedelta

from find import text

US_BEFORE, US_AFTER = 60, 14  # days around a US election that the desk stays up
WORLD_BEFORE, WORLD_AFTER = 14, 7  # the same for an election abroad
TERRITORIES = {"US", "AS", "GU", "MP", "PR", "VI"}  # they vote with the US and report apart from it
PHASES = ("voting", "counting", "upcoming", "results")
NAMES = {"house": "House", "senate": "Senate", "governor": "Governors", "president": "President"}
PARTIES = {"D": "Democrats", "R": "Republicans"}
SIDES = {"D": "Democratic", "R": "Republican"}
FORECASTERS = {"cook": "Cook", "sabato": "Sabato", "insideelections": "Inside Elections", "splitticket": "Split Ticket", "ddhq": "DDHQ"}
TIE = "R"  # the vice president's party, who breaks a 50-50 Senate, until January 2029
GAP = .12  # how far apart the model and the market have to be before that's worth saying
# When each state's last polls close, in hours after the first close at 6pm Eastern, because a state can't be called before then. From 270toWin's table for 2026.
CLOSES = ((1, "GA IN KY SC VA VT"), (1.5, "NC OH WV"), (2, "AL CT DC DE FL IL MA MD ME MO MS NH NJ OK PA RI TN"), (2.5, "AR"), (3, "AZ CO IA KS LA MI MN ND NE NM NY SD TX WI WY"), (4, "MT NV UT"), (5, "CA ID OR WA"), (6, "HI"), (7, "AK"))
RACE = re.compile(r"(?:H-[A-Z]{2}-(?:\d{2}|AL)|[SGP]-[A-Z]{2})")
ELECTION = re.compile(r"[a-z0-9-]{2,40}")


def share(p):
    """A chance as a whole percent, rounding the way the page does, so a number reads the same everywhere."""
    return int(p * 100 + .5)


def number(value, low=0.0, high=100.0):
    """A stranger's number, or None. bool counts as an int here, and NaN fails every comparison."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
        return None
    return value if low <= value <= high else None


def day(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def person(c):
    return {"n": text(c.get("name"), 80), "p": c["party"] if c.get("party") in ("D", "R", "I") else "O"}


def table(value):
    return value if isinstance(value, dict) else {}


def race(r):
    """One race as the page reads it. Trust boundary: nothing else in the row gets through."""
    key = str(r.get("key") or "")
    if not RACE.fullmatch(key) or r.get("kind") not in NAMES:
        return None
    won, lead, polls, held = table(r.get("winner")), table(r.get("leader")), table(r.get("polls")), table(r.get("holder"))
    runners = [{**person(c), "votes": number(c.get("votes"), 0, 1e9) or 0, "pct": number(c.get("pct")) or 0, "won": c.get("winner") is True} for c in (r.get("candidates") or [])[:40] if isinstance(c, dict) and c.get("name")]
    noms = {k: text(v, 80) for k, v in table(r.get("nominees")).items() if k in ("D", "R", "I") and v}
    for c in runners:  # a nominee can be missing while the candidate is listed
        noms.setdefault(c["p"], c["n"]) if c["p"] in ("D", "R") else None
    return {
        "key": key, "kind": r["kind"], "state": key[2:4], "where": text(r.get("state_name"), 40), "seat": text(r.get("name"), 80), "inc": r.get("incumbent_party") if r.get("incumbent_party") in ("D", "R", "I") else None,
        "noms": noms, "holder": {"n": text(held.get("name"), 80), "since": text(held.get("since"), 10)} if held.get("name") else None,
        "ratings": {k: text(v, 20) for k, v in table(r.get("ratings")).items() if k in FORECASTERS and text(v, 20)}, "volume": number(table(r.get("market")).get("volume"), 0, 1e11),
        "rep": number(r.get("reporting")) or 0, "won": person(won) if won.get("name") else None, "lead": {**person(lead), "pct": number(lead.get("pct"))} if lead.get("name") else None,
        "at": number(r.get("called_at"), 0, 1e11), "pd": number(table(r.get("prob")).get("D"), 0, 1), "rating": text(r.get("rating"), 20), "md": number(table(r.get("market")).get("d"), 0, 1),
        "poll": {"d": number(polls.get("d")), "r": number(polls.get("r")), "n": number(polls.get("n"), 0, 1e4), "last": text(polls.get("last"), 10)} if number(polls.get("d")) is not None and number(polls.get("r")) is not None else None,
        "runners": sorted(runners, key=lambda c: -c["votes"])[:6],
    }


def us(d):
    """WARROOM's US answer, cleaned, or None if it isn't one."""
    if not day(d.get("date")):
        return None
    when = table(d.get("schedule"))
    control = {k: {"seats": number(c.get("seats"), 0, 1000), "majority": number(c.get("majority"), 0, 1000), "held": {p: number(n, 0, 1000) or 0 for p, n in table(c.get("holdover")).items() if p in ("D", "R", "I")}, "md": number(table(c.get("market")).get("d"), 0, 1), "mr": number(table(c.get("market")).get("r"), 0, 1)}
               for k, c in table(d.get("control")).items() if k in NAMES and isinstance(c, dict)}
    ballot = table(d.get("generic_ballot"))
    return {"id": text(d.get("id"), 20), "name": text(d.get("name"), 60), "date": str(d["date"])[:10], "presidential": d.get("presidential") is True, "live": d.get("live") is True, "read": number(table(d.get("updated")).get("races"), 0, 1e11), "phase": d.get("phase") if d.get("phase") in ("campaign", "voting", "counting", "final") else "campaign",
            "schedule": {k: number(when.get(k), 0, 1e11) for k in ("polls_open", "first_close", "last_close")}, "control": control, "ballot": {"d": number(ballot.get("d")), "r": number(ballot.get("r")), "last": text(ballot.get("last"), 10)} if ballot.get("d") is not None else None,
            "races": [r for r in map(race, [x for x in d.get("races") or [] if isinstance(x, dict)]) if r], "sources": [text(table(s).get("label"), 60) for s in d.get("sources") or []][:8]}


def world(items, today):
    """Elections abroad worth a place right now. One date in one country is one vote, however many offices are on it."""
    found = {}
    for e in items:
        start, end, phase = day(e.get("start")), day(e.get("end")), e.get("phase")
        if not isinstance(e, dict) or e.get("featured") or e.get("status") != "Confirmed" or e.get("iso2") in TERRITORIES or not start or not end or not ELECTION.fullmatch(str(e.get("id"))) or phase not in PHASES:
            continue
        got = found.setdefault((e.get("country"), e["start"]), {
            "id": e["id"], "country": text(e.get("country"), 60), "iso2": text(e.get("iso2"), 2), "offices": [], "start": str(e["start"])[:10], "end": str(e["end"])[:10], "phase": phase, "line": text(e.get("outcome_line"), 160),
            "snap": e.get("snap") is True, "lat": number(e.get("lat"), -90, 90), "lon": number(e.get("lon"), -180, 180), "outcome": e.get("has_outcome") is True})
        got["offices"].append(text(e.get("institution"), 80))
    return [e for e in found.values() if abroad_on(e, today)]


def abroad_on(e, today):
    """By the dates alone: a phase in an old snapshot can't hold the desk open."""
    return (day(e["start"]) - today).days <= WORLD_BEFORE and (today - day(e["end"])).days <= WORLD_AFTER


def us_on(when, today):
    held = day(when)
    return bool(held) and held - timedelta(days=US_BEFORE) <= today <= held + timedelta(days=US_AFTER)


def lean(r):
    """Who a race leans to before there's a count: the composite rating, or the model's number if there isn't one."""
    hit = re.search(r"\b([DR])$", r["rating"])
    if hit or r["rating"]:
        return hit.group(1) if hit else "T"
    p = r["pd"] if r["pd"] is not None else r["md"]
    return "T" if p is None or .45 < p < .55 else "D" if p > .5 else "R"


def chamber(rows, kind, control):
    won, ahead, leans = Counter(), Counter(), Counter()
    for r in rows:
        if r["won"]:
            won[r["won"]["p"]] += 1
        elif r["lead"]:
            ahead[r["lead"]["p"]] += 1
        else:
            leans[lean(r)] += 1
    held = control.get("held") or {}
    seats, majority = (control.get("seats"), control.get("majority")) if held or kind == "house" else (len(rows), None)
    # The independents already in the Senate caucus with Democrats, and a newly elected one hasn't said. The vice president breaks a tie, so 50 is enough for that party.
    tally = {"D": won["D"] + held.get("D", 0) + held.get("I", 0), "R": won["R"] + held.get("R", 0)}
    decided = next((p for p, n in tally.items() if majority and n >= majority - (kind == "senate" and p == TIE)), None)
    return {"kind": kind, "name": NAMES[kind], "seats": seats, "majority": majority, "up": len(rows), "held": held, "won": dict(won), "ahead": dict(ahead), "lean": dict(leans), "md": control.get("md"), "mr": control.get("mr"), "decided": decided, "called": sum(won.values())}


def surname(name):
    plain_name = "".join(c for c in unicodedata.normalize("NFKD", name or "") if not unicodedata.combining(c))
    words = re.sub(r"[.,]", "", plain_name).lower().split()
    return next((w for w in reversed(words) if w not in ("jr", "sr", "ii", "iii", "iv")), "")


def open_seat(r):
    """Nobody holds it who's on the ballot. Nominees alone can miss a sitting member, so the whole field is checked, and with no field there's nothing to say."""
    field = {surname(n) for n in [*r["noms"].values(), *(c["n"] for c in r["runners"])]}
    return bool(r["holder"] and field) and surname(r["holder"]["n"]) not in field


def side_of(r):
    """Who has this race for now: the call, then the count, then the forecast."""
    return (r["won"] or r["lead"] or {}).get("p") or lean(r)


def chance(r):
    """Democrats' chance, as near as anything can say at this moment."""
    if r["won"]:
        return {"D": 1.0, "R": 0.0}.get(r["won"]["p"], .5)
    if r["lead"] and r["rep"]:
        return {"D": .75, "R": .25}.get(r["lead"]["p"], .5)
    return r["pd"] if r["pd"] is not None else r["md"] if r["md"] is not None else .5


def ladder(rows, start, majority):
    """Rank the races from surest Democratic to surest Republican, and count down to a majority. The race you land on is the tipping point: if every likelier result holds, that one decides the chamber."""
    need = (majority or 0) - start
    order = sorted(rows, key=chance, reverse=True)
    if not 0 < need <= len(order):
        return None
    tip = order[need - 1]
    return {"need": need, "of": len(order), "start": start, "tip": row(tip), "chance": round(chance(tip), 3), "steps": [{"key": r["key"], "state": r["state"], "v": round((chance(r) - .5) * 2, 2)} for r in order] if len(order) < 60 else []}


def gains(rows):
    """Seats that have gone, or look like going, to the party that doesn't hold them."""
    out = {"D": [], "R": []}
    for r in rows:
        side = side_of(r)
        if side in out and r["inc"] in out and side != r["inc"]:
            out[side].append({"key": r["key"], "state": r["state"], "seat": r["seat"]})
    return out


def polls_against(r):
    p = r["poll"]
    return bool(p) and p["d"] != p["r"] and lean(r) in SIDES and (p["d"] > p["r"]) != (lean(r) == "D")


def signals(races):
    """Where the numbers don't tell one story, which is usually where the real uncertainty is."""
    big = [r for r in races if r["kind"] != "house" and not r["won"]]
    gaps = sorted((r for r in big if r["pd"] is not None and r["md"] is not None and abs(r["pd"] - r["md"]) >= GAP), key=lambda r: -abs(r["pd"] - r["md"]))
    against = [r for r in big if polls_against(r)]
    split = [r for r in big if len({v[-1] if v[-1] in "DR" else "T" for v in r["ratings"].values()}) > 1]
    return {"gaps": [{**row(r), "gap": round(r["md"] - r["pd"], 3)} for r in gaps[:4]], "against": [row(r) for r in against[:3]], "split": [row(r) for r in sorted(split, key=closeness)[:4]], "splits": len(split)}


def hours(races, first):
    """The night in order: when each batch of polls closes, and the closest races that go with it."""
    if not first:
        return []
    out = []
    for step, states in CLOSES:
        names = states.split()
        rows = sorted((r for r in races if r["kind"] != "house" and r["state"] in names), key=closeness)[:3]
        out.append({"at": int(first + step * 3600), "states": names, "watch": [{"key": r["key"], "seat": r["seat"], "rating": r["rating"]} for r in rows if closeness(r) < .4]})
    return out


def chase(r):
    """On the night: how much is left, and what the trailing candidate needs of it. An estimate, because "counted" is a share of a vote nobody knows yet."""
    two = r["runners"][:2]
    if r["won"] or len(two) < 2 or not 0 < r["rep"] < 100 or not two[0]["votes"]:
        return None
    counted = sum(c["votes"] for c in r["runners"])
    left, gap = counted * (100 / r["rep"] - 1), two[0]["votes"] - two[1]["votes"]
    return {"lead": two[0]["n"], "trail": two[1]["n"], "gap": gap, "left": int(round(left, -2)), "need": round((left + gap) / (2 * left), 3) if left else None}


def place(r, s):
    """How near a race is to the one that decides its chamber."""
    rows, c = [x for x in s["races"] if x["kind"] == r["kind"]], s["control"].get(r["kind"]) or {}
    held = c.get("held") or {}
    lad = ladder(rows, held.get("D", 0) + held.get("I", 0), c.get("majority")) if held or r["kind"] == "house" else None
    if not lad:
        return None
    order = sorted(rows, key=chance, reverse=True)
    return {"off": [x["key"] for x in order].index(r["key"]) - (lad["need"] - 1), "need": lad["need"], "of": lad["of"], "tip": lad["tip"]["seat"], "tipkey": lad["tip"]["key"]}


def forecasters(r):
    return [{"who": FORECASTERS[k], "rating": v} for k, v in r["ratings"].items()]


def said(names):
    return f"{names[0]}" if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def reading(r):
    """A race in sentences: who has it, what's at stake, and where the signals part."""
    out = []
    side, name = lean(r), r["noms"].get(lean(r))
    if r["won"]:
        gain = r["inc"] in SIDES and r["won"]["p"] != r["inc"]
        out.append(r["won"]["n"] + (f" wins, a {SIDES[r['won']['p']]} gain." if gain and r["won"]["p"] in SIDES else " wins."))
    race_left = chase(r)
    if race_left:
        need = race_left["need"]
        verdict = f"{race_left['trail']} would need {share(need)}% of what's left" if need is not None and need <= 1 else f"{race_left['trail']} can't catch up on this estimate"
        ahead = f"{race_left['lead']} leads by {race_left['gap']:,} votes" if race_left["gap"] else f"{race_left['lead']} and {race_left['trail']} are level"
        out.append(f"{ahead}, with about {race_left['left']:,} still out. {verdict}." if race_left["gap"] else f"{ahead}, with about {race_left['left']:,} still out.")
    elif r["lead"] and not r["won"]:
        out.append(f"{r['lead']['n']} is ahead with {r['rep']:.0f}% counted, and it hasn't been called.")
    elif not r["won"] and r["rating"]:
        rating = r["rating"].replace("Tossup", "Toss-up")
        grade = {"Lean": "Leans", "Tilt": "Tilts"}.get(rating.split(" ")[0], rating.split(" ")[0])
        out.append(f"{grade} {SIDES[side]}, with {name} favoured." if name and side in SIDES else f"{rating}.")
    if not r["won"]:
        if r["holder"] and not open_seat(r):
            out.append(f"{r['holder']['n']} has held it since {r['holder']['since'][:4]}." if r["holder"]["since"] else "")
        elif r["holder"]:
            out.append(f"An open seat: {r['holder']['n']} isn't on the ballot.")
        if r["inc"] in SIDES and side in SIDES and side != r["inc"] and not r["lead"]:
            out.append(f"That would take it from the {PARTIES[r['inc']]}.")
    if r["pd"] is not None and r["md"] is not None and abs(r["pd"] - r["md"]) >= GAP and not r["won"]:
        surer = "Bettors are surer of Democrats than the model" if r["md"] > r["pd"] else "The model is surer of Democrats than bettors are"
        out.append(f"{surer}, {share(max(r['md'], r['pd']))}% to {share(min(r['md'], r['pd']))}%.")
    if not r["won"] and not r["lead"] and polls_against(r):
        out.append(f"The polls point the other way, {r['poll']['d']} to {r['poll']['r']}.")
    calls = r["ratings"]
    camps = {}
    for who, rating in calls.items():
        camps.setdefault(rating.replace("Tossup", "toss-up"), []).append(FORECASTERS[who])
    if len({v[-1] if v[-1] in "DR" else "T" for v in calls.values()}) > 1 and not r["won"]:
        out.append("Forecasters split: " + "; ".join(f"{said(who)} {'say' if len(who) > 1 else 'says'} {rating}" for rating, who in camps.items()) + ".")
    return [x for x in out if x]


def ink(r):
    """How a race prints on the map, from -1 (surely Republican) to 1 (surely Democratic). A called race is solid, a count in progress leans by its lead, and otherwise it's the forecast."""
    if r["won"]:
        return {"D": 1, "R": -1}.get(r["won"]["p"], 0)
    if r["lead"]:
        return {"D": .5, "R": -.5}.get(r["lead"]["p"], 0)
    return round((r["pd"] - .5) * 2, 2) if r["pd"] is not None else 0


def closeness(r):
    if r["lead"] and r["rep"]:
        second = next((c["pct"] for c in r["runners"] if c["n"] != r["lead"]["n"]), 0)
        return abs((r["lead"]["pct"] or 0) - second) / 100
    return abs(r["pd"] - .5) if r["pd"] is not None else 1


def row(r):
    """A race in a list, without its full field of candidates."""
    return {**{k: r[k] for k in ("key", "kind", "state", "where", "seat", "noms", "rep", "won", "lead", "pd", "md", "rating", "poll", "at")}, "note": " ".join(reading(r)[:2]), "ink": ink(r)}


def odds_line(houses):
    picks = [(c["name"], "D" if c["md"] >= c["mr"] else "R", max(c["md"], c["mr"])) for c in houses if c.get("md") is not None and c.get("mr") is not None]
    if not picks:
        return ""
    parts = [f"{PARTIES[p]} at {share(n)}% for the {name}" for name, p, n in picks]
    return f"Betting markets have {' and '.join(parts)}."


def headline(s, today):
    """What to say at the top, from the numbers alone, so it's right at every stage of the night and costs nothing."""
    vote = "election" if s["presidential"] else "midterms"
    are = "is" if s["presidential"] else "are"
    left = (day(s["date"]) - today).days
    houses = [c for c in s["chambers"] if c["kind"] in ("house", "senate")]
    if s["phase"] == "campaign":
        title = f"{left} days to the {vote}" if left > 1 else f"The {vote} {are} tomorrow" if left == 1 else f"The {vote} {are} today"
        return {"title": title, "line": odds_line(houses)}
    if s["phase"] == "voting":
        return {"title": "Polls are open", "line": odds_line(houses)}
    done = [f"{PARTIES[c['decided']]} win the {c['name']}" for c in houses if c["decided"]]
    called, races = sum(c["called"] for c in houses), sum(c["up"] for c in houses)
    counts = [f"{c['name']}: Democrats {c['won'].get('D', 0)}, Republicans {c['won'].get('R', 0)}" for c in houses]
    title = ". ".join(done) if done else "Counting the votes" if not called else f"{called} of {races} races called"
    won = {c["name"]: c["decided"] for c in houses if c["decided"]}
    # for a one-line glance: "Democrats win Congress", or "House D · Senate R" when they split
    short = (f"{PARTIES[next(iter(won.values()))]} win Congress" if len(won) == len(houses) == 2 and len(set(won.values())) == 1
             else " \u00b7 ".join(f"{name} {party}" for name, party in won.items()) if won else title)
    return {"title": title, "short": short, "line": ". ".join(counts) + "." if counts else ""}


def phase(s, now):
    """From the clock, not the snapshot, so an old copy can't say the polls are still to open."""
    when = s["schedule"]
    if s["phase"] == "final" or not now or not when.get("polls_open") or not when.get("first_close"):
        return s["phase"]
    return "counting" if now >= when["first_close"] else "voting" if now >= when["polls_open"] else "campaign"


def summary(data, today, now=None):
    """What the page polls, every 30 seconds while votes are counted, or None, and the desk disappears."""
    data = data or {}
    abroad = [e for e in data.get("world") or [] if abroad_on(e, today)]
    abroad.sort(key=lambda e: (PHASES.index(e["phase"]), e["start"]))
    s = data.get("us")
    if not (s and us_on(s["date"], today)):
        return {"us": None, "world": abroad} if abroad else None
    s = {**s, "phase": phase(s, now)}
    races = s["races"]
    kinds = [k for k in NAMES if any(r["kind"] == k for r in races)]
    chambers = [chamber([r for r in races if r["kind"] == k], k, s["control"].get(k) or {}) for k in kinds]
    big = sorted((r for r in races if r["kind"] != "house" and not r["won"]), key=closeness)[:6]
    house = sorted((r for r in races if r["kind"] == "house" and not r["won"]), key=closeness)[:6]
    calls = sorted((r for r in races if r["won"] and r["at"]), key=lambda r: -r["at"])[:8]
    state_map = {k: {} for k in kinds}
    for r in races:
        state_map[r["kind"]].setdefault(r["state"], []).append(ink(r))
    for c in chambers:
        rows = [r for r in races if r["kind"] == c["kind"]]
        held = c["held"]
        c["ladder"] = ladder(rows, held.get("D", 0) + held.get("I", 0), c["majority"]) if c["majority"] else None
        c["gains"] = gains(rows)
    out = {**{k: s[k] for k in ("id", "name", "date", "phase", "presidential", "schedule", "ballot", "sources")}, "live": s.get("live") is True, "read": s.get("read"), "chambers": chambers, "map": state_map, "closest": [row(r) for r in big], "house": [row(r) for r in house], "calls": [row(r) for r in calls],
           "signals": signals(races), "hours": hours(races, s["schedule"].get("first_close"))}
    return {"us": {**out, **headline({**s, "chambers": chambers}, today)}, "world": abroad}


def polls(d):
    """Every poll of a race, newest first. A poll paid for by a side says so."""
    rows = [{"who": text(p.get("pollster"), 60), "end": text(p.get("end"), 10), "n": number(p.get("n"), 0, 1e6), "pop": text(p.get("pop"), 4), "partisan": text(p.get("partisan"), 4), "d": number(p.get("D")), "r": number(p.get("R")), "url": p["url"] if str(p.get("url") or "").startswith("https://") else None} for p in d.get("polls_list") or [] if isinstance(p, dict)]
    return sorted((p for p in rows if p["d"] is not None and p["r"] is not None and day(p["end"])), key=lambda p: p["end"], reverse=True)[:30]


def outcome(d):
    """Who won abroad, from WARROOM. Wikipedia's results box under CC BY-SA, so it keeps its link and its credit."""
    rows = [{"party": text(r.get("party"), 80), "person": text(r.get("person"), 80) if r.get("person") not in (None, "None") else "", "seats": number(r.get("seats_won"), 0, 1e4), "pct": number(r.get("pct"))} for r in d.get("rows") or [] if isinstance(r, dict) and r.get("party")]
    url = d.get("url") if isinstance(d.get("url"), str) and d["url"].startswith("https://en.wikipedia.org/") else None
    rows = [r for r in rows if r["seats"] is not None or r["pct"] is not None]
    return {"decided": d.get("decided") is True, "line": text(d.get("line"), 160), "turnout": text(d.get("turnout"), 40), "rows": rows[:10], "seats": number(d.get("seats_total"), 0, 1e4), "majority": number(d.get("majority"), 0, 1e4), "url": url}
