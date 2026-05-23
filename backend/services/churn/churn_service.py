from __future__ import annotations

import csv
import json
import math
import os
import pickle
import random
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from models.churn_models import ChurnScoreResponse

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "bank.csv")
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "artifacts", "churn")
MODEL_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "churn_model.pkl")
METADATA_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "churn_metadata.json")
METRICS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "metrics")
METRICS_JSON_PATH = os.path.join(METRICS_DIR, "churn_model_metrics.json")
METRICS_REPORT_PATH = os.path.join(METRICS_DIR, "churn_model_report.md")
HIGH_RISK_CSV_PATH = os.path.join(METRICS_DIR, "high_risk_customers.csv")
ARTIFACT_VERSION = 1

NUMERIC_COLUMNS = ["age", "balance", "day", "campaign", "pdays", "previous"]
CATEGORICAL_COLUMNS = [
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "month",
    "poutcome",
]
EXCLUDED_COLUMNS = {"contact", "deposit", "duration"}


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


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


class ChurnVectorizer:
    def __init__(self) -> None:
        self.numeric_stats: dict[str, tuple[float, float]] = {}
        self.categories: dict[str, list[str]] = {}
        self.feature_names: list[str] = []

    def fit(self, rows: list[dict[str, str]]) -> None:
        for col in NUMERIC_COLUMNS:
            values = [_to_float(row.get(col), 0.0) for row in rows]
            mean = statistics.fmean(values)
            stdev = statistics.pstdev(values) or 1.0
            self.numeric_stats[col] = (mean, stdev)

        for col in CATEGORICAL_COLUMNS:
            values = sorted({(row.get(col) or "unknown").strip().lower() for row in rows})
            self.categories[col] = values

        self.feature_names = (
            NUMERIC_COLUMNS[:]
            + [
                f"{col}={value}"
                for col in CATEGORICAL_COLUMNS
                for value in self.categories[col]
            ]
        )

    def transform_one(self, row: dict[str, Any]) -> list[float]:
        features: list[float] = []
        for col in NUMERIC_COLUMNS:
            mean, stdev = self.numeric_stats[col]
            features.append((_to_float(row.get(col), mean) - mean) / stdev)

        for col in CATEGORICAL_COLUMNS:
            value = str(row.get(col, "unknown")).strip().lower()
            features.extend(1.0 if value == category else 0.0 for category in self.categories[col])

        return features

    def transform(self, rows: list[dict[str, Any]]) -> list[list[float]]:
        return [self.transform_one(row) for row in rows]


class LogisticChurnModel:
    def __init__(self, n_features: int) -> None:
        self.weights = [0.0] * (n_features + 1)

    def fit(
        self,
        x_rows: list[list[float]],
        y_values: list[int],
        *,
        epochs: int = 32,
        lr: float = 0.032,
        l2: float = 0.001,
    ) -> None:
        if not x_rows:
            return

        positives = sum(y_values)
        negatives = len(y_values) - positives
        positive_weight = len(y_values) / max(2 * positives, 1)
        negative_weight = len(y_values) / max(2 * negatives, 1)

        for _ in range(epochs):
            for x, y in zip(x_rows, y_values):
                prediction = self.predict_proba(x)
                sample_weight = positive_weight if y == 1 else negative_weight
                error = (prediction - y) * sample_weight
                self.weights[0] -= lr * error
                for i, value in enumerate(x, start=1):
                    self.weights[i] -= lr * ((error * value) + (l2 * self.weights[i]))

    def predict_proba(self, x: list[float]) -> float:
        score = self.weights[0]
        for weight, value in zip(self.weights[1:], x):
            score += weight * value
        return _sigmoid(score)


@dataclass
class ChurnArtifacts:
    vectorizer: ChurnVectorizer
    model: LogisticChurnModel
    rows: list[dict[str, str]]
    x_rows: list[list[float]]
    churn_labels: list[int]
    train_indices: list[int]
    test_indices: list[int]
    trained_at: str


