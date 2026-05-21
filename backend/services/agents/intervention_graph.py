"""
Intervention graph: Compliance (Node 1) → Strategy (Node 2).
"""
from langgraph.graph import StateGraph, END

from models.compliance_models import InterventionPayload
from models.strategy_models import InterventionGraphState
from services.agents.compliance_agent import compliance_node
from services.agents.strategy_agent import strategy_node


def route_after_compliance(state: InterventionGraphState) -> str:
    if state.get("should_intervene"):
        return "continue"
    return "stop"


def build_intervention_graph():
    graph = StateGraph(InterventionGraphState)
    graph.add_node("compliance", compliance_node)
    graph.add_node("strategy", strategy_node)
    graph.set_entry_point("compliance")
    graph.add_conditional_edges(
        "compliance",
        route_after_compliance,
        {"continue": "strategy", "stop": END},
    )
    graph.add_edge("strategy", END)
    return graph.compile()


def initial_graph_state(payload: InterventionPayload) -> InterventionGraphState:
    return {
        "payload": payload,
        "queries": [],
        "primary_query": "",
        "raw_chunks": [],
        "fused_chunks": [],
        "graded_chunks": [],
        "reasoning_trace": "",
        "compliance_result": None,
        "should_intervene": False,
        "subscriber_profile": None,
        "interaction_history": [],
        "strategy_result": None,
    }


def run_intervention_graph(payload: InterventionPayload) -> InterventionGraphState:
    app = build_intervention_graph()
    return app.invoke(initial_graph_state(payload))
