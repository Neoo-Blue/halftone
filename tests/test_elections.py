# Election watch: only what's known gets through, the sums are right, and the desk leaves on its own. Runs inside test_paper.py.
import elections as elect
from datetime import date as _date

_day = _date(2026, 11, 1)
_race = lambda key, kind, **more: {"key": key, "kind": kind, "state_name": "Georgia", "name": "A race", "nominees": {"D": "Dee", "R": "Arr", "X": "No"}, "candidates": [{"name": "Dee", "party": "D", "votes": 60, "pct": 60.0}, {"name": "Arr", "party": "R", "votes": 40, "pct": 40.0}], "prob": {"D": .7}, "rating": "Lean D", "market": {"d": .8, "r": .2}, "reporting": 0.0, **more}
assert elect.race({"key": "S-GA; DROP", "kind": "senate"}) is None and elect.race({"key": "S-GA", "kind": "measure"}) is None, "only a race, and only a real key"
_r = elect.race({**_race("S-GA", "senate"), "state_name": "<b>Georgia</b>", "prob": {"D": float("nan")}, "market": {"d": 5}, "candidates": [{"name": "<i>Dee</i>", "party": "Z", "votes": True, "pct": "x"}, 7]})
assert _r["where"] == "Georgia" and _r["pd"] is None and _r["md"] is None and _r["runners"] == [{"n": "Dee", "p": "O", "votes": 0, "pct": 0, "won": False}] and "X" not in _r["noms"], _r

# the calendar: one vote per country and date, confirmed, near, and not the US or its territories
_cal = [{"id": "eg-1", "country": "Bulgaria", "iso2": "BG", "institution": "Presidency", "start": "2026-11-01", "end": "2026-11-01", "status": "Confirmed", "phase": "voting"},
        {"id": "eg-2", "country": "Norland", "iso2": "NO", "institution": "Senate", "start": "2026-11-10", "end": "2026-11-10", "status": "Confirmed", "phase": "upcoming"}, {"id": "eg-3", "country": "Norland", "iso2": "NO", "institution": "House", "start": "2026-11-10", "end": "2026-11-10", "status": "Confirmed", "phase": "upcoming"},
        {"id": "eg-4", "country": "Farland", "iso2": "FA", "institution": "House", "start": "2026-12-20", "end": "2026-12-20", "status": "Confirmed", "phase": "upcoming"}, {"id": "eg-5", "country": "Guess", "iso2": "GS", "institution": "House", "start": "2026-11-05", "end": "2026-11-05", "status": "Date not confirmed", "phase": "upcoming"},
        {"id": "eg-6", "country": "United States of America", "iso2": "US", "institution": "US Senate", "start": "2026-11-03", "end": "2026-11-03", "status": "Confirmed", "phase": "upcoming", "featured": "us-2026"}, {"id": "eg-7", "country": "Guam", "iso2": "GU", "institution": "Governor", "start": "2026-11-03", "end": "2026-11-03", "status": "Confirmed", "phase": "upcoming"},
        {"id": "eg-8", "country": "Oldland", "iso2": "OL", "institution": "House", "start": "2026-10-01", "end": "2026-10-01", "status": "Confirmed", "phase": "results"}, {"id": "../x", "country": "Bad", "iso2": "BD", "institution": "House", "start": "2026-11-02", "end": "2026-11-02", "status": "Confirmed", "phase": "upcoming"}]
_w = elect.world(_cal, _day)
assert [e["country"] for e in _w] == ["Bulgaria", "Norland"] and _w[1]["offices"] == ["Senate", "House"], _w

_us = {"id": "us-2026", "name": "US midterm elections", "date": "2026-11-03", "phase": "campaign", "presidential": False, "schedule": {"first_close": 1}, "generic_ballot": {"d": 49.8, "r": 42.5, "last": "2026-10-04"},
       "control": {"house": {"seats": 435, "majority": 218, "market": {"d": .95, "r": .05}}, "senate": {"seats": 100, "majority": 51, "holdover": {"D": 32, "R": 31, "I": 2}, "market": {"d": .71, "r": .29}}, "governor": {"seats": 50, "majority": 26}},
       "races": [_race("S-GA", "senate"), _race("S-IA", "senate", rating="Tossup", prob={"D": .49}), _race("G-GA", "governor"), _race("H-GA-02", "house"), _race("H-GA-01", "house", rating="Safe R", prob={"D": .02})], "sources": [{"label": "civicAPI"}]}
_v = elect.summary({"us": elect.us(_us), "world": _w}, _day)
_s = _v["us"]
assert _s["title"] == "2 days to the midterms" and _s["line"] == "Betting markets have Democrats at 95% for the House and Democrats at 71% for the Senate.", _s
_h, _sn, _g = (next(c for c in _s["chambers"] if c["kind"] == k) for k in ("house", "senate", "governor"))
assert _h["lean"] == {"D": 1, "R": 1} and _h["seats"] == 435 and _sn["lean"] == {"D": 1, "T": 1} and _sn["held"] == {"D": 32, "R": 31, "I": 2} and _g["seats"] == 1 and _g["majority"] is None, (_h, _sn, _g)
assert _s["closest"][0]["key"] == "S-IA" and _s["map"]["senate"]["GA"] == [.4] and _s["map"]["house"]["GA"] == [.4, -.96], "the closest first, and the map's ink"
assert list(_s["map"]) == ["house", "senate", "governor"] and "races" not in _s and "runners" not in _s["closest"][0], "the page polls this every minute, so it stays small"
assert elect.summary({"us": elect.us({**_us, "date": "2026-10-20"})}, _day)["us"]["phase"] == "campaign", "still up two weeks after the day"

# the night, and the morning after
_night = {**_us, "phase": "counting", "races": [_race("S-GA", "senate", winner={"name": "Dee", "party": "D"}, called_at=100, reporting=90.0), _race("S-IA", "senate", leader={"name": "Arr", "party": "R", "pct": 51.0}, reporting=60.0, candidates=[{"name": "Arr", "party": "R", "votes": 51, "pct": 51.0}, {"name": "Dee", "party": "D", "votes": 49, "pct": 49.0}]), _race("H-GA-02", "house", winner={"name": "Dee", "party": "D"}, called_at=99)]}
_n = elect.summary({"us": elect.us(_night)}, _date(2026, 11, 4))["us"]
assert _n["title"] == "2 of 3 races called" and _n["calls"][0]["key"] == "S-GA" and _n["map"]["senate"]["GA"] == [1] and _n["map"]["senate"]["IA"] == [-.5], _n
_seat = next(c for c in _n["chambers"] if c["kind"] == "senate")
assert _seat["won"] == {"D": 1} and _seat["ahead"] == {"R": 1} and _seat["decided"] is None
assert elect.chamber([elect.race(_race(f"S-A{chr(65 + i)}", "senate", winner={"name": "Dee", "party": "D"})) for i in range(16)], "senate", {"seats": 100, "majority": 51, "held": {"D": 33, "R": 31, "I": 2}})["decided"] == "D", "independents caucus with Democrats, so 51 is a majority"

# and it leaves: nothing near means no desk at all, however recent the snapshot
assert elect.summary({"us": elect.us(_us), "world": []}, _date(2026, 11, 18))is None, "the US desk goes two weeks after the day"
assert elect.summary({"us": elect.us({**_us, "date": "2028-11-07"}), "world": []}, _day) is None, "and doesn't come back until two months before the next"
assert elect.summary({"us": None, "world": _w}, _date(2026, 11, 26)) is None, "a vote abroad goes a week after, even if the job has stopped"
assert elect.summary(None, _day) is None and elect.summary({"us": None, "world": []}, _day) is None
assert elect.summary({"us": None, "world": _w}, _day)["us"] is None, "an election abroad is enough on its own"
_out = elect.outcome({"line": "A wins", "url": "javascript:alert(1)", "rows": [{"party": "A", "person": "None", "seats_won": 141, "pct": 53.0}, "x"]})
assert _out["url"] is None and _out["rows"] == [{"party": "A", "person": "", "seats": 141, "pct": 53.0}], _out

# what it all adds up to, because a page of numbers isn't insight
_held = {"D": 33, "R": 31, "I": 2}
_seats = [elect.race(_race(f"S-{a}", "senate", prob={"D": p}, rating="Tossup")) for a, p in (("AA", .9), ("AB", .7), ("AC", .55), ("AD", .4), ("AE", .1))]
_lad = elect.ladder(_seats, 35 + 13, 51)
assert _lad["need"] == 3 and _lad["tip"]["key"] == "S-AC" and _lad["chance"] == .55 and len(_lad["steps"]) == 5, _lad
assert elect.ladder(_seats, 60, 51) is None and elect.ladder(_seats, 40, 51) is None, "nothing to decide, or out of reach"

_flip = elect.race({**_race("S-AK", "senate"), "incumbent_party": "R", "rating": "Tilt D", "holder": {"name": "Dan Sullivan", "since": "2015-01-03"}, "nominees": {"D": "Mary Peltola", "R": None}, "candidates": [{"name": "Dan Sullivan", "party": "R"}, {"name": "Mary Peltola", "party": "D"}]})
assert not elect.open_seat(_flip) and _flip["noms"]["R"] == "Dan Sullivan", "a sitting member the nominee list has missed isn't an open seat"
assert elect.gains([_flip])["D"][0]["state"] == "AK"
_said = " ".join(elect.reading(_flip))
assert "Tilts Democratic, with Mary Peltola favoured" in _said and "Dan Sullivan has held it since 2015" in _said and "take it from the Republicans" in _said, _said
_open = elect.race({**_race("S-NH", "senate"), "incumbent_party": "D", "rating": "Lean D", "holder": {"name": "Jeanne Shaheen", "since": "2009-01-06"}, "prob": {"D": .68}, "market": {"d": .94, "r": .06}})
assert elect.open_seat(_open) and "An open seat: Jeanne Shaheen" in " ".join(elect.reading(_open)) and "Bettors are surer of Democrats than the model, 94% to 68%" in " ".join(elect.reading(_open))
_kansas = elect.race({**_race("S-KS", "senate"), "rating": "Tilt R", "prob": {"D": .36}, "polls": {"d": 49.4, "r": 46.6, "n": 6, "last": "2026-10-20"}, "ratings": {"cook": "Tossup", "sabato": "Tossup", "ddhq": "Likely R"}})
_said = " ".join(elect.reading(_kansas))
assert "The polls point the other way, 49.4 to 46.6" in _said and "Forecasters split: Cook and Sabato say toss-up; DDHQ says Likely R" in _said, _said
_sig = elect.signals([_open, _kansas])
assert {g["key"] for g in _sig["gaps"]} == {"S-NH", "S-KS"} and _sig["against"][0]["key"] == "S-KS" and _sig["splits"] == 1, _sig

