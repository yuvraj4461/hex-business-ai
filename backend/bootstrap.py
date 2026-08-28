"""Idempotent database bootstrap — run once on every deploy, before the app.

  Fresh database    -> create every table from the models, stamp Alembic at head.
  Existing database -> apply any pending Alembic migrations.

Usage:  python bootstrap.py
"""

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.database.connection import Base, engine
import app.models  # noqa: F401  — registers every model on Base.metadata


def main() -> None:
    cfg = Config("alembic.ini")
    existing = set(inspect(engine).get_table_names())

    if "alembic_version" in existing or "organizations" in existing:
        # Already-Alembic-managed, or an older pre-Alembic DB that still has
        # the base tables. Every migration is additive, so running them from
        # the start brings the pre-Alembic DB up to date without data loss.
        print("Applying migrations to existing database...")
        command.upgrade(cfg, "head")
        print("Migrations applied.")
    else:
        # Truly empty database — create the full schema from the models and
        # mark it at head so future deploys migrate normally.
        print("Empty database — creating schema from models...")
        Base.metadata.create_all(bind=engine)
        command.stamp(cfg, "head")
        print("Schema created and stamped at Alembic head.")


if __name__ == "__main__":
    main()
