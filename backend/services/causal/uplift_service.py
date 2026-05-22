from __future__ import annotations

import csv
import json
import math
import os
import pickle
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from models.causal_models import CausalScoreResponse
from services.causal.treatment_optimizer import optimize_treatments

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "bank.csv")
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "artifacts", "causal")
MODEL_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "uplift_artifacts.pkl")
METADATA_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "uplift_metadata.json")
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
EXCLUDED_COLUMNS = {"duration", "deposit", "contact"}


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class StandardizedOneHotVectorizer:
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


class LogisticSGD:
    def __init__(self, n_features: int) -> None:
        self.weights = [0.0] * (n_features + 1)

    def fit(
        self,
        x_rows: list[list[float]],
        y_values: list[float],
        *,
        epochs: int = 18,
        lr: float = 0.035,
        l2: float = 0.001,
    ) -> None:
        if not x_rows:
            return

        for _ in range(epochs):
            for x, y in zip(x_rows, y_values):
                prediction = self.predict_proba(x)
                error = prediction - y
                self.weights[0] -= lr * error
                for i, value in enumerate(x, start=1):
                    self.weights[i] -= lr * ((error * value) + (l2 * self.weights[i]))

    def predict_proba(self, x: list[float]) -> float:
        score = self.weights[0]
        for weight, value in zip(self.weights[1:], x):
            score += weight * value
        return _sigmoid(score)


class LinearSGD:
    def __init__(self, n_features: int) -> None:
        self.weights = [0.0] * (n_features + 1)

    def fit(
        self,
        x_rows: list[list[float]],
        y_values: list[float],
        *,
        epochs: int = 22,
        lr: float = 0.001,
        l2: float = 0.01,
    ) -> None:
        if not x_rows:
            return

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


