# Run from test_paper.py: what AI was used and what it was worth, charged or not.
import usage as u

assert u.worth("claude-opus-5-5", 1e6, 1e6, 1e6, 1e6) == 4 + 20 + .2 + 5, "Opus 5.5 is not priced as Opus 5"
assert u.worth("claude-opus-5", 1e6) == 5 and u.worth("claude-opus-4-8", 1e6) == 5
assert u.worth("anthropic/claude-haiku-5-5", 1e6, 1e6) == .6, "a provider prefix doesn't hide the model"
assert u.worth("claude-haiku-4-5-20251001", 1e6) == 1, "a dated snapshot finds its model, and Haiku 4.5 is not Haiku 5.5"
assert u.worth("claude-sonnet-5-5", 0, 1e6) == 10 and u.worth("claude-fable-5-1", 0, 0, 1e6) == .25
assert u.worth("gemini-3.8-flash", 1e6) is None and u.worth(None, 1e6) is None, "no price is not the same as free"

line = lambda agent, source, model, **k: {"agent": agent, "source": source, "model": model, "tokens_in": 0, "tokens_out": 0, "cache_read": 0, "cache_write": 0, "cost": 0, **k}
today = [line("Claude", "claude-code", "claude-opus-5-5", tokens_out=1e6), line("Claude", "claude-code subagent", "claude-opus-5-5", tokens_out=5e5), line("provider:anthropic", "commons", "anthropic/claude-haiku-5-5", tokens_in=1e6, cost=1.0)]
two_days = [line("Claude", "claude-code", "claude-opus-5-5", tokens_out=3e6), line("Claude", "claude-code subagent", "claude-opus-5-5", tokens_out=5e5), line("provider:anthropic", "commons", "anthropic/claude-haiku-5-5", tokens_in=1e6, cost=1.0), line("antigravity", "antigravity bridge", "default", tokens_in=7e6), line("grok-build", "grok bridge", "grok-4.7-build", tokens_in=9, cost=2.5)]
rows = u.ledger_rows([{"days": ["2026-10-31"], "rows": today}, {"days": ["2026-10-30", "2026-10-31"], "rows": two_days}])
by = {(r["day"], r["who"], r["model"]): r for r in rows}
assert len(rows) == 6 and by[("2026-10-30", "Claude Code", "claude-opus-5-5")]["qty"] == 2e6, "a day is one answer minus the one before it"
assert not any(r["day"] == "2026-10-30" and r["who"] == "Commons" for r in rows), "a model with nothing that day has no row"
api = by[("2026-10-31", "Commons", "claude-haiku-5-5")]
assert api["worth"] == api["charged"] == .1, "the list price wins over a stored guess, and Commons' API calls are real money"
assert by[("2026-10-30", "Claude Code", "claude-opus-5-5")]["charged"] == 0, "a plan covers Claude Code"
assert by[("2026-10-30", "Antigravity", "default")]["worth"] is None and by[("2026-10-30", "Grok Build", "grok-4.7-build")]["worth"] == 2.5, "with no price here, the ledger's own figure is the fallback"
for bad in (float("nan"), float("inf"), -1, 10 ** 400):
    try:
        u.ledger_rows([{"days": ["2026-10-31"], "rows": [line("x", "y", "z", tokens_in=bad)]}])
    except ValueError:
        continue
    raise AssertionError(bad)
for page in ({"days": ["2999-01-01"], "rows": []}, {"days": ['3"><b>PWN'], "rows": []}, {"days": [], "rows": []}, {"days": ["2026-10-30", "2026-10-31"], "rows": []}, {"days": ["2026-10-31"], "rows": [{}] * (u.MAX_ROWS + 1)}):
    try:
        u.ledger_rows([page])
    except (ValueError, IndexError):
        continue
    raise AssertionError(page["days"])
routed = u.ledger_rows([{"days": ["2026-10-31"], "rows": [line("provider:openrouter", "commons", "openai/gpt-x", tokens_in=9, cost=40)]}])[0]
assert routed["who"] == "Commons, openrouter" and routed["charged"] == 40, routed

