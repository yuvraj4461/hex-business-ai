from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


# Lifecycle of a connection to an external system.
CONNECTION_STATUSES = ("PENDING", "ACTIVE", "ERROR", "DISABLED")

# Registered source types (see app/sources/registry.py).
SOURCE_TYPES = ("file_upload", "sql", "merge")


class Connection(Base):
    """A configured link between one organization and one external system.

    Non-secret settings live in ``config`` (JSON). Secrets (DB passwords,
    API tokens) live only in ``credentials_encrypted`` (Fernet, see
    app/security/crypto.py) and are never returned by the API or logged.
    """

    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    source_type: Mapped[str] = mapped_column(String(50), nullable=False)

    display_name: Mapped[str] = mapped_column(String(150), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
    )

    # Non-secret configuration: entity->query map for SQL, column mappings
    # for file upload, Merge account id, etc.
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    credentials_encrypted: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
    )

    # Per-entity sync position, e.g. {"purchase_order": "2026-08-01T..."}.
    cursor: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
