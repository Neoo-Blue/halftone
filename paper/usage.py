"""What AI was used and what it was worth, charged or not.

Every source becomes the same row: who used what on which day, what that is worth at list price, and what was
really charged. A plan or a credit covers the gap between the two. No network here: the server fetches, this counts.
"""
from datetime import date, datetime, timedelta, timezone

# Dollars per million tokens: input, output, cache read. Anthropic's list prices. The longest name that fits wins, so a dated snapshot finds its model.
PRICES = {"claude-fable-5-1": (10, 50, .25), "claude-mythos-5-1": (10, 50, .25), "claude-fable-5": (10, 50, 1), "claude-mythos-5": (10, 50, 1), "claude-opus-5-5": (4, 20, .2), "claude-opus-5": (5, 25, .5), "claude-opus-4": (5, 25, .5),
          "claude-sonnet-5": (2, 10, .2), "claude-sonnet-4": (3, 15, .3), "claude-haiku-5-5": (.1, .5, .01), "claude-haiku-4-5": (1, 5, .1), "claude-3-5-haiku": (.8, 4, .08)}
CACHE_WRITE = 1.25  # times input, for the five-minute cache. ponytail: the ledger doesn't split it from the dearer one-hour cache
# LiveKit Cloud's Scale prices past what a plan includes. Worth means what the use would cost with nothing included.
LIVEKIT_MINUTE, LIVEKIT_AGENT_MINUTE, LIVEKIT_GB = .0004, .01, .1
TOKEN_FIELDS = ("tokens_in", "tokens_out", "cache_read", "cache_write")
PLANS = {"claude-code": "Claude Code", "claude-code subagent": "Claude Code", "grok bridge": "Grok Build", "antigravity bridge": "Antigravity"}
ANTHROPIC = "Anthropic bill"
MAX_ROWS = 2000  # a page of the ledger holds a few dozen. A hub can't fill the database through this
OWN_API_CALLS = ("Commons", "This paper")


def amount(v):
    """A number from someone else's answer."""
    try:
        v = float(v or 0)
    except OverflowError:
        raise ValueError("not a sane amount") from None
    if not 0 <= v < 1e15:  # refuses NaN and infinity too
        raise ValueError("not a sane amount")
    return v


def day_of(v):
    """A real date, and not a future one, which would push real days off the page."""
    day = date.fromisoformat(str(v)[:10])
    if day > datetime.now(timezone.utc).date() + timedelta(days=1):
        raise ValueError("a day from the future")
    return day.isoformat()


def short_model(model):
    return str(model or "unknown").removeprefix("anthropic/")[:60]


def worth(model, tokens_in=0, tokens_out=0, cache_read=0, cache_write=0):
    """Dollars at list price, or None when this model has no price here, which is not the same as free."""
    name = short_model(model)
    base = max((p for p in PRICES if name.startswith(p)), key=len, default=None)
    if not base:
        return None
    i, o, r = PRICES[base]
    return (tokens_in * i + tokens_out * o + cache_read * r + cache_write * i * CACHE_WRITE) / 1e6


def _totals(rows):
    out = {}
    for r in rows:
        e = out.setdefault((str(r.get("agent"))[:40], str(r.get("source") or "")[:40], short_model(r.get("model"))), dict.fromkeys((*TOKEN_FIELDS, "cost"), 0.0))
        for f in e:
            e[f] += amount(r.get(f))
    return out


def _ledger_row(day, key, e):
    """The ledger's own dollars are only a fallback: they age badly when prices change. Commons calling a provider with a key is real money. The rest ran on a plan."""
    agent, source, model = key
    value = worth(model, *(e[f] for f in TOKEN_FIELDS))
    value = e["cost"] or None if value is None else value
    api, route = agent.startswith("provider:"), agent.removeprefix("provider:")
    who = ("Commons" if route == "anthropic" else f"Commons, {route}") if api else PLANS.get(source, agent[:1].upper() + agent[1:])
    return {"day": day, "who": who, "model": model, "qty": sum(e[f] for f in TOKEN_FIELDS), "unit": "tokens", "worth": value, "charged": (value or 0) if api else 0}


