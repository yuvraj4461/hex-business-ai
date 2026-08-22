from app.agents.finance_agent import finance_agent
from app.agents.operations_agent import operations_agent
from app.agents.risk_agent import risk_agent

from app.agents.state import AgentState

from langgraph.graph import (
    START,
    END,
    StateGraph,
)


def build_agent_graph(db):

    graph_builder = StateGraph(
        AgentState
    )

    # ---------------------------------------------
    # Finance node
    # ---------------------------------------------

    def finance_node(
        state: AgentState,
    ) -> AgentState:

        return finance_agent(
            state,
            db,
        )

    # ---------------------------------------------
    # Operations node
    # ---------------------------------------------

    def operations_node(
        state: AgentState,
    ) -> AgentState:

        return operations_agent(
            state,
            db,
        )

    # ---------------------------------------------
    # Risk node
    # ---------------------------------------------

    def risk_node(
        state: AgentState,
    ) -> AgentState:

        return risk_agent(
            state,
            db,
        )

    # ---------------------------------------------
    # Graph
    # ---------------------------------------------

    graph_builder.add_node(
        "finance",
        finance_node,
    )

    graph_builder.add_node(
        "operations",
        operations_node,
    )

    graph_builder.add_node(
        "risk",
        risk_node,
    )

    graph_builder.add_edge(
        START,
        "finance",
    )

    graph_builder.add_edge(
        "finance",
        "operations",
    )

    graph_builder.add_edge(
        "operations",
        "risk",
    )

    graph_builder.add_edge(
        "risk",
        END,
    )

    return graph_builder.compile()


def run_business_agents(
    question: str,
    organization_id: int,
    db,
):

    initial_state = {
        "question": question,

        "organization_id":
            organization_id,

        "findings": [],

        "recommendations": [],
    }

    graph = build_agent_graph(
        db
    )

    result = graph.invoke(
        initial_state
    )

    return result