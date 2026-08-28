from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.models._mixins import SourceTrackedMixin


class SupplyRoute(SourceTrackedMixin, Base):
    __tablename__ = "supply_routes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"),
        nullable=True,
        index=True,
    )

    route_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    origin_country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    origin_port: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    destination_country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    destination_port: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    transport_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SEA",
    )

    corridor: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    distance_km: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    transit_days: Mapped[int] = mapped_column(
        nullable=False,
    )

    freight_cost: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    risk_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="LOW",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVE",
    )