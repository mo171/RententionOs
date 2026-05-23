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

from models.ltv_models import LTVScoreResponse

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "artifacts", "ltv")
MODEL_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "ltv_model.pkl")
METADATA_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "ltv_metadata.json")
METRICS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "metrics")
METRICS_JSON_PATH = os.path.join(METRICS_DIR, "ltv_model_metrics.json")
METRICS_REPORT_PATH = os.path.join(METRICS_DIR, "ltv_model_report.md")
HIGH_VALUE_CSV_PATH = os.path.join(METRICS_DIR, "high_value_customers.csv")
ARTIFACT_VERSION = 1

SEGMENTS = [
    "Student",
    "Low-Income/Jan Dhan",
    "Salaried Middle-Class",
    "MSME/Entrepreneur",
    "HNI",
]
SEGMENT_WEIGHTS = [0.15, 0.25, 0.40, 0.15, 0.05]
NUMERIC_FEATURES = [
    "avg_monthly_income_inr",
    "income_stability_score",
    "avg_monthly_spend_inr",
    "spend_variability",
    "upi_transaction_ratio",
    "cc_transaction_ratio",
    "bureau_score",
    "credit_utilization_ratio",
    "repayment_score",
    "bounce_count_3m",
    "wealth_liquidity_aum_inr",
    "engagement_score",
    "risk_composite_index",
]


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def _safe_expm1(value: float) -> float:
    return max(math.expm1(max(min(value, 24), 0)), 0.0)


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


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _poisson(rng: random.Random, lam: float) -> int:
    limit = math.exp(-lam)
    k = 0
    product = 1.0
    while product > limit:
        k += 1
        product *= rng.random()
    return k - 1


class LTVVectorizer:
    def __init__(self) -> None:
        self.numeric_stats: dict[str, tuple[float, float]] = {}
        self.feature_names: list[str] = []

    def fit(self, rows: list[dict[str, Any]]) -> None:
        for col in NUMERIC_FEATURES:
            values = [_to_float(row.get(col), 0.0) for row in rows]
            mean = statistics.fmean(values)
            stdev = statistics.pstdev(values) or 1.0
            self.numeric_stats[col] = (mean, stdev)

        self.feature_names = (
            [f"segment_tag={segment}" for segment in SEGMENTS]
            + NUMERIC_FEATURES[:]
        )

    def transform_one(self, row: dict[str, Any]) -> list[float]:
        segment = str(row.get("segment_tag", "Salaried Middle-Class"))
        features = [1.0 if segment == value else 0.0 for value in SEGMENTS]
        for col in NUMERIC_FEATURES:
            mean, stdev = self.numeric_stats[col]
            features.append((_to_float(row.get(col), mean) - mean) / stdev)
        return features

    def transform(self, rows: list[dict[str, Any]]) -> list[list[float]]:
        return [self.transform_one(row) for row in rows]


class LinearSGDRegressor:
    def __init__(self, n_features: int) -> None:
        self.weights = [0.0] * (n_features + 1)

    def fit(
        self,
        x_rows: list[list[float]],
        y_values: list[float],
        *,
        epochs: int = 42,
        lr: float = 0.004,
        l2: float = 0.0005,
    ) -> None:
        for _ in range(epochs):
            for x, y in zip(x_rows, y_values):
                prediction = self.predict(x)
                error = prediction - y
                self.weights[0] -= lr * error
                for i, value in enumerate(x, start=1):
                    self.weights[i] -= lr * ((error * value) + (l2 * self.weights[i]))

    def predict(self, x: list[float]) -> float:
        score = self.weights[0]
        for weight, value in zip(self.weights[1:], x):
            score += weight * value
        return score


class LogisticSGDClassifier:
    def __init__(self, n_features: int) -> None:
        self.weights = [0.0] * (n_features + 1)

    def fit(
        self,
        x_rows: list[list[float]],
        y_values: list[int],
        *,
        epochs: int = 36,
        lr: float = 0.035,
        l2: float = 0.001,
    ) -> None:
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
class LTVArtifacts:
    vectorizer: LTVVectorizer
    ltv_model: LinearSGDRegressor
    risk_model: LogisticSGDClassifier
    rows: list[dict[str, Any]]
    x_rows: list[list[float]]
    future_ltv_targets: list[float]
    default_labels: list[int]
    predicted_ltv: list[float]
    default_probabilities: list[float]
    cfvs_scores: list[float]
    train_indices: list[int]
    test_indices: list[int]
    tier_low_cutoff: float
    tier_high_cutoff: float
    normalizer_bounds: dict[str, tuple[float, float]]
    trained_at: str


