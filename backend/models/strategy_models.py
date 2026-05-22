from __future__ import annotations
from typing import TypedDict, Optional, Any
from pydantic import BaseModel, Field

from models.compliance_models import (
    InterventionPayload,
    ComplianceResult,
)
from models.message_models import MessageDraft, ReviewResult, SendMessageResult


class SubscriberProfile(BaseModel):
    """Row from subscribers table."""
    user_id: int
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    timezone: str = "UTC"
    preferred_channel: str = "email"
    opt_out_sms: bool = False
    opt_out_email: bool = False
    opt_out_push: bool = False
    segment: Optional[str] = None
    ltv_tier: Optional[str] = None


class InteractionEvent(BaseModel):
    """Row from interaction_events table."""
    id: str
    user_id: int
    channel: str
    event_type: str
    sent_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class StrategyResult(BaseModel):
    """Final output of the Strategy Agent (Node 2)."""
    channel: str = Field(description="Email | SMS | Push Notification")
    scheduled_time: str = Field(description="ISO-8601 UTC datetime for send")
    reasoning: str = Field(description="Why this channel and time were chosen")
    confidence: int = Field(ge=1, le=10, description="Agent confidence 1-10")


class InterventionGraphState(TypedDict, total=False):
    """Shared LangGraph state for the full intervention pipeline."""

    # ML payload — flows through all nodes untouched
    payload: InterventionPayload

    # Node 1 — Compliance / CRAG
    queries: list[str]
    primary_query: str
    raw_chunks: list[dict]
    fused_chunks: list[dict]
    graded_chunks: list[dict]
    reasoning_trace: str
    compliance_result: Optional[ComplianceResult]
    should_intervene: bool

    # Node 2 — Strategy
    subscriber_profile: Optional[dict]
    interaction_history: list[dict]
    strategy_result: Optional[StrategyResult]

    # Node 3 — Writer
    current_draft: Optional[MessageDraft]
    revision_count: int
    use_fallback_template: bool

    # Node 4 — Reviewer
    review_history: list[dict]
    last_review: Optional[ReviewResult]
    final_approved: bool

    # Dispatch
    send_result: Optional[SendMessageResult]


# Backward compatibility for Node 1-only graph
ComplianceAgentState = InterventionGraphState