# on the night: what the trailing candidate needs, and when it's over
_count = elect.race(_race("S-GA", "senate", reporting=80.0, leader={"name": "Dee", "party": "D", "pct": 55.0}, candidates=[{"name": "Dee", "party": "D", "votes": 5500, "pct": 55.0}, {"name": "Arr", "party": "R", "votes": 4500, "pct": 45.0}]))
_c = elect.chase(_count)
assert _c == {"lead": "Dee", "trail": "Arr", "gap": 1000, "left": 2500, "need": .7}, _c
assert "Arr would need 70% of what's left" in " ".join(elect.reading(_count))
_late = elect.race(_race("S-GA", "senate", reporting=98.0, leader={"name": "Dee", "party": "D", "pct": 60.0}, candidates=[{"name": "Dee", "party": "D", "votes": 6000, "pct": 60.0}, {"name": "Arr", "party": "R", "votes": 4000, "pct": 40.0}]))
assert elect.chase(_late)["need"] > 1 and "can't catch up" in " ".join(elect.reading(_late))
assert elect.chase(elect.race(_race("S-GA", "senate"))) is None and elect.chase(elect.race(_race("S-GA", "senate", reporting=100.0))) is None, "nothing out, nothing to chase"
_gain = elect.race({**_race("S-GA", "senate"), "incumbent_party": "R", "winner": {"name": "Dee", "party": "D"}})
assert elect.reading(_gain)[0] == "Dee wins, a Democratic gain."

_night = elect.hours([elect.race(_race("S-GA", "senate", rating="Tossup", prob={"D": .5})), elect.race(_race("S-ME", "senate", rating="Tossup", prob={"D": .55})), elect.race(_race("H-GA-02", "house"))], 1000)
_ga = next(h for h in _night if "GA" in h["states"])
assert _ga["at"] == 4600 and [w["key"] for w in _ga["watch"]] == ["S-GA"] and next(h for h in _night if "ME" in h["states"])["at"] == 8200 and _night[-1]["states"] == ["AK"], _night
assert sorted(s for _, states in elect.CLOSES for s in states.split() if s not in ("IN", "KY")) + ["IN", "KY"] and {s for _, states in elect.CLOSES for s in states.split()} == set("AL AK AZ AR CA CO CT DC DE FL GA HI IA ID IL IN KS KY LA MA MD ME MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY".split()), "every state has a closing time"
assert elect.polls({"polls_list": [{"pollster": "A", "end": "2026-10-20", "D": 50, "R": 45, "url": "javascript:x"}, {"pollster": "B", "end": "2026-10-28", "D": 51, "R": 44, "url": "https://a.example/p"}, {"pollster": "C", "end": "soon", "D": 1, "R": 2}]})[0]["who"] == "B", "newest first, and only what's a poll"

# what the independent review found: each of these went wrong once
_mix = elect.race({**_race("S-GA", "senate"), "polls": {"d": 50.0}, "ratings": {"cook": "<b></b>", "sabato": "Lean D"}})
assert _mix["poll"] is None and "cook" not in _mix["ratings"], "half a poll, or a rating that cleans to nothing, can't reach the sums"
assert elect.signals([_mix])["splits"] == 0 and elect.reading(_mix)

assert elect.surname("Nydia M. Velázquez") == elect.surname("Nydia Velazquez") == "velazquez" and elect.surname("Sanford D. Bishop, Jr.") == "bishop"
assert not elect.open_seat(elect.race({"key": "H-AK-AL", "kind": "house", "holder": {"name": "Nick Begich"}})), "no field, so nothing to say about who's running"
_ahead = elect.race(_race("S-GA", "senate", rating="Safe D", reporting=100.0, leader={"name": "Arr", "party": "R", "pct": 51.0}))
assert "Safe" not in " ".join(elect.reading(_ahead)) and "Arr is ahead with 100% counted" in elect.reading(_ahead)[0], "a rating's grade never goes on the count's side"
assert not any(" Democratic, with" == x[:16] for x in elect.reading(elect.race({**_race("S-GA", "senate"), "rating": ""}))), "no rating says nothing, not half a sentence"
_tie = elect.race(_race("S-GA", "senate", reporting=50.0, leader={"name": "Dee", "party": "D", "pct": 50.0}, candidates=[{"name": "Dee", "party": "D", "votes": 500, "pct": 50.0}, {"name": "Arr", "party": "R", "votes": 500, "pct": 50.0}]))
assert "Dee and Arr are level" in " ".join(elect.reading(_tie)) and "0 votes" not in " ".join(elect.reading(_tie))
assert not elect.polls_against(elect.race({**_race("S-GA", "senate"), "rating": "Lean R", "polls": {"d": 47.0, "r": 47.0, "n": 3, "last": "2026-10-20"}})), "a tied poll points nowhere"

