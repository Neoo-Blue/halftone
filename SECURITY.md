# Security

This paper holds keys to your mail, your servers and your money, so it is built to fail closed. Here is what it does, and what it leaves to you.

## Reporting a problem

Please use [a private security advisory](../../security/advisories/new) rather than a public issue.

## What protects you

- **Sign-in is on by default.** Everything but the sign-in page and the app's own code and fonts needs a session. A new install has no password: setting one takes a one-time code printed to the container log, so being first to reach a fresh install gets a stranger nothing.
- **Passwords** are stored as scrypt hashes. Sessions are random, stored hashed, last 30 days, and end when you change the password, including `PAPER_PASSWORD`. So does the AI token. Ten wrong tries in five minutes stops all tries for the rest of that window.
- **Secrets are write-only.** The settings page can set or clear a key but never read one back. Tests fail the build if a key reaches the settings page, or if a failed connection test repeats one.
- **A key stays with its address.** Change a connection's address, or turn off Proxmox's certificate check, and its saved key is deleted until you type it again, so a stolen session can't point Plex at another host and collect your token. A key is never sent on a redirect to another host.
- **Cross-site requests are refused.** The cookie is `HttpOnly` and `SameSite=Strict`, every write needs a custom header, and a strict Content Security Policy allows no inline script.
- **The reader can't reach your network.** Reader mode and news pictures fetch only public addresses, checked again after connecting, so a link in a story can't touch your LAN or a cloud metadata service.
- **An AI that reads can't act, and one that can act doesn't read.** Ask sees strangers' text and can only answer. Set it up by asking sees no stranger's text, no key and no query string, can only propose, and can't move a connection that holds a key. AI tokens are read only and open nothing else. See [docs/ai.md](docs/ai.md).
- **Mail is read only.** The code only sends GET requests. Mail text reaches the model as untrusted data, and the model's answer is checked like any other input.
- **The container** runs as an unprivileged user with a read-only filesystem, no capabilities and no new privileges. No secret is built into the image.

## What is left to you

- **Use HTTPS.** Compose publishes the paper on `127.0.0.1` only. To reach it from elsewhere, put a tunnel or a TLS reverse proxy in front. Over plain HTTP your password crosses the network in the clear. Have the proxy send `X-Forwarded-Proto: https` so the cookie is marked Secure.
- **Protect the data volume.** Keys sit in `/data/settings.json`, mode 600, unencrypted: the same trust as a `.env` file, and encrypting them with a key kept beside them would protect nothing. Anyone who can read the volume or run `docker exec` has your keys. Treat backups of it the same way. Or set keys through the environment and leave the file out of it.
- **Give each key the least it needs.** Proxmox: the `PVEAuditor` role. Microsoft Graph: `Mail.Read`. The SSH key: locked to the stats script (see `agent/stats.sh`).
- **`PAPER_AUTH=none` removes the password.** Use it only behind a gate of your own, such as Cloudflare Access, and make sure nothing can reach the port except that gate. `PAPER_HOSTS` stops a web page reaching the paper through a DNS trick, but it is not access control: anyone who can reach the port can send any host name.

## Known limits

- With an AI provider on, the headlines and part of the text of a story several outlets carry go to it to compare the coverage. That happens every hour for the biggest stories and the first time you open any other, so the provider can see which stories get opened. Settings has a switch. What your reading leans toward stays on your server and goes to no AI.

- With a voice service on, the headline and text of a story you press Listen on go to that service. Nothing else does: no mail, no money, nothing about you. Your device's own voice sends nothing.

- A browser that has signed in keeps the last edition for offline reading, including mail subjects and money. It goes when the session ends, and it stops being offered after three days, but anyone with that browser profile could read it until then.

- The login limit is global, because behind a proxy every caller has the same address. A stranger can hold the sign-in page shut, though not guess past it, and anyone already signed in isn't affected.
- Accepting a self-signed Proxmox certificate means the token goes to whatever answers at that address. Use it on your own network only.
- `PAPER_AUTH=password` has one user. Whoever signs in can change every setting.
- The built-in web server isn't made to face a flood of connections. Keep a proxy in front of it on the open internet.
- A stolen session can read your mail and change settings until you change the password. It can't read back a saved key. After one, check the AI provider's Address too, because mail sorting sends mail details to it.