bill = u.bill_rows([{"starting_at": "2026-10-30T00:00:00Z", "cost": {"amount": "12345.000000", "list_amount": "20000.000000"}, "group": {"model": "claude-haiku-5-5"}}, {"starting_at": "2026-10-30T00:00:00Z", "cost": {"amount": "100", "list_amount": "100"}, "group": {"model": None}}])
assert (bill[0]["charged"], bill[0]["worth"], bill[0]["who"], bill[1]["model"]) == (123.45, 200.0, u.ANTHROPIC, "other"), "fractional cents become dollars"
ours = {"source": "paper", "who": "This paper", "model": "claude-haiku-5-5", "qty": 9, "unit": "tokens", "worth": 1.0, "charged": 1.0}
plan = {"source": "ledger", "who": "Claude Code", "model": "claude-opus-5-5", "qty": 5, "unit": "tokens", "worth": 7.0, "charged": 0}
call = {"source": "livekit", "who": "LiveKit", "model": "calls", "qty": 60, "unit": "minutes", "worth": .5, "charged": 0}
paid = {**bill[0], "source": "bill"}
rep = u.report([{**ours, "day": "2026-10-30"}, {**plan, "day": "2026-10-30"}, {**paid, "day": "2026-10-30"}, {**call, "day": "2026-10-30"}, {**ours, "day": "2026-10-31"}, {**paid, "day": "2026-10-31"}], "2026-10-31")
first, second = rep["days"]
assert (first["charged"], first["worth"]) == (123.45, 207.5) and {r["who"] for r in first["rows"]} == {u.ANTHROPIC, "Claude Code", "LiveKit"}, "a billed day drops the estimates of the same calls, and only those"
assert first["tokens"] == 14 and first["rows"][0]["who"] == u.ANTHROPIC, "minutes aren't tokens, a billed day keeps its token count, and the largest comes first"
assert second["charged"] == 1.0 and len(second["rows"]) == 1, "today's bill is partial, so today keeps its estimate"
faked = u.report([{**ours, "day": "2026-10-30"}, {**ours, "source": "ledger", "who": u.ANTHROPIC, "day": "2026-10-30"}], "2026-10-31")
assert faked["days"][0]["charged"] == 2.0, "a hub calling itself the bill erases nothing"
via = {**ours, "who": "This paper, openrouter", "worth": 3.0, "charged": 3.0}
total = {"source": "openrouter", "who": "OpenRouter", "model": "all models", "qty": 0, "unit": "tokens", "worth": 40.0, "charged": 40.0, "day": "2026-10-30"}
assert u.report([{**via, "day": "2026-10-30"}, total, {**paid, "day": "2026-10-30"}], "2026-10-31")["days"][0]["charged"] == 163.45, "OpenRouter's total covers the calls through it, and the Anthropic bill doesn't claim them"
assert u.report([{**via, "day": "2026-10-30"}, {**paid, "day": "2026-10-30"}], "2026-10-31")["days"][0]["charged"] == 126.45, "without its total, the estimate stands"
g = u.glance(rep, "2026-10-31")
assert g["last"]["day"] == "2026-10-30" and len(g["days"]) == 2 and g["who"][0][0] == u.ANTHROPIC, "the last whole day, not today so far"
assert u.glance({}, "2026-10-31")["last"] is None and u.glance({}, "2026-10-31")["days"] == []
assert len(u.report([{**plan, "day": f"2026-{m:02d}-{d:02d}"} for m in range(1, 7) for d in range(1, 29)], "2026-10-31")["days"]) == 90
full = u.report([{**plan, "day": "2026-10-30", "model": str(i)} for i in range(500)] + [{**plan, "day": "2026-10-30", "model": str(i), "worth": None} for i in range(50)], "2026-10-31")
assert len(full["days"][0]["rows"]) == 100 and len(full["unpriced"]) <= 20 and full["days"][0]["worth"] == 3500, "a flood of rows can't fill the page, and the total still counts them"

