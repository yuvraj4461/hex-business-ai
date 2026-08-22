from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.global_event import (
    GlobalEvent,
)
from app.models.user import User

from app.security.dependencies import (
    require_permission,
)

from app.services.global_exposure import (
    build_global_exposure_summary,
)

from app.services.risk_score import (
    calculate_business_risk_score,
)


router = APIRouter(
    prefix="/global-exposure",
    tags=["Global Exposure"],
)


@router.get("/{event_id}")
def get_global_exposure(
    event_id: int,

    current_user: User = Depends(
        require_permission(
            "view_analytics"
        )
    ),

    db: Session = Depends(
        get_db
    ),
):

    event = (
        db.query(GlobalEvent)
        .filter(
            GlobalEvent.id
            == event_id
        )
        .first()
    )

    if not event:

        raise HTTPException(
            status_code=404,
            detail=(
                "Global event not found."
            ),
        )

    summary = (
        build_global_exposure_summary(
            db=db,
            organization_id=(
                current_user.organization_id
            ),
            event=event,
        )
    )

    risk = (
        calculate_business_risk_score(
            summary
        )
    )

    return {
        **summary,
        "business_risk": risk,
    }