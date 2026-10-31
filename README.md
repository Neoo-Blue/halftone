# Halftone

A private morning newspaper you run yourself. It opens with real news from 57 outlets and a live globe of the world's conflicts, with no keys and no accounts. Connect your mail, money, media and servers and they join the same page.

![The front page, in the Morning theme](docs/img/front-morning.png)

Stories open inside the paper, in a clean reader. The globe, charts and meters are all printed in dots, and there are four themes: Morning, Night, Cobalt and Glass. Call it what you like and set the title in blackletter, like a real masthead, or in one of four other faces.

Every story gets told in its own way. A cyclone draws its track across a map you can scrub through time, with its wind swath, forecast path and the people in its way. An earthquake's shaking spreads from the epicentre. A conflict plays back report by report, and a story shows which outlets carried it and when, and what each one led with. Every map has real place names and a small world in the corner, so you always know where you are.

![A cyclone's track, wind swath and forecast](docs/img/scene.png)

The front page comes from `tools/demo.py`, where every name and number is made up.

## Run it

You need Docker.

```sh
git clone https://github.com/Neoo-Blue/halftone
cd halftone
docker compose up -d
docker compose logs paper
```

The log prints a one-time setup code. Open <http://localhost:8095>, enter the code and choose a password. The first news edition takes about two minutes to arrive, then it refreshes every three.

Everything else is in **Settings**.

To look around first, with no Docker and no setup, run `python3 tools/demo.py` and open <http://127.0.0.1:8096>.

**Kubernetes:** `kubectl apply -f deploy/kubernetes.yaml` gives you a Deployment, a Service and a 2 GB PersistentVolumeClaim. Keep it at one replica on local or block storage, because the database is SQLite. The file's first lines cover the setup code and keys.

**Proxmox:** run Docker in an LXC and use the steps above. Enable nesting on the container.

**Updating:** `docker compose pull && docker compose up -d`. Your settings and history stay in the `paper-data` volume.

## What you can connect

Leave anything blank and it stays off the page.

| Desk | Connect | What you get |
|---|---|---|
| News | Nothing | 57 outlets, grouped by story and ranked by how many carry it. Add your own feeds |
| World | Nothing | The [WARROOM public API](docs/warroom-api.md): globe, conflict desk, forecasts, hazards, space weather |
| Mail | Microsoft 365 app, optional Anthropic key | Read-only triage across your mailboxes. Money, customer, security and legal mail rises to the top |
| Business | Any address returning [the money report](docs/money-feed.md) | Are you making money? Sales minus costs, by product |
| Arts | Plex, optional Sonarr, Radarr and Seerr | What landed, what's playing, what's coming |
| Systems | Proxmox, SSH, or plain addresses | Service checks, machines, containers, storage and backups, and a list of what needs you |

![Settings](docs/img/settings.png)

Name the paper and choose its title face, from blackletter like a real masthead to the theme's own. Each connection has a Test button that tells you in plain words what went wrong. Saved keys can never be read back, not even by you. Any setting can come from the environment instead: see `.env.example`.

## AI

Add any provider in Settings: Anthropic, OpenAI, Google Gemini, xAI Grok, OpenRouter, Groq, Mistral, DeepSeek, Together, Ollama, LM Studio, or anything OpenAI-compatible. You can then ask the paper questions, have your mail sorted, and set it up by describing what you want.

Any AI can also read the paper, over MCP or plain HTTP, with a token you control. Only news and world are shared until you tick more. [docs/ai.md](docs/ai.md) has the setup for Claude, Cursor and the rest, and explains why the AI that reads strangers' words can never change a setting.

## Putting it on the internet

`compose.yaml` publishes the paper on this machine only. Before you change that, read [SECURITY.md](SECURITY.md). In short:

- Put a tunnel or a TLS reverse proxy in front of it. Plain HTTP sends your password in the clear.
- Have the proxy send `X-Forwarded-Proto: https`, so the session cookie is marked Secure.
- If your proxy already has its own login, you can set `PAPER_AUTH=none` and name the hostname in `PAPER_HOSTS`. Without a gate of your own, leave sign-in on.

Back up the `paper-data` volume, and treat that backup like your keys.

## How it works

One Python process, stdlib apart from the Anthropic SDK that mail sorting uses. Background jobs snapshot each source into SQLite and the page only reads those snapshots, so a slow or dead source can't slow the paper down: it shows the last good copy and how old it is. The front end is plain ES modules with no build step.

```sh
python3 tests/test_paper.py   # the logic that can quietly lie: money, sanitizing, secrets, sign-in
python3 paper/server.py       # needs PAPER_DATA set to a folder you can write to
```

`DESIGN.md` describes the design system.

## License

MIT. The fonts in `web/fonts` are under the SIL Open Font License: see `web/fonts/LICENSE.md`.

World data comes from WARROOM and is free to use with attribution. Headlines belong to their publishers.
