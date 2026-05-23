from __future__ import annotations

import csv
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from typing import Any

BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.causal.treatment_optimizer import DEFAULT_TREATMENT_COSTS, optimize_treatments

METRICS_DIR = os.path.dirname(__file__)
METRICS_JSON_PATH = os.path.join(METRICS_DIR, "uplift_model_metrics.json")
METRICS_REPORT_PATH = os.path.join(METRICS_DIR, "uplift_model_report.md")
PERSUADABLES_CSV_PATH = os.path.join(METRICS_DIR, "persuadable_customers.csv")


def write_metrics_bundle(
    artifacts: Any,
    *,
    ltv: float = 1000.0,
    treatment_costs: dict[str, float] | None = None,
    top_n: int = 100,
) -> dict[str, Any]:
    """Evaluate the saved X-learner artifact and persist metrics files.

    The Bank Marketing dataset does not contain randomized treatment assignment,
    so these are observational uplift diagnostics rather than causal proof.
    """

    os.makedirs(METRICS_DIR, exist_ok=True)
    metrics = build_metrics_report(
        artifacts,
        ltv=ltv,
        treatment_costs=treatment_costs,
        top_n=top_n,
    )

    with open(METRICS_JSON_PATH, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

    with open(METRICS_REPORT_PATH, "w", encoding="utf-8") as handle:
        handle.write(_render_markdown_report(metrics))

    _write_persuadables_csv(metrics["prioritized_persuadables"], PERSUADABLES_CSV_PATH)
    return metrics


def build_metrics_report(
    artifacts: Any,
    *,
    ltv: float = 1000.0,
    treatment_costs: dict[str, float] | None = None,
    top_n: int = 100,
) -> dict[str, Any]:
    uplift = [float(score) for score in artifacts.uplift_scores]
    outcome = [int(value) for value in artifacts.outcome]
    treatment = [int(value) for value in artifacts.treatment]
    propensities = [float(value) for value in artifacts.propensities]
    churn_scores = _churn_risk_scores(artifacts)
    actual_churn = [1 - value for value in outcome]
    churn_metrics = _binary_classification_metrics(actual_churn, churn_scores)
    qini_curve = _qini_curve(uplift, outcome, treatment)
    causal_metrics = _causal_metrics(uplift, outcome, treatment, qini_curve)
    prioritized = _prioritized_persuadables(
        artifacts,
        uplift,
        ltv=ltv,
        treatment_costs=treatment_costs,
        top_n=top_n,
    )

    treatment_rate = statistics.fmean(treatment) if treatment else 0.0
    outcome_rate = statistics.fmean(outcome) if outcome else 0.0
    positive_uplift = [score for score in uplift if score > 0]
    approved_count = sum(1 for item in prioritized if item["approved"])

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "model": {
            "model_type": "stdlib_x_learner_mvp",
            "trained_at": artifacts.trained_at,
            "row_count": len(outcome),
            "feature_count": len(artifacts.vectorizer.feature_names),
            "feature_columns": list(artifacts.vectorizer.feature_names),
            "model_artifact_path": "backend/artifacts/causal/uplift_artifacts.pkl",
            "metrics_json_path": "backend/metrics/uplift_model_metrics.json",
            "metrics_report_path": "backend/metrics/uplift_model_report.md",
            "persuadables_csv_path": "backend/metrics/persuadable_customers.csv",
        },
        "schema_mapping": {
            "features": {
                "numeric": ["age", "balance", "day", "campaign", "pdays", "previous"],
                "categorical": [
                    "job",
                    "marital",
                    "education",
                    "default",
                    "housing",
                    "loan",
                    "month",
                    "poutcome",
                ],
                "excluded_for_leakage_or_target": ["contact", "deposit", "duration"],
            },
            "treatment": "contact != 'unknown'",
            "outcome": "deposit == 'yes'",
        },
        "dataset": {
            "rows": len(outcome),
            "treated_rows": sum(treatment),
            "control_rows": len(treatment) - sum(treatment),
            "treatment_rate": round(treatment_rate, 4),
            "outcome_rate": round(outcome_rate, 4),
        },
        "causal_metrics": causal_metrics,
        "churn_metrics": churn_metrics,
        "profit_guardrail": {
            "ltv_assumption": round(ltv, 2),
            "default_treatment_costs": DEFAULT_TREATMENT_COSTS,
            "approval_rule": "approved when uplift_score > 0 and best expected_profit > 0",
            "approved_in_top_list": approved_count,
            "top_list_size": len(prioritized),
            "positive_uplift_rows": len(positive_uplift),
            "positive_uplift_rate": round(len(positive_uplift) / max(len(uplift), 1), 4),
        },
        "qini_curve": qini_curve,
        "uplift_deciles": _uplift_deciles(uplift, outcome, treatment),
        "calibration": _calibration_by_decile(uplift, outcome, treatment),
        "propensity_summary": _summary_stats(propensities),
        "uplift_summary": _summary_stats(uplift),
        "prioritized_persuadables": prioritized,
        "caveats": [
            "Individual uplift accuracy cannot be directly observed without randomized counterfactual outcomes.",
            "bank.csv has no true randomized discount assignment; contact != 'unknown' is used as the MVP outreach proxy.",
            "duration is excluded because it is a post-contact leakage feature.",
            "AUUC and Qini are observational diagnostics here, not production causal validity guarantees.",
        ],
    }


