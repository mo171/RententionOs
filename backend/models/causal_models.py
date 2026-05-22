from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CausalScoreRequest(BaseModel):
    """Single-customer scoring request for the uplift service."""

    customer: dict[str, Any] = Field(
        description="Bank customer feature map using bank.csv column names."
    )
    clv: float = Field(default=1000.0, ge=0)
    treatment_costs: dict[str, float] | None = Field(default=None)


class TreatmentRecommendation(BaseModel):
    treatment: str
    uplift: float
    expected_profit: float
    cost: float


class CausalScoreResponse(BaseModel):
    uplift_score: float
    propensity: float
    baseline_stay_probability: float
    treated_stay_probability: float
    segment: Literal["Persuadables", "Sure Things", "Lost Causes", "Sleeping Dogs"]
    best_treatment: TreatmentRecommendation
    recommendations: list[TreatmentRecommendation]


class CausalSnapshotResponse(BaseModel):
    """Shape returned to the frontend causal model store."""

    snapshot: dict[str, Any]
    model_metadata: dict[str, Any]

