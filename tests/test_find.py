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