def _churn_risk_scores(artifacts: Any) -> list[float]:
    return [1 - artifacts.control_model.predict_proba(x) for x in artifacts.x_rows]


def _binary_classification_metrics(
    y_true: list[int],
    y_score: list[float],
    *,
    threshold: float = 0.5,
) -> dict[str, Any]:
    y_pred = [1 if score >= threshold else 0 for score in y_score]
    tp = sum(1 for pred, true in zip(y_pred, y_true) if pred == 1 and true == 1)
    fp = sum(1 for pred, true in zip(y_pred, y_true) if pred == 1 and true == 0)
    fn = sum(1 for pred, true in zip(y_pred, y_true) if pred == 0 and true == 1)
    tn = sum(1 for pred, true in zip(y_pred, y_true) if pred == 0 and true == 0)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    accuracy = (tp + tn) / max(len(y_true), 1)
    f1 = 2 * precision * recall / max(precision + recall, 0.000001)

    return {
        "threshold": threshold,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "auc_roc": round(_roc_auc(y_true, y_score), 4),
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
    }


def _roc_auc(y_true: list[int], y_score: list[float]) -> float:
    positives = sum(y_true)
    negatives = len(y_true) - positives
    if positives == 0 or negatives == 0:
        return 0.0

    ordered = sorted(zip(y_score, y_true), key=lambda item: item[0])
    rank_sum = 0.0
    rank = 1
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and ordered[j + 1][0] == ordered[i][0]:
            j += 1
        average_rank = (rank + rank + (j - i)) / 2
        positives_in_tie = sum(ordered[k][1] for k in range(i, j + 1))
        rank_sum += positives_in_tie * average_rank
        rank += j - i + 1
        i = j + 1

    return (rank_sum - (positives * (positives + 1) / 2)) / (positives * negatives)


def _causal_metrics(
    uplift: list[float],
    outcome: list[int],
    treatment: list[int],
    qini_curve: list[dict[str, float]],
) -> dict[str, Any]:
    raw_auuc = _area_under_curve(qini_curve, "observed_uplift_rate")
    dashboard_scaled_auuc = max(0.0, min(raw_auuc * 4, 1.0))
    qini_area = _area_under_curve(qini_curve, "incremental_outcomes")
    total_incremental = qini_curve[-1]["incremental_outcomes"] if qini_curve else 0.0
    random_area = total_incremental / 2
    qini_coefficient = qini_area - random_area
    normalized_qini = qini_coefficient / max(abs(total_incremental), 1.0)

    top_decile = _top_fraction_indices(uplift, 0.1)
    top_decile_observed = _observed_uplift_rate(top_decile, outcome, treatment)

    return {
        "auuc": round(raw_auuc, 4),
        "dashboard_scaled_auuc": round(dashboard_scaled_auuc, 4),
        "qini_coefficient": round(qini_coefficient, 4),
        "normalized_qini": round(normalized_qini, 4),
        "top_decile_observed_uplift": round(top_decile_observed, 4),
        "mean_predicted_uplift": round(statistics.fmean(uplift), 4) if uplift else 0.0,
        "median_predicted_uplift": round(statistics.median(uplift), 4) if uplift else 0.0,
        "max_predicted_uplift": round(max(uplift), 4) if uplift else 0.0,
        "min_predicted_uplift": round(min(uplift), 4) if uplift else 0.0,
    }