_ind = [elect.race(_race(f"S-A{chr(65 + i)}", "senate", winner={"name": "Dee", "party": "I" if i == 0 else "D"})) for i in range(16)]
assert elect.chamber(_ind, "senate", {"seats": 100, "majority": 51, "held": {"D": 33, "R": 31, "I": 2}})["decided"] is None, "a new independent hasn't said who they'd sit with"
_r50 = [elect.race(_race(f"S-A{chr(65 + i)}", "senate", winner={"name": "Arr", "party": "R"})) for i in range(19)]
assert elect.chamber(_r50, "senate", {"seats": 100, "majority": 51, "held": {"D": 34, "R": 31, "I": 2}})["decided"] == elect.TIE, "fifty and the vice president is a majority"
assert elect.chance(elect.race(_race("S-GA", "senate", winner={"name": "Ind", "party": "I"}))) == .5 == elect.chance(elect.race(_race("S-GA", "senate", leader={"name": "Ind", "party": "I", "pct": 40.0}, reporting=9.0)))

_old = elect.us({**_us, "schedule": {"polls_open": 100, "first_close": 200}})
assert elect.summary({"us": _old}, _day, 50)["us"]["phase"] == "campaign" and elect.summary({"us": _old}, _day, 150)["us"]["phase"] == "voting" and elect.summary({"us": _old}, _day, 250)["us"]["phase"] == "counting", "the clock says, not an old copy"
assert elect.headline({"presidential": False, "date": "2026-11-03", "phase": "counting", "chambers": []}, _day)["line"] == ""
# the front page's one-line glance gets a short form of the result, which fits its row
_house = {"kind": "house", "name": "House", "decided": "D", "called": 435, "up": 435, "won": {"D": 230, "R": 205}}
_senate = {"kind": "senate", "name": "Senate", "decided": "D", "called": 35, "up": 35, "won": {"D": 20, "R": 15}}
_h = elect.headline({"presidential": False, "date": "2026-11-03", "phase": "counting", "chambers": [_house, _senate]}, _day)
assert _h["title"] == "Democrats win the House. Democrats win the Senate" and _h["short"] == "Democrats win Congress", _h
assert elect.headline({"presidential": False, "date": "2026-11-03", "phase": "counting", "chambers": [_house, {**_senate, "decided": "R"}]}, _day)["short"] == "House D \u00b7 Senate R"
assert elect.headline({"presidential": False, "date": "2026-11-03", "phase": "counting", "chambers": [{**_house, "decided": None}, {**_senate, "decided": None, "called": 0}]}, _day)["short"] == "435 of 470 races called"
_won = elect.outcome({"decided": False, "rows": [{"party": "A"}, {"party": "B", "pct": 40.0}]})
assert _won["decided"] is False and [r["party"] for r in _won["rows"]] == ["B"], "a row with no numbers isn't a result"

# the job looks again when it should, and a bad answer can't replace a good one
_real_war, _asked, _soon = s.war_open, [], (s.datetime.now(s.zone()).date() + s.timedelta(days=2)).isoformat()
_doc = {**_us, "date": _soon}
s.war_open = lambda path, timeout=30: _asked.append(path) or ({"featured": {"id": "us-2026", "date": _soon, "phase": "campaign"}, "items": []} if path == "/elections" else _doc)
s.save("elections", s.elections_run())
s.save("elections", s.elections_run())
assert _asked.count("/elections/us") == 1, "calm before the polls open"
_held = s.load("elections")["data"]
s.save("elections", {**_held, "us": {**_held["us"], "fetched": 1}})
s.save("elections", s.elections_run())
assert _asked.count("/elections/us") == 2, "but it does look again: save() stamps every run, so the age lives in the snapshot"
assert s.election_view()["as_of"] and s.election_view()["us"]["title"] == "2 days to the midterms"
_good = s.load("elections")["data"]
s.save("elections", {**_good, "us": {**_good["us"], "fetched": 1}})
_doc = {**_us, "date": _soon, "races": "not a list"}
_bad = False
try:
    s.elections_run()
except (TypeError, AttributeError, KeyError):
    _bad = True
assert _bad or s.elections_run()["us"]["races"] == [], "an answer that can't be read raises, and the job keeps the last good copy"

# while votes are counted nothing on the way waits: every job is 30 seconds, and a late count still gets looked at after the phase turns final
assert dict((n, e) for n, _, e in s.JOBS)["elections"] == 30 == dict((n, e) for n, _, e in s.JOBS)["following"], "the job can't hold the count back"
assert s.FOLLOW_EVERY["race"] == 30, "nor can a followed race's card"
_doc = {**_us, "date": _soon, "live": True, "updated": {"races": 1793750000}}
s.war_open = lambda path, timeout=30: _asked.append(path) or ({"featured": {"id": "us-2026", "date": _soon, "phase": "final"}, "items": []} if path == "/elections" else _doc)
_asked.clear()
s.save("elections", s.elections_run())
_held = s.load("elections")["data"]
assert _held["us"]["live"] is True and _held["us"]["read"] == 1793750000, "WARROOM's word, and when it last read the count"
_v = s.election_view()
assert _v["us"]["live"] is True and _v["us"]["read"] == 1793750000
s.save("elections", {**_held, "us": {**_held["us"], "phase": "final"}})
s.save("elections", s.elections_run())
assert _asked.count("/elections/us") == 2, "a late count isn't left calm"
_doc = {**_us, "date": _soon, "live": False}
s.save("elections", s.elections_run())
assert _asked.count("/elections/us") == 3
_held = s.load("elections")["data"]
assert _held["us"]["live"] is False and _held["us"]["read"] is None
s.save("elections", {**_held, "us": {**_held["us"], "phase": "final"}})
s.save("elections", s.elections_run())
assert _asked.count("/elections/us") == 3, "and once it's over, it is"

