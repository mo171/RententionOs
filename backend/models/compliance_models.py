from __future__ import annotations
from typing import TypedDict, Optional
from pydantic import BaseModel, Field


# ─── Input from ML pipeline ──────────────────────────────────────────────────

class InterventionPayload(BaseModel):
    """The JSON that arrives from the ML pipeline after treatment optimization."""
    user_id: int
    best_discount: str          # e.g. "10%"
    expected_profit: float      # e.g. 1400.0
    
    # Optional fields from the Gatekeeper ML pipeline
    ltv: Optional[float] = None
    churn_prob: Optional[float] = None
    uplift_score: Optional[float] = None
    recommended_incentive: Optional[str] = None
    segment: Optional[str] = None


# ─── CRAG intermediate ───────────────────────────────────────────────────────

class RelevanceGrade(BaseModel):
    """Structured output from the relevance grader LLM per chunk."""
    is_relevant: bool = Field(description="Whether this chunk is relevant to the query")
    explanation: str = Field(description="One-sentence reason for the grade")


# ─── Final compliance output ─────────────────────────────────────────────────

class ComplianceResult(BaseModel):
    """Final structured output of the CRAG Compliance Agent."""
    intervene: bool = Field(description="Whether intervention is approved by policy")
    reasoning: str  = Field(description="Verbose chain-of-thought trace for UI display")
    policy_source: str = Field(description="Name of the policy document that decided this")
    confidence: int = Field(ge=1, le=10, description="Agent self-assessed confidence score 1-10")


# LangGraph shared state: see models.strategy_models.InterventionGraphState
# ComplianceAgentState is an alias in strategy_models for backward compatibility.
