# AI use

The AI use desk answers two questions for every day: what was all that AI worth, and what did it really cost you? A plan or a credit covers the gap, so the desk still shows the value of what a subscription hides.

The paper counts its own AI calls as soon as you add a provider. Each of these adds more, and each is optional. Add them under Settings.

| Source | What it adds | What it needs |
|---|---|---|
| AI ledger | Every agent's tokens by day, from a [Commons](https://github.com/Neoo-Blue/commons-memory) hub | The dashboard address, and a viewer token if your dashboard asks for one |
| Anthropic bill | What Anthropic really charged, by day and model | An Admin API key |
| OpenRouter | What the account spent each day | Any API key on the account |
| LiveKit | Call minutes and data by day | Your project ID and a list-only token, on the Scale plan or higher |

## How it counts

**Worth** is what the same use would cost at public list prices. For Claude models it comes from token counts and the paper's own price table in `paper/usage.py`, so it stays right when a source's stored dollars don't. A model with no price there shows its tokens and "No price", which is not the same as free.

**Charged** is what left your account. With the Anthropic bill connected, that is Anthropic's own figure, before any credit. It replaces the paper's estimates of the same API calls on every finished day. Today keeps the estimates, because the bill is still partial. Without it, Charged is the paper's estimate of its own calls and of Commons' API calls. Use through a subscription such as Claude Code counts as worth, with nothing charged.

**OpenRouter** gives a running total for the account and no history, so a day is how far that total moved, counted from the day you add it. It covers every key on the account, and all of it counts as charged, because the account is prepaid. Calls the paper or Commons made through OpenRouter are already in that total, so on those days their estimates step aside.

**LiveKit** worth is what the use would cost with nothing included: WebRTC minutes, data sent, and agent minutes for participants under LiveKit's `agent-` prefix. LiveKit lists sessions for only seven days and has no daily total, so the paper reads each finished session once and keeps the numbers. Nothing LiveKit charges is counted as charged, because the API doesn't report it.

Days run midnight to midnight UTC, the same as the ledger. Cache writes are priced at the five-minute rate, because the ledger doesn't separate them from the dearer one-hour cache, so heavy one-hour caching reads a little low. Haiku 5.5 is priced at its rate for prompts up to 100K tokens.

## Keys

- The Admin key can manage your Anthropic organization. It goes only to `api.anthropic.com`, and only to read the cost report.
- The LiveKit token is not your API secret. Make one that can only list sessions, so the secret stays where it is:

  ```
  lk token create --list --valid-for 8760h
  ```

  It runs out after a year. Make a new one then.
