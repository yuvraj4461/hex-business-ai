from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.models._mixins import SourceTrackedMixin


class Inventory(SourceTrackedMixin, Base):
    __tablename__ = "inventory"

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

    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"),
        nullable=True,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    reorder_level: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    safety_stock: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    