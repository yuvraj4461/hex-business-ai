from sqlalchemy.orm import Session

from app.models.supply_route import SupplyRoute


def find_alternative_routes(
    db: Session,
    organization_id: int,
    affected_route_id: int,
) -> list[dict]:

    affected_route = (
        db.query(SupplyRoute)
        .filter(
            SupplyRoute.id
            == affected_route_id,
            SupplyRoute.organization_id
            == organization_id,
        )
        .first()
    )

    if not affected_route:
        return []

    alternatives = (
        db.query(SupplyRoute)
        .filter(
            SupplyRoute.organization_id
            == organization_id,
            SupplyRoute.id
            != affected_route_id,
            SupplyRoute.product_id
            == affected_route.product_id,
            SupplyRoute.status == "ACTIVE",
        )
        .all()
    )

    result = []

    for route in alternatives:

        if route.corridor == "RED_SEA":
            continue

        cost_delta = (
            float(route.freight_cost)
            - float(
                affected_route.freight_cost
            )
        )

        delay_delta = (
            route.transit_days
            - affected_route.transit_days
        )

        result.append(
            {
                "route_id": route.id,
                "route_name": (
                    route.route_name
                ),
                "corridor": route.corridor,
                "transport_mode": (
                    route.transport_mode
                ),
                "transit_days": (
                    route.transit_days
                ),
                "freight_cost": float(
                    route.freight_cost
                ),
                "cost_delta": cost_delta,
                "delay_delta_days": (
                    delay_delta
                ),
                "risk_level": (
                    route.risk_level
                ),
            }
        )

    result.sort(
        key=lambda item: (
            item["risk_level"] != "LOW",
            item["freight_cost"],
            item["transit_days"],
        )
    )

    return result