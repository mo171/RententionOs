from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BankMarketingSchema:
    feature_columns: list[str] = field(
        default_factory=lambda: [
            "age",
            "balance",
            "housing",
            "loan",
            "day",
            "month",
            "job",
            "marital",
            "education",
            "default",
            "campaign",
            "pdays",
            "previous",
            "poutcome",
        ]
    )
    numeric_columns: list[str] = field(
        default_factory=lambda: ["age", "balance", "day", "campaign", "pdays", "previous"]
    )
    categorical_columns: list[str] = field(
        default_factory=lambda: [
            "housing",
            "loan",
            "month",
            "job",
            "marital",
            "education",
            "default",
            "poutcome",
        ]
    )
    treatment_column: str = "campaign_contacted"
    outcome_column: str = "retained_or_subscribed"


@dataclass(frozen=True)
class ProfitGuardrail:
    ltv_column: str = "ltv"
    default_ltv: float = 1000.0
    treatment_costs: dict[str, float] = field(
        default_factory=lambda: {
            "discount_5": 50.0,
            "discount_10": 100.0,
            "discount_15": 150.0,
            "discount_20": 200.0,
        }
    )
    treatment_multipliers: dict[str, float] = field(
        default_factory=lambda: {
            "discount_5": 0.72,
            "discount_10": 1.0,
            "discount_15": 1.14,
            "discount_20": 1.22,
        }
    )