# an open race page: the count alone, from the snapshot, never two minutes old
_doc = {**_us, "date": _soon, "live": True, "updated": {"races": 1793750000}}
s.save("elections", {**_held, "us": {**_held["us"], "phase": "final", "fetched": 1}})
s.save("elections", s.elections_run())
_key = s.load("elections")["data"]["us"]["races"][0]["key"]
_asked.clear()
_now = s.detail("count", _key)
assert not _asked, "it asks nobody"
assert _now["live"] is True and _now["read"] == 1793750000 and "reading" in _now and "runners" in _now and "polls" not in _now and _now["phase"], _now
_held = s.load("elections")["data"]
s.save("elections", {**_held, "us": {**_held["us"], "read": 1793750030}})
assert s.detail("count", _key)["read"] == 1793750030, "and isn't kept in the two-minute cache"
_ok, s.outside_news = s.outside_news, lambda q: []
_page = s.detail("race", _key)
assert _page["kind"] == "race" and _page["office"] and _page["live"] is True and _page["read"] == 1793750030, "the whole page has them too"
s.save("elections", {**_held, "us": {**_held["us"], "read": 1793750060}})
_again = s.detail("race", _key)
assert _again["read"] == 1793750060 and _again["q"] == _page["q"], "a page in the cache still opens on the latest count"
assert s.detail("elections", "")["us"]["read"] == 1793750060, "and so does the elections page"
try:
    s.detail("count", "S-ZZ")
    raise AssertionError("a race that isn't there")
except LookupError:
    pass
s.outside_news = _ok
s.HOT.clear()

_real_ask, _real_ready, _tried, _notes = s.ai.ask, s.ai.ready, [], {}
s.ai.ready = lambda: True
s.ai.ask = lambda *a, **k: _tried.append(1) or "A note."
s.NOTE_TRIED["at"] = 0
s.save("election_note", {"text": "Old.", "at": 1})
_doc = {**_us, "date": _soon}
assert s.election_note_run()["text"] == "A note." and len(_tried) == 1, "an old note is written again: its age is its own, not the job's"
s.NOTE_TRIED["at"] = 0
s.save("election_note", s.election_note_run())
_n = len(_tried)
s.NOTE_TRIED["at"] = 0
assert s.election_note_run()["text"] == "A note." and len(_tried) == _n, "and a fresh one isn't"
s.save("election_note", {"text": "Old.", "at": 1})
s.NOTE_TRIED["at"] = time.time()
assert s.election_note_run()["text"] == "Old." and len(_tried) == _n, "a provider that's failing gets one try each half hour"
s.ai.ask, s.ai.ready, s.war_open = _real_ask, _real_ready, _real_war
s.save("elections", {"us": None, "world": []})

# an edition reading WARROOM's own /api still gets the public shapes, which is what the live paper does
_fetched, _real_fetch = [], s.fetch
s.fetch = lambda url, **k: _fetched.append(url) or b"{}"
for _base in ("https://war.example/api", "https://war.example/api/", "https://war.example/api/v1"):
    settings.update({"WARROOM_URL": _base})
    s.war_open("/elections")
assert set(_fetched) == {"https://war.example/api/v1/elections"}, _fetched

# WARROOM as a good guest: an answer is reused for a few seconds, and a "slow down" is waited out on the last copy
s.WAR_SEEN.clear()
_fetched.clear()
_answers = [b'{"n": 1}']
s.fetch = lambda url, **k: _fetched.append(url) or _answers[0]
assert s.war_fetch("https://war.example/x", 5) == {"n": 1} == s.war_fetch("https://war.example/x", 5) and len(_fetched) == 1, "readers opening pages together ask once"
_got = s.war_fetch("https://war.example/x", 5)
_got["n"] = 99
assert s.war_fetch("https://war.example/x", 5) == {"n": 1}, "each caller gets its own copy, so one can't change another's"


def _busy(url, **k):
    _fetched.append(url)
    raise s.urllib.error.HTTPError(url, 429, "Too Many Requests", {"Retry-After": "120"}, None)


