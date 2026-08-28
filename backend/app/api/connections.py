"""Connections API — configure and sync external data sources."""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.ingestion.sync import run_sync
from app.models.connection import Connection
from app.models.user import User
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionOut,
    ConnectionUpdate,
    ReadinessOut,
    SyncResult,
    TestResult,
)
from app.security.crypto import decrypt_dict, encrypt_dict
from app.security.dependencies import require_permission
from app.services.data_readiness import get_readiness
from app.sources.file_upload import (
    SUPPORTED_ENTITIES,
    FileUploadAdapter,
    connection_dir,
)
from app.sources.registry import get_adapter, is_supported

router = APIRouter(prefix="/connections", tags=["Connections"])


def _serialize(conn: Connection) -> dict:
    return {
        "id": conn.id,
        "organization_id": conn.organization_id,
        "source_type": conn.source_type,
        "display_name": conn.display_name,
        "status": conn.status,
        "config": conn.config or {},
        "cursor": conn.cursor or {},
        "has_credentials": conn.credentials_encrypted is not None,
        "last_sync_at": conn.last_sync_at,
        "last_error": conn.last_error,
        "created_at": conn.created_at,
        "updated_at": conn.updated_at,
    }


def _get_owned(
    connection_id: int, db: Session, user: User
) -> Connection:
    conn = db.get(Connection, connection_id)
    if conn is None or conn.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Backfill for connections created before webhook secrets existed.
    if not (conn.config or {}).get("webhook_secret"):
        conn.config = {
            **(conn.config or {}),
            "webhook_secret": secrets.token_urlsafe(24),
        }
        db.commit()

    return conn


@router.get("", response_model=list[ConnectionOut])
def list_connections(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("view_analytics")),
):
    rows = db.execute(
        select(Connection)
        .where(Connection.organization_id == user.organization_id)
        .order_by(Connection.id)
    ).scalars().all()
    return [_serialize(c) for c in rows]


@router.post("", response_model=ConnectionOut, status_code=201)
def create_connection(
    body: ConnectionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_data")),
):
    if not is_supported(body.source_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported source_type: {body.source_type}",
        )

    config = dict(body.config or {})
    config.setdefault("webhook_secret", secrets.token_urlsafe(24))

    conn = Connection(
        organization_id=user.organization_id,
        source_type=body.source_type,
        display_name=body.display_name,
        config=config,
        credentials_encrypted=(
            encrypt_dict(body.credentials) if body.credentials else None
        ),
        status="PENDING",
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return _serialize(conn)


@router.get("/{connection_id}", response_model=ConnectionOut)
def get_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("view_analytics")),
):
    return _serialize(_get_owned(connection_id, db, user))


@router.patch("/{connection_id}", response_model=ConnectionOut)
def update_connection(
    connection_id: int,
    body: ConnectionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_data")),
):
    conn = _get_owned(connection_id, db, user)

    if body.display_name is not None:
        conn.display_name = body.display_name
    if body.config is not None:
        conn.config = body.config
    if body.status is not None:
        conn.status = body.status
    if body.credentials is not None:
        merged = {**decrypt_dict(conn.credentials_encrypted), **body.credentials}
        conn.credentials_encrypted = encrypt_dict(merged)

    db.commit()
    db.refresh(conn)
    return _serialize(conn)


@router.delete("/{connection_id}", status_code=204)
def delete_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_data")),
):
    conn = _get_owned(connection_id, db, user)
    db.delete(conn)
    db.commit()


@router.post("/{connection_id}/test", response_model=TestResult)
def test_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_data")),
):
    conn = _get_owned(connection_id, db, user)
    try:
        ok, message = get_adapter(conn).test_connection()
    except Exception as exc:  # noqa: BLE001
        ok, message = False, str(exc)

    conn.status = "ACTIVE" if ok else "ERROR"
    conn.last_error = None if ok else message
    db.commit()
    return {"ok": ok, "message": message}


@router.post("/{connection_id}/sync", response_model=SyncResult)
def sync_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_data")),
):
    conn = _get_owned(connection_id, db, user)
    return run_sync(db, conn)


@router.post("/{connection_id}/upload", response_model=ConnectionOut)
def upload_file(
    connection_id: int,
    entity_type: str = Form(...),
    id_column: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_data")),
):
    conn = _get_owned(connection_id, db, user)
    if conn.source_type != FileUploadAdapter.source_type:
        raise HTTPException(
            status_code=400,
            detail="Uploads are only for file_upload connections",
        )
    if entity_type not in SUPPORTED_ENTITIES:
        raise HTTPException(
            status_code=400, detail=f"Unknown entity_type: {entity_type}"
        )

    suffix = Path(file.filename or "").suffix.lower() or ".csv"
    if suffix not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(
            status_code=400, detail="Upload a .csv, .xlsx or .xls file"
        )

    dest = connection_dir(conn.id) / f"{entity_type}{suffix}"
    dest.write_bytes(file.file.read())

    config = dict(conn.config or {})
    uploads = dict(config.get("uploads", {}))
    uploads[entity_type] = {
        "path": str(dest),
        "id_column": id_column or None,
        "filename": file.filename,
    }
    config["uploads"] = uploads
    conn.config = config
    conn.status = "ACTIVE"
    db.commit()
    db.refresh(conn)
    return _serialize(conn)


# Mounted at app level, not under /connections.
readiness_router = APIRouter(tags=["Connections"])


@readiness_router.get("/data/readiness", response_model=ReadinessOut)
def data_readiness(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("view_analytics")),
):
    return get_readiness(db, user.organization_id)
