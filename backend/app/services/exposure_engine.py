"""Legacy route-level exposure writer.

Kept for backwards compatibility (test_red_sea.py). New code should use
`app.services.exposure_recompute.recompute_exposure`, which is
shipment-driven. This version now matches events geographically via
`app.services.geo_exposure` instead of a hard-coded Red Sea rule.
"""

from sqlalchemy.orm import Session

from app.models.business_exposure import BusinessExposure
from app.models.global_event import GlobalEvent
from app.models.supply_route import SupplyRoute
from app.services import geo_exposure


def analyze_event_exposure(
    db: Session,
    event: GlobalEvent,
    organization_id: int,
) -> list[BusinessExposure]:

    routes = (
        db.query(SupplyRoute)
        .filter(
            SupplyRoute.organization_id == organization_id,
            SupplyRoute.status == "ACTIVE",
        )
        .all()
    )

    severity = (event.severity or "MEDIUM").upper()
    chokepoint = geo_exposure.is_chokepoint(event)
    delay = geo_exposure.disruption_delay_days(event, chokepoint)

    exposures = []

    for route in routes:

        affected, reason = geo_exposure.event_affects(
            event,
            corridor=route.corridor,
            origin_country=route.origin_country,
            destination_country=route.destination_country,
        )
        if not affected:
            continue

        cost_impact = float(route.freight_cost) * (
            0.25 if severity in ("HIGH", "CRITICAL") else 0.1
        )
        revenue_at_risk = cost_impact * 2

        exposure = BusinessExposure(
            organization_id=organization_id,
            global_event_id=event.id,
            route_id=route.id,
            supplier_id=route.supplier_id,
            product_id=route.product_id,
            exposure_type="ROUTE_DISRUPTION",
            severity=severity,
            estimated_delay_days=delay,
            estimated_cost_impact=cost_impact,
            estimated_revenue_at_risk=revenue_at_risk,
            explanation=reason or f"Route {route.route_name} is exposed.",
        )

        db.add(exposure)
        exposures.append(exposure)

    db.commit()

    return exposures
