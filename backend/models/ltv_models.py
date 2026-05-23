from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class LTVScoreRequest(BaseModel):
    """Single-customer scoring request for the LTV gate."""

    customer: dict[str, Any] = Field(
        description="Banking customer feature map using RetentionOS LTV fields."
    )


class LTVScoreResponse(BaseModel):
    historical_ltv_12m: float
    predicted_ltv_12m: float
    default_risk_probability: float
    cfvs: float
    ltv_tier: Literal["ineligible", "low", "medium", "high", "premium"]
    eligible_for_churn_scoring: bool
    recommended_action: str
    top_value_drivers: list[str]
    top_risk_drivers: list[str]


class LTVMetricsResponse(BaseModel):
    metrics: dict[str, Any]
    model_metadata: dict[str, Any]

