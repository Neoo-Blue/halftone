# AI

There are two separate things here: the paper using an AI, and an AI using the paper.

## The paper using an AI

Add a provider under **AI provider** in Settings. That turns on three things:

- **Ask**: a page in the paper for questions about today's edition and everything you've connected.
- **Set it up by asking**: describe what you want at the top of Settings and it proposes the changes. Nothing changes until you press Apply.
- **Mail sorting**: whatever the rules can't decide, up to 400 messages a day.

| Provider | Key | Model |
|---|---|---|
| Anthropic | Yes | Blank means `claude-opus-5-5`. Mail sorting uses `claude-haiku-5-5` |
| OpenAI, Google Gemini, xAI Grok, OpenRouter, Groq, Mistral, DeepSeek, Together | Yes | Its exact name at that provider |
| Ollama, LM Studio | No | The model you've loaded |
| Anything OpenAI-compatible | If it needs one | Set its Address too, ending before `/chat/completions` |

In Docker, a model on your own machine isn't at `localhost`. Use `http://host.docker.internal:11434/v1` as the Address. On Linux, add `extra_hosts: ["host.docker.internal:host-gateway"]` to `compose.yaml`.

Ask and Set it up by asking share a limit of 200 uses a day, so a mistake can't run up a bill.

## An AI using the paper

Make a token under **AI access** in Settings. It's shown once. Then any AI that speaks MCP can connect:

```
https://your-paper.example/mcp
Authorization: Bearer paper_...
```

Claude Code:

```sh
claude mcp add --transport http paper https://your-paper.example/mcp --header "Authorization: Bearer paper_..."
```

Cursor, in `.cursor/mcp.json`:

```json
{ "mcpServers": { "paper": { "url": "https://your-paper.example/mcp", "headers": { "Authorization": "Bearer paper_..." } } } }
```

Anything else can use plain HTTP, including a ChatGPT action or a script:

```sh
curl -H "Authorization: Bearer paper_..." 'https://your-paper.example/api/ai/news?query=flood&limit=5'
```

| Tool | REST | Shared by default |
|---|---|---|
| `news` (`query`, `desk`, `limit`) | `/api/ai/news` | Yes |
| `world` | `/api/ai/world` | Yes |
| `money` | `/api/ai/money` | No |
| `media` | `/api/ai/media` | No |
| `systems` | `/api/ai/systems` | No, and it never includes addresses |
| `mail` | `/api/ai/mail` | No, and it only ever has senders, subjects and a one-line reason |

Everything here is read only. No token can change a setting or read a key. An AI has to be able to reach the address, so a cloud AI needs the paper on the internet, behind HTTPS.

## Why Ask can't act, and Configure can't read

The paper is full of text written by strangers: headlines, articles, your mail. Any of it can contain instructions aimed at an AI. So the two jobs never meet.

| | Sees strangers' text | Can change anything |
|---|---|---|
| Ask | Yes | No. Its answer is printed as plain text |
| Set it up by asking | No, only your request and your settings | Only by proposing, and you press Apply |
| AI clients over MCP or REST | Yes | No |

Set it up by asking also can't touch keys, the AI settings, who may read the paper, or file paths. Whatever it proposes goes through the same checks as the settings page. If you connect another AI over MCP, what that AI can do with what it reads is up to that AI, which is why mail is off until you share it.

Anything you type into Ask or Set it up by asking goes to your AI provider, along with the parts of the paper it needs. With Ask, that can include mail subjects and money. Use Ollama or LM Studio to keep it on your own machine.
