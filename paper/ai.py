"""One door to any AI model.

Anthropic goes through its SDK. Everything else goes through the OpenAI-compatible chat API, which nearly every provider
and local runner speaks, so one small adapter covers them all. Keys go only to the provider's own address and never
follow a redirect.
"""
import json
import os
import urllib.error
import urllib.request

import settings

C = settings.get
DEFAULT_CLAUDE, CHEAP_CLAUDE = "claude-opus-5-5", "claude-haiku-5-5"
NO_KEY_NEEDED = ("ollama", "lmstudio", "custom")
BASES = {value: base for value, _, base in settings.PROVIDERS}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def provider():
    return C("AI_PROVIDER")


def key():
    return C("AI_KEY") or (os.environ.get("ANTHROPIC_API_KEY", "") if provider() == "anthropic" else "")


def base():
    return C("AI_URL") or BASES.get(provider(), "")


def model():
    return C("AI_MODEL") or (DEFAULT_CLAUDE if provider() == "anthropic" else "")


def ready():
    if provider() == "anthropic":
        return bool(key())
    return bool(base() and model() and (key() or provider() in NO_KEY_NEEDED))


def json_in(text):
    """Models wrap JSON in prose and code fences, so take what sits between the outermost braces."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON in the answer")
    return json.loads(text[start:end + 1])


def _anthropic(system, text, max_tokens, cheap, schema):
    import anthropic  # only AI work needs it, and it costs tens of megabytes
    config = {"effort": "low"} if cheap else {}
    if schema:
        config["format"] = {"type": "json_schema", "schema": schema}
    try:
        reply = anthropic.Anthropic(api_key=key(), timeout=60.0).messages.create(model=CHEAP_CLAUDE if cheap else model(), max_tokens=max_tokens, system=system, messages=[{"role": "user", "content": text}],
                                                                                 **({"output_config": config} if config else {}))
    except anthropic.APIStatusError as e:
        raise urllib.error.HTTPError("https://api.anthropic.com", e.status_code, "refused", {}, None) from None
    except anthropic.APIError:
        raise OSError("no answer") from None
    if reply.stop_reason != "end_turn":
        raise ValueError(f"stopped: {reply.stop_reason}")
    return next(b.text for b in reply.content if b.type == "text")


def _compatible(system, text):
    """No token limit is sent: providers disagree on what the field is called, and refuse the wrong one."""
    body = {"model": model(), "messages": [{"role": "system", "content": system}, {"role": "user", "content": text}]}
    headers = {"Content-Type": "application/json", "User-Agent": "MorningPaper/1.0"}
    if key():
        headers["Authorization"] = f"Bearer {key()}"
    with OPENER.open(urllib.request.Request(f"{base()}/chat/completions", json.dumps(body).encode(), headers), timeout=120) as r:
        return json.loads(r.read(4_000_000))["choices"][0]["message"]["content"]


def ask(system, text, max_tokens=1500, cheap=False, schema=None):
    """One question, one answer as text. Raises OSError, ValueError, KeyError or HTTPError when it can't get one."""
    if provider() == "anthropic":
        return _anthropic(system, text, max_tokens, cheap, schema)
    return _compatible(system, text)
