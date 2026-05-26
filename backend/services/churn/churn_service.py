import json
import os
import pickle
from datetime import datetime, timezone
from typing import Any
import pandas as pd

from models.churn_models import ChurnScoreResponse

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "indian_bank_profiles.csv")
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "artifacts", "churn")
MODEL_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "retentionos_churn_v1.pkl")
METADATA_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "churn_metadata.json")

def load_artifacts() -> dict[str, Any] | None:
    if not os.path.exists(MODEL_ARTIFACT_PATH):
        return None
    with open(MODEL_ARTIFACT_PATH, "rb") as handle:
        return pickle.load(handle)

def get_artifacts() -> dict[str, Any]:
    artifacts = load_artifacts()
    if artifacts is None:
        from create_xgboost_churn_model import train_xgboost_churn_model
        train_xgboost_churn_model()
        artifacts = load_artifacts()
    return artifacts

def retrain_churn_model() -> dict[str, Any]:
    from create_xgboost_churn_model import train_xgboost_churn_model
    train_xgboost_churn_model()
    
    with open(METADATA_ARTIFACT_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)
        
    return {
        "metrics": metadata.get("metrics", {}),
        "model_metadata": metadata
    }

def get_churn_metrics() -> dict[str, Any]:
    if not os.path.exists(METADATA_ARTIFACT_PATH):
        retrain_churn_model()
        
    with open(METADATA_ARTIFACT_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)
        
    return {
        "metrics": metadata.get("metrics", {}),
        "model_metadata": metadata
    }

def score_customer(customer: dict[str, Any]) -> ChurnScoreResponse:
    artifacts = get_artifacts()
    model = artifacts["model"]
    explainer = artifacts["explainer"]
    expected_features = artifacts["features"]
    categorical_cols = artifacts["categorical_cols"]
    threshold = artifacts["threshold"]
    
    # Exclude leakage
    excluded = ["contact", "deposit", "duration", "segment"]
    cust_df = pd.DataFrame([customer])
    cust_df.drop(columns=[col for col in excluded if col in cust_df.columns], inplace=True)
    
    # Encode matching training features
    cust_encoded = pd.get_dummies(cust_df, columns=[c for c in categorical_cols if c in cust_df.columns], drop_first=False)
    
    # Ensure all expected columns exist, fill with 0
    for col in expected_features:
        if col not in cust_encoded.columns:
            cust_encoded[col] = 0
            
    # Keep only expected features in correct order
    X = cust_encoded[expected_features]
    
    probability = float(model.predict_proba(X)[0, 1])
    
    # SHAP Explainability
    shap_values = explainer.shap_values(X)
    # TreeExplainer might return a list of arrays for classification, or a single array
    if isinstance(shap_values, list):
        shap_vals = shap_values[1][0] # Positive class
    else:
        shap_vals = shap_values[0]
        
    # Zip features with their SHAP values and raw values
    contributions = []
    for i, feature in enumerate(expected_features):
        val = shap_vals[i]
        raw_val = float(X.iloc[0, i])
        if val > 0.05: # Only significant contributors
            contributions.append((feature, val, raw_val))
            
    contributions.sort(key=lambda x: x[1], reverse=True)
    
    top_drivers = []
    for feature, shap_val, raw_val in contributions[:3]:
        # Friendly format
        if feature == "upi_frequency_drop" and raw_val > 0:
            top_drivers.append(f"Priority Risk due to {int(raw_val*100)}% UPI drop")
        elif feature == "relocation" and raw_val == 1:
            top_drivers.append("Priority Risk due to recent relocation")
        elif feature == "competitor_pricing_gap" and raw_val < 0:
            top_drivers.append(f"Priority Risk due to competitor better by {abs(raw_val)}%")
        elif feature == "job_change" and raw_val == 1:
            top_drivers.append("Priority Risk due to job change")
        else:
            top_drivers.append(f"Risk flagged by {feature}")
            
    if not top_drivers:
        top_drivers.append("Baseline risk profile")

    return ChurnScoreResponse(
        churn_probability=round(probability, 4),
        retention_probability=round(1 - probability, 4),
        risk_tier=_risk_tier(probability, threshold),
        should_enter_uplift_model=probability >= threshold,
        top_risk_drivers=top_drivers,
    )

def _risk_tier(probability: float, threshold: float) -> str:
    if probability >= threshold + 0.3:
        return "critical"
    if probability >= threshold + 0.1:
        return "high"
    if probability >= threshold:
        return "medium"
    return "low"
