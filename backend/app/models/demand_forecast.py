from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    forecast_period: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    forecast_quantity: Mapped[float] = mapped_column(
        Numeric(14, 4),
        nullable=False,
    )

    baseline_quantity: Mapped[float] = mapped_column(
        Numeric(14, 4),
        nullable=False,
    )

    growth_rate: Mapped[float] = mapped_column(
        Numeric(8, 4),
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    method: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )