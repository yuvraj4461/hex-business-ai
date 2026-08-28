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

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", "25000"))


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
    """Return the model's text, or raise (caller handles the fallback)."""

    response = get_client().models.generate_content(
        model=model or GEMINI_MODEL,
        contents=prompt,
    )
    return response.text or ""
