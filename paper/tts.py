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
DEFAULT = {"deepgram": "aura-2-draco-en", "livekit": "deepgram/aura-2:draco"}


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
    if provider == "livekit":
        return [*({"id": f"deepgram/aura-2:{n}", "name": n.title(), "about": about, "group": "Deepgram"} for n, about in AURA), *({"id": i, "name": n, "about": about, "group": g} for i, n, about, g in OTHERS)]
    return []


def fits(provider, voice):
    """A voice picked for one service, or for one device, means nothing to another."""
    return bool(SERVICE_VOICE.fullmatch(voice or "")) and (voice.startswith("aura-") if provider == "deepgram" else "/" in voice and ":" in voice)


def price(voice):
    return PRICE.get(voice.split("/")[0], PRICE["deepgram"])


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
        return livekit(key, voice, text) if provider == "livekit" else deepgram(key, voice, text)
    except OSError:
        raise
    except Exception as e:  # noqa: BLE001 - a library's own failures, and a reply that isn't what it promised, all mean the same to the reader
        raise OSError("the voice service failed") from e
