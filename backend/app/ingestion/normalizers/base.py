"""Normalizer contract + shared coercion / upsert helpers.

A normalizer turns one `RawRecord` into a row in a canonical table. Field
mapping (canonical_field -> source_column) comes from
``connection.config["mapping"][entity_type]``; when a column is not mapped
the canonical name is tried directly, so a HEX-template spreadsheet needs
no mapping at all.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from dateutil import parser as date_parser
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.sources.base import RawRecord


def to_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value).strip()


def to_float(value: Any) -> float | None:
    s = to_str(value)
    if s is None:
        return None
    s = s.replace(",", "").replace("₹", "").replace("$", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def to_int(value: Any) -> int | None:
    f = to_float(value)
    return None if f is None else int(f)


def to_date(value: Any) -> datetime | None:
    s = to_str(value)
    if s is None:
        return None
    try:
        return date_parser.parse(s, dayfirst=True)
    except (ValueError, OverflowError):
        return None


class Normalizer:
    entity_type: str = ""
    model: type = None  # SQLAlchemy model class

    def __init__(self, mapping: dict | None = None) -> None:
        self.mapping = mapping or {}

    def source_field(self, payload: dict, canonical: str) -> Any:
        """Value for a canonical field, honouring the configured mapping."""

        column = self.mapping.get(canonical, canonical)
        # case-insensitive column match for spreadsheet friendliness
        if column in payload:
            return payload[column]
        lowered = {str(k).lower(): v for k, v in payload.items()}
        return lowered.get(str(column).lower())

    # --- to implement per entity -------------------------------------

    def map(
        self,
        db: Session,
        raw: RawRecord,
        organization_id: int,
        connection_id: int,
    ) -> dict | None:
        """Return a canonical-column dict, or None to skip the record.

        `db` is available for foreign-key resolution (e.g. supplier name
        -> supplier_id); most normalizers ignore it.
        """
        raise NotImplementedError

    # --- generic upsert --------------------------------------------------

    def upsert(
        self,
        db: Session,
        mapped: dict,
        organization_id: int,
        connection_id: int,
        external_id: str,
    ) -> str:
        """Insert or update by (source_connection_id, source_external_id).

        Returns "inserted" | "updated".
        """

        model = self.model
        existing = db.execute(
            select(model).where(
                model.source_connection_id == connection_id,
                model.source_external_id == external_id,
            )
        ).scalar_one_or_none()

        # Only write fields the source actually provided; NOT NULL columns
        # then fall back to their model default on insert.
        mapped = {k: v for k, v in mapped.items() if v is not None}
        mapped.update(
            organization_id=organization_id,
            source_connection_id=connection_id,
            source_external_id=external_id,
            synced_at=datetime.utcnow(),
        )

        if existing is None:
            db.add(model(**mapped))
            return "inserted"

        for key, value in mapped.items():
            setattr(existing, key, value)
        return "updated"


def find_supplier_id(
    db: Session,
    organization_id: int,
    *,
    name: str | None = None,
    external_id: str | None = None,
    connection_id: int | None = None,
) -> int | None:
    """Resolve a supplier FK from a synced external id or a name match."""

    from app.models.supplier import Supplier

    if external_id and connection_id:
        row = db.execute(
            select(Supplier.id).where(
                Supplier.source_connection_id == connection_id,
                Supplier.source_external_id == str(external_id),
            )
        ).scalar_one_or_none()
        if row:
            return row

    if name:
        return db.execute(
            select(Supplier.id).where(
                Supplier.organization_id == organization_id,
                Supplier.name.ilike(name.strip()),
            )
        ).scalar_one_or_none()

    return None


def find_product_id(
    db: Session,
    organization_id: int,
    *,
    name: str | None = None,
    external_id: str | None = None,
    connection_id: int | None = None,
) -> int | None:
    from app.models.product import Product

    if external_id and connection_id:
        row = db.execute(
            select(Product.id).where(
                Product.source_connection_id == connection_id,
                Product.source_external_id == str(external_id),
            )
        ).scalar_one_or_none()
        if row:
            return row

    if name:
        return db.execute(
            select(Product.id).where(
                Product.organization_id == organization_id,
                Product.name.ilike(name.strip()),
            )
        ).scalar_one_or_none()

    return None