session = {"connectionMinutes": 12, "bandwidth": 2e9, "participants": [{"participantIdentity": "agent-AJ_x", "joinedAt": "2026-10-30T10:00:00Z", "leftAt": "2026-10-30T10:06:00.123456789Z"}, {"participantIdentity": "person", "joinedAt": "2026-10-30T10:00:00Z", "leftAt": "2026-10-30T11:00:00Z"}, {"participantIdentity": "agent-open", "joinedAt": "2026-10-30T10:00:00Z", "leftAt": None}]}
day_, minutes, agent, sent = u.livekit_session(session, {"seconds": 1793354400})
assert day_ == "2026-10-30" and minutes == 12 and 6 <= agent < 6.1 and sent == 2e9, (day_, minutes, agent)
assert u.livekit_session({"participants": []}, "2026-10-30T23:59:59Z")[0] == "2026-10-30", "a time can come as text or as seconds"
kit = u.livekit_rows([("2026-10-30", 1000, 100, 1e10)])[0]
assert round(kit["worth"], 2) == 2.4 and kit["charged"] == 0 and kit["unit"] == "minutes", kit

# ---------------------------------------------------------------- the paper's own calls, and the job
with s.db() as c:
    c.execute("DELETE FROM usage_day")
s.record_use("claude-haiku-5-5", 1e6, 0)
s.record_use("claude-haiku-5-5", 1e6, 0, 1e6)
s.record_use("local-model", 500, 500)
s.record_use("local-model", 500, 500)
s.record_use("broken", "many", None)
for bad in (float("nan"), float("inf"), -4e11, 10 ** 400):
    s.record_use("hostile", bad, 0)
with s.db() as c:
    mine = {r["model"]: r for r in c.execute("SELECT * FROM usage_day WHERE source = 'paper'")}
assert round(mine["claude-haiku-5-5"]["worth"], 6) == .21 and round(mine["claude-haiku-5-5"]["charged"], 6) == .21 and mine["claude-haiku-5-5"]["qty"] == 3e6, mine["claude-haiku-5-5"]["worth"]
assert mine["local-model"]["worth"] is None and mine["local-model"]["qty"] == 2000 and "broken" not in mine and "hostile" not in mine, "no price stays no price, and a bad count fails nothing and stores nothing"
assert s.ai.on_use is s.record_use

plain_row = {"day": "2026-10-30", "who": "X", "model": "m", "qty": 1, "unit": "tokens", "worth": 1.0, "charged": 0}
s.store_usage("ledger", [plain_row, plain_row])
s.store_usage("livekit", [{**plain_row, "who": "LiveKit"}])
s.store_usage("ledger", [{**plain_row, "qty": 5}])
with s.db() as c:
    kept = [dict(r) for r in c.execute("SELECT source, qty, worth FROM usage_day WHERE day = '2026-10-30' ORDER BY source")]
assert kept == [{"source": "ledger", "qty": 5, "worth": 1.0}, {"source": "livekit", "qty": 1, "worth": 1.0}], "a fresh answer replaces its own source's day, and no other"

real_fetch, asked = s.fetch, []
settings.update({"OPENROUTER_KEY": "or"})
totals = [10.0, 10.0, 10.5, 10.75, 9.0, 11.0]


def counted(url, head=None, **k):
    assert url == "https://openrouter.ai/api/v1/credits" and head == {"Authorization": "Bearer or"}, url
    return {"data": {"total_credits": 95, "total_usage": totals.pop(0)}}


s.fetch = counted
with s.db() as c:
    c.execute("DELETE FROM meta WHERE k = 'openrouter_total'")
def opened():
    with s.db() as c:
        r = c.execute("SELECT worth, charged FROM usage_day WHERE source = 'openrouter'").fetchone()
    return (r["worth"], r["charged"]) if r else None


for _ in range(2):
    s.openrouter_rows()
assert opened() is None, "the first reading only sets the start, and with nothing moved there is no row"
for _ in range(2):
    s.openrouter_rows()
assert opened() == (.75, .75), "the day adds up across runs"
s.openrouter_rows()
assert opened() == (.75, .75), "a total that falls adds nothing"
s.openrouter_rows()
assert opened() == (1.0, 1.0), "and it counts only what passes the highest reading, so a dip can't charge a day twice"
s.fetch = lambda *a, **k: {"data": {"total_usage": None}}
assert refuses(s.openrouter_total), "no total is a failure, never a zero"
s.fetch = lambda *a, **k: (_ for _ in ()).throw(OSError("down"))
settings.update({"OPENROUTER_KEY": None})
s.usage_report()
with s.db() as c:
    assert c.execute("SELECT v FROM meta WHERE k = 'openrouter_total'").fetchone() is None, "with the key gone the count stops, so adding one later can't charge one enormous day"
    c.execute("DELETE FROM usage_day WHERE source = 'openrouter'")
