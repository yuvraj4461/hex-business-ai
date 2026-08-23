from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.runner import run_business_agents

from app.ai.agent_synthesis import (
    synthesize_agent_findings,
)

from app.ai.context_builder import (
    build_ai_context,
)

from app.database.connection import (
    get_db,
)

from app.models.global_event import (
    GlobalEvent,
)

from app.models.user import User

from app.schemas.copilot import (
    CopilotRequest,
    CopilotResponse,
)

from app.security.dependencies import (
    require_permission,
)


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

    latest_event = (
        db.query(GlobalEvent)
        .order_by(
            GlobalEvent.detected_at.desc()
        )
        .first()
    )

    context = build_ai_context(
        db=db,
        organization_id=organization_id,
        event=latest_event,
    )

    verified = (
        context.get(
            "verified_facts",
            {},
        )
    )

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

    revenue_at_risk = float(
        verified.get(
            "revenue_at_risk",
            0,
        )
        or 0
    )

    risk_score = verified.get(
        "business_risk",
        {},
    ).get(
        "score"
    )

    risk_level = verified.get(
        "business_risk",
        {},
    ).get(
        "level"
    )


    # -------------------------------------------------
    # DIRECT VERIFIED ANSWER FOR FACTUAL QUESTIONS
    # -------------------------------------------------

    if is_financial_fact_question(
        request.question
    ):

        answer = (
            "## Verified HEX Financial Summary\n\n"
            f"- **Revenue:** ₹{revenue:,.2f}\n"
            f"- **Expenses:** ₹{expenses:,.2f}\n"
            f"- **Profit:** ₹{profit:,.2f}\n"
            f"- **Number of Orders:** {orders}\n\n"
            "These figures are read directly from "
            "the organization's production database."
        )

        # Add current exposure when available.
        if latest_event:

            answer += (
                "\n\n## Current Risk Context\n\n"
                f"- **Latest Event:** "
                f"{latest_event.title}\n"
                f"- **Severity:** "
                f"{latest_event.severity}\n"
                f"- **Revenue at Risk:** "
                f"₹{revenue_at_risk:,.2f}\n"
            )

            if risk_level is not None:
                answer += (
                    f"- **Business Risk:** "
                    f"{risk_level}\n"
                )

            if risk_score is not None:
                answer += (
                    f"- **Risk Score:** "
                    f"{risk_score}/100\n"
                )

        return {
            "question":
                request.question,

            "answer":
                answer,

            "data":
                context,
        }


    # -------------------------------------------------
    # GENERAL AI QUESTIONS
    # -------------------------------------------------

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
                context.get(
                    "verified_facts",
                    {},
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
            "Treat VERIFIED_HEX_DATABASE as "
            "authoritative for revenue, expenses, "
            "profit, order count, and business "
            "exposure. Never claim those values "
            "are missing when they are present "
            "in verified_facts."
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