# Run from test_paper.py: search past the paper, what the words are, and following each kind of thing its own way.
import find
import json as _json

raw = {}


def at(url, *allowed, raw_body=False, **k):
    assert url.startswith(allowed), url
    for start, answer in raw.items():
        if url.startswith(start):
            if isinstance(answer, Exception):
                raise answer
            return answer
    raise OSError("no answer")


# a stranger's text, and a stranger's link
assert find.text("<b>Hi</b>  &amp;\n there") == "Hi & there" and find.text("x " * 400, 20).endswith("...") and find.text(None) == ""
assert find.link("https://a.example/x") and not find.link("javascript:alert(1)") and not find.link("https://a b/") and not find.link("https://a.example\\.reuters.com/") and not find.link(5) and not find.link("https://a.example/" + "x" * 1000)
assert find.row("Title", "javascript:alert(1)", "S") is None and find.row("", "https://a.example", "S") is None
assert find.names("oil price", "The price of Oil") and not find.names("oil price", "The price of gold") and not find.names("", "anything")

# what the words are
raw.clear()
raw[find.QUOTE_FIND] = {"quotes": [{"symbol": "UKRN.DE", "shortname": "HANetf Ukraine", "quoteType": "ETF", "score": 20006}]}
assert find.market("Ukraine", at, s.invest.clean_symbol) is None, "a fund with the word in its name isn't what was meant"
raw[find.CHART] = {"chart": {"result": [{"meta": {"regularMarketPrice": 344.63, "currency": "USD", "shortName": "Apple Inc.", "fullExchangeName": "NasdaqGS"}, "indicators": {"quote": [{"close": [300.0, None, 340.0, 344.63]}]}}]}}
raw[find.QUOTE_FIND] = {"quotes": [{"symbol": "AAPL", "shortname": "Apple Inc.", "quoteType": "EQUITY", "score": 195752}]}
apple = find.market("apple", at, s.invest.clean_symbol)
assert apple["kind"] == "market" and apple["key"] == "AAPL" and apple["price"] == 344.63 and apple["prev"] == 340.0 and apple["closes"] == [300.0, 340.0, 344.63], apple
raw[find.QUOTE_FIND] = {"quotes": [{"symbol": "aapl;rm", "shortname": "apple", "quoteType": "EQUITY", "score": 999999}]}
assert refuses(find.market, "apple", at, s.invest.clean_symbol), "a symbol goes into an address, so it has to be one"
raw[find.CHART] = {"chart": {"result": [{"meta": {"regularMarketPrice": 500, "currency": "GBp"}, "indicators": {"quote": [{"close": [400, 500]}]}}]}}
assert find.priced("X.L", at)["price"] == 5 and find.priced("X.L", at)["currency"] == "GBP" and find.priced("X.L", at)["closes"] == [4, 5], "pence are pounds"
raw[find.GEO] = {"results": [{"name": "Arsenal", "feature_code": "PPL", "population": 2599, "latitude": 1, "longitude": 2}]}
assert find.place("Arsenal", at) is None, "a village isn't what anyone means by Arsenal"
raw[find.GEO] = {"results": [{"name": "Oakland", "feature_code": "PPLA2", "population": 419267, "latitude": 37.8, "longitude": -122.3, "admin1": "California", "country": "United States"}]}
assert find.place("Oakland, California", at)["lat"] == 37.8
raw[find.GEO] = {"results": [{"name": "Ukraine", "feature_code": "PCLI", "population": 39000000, "latitude": 49, "longitude": 32}]}
assert find.place("Ukraine", at) is None, "a country is a conflict or a subject, not a forecast"
raw[f"{find.WIKI}w/rest.php"] = {"pages": [{"key": "Binance"}]}
raw[f"{find.WIKI}api/rest_v1"] = {"type": "disambiguation", "title": "Binance"}
assert find.wiki("Binance", at) is None
raw[f"{find.WIKI}api/rest_v1"] = {"type": "standard", "title": "Binance", "description": "An exchange", "extract": "<b>Binance</b> is a crypto exchange.", "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Binance"}}, "thumbnail": {"source": "javascript:x"}}
page = find.wiki("Binance", at)
assert page["text"] == "Binance is a crypto exchange." and page["img"] is None
assert find.wiki("something else entirely", at) is None, "a page has to be about the words"

