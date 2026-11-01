"""python3 tests/test_paper.py: the logic that can quietly lie (money, sanitizing, what counts as down)."""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "paper"))
os.environ["PAPER_DATA"] = tmp = tempfile.mkdtemp(prefix="paper-test")
os.environ.pop("PAPER_AUTH", None)
os.environ["PAPER_PORT"] = "tcp://10.43.13.10:8095"  # what Kubernetes sets for a Service named paper
os.environ.pop("PAPER_PASSWORD", None)
import server as s  # noqa: E402
import settings  # noqa: E402

settings.update({"PAPER_TZ": "America/Los_Angeles", "BRIEF_URL": "https://brief.example", "PRODUCTS": [{"key": "shop", "name": "Shop", "host": "shop.example"}, {"key": "club", "name": "Club", "host": "club.example"}, {"key": "guide", "name": "Guide", "host": "guide.example"}],
                 "EARLIER": [{"label": "First invoice", "day": "2026-07-16", "amount": "268.20"}], "MAILBOXES": [{"address": "owner@shop.example", "label": "Owner"}, {"address": "hello@shop.example", "label": "Shop"}]})

assert s.PORT == 8095, "a Kubernetes service address must not stop the paper"
NOW = 1793468000
day = lambda ago: f"2026-10-{31 - ago:02d}"
sale = lambda ago, cents, site="shop", renewal=0: {"site": site, "item": "x", "cents": cents, "renewal": renewal, "created": NOW - ago * 86400, "day": day(ago), "country": "US", "city": None, "region": None}
feed = {
    "now": NOW, "older": {"cents": 1000, "orders": 1}, "subs": [{"site": "club", "status": "active", "monthly": 1999}, {"site": "club", "status": "trialing", "monthly": 1999}],
    "sales": [sale(1, 1900), sale(2, 1999, "club", 1), sale(20, 500, "guide")], "refunds": [{"site": "shop", "cents": 1900, "created": NOW - 86400, "day": day(1)}],
    "spend": [{"day": day(3), "site": "*", "channel": "ai", "cents": 967}], "visitors": [{"site": "shop", "day": day(1), "n": 40}, {"site": "nothing", "day": day(1), "n": 9}], "abandoned": [{"site": "shop", "created": NOW - 86400}, {"site": "shop", "created": NOW - 2 * 86400}, {"site": "shop", "created": NOW - 3 * 86400}, {"site": "shop", "created": NOW - 20 * 86400}],
}
costs = [{"name": "Hosting", "cents": 3000, "per": "month"}, {"name": "Domains", "cents": 36500, "per": "year"}, {"name": "Email", "cents": None, "per": "month"}]

r = s.money_report(feed, costs, 7)
assert r["gross"] == 3899 and r["refunds"] == 1900 and r["orders"] == 1, r
assert r["fees"] == s.fee(1900) + s.fee(1999)
assert r["missing"] == ["Email"], "a blank cost is named, never counted as zero"
assert [k["cents"] for k in r["known"]] == [690, 700], r["known"]  # 7 days of $30 a month and $365 a year
assert r["result"] == 3899 - 1900 - r["fees"] - 967 - 690 - 700
assert r["mrr"] == 1999 and r["subs"] == 1, "a trial is not recurring revenue"
assert r["visitors"] == 40 and r["abandoned"] == 3 and len(r["daily"]) == 7
assert "nothing" not in [p["site"] for p in r["products"]], "a site that sells nothing is not a product"
assert r["lifetime"]["cents"] == 26820 + 1000 + 1900 + 1999 + 500 - 1900, "refunds come off lifetime income"
m30 = s.money_report(feed, costs, 30)
assert m30["gross"] == 4399 and m30["abandoned"] == 4, "the checkout count follows the chosen period"
assert sum(d["cents"] for d in m30["daily"]) == m30["gross"] and len(m30["daily"]) == 30, "the chart and the ledger use one calendar"
late = {**feed, "now": 1793512800, "sales": [sale(0, 1900), sale(6, 5000)]}  # 18:00 Pacific, when UTC has already rolled over
lr = s.money_report(late, costs, 7)
assert sum(d["cents"] for d in lr["daily"]) == lr["gross"] == 6900 and lr["daily"][-1]["day"] == day(0), lr["daily"]