s.WAR_SEEN["https://war.example/x"] = (s.time.monotonic() - 600, b'{"n": 1}')
s.fetch = _busy
assert s.war_fetch("https://war.example/x", 5) == {"n": 1}, "told to slow down, the reader gets the last copy, not an error"
assert 110 < s.WAR_QUIET["api"] - s.time.monotonic() <= 120, "and the paper waits as long as it was asked"
_fetched.clear()
assert s.war_fetch("https://war.example/x", 5) == {"n": 1} and not _fetched, "nothing is asked while it waits"
s.fetch = lambda url, **k: _fetched.append(url) or b'{"n": 4}'
assert s.war_fetch("https://war.example/api/v1/y", 5) == {"n": 4} and _fetched, "a wait on the API doesn't hold /v1, which WARROOM rations apart"
_fetched.clear()
s.fetch = _busy
try:
    s.war_fetch("https://war.example/never-seen", 5)
    raise AssertionError("with no copy to give, it says so")
except s.Waiting as _w:
    assert not _fetched and 110 < _w.args[0] <= 121, "and how long to wait"
s.WAR_SEEN["https://war.example/old"] = (s.time.monotonic() - 7200, b'{"n": 2}')
try:
    s.war_fetch("https://war.example/old", 5)
    raise AssertionError("a copy two hours old isn't passed off as the news")
except s.Waiting:
    pass
s.WAR_QUIET["api"] = s.time.monotonic() + 0.2
_answers[0] = b'{"n": 3}'
s.fetch = lambda url, **k: _fetched.append(url) or _answers[0]
assert s.war_fetch("https://war.example/brief", 5) == {"n": 3}, "a short wait is sat out, not shown"
_answers[0] = b"not json"
s.WAR_SEEN["https://war.example/x"] = (s.time.monotonic() - 60, b'{"n": 1}')
try:
    s.war_fetch("https://war.example/x", 5)
    raise AssertionError("a broken answer is an error")
except ValueError:
    assert s.WAR_SEEN["https://war.example/x"][1] == b'{"n": 1}', "and it doesn't replace the last good copy"
s.WAR_QUIET.clear()
s.WAR_SEEN.clear()
s.fetch = _real_fetch
settings.update({"WARROOM_URL": ""})


# an analyst's note, told by an editor: once for each note, and a reply that isn't the shape leaves the analyst's words
_note = {"headline": "Hormuz composite risk falls to 0.55", "body": "Risk fell. <script>x</script>", "bullets": ["OBSERVED: AIS transits 12", {"text": "UNVERIFIED: a story"}], "ts": 1}
_asks, _real_ask, _real_ready = [], s.ai.ask, s.ai.ready
s.ai.ready = lambda: True
s.ai.ask = lambda system, text, **k: _asks.append((system, text)) or "HEAD: Ships still aren't coming back\nWHAT: About 12 a day cross.\n**WHY:** Oil.\nWATCH: Traffic."
_read = s.note_reading(_note)
assert _read == {"head": "Ships still aren't coming back", "what": "About 12 a day cross.", "why": "Oil.", "watch": "Traffic.", "doubt": True}, _read
assert "<script" not in _asks[0][1] and _asks[0][1].startswith("<note>") and "AIS transits 12" in _asks[0][1] and "a story" in _asks[0][1], "strangers' text can't close the tag it's held in"
assert s.note_reading(_note) == _read and len(_asks) == 1, "each note is told once"
s.ai.ask = lambda system, text, **k: "Sorry, I can't."
assert s.note_reading({**_note, "headline": "Another"}) is None, "a reply that isn't the shape leaves the analyst's words"
_with = s.with_reading([{**_note}, {**_note, "headline": "Older"}])
assert _with[0]["reading"] == _read and "reading" not in _with[1] and "telling" not in _with[0], "one already told comes with the page, and only the first note on a page is told"
assert s.with_reading([]) == []
s.ai.ask = lambda system, text, **k: _asks.append(1) or "HEAD: Ships held\nWHAT: Some ships wait.\nWHY: Oil.\nWATCH: Traffic."
_late = s.with_reading([{**_note, "headline": "A new one"}])[0]
assert "reading" not in _late and _late["telling"], "a new one follows the page, which never waits on a model"
assert s.detail("reading", _late["telling"])["reading"]["head"] == "Ships held", "and the page can ask for it"
for _odd in ("0" * 24, "not-a-key"):
    try:
        s.detail("reading", _odd)
        raise AssertionError("only a key a page was given")
    except (LookupError, KeyError):
        pass
_tellings = []
s.ai.ask = lambda system, text, **k: (_tellings.append(1), time.sleep(.2), "HEAD: Ships held\nWHAT: Some ships wait.\nWHY: Oil.\nWATCH: Traffic.")[2]
_a, _b = s.with_reading([{**_note, "headline": "Same note"}])[0], s.with_reading([{**_note, "headline": "Same note"}])[0]
assert _a["telling"] == _b["telling"] and s.detail("reading", _a["telling"])["reading"]["head"] == "Ships held" and len(_tellings) == 1, "one note on two pages is told once"

# a failure costs one question an hour, not the day's
_tries = []
def _down(system, text, **k):
    _tries.append(1)
    raise OSError("down")
s.ai.ask = _down
for _ in range(5):
    assert s.quiet(lambda: s.note_reading({**_note, "headline": "Provider down"})) is None
