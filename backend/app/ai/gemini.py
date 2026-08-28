"""Lazily-constructed Gemini client.

Importing this module never fails, even with no API key — the client is
built on first use. Callers wrap `get_client()` / `generate_text()` in
try/except and fall back to a non-AI path when the key is missing or the
model is unavailable.
"""

import logging
import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

# Which flash models a given API key can see varies. Set GEMINI_MODEL to
# pin one; otherwise we try these in order and cache the first that works.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", "25000"))

_MODEL_FALLBACKS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
]

# Populated at runtime once a model call succeeds, so we stop probing.
_working_model: str | None = None


def _candidate_models() -> list[str]:
    ordered = [GEMINI_MODEL, *_MODEL_FALLBACKS]
    seen: set[str] = set()
    out: list[str] = []
    for m in ordered:
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _is_model_unavailable(exc: Exception) -> bool:
    text = str(exc).lower()
    return "404" in text or "not available" in text or "not found" in text


def is_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    return genai.Client(
        api_key=key,
        http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
    )


def generate_text(prompt: str, *, model: str | None = None) -> str:
    """Return the model's text, or raise (caller handles the fallback).

    If a model alias has been retired (404), fall through the fallback
    list and remember the one that worked.
    """

    global _working_model

    client = get_client()
    if model:
        candidates = [model]
    else:
        candidates = _candidate_models()
        if _working_model and _working_model in candidates:
            candidates.remove(_working_model)
            candidates.insert(0, _working_model)

    last_exc: Exception | None = None
    for candidate in [c for c in candidates if c]:
        try:
            response = client.models.generate_content(
                model=candidate,
                contents=prompt,
            )
            if not model:
                _working_model = candidate
            return response.text or ""
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if not _is_model_unavailable(exc):
                raise
            logger.warning("Gemini model %s unavailable, trying next", candidate)

    raise last_exc or RuntimeError("No Gemini model available")
