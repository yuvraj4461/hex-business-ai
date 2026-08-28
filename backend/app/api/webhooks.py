"""Inbound webhooks — let a source push HEX to sync instead of polling.

No bearer auth: the caller proves itself with the per-connection
``webhook_secret`` (created with the connection) in the ``X-HEX-Token``
header. On a match the connection is synced in the background.
"""

from __future__ import annotations

import hmac

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Header,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal, get_db
from app.ingestion.sync import run_sync
from app.models.connection import Connection
from fastapi import Depends

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _sync_now(connection_id: int) -> None:
    db = SessionLocal()
    try:
        conn = db.get(Connection, connection_id)
        if conn is not None:
            run_sync(db, conn)
    finally:
        db.close()


@router.post("/connections/{connection_id}", status_code=202)
def trigger_sync(
    connection_id: int,
    background: BackgroundTasks,
    x_hex_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    conn = db.get(Connection, connection_id)
    if conn is None:
        raise HTTPException(status_code=404, detail="Connection not found")

    expected = (conn.config or {}).get("webhook_secret")
    if not expected or not x_hex_token or not hmac.compare_digest(
        str(expected), str(x_hex_token)
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    background.add_task(_sync_now, conn.id)
    return {"status": "accepted", "connection_id": conn.id}