assert len(_tries) == 1, "a provider that's down gets one try"
_late = s.with_reading([{**_note, "headline": "Provider down"}])[0]
assert "telling" not in _late and "reading" not in _late, "and pages stop waiting on it"
s.ai.ask = lambda system, text, **k: _tries.append(1) or "I'd rather not."
_tries.clear()
for _ in range(3):
    s.note_reading({**_note, "headline": "Out of shape"})
assert len(_tries) == 1, "nor does a reply that isn't the shape get asked again"
_tries.clear()
assert s.note_reading({"headline": "", "body": "", "bullets": [{"text": None}], "ts": 1}) is None and not _tries, "an empty note costs nothing"

# what the rule says, the code holds to
_small = {"headline": "Two ships delayed near Iran", "body": "Two ships were delayed.", "bullets": ["UNVERIFIED: a report of 12 mines"], "ts": 1}
s.ai.ask = lambda system, text, **k: "HEAD: Forty ships sunk by Iran\nWHAT: Forty ships were sunk.\nWHY: Oil.\nWATCH: More."
assert s.note_reading(_small) is None, "a count the note never gave doesn't print"
s.ai.ask = lambda system, text, **k: "HEAD: 900 ships delayed\nWHAT: 900 ships.\nWHY: Oil.\nWATCH: More."
assert s.note_reading({**_small, "headline": "Another"}) is None, "nor does a number"
s.ai.ask = lambda system, text, **k: "HEAD: Ships delayed\nWHAT: Ships off Tehran and Dubai and Muscat are held.\nWHY: Oil.\nWATCH: More."
assert s.note_reading({**_small, "headline": "A third"}) is None, "nor a run of names the note never used"
s.ai.ask = lambda system, text, **k: "HEAD: Two ships are held up\nWHAT: Two ships were delayed near Iran, and the mines, about 12, aren't confirmed. Trade through the Gulf waits.\nWHY: Oil.\nWATCH: More."
_ok = s.note_reading({**_small, "headline": "A fourth, near Iran"})
assert _ok and _ok["doubt"] is True, "a true telling prints, one general name is fine, and an unverified note says so on the page"
assert s.note_holds("Brent at 113.43 a barrel", {"what": "Brent is about 113"}), "rounding isn't invention"
_says = "Hormuz transits fall to 12. Iran says two tankers hit mines. Trump says targets remain. Brent is at $113.43."
for _wrong in ("Fifteen ships crossed.", "Four ships crossed.", "It cost $90 trillion.", "Oil is at $113bn.", "And President Biden says so.", "And former President Trump says so.", "Putin ordered it. Netanyahu agreed. Zelensky objected.", "See evil-site.example now."):
    assert not s.note_holds(_says, {"what": _wrong}), _wrong
for _wrong in ("But Putin ordered it. And Netanyahu agreed.", "The Kremlin ordered it. The Vatican agreed.", "About a fifth of all oil crosses here."):
    assert not s.note_holds(_says, {"what": _wrong}), _wrong
_titled = _says + " Former President Trump spoke. A general and Iran's leader did not."
for _wrong in ("President Biden says so.", "General Soleimani says so.", "Iran's Supreme Leader Khamenei says so."):
    assert not s.note_holds(_titled, {"what": _wrong}), "a title in the note doesn't vouch for a new name: " + _wrong
assert s.note_holds(_titled, {"what": "President Trump says so."})
for _fine in ("Only twelve ships crossed.", "Only a dozen ships crossed.", "Iran says 2 tankers hit mines.", "Brent is around $110.", "Trade through the Gulf is at risk, and the two sides wait.", "Iran's Revolutionary Guard says so.", "The general picture is pressure.", "Insurers will decide. Crude could rise. Households pay.", "It matters to Europe and Asia and the United States."):
    assert s.note_holds(_says, {"what": _fine}), _fine
for _wrote in ("Damage of up to $15B.", "Damage of up to $15bn.", "Damage of up to $15 billion.", "Damage of up to 15 bn."):
    for _told in ("$15B", "$15bn", "$15 billion", "15 billion dollars"):
        assert s.note_holds(_wrote, {"what": f"Damage of up to {_told}."}), (_wrote, _told)
for _told in ("$15 trillion", "$15M", "$15mn"):
    assert not s.note_holds("Damage of up to $15B.", {"what": f"Damage of up to {_told}."}), _told
for _wrote, _told in (("It closed for 10 minutes.", "It closed for 10m."), ("Three B-52s flew.", "3 B-52 bombers flew."), ("A 200 metre channel.", "A 200m channel.")):
    assert s.note_holds(_wrote, {"what": _told}), "a bare m or b is no scale: " + _told
_ships = "Ships crossed in the third week. A ship was hit."
for _fine in ("In the second half of the year a ship was hit.", "A third ship was hit.", "Third parties watch.", "It may reach the third quarter."):
    assert s.note_holds(_ships, {"what": _fine}), _fine
for _wrong in ("About a quarter of ships crossed.", "One-tenth of ships crossed."):
    assert not s.note_holds(_ships, {"what": _wrong}), _wrong
_cased = "Trump says shipping could halt. Tehran claims mine hits and Hormuz traffic collapses. President Trump spoke."
for _head in ("President Trump Warns Shipping Could Halt", "Hormuz Traffic Collapses As Tehran Claims Mine Hits"):
    assert s.note_holds(_cased, {"head": _head, "what": "Shipping could halt."}), _head
