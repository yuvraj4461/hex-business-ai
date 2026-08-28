"""Shared column mixins for canonical models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


class SourceTrackedMixin:
    """Provenance for rows that may be ingested from an external system.

    Seeded / manually-created rows leave every column NULL. Rows written by
    the ingestion pipeline (`app/ingestion/`) set all three so a sync can
    upsert by ``(source_connection_id, source_external_id)`` and the UI can
    show where a figure came from and how fresh it is.
    """

    source_connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("connections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    source_external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
