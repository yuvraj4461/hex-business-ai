from datetime import datetime

from sqlalchemy import (
    DateTime,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class CommodityForecast(Base):
    __tablename__ = "commodity_forecasts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    commodity_symbol: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    commodity_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    forecast_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    value: Mapped[float] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    source_report_date: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    is_forecast: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )