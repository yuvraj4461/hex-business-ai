"""Glue: question -> plan -> execute -> narrate. Never raises."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.analytics.executor import run_spec
from app.analytics.narrator import narrate
from app.analytics.planner import plan_query
from app.analytics.semantic import spec_label

logger = logging.getLogger(__name__)


def answer_data_question(
    db: Session,
    organization_id: int,
    question: str,
    prior_spec: dict | None = None,
) -> dict:
    """Return a dict ready for the API/frontend:

        {question, answer, spec, spec_label, result, degraded}
    """

    try:
        spec, plan_degraded = plan_query(question, prior_spec)
    except Exception as exc:  # noqa: BLE001
        logger.exception("analytics: planning failed")
        return _error(question, f"Could not interpret that question ({exc}).")

    try:
        result = run_spec(db, organization_id, spec)
    except Exception as exc:  # noqa: BLE001
        logger.exception("analytics: execution failed for spec %s", spec.to_dict())
        return _error(
            question,
            "Ran into a problem querying that. Try rephrasing, e.g. "
            "“revenue by month” or “top 5 products by revenue”.",
            spec=spec,
        )

    answer, _ai_written = narrate(question, spec, result)

    return {
        "question": question,
        "answer": answer,
        "spec": spec.to_dict(),
        "spec_label": spec_label(spec),
        "result": result,
        # "degraded" == HEX could not properly interpret the question with the
        # model and fell back to keyword parsing. A deterministic *narrative*
        # is the normal path and is not a degradation.
        "degraded": bool(plan_degraded),
    }


def _error(question: str, message: str, spec=None) -> dict:
    return {
        "question": question,
        "answer": message,
        "spec": spec.to_dict() if spec is not None else None,
        "spec_label": spec_label(spec) if spec is not None else "",
        "result": {"columns": [], "rows": [], "chart": None, "row_count": 0},
        "degraded": True,
    }