def generate_indian_banking_dataset(num_records: int = 10000, seed: int = 42) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows = []
    for index in range(num_records):
        segment = rng.choices(SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]
        anchors = _segment_anchors(segment, rng)

        income = rng.uniform(*anchors["income_range"])
        stability = _clamp(rng.gauss(anchors["stability_loc"], anchors["stability_scale"]), 0.01, 1.0)
        spend = income * rng.uniform(0.40, 0.90)
        bureau_score = rng.randint(*anchors["bureau_range"])
        credit_utilization = 0.0 if anchors["cc_ratio"] == 0 else _clamp(rng.betavariate(2, 5), 0.0, 1.0)
        repayment_base = (bureau_score - 300) / 600.0
        repayment_score = _clamp(repayment_base - rng.uniform(-0.1, 0.15), 0.0, 1.0)
        app_logins = _poisson(rng, 12 if segment in {"Student", "Salaried Middle-Class"} else 5)
        products = rng.randint(1, 3) if segment in {"Student", "Low-Income/Jan Dhan"} else rng.randint(3, 7)
        bounce_count = rng.choices([0, 1, 2, 3], weights=[0.88, 0.08, 0.03, 0.01], k=1)[0]
        if repayment_score < 0.5:
            bounce_count += rng.randint(1, 2)

        is_fraudster = 1 if rng.random() < 0.004 else 0
        fee_income = (spend * anchors["cc_ratio"] * 0.018) + rng.uniform(100, 1500)
        servicing_cost = rng.uniform(150, 600)

        rows.append(
            {
                "customer_id": f"synthetic_bank_customer_{index + 1}",
                "segment_tag": segment,
                "aa_consent_linked": bool(rng.randint(0, 1)),
                "avg_monthly_income_inr": round(income, 2),
                "income_stability_score": round(stability, 4),
                "avg_monthly_spend_inr": round(spend, 2),
                "spend_variability": round(rng.uniform(0.05, 0.45), 4),
                "upi_transaction_ratio": round(anchors["upi_ratio"], 4),
                "cc_transaction_ratio": round(anchors["cc_ratio"], 4),
                "bureau_score": bureau_score,
                "credit_utilization_ratio": round(credit_utilization, 4),
                "repayment_score": round(repayment_score, 4),
                "bounce_count_3m": bounce_count,
                "wealth_liquidity_aum_inr": round(anchors["aum_base"], 2),
                "app_logins_30d": app_logins,
                "distinct_products_used": products,
                "loan_interest_paid_12m": round(anchors["loan_interest_paid"], 2),
                "fee_income_earned_12m": round(fee_income, 2),
                "servicing_cost_12m": round(servicing_cost, 2),
                "is_fraudster": is_fraudster,
            }
        )
    return rows


def _segment_anchors(segment: str, rng: random.Random) -> dict[str, Any]:
    if segment == "Student":
        return {
            "income_range": (5000, 25000),
            "stability_loc": 0.4,
            "stability_scale": 0.15,
            "bureau_range": (300, 650),
            "upi_ratio": rng.uniform(0.70, 0.95),
            "cc_ratio": rng.uniform(0.00, 0.05),
            "aum_base": rng.uniform(1000, 15000),
            "loan_interest_paid": 0.0,
        }
    if segment == "Low-Income/Jan Dhan":
        return {
            "income_range": (8000, 35000),
            "stability_loc": 0.5,
            "stability_scale": 0.2,
            "bureau_range": (450, 700),
            "upi_ratio": rng.uniform(0.50, 0.85),
            "cc_ratio": 0.0,
            "aum_base": rng.uniform(500, 8000),
            "loan_interest_paid": rng.uniform(0, 1200),
        }
    if segment == "Salaried Middle-Class":
        return {
            "income_range": (40000, 180000),
            "stability_loc": 0.9,
            "stability_scale": 0.05,
            "bureau_range": (680, 850),
            "upi_ratio": rng.uniform(0.30, 0.60),
            "cc_ratio": rng.uniform(0.20, 0.50),
            "aum_base": rng.uniform(50000, 600000),
            "loan_interest_paid": rng.uniform(15000, 120000),
        }
    if segment == "MSME/Entrepreneur":
        return {
            "income_range": (60000, 500000),
            "stability_loc": 0.6,
            "stability_scale": 0.25,
            "bureau_range": (600, 820),
            "upi_ratio": rng.uniform(0.40, 0.70),
            "cc_ratio": rng.uniform(0.10, 0.40),
            "aum_base": rng.uniform(100000, 1500000),
            "loan_interest_paid": rng.uniform(50000, 350000),
        }
    return {
        "income_range": (600000, 5000000),
        "stability_loc": 0.85,
        "stability_scale": 0.1,
        "bureau_range": (750, 900),
        "upi_ratio": rng.uniform(0.10, 0.30),
        "cc_ratio": rng.uniform(0.50, 0.80),
        "aum_base": rng.uniform(2500000, 40000000),
        "loan_interest_paid": rng.uniform(100000, 800000),
    }


