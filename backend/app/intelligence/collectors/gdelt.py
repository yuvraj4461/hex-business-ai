"""GDELT collector — real-time global events (war, sanctions, disasters, ports)."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.global_event import GlobalEvent
from app.services.event_scoring import calculate_severity
from app.services.global_events import fetch_gdelt_events, store_gdelt_events

logger = logging.getLogger(__name__)


def collect_gdelt(db: Session, timespan_minutes: int = 180) -> dict:
    try:
        data = fetch_gdelt_events(timespan_minutes=timespan_minutes)
    except Exception as exc:  # noqa: BLE001
        logger.warning("GDELT fetch failed: %s", exc)
        return {"fetched": 0, "stored": 0, "error": str(exc)}

    stored = store_gdelt_events(db, data)

    # store_gdelt_events writes severity="UNKNOWN"; score the new rows.
    scored = 0
    rows = db.execute(
        select(GlobalEvent).where(
            GlobalEvent.source == "GDELT",
            GlobalEvent.severity.in_(("UNKNOWN", "", None)),
        )
    ).scalars().all()
    for row in rows:
        row.severity = calculate_severity(row.title or "", row.event_type or "")
        scored += 1
    db.commit()

    return {
        "fetched": len(data.get("features", [])),
        "stored": stored,
        "scored": scored,
    }
