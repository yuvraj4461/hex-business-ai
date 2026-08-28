from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class RawRecord(Base):
    """One record exactly as it arrived from a source, before normalization.

    The landing zone. Keeping the untouched payload means a mapping bug can
    be fixed and re-run without re-fetching from the customer's system, and
    ``content_hash`` lets a re-sync skip rows that have not changed.
    """

    __tablename__ = "raw_records"
    __table_args__ = (
        UniqueConstraint(
            "connection_id",
            "entity_type",
            "external_id",
            name="uq_raw_records_connection_entity_external",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    connection_id: Mapped[int] = mapped_column(
        ForeignKey("connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    normalized_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
