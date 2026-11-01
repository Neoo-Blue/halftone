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
s.fetch = lambda url, **k: _fetched.append(url) or {}
for _base in ("https://war.example/api", "https://war.example/api/", "https://war.example/api/v1"):
    settings.update({"WARROOM_URL": _base})
    s.war_open("/elections")
assert set(_fetched) == {"https://war.example/api/v1/elections"}, _fetched
s.fetch = _real_fetch
settings.update({"WARROOM_URL": ""})


# an analyst's note, told by an editor: once for each note, and a reply that isn't the shape leaves the analyst's words
_note = {"headline": "Hormuz composite risk falls to 0.55", "body": "Risk fell. <script>x</script>", "bullets": ["OBSERVED: AIS transits 12", {"text": "UNVERIFIED: a story"}], "ts": 1}
_asks, _real_ask, _real_ready = [], s.ai.ask, s.ai.ready
s.ai.ready = lambda: True
s.ai.ask = lambda system, text, **k: _asks.append((system, text)) or "HEAD: Ships still aren't coming back\nWHAT: About 12 a day cross.\n**WHY:** Oil.\nWATCH: Traffic."
_read = s.note_reading(_note)
assert _read == {"head": "Ships still aren't coming back", "what": "About 12 a day cross.", "why": "Oil.", "watch": "Traffic."}, _read
assert "<script" not in _asks[0][1] and _asks[0][1].startswith("<note>") and "AIS transits 12" in _asks[0][1] and "a story" in _asks[0][1], "strangers' text can't close the tag it's held in"
assert s.note_reading(_note) == _read and len(_asks) == 1, "each note is told once"
s.ai.ask = lambda system, text, **k: "Sorry, I can't."
assert s.note_reading({**_note, "headline": "Another"}) is None, "a reply that isn't the shape leaves the analyst's words"
_with = s.with_reading([{**_note}, {**_note, "headline": "Older"}])
assert _with[0]["reading"] == _read and "reading" not in _with[1], "the first note on a page is the one told"
assert s.with_reading([]) == []
s.ai.ready = lambda: False
assert s.note_reading({**_note, "headline": "Third"}) is None, "no AI, and the page stands"
s.ai.ask, s.ai.ready = _real_ask, _real_ready
