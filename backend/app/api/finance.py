"""Deterministic finance engine — a formula calculator and the computed
company metrics battery. No LLM in the loop.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.finance import formulas as F
from app.finance.engine import company_finance
from app.finance.registry import CATEGORIES, FORMULAS, describe, evaluate
from app.models.user import User
from app.security.dependencies import require_permission

router = APIRouter(prefix="/finance", tags=["Finance"])


class CalcRequest(BaseModel):
    formula: str
    inputs: dict[str, Any] = Field(default_factory=dict)


@router.get("/formulas")
def list_formulas(
    _: User = Depends(require_permission("view_analytics")),
):
    return {"categories": CATEGORIES, "formulas": describe()}


@router.post("/calc")
def calculate(
    request: CalcRequest,
    _: User = Depends(require_permission("view_analytics")),
):
    spec = FORMULAS.get(request.formula)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Unknown formula '{request.formula}'.")

    try:
        value = evaluate(request.formula, request.inputs)
    except F.FinanceError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Bad inputs: {exc}")

    if isinstance(value, list):
        rounded: Any = [round(float(v), 4) for v in value]
    elif value == float("inf"):
        rounded = None
    else:
        rounded = round(float(value), 4)

    return {
        "formula": spec.key,
        "label": spec.label,
        "unit": spec.unit,
        "value": rounded,
        "description": spec.description,
    }


@router.get("/metrics")
def company_metrics(
    current_user: User = Depends(require_permission("view_analytics")),
    db: Session = Depends(get_db),
):
    return company_finance(db, current_user.organization_id)