def _qini_curve(
    uplift: list[float],
    outcome: list[int],
    treatment: list[int],
) -> list[dict[str, float]]:
    ordered = sorted(range(len(uplift)), key=lambda index: uplift[index], reverse=True)
    points = [
        {
            "population_fraction": 0.0,
            "rows": 0,
            "treated_rows": 0,
            "control_rows": 0,
            "observed_uplift_rate": 0.0,
            "incremental_outcomes": 0.0,
        }
    ]

    for pct in range(10, 101, 10):
        n = max(1, round(len(ordered) * pct / 100))
        sample = ordered[:n]
        treated = [index for index in sample if treatment[index] == 1]
        control = [index for index in sample if treatment[index] == 0]
        treated_outcomes = sum(outcome[index] for index in treated)
        control_outcomes = sum(outcome[index] for index in control)
        observed_uplift = _observed_uplift_rate(sample, outcome, treatment)

        if treated and control:
            incremental = treated_outcomes - (len(treated) / len(control)) * control_outcomes
        else:
            incremental = 0.0

        points.append(
            {
                "population_fraction": round(pct / 100, 2),
                "rows": float(n),
                "treated_rows": float(len(treated)),
                "control_rows": float(len(control)),
                "observed_uplift_rate": round(observed_uplift, 4),
                "incremental_outcomes": round(incremental, 4),
            }
        )

    return points


def _area_under_curve(points: list[dict[str, float]], value_key: str) -> float:
    area = 0.0
    for prev, current in zip(points, points[1:]):
        width = current["population_fraction"] - prev["population_fraction"]
        area += width * ((current[value_key] + prev[value_key]) / 2)
    return area


def _observed_uplift_rate(
    indices: list[int],
    outcome: list[int],
    treatment: list[int],
) -> float:
    treated_outcomes = [outcome[index] for index in indices if treatment[index] == 1]
    control_outcomes = [outcome[index] for index in indices if treatment[index] == 0]
    if not treated_outcomes or not control_outcomes:
        return 0.0
    return statistics.fmean(treated_outcomes) - statistics.fmean(control_outcomes)


def _top_fraction_indices(uplift: list[float], fraction: float) -> list[int]:
    ordered = sorted(range(len(uplift)), key=lambda index: uplift[index], reverse=True)
    n = max(1, round(len(ordered) * fraction))
    return ordered[:n]


def _uplift_deciles(
    uplift: list[float],
    outcome: list[int],
    treatment: list[int],
) -> list[dict[str, float]]:
    ordered = sorted(range(len(uplift)), key=lambda index: uplift[index], reverse=True)
    deciles = _chunks(ordered, 10)
    rows = []
    for index, group in enumerate(deciles, start=1):
        rows.append(
            {
                "decile": float(index),
                "rows": float(len(group)),
                "mean_predicted_uplift": round(statistics.fmean(uplift[i] for i in group), 4),
                "observed_uplift_rate": round(_observed_uplift_rate(group, outcome, treatment), 4),
            }
        )
    return rows


def _calibration_by_decile(
    uplift: list[float],
    outcome: list[int],
    treatment: list[int],
) -> list[dict[str, float]]:
    ordered = sorted(range(len(uplift)), key=lambda index: uplift[index])
    deciles = _chunks(ordered, 10)
    rows = []
    for index, group in enumerate(deciles, start=1):
        predicted = statistics.fmean(uplift[i] for i in group)
        observed = _observed_uplift_rate(group, outcome, treatment)
        rows.append(
            {
                "bin": float(index),
                "mean_predicted_uplift": round(predicted, 4),
                "observed_uplift_rate": round(observed, 4),
                "absolute_error": round(abs(predicted - observed), 4),
            }
        )
    return rows


def _prioritized_persuadables(
    artifacts: Any,
    uplift: list[float],
    *,
    ltv: float,
    treatment_costs: dict[str, float] | None,
    top_n: int,
) -> list[dict[str, Any]]:
    rows = []
    for index, score in enumerate(uplift):
        best, recommendations = optimize_treatments(score, ltv, treatment_costs)
        approved = score > 0 and best.expected_profit > 0
        if not approved:
            continue

        source = artifacts.rows[index]
        control_probability = artifacts.control_model.predict_proba(artifacts.x_rows[index])
        treated_probability = artifacts.treated_model.predict_proba(artifacts.x_rows[index])
        rows.append(
            {
                "rank": 0,
                "customer_id": f"bank_row_{index + 1}",
                "source_row": index + 1,
                "age": _to_int(source.get("age")),
                "balance": round(_to_float(source.get("balance")), 2),
                "housing": source.get("housing", ""),
                "loan": source.get("loan", ""),
                "campaign": _to_int(source.get("campaign")),
                "uplift_score": round(score, 4),
                "propensity": round(float(artifacts.propensities[index]), 4),
                "baseline_stay_probability": round(control_probability, 4),
                "treated_stay_probability": round(treated_probability, 4),
                "best_treatment": best.treatment,
                "expected_profit": best.expected_profit,
                "cost": best.cost,
                "approved": approved,
                "recommendations": [item.model_dump() for item in recommendations],
            }
        )

    rows.sort(key=lambda row: row["expected_profit"], reverse=True)
    for rank, row in enumerate(rows[:top_n], start=1):
        row["rank"] = rank
    return rows[:top_n]


