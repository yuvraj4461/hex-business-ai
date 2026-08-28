"""Derive shipments from open purchase orders.

When a business has no TMS / freight-forwarder feed, HEX still needs
something concrete to reason about. For every open PO without an ingested
shipment we project one: route = the supplier's active lane, ETD = the
order date, ETA = ETD + transit/lead time. Marked ``is_derived=True`` and
keyed on the PO so re-projection updates in place.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrder
from app.models.shipment import Shipment
from app.models.supplier import Supplier
from app.models.supply_route import SupplyRoute

_CLOSED_PO = {"CLOSED", "CANCELLED", "RECEIVED", "COMPLETE", "COMPLETED"}
_DEFAULT_TRANSIT_DAYS = 30


def _pick_route(
    db: Session, organization_id: int, supplier_id, product_id
) -> SupplyRoute | None:
    base = select(SupplyRoute).where(
        SupplyRoute.organization_id == organization_id,
        SupplyRoute.status == "ACTIVE",
    )

    filters: list[tuple] = []
    if supplier_id and product_id:
        filters.append(
            (
                SupplyRoute.supplier_id == supplier_id,
                SupplyRoute.product_id == product_id,
            )
        )
    if supplier_id:
        filters.append((SupplyRoute.supplier_id == supplier_id,))
    if product_id:
        filters.append((SupplyRoute.product_id == product_id,))

    for extra in filters:
        row = db.execute(base.where(*extra)).scalars().first()
        if row:
            return row
    return None


def _status_for(now: datetime, etd: datetime, eta: datetime) -> str:
    if now < etd:
        return "PLANNED"
    if now > eta:
        return "ARRIVED"
    return "IN_TRANSIT"


def project_shipments(db: Session, organization_id: int) -> dict:
    """Create/update derived shipments for open POs. Commits its own work."""

    now = datetime.utcnow()

    pos = db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.organization_id == organization_id
        )
    ).scalars().all()

    created = updated = skipped = 0

    for po in pos:
        if (po.status or "").upper() in _CLOSED_PO:
            skipped += 1
            continue

        # An ingested shipment for this PO wins — don't shadow it.
        ingested = db.execute(
            select(Shipment.id).where(
                Shipment.organization_id == organization_id,
                Shipment.purchase_order_id == po.id,
                Shipment.is_derived.is_(False),
            )
        ).scalar_one_or_none()
        if ingested:
            skipped += 1
            continue

        supplier = (
            db.get(Supplier, po.supplier_id) if po.supplier_id else None
        )
        route = _pick_route(
            db, organization_id, po.supplier_id, None
        )

        transit = (
            (route.transit_days if route else None)
            or (supplier.lead_time_days if supplier else None)
            or _DEFAULT_TRANSIT_DAYS
        )
        etd = po.order_date or po.created_at or now
        eta = etd + timedelta(days=int(transit))

        key = f"derived:po:{po.id}"
        existing = db.execute(
            select(Shipment).where(
                Shipment.organization_id == organization_id,
                Shipment.source_external_id == key,
            )
        ).scalar_one_or_none()

        fields = {
            "reference": f"PROJ-{po.po_number}",
            "purchase_order_id": po.id,
            "supplier_id": po.supplier_id,
            "route_id": route.id if route else None,
            "origin_country": (route.origin_country if route else None)
            or (supplier.country if supplier else None),
            "origin_port": route.origin_port if route else None,
            "destination_country": route.destination_country if route else None,
            "destination_port": route.destination_port if route else None,
            "transport_mode": route.transport_mode if route else "SEA",
            "status": _status_for(now, etd, eta),
            "etd": etd,
            "eta": eta,
            "value_amount": float(po.total_amount or 0),
            "currency": po.currency or "INR",
            "is_derived": True,
            "source_external_id": key,
            "synced_at": now,
        }

        if existing is None:
            db.add(Shipment(organization_id=organization_id, **fields))
            created += 1
        else:
            for k, v in fields.items():
                setattr(existing, k, v)
            updated += 1

    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}
