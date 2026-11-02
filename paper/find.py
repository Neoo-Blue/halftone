"""Looking past the paper's own pages, and working out what kind of thing was asked about.

A stock, a team, a town and a war aren't followed the same way, so a search first asks what the words are. Each source
here is free and needs no key, and each is told the reader's words and nothing else.

Every answer is a stranger's. Only known fields survive, as plain text with a length limit, and an address only if it is a
web address, so the page can print all of it and the paper can open any of it in the reader.

Nothing here fetches for itself. The server hands in `at`, which goes through the same public-address checks as the
reader, so an odd link or a redirect in an answer can't walk the paper onto its own network.
"""
import email.utils
import html
import json
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET

WIKI = "https://en.wikipedia.org/"
BING = "https://www.bing.com/news/search?"
HN = "https://hn.algolia.com/api/v1/"
TALK_DAYS = 90
ARXIV = "https://export.arxiv.org/api/query?"
GITHUB = "https://api.github.com/search/repositories?"
POLY = "https://gamma-api.polymarket.com/"
QUOTE_FIND = "https://query2.finance.yahoo.com/v1/finance/search?"
CHART = "https://query1.finance.yahoo.com/v8/finance/chart/"
TEAM_FIND = "https://site.web.api.espn.com/apis/search/v2?"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/"
GEO = "https://geocoding-api.open-meteo.com/v1/search?"

#: Yahoo gives anything with the word in its name about 20,000: "Ukraine" finds a Frankfurt ETF. Real matches score far higher.
STRONG_MATCH = 50_000
MARKET_KINDS = {"EQUITY", "ETF", "CRYPTOCURRENCY", "INDEX", "FUTURE"}
MINOR_UNITS = {"GBp": "GBP", "ZAc": "ZAR", "ILA": "ILS"}  # these markets quote in hundredths
BIG_TOWN = 50_000  # Arsenal is also a village of 2,600 in Mauritius
ATOM = "{http://www.w3.org/2005/Atom}"


def text(value, most=300):
    """A stranger's words as plain text. [^<>]: a long run of < can't make the pattern backtrack."""
    words = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^<>]+>", " ", str(value or "")))).strip()
    return words if len(words) <= most else words[:most].rsplit(" ", 1)[0] + "..."


def link(url):
    """An address the page can offer, or None. Anything else in an answer's url field stays out of an href."""
    return url if isinstance(url, str) and len(url) <= 1000 and re.match(r"https?://[^\s\\]+$", url) else None


def host(url):
    try:
        return urllib.parse.urlsplit(str(url)).hostname or ""
    except ValueError:  # "https://[bad/": strangers' addresses can make urlsplit raise
        return ""


def row(title, url, src, summary="", ts=None, **more):
    u, t = link(url), text(title, 200)
    if not u or not t or t.lower().removeprefix("www.") == host(u).removeprefix("www."):  # a title that is only its address says nothing
        return None
    return {"t": t, "u": u, "src": text(src, 60), "sum": text(summary, 280), "ts": ts, **more}


def rows(found, most):
    return [r for r in found if r][:most]


def terms(q):
    return [w for w in re.findall(r"[^\W_]+", q.lower()) if len(w) > 1]


def names(q, *texts):
    """Every word of the search is in these: the test that keeps a loose match off the page."""
    words = terms(q)
    seen = set(terms(" ".join(str(t or "") for t in texts)))
    return bool(words) and all(w in seen for w in words)


def stamp(value):
    try:
        return int(email.utils.parsedate_to_datetime(value).timestamp())
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------- what was asked about

def wiki(q, at):
    hits = at(f"{WIKI}w/rest.php/v1/search/title?" + urllib.parse.urlencode({"q": q, "limit": 1}), WIKI).get("pages") or []
    if not hits:
        return None
    page = at(f"{WIKI}api/rest_v1/page/summary/" + urllib.parse.quote(str(hits[0]["key"]), safe=""), WIKI)
    if page.get("type") != "standard" or not names(q, page.get("title"), page.get("description"), str(page.get("extract"))[:200]):
        return None  # a disambiguation page, or a title that only sounds like the search
    url = link(((page.get("content_urls") or {}).get("desktop") or {}).get("page"))
    return url and {"kind": "thing", "name": text(page.get("title"), 80), "about": text(page.get("description"), 120), "text": text(page.get("extract"), 520),
                    "img": link((page.get("thumbnail") or {}).get("source")), "url": url}


