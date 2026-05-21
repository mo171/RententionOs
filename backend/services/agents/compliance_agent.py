"""
Compliance Agent: LangGraph Node 1 wrapper for the CRAG pipeline.
"""
from langgraph.graph import StateGraph, END

from models.compliance_models import (
    InterventionPayload,
    ComplianceAgentState,
    ComplianceResult,
)
from services.rag.compliance_service import run_compliance_check
from utils.supabase_client import get_supabase_client


def compliance_node(state: ComplianceAgentState) -> ComplianceAgentState:
    """LangGraph node: runs CRAG and updates state."""
    payload = state["payload"]
    if isinstance(payload, dict):
        payload = InterventionPayload(**payload)

    supabase = get_supabase_client()
    result, trace = run_compliance_check(payload, supabase)

    return {
        **state,
        "payload": payload,
        "queries": trace.get("queries", []),
        "primary_query": trace.get("primary_query", ""),
        "raw_chunks": trace.get("raw_chunks", []),
        "fused_chunks": trace.get("fused_chunks", []),
        "graded_chunks": trace.get("graded_chunks", []),
        "reasoning_trace": trace.get("reasoning_trace", result.reasoning),
        "compliance_result": result,
        "should_intervene": result.intervene,
    }


def build_compliance_graph():
    """Minimal single-node graph for Node 1 (Compliance)."""
    graph = StateGraph(ComplianceAgentState)
    graph.add_node("compliance", compliance_node)
    graph.set_entry_point("compliance")
    graph.add_edge("compliance", END)
    return graph.compile()


def run_compliance_graph(payload: InterventionPayload) -> ComplianceAgentState:
    """Convenience: invoke the compliance graph with an ML payload."""
    app = build_compliance_graph()
    initial: ComplianceAgentState = {
        "payload": payload,
        "queries": [],
        "primary_query": "",
        "raw_chunks": [],
        "fused_chunks": [],
        "graded_chunks": [],
        "reasoning_trace": "",
        "compliance_result": None,
        "should_intervene": False,
    }
    return app.invoke(initial)
