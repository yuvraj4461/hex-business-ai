from sqlalchemy.orm import Session

from app.models.business_exposure import BusinessExposure
from app.models.global_event import GlobalEvent
from app.models.supply_route import SupplyRoute


def analyze_event_exposure(
    db: Session,
    event: GlobalEvent,
    organization_id: int,
) -> list[BusinessExposure]:

    routes = (
        db.query(SupplyRoute)
        .filter(
            SupplyRoute.organization_id
            == organization_id,
            SupplyRoute.status == "ACTIVE",
        )
        .all()
    )

    exposures = []

    for route in routes:

        affected = False

        if (
            event.event_type
            == "LOGISTICS"
            and route.corridor
            == "RED_SEA"
        ):
            affected = True

        if (
            event.event_type
            == "GEOPOLITICAL"
            and route.corridor
            in {
                "RED_SEA",
                "CAPE_OF_GOOD_HOPE",
            }
        ):
            affected = True

        if not affected:
            continue

        if route.corridor == "RED_SEA":
            delay = 14
            cost_impact = (
                float(route.freight_cost)
                * 0.25
            )
            severity = "HIGH"

        else:
            delay = 0
            cost_impact = 0
            severity = "LOW"

        revenue_at_risk = (
            cost_impact * 2
        )

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
            estimated_revenue_at_risk=(
                revenue_at_risk
            ),
            explanation=(
                f"Route {route.route_name} "
                f"is exposed to the event."
            ),
        )

        db.add(exposure)
        exposures.append(exposure)

    db.commit()

    return exposures