def priced(symbol, at):
    """A month of closes, for the price and the line under it."""
    found = at(f"{CHART}{urllib.parse.quote(symbol, safe='')}?range=1mo&interval=1d", CHART)["chart"]["result"][0]
    meta, closes = found["meta"], found["indicators"]["quote"][0]["close"]
    closes = [float(c) for c in closes if isinstance(c, (int, float))][-31:]
    currency = str(meta.get("currency") or "")
    unit = 100 if currency in MINOR_UNITS else 1
    price = float(meta["regularMarketPrice"]) / unit
    closes = [round(c / unit, 4) for c in closes]
    currency = MINOR_UNITS.get(currency, currency)
    if not re.fullmatch(r"[A-Z]{3}", currency) or price <= 0:
        raise ValueError("not a price")
    prev = closes[-2] if len(closes) > 1 else None
    return {"kind": "market", "key": symbol, "name": text(meta.get("shortName") or meta.get("longName") or symbol, 60), "price": price, "prev": prev, "currency": currency,
            "closes": closes, "where": text(meta.get("fullExchangeName"), 40)}


def market(q, at, clean):
    quotes = at(QUOTE_FIND + urllib.parse.urlencode({"q": q, "quotesCount": 3, "newsCount": 0}), QUOTE_FIND).get("quotes") or []
    ticker = q.strip().upper()
    for x in quotes:
        strong = (x.get("score") or 0) >= STRONG_MATCH and x.get("quoteType") in MARKET_KINDS and names(q, x.get("shortname"), x.get("longname"), x.get("symbol"))
        if strong or x.get("symbol") == ticker:
            return priced(clean(x["symbol"]), at)
    return None


def _score(side):
    return side.get("score", {}).get("displayValue") if isinstance(side.get("score"), dict) else side.get("score")


def _game(event, tid):
    """One game as the page says it: who, the score if there is one, and how it came out for this team."""
    c = event["competitions"][0]
    state = c["status"]["type"]
    sides = {s.get("homeAway"): s for s in c["competitors"]}
    home, away = sides["home"], sides["away"]
    name = lambda s: text((s.get("team") or {}).get("shortDisplayName") or (s.get("team") or {}).get("displayName"), 40)
    mine = home if str(home.get("id")) == tid else away
    other = away if mine is home else home
    played = state.get("state") in ("in", "post") and _score(home) is not None
    return {"who": f"{name(away)} at {name(home)}", "vs": name(other), "home": mine is home, "state": state.get("state"), "status": text(state.get("shortDetail"), 40), "at": _when(event.get("date")),
            "mine": _score(mine) if played else None, "theirs": _score(other) if played else None}


def _when(iso):
    from datetime import datetime
    try:
        return int(datetime.fromisoformat(str(iso).replace("Z", "+00:00")).timestamp())
    except ValueError:
        return None


def team_card(sport, league, tid, at):
    t = at(f"{ESPN}{sport}/{league}/teams/{tid}", ESPN)["team"]
    upcoming = t.get("nextEvent") or []
    played = at(f"{ESPN}{sport}/{league}/teams/{tid}/schedule", ESPN).get("events") or []
    done = sorted((e for e in played if ((e.get("competitions") or [{}])[0].get("status") or {}).get("type", {}).get("state") == "post"), key=lambda e: _when(e.get("date")) or 0)
    record = ((t.get("record") or {}).get("items") or [{}])[0].get("summary")
    return {"kind": "team", "key": f"{sport}/{league}/{tid}", "name": text(t.get("displayName"), 60), "logo": link(((t.get("logos") or [{}])[0]).get("href")), "record": text(record, 20),
            "standing": text(t.get("standingSummary"), 60), "last": _game(done[-1], tid) if done else None, "next": _game(upcoming[0], tid) if upcoming else None}


def team(q, at):
    found = at(TEAM_FIND + urllib.parse.urlencode({"query": q, "limit": 3, "type": "team"}), TEAM_FIND).get("results") or []
    teams = next((r.get("contents") or [] for r in found if r.get("type") == "team"), [])
    hit = next((c for c in teams if names(q, c.get("displayName"))), None)
    tid = re.search(r"~t:(\d+)", str(hit.get("uid"))) if hit else None
    if not tid or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,29}", f"{hit.get('sport')}") or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,29}", f"{hit.get('defaultLeagueSlug')}"):
        return None
    return team_card(hit["sport"], hit["defaultLeagueSlug"], tid.group(1), at)


