from sqlalchemy.orm import Session

from app.services.analytics import (
    get_revenue_analysis,
)

from app.services.historical_analytics import (
    get_historical_snapshot,
)

from app.ai.agent_context import (
    get_agent_context,
)

from app.models.global_event import (
    GlobalEvent,
)


def finance_agent(
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
    # 2. Current financial data
    # -------------------------------------------------

    current_data = (
        get_revenue_analysis(
            db,
            organization_id,
        )
    )

    # -------------------------------------------------
    # 3. Historical financial data
    # -------------------------------------------------

    historical_data = (
        get_historical_snapshot(
            db,
            organization_id,
        )
    )

    # -------------------------------------------------
    # 4. Get latest global event
    # -------------------------------------------------

    latest_event = (
        db.query(GlobalEvent)
        .order_by(
            GlobalEvent.detected_at.desc()
        )
        .first()
    )

    # -------------------------------------------------
    # 5. Build complete HEX context
    # -------------------------------------------------

    global_context = get_agent_context(
        db=db,
        organization_id=organization_id,
        event=latest_event,
    )

    # -------------------------------------------------
    # 6. Existing agent state
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
    # 7. Existing financial finding
    # -------------------------------------------------

    findings.append(
        {
            "agent": "Finance Agent",
            "type": "financial_analysis",
            "data": {
                "revenue": current_data[
                    "revenue"
                ],
                "expenses": current_data[
                    "expenses"
                ],
                "profit": current_data[
                    "profit"
                ],
                "average_order_value": (
                    current_data[
                        "average_order_value"
                    ]
                ),
                "revenue_comparison": (
                    historical_data.get(
                        "revenue_comparison",
                        {},
                    )
                ),
            },
        }
    )

    # -------------------------------------------------
    # 8. Historical revenue analysis
    # -------------------------------------------------

    comparison = (
        historical_data.get(
            "revenue_comparison",
            {},
        )
    )

    if (
        comparison.get("status") == "OK"
        and comparison.get(
            "direction"
        ) == "DECREASED"
    ):

        recommendations.append(
            {
                "agent":
                    "Finance Agent",

                "type":
                    "investigate_revenue_decline",

                "reason": (
                    "Revenue declined compared "
                    "with the previous period."
                ),
            }
        )

    # -------------------------------------------------
    # 9. Add global intelligence finding
    # -------------------------------------------------

    market_context = (
        global_context.get(
            "market",
            {},
        )
    )

    exposure_context = (
        global_context.get(
            "exposure"
        )
    )

    agriculture_context = (
        global_context.get(
            "agriculture",
            [],
        )
    )

    demand_context = (
        global_context
        .get(
            "business",
            {},
        )
        .get(
            "demand_forecast",
            [],
        )
    )

    global_event_context = (
        global_context.get(
            "global_event"
        )
    )

    findings.append(
        {
            "agent": "Finance Agent",
            "type": "global_financial_context",
            "data": {
                "global_event":
                    global_event_context,

                "market":
                    market_context,

                "agriculture":
                    agriculture_context,

                "demand_forecast":
                    demand_context,

                "business_exposure":
                    exposure_context,
            },
        }
    )

    # -------------------------------------------------
    # 10. Evaluate revenue-at-risk
    # -------------------------------------------------

    if exposure_context:

        financial = (
            exposure_context.get(
                "financial",
                {},
            )
        )

        revenue_at_risk = float(
            financial.get(
                "total_revenue_at_risk",
                0,
            )
        )

        total_cost_impact = float(
            financial.get(
                "total_cost_impact",
                0,
            )
        )

        if revenue_at_risk > 0:

            recommendations.append(
                {
                    "agent":
                        "Finance Agent",

                    "type":
                        "global_event_financial_risk",

                    "reason": (
                        "A global event has created "
                        "financial exposure for the "
                        "business."
                    ),

                    "revenue_at_risk":
                        revenue_at_risk,

                    "cost_impact":
                        total_cost_impact,
                }
            )

    # -------------------------------------------------
    # 11. High-risk global event
    # -------------------------------------------------

    if global_event_context:

        event_severity = (
            global_event_context.get(
                "severity"
            )
        )

        if event_severity in {
            "HIGH",
            "CRITICAL",
        }:

            recommendations.append(
                {
                    "agent":
                        "Finance Agent",

                    "type":
                        "high_risk_global_event",

                    "reason": (
                        "A high-severity global "
                        "event may affect business "
                        "financial performance."
                    ),

                    "event":
                        global_event_context.get(
                            "title"
                        ),

                    "severity":
                        event_severity,
                }
            )

    # -------------------------------------------------
    # 12. Commodity risk
    # -------------------------------------------------

    commodities = (
        market_context.get(
            "commodities",
            {},
        )
    )

    for commodity_name, analysis in (
        commodities.items()
    ):

        if not isinstance(
            analysis,
            dict,
        ):
            continue

        if (
            analysis.get("status")
            != "OK"
        ):
            continue

        percentage_change = float(
            analysis.get(
                "percentage_change",
                0,
            )
        )

        if percentage_change >= 5:

            recommendations.append(
                {
                    "agent":
                        "Finance Agent",

                    "type":
                        "commodity_cost_risk",

                    "commodity":
                        commodity_name,

                    "percentage_change":
                        percentage_change,

                    "reason": (
                        f"{commodity_name} "
                        "increased materially "
                        "in the available "
                        "forecast data."
                    ),
                }
            )

    # -------------------------------------------------
    # 13. Agriculture risk
    # -------------------------------------------------

    high_agriculture_risks = [
        signal
        for signal in agriculture_context
        if signal.get(
            "severity"
        ) in {
            "HIGH",
            "CRITICAL",
        }
    ]

    if high_agriculture_risks:

        recommendations.append(
            {
                "agent":
                    "Finance Agent",

                "type":
                    "agriculture_cost_risk",

                "reason": (
                    "High-severity agriculture "
                    "signals may increase "
                    "commodity and supply costs."
                ),

                "risk_count":
                    len(
                        high_agriculture_risks
                    ),
            }
        )

    # -------------------------------------------------
    # 14. Demand growth context
    # -------------------------------------------------

    high_growth_products = [
        item
        for item in demand_context
        if float(
            item.get(
                "growth_rate",
                0,
            )
        ) >= 0.20
    ]

    if high_growth_products:

        recommendations.append(
            {
                "agent":
                    "Finance Agent",

                "type":
                    "high_demand_growth",

                "reason": (
                    "Some products show strong "
                    "forecast demand growth, "
                    "which may require additional "
                    "working capital or inventory."
                ),

                "product_count":
                    len(
                        high_growth_products
                    ),
            }
        )

    # -------------------------------------------------
    # 15. Return updated agent state
    # -------------------------------------------------

    return {
        **state,
        "findings": findings,
        "recommendations": recommendations,
    }