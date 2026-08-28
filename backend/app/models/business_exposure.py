from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class BusinessExposure(Base):
    __tablename__ = "business_exposures"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    global_event_id: Mapped[int] = mapped_column(
        ForeignKey("global_events.id"),
        nullable=False,
        index=True,
    )

    route_id: Mapped[int | None] = mapped_column(
        ForeignKey("supply_routes.id"),
        nullable=True,
        index=True,
    )

    shipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("shipments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=True,
        index=True,
    )

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"),
        nullable=True,
        index=True,
    )

    exposure_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    estimated_delay_days: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    estimated_cost_impact: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=0,
    )

    estimated_revenue_at_risk: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=0,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )