"""
Message Writer — LangGraph Node 3.
"""
from services.writer.writer_service import generate_draft, build_fallback_draft
from models.strategy_models import InterventionGraphState


def writer_node(state: InterventionGraphState) -> InterventionGraphState:
    if state.get("use_fallback_template"):
        from models.compliance_models import InterventionPayload

        payload = state["payload"]
        if isinstance(payload, dict):
            payload = InterventionPayload(**payload)
        profile = state.get("subscriber_profile") or {}
        channel = "Email"
        sr = state.get("strategy_result")
        if sr and not isinstance(sr, dict):
            channel = sr.channel
        elif isinstance(sr, dict):
            channel = sr.get("channel", "Email")
        draft = build_fallback_draft(channel, payload, profile)
        print("[Writer] Using fallback template after max revisions.")
    else:
        draft = generate_draft(state)

    return {
        **state,
        "current_draft": draft,
    }
