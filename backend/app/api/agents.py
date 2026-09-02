"""Agent API.

/agents/status previously returned a hardcoded list with every agent
marked READY, regardless of whether the agents could actually run. It now
performs a real dependency check, and /agents/run executes the graph and
reports per-agent outcomes.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.agents.orchestrator import AGENT_LABELS, AGENT_SEQUENCE
from app.agents.runner import run_business_agents
from app.database.connection import get_db
from app.models.user import User
from app.security.dependencies import require_permission

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


# What each agent needs in order to produce output. Used by /agents/status
# to report DEGRADED instead of claiming READY when a table is empty.
AGENT_REQUIREMENTS = {
    "finance": {
        "description": (
            "Deterministic finance engine — margins, growth, cash/runway, "
            "volatility, unit economics and break-even"
        ),
        "tables": ["transactions", "expenses", "orders"],
    },
    "sales": {
        "description": "Order volume, fulfilment and demand trend",
        "tables": ["orders"],
    },
    "operations": {
        "description": "Inventory, suppliers and supply-route health",
        "tables": ["inventory", "suppliers"],
    },
    "watch": {
        "description": (
            "Real-time disruption, tariff, FX and price-shock monitoring"
        ),
        "tables": ["global_events"],
    },
    "risk": {
        "description": "Global event exposure and risk scoring",
        "tables": ["global_events", "business_exposures"],
    },
}


class RunAgentsRequest(BaseModel):
    question: str = Field(
        default="Provide a full business health assessment.",
        max_length=1000,
    )


def _table_count(db: Session, table: str) -> int | None:
    """Row count for a table, or None if the table is unavailable."""

    try:
        result = db.execute(
            text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608 - fixed names
        )
        return int(result.scalar() or 0)

    except Exception:  # noqa: BLE001
        db.rollback()
        return None


@router.get("/status")
def agent_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("run_analysis")
    ),
) -> dict[str, Any]:
    """Report whether each agent has the data it needs to produce output."""

    agents = []

    for key in AGENT_SEQUENCE:

        spec = AGENT_REQUIREMENTS[key]

        counts: dict[str, int | None] = {
            table: _table_count(db, table)
            for table in spec["tables"]
        }

        missing = [
            table
            for table, count in counts.items()
            if count is None
        ]

        empty = [
            table
            for table, count in counts.items()
            if count == 0
        ]

        if missing:
            status = "UNAVAILABLE"
            detail = f"Table not reachable: {', '.join(missing)}"

        elif empty:
            status = "DEGRADED"
            detail = f"No data in: {', '.join(empty)}"

        else:
            status = "READY"
            detail = "All required data present"

        agents.append(
            {
                "key": key,
                "name": AGENT_LABELS[key],
                "description": spec["description"],
                "status": status,
                "detail": detail,
                "position": AGENT_SEQUENCE.index(key) + 1,
                "data_sources": counts,
            }
        )

    ready_count = sum(
        1 for a in agents if a["status"] == "READY"
    )

    return {
        "organization_id": current_user.organization_id,
        "pipeline": [AGENT_LABELS[k] for k in AGENT_SEQUENCE],
        "agents_total": len(agents),
        "agents_ready": ready_count,
        "system_status": (
            "READY"
            if ready_count == len(agents)
            else "DEGRADED"
            if ready_count
            else "UNAVAILABLE"
        ),
        "agents": agents,
    }


@router.post("/run")
def run_agents(
    request: RunAgentsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("run_analysis")
    ),
) -> dict[str, Any]:
    """Execute the full agent graph and return findings per agent.

    Returns HTTP 200 even when individual agents fail; inspect
    `agent_runs` and `errors` for partial-failure detail.
    """

    started = time.perf_counter()

    result = run_business_agents(
        question=request.question,
        organization_id=current_user.organization_id,
        db=db,
    )

    duration_ms = int(
        (time.perf_counter() - started) * 1000
    )

    runs = result.get("agent_runs") or []

    succeeded = [
        r for r in runs if r.get("status") == "OK"
    ]

    failed = [
        r for r in runs if r.get("status") == "FAILED"
    ]

    return {
        "organization_id": current_user.organization_id,
        "question": request.question,
        "duration_ms": duration_ms,
        "agents_run": len(runs),
        "agents_succeeded": len(succeeded),
        "agents_failed": len(failed),
        "status": (
            "OK"
            if runs and not failed
            else "PARTIAL"
            if succeeded
            else "FAILED"
        ),
        "agent_runs": runs,
        "findings": result.get("findings") or [],
        "recommendations": result.get("recommendations") or [],
        "errors": result.get("errors") or [],
    }