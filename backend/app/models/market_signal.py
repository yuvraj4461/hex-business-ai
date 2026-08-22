from datetime import datetime

from sqlalchemy import (
    DateTime,
    JSON,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class MarketSignal(Base):
    __tablename__ = "market_signals"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    signal_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    value: Mapped[float] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    unit: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    base_currency: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    quote_currency: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )