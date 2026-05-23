from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChurnScoreRequest(BaseModel):
    """Single-customer scoring request for the churn model."""

    customer: dict[str, Any] = Field(
        description="Bank customer feature map using bank.csv column names."
    )


class ChurnScoreResponse(BaseModel):
    churn_probability: float
    retention_probability: float
    risk_tier: Literal["low", "medium", "high", "critical"]
    should_enter_uplift_model: bool
    top_risk_drivers: list[str]


class ChurnMetricsResponse(BaseModel):
    metrics: dict[str, Any]
    model_metadata: dict[str, Any]

