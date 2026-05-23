# RetentionOS LTV Model Metrics

Generated at: `2026-05-23T18:43:55.704089Z`
Model artifact: `backend/artifacts/ltv/ltv_model.pkl`
Rows evaluated: `10000`

## Algorithm

- Historical LTV = `loan_interest_paid_12m + fee_income_earned_12m - servicing_cost_12m`.
- Future LTV is predicted from segment, income, spend, credit, liquidity, engagement, and risk signals.
- Default risk is predicted separately and penalizes the final customer value score.
- CFVS is a 0-100 customer financial value score used as the first RetentionOS eligibility gate.

## Future LTV Regression

- MAE: `36376.24`
- RMSE: `75132.08`
- R2: `0.7361`

## Default Risk Metrics

- Precision: `0.7766`
- Recall: `0.9803`
- F1: `0.8667`
- AUC-ROC: `0.9791`
- Confusion: `{'tp': 299, 'fp': 86, 'fn': 6, 'tn': 1609}`

## LTV Gate

- Low cutoff: `50.3568`
- High cutoff: `57.3026`
- Eligible rows: `5554`
- Eligible rate: `0.5554`
- Priority rows: `2126`

## Inferences for RetentionOS

- The LTV model is the first financial eligibility gate in the README flow before churn and uplift scoring.
- CFVS combines historical customer value, predicted future value, engagement, and default-risk penalty.
- Customers below the dynamic CFVS cutoff should not consume churn/uplift capacity in the MVP pipeline.
- Customers in high or premium tiers are the best candidates for churn risk scoring and later causal uplift checks.
- The current artifact is trained on synthetic Indian banking data from backend/models/LTV.py, not production ledger history.

## Caveats

- This is an MVP integration of the notebook prototype, with stdlib models replacing notebook-only LightGBM/XGBoost/SHAP runtime dependencies.
- Production LTV should train on real transaction, balance, fee, product, and servicing-cost history.
- Synthetic CFVS thresholds are population-relative and should be recalibrated when real customer data arrives.