s.fetch = real_fetch
settings.update({"COMMONS_URL": "http://hub.example:8771"})
assert s.job_on("usage")


def hub(url, head=None, **k):
    asked.append((url, head))
    n = int(url.rsplit("=", 1)[1])
    return {"days": [s.utc_day(i) for i in range(n - 1, -1, -1)], "rows": [line("Claude", "claude-code", "claude-opus-5-5", tokens_out=n * 1e6)]}


s.fetch = hub
with s.db() as c:
    c.execute("DELETE FROM usage_day WHERE source = 'ledger'")
result = s.usage_report()
assert len(asked) == 30 and asked[0][1] == {} and not result["missing"], "a first run reads a month, with no token when none is set"
asked.clear()
s.usage_report()
assert len(asked) == 3, "later runs read only the days still changing"
with s.db() as c:
    c.execute("DELETE FROM usage_day WHERE source = 'ledger' AND day > ?", (s.utc_day(8),))
asked.clear()
s.usage_report()
assert len(asked) == 10, "after an outage it reads back past the last day it has, so no hole is left"
with s.db() as c:
    assert c.execute("SELECT COUNT(DISTINCT day) FROM usage_day WHERE source = 'ledger'").fetchone()[0] == 30
settings.update({"COMMONS_TOKEN": "viewer"})
s.ledger_page(1)
assert asked[-1][1] == {"Authorization": "Bearer viewer"}
assert settings.update({"COMMONS_URL": "http://other.example:8771"}) == ["COMMONS_TOKEN"], "a saved token never follows the address to a new host"
settings.update({"ANTHROPIC_ADMIN_KEY": "admin", "LIVEKIT_PROJECT": "p_abc", "LIVEKIT_TOKEN": "list"})
assert settings.update({"COMMONS_URL": "http://third.example:8771"}) == [], "and moving one source leaves the others' keys alone"
assert s.holds_key("LIVEKIT_PROJECT"), "Configure can't move a project that holds a token"
assert settings.update({"LIVEKIT_PROJECT": "p_other"}) == ["LIVEKIT_TOKEN"]
settings.update({"LIVEKIT_PROJECT": "p/../x", "LIVEKIT_TOKEN": "list"})


def clouds(url, head=None, **k):
    asked.append((url, head))
    if "analytics/cost" in url:
        assert head["x-api-key"] == "admin" and head["anthropic-beta"] and "admin" not in url, "the key goes in a header"
        if "page=" in url:
            return {"data": [{"starting_at": "2026-10-29T00:00:00Z", "cost": {"amount": "200", "list_amount": "300"}, "group": {"model": "claude-haiku-5-5"}}], "has_more": False}
        return {"data": [{"starting_at": "2026-10-30T00:00:00Z", "cost": {"amount": "100", "list_amount": "300"}, "group": {"model": "claude-haiku-5-5"}}], "has_more": True, "next_page": "next"}
    if url.startswith("http://third"):
        raise OSError("hub is down")
    assert url.startswith("https://cloud-api.livekit.io/api/project/p%2F..%2Fx/sessions") and head == {"Authorization": "Bearer list"}, url
    if "?" in url:
        return {"sessions": [{"sessionId": "done", "createdAt": "2026-10-29T10:00:00Z", "endedAt": "2026-10-29T10:10:00Z"}, {"sessionId": "live", "createdAt": "2026-10-29T10:00:00Z", "endedAt": None}]}
    assert url.endswith("/sessions/done"), "a session still running isn't read yet"
    return {"connectionMinutes": 10, "bandwidth": 1e9, "participants": []}


s.fetch = lambda url, *a, **k: {"data": [{"starting_at": "2026-10-30T00:00:00Z", "cost": {"amount": 10 ** 400}}], "has_more": False} if "analytics" in url else clouds(url, *a, **k)
partly = s.usage_report()
assert "the Anthropic bill" in partly["missing"] and "LiveKit" not in partly["missing"], "a number too large to read costs its own source, not the ones after it"
with s.db() as c:
    c.execute("DELETE FROM livekit_session")
    c.execute("DELETE FROM usage_day WHERE source = 'livekit'")
