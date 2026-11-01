"""Everything this paper knows about its owner lives here, never in the code.

A value comes from the environment first, then settings.json, then the default below. A section with nothing set is
simply off. Secrets can be written and cleared from the settings page but never read back: view() only says whether
one is set. settings.json is mode 600 in the data volume, the same trust as a .env file. Encrypting it with a key kept
beside it would protect nothing.
"""
import json
import os
import re
import threading
import urllib.parse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DESKS = ("world", "us", "business", "tech", "ai", "security", "science", "sports")
CHARTS = (("dots", "Halftone dots"), ("line", "Lines"), ("area", "Filled areas"), ("bars", "Columns"))
MASTHEADS = (("blackletter", "Blackletter"), ("fraktur", "Fraktur"), ("fatface", "Fat face"), ("serif", "Classic serif"), ("theme", "Follows the theme"))
PROVIDERS = (  # value, label, OpenAI-compatible base address
    ("anthropic", "Anthropic", ""), ("openai", "OpenAI", "https://api.openai.com/v1"), ("gemini", "Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai"),
    ("xai", "xAI Grok", "https://api.x.ai/v1"), ("openrouter", "OpenRouter", "https://openrouter.ai/api/v1"), ("groq", "Groq", "https://api.groq.com/openai/v1"),
    ("mistral", "Mistral", "https://api.mistral.ai/v1"), ("deepseek", "DeepSeek", "https://api.deepseek.com/v1"), ("together", "Together", "https://api.together.xyz/v1"),
    ("ollama", "Ollama, on your own machine", "http://localhost:11434/v1"), ("lmstudio", "LM Studio, on your own machine", "http://localhost:1234/v1"), ("custom", "Anything OpenAI-compatible", ""),
)
SLUG, MAILBOX = r"[a-z]{1,40}", r"[^@\s]+@[^@\s]+\.[^@\s]+"
SSH_TARGET = r"[A-Za-z0-9._][A-Za-z0-9._-]*@[A-Za-z0-9.:_-]+"  # can't start with a dash, or ssh reads it as an option


def F(key, label, kind="text", default="", hint="", placeholder="", columns=None, options=None, guards=False):
    return {"key": key, "label": label, "kind": kind, "default": default, "hint": hint, "placeholder": placeholder, "columns": columns, "options": options, "guards": guards}


def COL(key, label, kind="text", pattern=None, options=None, placeholder=""):
    return {"key": key, "label": label, "kind": kind, "pattern": pattern, "options": options, "placeholder": placeholder}


