from fastapi import APIRouter, HTTPException, Depends
from typing import List
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
    supabase = get_supabase_client()
    response = supabase.table("pending_approvals").select("*").order("created_at", desc=True).limit(50).execute()
    return [map_db_to_approval_response(row) for row in response.data]

@router.get("/api/approvals/{approval_id}", response_model=ApprovalResponse)
def get_approval(approval_id: str):
    supabase = get_supabase_client()
    response = supabase.table("pending_approvals").select("*").eq("id", approval_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Approval not found")
    return map_db_to_approval_response(response.data[0])

@router.patch("/api/approvals/{approval_id}")
def update_approval_message(approval_id: str, edit: ApprovalMessageEdit):
    supabase = get_supabase_client()
    
    # Get current to update just the draft part
    res = supabase.table("pending_approvals").select("message_draft").eq("id", approval_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    draft = res.data[0].get("message_draft", {})
    draft["subject"] = edit.subject
    draft["body_plain"] = edit.body
    # Optionally update HTML body, simplified here
    
    response = supabase.table("pending_approvals").update({"message_draft": draft}).eq("id", approval_id).execute()
    
    if response.data:
        # Broadcast update
        updated_model = map_db_to_approval_response(response.data[0])
        import asyncio
        asyncio.create_task(broadcast_approval_update(updated_model.model_dump()))
        
    return {"status": "success"}

@router.post("/api/approvals/{approval_id}/status")
def update_approval_status(approval_id: str, update: ApprovalStatusUpdate):
    supabase = get_supabase_client()
    
    response = supabase.table("pending_approvals").update({"status": update.status}).eq("id", approval_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    row = response.data[0]
    
    # If approved, dispatch the message
    if update.status == "approved":
        draft_dict = row.get("message_draft")
        if draft_dict:
            # We use send_message tool directly for dispatch, simulating trigger.dev wait
            # We would normally schedule this via trigger.dev
            draft = MessageDraft(**draft_dict)
            try:
                # Note: getting email/phone requires fetching profile which isn't fully in pending_approvals, 
                # but we will send to TEST_RECIPIENT_EMAIL via test_mode in dispatch
                # If WhatsApp, we need to pass a phone number
                test_mode = os.environ.get("TEST_MODE", "true").lower() in ("1", "true", "yes")
                send_message(draft, test_mode=test_mode)
            except Exception as e:
                print(f"Error dispatching approved message: {e}")
                
    # Broadcast update
    updated_model = map_db_to_approval_response(row)
    import asyncio
    asyncio.create_task(broadcast_approval_update(updated_model.model_dump()))
        
    return {"status": "success"}