def _write_persuadables_csv(rows: list[dict[str, Any]], path: str) -> None:
    fieldnames = [
        "rank",
        "customer_id",
        "source_row",
        "age",
        "balance",
        "housing",
        "loan",
        "campaign",
        "uplift_score",
        "propensity",
        "baseline_stay_probability",
        "treated_stay_probability",
        "best_treatment",
        "expected_profit",
        "cost",
        "approved",
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def _summary_stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0.0, "p25": 0.0, "median": 0.0, "mean": 0.0, "p75": 0.0, "max": 0.0}
    ordered = sorted(values)
    return {
        "min": round(ordered[0], 4),
        "p25": round(_quantile(ordered, 0.25), 4),
        "median": round(statistics.median(ordered), 4),
        "mean": round(statistics.fmean(ordered), 4),
        "p75": round(_quantile(ordered, 0.75), 4),
        "max": round(ordered[-1], 4),
    }


def _quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    position = (len(sorted_values) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _chunks(values: list[int], n: int) -> list[list[int]]:
    size = max(len(values) // n, 1)
    groups = [values[i : i + size] for i in range(0, len(values), size)]
    if len(groups) > n:
        groups[n - 1].extend(item for group in groups[n:] for item in group)
        groups = groups[:n]
    return groups


def _render_markdown_report(metrics: dict[str, Any]) -> str:
    causal = metrics["causal_metrics"]
    churn = metrics["churn_metrics"]
    data = metrics["dataset"]
    profit = metrics["profit_guardrail"]
    model = metrics["model"]

    lines = [
        "# RetentionOS Uplift Model Metrics",
        "",
        f"Generated at: `{metrics['generated_at']}`",
        f"Model artifact: `{model['model_artifact_path']}`",
        f"Rows evaluated: `{data['rows']}`",
        "",
        "## Schema Mapping",
        "",
        "- Features: behavioral and demographic Bank Marketing columns, excluding target/leakage fields.",
        f"- Treatment: `{metrics['schema_mapping']['treatment']}`",
        f"- Outcome: `{metrics['schema_mapping']['outcome']}`",
        "- Leakage excluded: `contact`, `deposit`, `duration`",
        "",
        "## Causal Metrics",
        "",
        f"- AUUC: `{causal['auuc']}`",
        f"- Dashboard-scaled AUUC: `{causal['dashboard_scaled_auuc']}`",
        f"- Qini coefficient: `{causal['qini_coefficient']}`",
        f"- Normalized Qini: `{causal['normalized_qini']}`",
        f"- Top-decile observed uplift: `{causal['top_decile_observed_uplift']}`",
        f"- Mean predicted uplift: `{causal['mean_predicted_uplift']}`",
        "",
        "## Churn Base Filter Metrics",
        "",
        f"- Precision: `{churn['precision']}`",
        f"- Recall: `{churn['recall']}`",
        f"- AUC-ROC: `{churn['auc_roc']}`",
        f"- F1: `{churn['f1']}`",
        f"- Accuracy: `{churn['accuracy']}`",
        f"- Confusion: `{churn['confusion']}`",
        "",
        "## Profit Guardrail",
        "",
        f"- LTV assumption: `{profit['ltv_assumption']}`",
        f"- Approval rule: `{profit['approval_rule']}`",
        f"- Approved rows in prioritized CSV: `{profit['approved_in_top_list']}`",
        f"- Positive uplift rows: `{profit['positive_uplift_rows']}`",
        f"- Persuadable CSV: `{model['persuadables_csv_path']}`",
        "",
        "## Interpretation",
        "",
        "The uplift model does not have directly observable individual-level accuracy because each customer has only one observed outcome. "
        "Use AUUC, Qini, decile uplift, calibration, and future randomized holdout experiments to judge causal quality.",
        "",
        "## Caveats",
        "",
    ]
    lines.extend(f"- {caveat}" for caveat in metrics["caveats"])
    lines.append("")
    return "\n".join(lines)


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


if __name__ == "__main__":
    from services.causal.uplift_service import get_artifacts

    written = write_metrics_bundle(get_artifacts())
    print(json.dumps({"metrics_json": METRICS_JSON_PATH, "rows": written["dataset"]["rows"]}, indent=2))