s.fetch = clouds
asked.clear()
result = s.usage_report()
assert result["missing"] == ["Commons"], "one source down leaves the others"
assert [r["charged"] for d in result["days"] if d["day"] == "2026-10-29" for r in d["rows"] if r["who"] == u.ANTHROPIC] == [2.0], "every page of the bill is read"
assert any(r["who"] == "LiveKit" for d in result["days"] for r in d["rows"]), result
asked.clear()
s.usage_report()
assert not any(a[0].endswith("/sessions/done") for a in asked), "each finished session is read once"
assert any(r["who"] == "LiveKit" for d in s.usage_report()["days"] for r in d["rows"]), "and stays after LiveKit stops listing it"
s.fetch = real_fetch
s.save("usage", result)
page = s.detail("usage", "")
assert page["kind"] == "usage" and page["today"] == s.utc_day() and page["days"] and "usage" in s.desks_on() and s.paper()["usage"]["missing"] == ["Commons"], page
# ---------------------------------------------------------------- costs that fill themselves
settings.update({"ANTHROPIC_ADMIN_KEY": None, "COMMONS_URL": ""})
assert u.figure("8.04382") == 8.04382 and u.figure(0) == 0
for bad in (None, "", [], {}, True, False):
    assert refuses(u.figure, bad), bad
recent, old = s.utc_day(2), s.utc_day(45)
s.save("usage", {"days": [{"day": old, "rows": [{"who": "This paper", "charged": 99.0}]}, {"day": recent, "rows": [{"who": "This paper", "charged": 1.25}, {"who": "Commons", "charged": .5}, {"who": "Commons, openrouter", "charged": .1}, {"who": "OpenRouter", "charged": 2.0}, {"who": "Claude Code", "charged": 0}]}]})
assert u.charged_by(s.load("usage")["data"], s.utc_day(30)) == {"Anthropic API": 1.75, "OpenRouter": 2.1}, "thirty days means thirty days, not the last thirty with use in them"
typed_costs = [("Twilio", 797, "month"), ("Twilio numbers", 300, "month"), ("Twilio, support plan", 4900, "month"), ("Anthropic API", 30000, "month"), ("OpenRouter", 4000, "month"), ("Deepgram", None, "month"), ("Rent", 5000, "month"), ("Other", None, "month")]
s.set_costs(typed_costs)
settings.update({"TWILIO_ACCOUNT": "AC1", "TWILIO_KEY": "SK1", "TWILIO_SECRET": "shh", "DEEPGRAM_KEY": "dg", "OPENROUTER_KEY": "or"})
assert s.job_on("costs")
amounts = {"price": "8.04382", "dollars": 1.5}


def bills(url, head=None, **k):
    if "twilio" in url:
        assert head["Authorization"] == "Basic " + s.base64.b64encode(b"SK1:shh").decode() and "shh" not in url and "/Accounts/AC1/" in url, url
        return {"usage_records": [{"category": "totalprice", "price": amounts["price"], "price_unit": "usd"}]}
    assert head == {"Authorization": "Token dg"}, head
    if url.endswith("/projects"):
        return {"projects": [{"project_id": "p/1"}, {"project_id": "p2"}]}
    assert "p%2F1" in url or "p2" in url, url
    return {"results": [{"dollars": amounts["dollars"]}, {"dollars": .25}]}


s.fetch = bills
rows = s.cost_rows()
assert [(r["name"], r["cents"]) for r in rows] == [("Twilio", 804), ("Deepgram", 350)] and all(r["note"] for r in rows), rows
s.save("costs", rows)
for field, value in (("price", None), ("price", ""), ("dollars", None), ("price", "1e13")):
    keep, amounts[field] = amounts[field], value
    held = {r["name"]: r for r in s.cost_rows()}
    amounts[field] = keep
    moved = "Twilio" if field == "price" else "Deepgram"
    assert held[moved]["cents"] == (804 if moved == "Twilio" else 350) and "last good" in held[moved]["note"], "a missing or absurd figure holds the last good one, never a zero"