article = """<article><p>before any heading</p><h2 id="x">The Signal</h2><p class="dek">AI news.</p>
<p><strong>Big thing happened.</strong> Why it matters: <a href="https://e.com/a" onclick="evil()">link</a> and
<a href="javascript:alert(1)">bad</a> <img src=x onerror=evil()></p><script>evil()</script>
<div class="cta cta-mid"><p>Subscribe!</p><a href="/#newsletter">Subscribe</a></div>
<h2>Trending</h2><ul><li>a &lt;b&gt; repo</li></ul></article>"""
page = f'<title>Brief: Oct 31 | Owner</title><meta name="description" content="A &amp; B">{article}'
i = s.parse_issue(page, "brief-2026-10-31")
assert [x["title"] for x in i["sections"]] == ["The Signal", "Trending"], i
body = i["sections"][0]["html"]
for bad in ("evil", "onclick", "javascript:", "<img", "Subscribe", "newsletter"):
    assert bad not in body, (bad, body)
assert '<a href="/read?u=https%3A%2F%2Fe.com%2Fa">link</a>' in body and "<a>bad</a>" in body, body
assert s.inside("https://brief.example/n/brief-2026-10-30") == "/issue/brief-2026-10-30", "an issue link stays an issue"
unclosed = s.parse_issue('<title>T</title><article><h2>One</h2><div class="cta"><p>Sign up<source src=x></div><h2>Two</h2><p>Kept</p></article>', "x")
assert [x["title"] for x in unclosed["sections"]] == ["Two"], "a broken subscribe box can't swallow the sections after it"
assert s.parse_issue('<title>T</title><article><h2>The Signal</h2><p><strong>AT&amp;T wins.</strong> Yes</p></article>', "y")["headline"] == "AT&T wins"
assert i["headline"] == "Big thing happened" and i["deck"] == "A & B" and i["title"] == "Brief: Oct 31"
assert "a &lt;b&gt; repo" in i["sections"][1]["html"]

thin = s.every_nth(list(range(1440)))
assert thin[-1] == 1439 and thin[0] < 15 and len(thin) <= 97, "the chart spans the whole day and ends on the newest reading"
assert s.every_nth([1, 2, 3]) == [1, 2, 3]
assert s.first_block("Hormuz is steady. **Cross-domain.** Brent falls.") == "Hormuz is steady." and s.first_block(None) == ""
assert s.gated("https://team.cloudflareaccess.com/cdn-cgi/access/login/x") and not s.gated("https://x.example/login") and not s.gated(None)
assert s.answers(200) and s.answers(302) and s.answers(403) and not s.answers(502) and not s.answers(530) and not s.answers(None)

host = dict(name="NAS", ok=True, disk_used=90, disk_total=100, mem_used=1, mem_total=10, load=[0.1, 0, 0], cores=4, raid_degraded=1, failed_units=["anydesk"])
w = s.worries({"hosts": [host], "guests": [{"id": 7, "name": "club", "status": "stopped"}, {"id": 8, "name": "old", "status": "stopped"}]},
              [{"name": "Shop", "up": False}, {"name": "Plex", "up": True}], {"autostart": [7], "pools": [], "disks": [], "backups": [{"at": NOW - 3 * 86400, "ok": True, "status": "OK"}]}, NOW)
