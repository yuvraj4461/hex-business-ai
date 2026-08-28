"""Merge Link onboarding.

Front end flow:
  1. POST /connections/merge/link-token  -> { link_token }
  2. open Merge Link with that token; user picks + authorises their system
  3. POST /connections/merge/retrieve-token { public_token, display_name }
     -> swaps for a permanent account_token, creates a `merge` Connection
"""

from __future__ import annotations

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.connection import Connection
from app.models.user import User
from app.security.crypto import encrypt_dict
from app.security.dependencies import require_permission
from app.sources.merge_adapter import MERGE_API_KEY, is_configured

router = APIRouter(prefix="/connections/merge", tags=["Connections"])

_MERGE_ROOT = "https://api.merge.dev/api/integrations"


class RetrieveTokenBody(BaseModel):
    public_token: str
    display_name: str = "Accounting system (Merge)"


def _require_key() -> None:
    if not is_configured():
        raise HTTPException(
            status_code=503,
            detail="Merge is not configured (set MERGE_API_KEY).",
        )


@router.post("/link-token")
def create_link_token(
    user: User = Depends(require_permission("manage_data")),
):
    _require_key()
    resp = requests.post(
        f"{_MERGE_ROOT}/create-link-token",
        headers={"Authorization": f"Bearer {MERGE_API_KEY}"},
        json={
            "end_user_origin_id": str(user.organization_id),
            "end_user_organization_name": f"org-{user.organization_id}",
            "end_user_email_address": user.email,
            "categories": ["accounting"],
        },
        timeout=30,
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Merge: {resp.text}")
    return {"link_token": resp.json().get("link_token")}


@router.post("/retrieve-token")
def retrieve_token(
    body: RetrieveTokenBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("manage_data")),
):
    _require_key()
    resp = requests.get(
        f"{_MERGE_ROOT}/account-token/{body.public_token}",
        headers={"Authorization": f"Bearer {MERGE_API_KEY}"},
        timeout=30,
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Merge: {resp.text}")

    data = resp.json()
    account_token = data.get("account_token")
    integration = (data.get("integration") or {}).get("name", "Merge")

    conn = Connection(
        organization_id=user.organization_id,
        source_type="merge",
        display_name=f"{body.display_name} — {integration}",
        config={"category": "accounting", "integration": integration},
        credentials_encrypted=encrypt_dict(
            {"account_token": account_token}
        ),
        status="ACTIVE",
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return {"id": conn.id, "integration": integration}
