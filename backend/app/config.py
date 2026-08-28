"""Central configuration.

This module previously required OPENAI_API_KEY and raised RuntimeError at
import time if it was missing. HEX uses Gemini, not OpenAI, so that check
was both wrong and dangerous: any module importing config would crash the
whole application at startup.

Configuration is now read lazily and validated on demand.
"""

import os

from dotenv import load_dotenv

load_dotenv()


# --- LLM -------------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash",
)


# --- Database --------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")


# --- Auth ------------------------------------------------------------
# Accepts JWT_SECRET_KEY or JWT_SECRET. .env used the former while
# .env.production used the latter, which meant tokens signed in
# production fell back to a different secret and every request 401'd.

JWT_SECRET_KEY = (
    os.getenv("JWT_SECRET_KEY")
    or os.getenv("JWT_SECRET")
)

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

JWT_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "480")
)


# --- Frontend --------------------------------------------------------

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:3000",
)


def missing_settings() -> list[str]:
    """Return the names of required settings that are not configured."""

    required = {
        "DATABASE_URL": DATABASE_URL,
        "JWT_SECRET_KEY": JWT_SECRET_KEY,
        "GEMINI_API_KEY": GEMINI_API_KEY,
    }

    return [
        name
        for name, value in required.items()
        if not value
    ]


def require_gemini_key() -> str:
    """Return the Gemini key, raising only when a call actually needs it."""

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Add it to backend/.env"
        )

    return GEMINI_API_KEY