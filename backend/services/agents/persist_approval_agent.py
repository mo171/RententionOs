import os
import uuid
import json
import asyncio
from datetime import datetime, timezone

from models.strategy_models import InterventionGraphState
from models.compliance_models import InterventionPayload, ComplianceResult
from models.strategy_models import StrategyResult
from models.message_models import MessageDraft, ReviewResult
from utils.supabase_client import get_supabase_client

def persist_approval_node(state: InterventionGraphState) -> InterventionGraphState:
    """
    LangGraph node: In production mode, this runs instead of dispatch.
    It takes the final state after reviewer and persists to Supabase.
    """
    supabase = get_supabase_client()
    
    payload = state.get("payload")
    if isinstance(payload, dict):
        payload = InterventionPayload(**payload)
        
    cr = state.get("compliance_result")
    if isinstance(cr, dict):
        cr = ComplianceResult(**cr)
        
    sr = state.get("strategy_result")
    if isinstance(sr, dict):
        sr = StrategyResult(**sr)
        
    draft = state.get("current_draft")
    if isinstance(draft, dict):
        draft = MessageDraft(**draft)
        
    review = state.get("last_review")
    if isinstance(review, dict):
        review = ReviewResult(**review)

    profile = state.get("subscriber_profile", {})

    record = {
        "user_id": payload.user_id,
        "status": "pending",
        "payload": payload.model_dump() if payload else {},
        "compliance_result": cr.model_dump() if cr else {},
        "strategy_result": sr.model_dump() if sr else {},
        "message_draft": draft.model_dump() if draft else {},
        "review_result": review.model_dump() if review else {},
        # Provide fallback if cr is None
        "reasoning_text": cr.reasoning if cr else "No reasoning available.",
        "reasoning_bullets": [
            f"Expected profit: ${payload.expected_profit if payload else 'Unknown'}",
            f"Segment: {payload.segment if payload and hasattr(payload, 'segment') and payload.segment else profile.get('segment', 'Unknown')}",
            f"Strategy chosen: {sr.channel if sr else 'Unknown'}"
        ],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # Note: We omit graph_state to avoid storing massive json
        response = supabase.table("pending_approvals").insert(record).execute()
        if response.data:
            print(f"[PersistApproval] Successfully stored pending approval for user {payload.user_id}")
            try:
                from api.approval_routes import map_db_to_approval_response
                from api.websocket_routes import broadcast_approval_update
                updated_model = map_db_to_approval_response(response.data[0])
                loop = asyncio.new_event_loop()
                loop.run_until_complete(broadcast_approval_update({
                    "type": "approval_new",
                    "data": updated_model.model_dump()
                }))
            except Exception as e:
                print(f"[PersistApproval] Warning: WebSocket broadcast failed: {e}")
        else:
            print(f"[PersistApproval] Failed to store approval: {response}")
    except Exception as e:
        print(f"[PersistApproval] Error storing approval: {e}")

    # Don't modify the core state, just return it so graph ends
    return state