# who else is writing about it
bing = b"""<rss xmlns:News="https://www.bing.com/news/search?q=x"><channel><item><title>A &lt;b&gt;story&lt;/b&gt;</title><link>http://www.bing.com/news/apiclick.aspx?ref=x&amp;url=https%3a%2f%2fsite.example%2fa&amp;c=1</link><description>What it says</description><pubDate>Sun, 01 Nov 2026 09:09:34 GMT</pubDate><News:Source>CNN on MSN</News:Source></item><item><title>No link</title><link>http://www.bing.com/x</link></item></channel></rss>"""
raw[find.BING] = bing
got = find.news("x", at)
assert got == [{"t": "A story", "u": "https://site.example/a", "src": "CNN", "sum": "What it says", "ts": 1793524174}], got
raw[find.HN] = {"hits": [{"title": "Big", "url": "https://a.example/1", "points": 300, "num_comments": 9, "created_at_i": 5, "objectID": "42"}, {"title": "Small", "url": "https://a.example/2", "points": 2, "objectID": "1"}, {"title": "No link", "points": 900, "objectID": "1"}]}
assert [(r["t"], r["sum"]) for r in find.talk("x", at)] == [("Big", "300 points, 9 comments")]
asked = []
assert find.talk("x", lambda url, *allowed, **how: asked.append(url) or {}) == [] and "numericFilters=created_at_i" in asked[0], "what people are saying now, not in 2022"
assert find.row("graphsearch.epfl.ch", "https://graphsearch.epfl.ch/", "graphsearch.epfl.ch") is None, "a title that is only its address says nothing"
assert find.row("Example.com", "https://www.example.com/a", "x") is None and find.row("Example", "https://www.example.com/a", "x")
raw[find.GITHUB] = {"items": [{"full_name": "a/sqlite", "html_url": "https://github.com/a/sqlite", "description": "x", "stargazers_count": 9000}, {"full_name": "b/other", "html_url": "https://github.com/b/other", "description": "y", "stargazers_count": 9000}, {"full_name": "c/sqlite", "html_url": "https://github.com/c/sqlite", "stargazers_count": 3}]}
assert [r["t"] for r in find.code("sqlite", at)] == ["a/sqlite"], "popular, and plainly about the words"
raw[find.POLY] = {"events": [
    {"title": "Ukraine ceasefire by?", "slug": "a b", "volume": "9000000", "markets": [{"groupItemTitle": "June", "outcomes": '["Yes", "No"]', "outcomePrices": '["0.5", "0.5"]'}, {"groupItemTitle": "Past", "closed": True, "outcomes": '["Yes", "No"]', "outcomePrices": '["0", "1"]'}, {"outcomes": "broken", "outcomePrices": "x"}]},
    {"title": "Ukraine small", "volume": "10", "markets": []}, {"title": "Something else", "volume": "9000000", "markets": []}, {"title": "Ukraine closed", "closed": True, "volume": "9000000"}]}
assert find.odds("Ukraine", at) == [{"t": "Ukraine ceasefire by?", "u": "https://polymarket.com/event/a%20b", "lines": [{"t": "June", "pct": 50.0}], "volume": 9000000.0}]

# one meaning for the words
assert [c["kind"] for c in s.named_cards([], {"team": {"kind": "team"}, "thing": {"kind": "thing"}})] == ["team"], "Arsenal the club isn't a store of weapons"
assert [c["kind"] for c in s.named_cards([], {"market": {"kind": "market"}, "thing": {"kind": "thing"}})] == ["market"], "Apple isn't the fruit"
assert [c["kind"] for c in s.named_cards([], {"team": {"kind": "team"}, "place": {"kind": "place"}, "thing": {"kind": "thing"}})] == ["place", "thing"], "Oakland isn't Oakland Roots"
assert [c["kind"] for c in s.named_cards([{"kind": "conflict"}], {"team": {"kind": "team"}, "thing": {"kind": "thing"}})] == ["conflict", "thing"]
assert [c["kind"] for c in s.named_cards([{"kind": "conflict"}], {"market": {"kind": "market"}, "thing": {"kind": "thing"}})] == ["conflict", "thing"], "Taiwan isn't its chip maker"

# a search
for bad in (None, 5, "", "x", "y" * 121):
    assert refuses(s.clean_query, bad), bad
assert s.clean_query("  two   words ") == "two words"
assert refuses(s.outside_at, "https://evil.example/x", find.WIKI), "only the sources named here"
real_public, s.fetch_public = s.fetch_public, lambda url, *a, **k: (b'{"a": 1}', "", url)
assert s.outside_at(find.WIKI + "x", find.WIKI) == {"a": 1}
s.fetch_public = real_public
assert s.quiet(lambda: 1 / 0) is None
assert s.quiet(lambda: {"price": float("nan")}) is None, "a NaN in one price can't stop the page being saved"
assert find.host("https://[bad/") == "" and find.host("https://a.example/x") == "a.example"

# what the model says
said = s.clean_answer(_json.dumps({"answer": "It fell [1]. It <b>rose</b> [9] again [2]. [0]", "next": ["Why?", 5, "", "Who?", "Where?", "When?"]}), 2)
assert said == {"answer": "It fell [1]. It rose again [2].", "next": ["Why?", "Who?", "Where?"]}, said
for bad in ("no json", "[1]", _json.dumps({"answer": 5}), _json.dumps({"answer": " "})):
    try:
        s.clean_answer(bad, 2)
    except ValueError:
        pass
    else:
        raise AssertionError(bad)

# the day's ceiling, each kind apart
for _ in range(s.FIND_DAILY["web"]):
    s.spend_find("web")
try:
    s.spend_find("web")
except OverflowError:
    pass
else:
    raise AssertionError("a ceiling that doesn't stop anything")
s.spend_find("answer")
with s.db() as c:
    c.execute("DELETE FROM meta WHERE k LIKE 'finds:%'")

# following: each key goes into an address later, so each has to be exactly its own shape
good = [({"kind": "market", "key": "aapl", "name": "Apple"}, "AAPL"), ({"kind": "team", "key": "soccer/eng.1/359", "name": "Arsenal"}, "soccer/eng.1/359"), ({"kind": "place", "key": "37.8,-122.3", "name": "Oakland"}, "37.8,-122.3"), ({"kind": "topic", "key": "Binance hack", "name": "Binance hack"}, "Binance hack")]
for sent, key in good:
    assert s.clean_follow(sent)["key"] == key, sent
