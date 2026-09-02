from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.ai.agent_context import (
    resolve_context,
)

from app.models.global_event import (
    GlobalEvent,
)

from app.services.risk_score import (
    calculate_business_risk_score,
)


def risk_agent(
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

    # Recent HIGH/CRITICAL events (last 48h) — a single "latest" event is
    # too narrow now that World Watch keeps feeding new ones.
    _cutoff = datetime.utcnow() - timedelta(hours=48)
    recent_high_events = (
        db.query(GlobalEvent)
        .filter(
            GlobalEvent.detected_at >= _cutoff,
            GlobalEvent.severity.in_(("HIGH", "CRITICAL")),
        )
        .order_by(GlobalEvent.detected_at.desc())
        .limit(20)
        .all()
    )

    # -------------------------------------------------
    # 3. Build complete HEX context
    # -------------------------------------------------

    context = resolve_context(
        state, db, organization_id, latest_event
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
    # 5. Get exposure data
    # -------------------------------------------------

    exposure_context = (
        context.get(
            "exposure"
        )
    )

    if exposure_context:

        # ---------------------------------------------
        # 6. Calculate unified business risk
        # ---------------------------------------------

        business_risk = (
            calculate_business_risk_score(
                exposure_context
            )
        )

    else:

        business_risk = {
            "score": 0,
            "level": "LOW",
            "exposure_count": 0,
            "high_risk_count": 0,
            "revenue_at_risk": 0.0,
        }

    # -------------------------------------------------
    # 7. Global event risk
    # -------------------------------------------------

    global_event = (
        context.get(
            "global_event"
        )
    )

    global_event_severity = None

    if global_event:

        global_event_severity = (
            global_event.get(
                "severity"
            )
        )

    # -------------------------------------------------
    # 8. Market risk
    # -------------------------------------------------

    market_context = (
        context.get(
            "market",
            {},
        )
    )

    commodities = (
        market_context.get(
            "commodities",
            {},
        )
    )

    commodity_risks = []

    for (
        commodity_name,
        analysis,
    ) in commodities.items():

        if not isinstance(
            analysis,
            dict,
        ):
            continue

        if (
            analysis.get(
                "status"
            )
            != "OK"
        ):
            continue

        percentage_change = float(
            analysis.get(
                "percentage_change",
                0,
            )
        )

        if abs(
            percentage_change
        ) >= 5:

            commodity_risks.append(
                {
                    "commodity":
                        commodity_name,

                    "percentage_change":
                        percentage_change,

                    "direction":
                        analysis.get(
                            "direction"
                        ),
                }
            )

    # -------------------------------------------------
    # 9. Agriculture risk
    # -------------------------------------------------

    agriculture = (
        context.get(
            "agriculture",
            [],
        )
    )

    agriculture_risks = [
        signal
        for signal in agriculture
        if signal.get(
            "severity"
        ) in {
            "HIGH",
            "CRITICAL",
        }
    ]

    # -------------------------------------------------
    # 10. Demand risk
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

    demand_risks = [
        item
        for item in demand_forecast
        if float(
            item.get(
                "growth_rate",
                0,
            )
        ) >= 0.20
    ]

    # -------------------------------------------------
    # 11. Risk finding
    # -------------------------------------------------

    findings.append(
        {
            "agent":
                "Risk Agent",

            "type":
                "enterprise_risk_analysis",

            "data": {
                "business_risk":
                    business_risk,

                "global_event":
                    global_event,

                "global_event_severity":
                    global_event_severity,

                "recent_high_events": [
                    {
                        "title": ev.title,
                        "type": ev.event_type,
                        "severity": ev.severity,
                        "source": ev.source,
                    }
                    for ev in recent_high_events
                ],

                "commodity_risks":
                    commodity_risks,

                "agriculture_risks":
                    agriculture_risks,

                "demand_risks":
                    demand_risks,
            },
        }
    )

    # -------------------------------------------------
    # 12. High enterprise risk
    # -------------------------------------------------

    risk_level = (
        business_risk.get(
            "level",
            "LOW",
        )
    )

    if risk_level in {
        "HIGH",
        "CRITICAL",
    }:

        recommendations.append(
            {
                "agent":
                    "Risk Agent",

                "type":
                    "high_business_risk",

                "reason": (
                    "The combined business "
                    "exposure has reached a "
                    f"{risk_level.lower()} "
                    "risk level."
                ),

                "risk_score":
                    business_risk.get(
                        "score",
                        0,
                    ),

                "risk_level":
                    risk_level,

                "revenue_at_risk":
                    business_risk.get(
                        "revenue_at_risk",
                        0,
                    ),
            }
        )

    # -------------------------------------------------
    # 13. High-severity global event
    # -------------------------------------------------

    if global_event_severity in {
        "HIGH",
        "CRITICAL",
    }:

        recommendations.append(
            {
                "agent":
                    "Risk Agent",

                "type":
                    "global_event_risk",

                "reason": (
                    "A high-severity global "
                    "event may create "
                    "material operational "
                    "or financial risk."
                ),

                "event":
                    (
                        global_event.get(
                            "title"
                        )
                        if global_event
                        else None
                    ),

                "severity":
                    global_event_severity,
            }
        )

    # -------------------------------------------------
    # 14. Commodity risk
    # -------------------------------------------------

    if commodity_risks:

        recommendations.append(
            {
                "agent":
                    "Risk Agent",

                "type":
                    "commodity_volatility",

                "reason": (
                    "One or more tracked "
                    "commodities show "
                    "material forecast "
                    "movement."
                ),

                "commodities":
                    commodity_risks,
            }
        )

    # -------------------------------------------------
    # 15. Agriculture risk
    # -------------------------------------------------

    if agriculture_risks:

        recommendations.append(
            {
                "agent":
                    "Risk Agent",

                "type":
                    "agriculture_supply_risk",

                "reason": (
                    "High-severity agriculture "
                    "signals may affect "
                    "commodity availability "
                    "or cost."
                ),

                "signal_count":
                    len(
                        agriculture_risks
                    ),
            }
        )

    # -------------------------------------------------
    # 16. Demand / supply mismatch
    # -------------------------------------------------

    if demand_risks:

        recommendations.append(
            {
                "agent":
                    "Risk Agent",

                "type":
                    "demand_pressure",

                "reason": (
                    "Strong demand growth may "
                    "increase inventory, "
                    "supplier and working "
                    "capital risk."
                ),

                "product_count":
                    len(
                        demand_risks
                    ),
            }
        )

    # -------------------------------------------------
    # 17. Human approval reminder
    # -------------------------------------------------

    if recommendations:

        recommendations.append(
            {
                "agent":
                    "Risk Agent",

                "type":
                    "human_review_required",

                "reason": (
                    "Material risk recommendations "
                    "should be reviewed by an "
                    "authorized decision maker "
                    "before execution."
                ),
            }
        )

    # -------------------------------------------------
    # 18. Return updated state
    # -------------------------------------------------

    return {
        **state,
        "findings": findings,
        "recommendations": recommendations,
    }