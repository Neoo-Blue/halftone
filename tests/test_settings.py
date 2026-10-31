# Run from test_paper.py, which owns the temp data dir: the two things a public release must get right, secrets and the door.
import http.client
import stat
import threading
import time as _t
from http.server import ThreadingHTTPServer

import auth


def refuses(fn, *a):
    try:
        fn(*a)
    except ValueError:
        return True
    return False


# ---------------------------------------------------------------- settings: a secret goes in and never comes out
PLEX_SECRET, KEY2 = "plex-secret-value-1234", "sonarr-secret-value-5678"
settings.update({"PLEX_URL": "http://10.0.0.5:32400", "PLEX_TOKEN": PLEX_SECRET, "SONARR_URL": "http://10.0.0.5:8989", "SONARR_KEY": KEY2})
assert settings.get("PLEX_TOKEN") == PLEX_SECRET and settings.enabled("plex")
shown = json.dumps(s.settings_page())
assert PLEX_SECRET not in shown and KEY2 not in shown, "a secret reached the browser"
field = next(f for x in settings.view() if x["id"] == "plex" for f in x["fields"] if f["key"] == "PLEX_TOKEN")
assert field["set"] is True and "value" not in field

stored = Path(tmp) / "settings.json"
assert stat.S_IMODE(stored.stat().st_mode) == 0o600, "secrets on disk must be owner only"

settings.update({"PLEX_TOKEN": ""})
assert settings.get("PLEX_TOKEN") == PLEX_SECRET, "a blank secret keeps the saved one"
assert settings.update({"PLEX_URL": "http://10.0.0.5:32400"}) == [], "the same address keeps its secret"
assert settings.update({"PLEX_URL": "http://attacker.example:32400"}) == ["PLEX_TOKEN"] and not settings.get("PLEX_TOKEN"), "a saved token follows a changed address"
assert settings.get("SONARR_KEY") == KEY2, "only that connection's secret goes"
settings.update({"PLEX_URL": "http://10.0.0.6:32400", "PLEX_TOKEN": "typed-with-the-new-address"})
assert settings.get("PLEX_TOKEN") == "typed-with-the-new-address", "a token typed with a new address stays"
settings.update({"PLEX_TOKEN": None})
assert not settings.get("PLEX_TOKEN") and not settings.enabled("plex")

os.environ["RADARR_KEY"] = "from-the-environment"
assert settings.get("RADARR_KEY") == "from-the-environment" and "from-the-environment" not in json.dumps(settings.view()), "the environment wins, and stays hidden"
assert next(f for x in settings.view() if x["id"] == "radarr" for f in x["fields"] if f["key"] == "RADARR_KEY")["locked"]
assert refuses(settings.update, {"RADARR_KEY": "x"}), "a setting from the environment can't be overwritten here"
assert refuses(settings.update, {"RADARR_URL": "http://attacker.example"}), "or pointed somewhere else"
del os.environ["RADARR_KEY"]

for bad in ({"NOPE": "x"}, {"_auth": {"hash": "x"}}, {"PAPER_TZ": "Mars/Base"}, {"PLEX_URL": "file:///etc/passwd"}, {"PLEX_URL": "http://user:pw@host/"}, {"PAPER_SINCE": "tomorrow"}, {"PVE_INSECURE": "yes"},
            {"HOSTS": "nope"}, {"HOSTS": [{"name": "x", "target": "-oProxyCommand=evil"}]}, {"HOSTS": [{"name": "x", "target": "a@b c"}]}, {"PROBES": [{"group": "g", "name": "n", "url": "ftp://x"}]},
            {"EXTRA_FEEDS": [{"desk": "nope", "name": "n", "url": "https://x.example"}]}, {"EARLIER": [{"label": "x", "day": "2026-01-01", "amount": "lots"}]}, {"MAILBOXES": [{"address": "not an address", "label": ""}]}, {"PAPER_NAME": 5}, {"PAPER_FONT": "comic-sans"}, {"PAPER_FONT": '"><script>'}):
    assert refuses(settings.update, bad), bad