s.fetch = lambda url, *a, **k: {"usage_records": {}} if "twilio" in url else bills(url, *a, **k)
assert "last good" in s.cost_rows()[0]["note"], "the wrong shape is a failure too"
s.fetch = lambda url, *a, **k: (_ for _ in ()).throw(OSError("down")) if "twilio" in url else bills(url, *a, **k)
held = s.cost_rows()
assert held[0]["cents"] == 804 and "last good" in held[0]["note"] and held[1]["cents"] == 350, "a bill that can't be read keeps its last figure and says so"
s.save("costs", [])
s.fetch = lambda *a, **k: (_ for _ in ()).throw(OSError("down"))
assert s.cost_rows() == [], "and with no figure yet there is no row, not a zero"
s.fetch = real_fetch
s.save("costs", rows)
shown = {r["name"]: r for r in s.get_costs()}
assert shown["Twilio"]["cents"] == 804 and shown["Deepgram"]["cents"] == 350 and shown["OpenRouter"]["cents"] == 210, "a real bill stands in for the typed row"
real_provider, real_ready = s.ai.provider, s.ai.ready
s.ai.provider, s.ai.ready = (lambda: "anthropic"), (lambda: True)
assert shown["Twilio numbers"]["cents"] == 300 and shown["Twilio, support plan"]["cents"] == 4900, "and only the row of that exact name"
shown = {r["name"]: r for r in s.get_costs()}
assert shown["Anthropic API"]["cents"] == 30000 and "note" not in shown["Anthropic API"], "an estimate never replaces a figure you typed"
s.ai.ready = real_ready
assert shown["Rent"]["cents"] == 5000 and shown["Other"]["connect"] is None, "other rows stay as they are"
page_rows = s.clean_costs({"rows": [{"name": r["name"], "cents": r["cents"], "per": r["per"]} for r in s.get_costs() if not r.get("note")]})
s.set_costs(page_rows + s.replaced_costs(page_rows))
settings.update({"TWILIO_ACCOUNT": "", "TWILIO_KEY": "", "TWILIO_SECRET": None})
gone = {r["name"]: r for r in s.get_costs()}
assert "note" not in gone["Twilio"] and gone["Twilio"]["cents"] == 797, "a page save keeps a replaced row, so it's back when its source goes, and a source that's off stops showing at once"
assert gone["Deepgram"]["cents"] == 350
settings.update({"DEEPGRAM_KEY": None, "OPENROUTER_KEY": None})
s.save("costs", [])
with s.db() as c:
    c.execute("DELETE FROM cost")
s.set_costs([("Deepgram", None, "month"), ("Anthropic API", None, "month"), ("Rent", 100, "month")])
blank = {r["name"]: r for r in s.get_costs()}
assert blank["Deepgram"]["connect"] == "deepgram", "a blank row with a source offers to connect it"
s.ai.ready = lambda: True
filled = {r["name"]: r for r in s.get_costs()}
assert filled["Anthropic API"]["cents"] == 175 and filled["Anthropic API"]["estimate"] and "Estimated" in filled["Anthropic API"]["note"], "an estimate fills a blank row, and says it's an estimate"
s.ai.provider = lambda: "ollama"
assert "connect" in {r["name"]: r for r in s.get_costs()}["Anthropic API"], "a local model is not an Anthropic bill"
s.ai.provider, s.ai.ready = real_provider, real_ready
s.save("usage", {"days": []})
settings.update({"OPENROUTER_KEY": "or"})
assert all(r["name"] != "OpenRouter" for r in s.get_costs()), "with nothing counted there is no row, not a zero"
s.save("usage", {"days": [{"day": recent, "rows": [{"who": "OpenRouter", "charged": 1e13}]}]})
assert all(r["name"] != "OpenRouter" for r in s.get_costs()), "and an absurd figure can't move the money total"
with s.db() as c:
    c.execute("DELETE FROM cost")
settings.update({"OPENROUTER_KEY": None})
s.save("usage", result)
settings.update({"COMMONS_URL": "", "ANTHROPIC_ADMIN_KEY": None, "LIVEKIT_PROJECT": "", "LIVEKIT_TOKEN": None})
assert not s.job_on("usage"), "nothing connected and no provider means no desk"
try:
    s.d_usage("")
except LookupError:
    pass
else:
    raise AssertionError("switched off means no page")
