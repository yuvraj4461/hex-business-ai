from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.audit_log import AuditLog
from app.models.recommendation import Recommendation
from app.models.user import User
from app.security.dependencies import (
    require_permission,
)


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.post("/{recommendation_id}/approve")
def approve_recommendation(
    recommendation_id: int,
    current_user: User = Depends(
        require_permission(
            "approve_recommendations"
        )
    ),
    db: Session = Depends(get_db),
):

    recommendation = (
        db.query(Recommendation)
        .filter(
            Recommendation.id
            == recommendation_id,
            Recommendation.organization_id
            == current_user.organization_id,
        )
        .first()
    )

    if not recommendation:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found.",
        )

    recommendation.status = "APPROVED"

    audit = AuditLog(
        organization_id=(
            current_user.organization_id
        ),
        user_id=current_user.id,
        action="APPROVE_RECOMMENDATION",
        entity_type="Recommendation",
        entity_id=recommendation.id,
        description=(
            "Recommendation approved by human decision maker."
        ),
        data={
            "recommendation_id":
                recommendation.id,
        },
        created_at=datetime.utcnow(),
    )

    db.add(audit)
    db.commit()

    return {
        "message": "Recommendation approved.",
        "recommendation_id": recommendation.id,
        "status": recommendation.status,
    }