def execute_feature_engineering(rows: list[dict[str, Any]], seed: int = 42) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    engineered = []
    for row in rows:
        item = dict(row)
        item["ltv_historical_12m"] = (
            _to_float(item["loan_interest_paid_12m"])
            + _to_float(item["fee_income_earned_12m"])
            - _to_float(item["servicing_cost_12m"])
        )
        item["risk_composite_index"] = (
            (1.0 - _to_float(item["repayment_score"])) * 0.40
            + (_to_float(item["bounce_count_3m"]) / 5.0) * 0.40
            + _to_float(item["credit_utilization_ratio"]) * 0.20
        )
        item["engagement_score"] = _clamp(
            (_to_float(item["app_logins_30d"]) / 35.0) * 0.50
            + (_to_float(item["distinct_products_used"]) / 7.0) * 0.50,
            0.0,
            1.0,
        )
        item["target_future_ltv_12m"] = max(
            item["ltv_historical_12m"] * rng.gauss(1.08, 0.05),
            0.0,
        )
        item["target_default_risk"] = 1 if (
            (_to_float(item["repayment_score"]) < 0.45 and _to_int(item["bounce_count_3m"]) >= 2)
            or _to_int(item["is_fraudster"]) == 1
        ) else 0
        engineered.append(item)
    return engineered