for bad in ({"kind": "market", "key": "a;b", "name": "x"}, {"kind": "team", "key": "../../etc/1", "name": "x"}, {"kind": "team", "key": "soccer/eng.1/abc", "name": "x"}, {"kind": "team", "key": "../../1", "name": "x"}, {"kind": "place", "key": "91,0", "name": "x"}, {"kind": "place", "key": "1,2&x=3", "name": "x"},
            {"kind": "conflict", "key": "nope", "name": "x"}, {"kind": "topic", "key": "the of", "name": "x"}, {"kind": "mail", "key": "x", "name": "x"}, {"kind": "market", "key": 5, "name": "x"}, {"kind": "market", "key": "AAPL"}):
    assert refuses(s.clean_follow, bad), bad
real_card, s.follow_card = s.follow_card, lambda f, old=None: {"id": f["id"], "kind": f["kind"], "name": f["name"]}
try:
    assert s.set_follow({"kind": "market", "key": "AAPL", "name": "Apple"})["on"] and [r["key"] for r in s.follow_rows() if r["kind"] == "market"] == ["AAPL"]
    assert any(c["name"] == "Apple" for c in s.load("following")["data"]["cards"]), "a new follow is on the page at once"
    s.set_follow({"kind": "market", "key": "AAPL", "name": "Apple"})
    assert len([r for r in s.follow_rows() if r["kind"] == "market"]) == 1, "pressing twice doesn't follow twice"
    assert s.job_on("following")
    settings.update({"FOLLOW": "Harbor, Acme"})
    assert {"Harbor", "Acme"} <= {r["key"] for r in s.follow_rows()}, "a word in the Follow setting is a subject, as it always was"
    s.set_follow({"kind": "topic", "key": "Acme", "name": "Acme", "on": False})
    assert settings.get("FOLLOW") == "Harbor", "and stopping takes it out of the setting"
    s.set_follow({"kind": "market", "key": "AAPL", "name": "Apple", "on": False})
    assert not [r for r in s.follow_rows() if r["kind"] == "market"] and not any(c["name"] == "Apple" for c in s.load("following")["data"]["cards"])
    s.remember("follows", [{"id": str(i), "kind": "topic", "key": f"k{i}", "name": "n"} for i in range(s.FOLLOW_MOST)])
    assert refuses(s.set_follow, {"kind": "topic", "key": "One more", "name": "One more"}), "a ceiling, because each one is fetched every few minutes"
    s.remember("follows", [])
finally:
    s.follow_card = real_card
    settings.update({"FOLLOW": ""})

# stopping always works, even for a conflict that has since ended
s.remember("follows", [{"id": s.follow_id("conflict", "gone"), "kind": "conflict", "key": "gone", "name": "Gone"}])
assert s.set_follow({"kind": "conflict", "key": "gone", "name": "Gone", "on": False})["on"] is False and not [r for r in s.follow_rows() if r["key"] == "gone"]

# what a failing answer costs, and what the switches really stop
real_ready, real_ask, real_kept, real_around, real_web = s.ai.ready, s.ai.ask, s.find_kept, s.around, s.web_for
read = []
real_sources, s.sources_for = s.sources_for, lambda *a: read.append(a) or [{"n": 1, "t": "A", "u": "https://a.example", "src": "S", "sum": ""}]
s.find_kept, s.around, s.web_for = (lambda *a: None), (lambda q: {"cards": [], "news": []}), (lambda q: [])
s.ai.ready = lambda: False
assert s.find_answer({"q": "harbor"})["answer"] == "" and not read, "no AI, and no outlet's page is opened for an answer nobody will write"
s.ai.ready = lambda: True


def key_in_error(*a, **k):
    raise ValueError("Invalid header value b'Bearer sk-secret'")


s.ai.ask = key_in_error
assert s.find_answer({"q": "harbor"})["answer"] == "", "the results stand without an answer"
assert "secret" not in str(s.find_answer({"q": "harbor", "ask": "Why?"})), "and no library's words reach the page"
s.ai.ask = lambda *a, **k: None
assert s.find_answer({"q": "harbor"})["answer"] == "", "an empty reply is a failure, not a crash"
s.ai.ask = lambda *a, **k: _json.dumps({"answer": "Yes [1].", "next": []})
with s.db() as c:
    c.execute("DELETE FROM meta WHERE k LIKE 'finds:%'")
for _ in range(s.FIND_DAILY["answer"]):
    assert s.find_answer({"q": "harbor", "ask": "Why?"})["answer"] == "Yes [1]."
assert s.find_answer({"q": "harbor", "ask": "Why?"})["answer"].startswith("That question could not"), "follow-ups count too"
s.ai.ready, s.ai.ask, s.find_kept, s.around, s.web_for, s.sources_for = real_ready, real_ask, real_kept, real_around, real_web, real_sources
with s.db() as c:
    c.execute("DELETE FROM meta WHERE k LIKE 'finds:%'")
settings.update({"FIND_OUTSIDE": False})
assert s.quiet(lambda: s.follow_fresh({"kind": "market", "key": "AAPL", "name": "Apple"})) is None, "the switch stops a follow's fetches too"
settings.update({"FIND_OUTSIDE": True})

