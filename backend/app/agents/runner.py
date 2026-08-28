"""Entry point for running the HEX agent graph.

This module used to build its own graph that omitted the Sales Agent.
It now delegates to app.agents.orchestrator.build_graph so there is
exactly one definition of the agent pipeline.
"""

import logging
from typing import Any

from app.agents.orchestrator import (
    AGENT_LABELS,
    AGENT_SEQUENCE,
    build_graph,
)

logger = logging.getLogger(__name__)


# Kept for backwards compatibility: older code imported build_agent_graph
# from this module.
def build_agent_graph(db):
    return build_graph(db)


def run_business_agents(
    question: str,
    organization_id: int,
    db,
) -> dict[str, Any]:
    """Run all four agents and return the merged state.

    Always returns a dict with findings, recommendations, agent_runs and
    errors, even if the graph itself fails to execute. Callers such as the
    copilot endpoint can rely on those keys existing.
    """

    initial_state: dict[str, Any] = {
        "question": question,
        "organization_id": organization_id,
        "findings": [],
        "recommendations": [],
        "agent_runs": [],
        "errors": [],
    }

    try:
        graph = build_graph(db)

        result = graph.invoke(initial_state)

    except Exception as exc:  # noqa: BLE001

        logger.exception("Agent graph failed to execute")

        return {
            **initial_state,
            "errors": [f"Agent graph failed: {exc}"],
            "agent_runs": [
                {
                    "agent": AGENT_LABELS[name],
                    "key": name,
                    "status": "NOT_RUN",
                    "duration_ms": 0,
                    "findings_added": 0,
                    "recommendations_added": 0,
                }
                for name in AGENT_SEQUENCE
            ],
        }

    # Normalise so downstream consumers never hit a missing key.
    result.setdefault("findings", [])
    result.setdefault("recommendations", [])
    result.setdefault("agent_runs", [])
    result.setdefault("errors", [])

    return result