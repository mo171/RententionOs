from fastapi import APIRouter, HTTPException, Depends
from typing import List
import os
import asyncio
from datetime import datetime, timezone

from models.approval_models import ApprovalResponse, ApprovalStatusUpdate, ApprovalMessageEdit
from utils.supabase_client import get_supabase_client
from api.websocket_routes import broadcast_approval_update
from services.tools.send_message import send_message
from models.message_models import MessageDraft

router = APIRouter()

def map_db_to_approval_response(row: dict) -> ApprovalResponse:
    payload = row.get("payload", {})
    cr = row.get("compliance_result", {})
    sr = row.get("strategy_result", {})
    draft = row.get("message_draft", {})
    
    amount = payload.get("best_discount")
    if not amount and payload.get("expected_profit"):
        amount = f"${payload.get('expected_profit')}"

    return ApprovalResponse(
        id=str(row["id"]),
        company="Subscriber #" + str(row["user_id"]),
        contact=f"User {row['user_id']}",
        type=f"Offer {payload.get('best_discount', 'discount')}",
        amount=amount,
        confidence=cr.get("confidence", 0) if cr else 0,
        risk="High" if cr and not cr.get("intervene") else "Medium",
        summary=row.get("reasoning_text", "")[:100] + "...",
        status=row["status"],
        createdAt=row.get("created_at", ""),
        agentAction={
            "action": f"offer_{payload.get('best_discount', '').replace('%', '')}",
            "amount": amount,
            "channel": sr.get("channel", "Email") if sr else "Email",
            "template": "dynamic_draft",
            "send_at": sr.get("scheduled_time", "auto") if sr else "auto",
            "expected_lift": f"+{round(payload.get('uplift_score', 0) * 100, 1)}%" if payload.get('uplift_score') else "N/A",
            "expected_roi": f"${payload.get('expected_profit', 0)}"
        },
        messagePreview={
            "subject": draft.get("subject", ""),
            "body": draft.get("body_plain", "")
        },
        reasoning={
            "text": row.get("reasoning_text", ""),
            "bullets": row.get("reasoning_bullets", [])
        },
        alternatives=[]
    )

@router.get("/api/approvals", response_model=List[ApprovalResponse])
def get_approvals():
    """Retrieve all pending approvals, ordered by most recent."""
    supabase = get_supabase_client()
    response = supabase.table("pending_approvals").select("*").order("created_at", desc=True).limit(50).execute()
    return [map_db_to_approval_response(row) for row in response.data]

@router.get("/api/approvals/{approval_id}", response_model=ApprovalResponse)
def get_approval(approval_id: str):
    """Retrieve a single approval by ID."""
    supabase = get_supabase_client()
    response = supabase.table("pending_approvals").select("*").eq("id", approval_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Approval not found")
    return map_db_to_approval_response(response.data[0])

@router.patch("/api/approvals/{approval_id}")
def update_approval_message(approval_id: str, edit: ApprovalMessageEdit):
    """Allow admin to edit the message draft before approval."""
    supabase = get_supabase_client()
    
    # Get current approval to preserve existing fields
    res = supabase.table("pending_approvals").select("message_draft").eq("id", approval_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    draft = res.data[0].get("message_draft", {})
    draft["subject"] = edit.subject
    draft["body_plain"] = edit.body
    # Build HTML body from plain text if it's an Email
    if draft.get("channel") == "Email":
        from services.writer.writer_service import build_email_html
        subscriber_name = "Valued Customer"  # Could fetch from profile if needed
        cta_text = draft.get("cta_text", "Get this discount")
        cta_url = draft.get("cta_url", "#")
        discount = draft.get("subject", "").split()[-1] if draft.get("subject") else ""
        draft["body_html"] = build_email_html(
            edit.body,
            cta_text,
            cta_url,
            discount,
            subscriber_name
        )
    
    response = supabase.table("pending_approvals").update({"message_draft": draft}).eq("id", approval_id).execute()
    
    if response.data:
        # Broadcast update to frontend (via WebSocket)
        updated_model = map_db_to_approval_response(response.data[0])
        try:
            # Use asyncio to run the async broadcast
            loop = asyncio.new_event_loop()
            loop.run_until_complete(broadcast_approval_update({
                "type": "approval_updated",
                "data": updated_model.model_dump()
            }))
        except Exception as e:
            print(f"[Approval] Warning: WebSocket broadcast failed: {e}")
        
    return {"status": "success", "message": "Draft updated"}

@router.post("/api/approvals/{approval_id}/approve")
def approve_intervention(approval_id: str):
    """Approve an intervention — update status and trigger dispatch."""
    supabase = get_supabase_client()
    
    response = supabase.table("pending_approvals").update({
        "status": "approved",
        "approved_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", approval_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    row = response.data[0]
    draft_dict = row.get("message_draft")
    
    # If there's a draft, trigger message dispatch
    if draft_dict:
        try:
            draft = MessageDraft(**draft_dict)
            test_mode = os.environ.get("TEST_MODE", "true").lower() in ("1", "true", "yes")
            # In production, we'd use Trigger.dev to schedule this at strategy_result.scheduled_time
            # For now, we send immediately in test mode
            result = send_message(draft, test_mode=test_mode)
            print(f"[Approval] Dispatch triggered for approval {approval_id}: {result}")
        except Exception as e:
            print(f"[Approval] Error during dispatch: {str(e)}")
            # Don't fail the approval just because dispatch had an issue
    
    # Broadcast update to frontend
    updated_model = map_db_to_approval_response(row)
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(broadcast_approval_update({
            "type": "approval_approved",
            "data": updated_model.model_dump()
        }))
    except Exception as e:
        print(f"[Approval] Warning: WebSocket broadcast failed: {e}")
    
    return {"status": "success", "message": "Intervention approved and dispatched"}

@router.post("/api/approvals/{approval_id}/reject")
def reject_intervention(approval_id: str):
    """Reject an intervention."""
    supabase = get_supabase_client()
    
    response = supabase.table("pending_approvals").update({
        "status": "rejected",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", approval_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    row = response.data[0]
    
    # Broadcast update to frontend
    updated_model = map_db_to_approval_response(row)
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(broadcast_approval_update({
            "type": "approval_rejected",
            "data": updated_model.model_dump()
        }))
    except Exception as e:
        print(f"[Approval] Warning: WebSocket broadcast failed: {e}")
    
    return {"status": "success", "message": "Intervention rejected"}
