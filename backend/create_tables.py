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