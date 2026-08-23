from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.global_event import GlobalEvent
from app.models.user import User
from app.security.dependencies import require_permission


router = APIRouter(
    prefix="/global-events",
    tags=["Global Events"],
)


@router.get("/")
def get_global_events(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(
        require_permission("view_analytics")
    ),
    db: Session = Depends(get_db),
):
    events = (
        db.query(GlobalEvent)
        .order_by(
            GlobalEvent.detected_at.desc()
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "id": event.id,
            "source": event.source,
            "external_id": event.external_id,
            "event_type": event.event_type,
            "title": event.title,
            "description": event.description,
            "url": event.url,
            "country": event.country,
            "region": event.region,
            "severity": event.severity,
            "source_published_at": (
                event.source_published_at.isoformat()
                if event.source_published_at
                else None
            ),
            "detected_at": (
                event.detected_at.isoformat()
                if event.detected_at
                else None
            ),
        }
        for event in events
    ]