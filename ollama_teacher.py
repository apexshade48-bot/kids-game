"""Kid-safe English helper using a local Ollama model (llama3.2:3b)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

SYSTEM = (
    "You are a kind English teacher for children ages 4 to 8. "
    "Use very short, happy sentences. Easy words only. "
    "Help them say, spell, and understand English. "
    "Give one example sentence a kid can copy. "
    "Never talk about adult, scary, violent, or rude things. "
    "If the question is not about English words or speaking, "
    "say: Let's practice a word instead! "
    "Keep the whole answer under 40 words."
)


def ping(host: str | None = None) -> bool:
    url = (host or DEFAULT_HOST) + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=2) as res:
            return 200 <= res.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def ask(
    user_text: str,
    word: str | None = None,
    history: list[dict] | None = None,
    host: str | None = None,
    model: str | None = None,
) -> tuple[bool, str]:
    text = " ".join((user_text or "").split())[:200]
    if not text:
        return False, "Say or type a question first."
    w = (word or "").strip().lower()[:48]
    if w:
        text = f"The word we are practicing is: {w}. {text}"

    messages = [{"role": "system", "content": SYSTEM}]
    for turn in (history or [])[-6:]:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()[:300]
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": text})

    body = json.dumps(
        {
            "model": model or DEFAULT_MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.4, "num_predict": 90},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        (host or DEFAULT_HOST) + "/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError:
        return False, "Teacher could not answer. Is Ollama running?"
    except (urllib.error.URLError, TimeoutError, OSError):
        return False, "Teacher is asleep. On this PC run: ollama serve"
    except json.JSONDecodeError:
        return False, "Teacher sent a mixed-up answer. Try again."

    reply = (
        ((data.get("message") or {}).get("content"))
        or data.get("response")
        or ""
    ).strip()
    if not reply:
        return False, "Teacher is thinking. Try again."
    # Keep it short for kids even if the model rambles.
    parts = reply.replace("\n", " ").split()
    if len(parts) > 50:
        reply = " ".join(parts[:50]) + "…"
    return True, reply