# a follow keeps its last good card when its source is down, and isn't fetched more than it needs
real_fresh, s.follow_fresh = s.follow_fresh, lambda f: 1 / 0
old = {"id": "x", "kind": "market", "price": 5, "at": 1}
f = {"id": "x", "kind": "market", "key": "AAPL", "name": "Apple"}
assert s.follow_card(f, old)["price"] == 5 and s.follow_card(f)["href"] == "/topic/AAPL"
s.follow_fresh = lambda f: {"price": 6}
assert s.follow_card(f, old)["price"] == 6
recent = {**old, "at": int(time.time())}
assert s.follow_card(f, recent)["price"] == 5, "fetched this minute already"
s.follow_fresh = real_fresh
assert s.follow_card({"id": "p", "kind": "conflict", "key": "x", "name": "X"})["href"].startswith("/topic/")
s.follow_fresh = lambda f: {"href": "/world/theater/x"}
assert s.follow_card({"id": "p", "kind": "conflict", "key": "x", "name": "X"})["href"] == "/world/theater/x"
s.follow_fresh = real_fresh

# A town only when the news is about the town: Rogers the Michigan candidate isn't Rogers, Arkansas
_real_place, _real_forecast = s.find.place, s.forecast_card
_town = lambda name, pop, region: (lambda q, at: {"name": name, "region": region, "country": "United States", "lat": 1.0, "lon": 2.0, "population": pop})
s.forecast_card = lambda p: {"kind": "place", "name": p["name"]}
_story = lambda t, summary="": {"t": t, "sum": summary, "u": "https://n.example/" + t[:8], "src": "A", "ts": int(s.time.time()), "desks": [], "outlets": [{"src": "A"}]}
s.save("news", {"stories": [_story("Carville rips Stevens over Rogers endorsement", "The Michigan Senate race tightens."), _story("Haley Stevens backs Mike Rogers")]})
s.find.place = _town("Rogers", 70_000, "Arkansas")
assert s.place_card("Rogers") is None, "a namesake town the news never puts in its state isn't what the page is about"
s.find.place = _town("Rogers", 700_000, "Arkansas")
assert s.place_card("Rogers"), "a big city is what the word means whatever the news says"
s.save("news", {"stories": [_story("Jet crashes in Cresthaven", "A private jet crashed in Cresthaven, Florida, killing nine.")]})
s.find.place = _town("Cresthaven", 60_000, "Florida")
assert s.place_card("Cresthaven"), "a small town in the news is the place when the news says where it is"
s.save("news", {"stories": []})
assert s.place_card("Cresthaven"), "and a search with no news about it gets its forecast"
s.find.place, s.forecast_card = _real_place, _real_forecast
assert "population" in (find.place("Oakland", lambda url, cache: {"results": [{"name": "Oakland", "feature_code": "PPLA2", "population": 419267, "latitude": 37.8, "longitude": -122.3}]}) or {})

# a report WARROOM could only place in a country has no point on a map
_coarse = s.curated([{"id": "c", "title": "Prominent Democrat backs Republican candidate in Michigan midterm", "ts": 5, "domain": "economic", "severity": 0.4, "lat": 31.5, "lon": 34.75, "geo_precision": "country"},
                     {"id": "p", "title": "Strike hits a depot near Kharkiv", "ts": 6, "domain": "kinetic", "severity": 0.6, "lat": 49.9, "lon": 36.2, "geo_precision": "city"}])
assert [("la" in r) for r in _coarse] == [True, False], _coarse

# a container that only has a sidebar isn't the sidebar (PBS wraps every story in page__body--with-sidebar)
_long = "Vice President JD Vance sought to distance himself from the administration in a long post on Wednesday night. " * 2
_page = f'<html><head><meta property="og:title" content="Vance"></head><body><div class="page__body page__body--with-sidebar"><article><p>{_long}</p><p>He blamed the war with Iran for the losses of his party and said voters had told them so plainly at every stop.</p><p>The White House did not answer questions about the post on Thursday morning, and aides declined to comment further on it.</p></article><div class="sidebar"><p>{_long} sidebar</p></div></div></body></html>'
_got = s.extract(_page, "https://www.pbs.org/newshour/politics/x")
assert _got["words"] > 60 and "sidebar" not in _got["body"], _got["words"]

# a publisher that won't share is read from another outlet carrying the same story, and named
_real_read = s.read_page
_pages = {"https://a.example/1": {"body": ""}, "https://b.example/2": {"body": "<p>" + _long + "</p>", "words": 40}}
s.read_page = lambda u, **k: _pages[u] if u in _pages else (_ for _ in ()).throw(OSError("403"))
_item = {"outlets": [{"u": "https://nyt.example/0", "src": "New York Times"}, {"u": "https://a.example/1", "src": "A"}, {"u": "https://b.example/2", "src": "The Guardian"}]}
_from = s.elsewhere(_item, "https://nyt.example/0", {})
assert {k: _from["via"][k] for k in ("src", "u")} == {"src": "The Guardian", "u": "https://b.example/2"} and _from["body"].startswith("<p>Vice"), _from
assert "image" not in _from, "the original's picture stays"

# nobody the paper saw has it: the same story further out, never from the publisher that refused, never an unrelated one
_pages.update({"https://c.example/3": {"body": "<p>" + _long + "</p>", "words": 300}, "https://d.example/4": {"body": "<p>teaser</p>", "words": 90, "held": True}})
_real_news, _real_spend_find, _searched = find.news, s.spend_find, []
find.news = lambda q, at, most=8: _searched.append(q) or [{"t": "Vance distances himself from the administration", "u": "https://www.nyt.example/9", "src": "NYT", "ts": None},
                                                       {"t": "Weather is mild in Ohio", "u": "https://e.example/5", "src": "E", "ts": None},
                                                       {"t": "Vance distances himself from the administration, paywalled", "u": "https://d.example/4", "src": "D", "ts": None},
                                                       {"t": "JD Vance distances himself from administration", "u": "https://c.example/3", "src": "", "ts": None}]
