from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.global_event import GlobalEvent
from app.schemas.global_event import GlobalEventResponse
from app.security.dependencies import require_permission


router = APIRouter(
    prefix="/global-events",
    tags=["Global Events"],
)


@router.get(
    "/",
    response_model=list[GlobalEventResponse],
)
def get_global_events(
    event_type: str | None = Query(
        default=None,
    ),
    severity: str | None = Query(
        default=None,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
    _user=Depends(
        require_permission("view_analytics")
    ),
):
    query = db.query(
        GlobalEvent
    )

    if event_type:
        query = query.filter(
            GlobalEvent.event_type
            == event_type.upper()
        )

    if severity:
        query = query.filter(
            GlobalEvent.severity
            == severity.upper()
        )

    return (
        query
        .order_by(
            GlobalEvent.detected_at.desc()
        )
        .limit(limit)
        .all()
    )

@router.get(
    "/critical",
    response_model=list[GlobalEventResponse],
)
def get_critical_events(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
    _user=Depends(
        require_permission("view_analytics")
    ),
):
    return (
        db.query(GlobalEvent)
        .filter(
            GlobalEvent.severity.in_(
                [
                    "HIGH",
                    "CRITICAL",
                ]
            )
        )
        .order_by(
            GlobalEvent.detected_at.desc()
        )
        .limit(limit)
        .all()
    )