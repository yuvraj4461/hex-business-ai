from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    scenario_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenarios.id"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    recommendation_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="MEDIUM",
    )

    reasoning: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    estimated_cost: Mapped[float | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    estimated_benefit: Mapped[float | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING_APPROVAL",
    )

    extra_data: Mapped[dict | None] = mapped_column(
    JSON,
    nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )