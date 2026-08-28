"""Symmetric encryption for connection credentials at rest.

Credentials (DB passwords, API tokens) are stored only as the Fernet
ciphertext produced here — never in plaintext columns, never logged.

Key resolution:
  1. ``HEX_SECRET_KEY`` env var, if it is a valid 32-byte urlsafe-base64
     Fernet key (generate one with ``Fernet.generate_key()``).
  2. Otherwise a key derived deterministically from ``JWT_SECRET_KEY`` /
     ``JWT_SECRET`` so local development works with no extra setup.

For production, set ``HEX_SECRET_KEY`` explicitly and rotate it via
Fernet's MultiFernet if needed.
"""

import base64
import hashlib
import json
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


def _resolve_key() -> bytes:
    explicit = os.getenv("HEX_SECRET_KEY")
    if explicit:
        try:
            Fernet(explicit.encode())
            return explicit.encode()
        except (ValueError, TypeError):
            logger.warning(
                "HEX_SECRET_KEY is set but not a valid Fernet key; "
                "falling back to a derived key.",
            )

    seed = (
        os.getenv("JWT_SECRET_KEY")
        or os.getenv("JWT_SECRET")
        or "hex-insecure-dev-key"
    )
    digest = hashlib.sha256(seed.encode()).digest()
    return base64.urlsafe_b64encode(digest)


_fernet = Fernet(_resolve_key())


def encrypt_dict(data: dict) -> bytes:
    """Encrypt a JSON-serialisable dict to Fernet ciphertext."""

    return _fernet.encrypt(json.dumps(data).encode())


def decrypt_dict(token: bytes | None) -> dict:
    """Decrypt ciphertext back to a dict. Returns {} for None/invalid."""

    if not token:
        return {}
    try:
        return json.loads(_fernet.decrypt(bytes(token)).decode())
    except (InvalidToken, ValueError):
        logger.error("Failed to decrypt connection credentials.")
        return {}