assert refuses(settings.update, ["x"])
settings.update({"PROBES": [{"group": "", "name": "", "url": ""}]})
assert settings.get("PROBES") == [], "a row left blank is dropped"
settings.update({"PLEX_URL": ""})

# ---------------------------------------------------------------- a section with nothing set stays off the page
page = s.paper()
assert page["on"]["media"] is False and page["on"]["money"] is False and page["on"]["systems"] is False and page["on"]["world"] is True
assert page["media"]["data"] is None and page["name"] == "The Times"
settings.update({"MAILBOXES": []})
s.save("mail", {"read": 1})
assert s.paper()["mail_status"]["data"] is None and s.paper()["mail"]["need"] == [], "switching a desk off takes its old snapshot off the page"
assert not any("Mail" in w["text"] or "Plex" in w["text"] for w in s.paper()["worries"]), "a desk that's off is not a worry"
assert s.check("plex") == {"ok": False, "text": "Fill in every field first."} and not s.check("nope")["ok"]


def stub(handler_status):
    def fake(*a, **k):
        raise s.urllib.error.HTTPError("http://x", handler_status, "no", {}, None)
    return fake


settings.update({"PLEX_URL": "http://10.0.0.5:32400", "PLEX_TOKEN": PLEX_SECRET})
real_fetch, s.fetch = s.fetch, stub(401)
said = s.check("plex")
assert not said["ok"] and "refused the key" in said["text"] and PLEX_SECRET not in json.dumps(said)
s.fetch = lambda *a, **k: (_ for _ in ()).throw(OSError(f"token {PLEX_SECRET} in an error"))
assert PLEX_SECRET not in json.dumps(s.check("plex")), "an error's text never reaches the page"
s.fetch = real_fetch
settings.update({"PLEX_URL": ""})

# ---------------------------------------------------------------- the door, over real HTTP
auth._fails.clear()
server = ThreadingHTTPServer(("127.0.0.1", 0), s.Handler)
port = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()


