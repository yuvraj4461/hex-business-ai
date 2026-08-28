from sqlalchemy.orm import Session

from app.models.global_event import (
    GlobalEvent,
)

from app.ai.context_builder import (
    build_ai_context,
)

from app.ai.business_analyst import (
    ask_business_ai,
)

from app.services.route_optimizer import (
    find_alternative_routes,
)


def run_red_sea_analysis(
    db: Session,
    organization_id: int,
) -> dict:

    event = (
        db.query(GlobalEvent)
        .filter(
            GlobalEvent.source
            == "HEX_SIMULATION",

            GlobalEvent.event_type
            == "LOGISTICS",
        )
        .order_by(
            GlobalEvent.detected_at.desc()
        )
        .first()
    )

    if not event:

        return {
            "status": "NO_SCENARIO",
            "message": (
                "No Red Sea simulation "
                "event found."
            ),
        }

    context = build_ai_context(
        db=db,
        organization_id=organization_id,
        event=event,
    )

    exposures = (
        context.get(
            "exposure",
            {},
        ).get(
            "exposures",
            [],
        )
    )

    alternatives = []

    for exposure in exposures:

        route_id = exposure.get(
            "route_id"
        )

        if not route_id:
            continue

        alternatives.extend(
            find_alternative_routes(
                db=db,
                organization_id=(
                    organization_id
                ),
                affected_route_id=(
                    route_id
                ),
                event=event,
            )
        )

    context[
        "route_alternatives"
    ] = alternatives

    question = """
A Red Sea disruption has affected this business.

Analyze the situation.

Identify:
1. The most important business impact.
2. The affected suppliers/products/routes.
3. The best available alternative route.
4. The financial trade-off.
5. The main uncertainty.

Do not claim any action has been executed.
"""

    recommendation = ask_business_ai(
    question=question,
    context=context,
    )

    if not recommendation:
        recommendation = (
            "HEX completed the disruption analysis "
            "but no AI recommendation was generated."
        )

    return {
        "status": "OK",
        "event": context[
            "global_event"
        ],
        "exposure": context[
            "exposure"
        ],
        "market": context[
            "market"
        ],
        "demand": context[
            "business"
        ][
            "demand_forecast"
        ],
        "agriculture": context[
            "agriculture"
        ],
        "route_alternatives":
            alternatives,
        "ai_recommendation":
            recommendation,
    }