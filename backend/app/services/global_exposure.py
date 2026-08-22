from sqlalchemy.orm import Session

from app.models.business_exposure import (
    BusinessExposure,
)
from app.models.global_event import (
    GlobalEvent,
)
from app.models.supply_route import (
    SupplyRoute,
)


def analyze_global_event_exposure(
    db: Session,
    organization_id: int,
    event: GlobalEvent,
) -> list[dict]:
    """
    Determine which supply routes and business
    entities may be affected by a global event.

    This first version uses deterministic rules.
    AI will explain the results later.
    """

    routes = (
        db.query(SupplyRoute)
        .filter(
            SupplyRoute.organization_id
            == organization_id,
            SupplyRoute.status == "ACTIVE",
        )
        .all()
    )

    results = []

    event_type = (
        event.event_type or ""
    ).upper()

    region = (
        event.region or ""
    ).upper()

    title = (
        event.title or ""
    ).upper()

    for route in routes:

        affected = False
        exposure_type = None
        severity = "LOW"

        # ---------------------------------------
        # Logistics / shipping disruption
        # ---------------------------------------

        if event_type == "LOGISTICS":

            if (
                route.corridor
                == "RED_SEA"
            ):
                affected = True
                exposure_type = (
                    "ROUTE_DISRUPTION"
                )
                severity = "HIGH"

        # ---------------------------------------
        # Geopolitical event
        # ---------------------------------------

        elif event_type == "GEOPOLITICAL":

            if (
                route.corridor
                == "RED_SEA"
                or "RED SEA" in region
                or "RED SEA" in title
            ):
                affected = True
                exposure_type = (
                    "GEOPOLITICAL_ROUTE_RISK"
                )
                severity = "HIGH"

        # ---------------------------------------
        # Trade events
        # ---------------------------------------

        elif event_type == "TRADE":

            affected = True
            exposure_type = (
                "TRADE_DISRUPTION"
            )
            severity = "MEDIUM"

        if not affected:
            continue

        if severity == "HIGH":

            delay_days = (
                14
                if route.corridor
                == "RED_SEA"
                else 7
            )

            cost_impact = (
                float(
                    route.freight_cost
                )
                * 0.25
            )

            revenue_at_risk = (
                cost_impact * 2
            )

        else:

            delay_days = 5

            cost_impact = (
                float(
                    route.freight_cost
                )
                * 0.10
            )

            revenue_at_risk = (
                cost_impact
                * 1.5
            )

        results.append(
            {
                "event_id": event.id,
                "route_id": route.id,
                "supplier_id": route.supplier_id,
                "product_id": route.product_id,
                "exposure_type": exposure_type,
                "severity": severity,
                "delay_days": delay_days,
                "cost_impact": cost_impact,
                "revenue_at_risk":
                    revenue_at_risk,
                "route_name":
                    route.route_name,
                "corridor":
                    route.corridor,
            }
        )

    return results

def summarize_supplier_impact(
    exposure_results: list[dict],
) -> list[dict]:

    supplier_map = {}

    for item in exposure_results:

        supplier_id = (
            item["supplier_id"]
        )

        if supplier_id not in supplier_map:

            supplier_map[
                supplier_id
            ] = {
                "supplier_id":
                    supplier_id,
                "route_count": 0,
                "product_count": 0,
                "max_severity": "LOW",
                "delay_days": 0,
                "cost_impact": 0.0,
                "revenue_at_risk": 0.0,
            }

        supplier = supplier_map[
            supplier_id
        ]

        supplier["route_count"] += 1

        if item["product_id"] is not None:
            supplier[
                "product_count"
            ] += 1

        supplier["delay_days"] = max(
            supplier["delay_days"],
            item["delay_days"],
        )

        supplier["cost_impact"] += (
            item["cost_impact"]
        )

        supplier[
            "revenue_at_risk"
        ] += item[
            "revenue_at_risk"
        ]

        if item["severity"] == "HIGH":
            supplier[
                "max_severity"
            ] = "HIGH"

        elif (
            item["severity"] == "MEDIUM"
            and supplier["max_severity"]
            != "HIGH"
        ):
            supplier[
                "max_severity"
            ] = "MEDIUM"

    return list(
        supplier_map.values()
    )

def summarize_product_impact(
    exposure_results: list[dict],
) -> list[dict]:

    product_map = {}

    for item in exposure_results:

        product_id = (
            item["product_id"]
        )

        if product_id is None:
            continue

        if product_id not in product_map:

            product_map[
                product_id
            ] = {
                "product_id":
                    product_id,
                "route_count": 0,
                "delay_days": 0,
                "cost_impact": 0.0,
                "revenue_at_risk": 0.0,
                "max_severity": "LOW",
            }

        product = product_map[
            product_id
        ]

        product[
            "route_count"
        ] += 1

        product["delay_days"] = max(
            product["delay_days"],
            item["delay_days"],
        )

        product["cost_impact"] += (
            item["cost_impact"]
        )

        product[
            "revenue_at_risk"
        ] += item[
            "revenue_at_risk"
        ]

        if item["severity"] == "HIGH":

            product[
                "max_severity"
            ] = "HIGH"

        elif (
            item["severity"] == "MEDIUM"
            and product[
                "max_severity"
            ] != "HIGH"
        ):

            product[
                "max_severity"
            ] = "MEDIUM"

    return list(
        product_map.values()
    )

def summarize_financial_impact(
    exposure_results: list[dict],
) -> dict:

    total_cost = sum(
        item["cost_impact"]
        for item in exposure_results
    )

    total_revenue_at_risk = sum(
        item["revenue_at_risk"]
        for item in exposure_results
    )

    return {
        "affected_routes":
            len(exposure_results),

        "total_cost_impact":
            total_cost,

        "total_revenue_at_risk":
            total_revenue_at_risk,
    }

def build_global_exposure_summary(
    db: Session,
    organization_id: int,
    event: GlobalEvent,
) -> dict:

    exposures = (
        analyze_global_event_exposure(
            db=db,
            organization_id=organization_id,
            event=event,
        )
    )

    suppliers = (
        summarize_supplier_impact(
            exposures
        )
    )

    products = (
        summarize_product_impact(
            exposures
        )
    )

    financial = (
        summarize_financial_impact(
            exposures
        )
    )

    return {
        "event": {
            "id": event.id,
            "type": event.event_type,
            "title": event.title,
            "severity": event.severity,
            "region": event.region,
        },

        "exposures": exposures,

        "suppliers": suppliers,

        "products": products,

        "financial": financial,
    }