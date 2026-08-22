from langgraph.graph import (
    START,
    END,
    StateGraph,
)

from app.agents.state import AgentState


def build_graph(
    finance_node,
    sales_node,
    operations_node,
    risk_node,
):

    graph = StateGraph(
        AgentState
    )

    graph.add_node(
        "finance",
        finance_node,
    )

    graph.add_node(
        "sales",
        sales_node,
    )

    graph.add_node(
        "operations",
        operations_node,
    )

    graph.add_node(
        "risk",
        risk_node,
    )

    graph.add_edge(
        START,
        "finance",
    )

    graph.add_edge(
        "finance",
        "sales",
    )

    graph.add_edge(
        "sales",
        "operations",
    )

    graph.add_edge(
        "operations",
        "risk",
    )

    graph.add_edge(
        "risk",
        END,
    )

    return graph.compile()