"""Single source of truth for the HEX agent graph.

Previously there were two graph builders: this file (which included the
Sales Agent) and runner.build_agent_graph (which did not). runner built
its own graph, so the Sales Agent never executed. Both now go through
build_graph below.

Execution order is sequential and deliberate:

    finance -> sales -> operations -> risk

Finance establishes the money baseline, sales adds demand reality,
operations reads supply against that demand, and risk runs last so it
can weigh everything the others found.
"""

import logging
import time
from typing import Any, Callable

from langgraph.graph import END, START, StateGraph

from app.agents.state import AgentState

logger = logging.getLogger(__name__)


# Order matters: later agents read findings produced by earlier ones.
# "watch" runs before "risk" so risk sees the live disruption findings.
AGENT_SEQUENCE = [
    "finance",
    "sales",
    "operations",
    "watch",
    "risk",
]


AGENT_LABELS = {
    "finance": "Finance Agent",
    "sales": "Sales Agent",
    "operations": "Operations Agent",
    "watch": "World Watch Agent",
    "risk": "Risk Agent",
}


def _record(
    state: AgentState,
    name: str,
    status: str,
    duration_ms: int,
    findings_added: int = 0,
    recommendations_added: int = 0,
    error: str | None = None,
) -> dict[str, Any]:
    """Build one entry for state['agent_runs']."""

    entry: dict[str, Any] = {
        "agent": AGENT_LABELS.get(name, name),
        "key": name,
        "status": status,
        "duration_ms": duration_ms,
        "findings_added": findings_added,
        "recommendations_added": recommendations_added,
    }

    if error:
        entry["error"] = error

    return entry


def wrap_agent(
    name: str,
    agent_fn: Callable[..., dict],
    db,
):
    """Wrap a raw agent function into a fault-isolated graph node.

    An agent that raises no longer takes the whole run down. It is marked
    FAILED in agent_runs, its error is appended to state['errors'], and the
    graph continues to the next node with state intact. A partial answer
    from three agents is far more useful in a live demo than a 500.
    """

    def node(state: AgentState) -> AgentState:

        started = time.perf_counter()

        before_findings = len(state.get("findings") or [])
        before_recs = len(state.get("recommendations") or [])

        runs = list(state.get("agent_runs") or [])
        errors = list(state.get("errors") or [])

        try:
            result = agent_fn(state, db)

            if not isinstance(result, dict):
                raise TypeError(
                    f"{name} agent returned {type(result).__name__}, expected dict"
                )

            duration_ms = int(
                (time.perf_counter() - started) * 1000
            )

            findings = list(result.get("findings") or [])
            recommendations = list(
                result.get("recommendations") or []
            )

            runs.append(
                _record(
                    state,
                    name,
                    "OK",
                    duration_ms,
                    findings_added=len(findings) - before_findings,
                    recommendations_added=len(recommendations) - before_recs,
                )
            )

            return {
                **result,
                "agent_runs": runs,
                "errors": errors,
            }

        except Exception as exc:  # noqa: BLE001 - deliberate catch-all

            duration_ms = int(
                (time.perf_counter() - started) * 1000
            )

            message = f"{AGENT_LABELS.get(name, name)}: {exc}"

            logger.exception(
                "Agent %s failed during graph execution", name
            )

            errors.append(message)

            runs.append(
                _record(
                    state,
                    name,
                    "FAILED",
                    duration_ms,
                    error=str(exc),
                )
            )

            return {
                **state,
                "agent_runs": runs,
                "errors": errors,
            }

    node.__name__ = f"{name}_node"

    return node


def resolve_sequence(agents: list[str] | None) -> list[str]:
    """Filter AGENT_SEQUENCE to the requested subset, preserving order.

    Unknown names are ignored; an empty or fully-unknown request runs the
    whole pipeline.
    """

    if not agents:
        return list(AGENT_SEQUENCE)

    wanted = {str(a).strip().lower() for a in agents}
    picked = [name for name in AGENT_SEQUENCE if name in wanted]
    return picked or list(AGENT_SEQUENCE)


def build_graph(db, agents: list[str] | None = None):
    """Compile the agent graph, optionally limited to a subset of agents
    (finance / sales / operations / watch / risk). Order is always the
    canonical AGENT_SEQUENCE order so later agents still see earlier
    findings."""

    sequence = resolve_sequence(agents)

    # Imported here rather than at module scope so that a syntax error or
    # heavy import inside one agent cannot break the whole package import.
    from app.agents.finance_agent import finance_agent
    from app.agents.operations_agent import operations_agent
    from app.agents.risk_agent import risk_agent
    from app.agents.sales_agent import sales_agent
    from app.agents.watch_agent import watch_agent

    agent_functions = {
        "finance": finance_agent,
        "sales": sales_agent,
        "operations": operations_agent,
        "watch": watch_agent,
        "risk": risk_agent,
    }

    graph = StateGraph(AgentState)

    for name in sequence:
        graph.add_node(
            name,
            wrap_agent(name, agent_functions[name], db),
        )

    graph.add_edge(START, sequence[0])

    for current, following in zip(sequence, sequence[1:]):
        graph.add_edge(current, following)

    graph.add_edge(sequence[-1], END)

    return graph.compile()