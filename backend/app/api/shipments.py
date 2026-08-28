"""Shipments API — in-transit view + projection from open POs."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.shipment import Shipment
from app.models.supply_route import SupplyRoute
from app.models.user import User
from app.security.dependencies import require_permission
from app.services.shipment_projection import project_shipments

router = APIRouter(prefix="/shipments", tags=["Shipments"])


class ShipmentOut(BaseModel):
    id: int
    reference: str
    status: str
    transport_mode: str
    carrier: str | None
    route_id: int | None
    route_name: str | None
    corridor: str | None
    origin: str | None
    destination: str | None
    etd: datetime | None
    eta: datetime | None
    value_amount: float
    currency: str
    is_derived: bool


@router.get("", response_model=list[ShipmentOut])
def list_shipments(
    status: str | None = Query(default=None),
    route_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("view_analytics")),
):
    stmt = select(Shipment).where(
        Shipment.organization_id == user.organization_id
    )
    if status:
        stmt = stmt.where(Shipment.status == status.upper())
    if route_id:
        stmt = stmt.where(Shipment.route_id == route_id)
    stmt = stmt.order_by(Shipment.eta.is_(None), Shipment.eta)

    rows = db.execute(stmt).scalars().all()
    routes = {
        r.id: r
        for r in db.execute(
            select(SupplyRoute).where(
                SupplyRoute.organization_id == user.organization_id
            )
        ).scalars()
    }

    out = []
    for s in rows:
        route = routes.get(s.route_id)
        out.append(
            ShipmentOut(
                id=s.id,
                reference=s.reference,
                status=s.status,
                transport_mode=s.transport_mode,
                carrier=s.carrier,
                route_id=s.route_id,
                route_name=route.route_name if route else None,
                corridor=route.corridor if route else None,
                origin=s.origin_port
                or (route.origin_port if route else None)
                or s.origin_country,
                destination=s.destination_port
                or (route.destination_port if route else None)
                or s.destination_country,
                etd=s.etd,
                eta=s.eta,
                value_amount=float(s.value_amount or 0),
                currency=s.currency,
                is_derived=s.is_derived,
            )
        )
    return out


@router.post("/project")
def project(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_data")),
):
    """Derive shipments from open purchase orders."""

    return project_shipments(db, user.organization_id)
