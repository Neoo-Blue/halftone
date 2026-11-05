"""Reading a story aloud through a speech service. Only the paper talks to the service, so a key never reaches a browser."""
import base64
import html
import io
import json
import re
import time
import urllib.parse
import urllib.request
import wave

from ai import OPENER, read_all

LIMIT, MOST = 1800, 30  # Deepgram refuses more than 2,000 characters at once. Thirty pieces is about an hour
ROOM = (250, 700)  # a voice takes about a quarter of its playing time to make, so short pieces first start it in seconds, and each is ready before the last one ends
RATE = 24000  # LiveKit's gateway sends raw 16-bit audio at the rate it's asked for
GATEWAY = "wss://agent-gateway.livekit.cloud/v1/tts"
AUDIO_MOST = 60 * 2 ** 20
SERVICE_VOICE = re.compile(r"[\w./:-]{3,120}")

# Dollars a million characters at list price. A plan's discount or included credit shows on the bill, not here.
PRICE = {"cartesia": 50, "deepgram": 30, "inworld": 25, "rime": 50}

# Deepgram's English voices, for LiveKit, which has no list to ask, and for Deepgram when its own list won't answer.
AURA = (("draco", "British man, warm"), ("pandora", "British woman, calm"), ("athena", "American woman, calm"), ("orion", "American man, approachable"), ("orpheus", "American man, clear"), ("hera", "American woman, warm"),
        ("arcas", "American man, smooth"), ("thalia", "American woman, clear"), ("odysseus", "American man, calm"), ("apollo", "American man, confident"), ("theia", "Australian woman, polite"), ("hyperion", "Australian man, warm"))
OTHERS = (("cartesia/sonic-3:a167e0f3-df7e-4d52-a9c3-f949145efdab", "Blake", "American man, energetic", "Cartesia"), ("cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc", "Jacqueline", "American woman, confident", "Cartesia"),
          ("cartesia/sonic-3:f31cc6a7-c1e8-4764-980c-60a361443dd1", "Robyn", "Australian woman, neutral", "Cartesia"), ("inworld/inworld-tts-2:Olivia", "Olivia", "British woman, friendly", "Inworld"),
          ("inworld/inworld-tts-2:Ashley", "Ashley", "American woman, warm", "Inworld"), ("inworld/inworld-tts-2:Edward", "Edward", "American man, emphatic", "Inworld"),
          ("rime/coda:astra", "Astra", "American woman, upbeat", "Rime"), ("rime/coda:luna", "Luna", "American woman, lively", "Rime"))
# Cartesia's own API: Sonic 3.6, the newest, which LiveKit's gateway doesn't carry. Ids are model:voice.
SONIC = (("4703c250-66e4-4682-a223-0a60acafcfc0", "Levi", "American man, newsreader"), ("26403c37-80c1-4a1a-8692-540551ca2ae5", "Marian", "American woman, poised narrator"),
         ("a167e0f3-df7e-4d52-a9c3-f949145efdab", "Blake", "American man, energetic"), ("9626c31c-bec5-4cca-baa8-f8ba9e84c8bc", "Jacqueline", "American woman, confident"),
         ("62ae83ad-4f6a-430b-af41-a9bede9286ca", "Gemma", "British woman, confident"), ("ef191366-f52f-447a-a398-ed8c0f2943a1", "Archie", "British man, warm"),
         ("f31cc6a7-c1e8-4764-980c-60a361443dd1", "Robyn", "Australian woman, neutral"), ("9c8880b2-ccf9-4730-b805-cea23df247d7", "Conrad", "American man, seasoned"))
CARTESIA = "https://api.cartesia.ai/tts/bytes"
DEFAULT = {"cartesia": f"sonic-3.6:{SONIC[0][0]}", "deepgram": "aura-2-draco-en", "livekit": "deepgram/aura-2:draco"}


def aura(models):
    """Deepgram's own list, cut down to its current English voices. What the service sends is checked here."""
    rows = []
    for m in (models or {}).get("tts") or []:
        found = isinstance(m, dict) and re.fullmatch(r"aura-2-([a-z]+)-en", str(m.get("canonical_name") or ""))
        if found:
            info = m.get("metadata") if isinstance(m.get("metadata"), dict) else {}
            tags = [str(t)[:30] for t in info.get("tags") or []]
            who = "woman" if "feminine" in tags else "man" if "masculine" in tags else "voice"
            rows.append((found[1], ", ".join([f"{str(info.get('accent') or 'English')[:30]} {who}", *[t for t in tags if t not in ("feminine", "masculine")][:2]])))
    return rows


def voices(provider, models=None):
    if provider == "deepgram":
        return [{"id": f"aura-2-{n}-en", "name": n.title(), "about": about, "group": "Deepgram"} for n, about in aura(models) or AURA]
    if provider == "cartesia":
        return [{"id": f"sonic-3.6:{i}", "name": n, "about": about, "group": "Cartesia"} for i, n, about in SONIC]
    if provider == "livekit":
        return [*({"id": f"deepgram/aura-2:{n}", "name": n.title(), "about": about, "group": "Deepgram"} for n, about in AURA), *({"id": i, "name": n, "about": about, "group": g} for i, n, about, g in OTHERS)]
    return []


