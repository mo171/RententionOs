"""
Meta Tribe Reviewer — LangGraph Node 4.
"""
from models.message_models import MessageDraft, ReviewResult
from models.strategy_models import InterventionGraphState
from services.meta_tribe.meta_tribe_service import review_draft

MAX_REVISIONS = 3


def reviewer_node(state: InterventionGraphState) -> InterventionGraphState:
    draft = state.get("current_draft")
    if draft is None:
        raise ValueError("reviewer_node requires current_draft from writer")

    if isinstance(draft, dict):
        draft = MessageDraft(**draft)

    result = review_draft(draft, state)
    history = list(state.get("review_history") or [])
    history.append(result.model_dump())

    revision_count = state.get("revision_count", 0)
    final_approved = result.approved

    return {
        **state,
        "last_review": result,
        "review_history": history,
        "final_approved": final_approved,
        "revision_count": revision_count,
    }