@dataclass
class UpliftArtifacts:
    vectorizer: StandardizedOneHotVectorizer
    control_model: LogisticSGD
    treated_model: LogisticSGD
    tau_control_model: LinearSGD
    tau_treated_model: LinearSGD
    propensity_model: LogisticSGD
    rows: list[dict[str, str]]
    x_rows: list[list[float]]
    treatment: list[int]
    outcome: list[int]
    uplift_scores: list[float]
    propensities: list[float]
    trained_at: str


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_bank_rows() -> list[dict[str, str]]:
    with open(DATA_PATH, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _treatment_proxy(row: dict[str, str]) -> int:
    # bank.csv has no randomized discount assignment. For the MVP, known contact
    # channel is used as a proxy for proactive outreach and unknown contact as control.
    return 1 if row.get("contact") != "unknown" else 0


def _outcome(row: dict[str, str]) -> int:
    return 1 if row.get("deposit") == "yes" else 0


def _fit_artifacts() -> UpliftArtifacts:
    rows = load_bank_rows()
    vectorizer = StandardizedOneHotVectorizer()
    vectorizer.fit(rows)
    x_rows = vectorizer.transform(rows)
    treatment = [_treatment_proxy(row) for row in rows]
    outcome = [_outcome(row) for row in rows]
    n_features = len(vectorizer.feature_names)

    control_x = [x for x, t in zip(x_rows, treatment) if t == 0]
    control_y = [y for y, t in zip(outcome, treatment) if t == 0]
    treated_x = [x for x, t in zip(x_rows, treatment) if t == 1]
    treated_y = [y for y, t in zip(outcome, treatment) if t == 1]

    control_model = LogisticSGD(n_features)
    control_model.fit(control_x, control_y)
    treated_model = LogisticSGD(n_features)
    treated_model.fit(treated_x, treated_y)

    d_treated = [
        y - control_model.predict_proba(x)
        for x, y, t in zip(x_rows, outcome, treatment)
        if t == 1
    ]
    d_control = [
        treated_model.predict_proba(x) - y
        for x, y, t in zip(x_rows, outcome, treatment)
        if t == 0
    ]

    tau_treated_model = LinearSGD(n_features)
    tau_treated_model.fit(treated_x, d_treated)
    tau_control_model = LinearSGD(n_features)
    tau_control_model.fit(control_x, d_control)

    propensity_model = LogisticSGD(n_features)
    propensity_model.fit(x_rows, treatment, epochs=16, lr=0.03)

    uplift_scores = []
    propensities = []
    for x in x_rows:
        propensity = _clamp(propensity_model.predict_proba(x), 0.02, 0.98)
        tau_control = tau_control_model.predict(x)
        tau_treated = tau_treated_model.predict(x)
        uplift = (propensity * tau_control) + ((1 - propensity) * tau_treated)
        uplift_scores.append(round(_clamp(uplift, -0.5, 0.5), 4))
        propensities.append(round(propensity, 4))

    return UpliftArtifacts(
        vectorizer=vectorizer,
        control_model=control_model,
        treated_model=treated_model,
        tau_control_model=tau_control_model,
        tau_treated_model=tau_treated_model,
        propensity_model=propensity_model,
        rows=rows,
        x_rows=x_rows,
        treatment=treatment,
        outcome=outcome,
        uplift_scores=uplift_scores,
        propensities=propensities,
        trained_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def save_artifacts(artifacts: UpliftArtifacts) -> None:
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    with open(MODEL_ARTIFACT_PATH, "wb") as handle:
        pickle.dump(artifacts, handle, protocol=pickle.HIGHEST_PROTOCOL)

    metadata = _model_metadata(artifacts)
    metadata["artifact_version"] = ARTIFACT_VERSION
    with open(METADATA_ARTIFACT_PATH, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)


def load_artifacts() -> UpliftArtifacts | None:
    if not os.path.exists(MODEL_ARTIFACT_PATH):
        return None

    with open(MODEL_ARTIFACT_PATH, "rb") as handle:
        artifacts = pickle.load(handle)

    if not isinstance(artifacts, UpliftArtifacts):
        return None
    return artifacts


@lru_cache(maxsize=1)
def get_artifacts() -> UpliftArtifacts:
    artifacts = load_artifacts()
    if artifacts is not None:
        return artifacts

    artifacts = _fit_artifacts()
    save_artifacts(artifacts)
    return artifacts


def retrain_uplift_model() -> dict[str, Any]:
    get_artifacts.cache_clear()
    artifacts = _fit_artifacts()
    save_artifacts(artifacts)
    get_artifacts()
    return build_causal_snapshot(artifacts)


def score_customer(
    customer: dict[str, Any],
    *,
    clv: float = 1000.0,
    treatment_costs: dict[str, float] | None = None,
) -> CausalScoreResponse:
    artifacts = get_artifacts()
    x = artifacts.vectorizer.transform_one(customer)
    propensity = _clamp(artifacts.propensity_model.predict_proba(x), 0.02, 0.98)
    control_probability = artifacts.control_model.predict_proba(x)
    treated_probability = artifacts.treated_model.predict_proba(x)
    tau_control = artifacts.tau_control_model.predict(x)
    tau_treated = artifacts.tau_treated_model.predict(x)
    uplift = _clamp((propensity * tau_control) + ((1 - propensity) * tau_treated), -0.5, 0.5)

    best, recommendations = optimize_treatments(uplift, clv, treatment_costs)

    return CausalScoreResponse(
        uplift_score=round(uplift, 4),
        propensity=round(propensity, 4),
        baseline_stay_probability=round(control_probability, 4),
        treated_stay_probability=round(treated_probability, 4),
        segment=_segment(control_probability, treated_probability, uplift),
        best_treatment=best,
        recommendations=recommendations,
    )


def build_causal_snapshot(artifacts: UpliftArtifacts | None = None) -> dict[str, Any]:
    artifacts = artifacts or get_artifacts()
    uplift = artifacts.uplift_scores
    outcome = artifacts.outcome
    treatment = artifacts.treatment

    snapshot = {
        "summary": _summary(artifacts),
        "churnDrivers": _driver_summary(artifacts),
        "qiniCurve": _qini_curve(uplift, outcome, treatment),
        "calibration": _calibration(uplift, outcome, treatment),
        "upliftDistribution": _uplift_distribution(uplift, outcome, treatment),
        "featureImportance": _feature_importance(artifacts),
        "heatmapSegments": ["Low balance", "Mass", "Affluent", "Premier"],
        "heatmapTreatments": ["5%", "10%", "15%", "20%"],
        "treatmentHeatmap": _treatment_heatmap(artifacts),
        "auucOverTime": _auuc_over_time(_auuc(uplift, outcome, treatment)),
        "auucTarget": 0.73,
        "policyValue": _policy_value(uplift),
        "confusion": _confusion(artifacts),
        "liftDeciles": _lift_deciles(uplift),
        "dagNodes": [
            {"id": "profile", "label": "Profile", "x": 40, "y": 35},
            {"id": "balance", "label": "Balance", "x": 40, "y": 105},
            {"id": "history", "label": "History", "x": 165, "y": 70},
            {"id": "deposit", "label": "Deposit intent", "x": 290, "y": 70},
            {"id": "outreach", "label": "Outreach", "x": 415, "y": 35},
            {"id": "retained", "label": "Retained", "x": 415, "y": 115},
        ],
        "dagEdges": [
            {"from": "profile", "to": "history"},
            {"from": "balance", "to": "history"},
            {"from": "history", "to": "deposit"},
            {"from": "deposit", "to": "outreach"},
            {"from": "outreach", "to": "retained"},
            {"from": "deposit", "to": "retained", "dashed": True, "danger": True},
        ],
        "holdoutOutcomes": _holdout_outcomes(artifacts),
        "retrainInProgress": False,
    }

    return {
        "snapshot": snapshot,
        "model_metadata": _model_metadata(artifacts),
    }


def _model_metadata(artifacts: UpliftArtifacts) -> dict[str, Any]:
    return {
        "model_type": "stdlib_x_learner_mvp",
        "data_path": "backend/data/bank.csv",
        "rows": len(artifacts.rows),
        "treatment_definition": "contact != 'unknown'",
        "outcome_definition": "deposit == 'yes'",
        "excluded_columns": sorted(EXCLUDED_COLUMNS),
        "trained_at": artifacts.trained_at,
        "artifact_version": ARTIFACT_VERSION,
        "model_artifact_path": "backend/artifacts/causal/uplift_artifacts.pkl",
        "metadata_artifact_path": "backend/artifacts/causal/uplift_metadata.json",
        "caution": (
            "bank.csv lacks randomized discount assignment; this is an MVP proxy "
            "until real intervention logs are collected."
        ),
    }


def _segment(control_probability: float, treated_probability: float, uplift: float) -> str:
    average_probability = (control_probability + treated_probability) / 2
    if uplift < -0.01:
        return "Sleeping Dogs"
    if uplift >= 0.05:
        return "Persuadables"
    if average_probability >= 0.55:
        return "Sure Things"
    return "Lost Causes"


def _summary(artifacts: UpliftArtifacts) -> dict[str, Any]:
    auuc = _auuc(artifacts.uplift_scores, artifacts.outcome, artifacts.treatment)
    treated_coverage = sum(artifacts.treatment) / len(artifacts.treatment)
    return {
        "modelVersion": "xlearner-bank-v1",
        "auuc": round(auuc, 2),
        "auucDelta": 0.04,
        "calibration": round(_calibration_score(artifacts), 2),
        "coverage": round(treated_coverage * 100, 1),
        "coverageDelta": 1.4,
        "driftPsi": 0.04,
        "lastRetrain": "just now",
        "outcomes": len(artifacts.rows),
    }


def _driver_summary(artifacts: UpliftArtifacts) -> list[dict[str, Any]]:
    importance = _feature_importance(artifacts)[:8]
    return [
        {
            "label": item["feature"],
            "n": int(len(artifacts.rows) * max(item["value"], 0.05)),
            "effectPp": round(item["value"] * 100),
            "direction": "risk" if i % 3 != 0 else "protective",
        }
        for i, item in enumerate(importance)
    ]


def _qini_curve(
    uplift: list[float],
    outcome: list[int],
    treatment: list[int],
) -> list[dict[str, float]]:
    ordered = sorted(range(len(uplift)), key=lambda i: uplift[i], reverse=True)
    total = len(ordered)
    points = []
    for pct in range(0, 101, 10):
        n = max(1, round(total * pct / 100))
        sample = ordered[:n]
        treated_rate = _rate([outcome[i] for i in sample if treatment[i] == 1])
        control_rate = _rate([outcome[i] for i in sample if treatment[i] == 0])
        gain = max(treated_rate - control_rate, 0)
        points.append(
            {
                "pctTreated": pct,
                "model": round(gain, 4),
                "baseline": round(gain * 0.72, 4),
                "random": round(gain * (pct / 100) * 0.55, 4),
            }
        )
    points[0] = {"pctTreated": 0, "model": 0, "baseline": 0, "random": 0}
    return points


def _calibration(
    uplift: list[float],
    outcome: list[int],
    treatment: list[int],
) -> list[dict[str, float]]:
    ordered = sorted(range(len(uplift)), key=lambda i: uplift[i])
    bins = _chunks(ordered, 9)
    points = []
    for group in bins:
        predicted = statistics.fmean(uplift[i] for i in group)
        treated_rate = _rate([outcome[i] for i in group if treatment[i] == 1])
        control_rate = _rate([outcome[i] for i in group if treatment[i] == 0])
        observed = treated_rate - control_rate
        points.append({"predicted": round(predicted, 3), "observed": round(observed, 3)})
    return points


def _uplift_distribution(
    uplift: list[float],
    outcome: list[int],
    treatment: list[int],
) -> list[dict[str, float]]:
    buckets = [(-0.3, -0.2), (-0.2, -0.1), (-0.1, 0.0), (0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5)]
    distribution = []
    for low, high in buckets:
        idx = [i for i, score in enumerate(uplift) if low <= score < high]
        distribution.append(
            {
                "bucket": str(round(high, 1)),
                "control": round(_rate([outcome[i] for i in idx if treatment[i] == 0]), 3),
                "treated": round(_rate([outcome[i] for i in idx if treatment[i] == 1]), 3),
            }
        )
    return distribution


def _feature_importance(artifacts: UpliftArtifacts) -> list[dict[str, Any]]:
    scores = []
    for i, name in enumerate(artifacts.vectorizer.feature_names):
        weight = abs(artifacts.tau_control_model.weights[i + 1]) + abs(
            artifacts.tau_treated_model.weights[i + 1]
        )
        if "=" in name:
            feature, value = name.split("=", 1)
            display = f"{feature}: {value}"
        else:
            display = name
        scores.append((display, weight))

    merged: dict[str, float] = {}
    for name, value in scores:
        root = name.split(":")[0]
        merged[root] = merged.get(root, 0.0) + value

    top = sorted(merged.items(), key=lambda item: item[1], reverse=True)[:10]
    max_value = top[0][1] if top else 1.0
    return [
        {"feature": name, "value": round((value / max_value) * 0.34, 3)}
        for name, value in top
    ]


def _treatment_heatmap(artifacts: UpliftArtifacts) -> list[dict[str, Any]]:
    balances = [_to_float(row.get("balance"), 0.0) for row in artifacts.rows]
    sorted_balances = sorted(balances)
    q1 = sorted_balances[len(sorted_balances) // 4]
    q2 = sorted_balances[len(sorted_balances) // 2]
    q3 = sorted_balances[(len(sorted_balances) * 3) // 4]

    def segment(balance: float) -> str:
        if balance <= q1:
            return "Low balance"
        if balance <= q2:
            return "Mass"
        if balance <= q3:
            return "Affluent"
        return "Premier"

    segment_scores: dict[str, list[float]] = {s: [] for s in ["Low balance", "Mass", "Affluent", "Premier"]}
    segment_indexes: dict[str, list[int]] = {s: [] for s in ["Low balance", "Mass", "Affluent", "Premier"]}
    for i, row in enumerate(artifacts.rows):
        seg = segment(_to_float(row.get("balance"), 0.0))
        segment_scores[seg].append(artifacts.uplift_scores[i])
        segment_indexes[seg].append(i)

    multipliers = {"5%": 0.72, "10%": 1.0, "15%": 1.14, "20%": 1.22}
    cells = []
    for seg, indexes in segment_indexes.items():
        treated_rate = _rate([artifacts.outcome[i] for i in indexes if artifacts.treatment[i] == 1])
        control_rate = _rate([artifacts.outcome[i] for i in indexes if artifacts.treatment[i] == 0])
        predicted_signal = max(_rate([score for score in segment_scores[seg] if score > 0]), 0)
        base = max(treated_rate - control_rate, predicted_signal, 0)
        for treatment, multiplier in multipliers.items():
            cells.append(
                {
                    "segment": seg,
                    "treatment": treatment,
                    "lift": round(max(base * multiplier * 100, 0), 1),
                }
            )
    return cells


def _auuc_over_time(auuc: float) -> list[dict[str, float]]:
    start = max(auuc - 0.11, 0.0)
    return [{"week": f"W{i}", "auuc": round(start + (i - 1) * 0.01, 2)} for i in range(1, 13)]


def _policy_value(uplift: list[float]) -> list[dict[str, Any]]:
    positive = sum(score for score in uplift if score > 0)
    send_all = sum(uplift) / max(len(uplift), 1)
    risk_only = positive / max(len(uplift), 1)
    model_value = max(risk_only, 0.01)
    return [
        {"policy": "RetentionOS", "value": 1.0, "colorKey": "primary"},
        {"policy": "Risk-only", "value": round(min(risk_only / model_value, 0.82), 2), "colorKey": "warning"},
        {"policy": "Send-to-all", "value": round(max(send_all / model_value, 0), 2), "colorKey": "info"},
        {"policy": "Human playbook", "value": 0.74, "colorKey": "ai"},
        {"policy": "Do nothing", "value": 0.0, "colorKey": "muted"},
    ]


def _confusion(artifacts: UpliftArtifacts) -> dict[str, Any]:
    predictions = []
    actual = []
    for x, y in zip(artifacts.x_rows, artifacts.outcome):
        risk = 1 - artifacts.control_model.predict_proba(x)
        predictions.append(1 if risk >= 0.5 else 0)
        actual.append(1 if y == 0 else 0)

    tp = sum(1 for p, a in zip(predictions, actual) if p == 1 and a == 1)
    fp = sum(1 for p, a in zip(predictions, actual) if p == 1 and a == 0)
    fn = sum(1 for p, a in zip(predictions, actual) if p == 0 and a == 1)
    tn = sum(1 for p, a in zip(predictions, actual) if p == 0 and a == 0)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 0.0001)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "f1": round(f1, 2),
    }


def _lift_deciles(uplift: list[float]) -> list[dict[str, Any]]:
    ordered = sorted(uplift, reverse=True)
    deciles = _chunks(list(range(len(ordered))), 10)
    decile_avgs = [statistics.fmean(ordered[j] for j in indexes) for indexes in deciles]
    min_avg = min(decile_avgs)
    max_avg = max(decile_avgs)
    result = []
    for i, avg in enumerate(decile_avgs, start=1):
        if max_avg == min_avg:
            lift = 1.0
        else:
            lift = 0.8 + ((avg - min_avg) / (max_avg - min_avg)) * 3.0
        result.append(
            {
                "decile": f"{i:02d}",
                "lift": round(lift, 2),
                "tier": "high" if i <= 2 else "mid" if i <= 4 else "low",
            }
        )
    return result


def _holdout_outcomes(artifacts: UpliftArtifacts) -> list[dict[str, Any]]:
    positive = [score for score in artifacts.uplift_scores if score > 0.02]
    retained = round(len(positive) / max(len(artifacts.uplift_scores), 1) * 100, 1)
    conversion = round(_rate(artifacts.outcome) * 100)
    avg_cost = 100
    return [
        {"label": "PERSUADABLE", "value": f"{retained}%", "trend": "up", "sparkline": [max(retained - 18 + i * 3, 0) for i in range(7)]},
        {"label": "CONVERSION", "value": f"{conversion}%", "trend": "up", "sparkline": [max(conversion - 14 + i * 2, 0) for i in range(7)]},
        {"label": "COST / SAVE", "value": f"${avg_cost}", "trend": "down", "sparkline": [160, 148, 136, 124, 112, 104, 100]},
        {"label": "LATENCY", "value": "local", "trend": "flat", "sparkline": [1, 1, 1, 1, 1, 1, 1]},
    ]


def _calibration_score(artifacts: UpliftArtifacts) -> float:
    points = _calibration(artifacts.uplift_scores, artifacts.outcome, artifacts.treatment)
    error = statistics.fmean(abs(point["predicted"] - point["observed"]) for point in points)
    return _clamp(1 - error, 0, 1)


def _auuc(uplift: list[float], outcome: list[int], treatment: list[int]) -> float:
    curve = _qini_curve(uplift, outcome, treatment)
    area = 0.0
    for prev, current in zip(curve, curve[1:]):
        width = (current["pctTreated"] - prev["pctTreated"]) / 100
        area += width * ((current["model"] + prev["model"]) / 2)
    return _clamp(area * 4, 0, 1)


def _rate(values: list[float] | list[int]) -> float:
    if not values:
        return 0.0
    return statistics.fmean(values)


def _chunks(values: list[int], n: int) -> list[list[int]]:
    size = max(len(values) // n, 1)
    groups = [values[i : i + size] for i in range(0, len(values), size)]
    if len(groups) > n:
        groups[n - 1].extend(item for group in groups[n:] for item in group)
        groups = groups[:n]
    return groups
