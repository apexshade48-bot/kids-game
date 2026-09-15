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


def list_models(host: str | None = None) -> list[str]:
    url = (host or DEFAULT_HOST) + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=2) as res:
            data = json.loads(res.read().decode("utf-8"))
            return [m.get("name") or m.get("model") for m in data.get("models") or []]
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return []


def ping(host: str | None = None) -> bool:
    url = (host or DEFAULT_HOST) + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=2) as res:
            return 200 <= res.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _resolve_model(host: str | None, requested: str | None) -> tuple[str | None, str | None]:
    """Pick a model that's actually installed. The configured default
    (llama3.2:3b) may not be the one the person actually pulled — fall back
    to whatever IS installed instead of failing outright."""
    wanted = requested or DEFAULT_MODEL
    available = list_models(host)
    if not available:
        if not ping(host):
            return None, (
                "The AI Teacher only works when Word Stars is running on your "
                "own computer with Ollama installed — it can't run on this "
                "online version."
            )
        return None, "No AI model is installed yet. Ask a grown-up to run: ollama pull llama3.2:3b"
    if wanted in available:
        return wanted, None
    # Exact tag (e.g. "llama3.2:3b") may differ from an installed "llama3.2:latest" —
    # match on the name before the colon before giving up and falling back.
    base = wanted.split(":")[0]
    for name in available:
        if name and name.split(":")[0] == base:
            return name, None
    return available[0], None


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

    resolved_model, resolve_error = _resolve_model(host, model)
    if resolve_error:
        return False, resolve_error

    messages = [{"role": "system", "content": SYSTEM}]
    for turn in (history or [])[-6:]:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()[:300]
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": text})

    body = json.dumps(
        {
            "model": resolved_model,
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
        with urllib.request.urlopen(req, timeout=45) as res:
            data = json.loads(res.read().decode("utf-8"))
    except TimeoutError:
        return False, (
            f"'{resolved_model}' is too slow to answer quickly. "
            "Try a smaller model: ollama pull llama3.2:3b"
        )
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.loads(e.read().decode("utf-8")).get("error", "")
        except Exception:
            pass
        return False, ("Teacher hit an error: " + detail) if detail else "Teacher could not answer. Try again."
    except (urllib.error.URLError, OSError):
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
