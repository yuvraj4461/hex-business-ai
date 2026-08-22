from app.database.connection import Base, engine

# Import models so SQLAlchemy knows about them.
from app.models import (
    Organization,
    Customer,
    Product,
    Service,
)

print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")