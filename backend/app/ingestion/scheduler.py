"""Background auto-sync.

One APScheduler job runs every ``HEX_SYNC_INTERVAL_MINUTES`` and syncs any
ACTIVE connection whose ``config.auto_sync`` is not False and whose
``last_sync_at`` is older than the interval. Disabled with
``HEX_SCHEDULER_ENABLED=false`` (and under pytest).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.database.connection import SessionLocal
from app.ingestion.sync import run_sync
from app.models.connection import Connection

logger = logging.getLogger(__name__)

INTERVAL_MINUTES = int(os.getenv("HEX_SYNC_INTERVAL_MINUTES", "30"))

_scheduler: BackgroundScheduler | None = None


def _due(connection: Connection, cutoff: datetime) -> bool:
    if connection.status != "ACTIVE":
        return False
    if (connection.config or {}).get("auto_sync") is False:
        return False
    return connection.last_sync_at is None or connection.last_sync_at < cutoff


def _run_due_syncs() -> None:
    cutoff = datetime.utcnow() - timedelta(minutes=INTERVAL_MINUTES)
    db = SessionLocal()
    try:
        connections = db.execute(select(Connection)).scalars().all()
        for connection in connections:
            if not _due(connection, cutoff):
                continue
            try:
                logger.info(
                    "auto-sync: connection %s (%s)",
                    connection.id,
                    connection.display_name,
                )
                run_sync(db, connection)
            except Exception:  # noqa: BLE001
                logger.exception(
                    "auto-sync failed for connection %s", connection.id
                )
                db.rollback()
    finally:
        db.close()


def start_scheduler() -> None:
    global _scheduler

    if os.getenv("HEX_SCHEDULER_ENABLED", "true").lower() == "false":
        logger.info("Auto-sync scheduler disabled by env.")
        return
    if "PYTEST_CURRENT_TEST" in os.environ:
        return
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        _run_due_syncs,
        "interval",
        minutes=INTERVAL_MINUTES,
        max_instances=1,
        coalesce=True,
        id="hex_auto_sync",
    )
    _scheduler.start()
    logger.info(
        "Auto-sync scheduler started (every %s min).", INTERVAL_MINUTES
    )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
