import pandas as pd
# pyrefly: ignore [missing-import]
import xgboost as xgb
import pickle
import json
import os
from datetime import datetime, timezone
from sklearn.model_selection import train_test_split

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "indian_bank_profiles.csv")
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts", "causal")
MODEL_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "uplift_artifacts.pkl")
METADATA_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "uplift_metadata.json")

# Features to exclude from training to prevent leakage
EXCLUDED_COLUMNS = ["duration", "deposit", "contact", "segment"]
TREATMENT_COL = "contact"
OUTCOME_COL = "deposit"

def train_xgboost_xlearner():
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    # Target: 1 if retained (deposit == 'yes'), 0 if churn (deposit == 'no')
    y = (df[OUTCOME_COL] == 'yes').astype(int)
    
    # Treatment proxy: 1 if contacted, 0 if not contacted
    t = (df[TREATMENT_COL] != 'unknown').astype(int)
    
    # Features
    X = df.drop(columns=EXCLUDED_COLUMNS, errors='ignore')
    
    # One-hot encode categorical features
    categorical_cols = X.select_dtypes(include=['object', 'string']).columns.tolist()
    X_encoded = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    print("Training Propensity Model...")
    propensity_model = xgb.XGBClassifier(n_estimators=100, max_depth=3, use_label_encoder=False, eval_metric="logloss", random_state=42)
    propensity_model.fit(X_encoded, t)
    
    # Split into treatment and control groups
    X_treated = X_encoded[t == 1]
    y_treated = y[t == 1]
    X_control = X_encoded[t == 0]
    y_control = y[t == 0]
    
    print("Training Stage 1 Models (Mu)...")
    mu_treated_model = xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42)
    mu_treated_model.fit(X_treated, y_treated)
    
    mu_control_model = xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42)
    mu_control_model.fit(X_control, y_control)
    
    print("Calculating Imputed Treatment Effects...")
    # Imputed treatment effects
    d_treated = y_treated - mu_control_model.predict(X_treated)
    d_control = mu_treated_model.predict(X_control) - y_control
    
    print("Training Stage 2 Models (Tau)...")
    tau_treated_model = xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42)
    tau_treated_model.fit(X_treated, d_treated)
    
    tau_control_model = xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42)
    tau_control_model.fit(X_control, d_control)
    
    # Calculate uplift scores for snapshot
    print("Calculating full uplift scores...")
    propensities = propensity_model.predict_proba(X_encoded)[:, 1]
    tau_treated = tau_treated_model.predict(X_encoded)
    tau_control = tau_control_model.predict(X_encoded)
    uplift_scores = (propensities * tau_control) + ((1 - propensities) * tau_treated)
    
    print("Packaging X-Learner Artifacts...")
    artifacts = {
        "propensity_model": propensity_model,
        "mu_treated_model": mu_treated_model,
        "mu_control_model": mu_control_model,
        "tau_treated_model": tau_treated_model,
        "tau_control_model": tau_control_model,
        "features": list(X_encoded.columns),
        "categorical_cols": categorical_cols,
        "rows": df.to_dict(orient="records"),
        "treatment": t.tolist(),
        "outcome": y.tolist(),
        "uplift_scores": uplift_scores.tolist(),
        "propensities": propensities.tolist()
    }
    
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    with open(MODEL_ARTIFACT_PATH, "wb") as f:
        pickle.dump(artifacts, f, protocol=pickle.HIGHEST_PROTOCOL)
        
    metadata = {
        "model_type": "xgboost_xlearner_v1",
        "data_path": "backend/data/indian_bank_profiles.csv",
        "features_count": len(X_encoded.columns),
        "outcome": "deposit == 'yes'",
        "treatment": "contact != 'unknown'",
        "excluded_columns": EXCLUDED_COLUMNS,
        "trained_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "artifact_version": 1
    }
    
    with open(METADATA_ARTIFACT_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Saved artifacts to {MODEL_ARTIFACT_PATH}")

if __name__ == "__main__":
    train_xgboost_xlearner()
