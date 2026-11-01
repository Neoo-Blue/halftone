"""What you hold and how it's doing. No network here: the server fetches prices, this counts."""
import re

from usage import amount, figure

SYMBOL = r"[A-Za-z0-9^][A-Za-z0-9.=^-]{0,14}"
MAX_HOLDINGS = 60


def clean_symbol(v):
    symbol = str(v).strip().upper()
    if not re.fullmatch(SYMBOL, symbol):
        raise ValueError("not a symbol")
    return symbol


def holding(symbol, shares, buy, tape, source):
    return {"symbol": clean_symbol(symbol), "shares": amount(shares), "buy": None if buy in (None, "") else figure(buy), "tape": tape, "source": source}


def typed(rows):
    return [holding(r["symbol"], r.get("shares"), r.get("buy"), r.get("tape") != "no", "typed") for r in rows]


def from_feed(body):
    """Trust boundary: the answer from a broker or portfolio address."""
    if not isinstance(body, dict) or not isinstance(body.get("positions"), list):
        raise ValueError("not a portfolio")
    return [holding(p["symbol"], p.get("shares"), p.get("buy"), p.get("tape") is not False, "feed") for p in body["positions"][:MAX_HOLDINGS]]


def merged(rows):
    """One line per symbol. Two lots of the same stock add up, and the buy price becomes their average."""
    out = {}
    for r in rows:
        e = out.get(r["symbol"])
        if not e:
            out[r["symbol"]] = dict(r)
            continue
        shares, lots = e["shares"] + r["shares"], [x for x in (e, r) if x["shares"]]  # a row that only watches has no price to average
        e["buy"] = None if not lots or any(x["buy"] is None for x in lots) else sum(x["buy"] * x["shares"] for x in lots) / shares
        e["shares"], e["tape"] = shares, e["tape"] or r["tape"]
    return list(out.values())


def report(rows, quotes, rates):
    """Totals in dollars. A holding with no buy price counts toward the value but not the gain, and the report says how many that is."""
    positions = []
    for h in rows:
        q, r = quotes.get(h["symbol"]), {**h, "name": None, "price": None, "pct": None, "currency": None, "value": None, "day": None, "cost": None, "gain": None, "stale": False}
        rate = rates.get(q["currency"]) if q else None
        if q:
            r.update(name=q["name"], price=q["price"], currency=q["currency"], stale=q.get("stale", False), pct=100 * (q["price"] - q["prev"]) / q["prev"] if q["prev"] else None)
        if q and rate and h["shares"]:
            r.update(value=h["shares"] * q["price"] * rate, day=h["shares"] * (q["price"] - q["prev"]) * rate if q["prev"] else None)
            if h["buy"] is not None:
                r.update(cost=h["shares"] * h["buy"] * rate, gain=h["shares"] * (q["price"] - h["buy"]) * rate)
        positions.append(r)
    held = [r for r in positions if r["value"] is not None]
    known = [r for r in held if r["gain"] is not None]
    cost, gain = sum(r["cost"] for r in known), sum(r["gain"] for r in known)
    return {"positions": sorted(positions, key=lambda r: -(r["value"] or 0)), "total": sum(r["value"] for r in held) if held else None, "day": sum(r["day"] or 0 for r in held) if held else None,
            "cost": cost if known else None, "gain": gain if known else None, "gain_pct": 100 * gain / cost if cost >= 1e-12 else None, "no_buy": len(held) - len(known), "no_price": [r["symbol"] for r in positions if r["price"] is None]}


def glance(rep, show_gain):
    return {"total": rep.get("total"), "day": rep.get("day"), "gain": rep.get("gain") if show_gain else None, "gain_pct": rep.get("gain_pct") if show_gain else None,
            "tape": [{"label": r["symbol"], "pct": r["pct"]} for r in rep.get("positions", []) if r["tape"] and r["pct"] is not None]}
