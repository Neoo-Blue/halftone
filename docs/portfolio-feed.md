# The portfolio address

The Investments page prices what you type in. If a broker or a script of yours knows your holdings already, point the paper at it instead. It reads one JSON document from any address you like, every five minutes, and adds those holdings to the ones you typed.

The paper asks with `Authorization: Bearer <token>` when you set a token.

```json
{
  "positions": [
    { "symbol": "AAPL", "shares": 10, "buy": 150.25 },
    { "symbol": "BTC-USD", "shares": 0.25, "buy": 42000, "tape": false }
  ]
}
```

| Field | Meaning |
|---|---|
| `symbol` | The symbol as Yahoo Finance writes it: `AAPL`, `VOO`, `BTC-USD`, `VOD.L` |
| `shares` | How many you hold. Zero or blank only watches it |
| `buy` | What you paid per share. Optional, and without it the holding counts toward the value but not the gain |
| `tape` | `false` keeps it off the tape. Optional |

The same symbol from two places adds up, and its buy price becomes the average. Only the numbers are used: the paper prices everything itself. Holdings are never shared with an AI, and Ask can't see them.