assert s.note_holds("Guards and Houthis say mines hit.", {"what": "One Guard source says so, as does the Houthi side."}), "a singular is the note's plural"
assert not s.note_holds("Thin reports [thr:caf9264cde] on freight.", {"what": "Only 9,264 ships moved."}), "an id isn't a figure, with a prefix or without"
for _wrong in ("Ten ships were hit.", "Eight ships were hit.", "Only 40 ships moved."):
    assert not s.note_holds("Tensions rise over freight [ec48178dcddf1cbc87a3f2396b881a16].", {"what": _wrong}), _wrong
assert s.market_words("Lithium & Battery Tech (LIT)") == ["lithium", "battery", "tech"] and s.market_words("EUR / USD") == ["eur", "usd"], "a lone mark matches nothing"
assert s.market_words("US Natural Gas (Henry Hub)") == ["natural gas"] and s.market_words("S&P 500") == ["s&p"] and s.market_words("The US") == ["the us"]
_real_spend, _real_find, _charged = s.spend_ai, s.spend_find, []
def _spent():
    raise OverflowError("daily limit")
s.spend_ai, s.spend_find = _spent, lambda kind: _charged.append(kind)
_day_over = {**_small, "headline": "A day with nothing left to spend"}
for _ in range(3):
    try:
        s.note_reading(_day_over)
    except OverflowError:
        pass
assert not _charged, "a spent day doesn't use up the notes' own allowance, page after page"
assert s.find_kept("noteless", s.note_said(_day_over)), "and it waits its hour"
s.spend_ai, s.spend_find = _real_spend, _real_find
s.ai.ask = lambda system, text, **k: "HEAD: \nWHAT: Some ships wait.\nWHY: Oil.\nWATCH: Traffic."
assert s.note_reading({**_small, "headline": "A fifth"}) is None, "an empty part is no part"
s.ai.ask = lambda system, text, **k: "**HEAD: Ships are held**\nWHAT: Some ships wait.\nWHY: Oil.\nWATCH: Traffic."
assert s.note_reading({**_small, "headline": "A sixth"})["head"] == "Ships are held", "and stars round a line aren't kept"

# an hour on, a note that failed is tried again rather than waiting for the server to restart
_retry = {**_note, "headline": "Failed once"}
s.ai.ask = lambda system, text, **k: "No."
_key = s.with_reading([{**_retry}])[0]["telling"]
assert s.TELLING[_key].result(timeout=5) is None
with s.db() as _c:
    _c.execute("DELETE FROM finds WHERE kind = 'noteless'")
s.ai.ask = lambda system, text, **k: "HEAD: Ships held\nWHAT: Some ships wait.\nWHY: Oil.\nWATCH: Traffic."
s.with_reading([{**_retry}])
assert s.TELLING[_key].result(timeout=5)["head"] == "Ships held"
s.ai.ready = lambda: False
assert s.note_reading({**_note, "headline": "Third"}) is None, "no AI, and the page stands"
s.ai.ask, s.ai.ready = _real_ask, _real_ready


# the map's zoom: a shape for every state, every seat a race can name, and each race says how it prints
import json as _json
_shapes = {f.stem: _json.loads(f.read_text()) for f in (Path(__file__).parent.parent / "web" / "us").glob("*.json")}
assert len(_shapes) == 51 and sum(len(v["seats"]) for v in _shapes.values()) == 435, "every state and every seat"
assert all(k.startswith("H-") and (k.endswith("-AL") or k[-2:].isdigit()) for v in _shapes.values() for k in (q["k"] for q in v["seats"]))
assert _shapes["GA"]["seats"][4]["k"] == "H-GA-05" and any(c["n"] == "Fulton" and "H-GA-05" in c["k"] for c in _shapes["GA"]["cos"]), "a district knows its counties"
assert any(t[2] == "Atlanta" for t in _shapes["GA"]["towns"]) and not any("CDP" in t[2] for t in _shapes["GA"]["towns"])
assert "ink" in elect.row(elect.race(_race("H-GA-05", "house"))), "the map draws each seat from its row"

# a statewide race county by county, keyed by name as the paper's own county shapes are
assert s.county_name("St. Louis County") == s.county_name("Saint Louis") == "stlouis" and s.county_name("DeKalb") == "dekalb"
assert s.county_name("Fairfax") != s.county_name("Fairfax City"), "a county and the city of the same name are two places"
_real_war = s.war_open
s.war_open = lambda path, timeout=30: {"fetched": 7, "counties": {"13089": {"name": "DeKalb", "reporting": 61, "candidates": [{"name": "Jon Ossoff", "party": "Democratic", "votes": 900, "percent": 81.2}, {"name": "Mike Collins", "party": "Republican", "votes": 200, "percent": 18.8}]}, "x": {"name": "", "candidates": []}}}
_cos = s.d_counties("S-GA")
assert _cos["fetched"] == 7 and list(_cos["rows"]) == ["dekalb"] and _cos["rows"]["dekalb"]["c"][0]["pct"] == 81.2 and _cos["rows"]["dekalb"]["fips"] == "13089", _cos
s.war_open = _real_war
