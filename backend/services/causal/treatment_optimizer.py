from __future__ import annotations

from models.causal_models import TreatmentRecommendation


DEFAULT_TREATMENT_COSTS = {
    "discount_5": 50.0,
    "discount_10": 100.0,
    "discount_15": 150.0,
    "discount_20": 200.0,
}

TREATMENT_MULTIPLIERS = {
    "discount_5": 0.72,
    "discount_10": 1.0,
    "discount_15": 1.14,
    "discount_20": 1.22,
}


def optimize_treatments(
    uplift_score: float,
    clv: float,
    treatment_costs: dict[str, float] | None = None,
) -> tuple[TreatmentRecommendation, list[TreatmentRecommendation]]:
    costs = {**DEFAULT_TREATMENT_COSTS, **(treatment_costs or {})}

    recommendations = []
    for treatment, cost in costs.items():
        multiplier = TREATMENT_MULTIPLIERS.get(treatment, 1.0)
        treatment_uplift = max(min(uplift_score * multiplier, 0.95), -0.95)
        expected_profit = (treatment_uplift * clv) - cost
        recommendations.append(
            TreatmentRecommendation(
                treatment=treatment,
                uplift=round(treatment_uplift, 4),
                expected_profit=round(expected_profit, 2),
                cost=round(cost, 2),
            )
        )

    recommendations.sort(key=lambda item: item.expected_profit, reverse=True)
    return recommendations[0], recommendations

