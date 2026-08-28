"""Idempotent database bootstrap.

  Alembic-managed / pre-Alembic DB with the base tables -> run migrations.
  Truly empty DB                                        -> create_all + stamp head.

Called both from `bootstrap.py` (CLI, pre-deploy) and from the app's
startup lifespan, so the schema is right even on hosts with no pre-deploy
hook or shell access.
"""

from __future__ import annotations

import logging
import os

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

logger = logging.getLogger(__name__)

_ALEMBIC_INI = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")


def bootstrap_database() -> str:
    """Bring the database schema up to date. Returns a short status string."""

    # Imported here so importing this module never touches the DB.
    from app.database.connection import Base, engine
    import app.models  # noqa: F401 — register every model on Base.metadata

    cfg = Config(_ALEMBIC_INI)
    existing = set(inspect(engine).get_table_names())

    if "alembic_version" in existing or "organizations" in existing:
        command.upgrade(cfg, "head")
        return "migrated"

    Base.metadata.create_all(bind=engine)
    command.stamp(cfg, "head")
    return "created"


def bootstrap_on_startup() -> None:
    """Best-effort bootstrap from the app lifespan — never raises."""

    try:
        result = bootstrap_database()
        logger.info("Database bootstrap: %s", result)
    except Exception:
        logger.exception(
            "Database bootstrap failed on startup — some endpoints may 500 "
            "until migrations are applied."
        )