def fits(provider, voice):
    """A voice picked for one service, or for one device, means nothing to another."""
    if provider == "cartesia":
        return bool(re.fullmatch(r"sonic[\w.-]*:[0-9a-f-]{36}", voice or ""))
    return bool(SERVICE_VOICE.fullmatch(voice or "")) and (voice.startswith("aura-") if provider == "deepgram" else "/" in voice and ":" in voice)


def price(voice):
    return PRICE.get("cartesia" if voice.startswith("sonic") else voice.split("/")[0], PRICE["deepgram"])


def pieces(title, deck, body):
    """The story as it would be read: headline, summary, then the text, in pieces a service will take, broken between sentences."""
    blocks = [x.strip() if x.strip()[-1:] in tuple(".!?") else f"{x.strip()}." for x in (title, deck) if x and x.strip()]
    for part in re.split(r"</(?:p|li|h\d|blockquote)>", body or ""):
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^<>]+>", " ", part))).strip()
        if text:
            blocks.append(text)
    out, now = [], ""
    for block in blocks:
        joint = "\n\n"  # a paragraph gets a pause, a sentence just follows on
        for bit in re.split(r"(?<=[.!?])\s+", block):
            bit = bit[:LIMIT]  # a sentence this long isn't prose
            if now and len(now) + len(bit) + 2 > (ROOM[len(out)] if len(out) < len(ROOM) else LIMIT):
                out.append(now)
                now = ""
            now = f"{now}{joint}{bit}" if now else bit
            joint = " "
    return [*out, now][:MOST] if now else out[:MOST]


def deepgram(key, voice, text):
    url = "https://api.deepgram.com/v1/speak?" + urllib.parse.urlencode({"model": voice, "encoding": "mp3"})
    req = urllib.request.Request(url, json.dumps({"text": text}).encode(), {"Authorization": f"Token {key}", "Content-Type": "application/json"})
    with OPENER.open(req, timeout=60) as r:  # no redirects, so the key goes to this address or nowhere
        return read_all(r, AUDIO_MOST, 120), "audio/mpeg"


def cartesia(key, voice, text):
    model, _, vid = voice.partition(":")
    body = {"model_id": model, "transcript": text, "voice": {"mode": "id", "id": vid}, "language": "en", "output_format": {"container": "mp3", "sample_rate": 44100, "bit_rate": 128000}}
    req = urllib.request.Request(CARTESIA, json.dumps(body).encode(), {"Authorization": f"Bearer {key}", "Cartesia-Version": "2026-03-01", "Content-Type": "application/json"})
    with OPENER.open(req, timeout=60) as r:  # no redirects, so the key goes to this address or nowhere
        return read_all(r, AUDIO_MOST, 120), "audio/mpeg"


def to_wav(pcm):
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(bytes(pcm))
    return out.getvalue()


def livekit(token, voice, text, connect=None):
    """LiveKit's gateway, spoken to the way its own agents do: open a session, send the text, flush, and gather audio until it says done."""
    if connect is None:
        from websockets.sync.client import connect  # noqa: PLC0415 - only this service needs it
    model, _, name = voice.rpartition(":")
    pcm, stop = bytearray(), time.monotonic() + 120
    choice = {"model": model, "voice": name, "language": "en"}
    with connect(f"{GATEWAY}?{urllib.parse.urlencode({'model': model})}", additional_headers={"Authorization": f"Bearer {token}"}, open_timeout=20, close_timeout=2, max_size=2 ** 24) as ws:
        ws.send(json.dumps({"type": "session.create", "sample_rate": str(RATE), "encoding": "pcm_s16le", "extra": {}, **choice}))
        ws.send(json.dumps({"type": "input_transcript", "transcript": f"{text} ", "generation_config": choice, "extra": {}}))
        ws.send(json.dumps({"type": "session.flush"}))
        while True:
            left = stop - time.monotonic()
            if left <= 0 or len(pcm) > AUDIO_MOST:
                raise OSError("the voice service ran too long")
            sent = json.loads(ws.recv(timeout=left))
            kind = sent.get("type") if isinstance(sent, dict) else None
            if kind == "output_audio":
                pcm += base64.b64decode(sent["audio"])
            elif kind == "done":
                if not pcm:
                    raise OSError("no audio came back")
                return to_wav(pcm), "audio/wav"
            elif kind == "error":
                raise OSError("the voice service refused")


def speak(provider, key, voice, text):
    try:
        return {"livekit": livekit, "cartesia": cartesia}.get(provider, deepgram)(key, voice, text)
    except OSError:
        raise
    except Exception as e:  # noqa: BLE001 - a library's own failures, and a reply that isn't what it promised, all mean the same to the reader
        raise OSError("the voice service failed") from e