SECTIONS = [
    {"id": "paper", "title": "The paper", "about": "What it is called and whose day it follows.", "needs": (), "fields": [
        F("PAPER_NAME", "Name", default="The Times"),
        F("PAPER_FONT", "Title font", "choice", "blackletter", options=MASTHEADS),
        F("PAPER_TZ", "Time zone", "tz", "UTC", "A name like America/New_York. It sets the date on the masthead and the days in the money report."),
        F("PAPER_SINCE", "First edition", "date", hint="Each day's number counts from here. Blank counts from the day you started the paper."),
    ]},
    {"id": "layout", "title": "Layout", "about": "How the front page arranges itself, and how your machines are charted. Use Arrange in the menu to move sections by hand.", "needs": (), "fields": [
        F("LEARN_LAYOUT", "Learn from what I read", "bool", False, "After every 2 hours of reading, the sections you spend the most time in move up. Phone and desktop learn separately, and you can undo each change."),
        F("CHART_STYLE", "Home server charts", "select", "dots", options=CHARTS),
    ]},
    {"id": "invest", "title": "Investments", "about": "What you hold, priced from Yahoo Finance, on the front page and the tape. Easiest to edit on the Investments page. None of it is shared with an AI.", "needs": (), "fields": [
        F("HOLDINGS", "What you hold", "rows", [], "A symbol with no shares is only watched. Use BTC-USD for crypto.", columns=[
            COL("symbol", "Symbol", pattern=r"[A-Za-z0-9^][A-Za-z0-9.=^-]{0,14}", placeholder="AAPL"), COL("shares", "Shares", "qty", placeholder="10"), COL("buy", "Buy price", "qty", placeholder="150.25"), COL("tape", "On the tape", "select", options=("yes", "no"))]),
        F("SHOW_GAIN", "Show gain and loss", "bool", True, "Worked out from the buy prices you add. Turn it off to show only the total."),
        F("TAPE_OFF", "Hide from the tape", hint="Market names, separated by commas. The Investments page has a switch for each."),
        F("TAPE_SYMBOLS", "Tape symbols", default="^GSPC,^IXIC,^DJI,^VIX,GC=F,CL=F,BTC-USD,EURUSD=X", hint="Shown when WARROOM sends no markets. Yahoo Finance symbols, separated by commas."),
        F("PORTFOLIO_URL", "Broker or portfolio address", "url", hint="docs/portfolio-feed.md shows the JSON to return."),
        F("PORTFOLIO_TOKEN", "Bearer token", "secret"),
    ]},
    {"id": "world", "title": "World", "about": "The globe, the conflict desk and the odds. Works from the first minute.", "needs": ("WARROOM_URL",), "fields": [
        F("WARROOM_URL", "WARROOM address", "url", "https://war.wakxi.com/api/v1", "The free public API. Change it only if you run your own WARROOM."),
    ]},
    {"id": "news", "title": "News", "about": "More than 60 outlets are already on the wire. Add your own here.", "needs": (), "fields": [
        F("EXTRA_FEEDS", "Your feeds", "rows", [], "Any RSS or Atom address.", columns=[
            COL("desk", "Desk", "select", options=DESKS), COL("name", "Outlet", placeholder="Local Times"), COL("url", "Feed address", "url", placeholder="https://example.com/rss.xml")]),
    ]},
    {"id": "weather", "title": "Weather", "about": "Now, the next two days and the week ahead, from Open-Meteo. No key needed.", "needs": ("WEATHER_PLACE",), "fields": [
        F("WEATHER_PLACE", "Place", placeholder="Oakland"),
        F("WEATHER_UNITS", "Units", "select", "celsius", options=(("celsius", "Celsius, km/h"), ("fahrenheit", "Fahrenheit, mph"))),
    ]},
    {"id": "sports", "title": "Sports", "about": "Live scores and results. No key needed. Sports news is on the wire either way.", "needs": ("SPORTS_LEAGUES",), "fields": [
        F("SPORTS_LEAGUES", "Leagues", default="nfl,nba,mlb,nhl,epl,ucl", hint="Any of nfl, nba, wnba, mlb, nhl, mls, epl, ucl, laliga, bundesliga, seriea, ligue1. Blank turns scores off."),
    ]},
    {"id": "plex", "title": "Plex", "about": "What landed in your library, and what is playing.", "needs": ("PLEX_URL", "PLEX_TOKEN"), "fields": [
        F("PLEX_URL", "Address", "url", placeholder="http://192.168.1.10:32400"),
        F("PLEX_TOKEN", "Token", "secret"),
    ]},
    {"id": "sonarr", "title": "Sonarr", "about": "Episodes coming up.", "needs": ("SONARR_URL", "SONARR_KEY"), "fields": [
        F("SONARR_URL", "Address", "url", placeholder="http://192.168.1.10:8989"),
        F("SONARR_KEY", "API key", "secret"),
    ]},
    {"id": "radarr", "title": "Radarr", "about": "Films coming up.", "needs": ("RADARR_URL", "RADARR_KEY"), "fields": [
        F("RADARR_URL", "Address", "url", placeholder="http://192.168.1.10:7878"),
        F("RADARR_KEY", "API key", "secret"),
    ]},
    {"id": "seerr", "title": "Seerr", "about": "How many requests are waiting.", "needs": ("SEERR_URL", "SEERR_KEY"), "fields": [
        F("SEERR_URL", "Address", "url", placeholder="http://192.168.1.10:5055"),
        F("SEERR_KEY", "API key", "secret"),
    ]},
    {"id": "proxmox", "title": "Proxmox", "about": "CPU, memory, disks, backups and every container.", "needs": ("PVE_URL", "PVE_TOKEN"), "fields": [
        F("PVE_URL", "API address", "url", placeholder="https://192.168.1.2:8006/api2/json"),
        F("PVE_TOKEN", "API token", "secret", hint="user@pve!name=uuid. Give it the PVEAuditor role and nothing more."),
        F("PVE_NODE", "Node", default="pve"),
        F("PVE_ROLE", "What it runs", default="Containers"),
        F("PVE_INSECURE", "Accept a self-signed certificate", "bool", False, "Most home Proxmox boxes have one. The token then travels without proof of who is answering, so use this on your own network only."),
    ]},
    {"id": "hosts", "title": "Other machines", "about": "Any Linux box, read over SSH with a key that can only run the stats script.", "needs": ("HOSTS",), "fields": [
        F("HOSTS", "Machines", "rows", [], "See agent/stats.sh for how to lock the key to that one script.", columns=[
            COL("name", "Name", placeholder="NAS"), COL("role", "What it runs", placeholder="Backups"), COL("target", "SSH login", pattern=SSH_TARGET, placeholder="stats@192.168.1.20")]),
        F("PAPER_SSH_KEY", "Private key file", default=str(Path(os.environ.get("PAPER_DATA", "/var/lib/paper")) / "ssh_key"), hint="A path inside the container. Mount the key there; it is never stored in settings."),
    ]},
    {"id": "services", "title": "Service checks", "about": "Each address is tried every minute: up, down and how fast.", "needs": ("PROBES",), "fields": [
        F("PROBES", "Services", "rows", [], "Services in the same group sit together on the page.", columns=[
            COL("group", "Group", placeholder="At home"), COL("name", "Name", placeholder="Router"), COL("url", "Address", "url", placeholder="http://192.168.1.1/")]),
    ]},
    {"id": "mail", "title": "Mail", "about": "Reads Microsoft 365 mailboxes and lifts what needs you. It never sends, moves or marks anything. Add an AI provider and it sorts what the rules can't, up to 400 messages a day.", "needs": ("MAIL_TENANT", "MAIL_CLIENT_ID", "MAIL_CLIENT_SECRET", "MAILBOXES"), "fields": [
        F("MAIL_TENANT", "Tenant ID"),
        F("MAIL_CLIENT_ID", "App client ID"),
        F("MAIL_CLIENT_SECRET", "App client secret", "secret", hint="Give the app Mail.Read and nothing more."),
        F("MAILBOXES", "Mailboxes", "rows", [], columns=[COL("address", "Address", pattern=MAILBOX, placeholder="you@example.com"), COL("label", "Label", placeholder="Support")]),
        F("MAIL_ABOUT", "Who the mail is for", default="the owner of a small online business", hint="Finishes the sentence: You sort incoming email for..."),
    ]},
    {"id": "money", "title": "Money", "about": "Sales minus costs, from any address that returns the money report.", "needs": ("MONEY_URL",), "fields": [
        F("MONEY_URL", "Report address", "url", hint="docs/money-feed.md shows the JSON to return."),
        F("FEED_TOKEN", "Bearer token", "secret"),
        F("PRODUCTS", "Products", "rows", [], "The key is the site value in the report.", columns=[
            COL("key", "Key", pattern=SLUG, placeholder="shop"), COL("name", "Name", placeholder="My Shop"), COL("host", "Web address", placeholder="shop.example.com")]),
        F("EARLIER", "Income from before the report", "rows", [], "Counted in all-time income only.", columns=[
            COL("label", "Label", placeholder="First invoice"), COL("day", "Date", "date"), COL("amount", "Amount", "money", placeholder="100.00")]),
    ]},
    {"id": "ledger", "title": "AI ledger", "about": "Every agent's tokens by day, from a Commons hub, worth counted at list price even when a plan covers them. The paper counts its own AI calls either way.", "needs": ("COMMONS_URL",), "fields": [
        F("COMMONS_URL", "Commons dashboard address", "url", placeholder="http://192.168.1.10:8771"),
        F("COMMONS_TOKEN", "Dashboard token", "secret", hint="Only if your dashboard asks for one. A viewer token is enough."),
    ]},
    {"id": "bill", "title": "Anthropic bill", "about": "What Anthropic really charged by day and model, in place of the paper's estimates. It takes an Admin key, and an ordinary key can't read this.", "needs": ("ANTHROPIC_ADMIN_KEY",), "fields": [
        F("ANTHROPIC_ADMIN_KEY", "Admin API key", "secret", hint="Console, Settings, Admin keys. It can manage your organization, so keep it here and nowhere else."),
    ]},
    {"id": "openrouter", "title": "OpenRouter", "about": "What your OpenRouter account spends each day, counted from the day you add it. It has a running total and no history, so a day is how far the total moved.", "needs": ("OPENROUTER_KEY",), "fields": [
        F("OPENROUTER_KEY", "API key", "secret", hint="Any key on the account. The paper only reads the total."),
    ]},
    {"id": "livekit", "title": "LiveKit", "about": "Call minutes and data by day, and what they would cost with nothing included. Needs the Scale plan or higher.", "needs": ("LIVEKIT_PROJECT", "LIVEKIT_TOKEN"), "fields": [
        F("LIVEKIT_PROJECT", "Project ID", placeholder="p_abc123", hint="The part of your LiveKit dashboard address that starts with p_.", guards=True),
        F("LIVEKIT_TOKEN", "List-only token", "secret", hint="Run: lk token create --list --valid-for 8760h. It can list sessions and nothing else, so your API secret stays where it is."),
    ]},
    {"id": "notify", "title": "Alerts", "about": "When something serious goes wrong, this sends you one message, and stays quiet until something new does. Works with ntfy or any address that takes a POST.", "needs": ("NOTIFY_URL",), "fields": [
        F("NOTIFY_URL", "Alert address", "url", placeholder="https://ntfy.sh/your-private-topic"),
        F("NOTIFY_TOKEN", "Bearer token", "secret", hint="Only if your address asks for one."),
    ]},
    {"id": "twilio", "title": "Twilio", "about": "Fills in last month's Twilio bill on the Business desk.", "needs": ("TWILIO_ACCOUNT", "TWILIO_KEY", "TWILIO_SECRET"), "fields": [
        F("TWILIO_ACCOUNT", "Account SID", placeholder="AC...", guards=True),
        F("TWILIO_KEY", "API key SID", placeholder="SK...", hint="An API key, so your auth token stays where it is. Console, Account, API keys.", guards=True),
        F("TWILIO_SECRET", "API key secret", "secret"),
    ]},
    {"id": "deepgram", "title": "Deepgram", "about": "Fills in what Deepgram cost over the last 30 days on the Business desk.", "needs": ("DEEPGRAM_KEY",), "fields": [
        F("DEEPGRAM_KEY", "API key", "secret", hint="It has to be able to read billing. A key that can only transcribe is refused."),
    ]},
    {"id": "ai", "title": "AI provider", "about": "Add one and you can ask the paper questions, set it up by describing what you want, and have your mail sorted.", "needs": (), "fields": [
        F("AI_PROVIDER", "Provider", "select", "anthropic", options=tuple((v, label) for v, label, _ in PROVIDERS), guards=True),
        F("AI_KEY", "API key", "secret", hint="Not needed for Ollama or LM Studio."),
        F("AI_MODEL", "Model", placeholder="claude-opus-5-5", hint="Its exact name at your provider. For Anthropic, blank means claude-opus-5-5."),
        F("AI_URL", "Address", "url", hint="Only if yours differs from the provider's. In Docker, a model on the host is at http://host.docker.internal:11434/v1."),
    ]},
    {"id": "access", "title": "AI access", "about": "Let Claude, ChatGPT, Cursor or any agent read this paper, over MCP or plain HTTP. News and world are shared. The rest stays private until you tick it. Headlines are strangers' words too, so don't give a token to an agent that acts without asking you.", "needs": (), "fields": [
        F("AI_SHARE_MONEY", "Share money", "bool", False),
        F("AI_SHARE_MEDIA", "Share media", "bool", False),
        F("AI_SHARE_SYSTEMS", "Share systems", "bool", False),
        F("AI_SHARE_MAIL", "Share mail", "bool", False, "Senders, subjects and why each one matters, never full text. Anything an AI reads from strangers can try to steer it, so share this only with an AI you trust not to act on it."),
    ]},
    {"id": "brief", "title": "Newsletter", "about": "A daily brief on the Tech desk, from a site built the way this one expects. Most papers leave this blank.", "needs": ("BRIEF_URL",), "fields": [
        F("BRIEF_URL", "Site address", "url", hint="An archive at /n/ linking to issues, each one article element with h2 sections."),
    ]},
]
FIELDS = {f["key"]: f for s in SECTIONS for f in s["fields"]}
BY_ID = {s["id"]: s for s in SECTIONS}

