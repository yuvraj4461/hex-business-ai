from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Shared state passed between every agent node in the graph.

    Each agent receives the full state and returns it with its own
    findings/recommendations appended. Nothing is overwritten, so the
    order of nodes in the graph determines the order of results.
    """

    question: str

    organization_id: int

    business_data: dict[str, Any]

    findings: list[dict[str, Any]]

    recommendations: list[dict[str, Any]]

    # Per-agent execution record: one entry per node that was attempted,
    # whether it succeeded or failed. This is what /agents/status reports
    # instead of a hardcoded "READY".
    agent_runs: list[dict[str, Any]]

    errors: list[str]

    final_answer: str

    # Built once per run and reused by every agent that needs the
    # market / exposure / agriculture / demand context, instead of each
    # agent rebuilding it (it was ~3 heavy rebuilds per run).
    shared_context: dict[str, Any] | None