from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class MessageDraft(BaseModel):
    """Output of the Message Writer (Node 3)."""
    channel: str
    subject: Optional[str] = None
    body_plain: str
    body_html: Optional[str] = None
    cta_text: str
    cta_url: str


class ReviewResult(BaseModel):
    """Output of the Meta Tribe reviewer (Node 4) — LLM today; TRIBE v2 future."""
    approved: bool
    score: int = Field(ge=1, le=10)
    feedback: str


class SendMessageResult(BaseModel):
    """Result from the unified send_message delivery tool."""
    success: bool
    channel: str
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None
