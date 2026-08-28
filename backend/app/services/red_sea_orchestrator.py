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


RED_SEA_QUESTION = """
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


# Event types whose impact is financial/market rather than route-level:
# still worth an AI read even when no shipping lane is directly hit.
MACRO_EVENT_TYPES = {"ECONOMIC", "PRICE_SHOCK", "TRADE", "GEOPOLITICAL"}


def _macro_question(event: GlobalEvent) -> str:
    title = (event.title or "this event").strip()
    return f"""
A market / macro event has been detected: "{title}"
(type: {event.event_type}). It does not directly disrupt any specific
shipping route in this business.

Using ONLY the supplied HEX context (financials, expenses, demand,
market / FX / commodity signals), assess:
1. Which cost lines or input commodities could be affected, and in which
   direction.
2. Whether the FX or commodity signals already in the context corroborate
   a real move, or whether this is just forward-looking commentary.
3. The likely margin impact — qualitative only, do NOT invent numbers.
4. What the business should monitor next.

Be concise. If the likely impact is negligible, say so plainly.
Do not claim any action has been executed.
"""


def _question_for(event: GlobalEvent) -> str:
    title = (event.title or "this event").strip()
    region = (event.region or event.country or "").strip()
    where = f" affecting {region}" if region else ""
    return f"""
An external event has been detected: "{title}"{where}
(type: {event.event_type}, severity: {event.severity}).

Analyze how this event affects the business.

Identify:
1. The most important business impact (or state clearly if there is none).
2. The affected suppliers/products/routes.
3. The best available alternative route, if a route is affected.
4. The financial trade-off.
5. The main uncertainty.

Do not claim any action has been executed.
"""


def _analyze_event(
    db: Session,
    organization_id: int,
    event: GlobalEvent,
    question: str,
) -> dict:

    context = build_ai_context(
        db=db,
        organization_id=organization_id,
        event=event,
    )

    exposures = (
        context.get("exposure", {}).get("exposures", [])
    )

    alternatives = []

    for exposure in exposures:

        route_id = exposure.get("route_id")

        if not route_id:
            continue

        alternatives.extend(
            find_alternative_routes(
                db=db,
                organization_id=organization_id,
                affected_route_id=route_id,
                event=event,
            )
        )

    context["route_alternatives"] = alternatives

    affected = len(exposures)
    event_type = getattr(event, "event_type", "") or ""

    if affected == 0 and event_type not in MACRO_EVENT_TYPES:
        recommendation = (
            "This event does not intersect any of your active supply "
            "routes or open shipments, so HEX projects no direct "
            "operational or financial exposure. Continue monitoring."
        )
    else:
        if affected == 0:
            question = _macro_question(event)
        recommendation = ask_business_ai(
            question=question,
            context=context,
        )
        if not recommendation:
            recommendation = (
                "HEX completed the analysis but no AI recommendation "
                "was generated."
            )

    return {
        "status": "OK",
        "event": context["global_event"],
        "exposure": context["exposure"],
        "market": context["market"],
        "demand": context["business"]["demand_forecast"],
        "agriculture": context["agriculture"],
        "route_alternatives": alternatives,
        "ai_recommendation": recommendation,
    }


def run_red_sea_analysis(
    db: Session,
    organization_id: int,
) -> dict:

    event = (
        db.query(GlobalEvent)
        .filter(
            GlobalEvent.source == "HEX_SIMULATION",
            GlobalEvent.event_type == "LOGISTICS",
        )
        .order_by(GlobalEvent.detected_at.desc())
        .first()
    )

    if not event:
        return {
            "status": "NO_SCENARIO",
            "message": "No Red Sea simulation event found.",
        }

    return _analyze_event(
        db, organization_id, event, RED_SEA_QUESTION
    )


def run_event_scenario(
    db: Session,
    organization_id: int,
    event_id: int,
) -> dict:
    """Generic per-event scenario analysis for any global event."""

    event = (
        db.query(GlobalEvent)
        .filter(GlobalEvent.id == event_id)
        .first()
    )

    if not event:
        return {
            "status": "NOT_FOUND",
            "message": f"No global event with id {event_id}.",
        }

    return _analyze_event(
        db, organization_id, event, _question_for(event)
    )
