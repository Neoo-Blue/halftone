# Run from test_paper.py: what you hold, priced, and what the tape shows.
import invest as inv

rows = inv.typed([{"symbol": "aapl", "shares": "10", "buy": "150", "tape": "yes"}, {"symbol": "VOO", "shares": "2", "buy": "", "tape": "no"}, {"symbol": "TSLA", "shares": "", "buy": "", "tape": "yes"}])
assert rows[0]["symbol"] == "AAPL" and rows[1]["buy"] is None and rows[1]["tape"] is False and rows[2]["shares"] == 0
q = {"AAPL": {"name": "Apple", "price": 200.0, "prev": 190.0, "currency": "USD"}, "VOO": {"name": "S&P", "price": 500.0, "prev": 505.0, "currency": "USD"}, "TSLA": {"name": "Tesla", "price": 300.0, "prev": 300.0, "currency": "USD"}}
rep = inv.report(rows, q, {"USD": 1.0})
assert rep["total"] == 3000 and rep["day"] == 90 and rep["cost"] == 1500 and rep["gain"] == 500, rep
assert round(rep["gain_pct"], 2) == 33.33 and rep["no_buy"] == 1, "the gain only counts what has a buy price, and says how many don't"
assert next(r for r in rep["positions"] if r["symbol"] == "TSLA")["value"] is None, "a watched symbol isn't money"
assert rep["no_price"] == []
gone = inv.report(rows, {"AAPL": q["AAPL"]}, {"USD": 1.0})
assert sorted(gone["no_price"]) == ["TSLA", "VOO"] and gone["total"] == 2000, "a symbol with no price is named, never a zero"
eur = inv.report(inv.typed([{"symbol": "SAP.DE", "shares": "1", "buy": "100"}]), {"SAP.DE": {"name": "SAP", "price": 110.0, "prev": 100.0, "currency": "EUR"}}, {"USD": 1.0, "EUR": 1.2})
assert round(eur["total"], 2) == 132 and round(eur["gain"], 2) == 12, "totals are in dollars"
assert inv.report(inv.typed([{"symbol": "X", "shares": "1"}]), {"X": {"name": "", "price": 5.0, "prev": 5.0, "currency": "EUR"}}, {"USD": 1.0})["total"] is None, "a currency with no rate isn't counted at one to one"
two = inv.merged(inv.typed([{"symbol": "A", "shares": "1", "buy": "100"}, {"symbol": "A", "shares": "3", "buy": "200"}]))
assert len(two) == 1 and two[0]["shares"] == 4 and two[0]["buy"] == 175, "two lots add up, at their average price"
assert inv.merged(inv.typed([{"symbol": "A", "shares": "1", "buy": "100"}, {"symbol": "A", "shares": "3"}]))[0]["buy"] is None, "an unknown lot makes the average unknown"
assert inv.merged(inv.typed([{"symbol": "A"}, {"symbol": "A", "shares": "3", "buy": "200"}]))[0]["buy"] == 200, "a row that only watches doesn't erase a real lot's price"
assert inv.glance(rep, False)["gain"] is None and inv.glance(rep, True)["gain"] == 500, "gain can be turned off"
assert [t["label"] for t in inv.glance(rep, True)["tape"]] == ["AAPL", "TSLA"], "only what's marked for the tape"
assert inv.glance({}, True) == {"total": None, "day": None, "gain": None, "gain_pct": None, "tape": []}
feed = inv.from_feed({"positions": [{"symbol": "nvda", "shares": 2, "buy": 100.5, "tape": False}]})
assert feed[0]["symbol"] == "NVDA" and feed[0]["tape"] is False and feed[0]["source"] == "feed"
for bad in ([], {"positions": "x"}, {"positions": [{"symbol": "<b>", "shares": 1}]}, {"positions": [{"symbol": "A", "shares": float("nan")}]}, {"positions": [{"symbol": "A", "shares": -1}]}, {"positions": [{"symbol": "A", "buy": True}]}, {"positions": [{"shares": 1}]}):
    try:
        inv.from_feed(bad)
    except (ValueError, KeyError, TypeError):
        continue
    raise AssertionError(bad)

for bad in ([{"symbol": "<b>", "shares": "1", "buy": "", "tape": "yes"}], [{"symbol": "A", "shares": "lots", "buy": "", "tape": "yes"}], [{"symbol": "A", "shares": "1", "buy": "-5", "tape": "yes"}], [{"symbol": "A", "shares": "1", "buy": "", "tape": "maybe"}]):
    assert refuses(settings.update, {"HOLDINGS": bad}), bad
