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

DESKS = ("world", "us", "business", "tech", "ai", "security", "science")
SLUG, MAILBOX = r"[a-z]{1,40}", r"[^@\s]+@[^@\s]+\.[^@\s]+"
SSH_TARGET = r"[A-Za-z0-9._][A-Za-z0-9._-]*@[A-Za-z0-9.:_-]+"  # can't start with a dash, or ssh reads it as an option


def F(key, label, kind="text", default="", hint="", placeholder="", columns=None):
    return {"key": key, "label": label, "kind": kind, "default": default, "hint": hint, "placeholder": placeholder, "columns": columns}


def COL(key, label, kind="text", pattern=None, options=None, placeholder=""):
    return {"key": key, "label": label, "kind": kind, "pattern": pattern, "options": options, "placeholder": placeholder}


SECTIONS = [
    {"id": "paper", "title": "The paper", "about": "What it is called and whose day it follows.", "needs": (), "fields": [
        F("PAPER_NAME", "Name", default="The Morning Paper"),
        F("PAPER_TZ", "Time zone", "tz", "UTC", "A name like America/New_York. It sets the date on the masthead and the days in the money report."),
        F("PAPER_SINCE", "First edition", "date", hint="Each day's number counts from here. Blank counts from the day you started the paper."),
    ]},
    {"id": "world", "title": "World", "about": "The globe, the conflict desk and the odds. Works from the first minute.", "needs": ("WARROOM_URL",), "fields": [
        F("WARROOM_URL", "WARROOM address", "url", "https://war.wakxi.com/api/v1", "The free public API. Change it only if you run your own WARROOM."),
    ]},
    {"id": "news", "title": "News", "about": "57 outlets are already on the wire. Add your own here.", "needs": (), "fields": [
        F("EXTRA_FEEDS", "Your feeds", "rows", [], "Any RSS or Atom address.", columns=[
            COL("desk", "Desk", "select", options=DESKS), COL("name", "Outlet", placeholder="Local Times"), COL("url", "Feed address", "url", placeholder="https://example.com/rss.xml")]),
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
    {"id": "mail", "title": "Mail", "about": "Reads Microsoft 365 mailboxes and lifts what needs you. It never sends, moves or marks anything.", "needs": ("MAIL_TENANT", "MAIL_CLIENT_ID", "MAIL_CLIENT_SECRET", "MAILBOXES"), "fields": [
        F("MAIL_TENANT", "Tenant ID"),
        F("MAIL_CLIENT_ID", "App client ID"),
        F("MAIL_CLIENT_SECRET", "App client secret", "secret", hint="Give the app Mail.Read and nothing more."),
        F("MAILBOXES", "Mailboxes", "rows", [], columns=[COL("address", "Address", pattern=MAILBOX, placeholder="you@example.com"), COL("label", "Label", placeholder="Support")]),
        F("ANTHROPIC_API_KEY", "Anthropic API key", "secret", hint="Optional. Sorts what the rules can't, at most 400 messages a day on Claude Haiku. Without it, unsorted mail stays visible as unsorted."),
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
            missing = [c["label"] for c in field["columns"] if c["kind"] != "select" and not r[c["key"]] and c["key"] not in ("role", "label", "host")]
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
            urls = [f["key"] for f in section["fields"] if f["kind"] == "url"]
            weakened = section["id"] == "proxmox" and fresh.get("PVE_INSECURE") and not _saved.get("PVE_INSECURE")  # no certificate check means no proof of who gets the token
            if not weakened and not any(fresh.get(k, "") != _saved.get(k, "") for k in urls):
                continue
            for f in section["fields"]:
                if f["kind"] == "secret" and f["key"] not in typed:
                    if from_env(f["key"]):
                        raise ValueError(f"{section['title']}: this can't change while its secret is set by the environment.")
                    if fresh.pop(f["key"], None):
                        dropped.append(f["key"])
        _write(fresh)
        _saved.clear()
        _saved.update(fresh)
    return dropped


def view():
    """What the settings page may see. Keep this the only thing that describes settings to the outside."""
    out = []
    for section in SECTIONS:
        fields = []
        for f in section["fields"]:
            item = {k: f[k] for k in ("key", "label", "kind", "hint", "placeholder", "columns")}
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


def set_auth(record):
    with _lock:
        fresh = {**_saved, "_auth": record}
        _write(fresh)
        _saved.update(fresh)
