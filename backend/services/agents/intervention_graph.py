"""
Intervention graph: Compliance -> Strategy -> Writer <-> Reviewer -> Dispatch.
"""
from langgraph.graph import StateGraph, END

from models.compliance_models import InterventionPayload
from models.strategy_models import InterventionGraphState
from services.agents.compliance_agent import compliance_node
from services.agents.strategy_agent import strategy_node
from services.agents.writer_agent import writer_node
from services.agents.reviewer_agent import reviewer_node
from services.agents.dispatch_agent import dispatch_node

MAX_REVISIONS = 3


def route_after_compliance(state: InterventionGraphState) -> str:
    if state.get("should_intervene"):
        return "continue"
    return "stop"


def route_after_review(state: InterventionGraphState) -> str:
    last = state.get("last_review")
    if last is None:
        return "revise"

    approved = last.approved if not isinstance(last, dict) else last.get("approved")
    revision_count = state.get("revision_count", 0)

    if approved:
        return "dispatch"
    if revision_count < MAX_REVISIONS:
        return "revise"
    return "fallback_dispatch"


def increment_revision(state: InterventionGraphState) -> InterventionGraphState:
    """Runs before writer on revise path."""
    count = state.get("revision_count", 0) + 1
    return {**state, "revision_count": count, "use_fallback_template": False}


def set_fallback_flag(state: InterventionGraphState) -> InterventionGraphState:
    return {**state, "use_fallback_template": True, "revision_count": MAX_REVISIONS}


def build_intervention_graph():
    graph = StateGraph(InterventionGraphState)

    graph.add_node("compliance", compliance_node)
    graph.add_node("strategy", strategy_node)
    graph.add_node("writer", writer_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("increment_revision", increment_revision)
    graph.add_node("set_fallback", set_fallback_flag)
    graph.add_node("dispatch", dispatch_node)

    graph.set_entry_point("compliance")
    graph.add_conditional_edges(
        "compliance",
        route_after_compliance,
        {"continue": "strategy", "stop": END},
    )
    graph.add_edge("strategy", "writer")

    def route_after_writer(state: InterventionGraphState) -> str:
        if state.get("use_fallback_template"):
            return "dispatch"
        return "reviewer"

    graph.add_conditional_edges(
        "writer",
        route_after_writer,
        {"dispatch": "dispatch", "reviewer": "reviewer"},
    )
    graph.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "dispatch": "dispatch",
            "revise": "increment_revision",
            "fallback_dispatch": "set_fallback",
        },
    )
    graph.add_edge("increment_revision", "writer")
    graph.add_edge("set_fallback", "writer")
    graph.add_edge("dispatch", END)

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
        "current_draft": None,
        "revision_count": 0,
        "use_fallback_template": False,
        "review_history": [],
        "last_review": None,
        "final_approved": False,
        "send_result": None,
    }


def run_intervention_graph(payload: InterventionPayload) -> InterventionGraphState:
    app = build_intervention_graph()
    return app.invoke(initial_graph_state(payload))
