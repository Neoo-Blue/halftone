# The money report

The Business desk answers one question: are you making money? It reads one JSON document, from any address you like, every five minutes. Write a small script, a serverless function or a scheduled export that returns this shape, put its address in Settings under Money, and add a bearer token if you want one.

The paper asks with `Authorization: Bearer <token>`.

```json
{
  "now": 1793468000,
  "sales": [
    { "site": "shop", "cents": 1900, "renewal": 0, "day": "2026-10-30" }
  ],
  "refunds": [
    { "site": "shop", "cents": 1900, "day": "2026-10-30" }
  ],
  "spend": [
    { "day": "2026-10-28", "cents": 967 }
  ],
  "subs": [
    { "site": "shop", "status": "active", "monthly": 1999 }
  ],
  "visitors": [
    { "site": "shop", "day": "2026-10-30", "n": 40 }
  ],
  "abandoned": [
    { "site": "shop", "created": 1793381600 }
  ],
  "older": { "cents": 1000 }
}
```

| Field | Meaning |
|---|---|
| `now` | Unix seconds when the report was made |
| `sales` | Each sale for at least the last 90 days. `renewal` is 1 for a repeat subscription charge, which isn't a new order |
| `refunds` | Each refund, same window |
| `spend` | Money spent on marketing or AI, by day |
| `subs` | Every current subscription. `status` of `trialing` doesn't count as recurring income |
| `visitors` | Real visitors per site per day. Optional, an empty list is fine |
| `abandoned` | Checkouts started and not finished. Optional |
| `older` | Total income from before the sales list starts, for the all-time figure |

`site` matches the Key column under Products in Settings. `day` is `YYYY-MM-DD` in the paper's time zone. Amounts are whole cents.

Everything is required but may be an empty list. Fees are estimated at 2.9% plus 30 cents a sale. Costs you run on live on the Business desk. Connect Twilio or Deepgram in Settings and their bills fill themselves, and Anthropic and OpenRouter come from [AI use](ai-use.md). The rest you enter once. A cost with no amount stays visibly blank instead of counting as zero, and a blank one with a source to connect offers that instead of asking for a number.
