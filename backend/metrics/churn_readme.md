# XGBoost Churn Model Metrics

This document outlines the performance metrics for the `xgboost_churn_v1` model used in the RetentionOS Gatekeeper pipeline.

## Current Model Metrics

Based on the latest training run using the `indian_bank_profiles.csv` synthetic dataset, the model achieved the following performance:

*   **Decision Threshold:** `0.29`
*   **Recall:** `0.9578` (95.78%)
*   **Precision:** `0.4773` (47.73%)
*   **ROC-AUC:** `0.6941`

---

## How to Analyze and Read These Metrics

### 1. Recall (0.9578) — *The Primary Optimization Target*
**What it means:** Out of all the customers who actually churned (or would have churned), the model correctly identified **95.78%** of them. 

**Why it matters for RetentionOS:** We purposefully optimized this model for high recall. Missing a high-value customer who is about to churn is an incredibly expensive mistake (high false-negative cost). A recall of >0.95 means our initial "safety net" is extremely wide, ensuring very few genuine churners slip through the cracks.

### 2. Precision (0.4773)
**What it means:** When the model flags a customer as "At Risk of Churn", it is correct about **47.73%** of the time. 

**Why it matters for RetentionOS:** A precision of ~48% means there are a significant number of false positives (customers flagged as churners who were actually going to stay). 

**This is an intentional trade-off**. Because we force the model to prioritize Recall, it casts a wider net. In a traditional system, low precision wastes budget by sending unnecessary discounts. However, in RetentionOS, the downstream **Causal Uplift Model** and **Profit Guardrail** act as secondary filters to ensure we don't waste intervention budgets on these false positives.

### 3. Decision Threshold (0.29)
**What it means:** Instead of using the standard `0.50` probability cutoff for binary classification, the model flags a customer as a churn risk if their predicted churn probability is `>= 0.29`.

**Why it matters for RetentionOS:** Lowering the threshold is the mechanical lever used to achieve the >0.95 Recall. By lowering the bar for what constitutes a "risk", we capture more potential churners early and pass them into the LangGraph evaluation pipeline.

### 4. ROC-AUC (0.6941)
**What it means:** The Area Under the Receiver Operating Characteristic Curve (ROC-AUC) evaluates how well the model separates churners from non-churners across *all* possible thresholds. A score of 0.5 is random guessing, and 1.0 is perfect separation.

**Why it matters for RetentionOS:** A score of ~0.69 indicates moderate discriminative ability on this synthetic dataset. While perfectly acceptable for the MVP, future iterations trained on real production ledger data (with richer historical transaction features) should aim to push this metric above 0.80.

---

## The Big Picture: Downstream Pipeline Impact

Because the Churn Model intentionally produces false positives to secure high recall, it acts solely as the **Top of Funnel Gatekeeper**. 

If a customer is flagged by this model, they are **not** immediately sent a discount. Instead, they must still successfully pass through the rest of the Gatekeeper Architecture:
1. **LTV Filter:** Are they financially worth saving?
2. **Causal X-Learner Uplift Model:** Are they *persuadable*, or are they a "Lost Cause"/"Sure Thing"?
3. **Graph Intelligence:** Are they a highly influential network hub?
4. **Strategy Agent Guardrail:** Is the final `Expected Profit > 0` after accounting for the intervention cost?
