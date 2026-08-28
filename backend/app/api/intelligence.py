"""World Watch API — cron refresh, manual refresh, status, live feed."""

from __future__ import annotations

import hmac
import os
from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
)
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal, get_db
from app.intelligence.watcher import run_world_watch
from app.models.audit_log import AuditLog
from app.models.global_event import GlobalEvent
from app.models.user import User
from app.security.dependencies import require_permission

router = APIRouter(prefix="/intelligence", tags=["World Watch"])

FEED_SOURCES = ("GDELT", "WEB_SEARCH", "HEX_SIMULATION")


def _run_in_session() -> dict:
    db = SessionLocal()
    try:
        return run_world_watch(db)
    finally:
        db.close()


@router.post("/refresh", status_code=202)
def refresh_via_cron(
    background: BackgroundTasks,
    x_hex_cron_token: str | None = Header(default=None),
):
    """External cron target. Auth via the X-HEX-Cron-Token header."""

    expected = os.getenv("HEX_CRON_TOKEN")
    if not expected or not x_hex_cron_token or not hmac.compare_digest(
        str(expected), str(x_hex_cron_token)
    ):
        raise HTTPException(status_code=401, detail="Invalid cron token")

    background.add_task(_run_in_session)
    return {"status": "accepted"}


@router.post("/refresh-now")
def refresh_now(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("run_analysis")),
):
    """Run the refresh inline and return the summary."""

    return run_world_watch(db)


@router.get("/status")
def status(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("view_analytics")),
):
    last = db.execute(
        select(AuditLog)
        .where(AuditLog.action == "intelligence.refresh")
        .order_by(desc(AuditLog.created_at))
        .limit(1)
    ).scalar_one_or_none()

    day_ago = datetime.utcnow() - timedelta(hours=24)
    high_24h = db.execute(
        select(GlobalEvent).where(
            GlobalEvent.detected_at >= day_ago,
            GlobalEvent.severity.in_(("HIGH", "CRITICAL")),
            GlobalEvent.source.in_(FEED_SOURCES),
        )
    ).scalars().all()

    return {
        "last_run_at": last.created_at.isoformat() if last else None,
        "last_summary": (last.data if last else None),
        "high_events_24h": len(high_24h),
    }


@router.get("/feed")
def feed(
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("view_analytics")),
):
    rows = db.execute(
        select(GlobalEvent)
        .where(GlobalEvent.source.in_(FEED_SOURCES))
        .order_by(desc(GlobalEvent.detected_at))
        .limit(limit)
    ).scalars().all()

    return [
        {
            "id": e.id,
            "source": e.source,
            "event_type": e.event_type,
            "title": e.title,
            "summary": (e.raw_data or {}).get("answer") or e.description,
            "severity": e.severity,
            "region": e.region,
            "url": e.url,
            "sources": (e.raw_data or {}).get("sources", []),
            "detected_at": (
                e.detected_at.isoformat() if e.detected_at else None
            ),
        }
        for e in rows
    ]
