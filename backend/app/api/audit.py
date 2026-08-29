"""Audit log — an append-only record of every action in an organization."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.security.dependencies import require_permission

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("")
def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_permission("view_audit_logs")),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(AuditLog, User.name)
        .join(User, User.id == AuditLog.user_id, isouter=True)
        .where(AuditLog.organization_id == user.organization_id)
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
    ).all()

    return [
        {
            "id": log.id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "description": log.description,
            "user": user_name or "system",
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for (log, user_name) in rows
    ]
