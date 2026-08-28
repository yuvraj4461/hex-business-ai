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

    if "organizations" not in existing:
        print("Fresh database — creating schema from models...")
        Base.metadata.create_all(bind=engine)
        command.stamp(cfg, "head")
        print("Schema created and stamped at Alembic head.")
    else:
        print("Existing database — applying pending migrations...")
        command.upgrade(cfg, "head")
        print("Migrations applied.")


if __name__ == "__main__":
    main()
