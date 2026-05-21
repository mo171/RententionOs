"""
Strategy Agent: LangGraph Node 2 — channel and timing.
"""
import os
from models.compliance_models import InterventionPayload, ComplianceResult
from models.strategy_models import InterventionGraphState, StrategyResult
from services.strategy.strategy_service import run_strategy
from utils.supabase_client import get_supabase_client


def strategy_node(state: InterventionGraphState) -> InterventionGraphState:
    """Runs only when compliance approved intervention."""
    if not state.get("should_intervene"):
        print("[Strategy] Skipped — should_intervene is False.")
        return state

    payload = state["payload"]
    if isinstance(payload, dict):
        payload = InterventionPayload(**payload)

    compliance_result = state.get("compliance_result")
    if compliance_result is None:
        raise ValueError("strategy_node requires compliance_result from Node 1")
    if isinstance(compliance_result, dict):
        compliance_result = ComplianceResult(**compliance_result)

    reasoning_trace = state.get("reasoning_trace", "")
    supabase = get_supabase_client()
    result, trace = run_strategy(
        payload, compliance_result, reasoning_trace, supabase
    )

    if os.getenv("FORCE_EMAIL_CHANNEL", "").lower() in ("1", "true", "yes"):
        result = result.model_copy(update={"channel": "Email"})
        print("[Strategy] FORCE_EMAIL_CHANNEL enabled — channel set to Email.")

    return {
        **state,
        "subscriber_profile": trace.get("subscriber_profile"),
        "interaction_history": trace.get("interaction_history", []),
        "strategy_result": result,
    }
