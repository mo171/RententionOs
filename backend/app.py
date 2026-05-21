from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

from utils.llm import get_llm
from utils.trigger import get_trigger_client

load_dotenv()

app = FastAPI(title="RetentionOS Agentic Backend", version="1.0.0")

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

@app.post("/api/llm/invoke")
async def invoke_llm(request: LLMInvokeRequest):
    """Test endpoint for Langchain LLM invocation."""
    try:
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
