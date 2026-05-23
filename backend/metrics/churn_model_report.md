# RetentionOS Churn Model Metrics

Generated at: `2026-05-23T18:13:45.555495Z`
Model artifact: `backend/artifacts/churn/churn_model.pkl`
Rows evaluated: `11162`

## Schema Mapping

- Features: behavioral and demographic Bank Marketing columns available before uplift scoring.
- Target: `churn_proxy = deposit == 'no'`
- Leakage excluded: `contact`, `deposit`, `duration`

## Classification Metrics

- Threshold: `0.32`
- Precision: `0.6136`
- Recall: `0.9379`
- F1: `0.7418`
- Accuracy: `0.6565`
- AUC-ROC: `0.7039`
- PR-AUC: `0.6778`
- Confusion: `{'tp': 1102, 'fp': 694, 'fn': 73, 'tn': 364}`

## Probability Quality

- Brier score: `0.2184`

## Business Gate

- Risk gate threshold: `0.32`
- Test rows entering uplift model: `1796`
- Test coverage entering uplift model: `0.8043`
- Recall at top 10%: `0.1336`
- Recall at top 20%: `0.2647`

## Inferences for RetentionOS

- The churn model is acting as the risk gate in the README flow: `LTV Filtering -> Churn Prediction -> Causal Uplift Modeling -> Treatment Optimization`.
- A high recall score means the model is intentionally broad and catches most customers who match the churn proxy before they reach the uplift model.
- Precision is moderate, so some customers sent to uplift will not truly be risky; this is acceptable for an MVP gate because the uplift and profit guardrail layers make the final intervention decision.
- AUC-ROC above random indicates useful ranking power, but this is not a production-grade BFSI churn model yet.
- The current threshold sends a wide portion of customers into uplift scoring, prioritizing missed-churn avoidance over compute savings.
- `high_risk_customers.csv` should be read as the prioritized risk queue, not as an approved intervention list.
- Customers marked high or critical risk should still pass through the uplift model; only positive uplift and positive expected profit should trigger agentic intervention.

## Caveats

- This MVP uses deposit == 'no' as a churn proxy because bank.csv has no future churn event.
- Production churn should be trained on historical snapshots with a future inactivity or closure window.
- duration is excluded because it is known only after customer contact starts.
- contact is excluded because it is the uplift treatment proxy and should not leak into pre-uplift churn filtering.