def load_bank_rows() -> list[dict[str, str]]:
    with open(DATA_PATH, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def churn_label(row: dict[str, str]) -> int:
    # MVP proxy from bank.csv: no deposit/subscription means not retained.
    return 1 if row.get("deposit") == "no" else 0


def train_churn_model() -> ChurnArtifacts:
    rows = load_bank_rows()
    labels = [churn_label(row) for row in rows]
    train_indices, test_indices = _stratified_split(labels, test_size=0.2, seed=42)
    train_rows = [rows[i] for i in train_indices]

    vectorizer = ChurnVectorizer()
    vectorizer.fit(train_rows)
    x_rows = vectorizer.transform(rows)

    model = LogisticChurnModel(len(vectorizer.feature_names))
    model.fit([x_rows[i] for i in train_indices], [labels[i] for i in train_indices])

    return ChurnArtifacts(
        vectorizer=vectorizer,
        model=model,
        rows=rows,
        x_rows=x_rows,
        churn_labels=labels,
        train_indices=train_indices,
        test_indices=test_indices,
        trained_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def save_artifacts(artifacts: ChurnArtifacts) -> None:
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    with open(MODEL_ARTIFACT_PATH, "wb") as handle:
        pickle.dump(artifacts, handle, protocol=pickle.HIGHEST_PROTOCOL)

    metadata = model_metadata(artifacts)
    with open(METADATA_ARTIFACT_PATH, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    write_metrics_bundle(artifacts)


def load_artifacts() -> ChurnArtifacts | None:
    if not os.path.exists(MODEL_ARTIFACT_PATH):
        return None

    with open(MODEL_ARTIFACT_PATH, "rb") as handle:
        artifacts = pickle.load(handle)

    if not isinstance(artifacts, ChurnArtifacts):
        return None
    return artifacts


@lru_cache(maxsize=1)
def get_artifacts() -> ChurnArtifacts:
    artifacts = load_artifacts()
    if artifacts is not None:
        return artifacts

    artifacts = train_churn_model()
    save_artifacts(artifacts)
    return artifacts


def retrain_churn_model() -> dict[str, Any]:
    get_artifacts.cache_clear()
    artifacts = train_churn_model()
    save_artifacts(artifacts)
    get_artifacts()
    return {
        "metrics": build_metrics_bundle(artifacts),
        "model_metadata": model_metadata(artifacts),
    }


def get_churn_metrics() -> dict[str, Any]:
    artifacts = get_artifacts()
    if os.path.exists(METRICS_JSON_PATH):
        with open(METRICS_JSON_PATH, encoding="utf-8") as handle:
            metrics = json.load(handle)
    else:
        metrics = write_metrics_bundle(artifacts)

    return {
        "metrics": metrics,
        "model_metadata": model_metadata(artifacts),
    }


def score_customer(customer: dict[str, Any]) -> ChurnScoreResponse:
    artifacts = get_artifacts()
    x = artifacts.vectorizer.transform_one(customer)
    probability = artifacts.model.predict_proba(x)
    drivers = top_risk_drivers(artifacts, x)
    return ChurnScoreResponse(
        churn_probability=round(probability, 4),
        retention_probability=round(1 - probability, 4),
        risk_tier=risk_tier(probability),
        should_enter_uplift_model=probability >= 0.45,
        top_risk_drivers=drivers,
    )


def model_metadata(artifacts: ChurnArtifacts) -> dict[str, Any]:
    return {
        "model_type": "stdlib_logistic_churn_mvp",
        "data_path": "backend/data/bank.csv",
        "rows": len(artifacts.rows),
        "train_rows": len(artifacts.train_indices),
        "test_rows": len(artifacts.test_indices),
        "outcome_definition": "churn_proxy = deposit == 'no'",
        "retention_definition": "deposit == 'yes'",
        "excluded_columns": sorted(EXCLUDED_COLUMNS),
        "feature_count": len(artifacts.vectorizer.feature_names),
        "trained_at": artifacts.trained_at,
        "artifact_version": ARTIFACT_VERSION,
        "model_artifact_path": "backend/artifacts/churn/churn_model.pkl",
        "metadata_artifact_path": "backend/artifacts/churn/churn_metadata.json",
        "metrics_json_path": "backend/metrics/churn_model_metrics.json",
        "metrics_report_path": "backend/metrics/churn_model_report.md",
        "high_risk_customers_path": "backend/metrics/high_risk_customers.csv",
        "caution": (
            "bank.csv has no true churn event or future inactivity window; "
            "deposit == 'no' is used as an MVP churn proxy."
        ),
    }


def write_metrics_bundle(artifacts: ChurnArtifacts) -> dict[str, Any]:
    os.makedirs(METRICS_DIR, exist_ok=True)
    metrics = build_metrics_bundle(artifacts)

    with open(METRICS_JSON_PATH, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

    with open(METRICS_REPORT_PATH, "w", encoding="utf-8") as handle:
        handle.write(render_metrics_report(metrics))

    write_high_risk_customers(artifacts, metrics["high_risk_customers"])
    return metrics


def build_metrics_bundle(artifacts: ChurnArtifacts) -> dict[str, Any]:
    train_scores = [artifacts.model.predict_proba(artifacts.x_rows[i]) for i in artifacts.train_indices]
    train_labels = [artifacts.churn_labels[i] for i in artifacts.train_indices]
    test_scores = [artifacts.model.predict_proba(artifacts.x_rows[i]) for i in artifacts.test_indices]
    test_labels = [artifacts.churn_labels[i] for i in artifacts.test_indices]
    threshold = _best_f1_threshold(train_labels, train_scores)
    classification = _classification_metrics(test_labels, test_scores, threshold=threshold)
    all_scores = [artifacts.model.predict_proba(x) for x in artifacts.x_rows]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "model": model_metadata(artifacts),
        "schema_mapping": {
            "features": {
                "numeric": NUMERIC_COLUMNS,
                "categorical": CATEGORICAL_COLUMNS,
                "excluded_for_leakage_or_target": sorted(EXCLUDED_COLUMNS),
            },
            "target": "churn_proxy = deposit == 'no'",
            "positive_class": "customer did not deposit/subscribe",
            "negative_class": "customer deposited/subscribed",
        },
        "dataset": {
            "rows": len(artifacts.rows),
            "train_rows": len(artifacts.train_indices),
            "test_rows": len(artifacts.test_indices),
            "churn_rows": sum(artifacts.churn_labels),
            "retained_rows": len(artifacts.churn_labels) - sum(artifacts.churn_labels),
            "churn_rate": round(statistics.fmean(artifacts.churn_labels), 4),
        },
        "classification_metrics": classification,
        "probability_metrics": {
            "brier_score": round(_brier_score(test_labels, test_scores), 4),
            "score_summary": _summary_stats(test_scores),
            "calibration_by_decile": _calibration_by_decile(test_labels, test_scores),
        },
        "business_metrics": {
            "risk_gate_threshold": threshold,
            "test_rows_entering_uplift_model": classification["predicted_positive"],
            "test_coverage_entering_uplift_model": round(
                classification["predicted_positive"] / max(len(test_labels), 1), 4
            ),
            "recall_at_top_10_percent": round(_recall_at_fraction(test_labels, test_scores, 0.1), 4),
            "recall_at_top_20_percent": round(_recall_at_fraction(test_labels, test_scores, 0.2), 4),
        },
        "lift_deciles": _lift_deciles(test_labels, test_scores),
        "feature_importance": feature_importance(artifacts)[:15],
        "high_risk_customers": high_risk_customers(artifacts, limit=100),
        "caveats": [
            "This MVP uses deposit == 'no' as a churn proxy because bank.csv has no future churn event.",
            "Production churn should be trained on historical snapshots with a future inactivity or closure window.",
            "duration is excluded because it is known only after customer contact starts.",
            "contact is excluded because it is the uplift treatment proxy and should not leak into pre-uplift churn filtering.",
        ],
    }


def top_risk_drivers(artifacts: ChurnArtifacts, x: list[float], limit: int = 5) -> list[str]:
    contributions = []
    for i, (feature, value) in enumerate(zip(artifacts.vectorizer.feature_names, x), start=1):
        contribution = artifacts.model.weights[i] * value
        if contribution > 0:
            contributions.append((feature, contribution))
    contributions.sort(key=lambda item: item[1], reverse=True)
    return [name for name, _ in contributions[:limit]]


def feature_importance(artifacts: ChurnArtifacts) -> list[dict[str, Any]]:
    scores: dict[str, float] = {}
    for feature, weight in zip(artifacts.vectorizer.feature_names, artifacts.model.weights[1:]):
        root = feature.split("=")[0]
        scores[root] = scores.get(root, 0.0) + abs(weight)

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    max_score = ordered[0][1] if ordered else 1.0
    return [
        {"feature": feature, "importance": round(score / max_score, 4)}
        for feature, score in ordered
    ]


def high_risk_customers(artifacts: ChurnArtifacts, limit: int = 100) -> list[dict[str, Any]]:
    scored = []
    for index, row in enumerate(artifacts.rows):
        score = artifacts.model.predict_proba(artifacts.x_rows[index])
        scored.append(
            {
                "rank": 0,
                "customer_id": f"bank_row_{index + 1}",
                "source_row": index + 1,
                "age": _to_int(row.get("age")),
                "balance": round(_to_float(row.get("balance")), 2),
                "housing": row.get("housing", ""),
                "loan": row.get("loan", ""),
                "campaign": _to_int(row.get("campaign")),
                "churn_probability": round(score, 4),
                "retention_probability": round(1 - score, 4),
                "risk_tier": risk_tier(score),
                "actual_churn_proxy": churn_label(row),
                "should_enter_uplift_model": score >= 0.45,
            }
        )

    scored.sort(key=lambda item: item["churn_probability"], reverse=True)
    for rank, row in enumerate(scored[:limit], start=1):
        row["rank"] = rank
    return scored[:limit]


def write_high_risk_customers(artifacts: ChurnArtifacts, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "rank",
        "customer_id",
        "source_row",
        "age",
        "balance",
        "housing",
        "loan",
        "campaign",
        "churn_probability",
        "retention_probability",
        "risk_tier",
        "actual_churn_proxy",
        "should_enter_uplift_model",
    ]
    with open(HIGH_RISK_CSV_PATH, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def risk_tier(probability: float) -> str:
    if probability >= 0.8:
        return "critical"
    if probability >= 0.6:
        return "high"
    if probability >= 0.4:
        return "medium"
    return "low"


def render_metrics_report(metrics: dict[str, Any]) -> str:
    model = metrics["model"]
    data = metrics["dataset"]
    cls = metrics["classification_metrics"]
    prob = metrics["probability_metrics"]
    business = metrics["business_metrics"]

    lines = [
        "# RetentionOS Churn Model Metrics",
        "",
        f"Generated at: `{metrics['generated_at']}`",
        f"Model artifact: `{model['model_artifact_path']}`",
        f"Rows evaluated: `{data['rows']}`",
        "",
        "## Schema Mapping",
        "",
        "- Features: behavioral and demographic Bank Marketing columns available before uplift scoring.",
        "- Target: `churn_proxy = deposit == 'no'`",
        "- Leakage excluded: `contact`, `deposit`, `duration`",
        "",
        "## Classification Metrics",
        "",
        f"- Threshold: `{cls['threshold']}`",
        f"- Precision: `{cls['precision']}`",
        f"- Recall: `{cls['recall']}`",
        f"- F1: `{cls['f1']}`",
        f"- Accuracy: `{cls['accuracy']}`",
        f"- AUC-ROC: `{cls['auc_roc']}`",
        f"- PR-AUC: `{cls['pr_auc']}`",
        f"- Confusion: `{cls['confusion']}`",
        "",
        "## Probability Quality",
        "",
        f"- Brier score: `{prob['brier_score']}`",
        "",
        "## Business Gate",
        "",
        f"- Risk gate threshold: `{business['risk_gate_threshold']}`",
        f"- Test rows entering uplift model: `{business['test_rows_entering_uplift_model']}`",
        f"- Test coverage entering uplift model: `{business['test_coverage_entering_uplift_model']}`",
        f"- Recall at top 10%: `{business['recall_at_top_10_percent']}`",
        f"- Recall at top 20%: `{business['recall_at_top_20_percent']}`",
        "",
        "## Inferences for RetentionOS",
        "",
        "- The churn model is acting as the risk gate in the README flow: `LTV Filtering -> Churn Prediction -> Causal Uplift Modeling -> Treatment Optimization`.",
        "- A high recall score means the model is intentionally broad and catches most customers who match the churn proxy before they reach the uplift model.",
        "- Precision is moderate, so some customers sent to uplift will not truly be risky; this is acceptable for an MVP gate because the uplift and profit guardrail layers make the final intervention decision.",
        "- AUC-ROC above random indicates useful ranking power, but this is not a production-grade BFSI churn model yet.",
        "- The current threshold sends a wide portion of customers into uplift scoring, prioritizing missed-churn avoidance over compute savings.",
        "- `high_risk_customers.csv` should be read as the prioritized risk queue, not as an approved intervention list.",
        "- Customers marked high or critical risk should still pass through the uplift model; only positive uplift and positive expected profit should trigger agentic intervention.",
        "",
        "## Caveats",
        "",
    ]
    lines.extend(f"- {caveat}" for caveat in metrics["caveats"])
    lines.append("")
    return "\n".join(lines)


def _stratified_split(
    labels: list[int],
    *,
    test_size: float,
    seed: int,
) -> tuple[list[int], list[int]]:
    rng = random.Random(seed)
    positive = [index for index, label in enumerate(labels) if label == 1]
    negative = [index for index, label in enumerate(labels) if label == 0]
    rng.shuffle(positive)
    rng.shuffle(negative)

    positive_test = max(1, round(len(positive) * test_size))
    negative_test = max(1, round(len(negative) * test_size))
    test_indices = positive[:positive_test] + negative[:negative_test]
    train_indices = positive[positive_test:] + negative[negative_test:]
    rng.shuffle(train_indices)
    rng.shuffle(test_indices)
    return train_indices, test_indices


def _classification_metrics(
    labels: list[int],
    scores: list[float],
    *,
    threshold: float,
) -> dict[str, Any]:
    predictions = [1 if score >= threshold else 0 for score in scores]
    tp = sum(1 for pred, actual in zip(predictions, labels) if pred == 1 and actual == 1)
    fp = sum(1 for pred, actual in zip(predictions, labels) if pred == 1 and actual == 0)
    fn = sum(1 for pred, actual in zip(predictions, labels) if pred == 0 and actual == 1)
    tn = sum(1 for pred, actual in zip(predictions, labels) if pred == 0 and actual == 0)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 0.000001)
    accuracy = (tp + tn) / max(len(labels), 1)

    return {
        "threshold": round(threshold, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "auc_roc": round(_roc_auc(labels, scores), 4),
        "pr_auc": round(_average_precision(labels, scores), 4),
        "predicted_positive": sum(predictions),
        "predicted_negative": len(predictions) - sum(predictions),
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
    }


def _best_f1_threshold(labels: list[int], scores: list[float]) -> float:
    candidates = [i / 100 for i in range(25, 86)]
    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in candidates:
        metrics = _classification_metrics(labels, scores, threshold=threshold)
        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            best_threshold = threshold
    return best_threshold


def _roc_auc(labels: list[int], scores: list[float]) -> float:
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return 0.0

    ordered = sorted(zip(scores, labels), key=lambda item: item[0])
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


def _average_precision(labels: list[int], scores: list[float]) -> float:
    positives = sum(labels)
    if positives == 0:
        return 0.0

    ordered = sorted(zip(scores, labels), key=lambda item: item[0], reverse=True)
    true_positives = 0
    precision_sum = 0.0
    for rank, (_, label) in enumerate(ordered, start=1):
        if label == 1:
            true_positives += 1
            precision_sum += true_positives / rank
    return precision_sum / positives


def _brier_score(labels: list[int], scores: list[float]) -> float:
    if not labels:
        return 0.0
    return statistics.fmean((score - label) ** 2 for label, score in zip(labels, scores))


def _recall_at_fraction(labels: list[int], scores: list[float], fraction: float) -> float:
    positives = sum(labels)
    if positives == 0:
        return 0.0
    ordered = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)
    n = max(1, round(len(ordered) * fraction))
    captured = sum(labels[index] for index in ordered[:n])
    return captured / positives


def _lift_deciles(labels: list[int], scores: list[float]) -> list[dict[str, float]]:
    ordered = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)
    base_rate = statistics.fmean(labels) if labels else 0.0
    rows = []
    for decile, group in enumerate(_chunks(ordered, 10), start=1):
        churn_rate = statistics.fmean(labels[index] for index in group) if group else 0.0
        lift = churn_rate / base_rate if base_rate else 0.0
        rows.append(
            {
                "decile": float(decile),
                "rows": float(len(group)),
                "mean_score": round(statistics.fmean(scores[index] for index in group), 4),
                "observed_churn_rate": round(churn_rate, 4),
                "lift": round(lift, 4),
            }
        )
    return rows


def _calibration_by_decile(labels: list[int], scores: list[float]) -> list[dict[str, float]]:
    ordered = sorted(range(len(scores)), key=lambda index: scores[index])
    rows = []
    for bucket, group in enumerate(_chunks(ordered, 10), start=1):
        mean_score = statistics.fmean(scores[index] for index in group) if group else 0.0
        observed = statistics.fmean(labels[index] for index in group) if group else 0.0
        rows.append(
            {
                "bin": float(bucket),
                "mean_predicted_churn": round(mean_score, 4),
                "observed_churn_rate": round(observed, 4),
                "absolute_error": round(abs(mean_score - observed), 4),
            }
        )
    return rows


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
