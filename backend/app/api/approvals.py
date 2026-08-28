from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User

from app.security.dependencies import (
    require_permission,
)


router = APIRouter(
    prefix="/approvals",
    tags=["Approvals"],
)


class ApprovalRequest(BaseModel):
    recommendation: str
    scenario: str
    event_id: int | None = None
    decision: str = "APPROVED"
    comment: str | None = None


_APPROVAL_STORE: list[dict] = []


@router.post("")
def create_approval(
    request: ApprovalRequest,
    current_user: User = Depends(
        require_permission(
            "run_analysis"
        )
    ),
    db: Session = Depends(get_db),
):
    status = (
        "REJECTED"
        if str(request.decision).upper() == "REJECTED"
        else "APPROVED"
    )

    approval = {
        "id": len(_APPROVAL_STORE) + 1,
        "organization_id": (
            current_user.organization_id
        ),
        "user_id": current_user.id,
        "recommendation": (
            request.recommendation
        ),
        "scenario": request.scenario,
        "event_id": request.event_id,
        "comment": request.comment,
        "status": status,
        "approved_at": (
            datetime.utcnow().isoformat()
        ),
    }

    _APPROVAL_STORE.append(
        approval
    )

    return {
        "status": status,
        "approval": approval,
    }


@router.get("")
def list_approvals(
    current_user: User = Depends(
        require_permission(
            "view_analytics"
        )
    ),
    db: Session = Depends(get_db),
):
    return [
        approval
        for approval in _APPROVAL_STORE
        if approval[
            "organization_id"
        ]
        == current_user.organization_id
    ]