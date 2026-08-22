from sqlalchemy.orm import Session

from app.models.business_exposure import BusinessExposure
from app.models.supply_route import SupplyRoute


def evaluate_route_scenario(
    db: Session,
    organization_id: int,
    affected_route_id: int,
) -> dict:

    affected_route = (
        db.query(SupplyRoute)
        .filter(
            SupplyRoute.id == affected_route_id,
            SupplyRoute.organization_id
            == organization_id,
        )
        .first()
    )

    if not affected_route:
        return {
            "status": "ERROR",
            "message": "Affected route not found.",
        }

    alternatives = (
        db.query(SupplyRoute)
        .filter(
            SupplyRoute.organization_id
            == organization_id,
            SupplyRoute.product_id
            == affected_route.product_id,
            SupplyRoute.id != affected_route.id,
            SupplyRoute.status == "ACTIVE",
        )
        .all()
    )

    scenarios = []

    for route in alternatives:

        cost = float(route.freight_cost)
        days = route.transit_days

        scenarios.append(
            {
                "route_id": route.id,
                "route_name": route.route_name,
                "corridor": route.corridor,
                "transport_mode": route.transport_mode,
                "transit_days": days,
                "freight_cost": cost,
                "risk_level": route.risk_level,
            }
        )

    current_cost = float(
        affected_route.freight_cost
    )

    current_days = affected_route.transit_days

    current_exposure = (
        db.query(BusinessExposure)
        .filter(
            BusinessExposure.organization_id
            == organization_id,
            BusinessExposure.route_id
            == affected_route.id,
        )
        .order_by(
            BusinessExposure.detected_at.desc()
        )
        .first()
    )

    return {
        "status": "OK",
        "affected_route": {
            "route_id": affected_route.id,
            "route_name": affected_route.route_name,
            "corridor": affected_route.corridor,
            "transit_days": current_days,
            "freight_cost": current_cost,
            "risk_level": affected_route.risk_level,
        },
        "current_exposure": (
            {
                "severity": current_exposure.severity,
                "delay_days": (
                    current_exposure
                    .estimated_delay_days
                ),
                "cost_impact": float(
                    current_exposure
                    .estimated_cost_impact
                ),
                "revenue_at_risk": float(
                    current_exposure
                    .estimated_revenue_at_risk
                ),
            }
            if current_exposure
            else None
        ),
        "alternatives": scenarios,
    }