def train_ltv_model(num_records: int = 10000) -> LTVArtifacts:
    rows = execute_feature_engineering(generate_indian_banking_dataset(num_records))
    targets = [_to_float(row["target_future_ltv_12m"]) for row in rows]
    default_labels = [_to_int(row["target_default_risk"]) for row in rows]
    train_indices, test_indices = _split_indices(len(rows), test_size=0.2, seed=42)

    vectorizer = LTVVectorizer()
    vectorizer.fit([rows[i] for i in train_indices])
    x_rows = vectorizer.transform(rows)
    y_log = [math.log1p(max(target, 0.0)) for target in targets]

    ltv_model = LinearSGDRegressor(len(vectorizer.feature_names))
    ltv_model.fit([x_rows[i] for i in train_indices], [y_log[i] for i in train_indices])

    risk_model = LogisticSGDClassifier(len(vectorizer.feature_names))
    risk_model.fit([x_rows[i] for i in train_indices], [default_labels[i] for i in train_indices])

    predicted_ltv = [_safe_expm1(ltv_model.predict(x)) for x in x_rows]
    default_probabilities = [risk_model.predict_proba(x) for x in x_rows]
    normalizer_bounds = _normalizer_bounds(rows, predicted_ltv)
    cfvs_scores = [
        compute_cfvs_score(row, predicted_ltv[i], default_probabilities[i], normalizer_bounds)
        for i, row in enumerate(rows)
    ]
    positive_scores = [score for score in cfvs_scores if score > 0]
    tier_low_cutoff = _quantile(sorted(positive_scores), 0.35) if positive_scores else 0.0
    tier_high_cutoff = _quantile(sorted(positive_scores), 0.75) if positive_scores else 0.0

    return LTVArtifacts(
        vectorizer=vectorizer,
        ltv_model=ltv_model,
        risk_model=risk_model,
        rows=rows,
        x_rows=x_rows,
        future_ltv_targets=targets,
        default_labels=default_labels,
        predicted_ltv=predicted_ltv,
        default_probabilities=default_probabilities,
        cfvs_scores=cfvs_scores,
        train_indices=train_indices,
        test_indices=test_indices,
        tier_low_cutoff=tier_low_cutoff,
        tier_high_cutoff=tier_high_cutoff,
        normalizer_bounds=normalizer_bounds,
        trained_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def save_artifacts(artifacts: LTVArtifacts) -> None:
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    with open(MODEL_ARTIFACT_PATH, "wb") as handle:
        pickle.dump(artifacts, handle, protocol=pickle.HIGHEST_PROTOCOL)

    metadata = model_metadata(artifacts)
    with open(METADATA_ARTIFACT_PATH, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    write_metrics_bundle(artifacts)


def load_artifacts() -> LTVArtifacts | None:
    if not os.path.exists(MODEL_ARTIFACT_PATH):
        return None

    with open(MODEL_ARTIFACT_PATH, "rb") as handle:
        artifacts = pickle.load(handle)
    if not isinstance(artifacts, LTVArtifacts):
        return None
    return artifacts


@lru_cache(maxsize=1)
def get_artifacts() -> LTVArtifacts:
    artifacts = load_artifacts()
    if artifacts is not None:
        return artifacts

    artifacts = train_ltv_model()
    save_artifacts(artifacts)
    return artifacts


def retrain_ltv_model() -> dict[str, Any]:
    get_artifacts.cache_clear()
    artifacts = train_ltv_model()
    save_artifacts(artifacts)
    get_artifacts()
    return {"metrics": build_metrics_bundle(artifacts), "model_metadata": model_metadata(artifacts)}


def get_ltv_metrics() -> dict[str, Any]:
    artifacts = get_artifacts()
    if os.path.exists(METRICS_JSON_PATH):
        with open(METRICS_JSON_PATH, encoding="utf-8") as handle:
            metrics = json.load(handle)
    else:
        metrics = write_metrics_bundle(artifacts)
    return {"metrics": metrics, "model_metadata": model_metadata(artifacts)}


def score_customer(customer: dict[str, Any]) -> LTVScoreResponse:
    artifacts = get_artifacts()
    prepared = prepare_customer_features(customer)
    x = artifacts.vectorizer.transform_one(prepared)
    predicted_ltv = _safe_expm1(artifacts.ltv_model.predict(x))
    default_probability = artifacts.risk_model.predict_proba(x)
    cfvs = compute_cfvs_score(
        prepared,
        predicted_ltv,
        default_probability,
        artifacts.normalizer_bounds,
    )
    tier = ltv_tier(cfvs, artifacts.tier_low_cutoff, artifacts.tier_high_cutoff, default_probability)

    return LTVScoreResponse(
        historical_ltv_12m=round(_to_float(prepared["ltv_historical_12m"]), 2),
        predicted_ltv_12m=round(predicted_ltv, 2),
        default_risk_probability=round(default_probability, 4),
        cfvs=round(cfvs, 2),
        ltv_tier=tier,
        eligible_for_churn_scoring=tier in {"medium", "high", "premium"},
        recommended_action=recommended_action(cfvs, default_probability, artifacts.tier_low_cutoff, artifacts.tier_high_cutoff),
        top_value_drivers=top_value_drivers(prepared),
        top_risk_drivers=top_risk_drivers(prepared, default_probability),
    )


def prepare_customer_features(customer: dict[str, Any]) -> dict[str, Any]:
    row = dict(customer)
    segment = str(row.get("segment_tag", "Salaried Middle-Class"))
    row["segment_tag"] = segment if segment in SEGMENTS else "Salaried Middle-Class"
    row["avg_monthly_income_inr"] = _to_float(row.get("avg_monthly_income_inr"), 45000.0)
    row["avg_monthly_spend_inr"] = _to_float(
        row.get("avg_monthly_spend_inr"),
        row["avg_monthly_income_inr"] * 0.55,
    )
    row["bureau_score"] = _to_int(row.get("bureau_score"), 720)
    row["bounce_count_3m"] = _to_int(row.get("bounce_count_3m"), 0)
    row["wealth_liquidity_aum_inr"] = _to_float(row.get("wealth_liquidity_aum_inr"), 35000.0)
    row["app_logins_30d"] = _to_int(row.get("app_logins_30d"), 10)
    row["distinct_products_used"] = _to_int(row.get("distinct_products_used"), 3)
    row["income_stability_score"] = _to_float(
        row.get("income_stability_score"),
        0.90 if row["segment_tag"] == "Salaried Middle-Class" else 0.60,
    )
    row["upi_transaction_ratio"] = _to_float(
        row.get("upi_transaction_ratio"),
        0.80 if row["segment_tag"] in {"Student", "Low-Income/Jan Dhan"} else 0.40,
    )
    row["cc_transaction_ratio"] = _to_float(
        row.get("cc_transaction_ratio"),
        0.0 if row["segment_tag"] == "Low-Income/Jan Dhan" else 0.30,
    )
    row["credit_utilization_ratio"] = _to_float(
        row.get("credit_utilization_ratio"),
        0.35 if row["cc_transaction_ratio"] > 0 else 0.0,
    )
    row["spend_variability"] = _to_float(row.get("spend_variability"), 0.15)
    row["repayment_score"] = _to_float(
        row.get("repayment_score"),
        _clamp((row["bureau_score"] - 300) / 600.0 - (row["bounce_count_3m"] * 0.15), 0.0, 1.0),
    )
    row["loan_interest_paid_12m"] = _to_float(
        row.get("loan_interest_paid_12m"),
        row["avg_monthly_income_inr"] * 0.12,
    )
    row["fee_income_earned_12m"] = _to_float(
        row.get("fee_income_earned_12m"),
        row["avg_monthly_spend_inr"] * row["cc_transaction_ratio"] * 0.018 + 500.0,
    )
    row["servicing_cost_12m"] = _to_float(row.get("servicing_cost_12m"), 350.0)
    row["is_fraudster"] = _to_int(row.get("is_fraudster"), 0)
    return execute_feature_engineering([row])[0]


def compute_cfvs_score(
    row: dict[str, Any],
    predicted_ltv: float,
    default_probability: float,
    bounds: dict[str, tuple[float, float]],
) -> float:
    if _to_int(row.get("is_fraudster")) == 1 or _to_int(row.get("bounce_count_3m")) > 3 or _to_int(row.get("bureau_score")) < 500:
        return 0.0

    weights = _segment_score_weights(str(row.get("segment_tag")))
    norm_hist = _scale_log(_to_float(row.get("ltv_historical_12m")), bounds["historical_ltv"])
    norm_pred = _scale_log(predicted_ltv, bounds["predicted_ltv"])
    norm_engagement = _clamp(_to_float(row.get("engagement_score")) * 100, 0.0, 100.0)
    base_value = (
        weights["w_h"] * norm_hist
        + weights["w_p"] * norm_pred
        + weights["w_b"] * norm_engagement
    )
    final_score = base_value * (1.0 - (weights["w_r"] * default_probability))
    return _clamp(final_score, 0.0, 100.0)


def _segment_score_weights(segment: str) -> dict[str, float]:
    return {
        "Low-Income/Jan Dhan": {"w_h": 0.10, "w_p": 0.20, "w_b": 0.40, "w_r": 0.30},
        "Student": {"w_h": 0.05, "w_p": 0.55, "w_b": 0.25, "w_r": 0.15},
        "Salaried Middle-Class": {"w_h": 0.30, "w_p": 0.30, "w_b": 0.20, "w_r": 0.20},
        "MSME/Entrepreneur": {"w_h": 0.35, "w_p": 0.25, "w_b": 0.15, "w_r": 0.25},
        "HNI": {"w_h": 0.50, "w_p": 0.30, "w_b": 0.10, "w_r": 0.10},
    }.get(segment, {"w_h": 0.30, "w_p": 0.30, "w_b": 0.20, "w_r": 0.20})


def ltv_tier(cfvs: float, low_cutoff: float, high_cutoff: float, default_probability: float) -> str:
    if cfvs == 0.0 or default_probability > 0.65:
        return "ineligible"
    if cfvs >= high_cutoff + 10:
        return "premium"
    if cfvs >= high_cutoff:
        return "high"
    if cfvs >= low_cutoff:
        return "medium"
    return "low"


def recommended_action(cfvs: float, default_probability: float, low_cutoff: float, high_cutoff: float) -> str:
    if cfvs == 0.0 or default_probability > 0.65:
        return "critical_risk_freeze"
    if cfvs >= high_cutoff:
        return "priority_ltv_gate_pass"
    if cfvs >= low_cutoff:
        return "standard_ltv_gate_pass"
    return "do_not_route_to_churn_model"


def model_metadata(artifacts: LTVArtifacts) -> dict[str, Any]:
    return {
        "model_type": "stdlib_ltv_cfvs_mvp",
        "source_prototype": "backend/models/LTV.py",
        "rows": len(artifacts.rows),
        "train_rows": len(artifacts.train_indices),
        "test_rows": len(artifacts.test_indices),
        "historical_ltv_formula": "loan_interest_paid_12m + fee_income_earned_12m - servicing_cost_12m",
        "future_ltv_target": "ltv_historical_12m * synthetic trend factor",
        "score": "CFVS = segment-weighted historical LTV + predicted LTV + engagement, penalized by default risk",
        "tier_low_cutoff": round(artifacts.tier_low_cutoff, 4),
        "tier_high_cutoff": round(artifacts.tier_high_cutoff, 4),
        "trained_at": artifacts.trained_at,
        "artifact_version": ARTIFACT_VERSION,
        "model_artifact_path": "backend/artifacts/ltv/ltv_model.pkl",
        "metadata_artifact_path": "backend/artifacts/ltv/ltv_metadata.json",
        "metrics_json_path": "backend/metrics/ltv_model_metrics.json",
        "metrics_report_path": "backend/metrics/ltv_model_report.md",
        "high_value_customers_path": "backend/metrics/high_value_customers.csv",
        "caution": "The current LTV MVP trains on synthetic Indian banking data from the prototype until production transaction history is available.",
    }


def write_metrics_bundle(artifacts: LTVArtifacts) -> dict[str, Any]:
    os.makedirs(METRICS_DIR, exist_ok=True)
    metrics = build_metrics_bundle(artifacts)
    with open(METRICS_JSON_PATH, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    with open(METRICS_REPORT_PATH, "w", encoding="utf-8") as handle:
        handle.write(render_metrics_report(metrics))
    write_high_value_customers(metrics["high_value_customers"])
    return metrics


def build_metrics_bundle(artifacts: LTVArtifacts) -> dict[str, Any]:
    test = artifacts.test_indices
    y_true = [artifacts.future_ltv_targets[i] for i in test]
    y_pred = [artifacts.predicted_ltv[i] for i in test]
    risk_true = [artifacts.default_labels[i] for i in test]
    risk_score = [artifacts.default_probabilities[i] for i in test]
    cfvs = [artifacts.cfvs_scores[i] for i in test]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "model": model_metadata(artifacts),
        "schema_mapping": {
            "features": NUMERIC_FEATURES + ["segment_tag"],
            "historical_ltv": "loan_interest_paid_12m + fee_income_earned_12m - servicing_cost_12m",
            "future_ltv_target": "target_future_ltv_12m",
            "risk_target": "target_default_risk",
            "score_output": "CFVS",
        },
        "dataset": {
            "rows": len(artifacts.rows),
            "train_rows": len(artifacts.train_indices),
            "test_rows": len(artifacts.test_indices),
            "default_rate": round(statistics.fmean(artifacts.default_labels), 4),
            "mean_historical_ltv": round(statistics.fmean(_to_float(row["ltv_historical_12m"]) for row in artifacts.rows), 2),
            "mean_future_ltv_target": round(statistics.fmean(artifacts.future_ltv_targets), 2),
        },
        "future_ltv_regression_metrics": _regression_metrics(y_true, y_pred),
        "default_risk_metrics": _classification_metrics(risk_true, risk_score, threshold=0.5),
        "cfvs_distribution": _summary_stats(cfvs),
        "tier_thresholds": {
            "low_cutoff": round(artifacts.tier_low_cutoff, 4),
            "high_cutoff": round(artifacts.tier_high_cutoff, 4),
        },
        "ltv_gate": _gate_summary(artifacts),
        "feature_importance": feature_importance(artifacts)[:15],
        "high_value_customers": high_value_customers(artifacts, limit=100),
        "inferences": [
            "The LTV model is the first financial eligibility gate in the README flow before churn and uplift scoring.",
            "CFVS combines historical customer value, predicted future value, engagement, and default-risk penalty.",
            "Customers below the dynamic CFVS cutoff should not consume churn/uplift capacity in the MVP pipeline.",
            "Customers in high or premium tiers are the best candidates for churn risk scoring and later causal uplift checks.",
            "The current artifact is trained on synthetic Indian banking data from backend/models/LTV.py, not production ledger history.",
        ],
        "caveats": [
            "This is an MVP integration of the notebook prototype, with stdlib models replacing notebook-only LightGBM/XGBoost/SHAP runtime dependencies.",
            "Production LTV should train on real transaction, balance, fee, product, and servicing-cost history.",
            "Synthetic CFVS thresholds are population-relative and should be recalibrated when real customer data arrives.",
        ],
    }


def _regression_metrics(y_true: list[float], y_pred: list[float]) -> dict[str, float]:
    errors = [pred - true for true, pred in zip(y_true, y_pred)]
    mae = statistics.fmean(abs(error) for error in errors) if errors else 0.0
    rmse = math.sqrt(statistics.fmean(error * error for error in errors)) if errors else 0.0
    mean_true = statistics.fmean(y_true) if y_true else 0.0
    ss_res = sum((true - pred) ** 2 for true, pred in zip(y_true, y_pred))
    ss_tot = sum((true - mean_true) ** 2 for true in y_true)
    r2 = 1 - (ss_res / ss_tot) if ss_tot else 0.0
    return {"mae": round(mae, 2), "rmse": round(rmse, 2), "r2": round(r2, 4)}


def _classification_metrics(labels: list[int], scores: list[float], *, threshold: float) -> dict[str, Any]:
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
        "threshold": threshold,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "auc_roc": round(_roc_auc(labels, scores), 4),
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
    }


def _gate_summary(artifacts: LTVArtifacts) -> dict[str, Any]:
    eligible = [
        score > 0 and score >= artifacts.tier_low_cutoff and artifacts.default_probabilities[i] <= 0.65
        for i, score in enumerate(artifacts.cfvs_scores)
    ]
    return {
        "eligible_rows": sum(eligible),
        "eligible_rate": round(sum(eligible) / max(len(eligible), 1), 4),
        "priority_rows": sum(
            score >= artifacts.tier_high_cutoff and artifacts.default_probabilities[i] <= 0.65
            for i, score in enumerate(artifacts.cfvs_scores)
        ),
        "purpose": "Filter financially valuable customers before churn and uplift scoring.",
    }


def high_value_customers(artifacts: LTVArtifacts, limit: int) -> list[dict[str, Any]]:
    rows = []
    for i, source in enumerate(artifacts.rows):
        tier = ltv_tier(
            artifacts.cfvs_scores[i],
            artifacts.tier_low_cutoff,
            artifacts.tier_high_cutoff,
            artifacts.default_probabilities[i],
        )
        rows.append(
            {
                "rank": 0,
                "customer_id": source["customer_id"],
                "segment_tag": source["segment_tag"],
                "historical_ltv_12m": round(_to_float(source["ltv_historical_12m"]), 2),
                "predicted_ltv_12m": round(artifacts.predicted_ltv[i], 2),
                "default_risk_probability": round(artifacts.default_probabilities[i], 4),
                "cfvs": round(artifacts.cfvs_scores[i], 2),
                "ltv_tier": tier,
                "eligible_for_churn_scoring": tier in {"medium", "high", "premium"},
                "recommended_action": recommended_action(
                    artifacts.cfvs_scores[i],
                    artifacts.default_probabilities[i],
                    artifacts.tier_low_cutoff,
                    artifacts.tier_high_cutoff,
                ),
            }
        )
    rows.sort(key=lambda item: item["cfvs"], reverse=True)
    for rank, row in enumerate(rows[:limit], start=1):
        row["rank"] = rank
    return rows[:limit]


def write_high_value_customers(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "rank",
        "customer_id",
        "segment_tag",
        "historical_ltv_12m",
        "predicted_ltv_12m",
        "default_risk_probability",
        "cfvs",
        "ltv_tier",
        "eligible_for_churn_scoring",
        "recommended_action",
    ]
    with open(HIGH_VALUE_CSV_PATH, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def render_metrics_report(metrics: dict[str, Any]) -> str:
    regression = metrics["future_ltv_regression_metrics"]
    risk = metrics["default_risk_metrics"]
    gate = metrics["ltv_gate"]
    model = metrics["model"]
    data = metrics["dataset"]
    tiers = metrics["tier_thresholds"]
    lines = [
        "# RetentionOS LTV Model Metrics",
        "",
        f"Generated at: `{metrics['generated_at']}`",
        f"Model artifact: `{model['model_artifact_path']}`",
        f"Rows evaluated: `{data['rows']}`",
        "",
        "## Algorithm",
        "",
        "- Historical LTV = `loan_interest_paid_12m + fee_income_earned_12m - servicing_cost_12m`.",
        "- Future LTV is predicted from segment, income, spend, credit, liquidity, engagement, and risk signals.",
        "- Default risk is predicted separately and penalizes the final customer value score.",
        "- CFVS is a 0-100 customer financial value score used as the first RetentionOS eligibility gate.",
        "",
        "## Future LTV Regression",
        "",
        f"- MAE: `{regression['mae']}`",
        f"- RMSE: `{regression['rmse']}`",
        f"- R2: `{regression['r2']}`",
        "",
        "## Default Risk Metrics",
        "",
        f"- Precision: `{risk['precision']}`",
        f"- Recall: `{risk['recall']}`",
        f"- F1: `{risk['f1']}`",
        f"- AUC-ROC: `{risk['auc_roc']}`",
        f"- Confusion: `{risk['confusion']}`",
        "",
        "## LTV Gate",
        "",
        f"- Low cutoff: `{tiers['low_cutoff']}`",
        f"- High cutoff: `{tiers['high_cutoff']}`",
        f"- Eligible rows: `{gate['eligible_rows']}`",
        f"- Eligible rate: `{gate['eligible_rate']}`",
        f"- Priority rows: `{gate['priority_rows']}`",
        "",
        "## Inferences for RetentionOS",
        "",
    ]
    lines.extend(f"- {item}" for item in metrics["inferences"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in metrics["caveats"])
    lines.append("")
    return "\n".join(lines)


def feature_importance(artifacts: LTVArtifacts) -> list[dict[str, Any]]:
    scores: dict[str, float] = {}
    for feature, weight in zip(artifacts.vectorizer.feature_names, artifacts.ltv_model.weights[1:]):
        root = feature.split("=")[0]
        scores[root] = scores.get(root, 0.0) + abs(weight)
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    max_score = ordered[0][1] if ordered else 1.0
    return [{"feature": name, "importance": round(score / max_score, 4)} for name, score in ordered]


def top_value_drivers(row: dict[str, Any]) -> list[str]:
    candidates = [
        ("wealth_liquidity_aum_inr", _to_float(row.get("wealth_liquidity_aum_inr"))),
        ("ltv_historical_12m", _to_float(row.get("ltv_historical_12m"))),
        ("avg_monthly_income_inr", _to_float(row.get("avg_monthly_income_inr"))),
        ("engagement_score", _to_float(row.get("engagement_score")) * 100000),
        ("distinct_products_used", _to_float(row.get("distinct_products_used")) * 50000),
    ]
    return [name for name, _ in sorted(candidates, key=lambda item: item[1], reverse=True)[:3]]


def top_risk_drivers(row: dict[str, Any], default_probability: float) -> list[str]:
    drivers = []
    if _to_int(row.get("bureau_score")) < 650:
        drivers.append("bureau_score")
    if _to_int(row.get("bounce_count_3m")) > 0:
        drivers.append("bounce_count_3m")
    if _to_float(row.get("repayment_score")) < 0.55:
        drivers.append("repayment_score")
    if _to_float(row.get("risk_composite_index")) > 0.35:
        drivers.append("risk_composite_index")
    if default_probability > 0.5:
        drivers.append("probability_of_default")
    return drivers[:5] or ["no_material_risk_driver"]


def _normalizer_bounds(rows: list[dict[str, Any]], predicted_ltv: list[float]) -> dict[str, tuple[float, float]]:
    historical = [math.log1p(max(_to_float(row.get("ltv_historical_12m")), 0.0)) for row in rows]
    predicted = [math.log1p(max(value, 0.0)) for value in predicted_ltv]
    return {
        "historical_ltv": (min(historical), max(historical)),
        "predicted_ltv": (min(predicted), max(predicted)),
    }


def _scale_log(value: float, bounds: tuple[float, float]) -> float:
    low, high = bounds
    if high <= low:
        return 0.0
    logged = math.log1p(max(value, 0.0))
    return _clamp(((logged - low) / (high - low)) * 100, 0.0, 100.0)


def _split_indices(size: int, *, test_size: float, seed: int) -> tuple[list[int], list[int]]:
    rng = random.Random(seed)
    indices = list(range(size))
    rng.shuffle(indices)
    test_count = max(1, round(size * test_size))
    return indices[test_count:], indices[:test_count]


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

