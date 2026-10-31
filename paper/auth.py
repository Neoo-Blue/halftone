"""Who may read this paper.

PAPER_AUTH=password (the default) keeps the whole paper behind one password. A new install has none, so a one-time code
goes to the container log and setting the password needs it: being first to reach a fresh install proves nothing.
PAPER_AUTH=none is for a paper already behind a gate such as Cloudflare Access. Only hosts named in PAPER_HOSTS are then
answered, so a web page can't reach it through a DNS trick.
"""
import hashlib
import hmac
import os
import secrets
import threading
import time
from collections import deque

import settings

MODE = os.environ.get("PAPER_AUTH", "password")
if MODE not in ("password", "none"):
    raise SystemExit("PAPER_AUTH must be password or none")

COOKIE = "paper_session"
SESSION_DAYS = 30
MIN_PASSWORD = 10
FAIL_LIMIT, FAIL_WINDOW = 10, 300
LOCAL_HOSTS = {"localhost", "127.0.0.1", "[::1]"}

connect = None  # server.py hands over its database connection
_fails = deque()
_lock = threading.Lock()
_hashing = threading.Semaphore(2)  # each hash takes 32 MB on purpose, so a flood of logins can't take the box down
_setup_code = None


def state():
    if MODE == "none":
        return "open"
    return "login" if os.environ.get("PAPER_PASSWORD") or settings.auth_record() else "setup"


def host_allowed(host):
    if MODE != "none":
        return True
    name = (host or "").rsplit(":", 1)[0].lower() if not (host or "").endswith("]") else (host or "").lower()
    return name in LOCAL_HOSTS or name in {h.strip().lower() for h in os.environ.get("PAPER_HOSTS", "").split(",") if h.strip()}


def announce():
    """A new install prints its setup code once. It lives only in memory, so a restart makes a new one."""
    global _setup_code
    if MODE == "password" and 0 < len(os.environ.get("PAPER_PASSWORD", "")) < MIN_PASSWORD:
        raise SystemExit(f"PAPER_PASSWORD needs at least {MIN_PASSWORD} characters")
    if state() == "setup":
        _setup_code = secrets.token_urlsafe(9)
        print(f"\n  This paper has no password yet. Open it and enter this setup code: {_setup_code}\n", flush=True)


def retry_after():
    """Seconds until another try is allowed.

    ponytail: one counter for the whole paper, because behind a proxy every caller has the same address. A stranger can
    hold the login shut for five minutes at a time but can't guess, and anyone already signed in isn't affected.
    """
    with _lock:
        now = time.monotonic()
        while _fails and now - _fails[0] > FAIL_WINDOW:
            _fails.popleft()
        return round(FAIL_WINDOW - (now - _fails[0])) + 1 if len(_fails) >= FAIL_LIMIT else 0


def _failed():
    with _lock:
        _fails.append(time.monotonic())


def _hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=2 ** 15, r=8, p=1, maxmem=2 ** 26).hex()


def _digest(text):
    return hashlib.sha256(text.encode()).digest()


def check_password(password):
    if not isinstance(password, str) or len(password) > 200:
        return False
    if retry_after() or not _hashing.acquire(blocking=False):  # here too: a request can pass the door and then wait with its body held open
        return False
    try:
        env = os.environ.get("PAPER_PASSWORD")
        if env:
            ok = hmac.compare_digest(_digest(password), _digest(env))
        else:
            rec = settings.auth_record()
            ok = bool(rec) and hmac.compare_digest(_hash(password, bytes.fromhex(rec["salt"])), rec["hash"])
    finally:
        _hashing.release()
    if not ok:
        _failed()
    return ok


def valid_new(password):
    if not isinstance(password, str) or not MIN_PASSWORD <= len(password) <= 200:
        raise ValueError(f"Use at least {MIN_PASSWORD} characters.")


def store_password(password):
    salt = secrets.token_bytes(16)
    settings.set_auth({"salt": salt.hex(), "hash": _hash(password, salt)})


def set_first_password(code, password):
    """True once the password is set. A wrong code counts as a failed login."""
    global _setup_code
    valid_new(password)
    if retry_after() or state() != "setup" or not isinstance(code, str) or not _setup_code or not hmac.compare_digest(_digest(code.strip()), _digest(_setup_code)):
        _failed()
        return False
    store_password(password)
    _setup_code = None
    return True


def change_password(current, new):
    if os.environ.get("PAPER_PASSWORD"):
        raise ValueError("The password is set by the environment, so change it there.")
    valid_new(new)
    if not check_password(current):
        return False
    store_password(new)
    end_all()
    return True


def _session_key(token):
    """Mixing in PAPER_PASSWORD means that changing it ends every session, as changing a stored password does."""
    return _digest(token + os.environ.get("PAPER_PASSWORD", "")).hex()


def new_token():
    """For AI clients. Shown once and stored hashed, so losing the file doesn't lose it to anyone."""
    token = "paper_" + secrets.token_urlsafe(32)
    settings.set_token(_digest(token).hex())
    return token


def token_ok(token):
    env, saved = os.environ.get("PAPER_AI_TOKEN"), settings.token_record()
    if env:
        return hmac.compare_digest(_digest(token), _digest(env))
    return bool(saved) and hmac.compare_digest(_digest(token).hex(), saved)


def start_session():
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    with connect() as c:
        c.execute("DELETE FROM session WHERE expires < ?", (now,))
        c.execute("INSERT INTO session VALUES (?, ?)", (_session_key(token), now + SESSION_DAYS * 86400))
    return token


def signed_in(token):
    if not token:
        return False
    with connect() as c:
        return bool(c.execute("SELECT 1 FROM session WHERE hash = ? AND expires >= ?", (_session_key(token), int(time.time()))).fetchone())


def end_session(token):
    with connect() as c:
        c.execute("DELETE FROM session WHERE hash = ?", (_session_key(token or ""),))


def end_all():
    with connect() as c:
        c.execute("DELETE FROM session")
