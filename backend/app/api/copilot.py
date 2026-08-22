from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.runner import run_business_agents

from app.ai.agent_synthesis import (
    synthesize_agent_findings,
)

from app.ai.context_builder import (
    build_ai_context,
)

from app.database.connection import get_db

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
    # -------------------------------------------------
    # 1. Get organization
    # -------------------------------------------------

    organization_id = (
        current_user.organization_id
    )

    # -------------------------------------------------
    # 2. Get the latest global event
    # -------------------------------------------------

    latest_event = (
        db.query(GlobalEvent)
        .order_by(
            GlobalEvent.detected_at.desc()
        )
        .first()
    )

    # -------------------------------------------------
    # 3. Build complete HEX AI context
    # -------------------------------------------------

    context = build_ai_context(
        db=db,
        organization_id=organization_id,
        event=latest_event,
    )

    # -------------------------------------------------
    # 4. Run existing business agents
    # -------------------------------------------------

    agent_result = run_business_agents(
        question=request.question,
        organization_id=organization_id,
        db=db,
    )

    findings = agent_result.get(
        "findings",
        [],
    )

    recommendations = agent_result.get(
        "recommendations",
        [],
    )

    # -------------------------------------------------
    # 5. Add global context to agent findings
    # -------------------------------------------------

    findings.append(
        {
            "source": "GLOBAL_CONTEXT",
            "data": context,
        }
    )

    # -------------------------------------------------
    # 6. Synthesize the final response
    # -------------------------------------------------

    answer = synthesize_agent_findings(
        question=request.question,
        findings=findings,
        recommendations=recommendations,
    )

    # -------------------------------------------------
    # 7. Return answer + verified HEX context
    # -------------------------------------------------

    return {
        "question": request.question,
        "answer": answer,
        "data": context,
    }