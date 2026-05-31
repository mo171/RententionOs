from fastapi import APIRouter, HTTPException
from models.compliance_models import InterventionPayload
from inngest_client import inngest_client

router = APIRouter()

@router.post("/api/interventions/start")
def start_intervention(payload: InterventionPayload):
    """
    Accepts an ML payload and triggers the Inngest workflow to process it.
    """
    try:
        inngest_client.send_sync({
            "name": "gatekeeper/process.retention",
            "data": payload.model_dump()
        })
        return {"status": "success", "message": "Intervention workflow started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