_lock = threading.Lock()
_saved = {}
_path = None


def load(path):
    """A file that won't parse stops the paper here, rather than being overwritten by the next save."""
    global _path, _saved
    _path = Path(path)
    _saved = json.loads(_path.read_text()) if _path.exists() else {}


def _write(data):
    _path.parent.mkdir(parents=True, exist_ok=True)
    tmp = _path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)  # a leftover tmp file would otherwise keep its old mode
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, _path)


def from_env(key):
    return os.environ.get(key) or None


def parsed_env(field, raw):
    if field["kind"] == "bool":
        return raw.lower() in ("1", "true", "yes", "on")
    if field["kind"] == "rows":
        return json.loads(raw)
    return raw


def get(key):
    field = FIELDS[key]
    raw = from_env(key)
    if raw is not None:
        return parsed_env(field, raw)
    value = _saved.get(key)
    return field["default"] if value in (None, "") else value


def enabled(section):
    return all(get(k) for k in BY_ID[section]["needs"])


def clean_url(label, value):
    if not value:
        return ""
    p = urllib.parse.urlsplit(value)
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
        raise ValueError(f"{label} needs a full http or https address, with no password in it.")
    return value.rstrip("/")


def clean_date(label, value):
    if value:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"{label} needs a date like 2026-10-31.") from None
    return value


