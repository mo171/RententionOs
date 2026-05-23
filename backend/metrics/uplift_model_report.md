# RetentionOS Uplift Model Metrics

Generated at: `2026-05-22T17:57:05.584752Z`
Model artifact: `backend/artifacts/causal/uplift_artifacts.pkl`
Rows evaluated: `11162`

## Schema Mapping

- Features: behavioral and demographic Bank Marketing columns, excluding target/leakage fields.
- Treatment: `contact != 'unknown'`
- Outcome: `deposit == 'yes'`
- Leakage excluded: `contact`, `deposit`, `duration`

## Causal Metrics

- AUUC: `0.216`
- Dashboard-scaled AUUC: `0.8639`
- Qini coefficient: `-304.0515`
- Normalized Qini: `-0.1099`
- Top-decile observed uplift: `0.0619`
- Mean predicted uplift: `-0.0459`

## Churn Base Filter Metrics

- Precision: `0.5262`
- Recall: `1.0`
- AUC-ROC: `0.6378`
- F1: `0.6895`
- Accuracy: `0.5262`
- Confusion: `{'tp': 5873, 'fp': 5289, 'fn': 0, 'tn': 0}`

## Profit Guardrail

- LTV assumption: `1000.0`
- Approval rule: `approved when uplift_score > 0 and best expected_profit > 0`
- Approved rows in prioritized CSV: `5`
- Positive uplift rows: `1172`
- Persuadable CSV: `backend/metrics/persuadable_customers.csv`

## Interpretation

The uplift model does not have directly observable individual-level accuracy because each customer has only one observed outcome. Use AUUC, Qini, decile uplift, calibration, and future randomized holdout experiments to judge causal quality.

## Caveats

- Individual uplift accuracy cannot be directly observed without randomized counterfactual outcomes.
- bank.csv has no true randomized discount assignment; contact != 'unknown' is used as the MVP outreach proxy.
- duration is excluded because it is a post-contact leakage feature.
- AUUC and Qini are observational diagnostics here, not production causal validity guarantees.