s.spend_find = lambda kind: None
_lone = {"t": "Vance distances himself from the administration", "outlets": [{"u": "https://www.nyt.example/0", "src": "New York Times"}], "ts": time.time()}
_from = s.elsewhere(_lone, "https://www.nyt.example/0", {})
assert {k: _from["via"][k] for k in ("src", "u")} == {"src": "c.example", "u": "https://c.example/3"}, _from
assert s.elsewhere(_lone, "https://www.nyt.example/0", {})["via"]["u"] == "https://c.example/3" and len(_searched) == 1, "an hour's search is kept"
assert s.slug_words("https://www.nytimes.com/2026/11/04/us/politics/vance-ohio-recount.html") == "vance ohio recount" and s.slug_words("https://x.example/a/12345") == ""
find.news, s.spend_find, s.read_page = _real_news, _real_spend_find, _real_read

# the parser knows when it has missed a story that is on the page, and reads it again trusting no class name
_para = lambda n: f"<p>Paragraph {n} of the report says the county counted its ballots by hand through the night and finished at dawn.</p>"
_hidden = f'<html><body><div id="article-sidebar-layout">{"".join(_para(n) for n in range(5))}</div><ul class="sidebar"><li><a href="/a">Another story</a></li></ul></body></html>'
_got = s.extract(_hidden, "https://x.example/hidden")
assert _got["words"] > 60 and "Paragraph 4" in _got["body"] and "Another story" not in _got["body"], _got
_divs = '<html><body><main>' + "".join(f'<div data-testid="paragraph-{n}">Line {n}: the <a href="/x">council</a> voted to keep the library open late through the winter months ahead.</div>' for n in range(5)) + '</main></body></html>'
_got = s.extract(_divs, "https://x.example/divs")
assert _got["words"] > 60 and "Line 4" in _got["body"] and _got["body"].count("<a ") == 5 and "</a>" in _got["body"], _got["body"]
_aspx = f'<html><body><form id="aspnetForm"><div class="content">{"".join(_para(n) for n in range(4))}</div></form></body></html>'
assert s.extract(_aspx, "https://x.example/aspx")["words"] > 60, "a whole page inside one form"

# a story the parser can't find on its own goes to the AI, which answers with passage numbers and nothing else
_scattered = "<html><body>" + "".join(f'<div class="related">{_para(n)}{"".join(f"<li><a href=/{n}{k}>Link {k}</a></li>" for k in range(7))}</div>' for n in range(7)) + "</body></html>"
_got = s.extract(_scattered, "https://x.example/scattered")
assert _got["body"] == "" and len(_got["_candidates"]) == 7, _got
assert "_candidates" not in s.extract(_scattered.replace("<body>", '<body><script type="application/ld+json">{"isAccessibleForFree": false}</script>'), "https://x.example/s2"), "a paywall isn't a parse to repair"
_real = s.ai.ready, s.ai.ask, s.spend_ai, s.spend_find
_asked = []
s.ai.ready, s.spend_ai, s.spend_find = (lambda: True), (lambda: None), (lambda kind: _asked.append(kind))
for _said, _want in (("1, 3-4", [0, 2, 3]), ("none", []), ("2, 99, 0", [1]), ("1-9999", list(range(7))), ("1-999999999", []), ("None.", []),
                     ("none (passages 1-4 are the menu)", []), ("I found 2 passages: 7, 8", []), ("3 to 5.", [2, 3, 4])):
    s.ai.ask = lambda system, text, **k: _said
    assert s.picked("t", _got["_candidates"]) == [_got["_candidates"][i] for i in _want], _said
assert _asked == ["parse"] * 9, "the parser's AI has its own daily ceiling"
s.ai.ask = lambda system, text, **k: (_ for _ in ()).throw(OSError("down"))
assert s.picked("t", _got["_candidates"]) == []
s.ai.ready, s.ai.ask, s.spend_ai, s.spend_find = _real

# a page that says it's for subscribers and shows only its opening is a teaser, not the story
_ld = '<script type="application/ld+json">{"@type": "NewsArticle", "isAccessibleForFree": "False"}</script>'
assert s.extract(f"<html><body>{_ld}<article>{_para(1)}{_para(2)}{_para(3)}</article></body></html>", "https://x.example/t")["held"]
assert not s.extract(f"<html><body>{_ld}<article>{''.join(_para(n) for n in range(30))}</article></body></html>", "https://x.example/t2")["held"]
assert not s.extract(f"<html><body><article>{_para(1)}{_para(2)}{_para(3)}</article></body></html>", "https://x.example/t3")["held"]

