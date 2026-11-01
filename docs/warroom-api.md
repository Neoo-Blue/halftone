# The WARROOM public API

[WARROOM](https://war.wakxi.com) is a live map of the world's conflicts, economic shocks and natural hazards. Its read API is free, needs no key, and is what this paper's World desk runs on. You can use it for anything of your own.

```
https://war.wakxi.com/api/v1
```

```sh
curl https://war.wakxi.com/api/v1
curl 'https://war.wakxi.com/api/v1/events?limit=5&min_severity=0.6'
```

## Endpoints

All are `GET`.

| Path | What it returns | Fresh for |
|---|---|---|
| `/` | This list, the limits and the license | 5 min |
| `/state` | Escalation index, theaters, map pins, tracked asset counts | 1 min |
| `/events` | The event feed, newest first | 1 min |
| `/events/{id}` | One event, its sources and any analyst note | 5 min |
| `/events/{id}/nearby` | Reports close to it in space and time | 5 min |
| `/threads/{id}` | One developing situation and its events | 5 min |
| `/assessment/latest` | The latest machine-written assessment and forecasts | 5 min |
| `/alerts` | Conflicts that have newly appeared or escalated | 1 min |
| `/hazards` | Natural hazards, with a count by alert level | 5 min |
| `/hazards/{id}` | One hazard | 5 min |
| `/spaceweather` | Geomagnetic conditions and forecast | 5 min |
| `/intel` | Analyst notes | 5 min |
| `/theaters/{id}/history` | A theater's timeline from day one, with a source on every entry | 5 min |
| `/theaters/{id}/accounts` | Who is reporting a theater, what only one side is saying, and each side's account | 1 min |

`/events` takes `limit` (1 to 300, default 100), `min_severity` (0 to 1), `theater`, `domain` (`kinetic` or `economic`), `since` (unix seconds, rounded down to the minute) and `cursor` (from `next_cursor`).

`/intel` takes `scope` (`theater`, `thread` or `global`), `scope_id`, which needs a `scope`, and `limit` (1 to 20).

The parameters listed here are the only ones that do anything. Others are ignored.

Every event says who is saying it. `basis` is one of `measured` (an instrument recorded it), `record` (an official document), `both` (opposing sides of the fight report it), `outside` (a voice outside the fight does), `one_side` (only one side does, among the sources WARROOM reads) or `unplaced` (a voice nobody has placed). `sides` lists the camps that spoke, such as `["RU", "UA"]`, and `voice` names who filed it. `one_side` does not mean false. `/events/{id}` adds `who`, with every voice behind the report and the count across its story.

Times are unix seconds, UTC. Every answer carries `meta.generated_at` and `meta.license`. Lists look like this:

```json
{ "items": [], "next_cursor": null, "meta": { "generated_at": 1793485138, "license": "..." } }
```

An event:

```json
{
  "id": "4f1c9a27b3e05d18a61c0e72d94b3f65",
  "ts": 1793484729,
  "title": "Headline in English",
  "summary": "Summary, when there is one",
  "domain": "kinetic",
  "category": "airstrike",
  "severity": 0.62,
  "confidence": 0.7,
  "place": "City", "admin1": "Region", "country": "XX",
  "lat": 0.0, "lon": 0.0,
  "theater": "theater_id",
  "thread_id": "thr:1a2b3c4d5e6f7a8b9c0d1e2f",
  "actor_a": null, "actor_b": null,
  "fatalities": null,
  "source": "gdelt_events",
  "source_url": "https://publisher.example/story",
  "title_source": "headline",
  "lang": "en"
}
```

Errors look like `{"ok": false, "ts": 1793485138, "error": {"code": "not_found", "message": "no such record"}}`.

## Limits

30 requests in a burst, then 75 a minute, per address (per /64 on IPv6). Past that you get `429` with a `Retry-After` header. Answers are cached on the server for the times above, so polling faster than that returns the same bytes and spends your allowance.

If a refresh fails or the server is busy you get the last good copy, up to an hour old, so check `meta.generated_at`. With no copy to give you get `502`, or `503` with `Retry-After`.

Any site may call it from a browser: `Access-Control-Allow-Origin` is `*`.

## What it leaves out

Price series, ACLED data and vessel positions are for reading on WARROOM itself, not for passing on, so they aren't here. Neither are events from those feeds, or chokepoint risk summaries, which quote them. That is why the paper's Markets table only appears if you run your own WARROOM.

Assessments and analyst notes are written by a machine with market and shipping data in view, so their text can mention a move or a traffic figure. It is commentary, not a data feed.

## Using the data

Free to use with attribution to WARROOM (war.wakxi.com). Headlines, summaries and links belong to their publishers. The data comes from GDELT, USGS, NASA FIRMS, NASA EONET, GDACS, NOAA SWPC, ReliefWeb, OFAC, the Federal Register and public news and Telegram channels. Asset counts come from CelesTrak, OpenSky, ADS-B and AIS feeds.

Reports are unverified and assessments are written by a machine. Do not use them for safety, targeting or trading decisions. There is no warranty, and no promise it stays up.
