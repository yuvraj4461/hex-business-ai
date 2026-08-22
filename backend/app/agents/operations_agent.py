from sqlalchemy.orm import Session

from app.ai.agent_context import (
    get_agent_context,
)

from app.models.global_event import (
    GlobalEvent,
)

from app.services.route_optimizer import (
    find_alternative_routes,
)


def operations_agent(
    state: dict,
    db: Session,
) -> dict:

    # -------------------------------------------------
    # 1. Organization
    # -------------------------------------------------

    organization_id = (
        state["organization_id"]
    )

    # -------------------------------------------------
    # 2. Latest global event
    # -------------------------------------------------

    latest_event = (
        db.query(GlobalEvent)
        .order_by(
            GlobalEvent.detected_at.desc()
        )
        .first()
    )

    # -------------------------------------------------
    # 3. Build complete HEX context
    # -------------------------------------------------

    context = get_agent_context(
        db=db,
        organization_id=organization_id,
        event=latest_event,
    )

    # -------------------------------------------------
    # 4. Existing state
    # -------------------------------------------------

    findings = list(
        state.get(
            "findings",
            [],
        )
    )

    recommendations = list(
        state.get(
            "recommendations",
            [],
        )
    )

    # -------------------------------------------------
    # 5. Extract exposure
    # -------------------------------------------------

    exposure_context = (
        context.get(
            "exposure"
        )
    )

    exposure_list = []

    if exposure_context:

        exposure_list = (
            exposure_context.get(
                "exposures",
                [],
            )
        )

    # -------------------------------------------------
    # 6. Build operational findings
    # -------------------------------------------------

    affected_routes = []
    affected_suppliers = []
    affected_products = []

    for exposure in exposure_list:

        route_id = exposure.get(
            "route_id"
        )

        supplier_id = exposure.get(
            "supplier_id"
        )

        product_id = exposure.get(
            "product_id"
        )

        if route_id is not None:
            affected_routes.append(
                route_id
            )

        if supplier_id is not None:
            affected_suppliers.append(
                supplier_id
            )

        if product_id is not None:
            affected_products.append(
                product_id
            )

    # Remove duplicates
    affected_routes = list(
        dict.fromkeys(
            affected_routes
        )
    )

    affected_suppliers = list(
        dict.fromkeys(
            affected_suppliers
        )
    )

    affected_products = list(
        dict.fromkeys(
            affected_products
        )
    )

    # -------------------------------------------------
    # 7. Find alternative routes
    # -------------------------------------------------

    alternatives = []

    for route_id in affected_routes:

        try:

            route_options = (
                find_alternative_routes(
                    db=db,
                    organization_id=(
                        organization_id
                    ),
                    affected_route_id=(
                        route_id
                    ),
                )
            )

            alternatives.extend(
                route_options
            )

        except Exception:
            # One bad route should not
            # crash the entire agent.
            continue

    # -------------------------------------------------
    # 8. Operational finding
    # -------------------------------------------------

    findings.append(
        {
            "agent":
                "Operations Agent",

            "type":
                "operational_analysis",

            "data": {
                "global_event":
                    context.get(
                        "global_event"
                    ),

                "affected_routes":
                    affected_routes,

                "affected_suppliers":
                    affected_suppliers,

                "affected_products":
                    affected_products,

                "route_alternatives":
                    alternatives,

                "demand_forecast":
                    context.get(
                        "business",
                        {},
                    ).get(
                        "demand_forecast",
                        [],
                    ),

                "agriculture":
                    context.get(
                        "agriculture",
                        [],
                    ),
            },
        }
    )

    # -------------------------------------------------
    # 9. Operational disruption recommendation
    # -------------------------------------------------

    if affected_routes:

        recommendations.append(
            {
                "agent":
                    "Operations Agent",

                "type":
                    "route_disruption",

                "reason": (
                    "One or more active business "
                    "routes are exposed to a "
                    "global event."
                ),

                "affected_routes":
                    affected_routes,

                "alternative_count":
                    len(alternatives),
            }
        )

    # -------------------------------------------------
    # 10. High delay recommendation
    # -------------------------------------------------

    high_delay_exposures = [
        exposure
        for exposure in exposure_list
        if float(
            exposure.get(
                "delay_days",
                0,
            )
        ) >= 7
    ]

    if high_delay_exposures:

        recommendations.append(
            {
                "agent":
                    "Operations Agent",

                "type":
                    "high_delay_risk",

                "reason": (
                    "Operational delays of seven "
                    "or more days may affect "
                    "supply continuity."
                ),

                "exposure_count":
                    len(
                        high_delay_exposures
                    ),
            }
        )

    # -------------------------------------------------
    # 11. Alternative route recommendation
    # -------------------------------------------------

    if alternatives:

        low_risk_alternatives = [
            route
            for route in alternatives
            if route.get(
                "risk_level"
            ) == "LOW"
        ]

        if low_risk_alternatives:

            recommendations.append(
                {
                    "agent":
                        "Operations Agent",

                    "type":
                        "alternative_route_available",

                    "reason": (
                        "A lower-risk alternative "
                        "route is available for "
                        "an affected shipment."
                    ),

                    "routes":
                        low_risk_alternatives[:5],
                }
            )

    # -------------------------------------------------
    # 12. Demand + operations connection
    # -------------------------------------------------

    demand_forecast = (
        context.get(
            "business",
            {},
        ).get(
            "demand_forecast",
            [],
        )
    )

    high_growth_products = [
        item
        for item in demand_forecast
        if float(
            item.get(
                "growth_rate",
                0,
            )
        ) >= 0.20
    ]

    if (
        high_growth_products
        and affected_products
    ):

        recommendations.append(
            {
                "agent":
                    "Operations Agent",

                "type":
                    "demand_supply_mismatch",

                "reason": (
                    "Demand growth and supply "
                    "disruption may occur "
                    "simultaneously."
                ),

                "affected_products":
                    affected_products,

                "high_growth_product_count":
                    len(
                        high_growth_products
                    ),
            }
        )

    # -------------------------------------------------
    # 13. Return updated state
    # -------------------------------------------------

    return {
        **state,
        "findings": findings,
        "recommendations": recommendations,
    }