# the reader says why a story is missing, and a teaser gives way to a whole telling from another outlet
import urllib.error  # noqa: E402
_real_read, _real_else = s.read_page, s.elsewhere
s.elsewhere = lambda item, url, story: {}
s.read_page = lambda u, **k: (_ for _ in ()).throw(urllib.error.HTTPError(u, 403, "Forbidden", {}, None))
assert s.reader("https://www.nyt.example/x")["why"] == "refused"
s.read_page = lambda u, **k: (_ for _ in ()).throw(TimeoutError("slow"))
assert s.reader("https://www.nyt.example/x")["why"] == "no answer"
s.read_page = lambda u, **k: {"url": u, "site": "WSJ", "title": "T", "deck": "", "image": None, "author": None, "published": 0, "body": "<p>teaser</p>", "words": 90, "held": True}
assert s.reader("https://wsj.example/x")["why"] == "paid", "a teaser with nothing better stays, and says so"
s.elsewhere = lambda item, url, story: {"body": "<p>whole</p>", "words": 800, "via": {"src": "AP", "u": "https://ap.example/1"}}
_got = s.reader("https://wsj.example/x")
assert _got["why"] == "paid" and _got["via"]["src"] == "AP" and _got["body"] == "<p>whole</p>", _got
s.read_page, s.elsewhere = _real_read, _real_else

# a list of other stories' headlines, however long each is, isn't more of this one
_teasers = "".join(f'<h4><a href="/s{n}">Another long headline about the midterm results number {n} and what it means</a></h4><li><a href="/t{n}">A teaser line that runs long enough to look like a paragraph {n}</a> 2h</li>' for n in range(8))
_got = s.extract(f'<html><body><div class="sidebar-wrap">{"".join(_para(n) for n in range(4))}</div><div>{_teasers}</div></body></html>', "https://x.example/teasers")
assert "Paragraph 3" in _got["body"] and "Another long headline" not in _got["body"] and "teaser line" not in _got["body"], _got["body"]

# the stand-in is the closest report, not the first that answers: a live page loses to a story on the same thing,
# and a refused story keeps its own headline rather than the live page's
_live_t = "US midterm elections 2026 live updates: Vance blames Iran war for Republicans' brutal midterms losses as Democrats retake Congress"
_pages = {"https://live.example/1": {"body": "<p>" + _long + "</p>", "words": 2000}, "https://ax.example/2": {"body": "<p>" + _long + "</p>", "words": 300}}
_item = {"t": _live_t, "u": "https://live.example/1", "sum": "Live from the count", "ts": 1, "img": None, "outlets": [
    {"u": "https://live.example/1", "src": "The Guardian", "t": _live_t, "ts": 1},
    {"u": "https://nyt.example/0", "src": "New York Times", "t": "Vance, in Break With Trump, Blames Iran War for Republicans' Rout", "ts": 2},
    {"u": "https://ax.example/2", "src": "Axios", "t": "Vance says the Iran war cost Republicans the midterms", "ts": 3}]}
_real_read, _real_known = s.read_page, s.known_item
s.read_page = lambda u, **k: _pages[u] if u in _pages else (_ for _ in ()).throw(urllib.error.HTTPError(u, 403, "Forbidden", {}, None))
s.known_item = lambda u: _item
_got = s.reader("https://nyt.example/0")
assert _got["via"]["src"] == "Axios" and _got["why"] == "refused", _got.get("via")
assert _got["title"].startswith("Vance, in Break") and _got["deck"] == "" and _got["site"] == "New York Times", (_got["title"], _got["deck"], _got["site"])
s.read_page, s.known_item = _real_read, _real_known

# a "this story is developing" stub stands in only when nothing fuller answers
_pages = {"https://stub.example/1": {"body": "<p>" + _long + "</p>", "words": 96}, "https://full.example/2": {"body": "<p>" + _long + "</p>", "words": 600}}
s.read_page = lambda u, **k: _pages[u] if u in _pages else (_ for _ in ()).throw(OSError("403"))
_two = [{"u": "https://stub.example/1", "src": "PBS"}, {"u": "https://full.example/2", "src": "Axios"}]
assert s.first_full(_two)["via"]["src"] == "Axios" and s.first_full(_two[:1])["via"]["src"] == "PBS"
_pages["https://g.example/us-news/live/2026/nov/04/x"] = {"body": "<p>" + _long + "</p>", "words": 2800}
_three = [{"u": "https://g.example/us-news/live/2026/nov/04/x", "src": "The Guardian"}, _two[0], _two[1]]
assert s.first_full(_three)["via"]["src"] == "Axios" and s.first_full(_three[:2])["via"]["src"] == "The Guardian", "a live page beats a stub, not a report"
s.read_page = _real_read

# a line break keeps its words apart; in a loose read it ends a paragraph; an unclosed link doesn't swallow the page
_got = s.extract("<html><body><article>" + "".join(f"<p>Line one of part {n}, a story long enough to count as one.<br>Line two carries on with more of the story here.</p>" for n in range(3)) + "</article></body></html>", "https://x.example/br")
assert "one.<br>Line two" in _got["body"] and "one.Line" not in _got["body"], _got["body"][:200]
_r = s.Reader("https://x.example/", guess=False)
_r.feed("<div>First loose paragraph of the story, long enough.<br><br>Second loose paragraph of it.</div>")
_r.close_block()
assert [b["text"] for b in _r.blocks] == ["First loose paragraph of the story, long enough.", "Second loose paragraph of it."], _r.blocks
_r = s.Reader("https://x.example/", guess=False)
_r.feed('<p>Intro with <a href="/x">an unclosed link</p>' + _para(1) + _para(2))
_r.close_block()
assert s.prose(_r.blocks[1]) and s.prose(_r.blocks[2]), [b.get("linked") for b in _r.blocks]

