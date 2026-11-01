# Run from test_paper.py: moving sections by hand, and the page learning from what you read.
default = list(s.DESK_IDS)
assert s.layout_view()["order"] == {"wide": default, "phone": default} and s.layout_view()["moved"] == {"wide": None, "phone": None} and s.layout_view()["learn"] is False and s.layout_view()["chart"] == "dots", s.layout_view()
for bad in ({"form": "wide", "order": default[:-1]}, {"form": "wide", "order": default + ["world"]}, {"form": "wide", "order": default[:-1] + ["<b>"]}, {"form": "wide", "order": "world"}, {"form": "wide", "order": [1] * 8}, {"form": "fridge", "order": default}, {"order": default}, {"seen": True}, ["x"], {"chart": "rainbow"}):
    assert refuses(s.set_layout, bad), bad
mine = default[::-1]
assert s.set_layout({"form": "phone", "order": mine})["order"] == {"wide": default, "phone": mine}, "each screen keeps its own order"
s.set_layout({"form": "phone", "order": default})
assert s.set_layout({"chart": "area"})["chart"] == "area" and settings.get("CHART_STYLE") == "area"

for bad in ({"form": "wide", "seconds": {"world": 121}}, {"form": "wide", "seconds": {"world": 80, "tech": 80}}, {"form": "wide", "seconds": {"attic": 5}}, {"form": "wide", "seconds": {"world": -5}}, {"form": "wide", "seconds": {"world": 1.5}}, {"form": "wide", "seconds": {"world": True}}, {"form": "wide", "seconds": ["world"]}, {"form": "tv", "seconds": {"world": 5}}, {"seconds": {"world": 5}}, [], "x", None):
    assert refuses(s.record_views, bad), bad
s.record_views({"form": "wide", "seconds": {"systems": 60}})
with s.db() as c:
    assert c.execute("SELECT COUNT(*) FROM view_time").fetchone()[0] == 0, "with learning off, nothing about your reading is kept"


def read(form, **seconds):
    """Reads in the two-minute reports the page sends."""
    left = dict(seconds)
    while any(left.values()):
        chunk = {}
        for desk, v in left.items():
            take = min(v, 120 - sum(chunk.values()))
            if take > 0:
                chunk[desk] = take
                left[desk] = v - take
        s.record_views({"form": form, "seconds": chunk})


s.remember("layout:wide", ["gone", "tech", "world"])
fixed = s.layout_view()["order"]["wide"]
assert sorted(fixed) == sorted(default) and fixed[:2] == ["tech", "world"], "an order saved before a section came or went stays valid"
s.set_layout({"form": "wide", "order": default})
settings.update({"LEARN_LAYOUT": True})
assert s.layout_view()["learn"] is True
read("wide", systems=3000, business=2000, front=1000)
assert s.layout_view()["order"]["wide"] == default, "under two hours nothing moves"
read("wide", systems=1200)
learned = s.layout_view()
assert learned["order"]["wide"][:2] == ["systems", "business"] and learned["order"]["phone"] == default, learned["order"]
assert sorted(learned["order"]["wide"]) == sorted(default), "every section is still there"
assert learned["moved"]["wide"]["from"] == default and learned["moved"]["wide"]["to"] == learned["order"]["wide"], "and the page can say what moved, and undo it"
with s.db() as c:
    assert c.execute("SELECT seconds FROM view_time WHERE form = 'wide' AND desk = 'systems'").fetchone()["seconds"] == 2100, "recent habits count for more"
assert s.saved("view_since:wide") == 0, "the next two hours start over"
read("wide", world=3600, tech=3500)
s.set_layout({"form": "wide", "seen": True})
assert s.layout_view()["moved"]["wide"] is None, "Keep clears the note and leaves the order"
now = s.layout_view()["order"]["wide"]
same = now[:]
with s.db() as c:
    c.execute("DELETE FROM view_time")
    c.executemany("INSERT INTO view_time VALUES ('wide', ?, ?)", [(d, 1000 + i) for i, d in enumerate(reversed(same))])
s.learn_layout("wide")
assert s.layout_view()["order"]["wide"] == same and s.layout_view()["moved"]["wide"] is None, "near-equal times don't reshuffle the page"
with s.db() as c:
    c.execute("DELETE FROM view_time")
