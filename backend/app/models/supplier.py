from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.models._mixins import SourceTrackedMixin


class Supplier(SourceTrackedMixin, Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    contact_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVE",
    )

    # Geography — needed to map a supplier onto a route/corridor and to
    # score its exposure to a located global event.
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)

    city: Mapped[str | None] = mapped_column(String(120), nullable=True)

    lead_time_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    