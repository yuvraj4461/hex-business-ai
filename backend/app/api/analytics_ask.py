"""'Ask Your Data' — conversational analytics over the org's own data.

`POST /copilot/data` is a stateless one-shot. The `/copilot/data/threads`
endpoints persist a conversation so follow-ups ("break it down by
category") build on the previous query.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analytics.service import answer_data_question
from app.database.connection import get_db
from app.models.audit_log import AuditLog
from app.models.data_thread import DataThread, DataThreadMessage
from app.models.user import User
from app.schemas.analytics import (
    DataAnswer,
    DataQueryRequest,
    ThreadDetail,
    ThreadSummary,
)
from app.security.dependencies import require_permission

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


# --------------------------------------------------------------------------
# Stateless one-shot
# --------------------------------------------------------------------------

@router.post("/data", response_model=DataAnswer)
def ask_data(
    request: DataQueryRequest,
    current_user: User = Depends(require_permission("run_analysis")),
    db: Session = Depends(get_db),
):
    return answer_data_question(
        db, current_user.organization_id, request.question, request.prior_spec
    )


# --------------------------------------------------------------------------
# Threads
# --------------------------------------------------------------------------

def _thread_or_404(db: Session, org_id: int, thread_id: int) -> DataThread:
    thread = (
        db.query(DataThread)
        .filter(
            DataThread.id == thread_id,
            DataThread.organization_id == org_id,
        )
        .first()
    )
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found.")
    return thread


def _message_payload(msg: DataThreadMessage) -> dict:
    return {
        "id": msg.id,
        "role": msg.role,
        "question": msg.question,
        "answer": msg.answer,
        "spec": msg.spec,
        "spec_label": msg.spec_label,
        "result": msg.result,
        "degraded": msg.degraded,
        "created_at": msg.created_at,
    }


def _thread_detail(thread: DataThread) -> dict:
    return {
        "id": thread.id,
        "title": thread.title,
        "created_at": thread.created_at,
        "updated_at": thread.updated_at,
        "messages": [_message_payload(m) for m in thread.messages],
    }


def _run_turn(
    db: Session,
    thread: DataThread,
    user: User,
    question: str,
) -> DataThreadMessage:
    """Append a user turn + a HEX turn to the thread, using the previous
    HEX answer's spec as the refinement base."""

    prior_spec = None
    for msg in reversed(thread.messages):
        if msg.role == "hex" and msg.spec:
            prior_spec = msg.spec
            break

    result = answer_data_question(
        db, user.organization_id, question, prior_spec
    )

    db.add(
        DataThreadMessage(
            thread_id=thread.id,
            organization_id=user.organization_id,
            role="user",
            question=question,
        )
    )
    hex_msg = DataThreadMessage(
        thread_id=thread.id,
        organization_id=user.organization_id,
        role="hex",
        answer=result["answer"],
        spec=result["spec"],
        spec_label=result["spec_label"],
        result=result["result"],
        degraded=result["degraded"],
    )
    db.add(hex_msg)

    thread.updated_at = datetime.utcnow()

    db.add(
        AuditLog(
            organization_id=user.organization_id,
            user_id=user.id,
            action="copilot.data",
            entity_type="DataThread",
            entity_id=thread.id,
            description=question[:250],
            data={"spec": result["spec"], "degraded": result["degraded"]},
        )
    )

    db.commit()
    db.refresh(hex_msg)
    return hex_msg


@router.get("/data/threads", response_model=list[ThreadSummary])
def list_threads(
    current_user: User = Depends(require_permission("run_analysis")),
    db: Session = Depends(get_db),
):
    threads = (
        db.query(DataThread)
        .filter(DataThread.organization_id == current_user.organization_id)
        .order_by(DataThread.updated_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": t.id,
            "title": t.title,
            "message_count": len(t.messages),
            "updated_at": t.updated_at,
        }
        for t in threads
    ]


@router.post("/data/threads", response_model=ThreadDetail)
def create_thread(
    request: DataQueryRequest,
    current_user: User = Depends(require_permission("run_analysis")),
    db: Session = Depends(get_db),
):
    title = request.question.strip()
    thread = DataThread(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        title=(title[:60] + "…") if len(title) > 60 else title,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)

    _run_turn(db, thread, current_user, request.question)
    db.refresh(thread)
    return _thread_detail(thread)


@router.get("/data/threads/{thread_id}", response_model=ThreadDetail)
def get_thread(
    thread_id: int,
    current_user: User = Depends(require_permission("run_analysis")),
    db: Session = Depends(get_db),
):
    thread = _thread_or_404(db, current_user.organization_id, thread_id)
    return _thread_detail(thread)


@router.post("/data/threads/{thread_id}/messages")
def add_message(
    thread_id: int,
    request: DataQueryRequest,
    current_user: User = Depends(require_permission("run_analysis")),
    db: Session = Depends(get_db),
):
    thread = _thread_or_404(db, current_user.organization_id, thread_id)
    hex_msg = _run_turn(db, thread, current_user, request.question)
    return _message_payload(hex_msg)


@router.delete("/data/threads/{thread_id}", status_code=204)
def delete_thread(
    thread_id: int,
    current_user: User = Depends(require_permission("run_analysis")),
    db: Session = Depends(get_db),
):
    thread = _thread_or_404(db, current_user.organization_id, thread_id)
    db.delete(thread)
    db.commit()
