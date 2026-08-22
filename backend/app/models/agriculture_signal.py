from datetime import datetime

from sqlalchemy import (
    DateTime,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class AgricultureSignal(Base):
    __tablename__ = "agriculture_signals"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    region: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    crop: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    signal_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    signal_value: Mapped[float] = mapped_column(
        Numeric(14, 4),
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="INFO",
    )

    source: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )