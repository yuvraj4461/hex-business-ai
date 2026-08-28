from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.models._mixins import SourceTrackedMixin

SHIPMENT_STATUSES = (
    "PLANNED",
    "IN_TRANSIT",
    "ARRIVED",
    "DELAYED",
    "CANCELLED",
)

# Statuses whose goods are still exposed to a disruption.
SHIPMENT_OPEN_STATUSES = ("PLANNED", "IN_TRANSIT", "DELAYED")


class Shipment(SourceTrackedMixin, Base):
    """An inbound movement of goods against a purchase order.

    This is the object a route disruption actually hits: a container on a
    corridor, with a value and an ETA. Shipments are either ingested from a
    TMS / freight-forwarder feed or **derived** from an open PO plus the
    supplier lead time and route transit time (`is_derived=True`).
    """

    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    purchase_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
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

    route_id: Mapped[int | None] = mapped_column(
        ForeignKey("supply_routes.id"),
        nullable=True,
        index=True,
    )

    reference: Mapped[str] = mapped_column(String(120), nullable=False)

    origin_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    origin_port: Mapped[str | None] = mapped_column(String(150), nullable=True)
    destination_country: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    destination_port: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )

    carrier: Mapped[str | None] = mapped_column(String(150), nullable=True)
    transport_mode: Mapped[str] = mapped_column(
        String(50), nullable=False, default="SEA"
    )

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PLANNED"
    )

    etd: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    eta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ata: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    value_amount: Mapped[float] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR"
    )

    is_derived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