texts = [t for _, t in w]
assert w[0][0] == 2 and "Shop is not answering" in texts and "NAS disk is 90% full" in texts and "NAS RAID is degraded" in texts
assert "Container club should be running" in texts and not any("Container old" in t for t in texts), "a stopped container that never autostarts is not a worry"
assert s.worries({"hosts": [dict(host, disk_used=10, raid_degraded=0, failed_units=[], fullest={"mount": "/", "pct": 95})], "guests": []}, [], None, NOW)[0] == (2, "NAS volume / is 95% full"), "a small full volume still counts"
assert s.worries(None, None, {"pools": [{"name": "rpool", "health": "ONLINE", "size": 100, "alloc": 90}], "backups": [{"at": NOW, "ok": True, "status": "OK"}]}, NOW) == [(1, "ZFS pool rpool is 90% full")]
assert "Newest backup is 3 days old" in texts and (0, "NAS: anydesk failed") in w
assert s.worries(None, None, {"backups": [{"at": NOW, "ok": False, "status": "disk full"}]}, NOW)[0] == (2, "Last backup run failed: disk full")
assert s.issue_index('<a href="/n/brief-x"><p>Issue #2 &middot; Oct 31</p><h3>Brief: Oct 31</h3><p>Deck</p></a><a href="/n/brief-x">newer</a>')[0]["title"] == "Brief: Oct 31"

s.init_db()
s.save("probes", [])
s.save("machines", [])
with s.db() as c:
    c.execute("UPDATE snap SET as_of = 1000 WHERE name = 'probes'")
    c.execute("DELETE FROM snap WHERE name = 'storage'")
    c.execute("INSERT INTO snap (name, error, tried) VALUES ('storage', 'boom', 1)")
settings.update({"PROBES": [{"group": "g", "name": "n", "url": "http://x.example/"}], "PVE_URL": "https://10.0.0.2:8006/api2/json", "PVE_TOKEN": "t"})
stale = s.stale_worries(4000)
assert (2, "Service checks are 50 minutes old") in stale and (1, "Storage checks have never reported") in stale and not any("Machine" in t for _, t in stale), stale
settings.update({"PROBES": [], "PVE_URL": "", "PVE_TOKEN": None})
assert s.stale_worries(4000) == [], "a section that is off can't be stale"

for good in ({"rows": []}, {"rows": [{"name": "x", "cents": 5, "per": "year"}, {"name": "y", "cents": None, "per": "month"}]}):
    s.clean_costs(good)
for bad in ({}, {"rows": "x"}, {"rows": [{"name": "", "cents": 1, "per": "month"}]}, {"rows": [{"name": "x", "cents": -1, "per": "month"}]},
            {"rows": [{"name": "x", "cents": 1.5, "per": "month"}]}, {"rows": [{"name": "x", "cents": True, "per": "month"}]}, {"rows": [{"name": "x", "cents": 1, "per": "week"}]}, {"rows": [1]}, {"rows": [{"name": 5, "cents": 1, "per": "month"}]}):
    try:
        s.clean_costs(bad)
    except ValueError:
        continue
    raise AssertionError(bad)

assert s.plex_image("/library/metadata/12/thumb/34") and not s.plex_image("/photo/../etc/passwd") and not s.plex_image("/library/metadata/12/thumb/34?x=1")
assert s.image_source("sonarr", "", "12") and not s.image_source("sonarr", "", "../x") and not s.image_source("nope", "", "1")
# the reader's trust boundary: only public web pages, whatever a link claims
for bad in ("http://127.0.0.1/", "http://localhost/", "http://169.254.169.254/latest/", "http://192.168.1.2:8006/", "http://10.0.0.1/", "http://[::1]/", "file:///etc/passwd",
            "ftp://1.1.1.1/", "https://user:pw@1.1.1.1/", "https://1.1.1.1:8006/", "http://100.64.0.1/", ""):
    try:
        s.public_url(bad)
    except (ValueError, OSError):
        continue
    raise AssertionError(bad)
assert s.public_url("https://1.1.1.1/x") == "https://1.1.1.1/x"

news_page = """<html><head><title>Fallback</title><meta property="og:title" content="Real &amp; true"><meta property="og:site_name" content="The Daily">
<meta property="og:image" content="/pic.jpg"><meta name="author" content="A Writer"><meta property="article:published_time" content="2026-10-31T10:00:00Z"></head>
<body><nav><p>Home and every section of this very long navigation menu that must not appear</p></nav><article><h1>Real</h1>
<p>The first paragraph of this story is long enough to count as real writing, and it has <a href="/next">a link</a> in it.</p>
<div class="newsletter-box"><p>Sign up to our newsletter today, it really is the best thing you will read all week long.</p></div>
<script>evil()</script><figure><p>A caption that should stay out of the story text, however long it happens to be.</p></figure>
<p>The second paragraph adds more words so that the story passes the sixty word floor, because a page with a few lines is a paywall teaser and not an article anyone can read properly at all, and the reader says so instead.</p>
<ul><li>One bullet</li></ul><p onclick="evil()"><script>x</script>A third paragraph, with <strong>bold</strong> text, carries on for long enough to be kept by the filter.</p></article>
<footer><p>Copyright notice that is long enough to look like a paragraph to a careless reader of this page.</p></footer></body></html>"""
st = s.extract(news_page, "https://paper.example/story")
assert st["title"] == "Real & true" and st["site"] == "The Daily" and st["image"] == "https://paper.example/pic.jpg" and st["author"] == "A Writer" and st["published"] > 0, st
for bad in ("navigation", "newsletter", "caption", "Copyright", "evil", "onclick", "<script", "<nav"):
    assert bad not in st["body"], (bad, st["body"])
assert 'href="/read?u=https%3A%2F%2Fpaper.example%2Fnext"' in st["body"] and "<ul><li>One bullet</li></ul>" in st["body"] and "<strong>bold</strong>" in st["body"], st["body"]
thin = s.extract("<html><body><article><p>Subscribe to keep reading this story right now.</p></article></body></html>", "https://x.example/a")
assert thin["body"] == "", "a teaser is not a story"
ld = s.extract('<html><head><script type="application/ld+json">{"@graph":[{"articleBody":"' + "word " * 80 + '"}]}</script></head><body><div id="root"></div></body></html>', "https://x.example/b")
assert ld["body"].startswith("<p>word") and ld["words"] == 80, "a script-built page can still be read"

rss = b"""<rss xmlns:media="http://search.yahoo.com/mrss/"><channel><item><title>A &amp; B</title><link>https://a.example/1</link><pubDate>Sat, 31 Oct 2026 10:00:00 GMT</pubDate>
<description>&lt;p&gt;Summary here&lt;/p&gt;</description><media:thumbnail url="https://a.example/1.jpg"/></item></channel></rss>"""
atom = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Atom one</title><link rel="alternate" href="https://b.example/2"/><published>2026-10-31T10:00:00Z</published><summary>Hi</summary></entry></feed>"""
r1, a1 = s.parse_feed(rss, "world", "BBC")[0], s.parse_feed(atom, "ai", "Verge")[0]
assert (r1["t"], r1["u"], r1["sum"], r1["img"]) == ("A & B", "https://a.example/1", "Summary here", "https://a.example/1.jpg") and r1["ts"] > 0, r1
assert (a1["t"], a1["u"]) == ("Atom one", "https://b.example/2") and a1["ts"] > 0, a1

ev = lambda t, **k: {"id": "a", "title": t, "ts": 5, "domain": "kinetic", "severity": 0.5, **k}
got = s.curated([ev("Real headline here"), ev("Real headline here"), ev("Machine", title_source="generated"), ev("Twist Ties From China", source="federal_register"), ev("Israeli vs Hamas code"), ev("Hidden", screened_out=True), ev("Главное за сегодня, 31 октября")])
assert [g["t"] for g in got] == ["Real headline here"], got

assert s.alert_line("Escalating: Ukraine / Russia at 69, up from 54 over the past week", 46) == "Ukraine / Russia reached 69, up from 54. Now 46."
assert s.alert_line("New conflict watched: Mali", 40) == "New conflict watched: Mali" and s.alert_line("Escalating: Mali at 9, up from 2 over the past week", None) == "Mali reached 9, up from 2."
assert s.short_title("\U0001f1f7\U0001f1fa Russian Air Force, : four bombs") == "Russian Air Force: four bombs" and s.outlet_of("https://t.me/x/1") == "Telegram"
assert s.short_title("▪️ Main news today. Second sentence goes on and on.") == "Main news today." and len(s.short_title("word " * 80)) <= 153
two = s.curated([ev("At least four Palestinians killed in Gaza strike"), ev("At least four Palestinians killed by Israeli fire")])
assert len(two) == 1 and s.outlet_of("https://www.bbc.com/a") == "bbc.com" and s.outlet_of(None) == "WARROOM"
assert s.bare_title("Big news | TechCrunch", "TechCrunch") == "Big news" and s.bare_title("War - and peace", "bbc.com") == "War - and peace"
assert s.extract('<html><head><meta name="author" content="https://www.facebook.com/bbcnews"></head><body></body></html>', "https://x.example/c")["author"] is None

mk = lambda subject, addr="a@b.co", preview="", junk=0: {"id": "x" * 24, "box": "owner@shop.example", "subject": subject, "addr": addr, "sender": "A", "preview": preview, "junk": junk}
assert s.rule_verdict(mk("Automatic reply: away"))[0] == "noise" and s.rule_verdict(mk("Hi", "MAILER-DAEMON@x.com"))[0] == "noise" and s.rule_verdict(mk("Report Domain: shop.example"))[0] == "noise"
assert s.rule_verdict(mk("Your payment failed"))[:2] == ("money", 1) and s.rule_verdict(mk("Dispute opened on charge"))[:2] == ("money", 1)
assert s.rule_verdict(mk("Unusual sign-in activity"))[:2] == ("security", 1) and s.rule_verdict(mk("DMCA takedown notice"))[:2] == ("legal", 1)
assert s.rule_verdict(mk("Your payment failed", junk=1)) is None, "spam is never raised by a rule, phishing is written to match"
assert s.rule_verdict(mk("Love the site, one question")) is None
assert s.rule_verdict(mk("Your Saturday digest", preview="2 tasks overdue")) is None, "a word in the preview says nothing about what the mail is"
batch = [mk("x")]
good = s.clean_verdicts(json.dumps({"items": [{"id": "x" * 24, "category": "customer", "important": True, "why": "A buyer <b>asks</b>."}]}), batch)
assert good["x" * 24][:2] == ("customer", 1) and "<b>" not in good["x" * 24][2]
assert s.clean_verdicts(json.dumps({"items": [{"id": "y" * 24, "category": "customer", "important": True, "why": ""}]}), batch) == {}, "an id the model invented is dropped"
assert s.clean_verdicts(json.dumps({"items": [{"id": "x" * 24, "category": "wire money now", "important": True, "why": ""}]}), batch) == {}
assert s.clean_verdicts(json.dumps({"items": [{"id": "x" * 24, "category": "other", "important": True, "why": ""}]}), batch)["x" * 24][1] == 0, "only the four alert kinds can be important"
row = s.message_row("hello@shop.example", {"id": "g1", "internetMessageId": "<1@x>", "from": {"emailAddress": {"name": "Ann", "address": "ann@x.co"}}, "subject": "Hi <b>there</b>", "bodyPreview": "Hello", "receivedDateTime": "2026-10-31T10:00:00Z", "isRead": False, "parentFolderId": "junk"}, "junk", {"sent"})
assert row["junk"] == 1 and row["unread"] == 1 and row["received"] > 0 and row["subject"] == "Hi there"
assert s.message_row("hello@shop.example", {"id": "g2", "from": {"emailAddress": {"address": "hello@shop.example"}}, "parentFolderId": "in"}, "junk", {"sent"}) is None, "our own sends are not incoming"
assert s.message_row("hello@shop.example", {"id": "g3", "from": {"emailAddress": {"address": "a@b.co"}}, "parentFolderId": "sent"}, "junk", {"sent"}) is None
with s.db() as c:
    c.execute("INSERT INTO mail (id, box, gid, sender, addr, subject, preview, received, unread, junk, triaged, cat, important) VALUES ('a', 'owner@shop.example', 'g', 'A', 'a@b', 'Need', '', ?, 1, 0, 1, 'customer', 1)", (int(__import__('time').time()),))
    c.execute("INSERT INTO mail (id, box, gid, sender, addr, subject, preview, received, unread, junk, triaged) VALUES ('b', 'owner@shop.example', 'g2', 'B', 'b@b', 'Waiting', '', ?, 1, 0, 0)", (int(__import__('time').time()),))
dg = s.mail_digest()
assert [m["id"] for m in dg["need"]] == ["a"] and [m["id"] for m in dg["unsorted"]] == ["b"], "unsorted mail is shown, never hidden"
assert s.set_mail_done("a", True) == 1 and s.mail_digest()["need"] == []

item = lambda t, src, ts=NOW, desk="world", u=None: {"t": t, "u": u or f"https://{src}.example/{abs(hash(t))}", "src": src, "ts": ts, "sum": "", "img": None, "desk": desk}
assert s.same_story(s.words("Ukraine strikes Russian oil refinery near Volgograd"), s.words("Russian oil refinery near Volgograd hit by Ukraine drones"))
assert not s.same_story(s.words("Apple reports record iPhone sales"), s.words("Apple Music adds new lossless tier"))
merged = s.cluster([item("Ukraine strikes Russian oil refinery near Volgograd", "bbc"), item("Russian oil refinery near Volgograd hit by Ukraine", "nyt", NOW - 600, "us"), item("Apple reports record iPhone sales", "bbc", NOW - 100, "business")])
assert len(merged) == 2 and [len(c["outlets"]) for c in sorted(merged, key=lambda c: c["t"])] == [1, 2], merged
big = next(c for c in merged if len(c["outlets"]) == 2)
assert sorted(big["desks"]) == ["us", "world"] and big["first"] == NOW - 600 and "w" not in big
assert len(s.cluster([item("Same headline word for word", "nyt"), item("Same headline word for word", "nyt", NOW - 5, "us")])[0]["outlets"]) == 1, "one outlet's two desks are one outlet"
assert s.opening("<p>A judge ruled today.</p><p>Second part.</p>", "A judge ruled today.") == "<p>Second part.</p>", "the deck isn't printed twice"
assert s.NOT_NEWS.search("Here's the latest.") and not s.NOT_NEWS.search("Here's the latest on the Binance hack")
wide = {"outlets": [1, 2, 3, 4], "ts": NOW - 7200}
assert s.heat(wide, NOW) > s.heat({"outlets": [1], "ts": NOW}, NOW), "six outlets beat one fresh post"
assert s.heat({"outlets": [1], "ts": NOW}, NOW) > s.heat({"outlets": [1], "ts": NOW - 86400}, NOW)
view = s.news_view({"lead": None, "tops": [], "stories": [{"u": "x", "t": "T", "ts": 1, "src": "A", "outlets": [{}, {}], "desks": ["ai"], "sum": "long"}], "feeds": 1})
assert view["wire"] == [{"u": "x", "t": "T", "ts": 1, "src": "A", "n": 2, "desks": ["ai"]}] and "stories" not in view

for kind, ident in (("mail", "../x"), ("nope", "1"), ("event", "../../etc"), ("plex", "1/../2"), ("theater", "A B"), ("product", "st ripe"), ("container", "1; rm")):
    try:
        s.detail(kind, ident)
    except KeyError:
        continue
    raise AssertionError((kind, ident))
for kind, ident in (("product", "stripe"), ("service", "nope")):  # well formed, and nothing is called that
    try:
        s.detail(kind, ident)
    except (KeyError, StopIteration):
        continue
    raise AssertionError((kind, ident))

tries = []


def page_for(url):
    tries.append(url)
    if "paywall" in url:
        raise OSError("403")
    return {"image": "https://open.example/p.jpg", "deck": "A deck", "body": "<p>Real words from the open outlet.</p>" if "open" in url else ""}


real_read, s.read_page = s.read_page, page_for
shut = {"u": "https://paywall.example/a", "src": "Paywall", "sum": "", "img": None, "outlets": [{"src": "Paywall", "u": "https://paywall.example/a"}, {"src": "Empty", "u": "https://empty.example/a"}, {"src": "Open", "u": "https://open.example/a"}, {"src": "Later", "u": "https://open.example/b"}]}
got = s.enrich(shut)
assert got["text"] == "<p>Real words from the open outlet.</p>" and got["via"]["src"] == "Open" and got["img"], "a refused publisher must not leave the front page blank, and the text names its outlet"
assert len(tries) == 3, "it stops at the first outlet with words"
s.enrich(shut)
assert len(tries) == 3, "one pass per story, however often the desk refreshes"
none = s.enrich({"u": "https://paywall.example/b", "src": "Paywall", "sum": "", "img": None, "outlets": [{"src": "Paywall", "u": "https://paywall.example/b"}]})
assert none["text"] == "" and none["via"] is None
s.read_page = real_read

# every kind of hazard comes from whoever published it, and strangers' addresses aren't followed
for url in ("http://169.254.169.254/x", "https://gdacs.org.evil.example/x", "https://www.gdacs.org.evil.example/x", "file:///etc/passwd"):
    try:
        s.open_json(url, s.GDACS)
    except ValueError:
        continue
    raise AssertionError(url)
assert [s.area_level(n) for n in ("Poly_Green", "Poly_Orange", "Poly_Red", "Poly_Cones", "Poly_Circle", "Point_Centroid", "Poly_SMPInt_4", "Poly_SMPInt_6", "Poly_SMPInt_9", "Poly_Other")] == [1, 2, 3, 0, None, None, 1, 2, 3, 2]
assert len(s.thin_ring([[i, i] for i in range(1000)])) <= 125 and s.rings_of({"type": "Point", "coordinates": [1, 2]}) == []
assert len(s.rings_of({"type": "MultiPolygon", "coordinates": [[[[1, 2], [3, 4]]], [[[5, 6], [7, 8]]]]})) == 2
real_open = s.open_json
s.open_json = lambda url, *a: {"channel": {"item": [
    {"latitude": "16", "longitude": "89.1", "wind_speed": "18", "storm_status": ["Storm", "Storm"], "advisory_datetime": "27 Oct 2026 06:00", "actual": "True", "windrad39km": "120", "pop39": "5", "pop74": "0", "popstormsurge": ""},
    {"latitude": "21", "longitude": "81", "wind_speed": "12", "storm_status": "Depression", "advisory_datetime": "26 Oct 2026 06:00", "actual": "False"}]}}
t = s.cyclone("x")
assert [p["la"] for p in t] == [21, 16] and t[1]["v"] == 65 and t[1]["label"] == "Storm" and t[0]["fc"] and not t[1]["fc"] and t[1]["gale"] == 5 and t[1]["r"] == 120, t
s.open_json = lambda *a: (_ for _ in ()).throw(OSError("down"))
assert s.hazard_depth("gdacs:TC:1")["track"] == [], "a source that doesn't answer leaves the page standing"
s.open_json = real_open
for hostile in ("gdacs:TC:1/../../x", "gdacs:T C:1", "eonet:../../x", "other:1"):
    assert s.hazard_depth(hostile)["track"] == [], hostile
assert s.number("") == 0.0 and s.number(None) == 0.0 and s.number("2.5") == 2.5
exec(open(Path(__file__).with_name("test_settings.py")).read())
exec(open(Path(__file__).with_name("test_ai.py")).read())
exec(open(Path(__file__).with_name("test_desks.py")).read())
exec(open(Path(__file__).with_name("test_usage.py")).read())
print("all good")