assert not s.job_on("portfolio") and s.paper()["invest"]["total"] is None, "nothing added shows nothing"
settings.update({"HOLDINGS": [{"symbol": "AAPL", "shares": "10", "buy": "150", "tape": "yes"}, {"symbol": "OOPS", "shares": "1", "buy": "1", "tape": "yes"}], "TAPE_OFF": "Gold, Wheat"})
assert s.job_on("portfolio") and s.tape_off() == ["Gold", "Wheat"]
real_json = s.open_json
got = []


def yahoo(url, *allowed):
    got.append(url)
    assert allowed == (s.QUOTES,) and "range=1d" in url
    if "OOPS" in url:
        raise s.urllib.error.HTTPError(url, 404, "no", {}, None)
    return {"chart": {"result": [{"meta": {"regularMarketPrice": 200.0, "chartPreviousClose": 190.0, "currency": "USD", "shortName": "<b>Apple</b>"}}]}}


s.open_json = yahoo
first = s.portfolio()
assert first["total"] == 2000 and first["no_price"] == ["OOPS"] and "<" not in first["positions"][0]["name"], first
s.save("portfolio", first)
shown = s.paper()
assert shown["invest"]["total"] == 2000 and shown["invest"]["gain"] == 500 and shown["on"]["invest"] and shown["tape_off"] == ["Gold", "Wheat"]
page = s.detail("investments", "")
assert page["kind"] == "investments" and page["holdings"][0]["symbol"] == "AAPL" and page["show_gain"] is True
s.open_json = lambda *a: (_ for _ in ()).throw(OSError("down"))
held = s.portfolio()
kept = next(r for r in held["positions"] if r["symbol"] == "AAPL")
assert kept["stale"] and kept["price"] == 200 and held["total"] == 2000 and kept["pct"] is None and kept["day"] is None, "a price that can't be read keeps the last one and says so, and today's move is unknown"
s.open_json = yahoo
settings.update({"PORTFOLIO_URL": "http://broker.example/positions", "PORTFOLIO_TOKEN": "tok"})
real_fetch = s.fetch
s.fetch = lambda url, head=None, **k: {"positions": [{"symbol": "NVDA", "shares": 1, "buy": 100}]} if head == {"Authorization": "Bearer tok"} else None
assert {r["symbol"] for r in s.portfolio()["positions"]} == {"AAPL", "OOPS", "NVDA"}, "a broker's holdings join the typed ones"
s.fetch = lambda *a, **k: (_ for _ in ()).throw(OSError("down"))
s.save("portfolio", {"fed": [inv.holding("NVDA", 1, 100, True, "feed")], "positions": []})
down = s.portfolio()
assert down["missing"] == ["The portfolio address"] and {r["symbol"] for r in down["positions"]} == {"AAPL", "OOPS", "NVDA"}, "a broker having a bad minute keeps what it last gave, and says so"
s.fetch = real_fetch
assert "HOLDINGS" in s.HELD_BACK and all(f["key"] != "HOLDINGS" for f in s.configurable()), "an AI never sees what you hold"
assert "invest" not in str(list(s.AI_TOOLS))

def meta(**k):
    return lambda *a: {"chart": {"result": [{"meta": {"regularMarketPrice": 100.0, "chartPreviousClose": 95.0, "currency": "USD", "shortName": "X", **k}}]}}


s.open_json = meta(chartPreviousClose=1e-305)
assert s.quote("X")["prev"] == 0, "a tiny previous close is no previous close, or the day's change is infinite"
for bad in ({"regularMarketPrice": 0}, {"currency": "eur"}, {"currency": ""}, {"currency": "USDX"}):
    s.open_json = meta(**bad)
    assert refuses(s.quote, "X"), bad
s.open_json = meta(currency="GBp", regularMarketPrice=1000.0)
assert (s.quote("X")["price"], s.quote("X")["currency"]) == (10.0, "GBP"), "pence become pounds"
s.open_json = meta(currency="ZAc", regularMarketPrice=500.0)
assert s.quote("X")["currency"] == "ZAR"
huge = inv.report(inv.typed([{"symbol": "A", "shares": "1", "buy": "0.00000001"}]), {"A": {"name": "", "price": 5.0, "prev": 5.0, "currency": "USD"}}, {"USD": 1.0})
s.save("portfolio", huge)
assert s.load("portfolio")["data"]["total"] == 5, "a tiny cost can't make an infinite percentage"