class SklearnXGBoostXLearner:
    """Production-style X-Learner reference for the Causal Intelligence Layer.

    This module intentionally lives outside the current FastAPI hot path. The app
    can keep serving the existing stdlib artifact while this class documents the
    sklearn/XGBoost upgrade path expected for the production ML stack.
    """

    def __init__(
        self,
        *,
        schema: BankMarketingSchema | None = None,
        guardrail: ProfitGuardrail | None = None,
        random_state: int = 42,
    ) -> None:
        self.schema = schema or BankMarketingSchema()
        self.guardrail = guardrail or ProfitGuardrail()
        self.random_state = random_state
        self.preprocessor: Any | None = None
        self.mu0: Any | None = None
        self.mu1: Any | None = None
        self.tau0: Any | None = None
        self.tau1: Any | None = None
        self.propensity_model: Any | None = None

    def fit(self, frame: Any) -> "SklearnXGBoostXLearner":
        deps = _load_ml_dependencies()
        xgb_classifier = deps["XGBClassifier"]
        xgb_regressor = deps["XGBRegressor"]
        pipeline = deps["Pipeline"]

        x = frame[self.schema.feature_columns]
        treatment = frame[self.schema.treatment_column].astype(int)
        outcome = frame[self.schema.outcome_column].astype(int)

        self.preprocessor = _build_preprocessor(self.schema, deps)
        control_mask = treatment == 0
        treated_mask = treatment == 1

        self.mu0 = pipeline(
            [
                ("prep", self.preprocessor),
                ("model", xgb_classifier(eval_metric="logloss", random_state=self.random_state)),
            ]
        )
        self.mu1 = pipeline(
            [
                ("prep", self.preprocessor),
                ("model", xgb_classifier(eval_metric="logloss", random_state=self.random_state)),
            ]
        )
        self.mu0.fit(x[control_mask], outcome[control_mask])
        self.mu1.fit(x[treated_mask], outcome[treated_mask])

        mu0_for_treated = self.mu0.predict_proba(x[treated_mask])[:, 1]
        mu1_for_control = self.mu1.predict_proba(x[control_mask])[:, 1]
        d1 = outcome[treated_mask].to_numpy() - mu0_for_treated
        d0 = mu1_for_control - outcome[control_mask].to_numpy()

        self.tau1 = pipeline(
            [("prep", self.preprocessor), ("model", xgb_regressor(random_state=self.random_state))]
        )
        self.tau0 = pipeline(
            [("prep", self.preprocessor), ("model", xgb_regressor(random_state=self.random_state))]
        )
        self.tau1.fit(x[treated_mask], d1)
        self.tau0.fit(x[control_mask], d0)

        self.propensity_model = pipeline(
            [
                ("prep", self.preprocessor),
                ("model", xgb_classifier(eval_metric="logloss", random_state=self.random_state)),
            ]
        )
        self.propensity_model.fit(x, treatment)
        return self

    def cate(self, frame: Any) -> Any:
        self._check_fitted()
        x = frame[self.schema.feature_columns]
        propensity = self.propensity_model.predict_proba(x)[:, 1].clip(0.02, 0.98)
        tau0 = self.tau0.predict(x)
        tau1 = self.tau1.predict(x)
        return (propensity * tau0) + ((1 - propensity) * tau1)

    def prioritized_persuadables(self, frame: Any) -> Any:
        deps = _load_ml_dependencies()
        pd = deps["pd"]
        scored = frame.copy()
        scored["uplift_score"] = self.cate(frame)
        scored["baseline_retention_probability"] = self.mu0.predict_proba(
            frame[self.schema.feature_columns]
        )[:, 1]
        scored["treated_retention_probability"] = self.mu1.predict_proba(
            frame[self.schema.feature_columns]
        )[:, 1]

        decisions = []
        for _, row in scored.iterrows():
            ltv = float(row.get(self.guardrail.ltv_column, self.guardrail.default_ltv))
            best_treatment = None
            best_profit = float("-inf")
            best_uplift = 0.0
            for treatment, cost in self.guardrail.treatment_costs.items():
                multiplier = self.guardrail.treatment_multipliers.get(treatment, 1.0)
                treatment_uplift = float(row["uplift_score"]) * multiplier
                expected_profit = (treatment_uplift * ltv) - cost
                if expected_profit > best_profit:
                    best_profit = expected_profit
                    best_treatment = treatment
                    best_uplift = treatment_uplift
            decisions.append(
                {
                    "best_treatment": best_treatment,
                    "treatment_uplift": best_uplift,
                    "expected_profit": best_profit,
                    "approved": row["uplift_score"] > 0 and best_profit > 0,
                }
            )

        decision_frame = pd.DataFrame(decisions, index=scored.index)
        scored = pd.concat([scored, decision_frame], axis=1)
        return scored[scored["approved"]].sort_values("expected_profit", ascending=False)

    def evaluate(self, frame: Any) -> dict[str, float]:
        deps = _load_ml_dependencies()
        metrics = deps["metrics"]
        cate = self.cate(frame)
        outcome = frame[self.schema.outcome_column].astype(int)
        treatment = frame[self.schema.treatment_column].astype(int)
        churn_actual = 1 - outcome
        churn_score = 1 - self.mu0.predict_proba(frame[self.schema.feature_columns])[:, 1]
        churn_pred = (churn_score >= 0.5).astype(int)

        return {
            "precision": float(metrics.precision_score(churn_actual, churn_pred, zero_division=0)),
            "recall": float(metrics.recall_score(churn_actual, churn_pred, zero_division=0)),
            "auc_roc": float(metrics.roc_auc_score(churn_actual, churn_score)),
            "auuc": _fallback_auuc(cate, outcome, treatment),
            "qini_coefficient": _fallback_qini(cate, outcome, treatment),
        }

    def save(self, path: str) -> None:
        with open(path, "wb") as handle:
            pickle.dump(self, handle, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load(cls, path: str) -> "SklearnXGBoostXLearner":
        with open(path, "rb") as handle:
            model = pickle.load(handle)
        if not isinstance(model, cls):
            raise TypeError(f"Expected {cls.__name__}, got {type(model).__name__}")
        return model

    def _check_fitted(self) -> None:
        if not all([self.mu0, self.mu1, self.tau0, self.tau1, self.propensity_model]):
            raise RuntimeError("X-Learner must be fitted or loaded before scoring.")


def _build_preprocessor(schema: BankMarketingSchema, deps: dict[str, Any]) -> Any:
    column_transformer = deps["ColumnTransformer"]
    one_hot_encoder = deps["OneHotEncoder"]
    pipeline = deps["Pipeline"]
    simple_imputer = deps["SimpleImputer"]
    standard_scaler = deps["StandardScaler"]

    numeric_pipe = pipeline(
        [
            ("impute", simple_imputer(strategy="median")),
            ("scale", standard_scaler()),
        ]
    )
    categorical_pipe = pipeline(
        [
            ("impute", simple_imputer(strategy="most_frequent")),
            ("onehot", one_hot_encoder(handle_unknown="ignore")),
        ]
    )
    return column_transformer(
        [
            ("num", numeric_pipe, schema.numeric_columns),
            ("cat", categorical_pipe, schema.categorical_columns),
        ]
    )


def _load_ml_dependencies() -> dict[str, Any]:
    try:
        import pandas as pd
        from sklearn import metrics
        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler
        from xgboost import XGBClassifier, XGBRegressor
    except ImportError as exc:
        raise ImportError(
            "Install the optional ML stack with `pip install -r backend/requirements-ml.txt` "
            "before using SklearnXGBoostXLearner."
        ) from exc

    return {
        "pd": pd,
        "metrics": metrics,
        "ColumnTransformer": ColumnTransformer,
        "SimpleImputer": SimpleImputer,
        "Pipeline": Pipeline,
        "OneHotEncoder": OneHotEncoder,
        "StandardScaler": StandardScaler,
        "XGBClassifier": XGBClassifier,
        "XGBRegressor": XGBRegressor,
    }


def _fallback_auuc(cate: Any, outcome: Any, treatment: Any) -> float:
    ordered = sorted(range(len(cate)), key=lambda index: cate[index], reverse=True)
    points = [0.0]
    for pct in range(10, 101, 10):
        sample = ordered[: max(1, round(len(ordered) * pct / 100))]
        points.append(_observed_uplift(sample, outcome, treatment))
    return sum((points[i] + points[i - 1]) / 20 for i in range(1, len(points)))


def _fallback_qini(cate: Any, outcome: Any, treatment: Any) -> float:
    ordered = sorted(range(len(cate)), key=lambda index: cate[index], reverse=True)
    gains = [0.0]
    for pct in range(10, 101, 10):
        sample = ordered[: max(1, round(len(ordered) * pct / 100))]
        treated = [index for index in sample if treatment.iloc[index] == 1]
        control = [index for index in sample if treatment.iloc[index] == 0]
        if not treated or not control:
            gains.append(0.0)
            continue
        treated_outcomes = sum(outcome.iloc[index] for index in treated)
        control_outcomes = sum(outcome.iloc[index] for index in control)
        gains.append(treated_outcomes - (len(treated) / len(control)) * control_outcomes)
    model_area = sum((gains[i] + gains[i - 1]) / 20 for i in range(1, len(gains)))
    random_area = gains[-1] / 2
    return model_area - random_area


def _observed_uplift(indices: list[int], outcome: Any, treatment: Any) -> float:
    treated = [outcome.iloc[index] for index in indices if treatment.iloc[index] == 1]
    control = [outcome.iloc[index] for index in indices if treatment.iloc[index] == 0]
    if not treated or not control:
        return 0.0
    return (sum(treated) / len(treated)) - (sum(control) / len(control))

