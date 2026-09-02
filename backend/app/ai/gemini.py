"""Lazily-constructed Gemini client.

Importing this module never fails, even with no API key — the client is
built on first use. Callers wrap `get_client()` / `generate_text()` in
try/except and fall back to a non-AI path when the key is missing or the
model is unavailable.
"""

import logging
import os
import time
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

# Google has retired 2.x flash for new API keys ("no longer available to
# new users … use models/gemini-3.6-flash"). Newer keys only serve the
# 3.6 generation. Set GEMINI_MODEL to pin one; otherwise we try these in
# order and cache the first that works.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", "20000"))
# Total wall-clock budget across retries + model fallbacks before we give
# up and let the caller use its deterministic path.
GEMINI_BUDGET_MS = int(os.getenv("GEMINI_BUDGET_MS", "45000"))
# Per-model retries when the model is overloaded (503) or rate-limited (429).
GEMINI_RETRIES = int(os.getenv("GEMINI_RETRIES", "2"))

_MODEL_FALLBACKS = [
    "gemini-3.6-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
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
    return (
        "404" in text
        or "not_found" in text
        or "not found" in text
        or "no longer available" in text
        or "not available" in text
        or "is not supported for generatecontent" in text
    )


def _is_overloaded(exc: Exception) -> bool:
    """Transient: the model is busy or we're rate-limited. Worth a retry
    or trying a different model."""
    text = str(exc).lower()
    return (
        "503" in text
        or "unavailable" in text
        or "overloaded" in text
        or "high demand" in text
        or "try again" in text
        or "429" in text
        or "resource_exhausted" in text
        or "rate limit" in text
        or "deadline" in text
        or "timeout" in text
        or "timed out" in text
    )


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

    Resilience:
    - a retired model alias (404) falls through to the next in the list;
    - an overloaded / rate-limited model (503 / 429) is retried a couple
      of times with backoff, then we move to the next model;
    - the whole thing is bounded by GEMINI_BUDGET_MS so a bad Gemini day
      can't hang the request.
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

    deadline = time.monotonic() + GEMINI_BUDGET_MS / 1000
    last_exc: Exception | None = None

    for candidate in [c for c in candidates if c]:
        for attempt in range(GEMINI_RETRIES + 1):
            if time.monotonic() > deadline:
                raise last_exc or RuntimeError("Gemini time budget exhausted")
            try:
                response = client.models.generate_content(
                    model=candidate, contents=prompt,
                )
                if not model:
                    _working_model = candidate
                return response.text or ""
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if _is_model_unavailable(exc):
                    logger.warning(
                        "Gemini model %s unavailable, trying next", candidate
                    )
                    break  # next model
                if _is_overloaded(exc) and attempt < GEMINI_RETRIES:
                    wait = 0.6 * (attempt + 1) ** 2
                    logger.warning(
                        "Gemini %s busy (%s), retry %d in %.1fs",
                        candidate, str(exc).splitlines()[0][:80],
                        attempt + 1, wait,
                    )
                    time.sleep(wait)
                    continue  # retry same model
                if _is_overloaded(exc):
                    logger.warning(
                        "Gemini %s still busy after retries, trying next", candidate
                    )
                    break  # next model
                raise  # a real error — surface it

    raise last_exc or RuntimeError("No Gemini model available")
