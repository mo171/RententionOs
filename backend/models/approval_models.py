from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ApprovalStatusUpdate(BaseModel):
    status: str = Field(description="Must be 'approved' or 'dismissed'")

class ApprovalMessageEdit(BaseModel):
    subject: str
    body: str

# Pydantic model for the frontend Approval interface
class AgentActionModel(BaseModel):
    action: str
    amount: str
    channel: str
    template: str
    send_at: str
    expected_lift: str
    expected_roi: str

class MessagePreviewModel(BaseModel):
    subject: str
    body: str

class ReasoningModel(BaseModel):
    text: str
    bullets: List[str]

class AlternativeModel(BaseModel):
    label: str
    amount: str
    roi: str
    selected: bool

class ApprovalResponse(BaseModel):
    id: str
    company: str
    contact: str
    type: str
    amount: Optional[str] = None
    confidence: int
    risk: str
    summary: str
    status: str
    createdAt: str
    agentAction: AgentActionModel
    messagePreview: MessagePreviewModel
    reasoning: ReasoningModel
    alternatives: List[AlternativeModel]
