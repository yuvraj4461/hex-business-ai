from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.runner import run_business_agents
from app.ai.agent_synthesis import synthesize_agent_findings
from app.ai.context_builder import build_ai_context
from app.database.connection import get_db
from app.models.global_event import GlobalEvent
from app.models.user import User
from app.schemas.copilot import (
    CopilotRequest,
    CopilotResponse,
)
from app.security.dependencies import require_permission


router = APIRouter(
    prefix="/copilot",
    tags=["AI Copilot"],
)


def is_financial_fact_question(
    question: str,
) -> bool:

    text = question.lower()

    keywords = [
        "revenue",
        "expense",
        "expenses",
        "profit",
        "orders",
        "order count",
        "number of orders",
    ]

    return any(
        keyword in text
        for keyword in keywords
    )


def find_relevant_event(
    db: Session,
    question: str,
) -> GlobalEvent | None:

    text = question.lower()

    events = (
        db.query(GlobalEvent)
        .order_by(
            GlobalEvent.detected_at.desc()
        )
        .all()
    )

    # Prefer an event explicitly mentioned
    # in the user's question.
    for event in events:

        title = (
            event.title or ""
        ).lower()

        region = (
            event.region or ""
        ).lower()

        event_type = (
            event.event_type or ""
        ).lower()

        if (
            "red sea" in text
            and "red sea" in title
        ):
            return event

        if (
            "turkey" in text
            and (
                "turkey" in title
                or "turkey" in region
            )
        ):
            return event

        if (
            "france" in text
            and (
                "france" in title
                or "france" in region
            )
        ):
            return event

        if (
            event_type
            and event_type in text
        ):
            return event

    # Otherwise use the latest event.
    return events[0] if events else None


def is_red_sea_question(
    question: str,
) -> bool:

    text = question.lower()

    return (
        "red sea" in text
        or "shipping disruption" in text
        or "shipping route" in text
    )


@router.post(
    "/ask",
    response_model=CopilotResponse,
)
def ask_copilot(
    request: CopilotRequest,
    current_user: User = Depends(
        require_permission("run_analysis")
    ),
    db: Session = Depends(get_db),
):

    organization_id = (
        current_user.organization_id
    )

    # ---------------------------------------------
    # Select the event relevant to the question
    # ---------------------------------------------

    relevant_event = find_relevant_event(
        db,
        request.question,
    )

    # ---------------------------------------------
    # Build verified HEX context
    # ---------------------------------------------

    context = build_ai_context(
        db=db,
        organization_id=organization_id,
        event=relevant_event,
    )

    verified = context.get(
        "verified_facts",
        {},
    )

    # ---------------------------------------------
    # Direct verified financial answer
    # ---------------------------------------------

    if is_financial_fact_question(
        request.question
    ):

        revenue = float(
            verified.get(
                "revenue",
                0,
            )
            or 0
        )

        expenses = float(
            verified.get(
                "expenses",
                0,
            )
            or 0
        )

        profit = float(
            verified.get(
                "profit",
                0,
            )
            or 0
        )

        orders = int(
            verified.get(
                "orders",
                0,
            )
            or 0
        )

        answer = (
            "## Verified HEX Financial Summary\n\n"
            f"- **Revenue:** ₹{revenue:,.2f}\n"
            f"- **Expenses:** ₹{expenses:,.2f}\n"
            f"- **Profit:** ₹{profit:,.2f}\n"
            f"- **Number of Orders:** {orders}\n\n"
            "These values are taken directly from "
            "the organization's production database."
        )

        return {
            "question":
                request.question,

            "answer":
                answer,

            "data":
                context,
        }

    # ---------------------------------------------
    # Direct Red Sea answer
    # ---------------------------------------------

    if is_red_sea_question(
        request.question
    ):

        event = context.get(
            "global_event"
        ) or {}

        revenue_at_risk = float(
            verified.get(
                "revenue_at_risk",
                0,
            )
            or 0
        )

        affected_routes = int(
            verified.get(
                "affected_routes",
                0,
            )
            or 0
        )

        business_risk = (
            verified.get(
                "business_risk",
                {},
            )
            or {}
        )

        risk_level = (
            business_risk.get(
                "level"
            )
            or event.get(
                "severity"
            )
            or "UNKNOWN"
        )

        risk_score = (
            business_risk.get(
                "score"
            )
        )

        answer = (
            "## Red Sea Disruption Assessment\n\n"
            f"- **Event:** "
            f"{event.get('title', 'Simulated Red Sea shipping disruption')}\n"
            f"- **Severity:** "
            f"{event.get('severity', 'HIGH')}\n"
            f"- **Revenue at Risk:** "
            f"₹{revenue_at_risk:,.2f}\n"
            f"- **Affected Routes:** "
            f"{affected_routes}\n"
            f"- **Business Risk:** "
            f"{risk_level}\n"
        )

        if risk_score is not None:
            answer += (
                f"- **Risk Score:** "
                f"{risk_score}/100\n"
            )

        answer += (
            "\n## Recommended Actions\n\n"
            "1. **Activate alternative supply routes** "
            "for shipments exposed to the Red Sea.\n"
            "2. **Review supplier and inventory exposure** "
            "for products dependent on affected routes.\n"
            "3. **Compare the financial trade-off** between "
            "rerouting costs and the current revenue at risk.\n"
            "4. **Escalate the decision for human approval** "
            "before implementing a material route change."
        )

        return {
            "question":
                request.question,

            "answer":
                answer,

            "data":
                context,
        }

    # ---------------------------------------------
    # General AI questions
    # ---------------------------------------------

    agent_result = run_business_agents(
        question=request.question,
        organization_id=organization_id,
        db=db,
    )

    findings = list(
        agent_result.get(
            "findings",
            [],
        )
        or []
    )

    recommendations = list(
        agent_result.get(
            "recommendations",
            [],
        )
        or []
    )

    findings.append(
        {
            "source":
                "VERIFIED_HEX_DATABASE",

            "data":
                verified,
        }
    )

    findings.append(
        {
            "source":
                "RELEVANT_GLOBAL_EVENT",

            "data":
                context.get(
                    "global_event"
                ),
        }
    )

    findings.append(
        {
            "source":
                "GLOBAL_CONTEXT",

            "data":
                context,
        }
    )

    recommendations.append(
        (
            "Use the relevant global event selected "
            "from the user's question. Do not substitute "
            "an unrelated event merely because it is the "
            "latest event in the database."
        )
    )

    recommendations.append(
        (
            "Treat VERIFIED_HEX_DATABASE as authoritative "
            "for financial metrics and verified exposure."
        )
    )

    answer = synthesize_agent_findings(
        question=request.question,
        findings=findings,
        recommendations=recommendations,
    )

    return {
        "question":
            request.question,

        "answer":
            answer,

        "data":
            context,
    }