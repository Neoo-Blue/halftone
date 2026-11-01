"""Who is carrying a story, by where each outlet sits.

A rating is about an outlet's overall slant, never about one story, and it's an opinion. These are a starting point, drawn
from where the public media bias charts broadly agree, and Settings can change any of them. Outlets abroad and the trade
press aren't rated, because an American left and right doesn't describe them.
"""
from collections import Counter

LEFT, LEAN_LEFT, CENTER, LEAN_RIGHT, RIGHT = "left", "lean left", "center", "lean right", "right"
SCALE = (LEFT, LEAN_LEFT, CENTER, LEAN_RIGHT, RIGHT)
SIDE = {LEFT: "l", LEAN_LEFT: "l", CENTER: "c", LEAN_RIGHT: "r", RIGHT: "r"}
RATED = {
    **dict.fromkeys(("Daily Beast", "Democracy Now", "HuffPost", "MS NOW", "Mother Jones", "Salon", "Slate", "The Intercept", "The Nation", "Vox"), LEFT),
    **dict.fromkeys(("ABC News", "Al Jazeera", "Axios", "Bloomberg", "CBS News", "NBC News", "New York Times", "NPR", "Politico", "The Atlantic", "The Guardian", "Time"), LEAN_LEFT),
    **dict.fromkeys(("BBC", "CNBC", "Christian Science Monitor", "Financial Times", "MarketWatch", "NewsNation", "PBS NewsHour", "The Hill"), CENTER),
    **dict.fromkeys(("New York Post", "Reason", "The American Conservative", "The Dispatch", "The Free Press", "Washington Examiner", "Washington Times"), LEAN_RIGHT),
    **dict.fromkeys(("American Spectator", "Breitbart", "Daily Signal", "Daily Wire", "Fox News", "Free Beacon", "National Review", "The Blaze", "The Federalist"), RIGHT),
}
WAIT = 3 * 3600  # a story gets this long for the other side to reach it before anyone calls it a blind spot
ENOUGH = {"l": 4, "r": 3}  # the wire carries more outlets on the left, so it takes more of them to mean something


def rated(source, own=None):
    return (own or {}).get(source) or RATED.get(source)


def count(outlets, own=None):
    """[left, center, right]. Outlets with no rating aren't on the scale at all."""
    tally = Counter(SIDE.get(rated(o.get("src"), own)) for o in outlets)
    return [tally["l"], tally["c"], tally["r"]]


def reach(stories, words, own=None):
    """How far each story has gone across the scale. Each side writes its own headlines, so the same event can sit in two stories on the wire:
    two rare words in common within two days counts as one event here. It stays two stories on the page, and only the count gets more honest."""
    rows = [{w for o in s["outlets"] for w in words(o.get("t") or "")} for s in stories]
    seen = Counter(w for r in rows for w in r)
    rare = max(5, len(stories) // 60)
    rows = [{w for w in r if seen[w] <= rare} for r in rows]
    where = {}
    for i, r in enumerate(rows):
        for w in r:
            where.setdefault(w, []).append(i)
    out = []
    for i, r in enumerate(rows):
        shared = Counter(j for w in r for j in where[w] if j != i)
        kin = [j for j, n in shared.items() if n >= 2 and abs(stories[i]["ts"] - stories[j]["ts"]) < 172800]
        out.append(count(list({o["src"]: o for s in (stories[i], *(stories[j] for j in kin)) for o in s["outlets"]}.values()), own))
    return out


def facing(outlets, words, own=None):
    """The same story from each side, the two headlines furthest apart. Wire copy runs everywhere word for word, and setting that against itself shows nothing."""
    side = lambda k: [o for o in outlets if SIDE.get(rated(o.get("src"), own)) == k and o.get("t")]
    pairs = [(len(words(a["t"]) & words(b["t"])) / (min(len(words(a["t"])), len(words(b["t"]))) or 1), a, b) for a in side("l") for b in side("r")]
    pairs = [p for p in pairs if p[0] < 0.7]
    if not pairs:
        return None
    _, left, right = min(pairs, key=lambda p: p[0])
    return {k: {"src": o["src"], "u": o["u"], "t": o["t"]} for k, o in (("left", left), ("right", right))}


def blind(stories, now, words, own=None):
    """Stories one side is carrying and the other isn't, as far as these feeds can show. Each side writes its own headlines, so a story only
    counts once nothing on the other side shares two of its rare words: saying nobody covered something is a claim that has to hold up."""
    heads = [(SIDE.get(rated(o.get("src"), own)), words(o.get("t") or "")) for s in stories for o in s["outlets"]]
    seen = Counter(w for _, ws in heads for w in ws)
    rare = max(6, len(heads) // 60)
    found = {"l": [], "r": []}
    for s in stories:
        left, _, right = s.get("lean") or count(s["outlets"], own)
        side = "l" if not right and left >= ENOUGH["l"] else "r" if not left and right >= ENOUGH["r"] else None
        if not side or now - s.get("first", s["ts"]) < WAIT:
            continue
        mine = {w for o in s["outlets"] for w in words(o.get("t") or "") if seen[w] <= rare}
        other = "r" if side == "l" else "l"
        if not any(sd == other and len(mine & ws) >= 2 for sd, ws in heads):
            found[side].append(s)
    picked = {}
    for k, rows in found.items():
        kept, used = [], set()
        for s in sorted(rows, key=lambda s: (-len(s["outlets"]), -s["ts"])):  # one event once, however many headlines it has
            mine = {w for o in s["outlets"] for w in words(o.get("t") or "") if seen[w] <= rare}
            if len(mine & used) < 2:
                kept.append(s)
                used |= mine
        picked[k] = kept[:6]
    return picked
