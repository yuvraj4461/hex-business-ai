from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.models._mixins import SourceTrackedMixin


class PurchaseOrder(SourceTrackedMixin, Base):
    """An inbound order placed with a supplier.

    HEX already models customer demand (`orders`); procurement is the other
    half and is what disruption exposure is computed against — an open PO
    on a route through a closed corridor is money and inventory at risk.
    """

    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=True,
        index=True,
    )

    po_number: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OPEN",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )

    total_amount: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=0,
    )

    incoterm: Mapped[str | None] = mapped_column(String(10), nullable=True)

    order_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    expected_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class PurchaseOrderLine(SourceTrackedMixin, Base):
    __tablename__ = "purchase_order_lines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"),
        nullable=True,
        index=True,
    )

    material_symbol: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    quantity: Mapped[float] = mapped_column(
        Numeric(14, 4),
        nullable=False,
        default=0,
    )

    unit_cost: Mapped[float] = mapped_column(
        Numeric(14, 4),
        nullable=False,
        default=0,
    )
