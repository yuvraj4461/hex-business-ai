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
    Return stored business exposure records for the
    selected event.

    The BusinessExposure table is the authoritative
    production exposure source because the Scenario
    engine already uses it. When there are no stored
    rows yet, they are computed once from what is in
    transit (see app.services.exposure_recompute).
    """

    exposures = (
        db.query(BusinessExposure)
        .filter(
            BusinessExposure.organization_id
            == organization_id,

            BusinessExposure.global_event_id
            == event.id,
        )
        .order_by(
            BusinessExposure.detected_at.desc()
        )
        .all()
    )

    if not exposures:
        from app.services.exposure_recompute import recompute_exposure

        if recompute_exposure(db, organization_id, event):
            exposures = (
                db.query(BusinessExposure)
                .filter(
                    BusinessExposure.organization_id == organization_id,
                    BusinessExposure.global_event_id == event.id,
                )
                .order_by(BusinessExposure.detected_at.desc())
                .all()
            )

    results = []

    for exposure in exposures:

        route = (
            db.query(SupplyRoute)
            .filter(
                SupplyRoute.id
                == exposure.route_id,

                SupplyRoute.organization_id
                == organization_id,
            )
            .first()
        )

        results.append(
            {
                "event_id": event.id,

                "route_id":
                    exposure.route_id,

                "supplier_id":
                    exposure.supplier_id,

                "product_id":
                    exposure.product_id,

                "exposure_type":
                    exposure.exposure_type,

                "severity":
                    exposure.severity,

                "delay_days":
                    exposure.estimated_delay_days,

                "cost_impact":
                    float(
                        exposure.estimated_cost_impact
                        or 0
                    ),

                "revenue_at_risk":
                    float(
                        exposure.estimated_revenue_at_risk
                        or 0
                    ),

                "route_name":
                    (
                        route.route_name
                        if route
                        else None
                    ),

                "corridor":
                    (
                        route.corridor
                        if route
                        else None
                    ),

                "explanation":
                    exposure.explanation,
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

                "route_count":
                    0,

                "product_count":
                    0,

                "max_severity":
                    "LOW",

                "delay_days":
                    0,

                "cost_impact":
                    0.0,

                "revenue_at_risk":
                    0.0,
            }

        supplier = (
            supplier_map[
                supplier_id
            ]
        )

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
            and supplier[
                "max_severity"
            ] != "HIGH"
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

                "route_count":
                    0,

                "delay_days":
                    0,

                "cost_impact":
                    0.0,

                "revenue_at_risk":
                    0.0,

                "max_severity":
                    "LOW",
            }

        product = (
            product_map[
                product_id
            ]
        )

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


def calculate_business_risk(
    exposure_results: list[dict],
) -> dict:

    if not exposure_results:

        return {
            "level": "LOW",
            "score": 0,
            "exposure_count": 0,
        }

    has_high = any(
        item["severity"] == "HIGH"
        for item in exposure_results
    )

    has_medium = any(
        item["severity"] == "MEDIUM"
        for item in exposure_results
    )

    if has_high:

        score = 80
        level = "HIGH"

    elif has_medium:

        score = 50
        level = "MEDIUM"

    else:

        score = 20
        level = "LOW"

    return {
        "level": level,
        "score": score,
        "exposure_count":
            len(exposure_results),
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

    business_risk = (
        calculate_business_risk(
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

        "exposures":
            exposures,

        "suppliers":
            suppliers,

        "products":
            products,

        "financial":
            financial,

        "business_risk":
            business_risk,
    }