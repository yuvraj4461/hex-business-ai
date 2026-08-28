import importlib
import pkgutil

from app.database.connection import Base, engine
import app.models


print("Loading HEX database models...")


# Import every Python module inside app.models.
# This ensures SQLAlchemy knows about every model
# before Base.metadata.create_all() runs.

for module_info in pkgutil.iter_modules(
    app.models.__path__
):
    module_name = module_info.name

    if module_name.startswith("_"):
        continue

    print(
        f"Loading model module: {module_name}"
    )

    importlib.import_module(
        f"app.models.{module_name}"
    )


print()
print("Creating database tables...")


Base.metadata.create_all(
    bind=engine
)


print()
print(
    "Database tables created successfully!"
)


# Mark this fresh database as being at the latest Alembic revision, so
# future `alembic upgrade head` runs only apply migrations added later.
# (Existing databases are migrated with `alembic upgrade head` instead.)
try:
    from alembic import command
    from alembic.config import Config

    print()
    print("Stamping Alembic revision -> head ...")
    command.stamp(Config("alembic.ini"), "head")
    print("Done.")
except Exception as exc:  # noqa: BLE001
    print(f"(Alembic stamp skipped: {exc})")