# WordPress names a post's tags and categories on its container; that container is the story, not a tag list
_wp = f'<html><body><p>Support our journalism with a donation today, because readers like you keep this site going strong.</p><main class="post type-post tag-2026-elections category-social-issues"><article>{"".join(_para(n) for n in range(4))}</article></main></body></html>'
_got = s.extract(_wp, "https://x.example/wp")
assert "Paragraph 3" in _got["body"] and "donation" not in _got["body"], _got["body"][:200]
# an element with no end tag can't start a skip that swallows the rest of the page
assert "Paragraph 3" in s.extract(f'<html><body><article><embed class="social-embed" src="/x">{"".join(_para(n) for n in range(4))}</article></body></html>', "https://x.example/void")["body"]

# every page is checked against a read that trusts no class name: a free article whose paragraphs are all marked
# "paywall" (Conde Nast does this) was read as its one unmarked paragraph
_free = '<script type="application/ld+json">{"isAccessibleForFree": true}</script>'
_got = s.extract(f'<html><body>{_free}<article><p>{_long}</p>{"".join(_para(n).replace("<p>", "<p class=paywall>") for n in range(9))}</article></body></html>', "https://x.example/wired")
assert "Paragraph 8" in _got["body"] and _got["words"] > 180, _got["words"]
_got = s.extract(f'<html><body><article><p>{_long}</p><p>{_long.replace("night", "evening")}</p></article><div class="footer-text">{"".join(_para(n) for n in range(2))}</div></body></html>', "https://x.example/brief")
assert "Paragraph" not in _got["body"], "a short story stays short: twice as much and 100 words more before the check takes over"

# a page that says its story is for subscribers keeps what it hides: the part it names, and the full text it gives search engines
_locked = '<script type="application/ld+json">{"isAccessibleForFree": "False", "hasPart": {"@type": "WebPageElement", "isAccessibleForFree": "False", "cssSelector": ".premium-body"}, "articleBody": "' + "hidden word " * 200 + '"}</script>'
_got = s.extract(f'<html><body>{_locked}<article><p>{_long}</p>{_para(1)}{_para(2)}<div class="premium-body">{"".join(_para(n) for n in range(10, 30))}</div></article></body></html>', "https://x.example/locked")
assert "Paragraph 10" not in _got["body"] and "Paragraph 2" in _got["body"] and _got["held"], _got["body"][:300]
_got = s.extract(f'<html><body>{_locked}<div id="root"></div></body></html>', "https://x.example/locked2")
assert _got["body"] == "" and "hidden" not in _got["body"] and _got["held"]

# --- what an independent review found -------------------------------------------------------------------------
# a hostile page can't make the densest-run search quadratic
_t0 = time.time()
s.densest([{"tag": "p", "text": "y" * 60, "html": "y" * 60} for _ in range(20000)] + [{"tag": "li", "text": "a", "html": "a"} for _ in range(20000)])
assert time.time() - _t0 < 1, time.time() - _t0
# nor can one huge paragraph of tiny tags
_t0 = time.time()
s.extract("<html><body><p>" + "a<i></i>" * 40000 + "</p></body></html>", "https://x.example/huge")
assert time.time() - _t0 < 4, time.time() - _t0
# the full text a script-built page gives search engines beats a loose read of its cookie notices
_cookies = "".join(f"<div>We use cookies number {n} to give you the best experience on our site, and to measure how it is used.</div>" for n in range(4))
_ld = '<script type="application/ld+json">{"@type": "NewsArticle", "articleBody": "' + " ".join(f"Sentence {n} of the real story." for n in range(100)) + '"}</script>'
_got = s.extract(f'<html><head><meta property="og:title" content="The real story"></head><body>{_ld}<div id="root">{_cookies}</div></body></html>', "https://x.example/ld")
assert "Sentence 99" in _got["body"] and "cookies" not in _got["body"], _got["body"][:200]
# a short story isn't padded out with its comments
_comments = "".join(f"<p>Commenter {n} writes that this is a disgrace and the whole thing should be investigated by somebody right away.</p>" for n in range(6))
_got = s.extract(f'<html><head><meta property="og:title" content="Council keeps library open"></head><body><article><p>The council voted on Tuesday to keep the library open late through the winter, officials said.</p></article><section id="comments">{_comments}</section></body></html>', "https://x.example/brief2")
assert "Commenter" not in _got["body"], _got["body"][:200]
# a modifier on a junk box doesn't rescue it, and Piano's paywall box is still a paywall box
for _cls in ('id="piano-paywall"', 'class="piano-subscribe"', 'class="newsletter-signup--with-image"', 'class="sidebar--no-border"', 'class="related-stories--has-images"'):
    _got = s.extract(f'<html><body><article>{"".join(_para(n) for n in range(4))}<div {_cls}><p>Subscribe today and get unlimited access to every story we publish, for just one dollar.</p></div></article></body></html>', "https://x.example/m")
    assert "Subscribe today" not in _got["body"], _cls
