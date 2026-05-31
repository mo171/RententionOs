from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

from models.causal_models import CausalScoreRequest, CausalSnapshotResponse
from models.churn_models import ChurnMetricsResponse, ChurnScoreRequest
from models.ltv_models import LTVMetricsResponse, LTVScoreRequest
from services.causal.uplift_service import (
    build_causal_snapshot,
    retrain_uplift_model,
    score_customer,
)
from services.churn.churn_service import (
    get_churn_metrics,
    retrain_churn_model,
    score_customer as score_churn_customer,
)
from services.ltv.ltv_service import (
    get_ltv_metrics,
    retrain_ltv_model,
    score_customer as score_ltv_customer,
)
from api.inngest_routes import router as inngest_router
from api.approval_routes import router as approval_router
from api.intervention_routes import router as intervention_router
from api.websocket_routes import router as websocket_router

load_dotenv()

app = FastAPI(title="RetentionOS Agentic Backend", version="1.0.0")

app.include_router(inngest_router)
app.include_router(approval_router)
app.include_router(intervention_router)
app.include_router(websocket_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class LLMInvokeRequest(BaseModel):
    prompt: str

class TriggerCallbackPayload(BaseModel):
    task_id: str
    status: str
    result: dict | None = None

@app.get("/health")
def health_check():
    """Health check endpoint to verify backend is running."""
    return {"status": "ok", "message": "RetentionOS Agentic Backend is up."}

@app.get("/api/causal/snapshot", response_model=CausalSnapshotResponse)
def causal_snapshot():
    """Return the latest causal dashboard snapshot from bank.csv."""
    try:
        return build_causal_snapshot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/causal/retrain", response_model=CausalSnapshotResponse)
def retrain_causal_model():
    """Retrain the MVP uplift artifacts and return a fresh dashboard snapshot."""
    try:
        return retrain_uplift_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/causal/score")
def score_causal_customer(request: CausalScoreRequest):
    """Score one customer and return uplift plus treatment optimization."""
    try:
        return score_customer(
            request.customer,
            clv=request.clv,
            treatment_costs=request.treatment_costs,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ltv/metrics", response_model=LTVMetricsResponse)
def ltv_metrics():
    """Return the latest LTV model metrics and gate diagnostics."""
    try:
        return get_ltv_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ltv/retrain", response_model=LTVMetricsResponse)
def retrain_ltv():
    """Retrain the MVP LTV model and regenerate artifacts plus metrics."""
    try:
        return retrain_ltv_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ltv/score")
def score_ltv(request: LTVScoreRequest):
    """Score one customer for financial value and churn-stage eligibility."""
    try:
        return score_ltv_customer(request.customer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/churn/metrics", response_model=ChurnMetricsResponse)
def churn_metrics():
    """Return the latest churn model metrics generated from bank.csv."""
    try:
        return get_churn_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/churn/retrain", response_model=ChurnMetricsResponse)
def retrain_churn():
    """Retrain the MVP churn model and regenerate artifacts plus metrics."""
    try:
        return retrain_churn_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/churn/score")
def score_churn(request: ChurnScoreRequest):
    """Score one customer and return churn probability plus risk tier."""
    try:
        return score_churn_customer(request.customer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/invoke")
async def invoke_llm(request: LLMInvokeRequest):
    """Test endpoint for Langchain LLM invocation."""
    try:
        from utils.llm import get_llm

        llm = get_llm()
        response = llm.invoke(request.prompt)
        return {"status": "success", "response": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trigger/callback")
async def trigger_callback(payload: TriggerCallbackPayload):
    """Callback endpoint for Trigger.dev tasks completion."""
    # Handle the callback from Trigger.dev 
    # (e.g. updating DB that a message was sent, or a step finished)
    print(f"Received Trigger.dev callback for task {payload.task_id} with status {payload.status}")
    return {"status": "received", "task_id": payload.task_id}

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