def place(q, at):
    """A town, if the words are one: it has to be called exactly that, and be big enough that nobody means something else."""
    name = q.split(",")[0].strip()
    hits = at(GEO + urllib.parse.urlencode({"name": name, "count": 1}), GEO).get("results") or []
    p = hits[0] if hits else {}
    if str(p.get("name")).lower() != name.lower() or not str(p.get("feature_code")).startswith("PPL") or (p.get("population") or 0) < BIG_TOWN:
        return None
    return {"name": text(p["name"], 60), "region": text(p.get("admin1"), 60), "country": text(p.get("country"), 60), "lat": float(p["latitude"]), "lon": float(p["longitude"]), "population": int(p.get("population") or 0)}


# ---------------------------------------------------------------------- what else is out there

def news(q, at, most=8):
    """Reporting past the paper's own outlets. Bing wraps each link in its own, with the real address inside."""
    found = []
    for item in ET.fromstring(at(BING + urllib.parse.urlencode({"q": q, "format": "rss"}), BING, raw=True)).iter("item"):
        fields = {c.tag.rsplit("}", 1)[-1]: c.text for c in item}
        real = urllib.parse.parse_qs(urllib.parse.urlsplit(fields.get("link") or "").query).get("url", [""])[0]
        found.append(row(fields.get("title"), real, re.sub(r" on MSN$", "", fields.get("Source") or ""), fields.get("description"), stamp(fields.get("pubDate"))))
    return rows(found, most)


def talk(q, at, most=4):
    """What people who build things are saying now. Twenty points keeps out what nobody read."""
    since = int(time.time()) - TALK_DAYS * 86400
    hits = at(HN + "search?" + urllib.parse.urlencode({"query": q, "tags": "story", "hitsPerPage": 12, "numericFilters": f"created_at_i>{since}"}), HN).get("hits") or []
    wanted = [h for h in hits if (h.get("points") or 0) >= 20 and h.get("url")]
    return rows([row(h.get("title"), h.get("url"), "Hacker News", f"{h['points']} points, {h.get('num_comments') or 0} comments", h.get("created_at_i")) for h in wanted], most)


def papers(q, at, most=3):
    """Research, when the words are in a title: arXiv answers anything with something."""
    query = " AND ".join(f"ti:{w}" for w in terms(q)[:5])
    if not query:
        return []
    feed = ET.fromstring(at(ARXIV + urllib.parse.urlencode({"search_query": query, "sortBy": "relevance", "max_results": most}), ARXIV, raw=True))
    found = []
    for e in feed.iter(f"{ATOM}entry"):
        who = [text(a.findtext(f"{ATOM}name"), 40) for a in e.iter(f"{ATOM}author")]
        found.append(row(e.findtext(f"{ATOM}title"), e.findtext(f"{ATOM}id"), f"arXiv, {who[0]}" if who else "arXiv", e.findtext(f"{ATOM}summary"), _when(e.findtext(f"{ATOM}published"))))
    return rows(found, most)


def code(q, at, most=3):
    """Code, when it's plainly about these words and people use it."""
    items = at(GITHUB + urllib.parse.urlencode({"q": q, "sort": "stars", "per_page": 6}), GITHUB).get("items") or []
    return rows([row(i.get("full_name"), i.get("html_url"), "GitHub", i.get("description"), _when(i.get("pushed_at")), stars=int(i.get("stargazers_count") or 0))
                 for i in items if (i.get("stargazers_count") or 0) >= 1000 and names(q, i.get("full_name"), i.get("description"))], most)


def odds(q, at, most=3):
    """What people are betting will happen. Prices aren't facts, and the page says so."""
    events = at(POLY + "public-search?" + urllib.parse.urlencode({"q": q, "limit_per_type": 8, "events_status": "active"}), POLY).get("events") or []
    found = []
    for e in events:
        if e.get("closed") or float(e.get("volume") or 0) < 25_000 or not names(q, e.get("title")):
            continue
        lines = []
        for m in e.get("markets") or []:
            try:
                sides = dict(zip(json.loads(m["outcomes"]), json.loads(m["outcomePrices"])))
                chance = round(float(sides["Yes"]) * 100, 1)
            except (KeyError, TypeError, ValueError):
                continue
            if not m.get("closed") and 0 < chance < 100:
                lines.append({"t": text(m.get("groupItemTitle") or "Yes", 60), "pct": chance})
        url = f"https://polymarket.com/event/{urllib.parse.quote(str(e.get('slug')), safe='')}"
        if lines:
            found.append({"t": text(e.get("title"), 140), "u": url, "lines": lines[:4], "volume": float(e["volume"])})
    return sorted(found, key=lambda x: -x["volume"])[:most]