# a line break inside a link in a loose read leaves no link open to swallow the next paragraph
_r = s.Reader("https://x.example/", guess=False)
_r.feed('<main><div>First, the council said it would act soon, <a href="/x">said the mayor<br>today</a></div><div>Second, the plan goes to a vote.</div></main>')
_r.close_block()
assert all(b["html"].count("<a") == b["html"].count("</a>") for b in _r.blocks), [b["html"] for b in _r.blocks]
_r = s.Reader("https://x.example/")
_r.feed("<p>Bold <b>start and <i>both</b> end</i> here.</p>")
_r.close_block()
assert _r.blocks[0]["html"] == "Bold <strong>start and <em>both</em></strong> end here.", _r.blocks[0]["html"]
# a story the site says is for subscribers, told whole, isn't called a teaser
_whole = '<script type="application/ld+json">{"isAccessibleForFree": false, "wordCount": 75}</script>'
assert not s.extract(f"<html><body>{_whole}<article><p>{_long}</p>{_para(1)}{_para(2)}</article></body></html>", "https://x.example/w")["held"]
# the AI picks only for a page someone opened; a page read in passing is kept for when it is
_real_fetch, _real_picked, _real_public, _fetches, _picks = s.fetch_public, s.picked, s.public_url, [], []
s.public_url = lambda u: u
s.fetch_public = lambda u, *a, **k: _fetches.append(u) or (_scattered.encode(), "text/html", u)
s.picked = lambda title, cands: _picks.append(len(cands)) or cands
_u = "https://x.example/scattered-" + str(time.time())
_p = s.read_page(_u)
assert _p["body"] == "" and _p.get("unpicked") and not _picks, _p
assert s.read_page(_u, pick=True)["picked"] and _picks == [7] and len(_fetches) == 2, (_picks, _fetches)
assert s.read_page(_u, pick=True)["picked"] and len(_fetches) == 2, "a picked page is kept like any other"
s.fetch_public, s.picked, s.public_url = _real_fetch, _real_picked, _real_public
# a stand-in's words carry no byline of the original's, and never come from the refusing publisher's other addresses
_pages = {"https://ax.example/2": {"body": "<p>" + _long + "</p>", "words": 300}}
s.read_page = lambda u, **k: {"url": u, "site": "WSJ", "title": "T", "deck": "", "image": None, "author": "Jane Doe", "published": 0, "body": "<p>teaser</p>", "words": 90, "held": True} if "wsj" in u else _pages[u]
s.known_item = lambda u: None
s.elsewhere = lambda item, url, story: {"body": "<p>whole</p>", "words": 800, "via": {"src": "AP", "u": "https://ap.example/1"}}
assert s.reader("https://www.wsj.example/x")["author"] is None
s.elsewhere = _real_else
_real_news = find.news
find.news = lambda q, at, most=8: [{"t": "Vance distances himself from the administration", "u": "https://amp.nyt.example/9", "src": "NYT", "ts": None}]
s.spend_find, _searched_q = (lambda kind: None), None
assert s.elsewhere(None, "https://www.nyt.example/2026/11/04/vance-distances-himself-administration.html", {}) == {}, "not the refusing paper's own amp. copy"
find.news, s.spend_find, s.read_page, s.known_item = _real_news, _real_spend_find, _real_read, _real_known
# the full text for search engines is meant to be plain; markup and entities in it print as text, not as code
_ld = '<script type="application/ld+json">{"articleBody": "<p>First&nbsp;part of the story.</p>' + "More of the story follows here. " * 20 + '"}</script>'
_got = s.extract(f"<html><body>{_ld}</body></html>", "https://x.example/ent")
assert "&amp;nbsp;" not in _got["body"] and "&lt;p&gt;" not in _got["body"] and "First part of the story." in _got["body"].replace("\xa0", " "), _got["body"][:200]
# a line that is nothing but links is a byline or a teaser: PBS prints its byline's link twice
_byline = '<p><a href="/author/ap">Associated Press</a>\n <a href="/author/ap">Associated Press</a></p>'
_got = s.extract(f"<html><body><article>{_byline}<p>{_long}</p>{_para(1)}{_para(2)}</article></body></html>", "https://x.example/pbs")
assert "Associated Press" not in _got["body"] and "Paragraph 2" in _got["body"], _got["body"][:200]
assert not s.link_only({"html": 'Read more: <a href="/x">this</a>'}) and s.link_only({"html": '<a href="/x">One</a>, <a href="/y">Two</a>'})
# a refused page the paper never saw takes its stand-in's headline
s.read_page = lambda u, **k: (_ for _ in ()).throw(urllib.error.HTTPError(u, 403, "Forbidden", {}, None)) if "toms" in u else {"body": "<p>" + _long + "</p>", "words": 400, "title": "AMD beats forecasts"}
s.known_item = lambda u: None
s.elsewhere = lambda item, url, story: {"body": "<p>whole</p>", "words": 400, "via": {"src": "Yahoo Finance", "u": "https://y.example/1", "t": "AMD beats forecasts"}}
assert s.reader("https://www.toms.example/amd-outsell-intel")["title"] == "AMD beats forecasts"
s.read_page, s.known_item, s.elsewhere = _real_read, _real_known, _real_else
# ...but a refused page the paper did see keeps its own headline, whatever its stand-in called the story
s.read_page = lambda u, **k: (_ for _ in ()).throw(urllib.error.HTTPError(u, 403, "Forbidden", {}, None))
s.known_item = lambda u: _item
s.elsewhere = lambda item, url, story: {"body": "<p>whole</p>", "words": 651, "via": {"src": "Daily Wire", "u": "https://dw.example/1", "t": "JD Vance Pins Republican Midterm Losses On Iran War"}}
assert s.reader("https://nyt.example/0")["title"].startswith("Vance, in Break")
s.read_page, s.known_item, s.elsewhere = _real_read, _real_known, _real_else
