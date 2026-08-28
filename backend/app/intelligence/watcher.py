"""World Watch — the scheduled/cron-driven intelligence refresh.

Runs every collector, then recomputes supply-chain exposure for every
organization against any newly-detected HIGH/CRITICAL event. Never raises.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.orm import Session

from app.intelligence.collectors.fx import collect_fx
from app.intelligence.collectors.gdelt import collect_gdelt
from app.intelligence.collectors.web_search import collect_web_search
from app.models.audit_log import AuditLog
from app.models.global_event import GlobalEvent
from app.models.organization import Organization
from app.services.exposure_recompute import recompute_exposure

logger = logging.getLogger(__name__)

_HIGH = ("HIGH", "CRITICAL")


def _recent_high_events(db: Session, minutes: int = 90) -> list[GlobalEvent]:
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    return db.execute(
        select(GlobalEvent).where(
            GlobalEvent.detected_at >= cutoff,
            GlobalEvent.severity.in_(_HIGH),
        )
    ).scalars().all()


def run_world_watch(db: Session) -> dict:
    started = datetime.utcnow()
    summary: dict = {"started_at": started.isoformat()}
    errors: list[str] = []

    for name, fn in (
        ("gdelt", collect_gdelt),
        ("fx", collect_fx),
        ("web_search", collect_web_search),
    ):
        try:
            summary[name] = fn(db)
        except Exception as exc:  # noqa: BLE001
            logger.exception("World Watch collector %s failed", name)
            db.rollback()
            errors.append(f"{name}: {exc}")
            summary[name] = {"error": str(exc)}

    # Recompute exposure for every org against fresh HIGH-severity events.
    recomputes = 0
    try:
        high_events = _recent_high_events(db)
        if high_events:
            org_ids = db.execute(
                select(Organization.id)
            ).scalars().all()
            for org_id in org_ids:
                for event in high_events:
                    try:
                        recompute_exposure(db, org_id, event)
                        recomputes += 1
                    except Exception as exc:  # noqa: BLE001
                        db.rollback()
                        errors.append(
                            f"recompute org={org_id} event={event.id}: {exc}"
                        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("World Watch exposure recompute failed")
        errors.append(f"recompute: {exc}")

    # Prune noise: legacy "UNKNOWN"-severity rows from the deprecated
    # collector, and stale unclassified GDELT geocode entries.
    pruned = 0
    try:
        result = db.execute(
            delete(GlobalEvent).where(
                GlobalEvent.source == "GDELT",
                or_(
                    GlobalEvent.severity == "UNKNOWN",
                    and_(
                        GlobalEvent.event_type == "GENERAL",
                        GlobalEvent.detected_at
                        < datetime.utcnow() - timedelta(days=2),
                    ),
                ),
            )
        )
        pruned = result.rowcount or 0
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        errors.append(f"prune: {exc}")

    duration_ms = int(
        (datetime.utcnow() - started).total_seconds() * 1000
    )
    summary.update(
        exposure_recomputes=recomputes,
        pruned=pruned,
        errors=errors,
        duration_ms=duration_ms,
        finished_at=datetime.utcnow().isoformat(),
    )

    try:
        any_org = db.execute(
            select(Organization.id).limit(1)
        ).scalar_one_or_none()
        if any_org is not None:
            db.add(
                AuditLog(
                    organization_id=any_org,
                    action="intelligence.refresh",
                    entity_type="intelligence",
                    description="World Watch refresh",
                    data=summary,
                )
            )
            db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()

    logger.info(
        "World Watch done in %dms: %s",
        duration_ms,
        {k: v for k, v in summary.items() if k not in ("started_at",)},
    )
    return summary
