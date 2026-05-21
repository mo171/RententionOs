Technical Mapping Report: Bank Marketing Dataset to X-Learner Causal Framework

1. Report Purpose and Alignment with RetentionOS

This report establishes the formal architectural schema for mapping the Bank Marketing Dataset to the Causal Intelligence Layer (Section 6.4) of the RetentionOS Gatekeeper Architecture. The objective is to facilitate the transition from traditional binary churn prediction to a more sophisticated identification of "persuadable" customers through the X-learner mathematical framework. While the current production state utilizes an R-learner to separate baseline churn from treatment effects, this X-learner extension represents the future-state evolution required for optimizing specific intervention strategies. By mapping raw banking features to formal causal components, we enable RetentionOS to move beyond reactive reporting into autonomous, ROI-positive customer persuasion.

2. The X-Learner Mathematical Framework (X, T, Y)

The X-learner framework is deployed to estimate the Conditional Average Treatment Effect (CATE) by imputing counterfactual outcomes for every individual in the dataset. Unlike simpler models, the X-learner is specifically designed to handle unbalanced treatment groups, which is common in banking outreach datasets.

Causal Variable Definitions

Variable (Notation)	RetentionOS Definition	Causal Role
Covariates (X)	Holistic customer profile data (Sections 5.1–5.5) encompassing behavioral, digital, and life event signals.	Provides the high-dimensional context necessary to model the heterogeneity of customer responses to interventions.
Treatment (T)	Proactive retention interventions executed via the Execution Layer (Section 6.6), such as relationship manager calls.	The indicator variable used to measure the causal impact of a specific outreach strategy against a control group.
Outcome (Y)	The stay-status or financial engagement level (Section 6.4) measured post-intervention.	The dependent variable used to calculate the Uplift Score and determine the realized ROI of the intervention.

3. Feature Mapping: Covariates (X)

Features from the Bank Marketing Dataset are mapped into the five intelligence categories of RetentionOS. Technical Requirement: All covariates must be pre-treatment indicators.

* Customer Behaviour Data
  * balance: Current account liquidity and resource depth.
  * housing: Binary indicator of existing housing loans.
  * loan: Binary indicator of personal loan status.
  * pdays: Recency signal representing days since the customer was last contacted.
  * previous: Frequency signal representing the number of contacts performed before this campaign.
* Digital Engagement Data
  * contact: Communication channel type (cellular, telephone).
  * month and day_of_week: Temporal engagement signals for campaign timing optimization.
  * CAUTION (Data Leakage Risk): The duration variable (last contact duration) must be excluded from the covariate set X. Because duration is only known after a contact begins, using it to predict uplift creates a post-treatment bias (leakage), as long durations are often highly correlated with the outcome Y but are not predictive at the moment of decision-making.
* Customer Support Data
  * Historical sentiment signals and ticket frequency (mapped from internal CRM logs and integrated into the holistic profile).
* Customer Life Events
  * age, job, marital, and education: Core demographic indicators used to define customer segments and life-stage stability.
* External Market Data
  * poutcome: Outcome of the previous marketing campaign (success/failure), serving as a critical strategic covariate for CATE estimation and baseline propensity.

4. Treatment Variable (T): Retention Interventions

In this framework, 'T' represents the specific outreach action selected by the Decision & Strategy Layer (Section 6.5). The variable models the transition from no-contact (control) to proactive engagement.

Potential treatments within the banking dataset include:

* Direct Outreach: Relationship manager interactions or phone calls.
* Digital Interventions: Automated email, SMS, or mobile notifications.
* Financial Incentives: Personalized offers or discount depth adjustments.

5. Outcome Variable (Y): Retention and Profitability

The outcome 'Y' is the realized stay-status. In the Causal Intelligence Layer, this is quantified via the Uplift Score formula: Uplift Score = P(stay | intervention) - P(stay | no intervention)

While the R-learner architecture models residuals, the X-learner advances this by imputing counterfactuals. It trains a Control Model (M0) to predict behavior without intervention and a Treatment Model (M1) for the reverse. By imputing the missing potential outcomes for both groups, the system isolates the true treatment effect from baseline noise, ensuring that the Decision Layer ignores customers who would have stayed regardless of the intervention.

6. CATE Estimation and 'Persuadable' Logic

By calculating the CATE for each individual, the Agentic Intelligence of RetentionOS segments the population into four causal quadrants. This ensures that the Decision & Strategy Layer (Section 6.5) can apply "Profit Guardrails" to protect margins.

Causal Segmentation Logic

Quadrant	CATE Description	RetentionOS Action
Persuadables	High Uplift (M1 > M0); intervention significantly changes stay probability.	Prioritize: Trigger the Decision Layer to optimize discount depth and select the highest-ROI communication channel.
Sure Things	Low Uplift; high probability of staying regardless of contact.	Ignore: Withhold intervention to eliminate "marketing waste" and preserve budget for persuadables.
Lost Causes	Low Uplift; high probability of churning regardless of contact.	Ignore: Halt analysis and intervention to protect discount budgets and computational overhead.
Sleeping Dogs	Negative Uplift (M1 < M0); outreach may trigger a churn event.	Avoid: Apply strict "Profit Guardrails" to ensure these customers are excluded from all proactive outreach.

7. Data Validation and Quality Guardrails

To achieve the benchmarked 15–20% Retention Improvement and the potential 25–95% Profit Increase (Source 24/33), the following technical requirements must be enforced:

1. Baseline ROI Benchmarking: Data quality validation is the mandatory prerequisite for achieving the platform's stated profit impact metrics.
2. Anti-Leakage Validation: Mandatory exclusion of duration and other post-treatment variables from the covariate set to prevent inflated accuracy and model risk.
3. Counterfactual Integrity: Verification that M0 and M1 models are learned on high-fidelity, cleaned data to reduce bias in CATE imputation.
4. Privacy and Trust Security: All mapped demographic features (age, job, marital) must be processed through secure systems to mitigate the "Trust Risk" cited by 63% of concerned consumers.
5. Human-in-the-Loop Support: Strategic overrides must be available to validate agentic decisions before mass execution in the Execution Layer.

8. Implementation Conclusion

This mapping provides the mathematical mandate for autonomous, ROI-positive customer retention. By converting raw features of the Bank Marketing Dataset into a formal X-learner schema, RetentionOS moves beyond late-stage churn detection into proactive, agent-based persuasion. This framework enables the system’s Agentic Intelligence to select the optimal retention strategy—balancing discount depth against channel effectiveness—while maintaining the strict profit guardrails necessary to maximize long-term customer lifetime value.