def clean_cell(column, value):
    """Trust boundary: one table cell from the settings page."""
    label = column["label"]
    if not isinstance(value, str) or len(value) > 500:
        raise ValueError(f"{label} is too long.")
    value = value.strip()
    if column["kind"] == "url":
        return clean_url(label, value)
    if column["kind"] == "date":
        return clean_date(label, value)
    if column["kind"] == "money" and value and not re.fullmatch(r"\d{1,9}(\.\d{1,2})?", value):
        raise ValueError(f"{label} needs an amount like 12.50.")
    if column["kind"] == "qty" and value and not re.fullmatch(r"\d{1,12}(\.\d{1,8})?", value):
        raise ValueError(f"{label} needs a number like 12.5.")
    if column["options"] and value not in column["options"]:
        raise ValueError(f"{label} needs to be one of the choices.")
    if column["pattern"] and value and not re.fullmatch(column["pattern"], value):
        raise ValueError(f"{label} does not look right: {value[:40]}")
    return value


def clean(field, value):
    """Trust boundary: one value from the settings page. Raises ValueError with something the owner can act on."""
    kind, label = field["kind"], field["label"]
    if kind == "bool":
        if type(value) is not bool:
            raise ValueError(f"{label} must be on or off.")
        return value
    if kind == "rows":
        if not isinstance(value, list) or len(value) > 200 or not all(isinstance(r, dict) for r in value):
            raise ValueError(f"{label} must be a list of up to 200 rows.")
        rows = [{c["key"]: clean_cell(c, r.get(c["key"], "")) for c in field["columns"]} for r in value]
        rows = [r for r in rows if any(r.values())]
        for r in rows:
            missing = [c["label"] for c in field["columns"] if c["kind"] != "select" and not r[c["key"]] and c["key"] not in ("role", "label", "host", "shares", "buy")]
            if missing:
                raise ValueError(f"{label}: a row is missing {missing[0].lower()}.")
        return rows
    if not isinstance(value, str) or len(value) > 2000:
        raise ValueError(f"{label} is too long.")
    value = value.strip()
    if kind == "url":
        return clean_url(label, value)
    if kind == "date":
        return clean_date(label, value)
    if kind in ("choice", "select") and value not in [v for v, _ in field["options"]]:
        raise ValueError(f"{label} needs to be one of the choices.")
    if kind == "tz":
        try:
            ZoneInfo(value)
        except (KeyError, ValueError, OSError):
            raise ValueError(f"{value[:40]} is not a time zone. Try one like America/New_York.") from None
    return value


