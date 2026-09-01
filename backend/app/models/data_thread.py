from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class DataThread(Base):
    """One "Ask Your Data" conversation."""

    __tablename__ = "data_threads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)

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

    messages: Mapped[list["DataThreadMessage"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="DataThreadMessage.created_at",
    )


class DataThreadMessage(Base):
    """One turn in a thread — a user question or a HEX answer (with its
    query spec and result payload for re-rendering)."""

    __tablename__ = "data_thread_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    thread_id: Mapped[int] = mapped_column(
        ForeignKey("data_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(String(10), nullable=False)  # user | hex

    question: Mapped[str | None] = mapped_column(Text, nullable=True)

    answer: Mapped[str | None] = mapped_column(Text, nullable=True)

    spec: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    spec_label: Mapped[str | None] = mapped_column(String(200), nullable=True)

    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    degraded: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    thread: Mapped["DataThread"] = relationship(back_populates="messages")
