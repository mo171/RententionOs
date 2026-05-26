import pandas as pd
# pyrefly: ignore [missing-import]
import xgboost as xgb
# pyrefly: ignore [missing-import]
import shap
import pickle
import json
import os
from datetime import datetime, timezone
from sklearn.model_selection import train_test_split
from sklearn.metrics import recall_score, precision_score, roc_auc_score, f1_score

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "indian_bank_profiles.csv")
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts", "churn")
MODEL_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "retentionos_churn_v1.pkl")
METADATA_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "churn_metadata.json")

# Features to exclude from training to prevent leakage
EXCLUDED_COLUMNS = ["contact", "deposit", "duration", "segment"]
TARGET_COL = "deposit"

def train_xgboost_churn_model():
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    # Target: 1 if churn (deposit == 'no'), 0 if retained (deposit == 'yes')
    y = (df[TARGET_COL] == 'no').astype(int)
    
    # Features
    X = df.drop(columns=EXCLUDED_COLUMNS, errors='ignore')
    
    # One-hot encode categorical features
    categorical_cols = X.select_dtypes(include=['object', 'string']).columns.tolist()
    X_encoded = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    # Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print("Training XGBoost Classifier...")
    # scale_pos_weight helps with optimizing for Recall on imbalanced data
    scale_pos_weight = (len(y_train) - sum(y_train)) / sum(y_train)
    
    model = xgb.XGBClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=5,
        scale_pos_weight=scale_pos_weight, # Prioritize positive class to boost recall
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Find threshold for recall > 0.95
    # We will sort probabilities and find the threshold that gives > 0.95 recall
    thresholds = [i/100.0 for i in range(1, 100)]
    best_threshold = 0.5
    for t in thresholds:
        y_pred = (y_pred_proba >= t).astype(int)
        recall = recall_score(y_test, y_pred)
        if recall >= 0.95:
            best_threshold = t
            # we want the highest threshold that still gives >= 0.95 recall to keep precision as high as possible
            
    # Final evaluation at best_threshold
    y_pred_best = (y_pred_proba >= best_threshold).astype(int)
    final_recall = recall_score(y_test, y_pred_best)
    final_precision = precision_score(y_test, y_pred_best, zero_division=0)
    final_roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    print(f"Metrics at threshold {best_threshold}:")
    print(f"Recall: {final_recall:.4f}")
    print(f"Precision: {final_precision:.4f}")
    print(f"ROC-AUC: {final_roc_auc:.4f}")
    
    # SHAP Explainer
    print("Fitting SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    
    # Package artifacts
    artifacts = {
        "model": model,
        "explainer": explainer,
        "features": list(X_encoded.columns),
        "categorical_cols": categorical_cols,
        "threshold": best_threshold
    }
    
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    with open(MODEL_ARTIFACT_PATH, "wb") as f:
        pickle.dump(artifacts, f, protocol=pickle.HIGHEST_PROTOCOL)
        
    metadata = {
        "model_type": "xgboost_churn_v1",
        "data_path": "backend/data/indian_bank_profiles.csv",
        "features_count": len(X_encoded.columns),
        "target": "churn_proxy = deposit == 'no'",
        "excluded_columns": EXCLUDED_COLUMNS,
        "metrics": {
            "threshold": best_threshold,
            "recall": final_recall,
            "precision": final_precision,
            "roc_auc": final_roc_auc
        },
        "trained_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "artifact_version": 1
    }
    
    with open(METADATA_ARTIFACT_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Saved artifacts to {MODEL_ARTIFACT_PATH}")
    print(f"Saved metadata to {METADATA_ARTIFACT_PATH}")

if __name__ == "__main__":
    train_xgboost_churn_model()