def update(values):
    """Saves a set of fields and returns the secrets it had to drop. A blank secret keeps the saved one; None clears it.

    A saved secret only ever goes to the address it was saved with. Change the address and the secret must be typed
    again, so a stolen session can't point a connection at another host and collect the token.
    """
    global _saved
    if not isinstance(values, dict):
        raise ValueError("Nothing to save.")
    with _lock:
        fresh = dict(_saved)
        typed = set()
        for key, value in values.items():
            field = FIELDS.get(key)
            if not field:
                raise ValueError("That is not a setting.")
            if from_env(key):
                raise ValueError(f"{field['label']} is set by the environment, so change it there.")
            if field["kind"] != "secret":
                fresh[key] = clean(field, value)
            elif value is None:
                fresh.pop(key, None)
            elif value != "":
                fresh[key] = clean(field, value)
                typed.add(key)
        dropped = []
        for section in SECTIONS:
            urls = [f["key"] for f in section["fields"] if f["kind"] == "url" or f["guards"]]
            was = lambda k, d: d.get(k) or FIELDS[k]["default"]
            weakened = section["id"] == "proxmox" and fresh.get("PVE_INSECURE") and not _saved.get("PVE_INSECURE")  # no certificate check means no proof of who gets the token
            if not weakened and not any(was(k, fresh) != was(k, _saved) for k in urls):
                continue
            for f in section["fields"]:
                if f["kind"] == "secret" and f["key"] not in typed:
                    if from_env(f["key"]):
                        raise ValueError(f"{section['title']}: this can't change while its secret is set by the environment.")
                    if fresh.pop(f["key"], None):
                        dropped.append(f["key"])
        _write(fresh)
        _saved = fresh  # in one step: a reader in between would see every setting back at its default
    return dropped


def view():
    """What the settings page may see. Keep this the only thing that describes settings to the outside."""
    out = []
    for section in SECTIONS:
        fields = []
        for f in section["fields"]:
            item = {k: f[k] for k in ("key", "label", "kind", "hint", "placeholder", "columns", "options")}
            item["locked"] = bool(from_env(f["key"]))
            if f["kind"] == "secret":
                item["set"] = bool(get(f["key"]))
            else:
                item["value"] = get(f["key"])
            fields.append(item)
        out.append({"id": section["id"], "title": section["title"], "about": section["about"], "on": enabled(section["id"]), "fields": fields})
    return out


def auth_record():
    return _saved.get("_auth")


def _set_record(name, value):
    with _lock:
        fresh = {**_saved, name: value}
        _write(fresh)
        _saved.update(fresh)


def set_auth(record):
    _set_record("_auth", record)


def token_record():
    return _saved.get("_ai_token")


def set_token(digest):
    _set_record("_ai_token", digest)