def ledger_rows(pages):
    """Pages are the ledger's answers for the last 1, 2, 3... days. Its rows are totals, so one day is one page minus the page before. Pass a generator, so a page can go once it's counted."""
    out, before = [], {}
    for n, page in enumerate(pages, 1):
        if len(page["days"]) != n or len(page["rows"]) > MAX_ROWS:
            raise ValueError("not the ledger's shape")
        day, now = day_of(page["days"][0]), _totals(page["rows"])
        for key, e in now.items():
            left = {f: max(0, v - before.get(key, {}).get(f, 0)) for f, v in e.items()}
            if any(left.values()):
                out.append(_ledger_row(day, key, left))
        before = now
    return out


def bill_rows(data):
    """Anthropic's analytics rows, in fractional cents: what it charged before any credit, and the same use at list price."""
    return [{"day": day_of(r["starting_at"]), "who": ANTHROPIC, "model": short_model((r.get("group") or {}).get("model") or "other"), "qty": 0, "unit": "tokens",
             "worth": amount(r["cost"].get("list_amount") or r["cost"].get("amount")) / 100, "charged": amount(r["cost"].get("amount")) / 100} for r in data]


def epoch(v):
    """LiveKit's times are Protobuf timestamps, which reach JSON as text or as seconds."""
    if isinstance(v, dict):
        return amount(v.get("seconds"))
    return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()


def livekit_session(session, created):
    """One finished session as (day, minutes, agent minutes, bytes). Agents join under LiveKit's agent- prefix, and only their time costs more."""
    agents = sum(max(0, epoch(p["leftAt"]) - epoch(p["joinedAt"])) for p in session.get("participants") or [] if str(p.get("participantIdentity")).startswith("agent-") and p.get("leftAt"))
    day = day_of(datetime.fromtimestamp(epoch(created), timezone.utc).date())
    return day, amount(session.get("connectionMinutes")), agents / 60, amount(session.get("bandwidth"))


def livekit_rows(days):
    return [{"day": d, "who": "LiveKit", "model": "calls", "qty": minutes, "unit": "minutes", "worth": minutes * LIVEKIT_MINUTE + agents * LIVEKIT_AGENT_MINUTE + sent / 1e9 * LIVEKIT_GB, "charged": 0} for d, minutes, agents, sent in days]


def report(rows, today):
    """Newest day last. The real figure wins over an estimate of the same calls: Anthropic's bill on a finished day, OpenRouter's total on a day it moved.
    Today's bill is still partial, so today keeps the estimates. Sources are told apart by where a row came from, never by a name a hub could send."""
    billed = {r["day"] for r in rows if r["source"] == "bill" and r["day"] < today}
    routed = {r["day"] for r in rows if r["source"] == "openrouter"}
    days = {}
    for r in rows:
        if r["source"] == "bill" and r["day"] >= today:
            continue
        d = days.setdefault(r["day"], {"day": r["day"], "worth": 0.0, "charged": 0.0, "tokens": 0, "rows": []})
        d["tokens"] += r["qty"] if r["unit"] == "tokens" else 0
        if (r["day"] in billed and r["who"] in OWN_API_CALLS and r["model"].startswith("claude")) or (r["day"] in routed and r["who"].endswith(", openrouter")):
            continue
        d["worth"] += r["worth"] or 0
        d["charged"] += r["charged"] or 0
        d["rows"].append({k: r[k] for k in ("who", "model", "qty", "unit", "worth", "charged")})
    for d in days.values():
        d["rows"] = sorted(d["rows"], key=lambda r: -(r["worth"] or 0))[:100]
    out = [days[k] for k in sorted(days)][-90:]
    return {"days": out, "unpriced": sorted({f"{r['who']}, {r['model']}" for d in out for r in d["rows"] if r["worth"] is None})[:20]}


def glance(rep, today):
    """What the front page needs: the last whole day, thirty days of columns, and who used the most."""
    days = rep.get("days") or []
    done, month, who = [d for d in days if d["day"] < today], days[-30:], {}
    for d in month:
        for r in d["rows"]:
            who[r["who"]] = who.get(r["who"], 0) + (r["worth"] or 0)
    last = done[-1] if done else None
    return {"last": {k: last[k] for k in ("day", "worth", "charged", "tokens")} if last else None, "days": [{k: d[k] for k in ("day", "worth", "charged")} for d in month], "month": sum(d["worth"] for d in month), "charged": sum(d["charged"] for d in month), "who": sorted(who.items(), key=lambda kv: -kv[1])[:6]}