def call(method, path, body=None, headers=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
    sent = {"X-Paper": "1", "Content-Type": "application/json", **(headers or {})}
    c.request(method, path, json.dumps(body) if body is not None else None, {k: v for k, v in sent.items() if v is not None})
    r = c.getresponse()
    raw = r.read()
    c.close()
    return r, raw


for path in ("/api/paper", "/api/settings", "/api/detail/mail/" + "a" * 24, "/api/read?u=https://1.1.1.1/", "/img/remote?u=https://1.1.1.1/", "/img/plex?p=x", "/api/detail/event/abc.js"):
    assert call("GET", path)[0].status == 401, f"{path} served without a session"
for path in ("/", "/settings", "/world/event/abc", "/index.html", "/settings.html"):
    r, _ = call("GET", path)
    assert r.status in (302, 404) and (r.status == 404 or r.getheader("Location") == "/login"), f"{path} served without a session"
assert call("PUT", "/api/settings", {"values": {"PAPER_NAME": "x"}})[0].status == 401
assert call("POST", "/api/settings/test/plex")[0].status == 401
assert call("GET", "/healthz")[0].status == 200 and call("GET", "/login")[0].status == 200 and call("GET", "/style.css")[0].status == 200

assert auth.state() == "setup"
auth.announce()
code = auth._setup_code
assert call("POST", "/api/login", {"password": "anything-at-all"})[0].status == 401, "no password exists yet"
assert call("POST", "/api/setup", {"code": "wrong", "password": "a-long-password"})[0].status == 401, "reaching a new install first proves nothing"
assert call("POST", "/api/setup", {"code": code, "password": "short"})[0].status == 400
assert call("POST", "/api/setup", {"password": "a-long-password"}, {"X-Paper": None})[0].status == 403, "a cross-site form can't set the header"
assert call("POST", "/api/setup", {"code": code, "password": "x" * 12}, {"Sec-Fetch-Site": "cross-site"})[0].status == 403
r, _ = call("POST", "/api/setup", {"code": code, "password": "a-long-password"})
cookie = r.getheader("Set-Cookie")
assert r.status == 200 and "HttpOnly" in cookie and "SameSite=Strict" in cookie and "Secure" not in cookie, cookie
jar = {"Cookie": cookie.split(";")[0]}
assert auth.state() == "login" and auth._setup_code is None
assert "hash" not in json.dumps(s.settings_page()) and "salt" not in json.dumps(s.settings_page())
assert call("POST", "/api/setup", {"code": code, "password": "taking-it-over"})[0].status == 401, "a used code is dead"

r, raw = call("GET", "/api/paper", headers=jar)
assert r.status == 200 and json.loads(raw)["name"], "a session opens the paper"
assert call("GET", "/settings", headers=jar)[0].status == 200 and b"Plex" in call("GET", "/api/settings", headers=jar)[1]
assert call("PUT", "/api/settings", {"values": {"PAPER_NAME": "The <b>Ledger</b>"}}, jar)[0].status == 200
front = call("GET", "/", headers=jar)[1]
assert b"The &lt;b&gt;Ledger&lt;/b&gt;" in front and b"The Times" not in front, "the name is printed escaped, everywhere"
assert b'data-masthead="blackletter"' in front and b"/fonts/manufacturing-consent.woff2" in front
assert call("PUT", "/api/settings", {"values": {"PAPER_FONT": "fraktur"}}, jar)[0].status == 200
front = call("GET", "/", headers=jar)[1]
assert b'data-masthead="fraktur"' in front and b'href="/fonts/unifrakturcook.woff2"' in front and b"manufacturing-consent" not in front, "the page arrives in the chosen face"
assert b'data-masthead="fraktur"' in call("GET", "/login")[1] and b'data-masthead="fraktur"' in call("GET", "/settings", headers=jar)[1]
settings.update({"PAPER_FONT": "theme"})
assert b'data-masthead="theme"' in call("GET", "/", headers=jar)[1]
assert all(call("GET", f"/fonts/{f}.woff2")[0].status == 200 for f in s.TITLE_FONTS.values()), "every title font ships"
os.environ["PAPER_FONT"] = '"><script>alert(1)</script>'
assert b"<script>alert" not in call("GET", "/", headers=jar)[1], "a bad environment value can't reach the page"
del os.environ["PAPER_FONT"]
settings.update({"PAPER_FONT": "blackletter"})
assert call("PUT", "/api/settings", {"values": {"PAPER_NAME": "x"}}, {**jar, "X-Paper": None})[0].status == 403
r, raw = call("PUT", "/api/settings", {"values": {"PLEX_URL": "ftp://x"}}, jar)
assert r.status == 400 and b"http" in raw
assert call("GET", "/img/remote?u=https://1.1.1.1/", headers={**jar, "Sec-Fetch-Site": "cross-site"})[0].status == 403
r, _ = call("POST", "/api/login", {"password": "a-long-password"}, {"X-Forwarded-Proto": "https"})
assert r.status == 200 and "Secure" in r.getheader("Set-Cookie"), "behind https the cookie is Secure"
assert call("GET", "/api/paper", headers={"Cookie": "paper_session=forged"})[0].status == 401
assert call("GET", "/api/paper", headers={"Cookie": "not a cookie;;;="})[0].status == 401

other = {"Cookie": r.getheader("Set-Cookie").split(";")[0]}
assert call("PUT", "/api/password", {"current": "wrong-password", "new": "another-long-one"}, jar)[0].status == 401
auth._fails.clear()
r, _ = call("PUT", "/api/password", {"current": "a-long-password", "new": "another-long-one"}, jar)
assert r.status == 200 and call("GET", "/api/paper", headers=other)[0].status == 401, "changing the password signs out everyone else"
jar = {"Cookie": r.getheader("Set-Cookie").split(";")[0]}
assert call("GET", "/api/paper", headers=jar)[0].status == 200
assert call("POST", "/api/logout", {}, jar)[0].status == 200 and call("GET", "/api/paper", headers=jar)[0].status == 401, "signing out ends the session"

for _ in range(auth.FAIL_LIMIT):
    call("POST", "/api/login", {"password": "guess-guess-guess"})
r, _ = call("POST", "/api/login", {"password": "another-long-one"})
assert r.status == 429 and r.getheader("Retry-After"), "guessing stops, even for the right password"
auth._fails.clear()
assert call("POST", "/api/login", {"password": "another-long-one"})[0].status == 200

# PAPER_PASSWORD wins, and is never stored
os.environ["PAPER_PASSWORD"] = "from-the-env-file"
assert auth.check_password("from-the-env-file") and not auth.check_password("another-long-one") and "from-the-env-file" not in stored.read_text()
assert refuses(auth.change_password, "from-the-env-file", "a-new-long-password")
del os.environ["PAPER_PASSWORD"]
auth._fails.clear()

# behind someone else's gate: no login, and only named hosts are answered
assert auth.host_allowed("evil.example")
auth.MODE = "none"
os.environ["PAPER_HOSTS"] = "paper.example, other.example"
assert auth.state() == "open" and auth.host_allowed("paper.example") and auth.host_allowed("OTHER.example:8095") and auth.host_allowed("127.0.0.1:8095") and auth.host_allowed("[::1]:8095") and auth.host_allowed("[::1]")
assert not auth.host_allowed("evil.example") and not auth.host_allowed(None) and not auth.host_allowed("paper.example.evil.example")
assert call("GET", "/api/paper", headers={"Host": "evil.example"})[0].status == 403, "a rebound DNS name gets nothing"
assert call("GET", "/api/paper")[0].status == 200
auth.MODE = "password"
del os.environ["PAPER_HOSTS"]
server.shutdown()

# ---------------------------------------------------------------- the security review's attacks, each one replayed
import socket as _socket

auth._fails.clear()
settings.set_auth(None)
auth.store_password("the-real-password")
server = ThreadingHTTPServer(("127.0.0.1", 0), s.Handler)
port = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()


def armed(password):
    """A login with everything sent but its last byte, so it passes the limit check and can land long after."""
    body = json.dumps({"password": password}).encode()
    c = _socket.create_connection(("127.0.0.1", port), timeout=20)
    c.sendall(b"POST /api/login HTTP/1.1\r\nHost: x\r\nX-Paper: 1\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body[:-1])
    return c, body[-1:]


guns = [armed(f"guess-number-{i}") for i in range(auth.FAIL_LIMIT + 6)] + [armed("the-real-password")]
_t.sleep(.4)  # every one of them is now past the check at the door, and waiting in the read
for i in range(auth.FAIL_LIMIT):
    call("POST", "/api/login", {"password": "shut-the-limit"})
assert auth.retry_after(), "the limit is shut"
got = []
for c, last in guns:
    c.sendall(last)
    got.append(c.recv(4096).split(b"\r\n")[0])
    c.close()
assert not any(b" 200 " in g for g in got), f"a held-open login beat the limit: {got[-1]}"
assert len(auth._fails) == auth.FAIL_LIMIT, f"guesses went on being tried during a lockout: {len(auth._fails)}"
assert not auth.check_password("the-real-password"), "a shut limit stops the password check itself"
try:
    assert not auth.change_password("the-real-password", "taken-over-now"), "a stolen session can't guess the password past the limit"
finally:
    auth._fails.clear()
assert auth.check_password("the-real-password"), "and nothing changed"

os.environ["PAPER_PASSWORD"] = "first-env-password"
token = auth.start_session()
assert auth.signed_in(token)
os.environ["PAPER_PASSWORD"] = "second-env-password"
assert not auth.signed_in(token), "changing PAPER_PASSWORD ends every session"
del os.environ["PAPER_PASSWORD"]
os.environ["PAPER_PASSWORD"] = "short"
try:
    auth.announce()
except SystemExit:
    pass
else:
    raise AssertionError("a short PAPER_PASSWORD must stop the paper from starting")
del os.environ["PAPER_PASSWORD"]

# a key read before its address can't follow the address to a new host
settings.update({"SONARR_URL": "http://old.example", "SONARR_KEY": "the-sonarr-key"})
seen = []


def fetching(url, headers=None, **k):
    seen.append((url, (headers or {}).get("X-Api-Key")))
    if len(seen) == 1:
        settings.update({"SONARR_URL": "http://attacker.example"})
    return [] if "episode" in url else {}


real_fetch, s.fetch = s.fetch, fetching
s.d_show("1")
s.fetch = real_fetch
assert all(u.startswith("http://old.example") for u, _ in seen), seen

# a key never follows a redirect to another host
red = s.KeptRedirect()
req = s.urllib.request.Request("https://plex.example/x", headers={"X-Plex-Token": "k", "X-Api-Key": "k", "Authorization": "k", "Accept": "a"})
moved = red.redirect_request(req, None, 302, "Found", {}, "http://evil.example/x")
assert not {k.lower() for k in moved.headers} & {"x-plex-token", "x-api-key", "authorization"} and moved.get_header("Accept") == "a", moved.headers
kept = red.redirect_request(req, None, 302, "Found", {}, "https://plex.example/y")
assert kept.has_header("Authorization"), "the same host keeps its key"

# turning certificate checks off counts as moving the key
settings.update({"PVE_URL": "https://pve.example/api2/json", "PVE_TOKEN": "a-token", "PVE_INSECURE": False})
assert settings.update({"PVE_INSECURE": True}) == ["PVE_TOKEN"], "a stolen session can't weaken TLS and keep the token"
settings.update({"PVE_TOKEN": "a-token"})
assert settings.update({"PVE_INSECURE": True}) == [], "saving it unchanged keeps the token"
settings.update({"PVE_URL": "", "PVE_TOKEN": None, "PVE_INSECURE": False, "SONARR_URL": "", "SONARR_KEY": None})

# hostile feeds and pages cost nothing and stop nothing
start = _t.monotonic()
assert s.plain("<" * 4_000_000, 50) and s.plain("<b>kept</b> text") == "kept text"
assert _t.monotonic() - start < 2, "a run of < must not freeze the server"
assert s.when_stamp("Mon, 01 Jan 99999999999 00:00:00 GMT") == 0
assert s.extract("<html><body><script type='application/ld+json'>" + "[" * 200000 + "</script><p>x</p></body></html>", "https://x.example/a")["body"] == ""
for bad_ip, why in (("::127.0.0.1", "IPv4 compatible"), ("fec0::1", "site local"), ("64:ff9b::a9fe:a9fe", "NAT64"), ("ff0e::1", "multicast"), ("224.0.0.1", "multicast")):
    assert not s.public_ip(bad_ip), why
assert s.public_ip("1.1.1.1") and s.public_ip("2606:4700::1111")


class Drip:
    def read1(self, n):
        _t.sleep(.02)
        return b"x"


try:
    s.read_all(Drip(), 10 ** 6, .1)
except OSError:
    pass
else:
    raise AssertionError("a server dripping bytes must run out of time")

# a GET with a body can't smuggle a second request
c = _socket.create_connection(("127.0.0.1", port), timeout=5)
smuggled = b"PUT /api/settings HTTP/1.1\r\nHost: x\r\nX-Paper: 1\r\nContent-Length: 2\r\n\r\n{}"
c.sendall(b"GET /healthz HTTP/1.1\r\nHost: x\r\nContent-Length: " + str(len(smuggled)).encode() + b"\r\n\r\n" + smuggled)
_t.sleep(.3)
raw = b""
while True:
    part = c.recv(4096)
    if not part:
        break
    raw += part
c.close()
assert raw.count(b"HTTP/1.1 ") == 1, f"two answers to one request: {raw[:200]}"

# a job's failure keeps its kind, never its text
s.save("media", error=s.failure(ValueError("Invalid header value b'the-secret-key'")))
assert "secret" not in s.load("media")["error"] and s.load("media")["error"] == "ValueError"
assert s.failure(s.urllib.error.HTTPError("http://x", 404, "no", {}, None)) == "HTTPError 404"
server.shutdown()