s.set_layout({"form": "wide", "order": default})
assert s.saved("view_since:wide") is None, "an order you choose starts the learning over"
read("phone", arts=7300)
assert s.layout_view()["order"]["phone"][0] == "arts" and s.layout_view()["order"]["wide"] == default, "a phone learns on its own"
moved = s.layout_view()["moved"]["phone"]
s.set_layout({"form": "phone", "order": moved["from"]})
assert s.layout_view()["order"]["phone"] == default and s.layout_view()["moved"]["phone"] is None, "Undo puts it back"
settings.update({"LEARN_LAYOUT": False, "CHART_STYLE": "dots"})
s.set_layout({"form": "phone", "order": default})
assert s.paper()["layout"]["order"]["wide"] == default

# ---------------------------------------------------------------- the reader keeps the story and drops the site
page = """<html><head><meta property="og:title" content="A real story"><meta property="og:site_name" content="ABC News"><meta name="author" content="ABC News"><meta property="og:description" content="The first thing that happened in this story, told plainly for everybody."></head><body><article>
<p>The first thing that happened in this story, told plainly for everybody.</p>
<p>A second paragraph with enough words in it to count as part of the story itself.</p>
<h3>Recommended Stories</h3><ul><li><a href="/a">Some other headline about something else entirely</a></li><li><a href="/b">Another one nobody asked for</a></li></ul>
<p><a href="/c">'Inexplicable' order probed in a different story altogether</a></p>
<p>Sponsored Content by Taboola</p>
<p>A third paragraph that carries on with the story after the interruption, and it has plenty of words in it to make the body long enough to keep, which the reader wants to do, and it goes on a little while longer still so that the sixty word floor is comfortably passed by the time we reach the end of this sentence right here.</p>
<h2>Most viewed</h2><ul><li>One thing</li><li>Another thing people clicked</li></ul>
</article></body></html>"""
story = s.extract(page, "https://abc.example/x")
assert "Recommended" not in story["body"] and "Inexplicable" not in story["body"] and "Taboola" not in story["body"] and "Most viewed" not in story["body"] and "people clicked" not in story["body"], story["body"]
assert "A second paragraph" in story["body"] and "carries on" in story["body"], "the story itself stays, either side of the interruption"
assert "The first thing" not in story["body"], "the summary isn't repeated as a first line"
assert story["author"] is None, "a site isn't its own byline"

# ---------------------------------------------------------------- saved stories and what you've read
for bad in ({"url": "javascript:alert(1)", "saved": True}, {"url": "https://a", "saved": "yes"}, {"saved": True}, [], {"url": "https://" + "a" * 2000, "saved": True}):
    assert refuses(s.set_saved, bad), bad
s.note_read("https://a.example/1", "One", "A")
s.set_saved({"url": "https://a.example/2", "title": "<b>Two</b>", "site": "B", "saved": True})
got = s.shelf_view()
assert got["read"] == ["https://a.example/1"] and got["saved"][0]["title"] == "Two", got
assert s.paper()["shelf"]["saved"] and s.detail("saved", "")["saved"]
s.note_read("https://a.example/2", "Two", "B")
assert s.shelf_view()["saved"], "reading a saved story keeps it saved"
s.set_saved({"url": "https://a.example/2", "saved": False})
assert not s.shelf_view()["saved"], "and it can be dropped"

# ---------------------------------------------------------------- alerts
posted = []
real_post, real_found = s.post_alert, s.all_worries
s.post_alert = posted.append
s.all_worries = lambda *a, **k: [(2, "NAS is not answering"), (1, "A small thing")]
settings.update({"NOTIFY_URL": "https://ntfy.example/mine"})
with s.db() as c:
    c.execute("DELETE FROM meta WHERE k = 'notified'")
assert s.notify() == {"sent": 0} and not posted, "turning this on isn't a flood"
s.all_worries = lambda *a, **k: [(2, "NAS is not answering"), (2, "Proxmox is not answering")]
assert s.notify() == {"sent": 1} and posted == ["Proxmox is not answering"], "only what's newly serious"
assert s.notify() == {"sent": 0} and len(posted) == 1, "then quiet"
s.all_worries = lambda *a, **k: []
s.notify()
s.all_worries = lambda *a, **k: [(2, "Proxmox is not answering")]
s.notify()
assert len(posted) == 2, "and it speaks up again if it comes back"
s.post_alert, s.all_worries = real_post, real_found
settings.update({"NOTIFY_URL": ""})
s.save("certs", {"shop.example": 3.0, "club.example": 10.0, "fine.example": 60.0})
settings.update({"PROBES": [{"group": "g", "name": "n", "url": "https://shop.example/"}]})
assert sorted(s.cert_worries()) == [(1, "club.example certificate runs out in 10 days"), (2, "shop.example certificate runs out in 3 days")], s.cert_worries()
settings.update({"PROBES": []})
s.save("certs", {})
