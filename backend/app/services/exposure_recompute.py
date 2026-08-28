"""Recompute business_exposures for an event from what is actually in transit.

This replaces pre-seeded exposure rows with data-driven ones. Output rows
have the same shape the rest of HEX expects
(`app/services/global_exposure.py` reads them), so `/global-exposure/{id}`,
`/demo/red-sea` and the Risk UI are unaffected — only the numbers get real.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business_exposure import BusinessExposure
from app.models.global_event import GlobalEvent
from app.models.shipment import Shipment, SHIPMENT_OPEN_STATUSES
from app.models.supply_route import SupplyRoute
from app.services import geo_exposure

# fraction of a lane's freight cost lost to a disruption, by severity
_COST_FACTOR = {"CRITICAL": 0.35, "HIGH": 0.25, "MEDIUM": 0.12, "LOW": 0.04}


def _severity(event: GlobalEvent) -> str:
    s = (event.severity or "MEDIUM").upper()
    return s if s in ("CRITICAL", "HIGH", "MEDIUM", "LOW") else "MEDIUM"


def _write(
    db: Session,
    *,
    organization_id: int,
    event: GlobalEvent,
    route: SupplyRoute | None,
    shipment: Shipment | None,
    supplier_id,
    product_id,
    severity: str,
    delay_days: int,
    reason: str,
) -> None:
    freight = float(route.freight_cost) if route else 0.0
    value = float(shipment.value_amount) if shipment else 0.0

    cost_impact = (
        freight * _COST_FACTOR.get(severity, 0.1)
        if freight
        else value * 0.15
    )
    revenue_at_risk = value or cost_impact * 2

    db.add(
        BusinessExposure(
            organization_id=organization_id,
            global_event_id=event.id,
            route_id=route.id if route else None,
            shipment_id=shipment.id if shipment else None,
            supplier_id=supplier_id,
            product_id=product_id,
            exposure_type="ROUTE_DISRUPTION",
            severity=severity,
            estimated_delay_days=delay_days,
            estimated_cost_impact=round(cost_impact, 2),
            estimated_revenue_at_risk=round(revenue_at_risk, 2),
            explanation=reason,
        )
    )


def recompute_exposure(
    db: Session, organization_id: int, event: GlobalEvent
) -> int:
    """Rebuild business_exposures for (org, event). Returns rows written."""

    db.query(BusinessExposure).filter(
        BusinessExposure.organization_id == organization_id,
        BusinessExposure.global_event_id == event.id,
    ).delete()

    severity = _severity(event)
    chokepoint = geo_exposure.is_chokepoint(event)
    delay = geo_exposure.disruption_delay_days(event, chokepoint)

    routes = {
        r.id: r
        for r in db.execute(
            select(SupplyRoute).where(
                SupplyRoute.organization_id == organization_id
            )
        ).scalars()
    }

    shipments = db.execute(
        select(Shipment).where(
            Shipment.organization_id == organization_id,
            Shipment.status.in_(SHIPMENT_OPEN_STATUSES),
        )
    ).scalars().all()

    written = 0
    routes_with_shipment: set[int] = set()

    # 1. Shipment-level exposure — actual goods in transit on an affected lane.
    for shipment in shipments:
        route = routes.get(shipment.route_id)
        affected, reason = geo_exposure.event_affects(
            event,
            corridor=route.corridor if route else None,
            origin_country=(
                shipment.origin_country
                or (route.origin_country if route else None)
            ),
            destination_country=(
                shipment.destination_country
                or (route.destination_country if route else None)
            ),
        )
        if not affected:
            continue

        _write(
            db,
            organization_id=organization_id,
            event=event,
            route=route,
            shipment=shipment,
            supplier_id=shipment.supplier_id,
            product_id=shipment.product_id,
            severity=severity,
            delay_days=delay,
            reason=reason,
        )
        written += 1
        if shipment.route_id:
            routes_with_shipment.add(shipment.route_id)

    # 2. Route-level exposure — an affected lane with no current shipment is
    #    still a disrupted lane worth flagging (lower urgency).
    for route in routes.values():
        if route.status != "ACTIVE" or route.id in routes_with_shipment:
            continue
        affected, reason = geo_exposure.event_affects(
            event,
            corridor=route.corridor,
            origin_country=route.origin_country,
            destination_country=route.destination_country,
        )
        if not affected:
            continue
        _write(
            db,
            organization_id=organization_id,
            event=event,
            route=route,
            shipment=None,
            supplier_id=route.supplier_id,
            product_id=route.product_id,
            severity=severity,
            delay_days=delay,
            reason=reason,
        )
        written += 1

    db.commit()
    return written