def euros(url, *a):
    if "EURUSD" in url:
        raise OSError("down")
    return meta(currency="EUR")(url)


s.open_json = euros
settings.update({"HOLDINGS": [{"symbol": "SAP.DE", "shares": "1", "buy": "", "tape": "yes"}], "PORTFOLIO_URL": ""})
s.save("portfolio", {"rates": {"USD": 1.0, "EUR": 1.25}, "positions": []})
kept_rate = s.portfolio()
assert kept_rate["total"] == 125 and not kept_rate["missing"], "a rate that can't be read keeps the last one"
s.save("portfolio", {})
no_rate = s.portfolio()
assert no_rate["total"] is None and no_rate["missing"] == ["The EUR rate"], "and with none it says so, rather than quietly shrinking the total"
s.open_json = meta()
settings.update({"HOLDINGS": [{"symbol": f"S{i}", "shares": "1", "buy": "", "tape": "no"} for i in range(70)]})
many = s.portfolio()
assert len(many["positions"]) == inv.MAX_HOLDINGS and many["missing"] == ["Holdings past the first 60"], "a cut is named"
settings.update({"HOLDINGS": [{"symbol": "aapl", "shares": "1", "buy": "", "tape": "yes"}]})
assert s.d_investments("")["holdings"][0]["symbol"] == "AAPL", "the page matches holdings by the same spelling the report uses"
s.open_json = real_json
settings.update({"HOLDINGS": [], "TAPE_OFF": "", "PORTFOLIO_URL": ""})
s.save("portfolio", {})

# ---------------------------------------------------------------- how a theater got here
sample = {"began": "2017-08-18", "began_note": "It starts here.", "summary": "A <b>summary</b>.", "eras": [{"name": "First", "from": "2017", "to": "2019", "summary": "Era.", "events": [{"date": "2017-08-18", "title": "USTR opens an inquiry", "detail": "Detail.", "source": "https://ustr.gov/x"}, {"date": "2018-07", "title": "Tariffs", "detail": "", "source": "javascript:alert(1)"}, {"date": "2019", "title": "Year only", "source": "http://plain.example"}]}]}
clean_h = s.clean_history(sample)
assert "<" not in clean_h["summary"] and clean_h["eras"][0]["events"][0]["source"] == "https://ustr.gov/x", clean_h
assert [e["source"] for e in clean_h["eras"][0]["events"]][1:] == [None, None], "a source is a plain web address or nothing"
bad_date = lambda d: {"eras": [{"name": "x", "from": "1", "to": "2", "events": [{"date": d, "title": "t"}]}]}
assert s.clean_history({"began": "2017-08-18", **bad_date("2024-02")})["eras"][0]["events"][0]["date"] == "2024-02"
assert s.clean_history({"eras": [{"name": "x", "from": "1", "to": "2", "events": [{"date": "2024", "title": "t", "source": "https://"}]}]})["eras"][0]["events"][0]["source"] is None, "a source needs a host"
for bad in (bad_date("soon"), bad_date("2024-13-45"), bad_date("\u0662\u0660\u0662\u0664"), {"began": "<img", **bad_date("2024")}, {"eras": "x"}, {}, []):
    try:
        s.clean_history(bad)
    except (ValueError, KeyError, TypeError, AttributeError):
        continue
    raise AssertionError(bad)
try:
    s.parsed(b"[" * 200000)
except ValueError:
    pass
else:
    raise AssertionError("nesting that stops the parser is a bad answer, not a dropped connection")
real_war = s.war
s.war = lambda path, timeout=30: (_ for _ in ()).throw(OSError("older WARROOM"))
assert s.theater_history("x") is None, "with no timeline the page simply goes without"
s.war = lambda path, timeout=30: sample
assert s.theater_history("x")["began"] == "2017-08-18"
s.war = real_war
notice = {"id": "1", "title": "Mobile Access Equipment From China: Five-Year Review", "ts": NOW, "source": "federal_register", "severity": .4, "domain": "economic"}
assert not s.curated([notice]) and s.curated([notice], notices=True), "a notice isn't front page news, but on a trade theater it's the story"
