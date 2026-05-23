# %%
# ==========================================
# CELL 1: ENVIRONMENT & INITIALIZATION
# ==========================================
# !pip install shap category_encoders lightgbm xgboost -q

import numpy as np
import pandas as pd
import uuid
import random
import matplotlib.pyplot as plt
import seaborn as sns
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output

# Machine Learning & Optimization Libraries
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from category_encoders import TargetEncoder
import xgboost as xgb
import lightgbm as lgb
import shap

# Set deterministic seeds for exact reproducibility across execution runs
np.random.seed(42)
random.seed(42)


# %%
# ==========================================
# CELL 2: SYNTHETIC INDIAN BANKING PIPELINE (10K RECORDS)
# ==========================================
def generate_indian_banking_dataset(num_records=10000):
    segments = ['Student', 'Low-Income/Jan Dhan', 'Salaried Middle-Class', 'MSME/Entrepreneur', 'HNI']
    segment_weights = [0.15, 0.25, 0.40, 0.15, 0.05]

    data = []

    for _ in range(num_records):
        cust_id = str(uuid.uuid4())
        segment = np.random.choice(segments, p=segment_weights)

        # Establish Segment-Specific Financial Anchors
        if segment == 'Student':
            income_range = (5000, 25000)
            stability_loc, stability_scale = 0.4, 0.15
            bureau_range = (300, 650)
            upi_ratio = random.uniform(0.70, 0.95)
            cc_ratio = random.uniform(0.00, 0.05)
            aum_base = random.uniform(1000, 15000)
            loan_interest_paid = 0.0

        elif segment == 'Low-Income/Jan Dhan':
            income_range = (8000, 35000)
            stability_loc, stability_scale = 0.5, 0.2
            bureau_range = (450, 700)
            upi_ratio = random.uniform(0.50, 0.85)
            cc_ratio = 0.0
            aum_base = random.uniform(500, 8000)
            loan_interest_paid = random.uniform(0, 1200)

        elif segment == 'Salaried Middle-Class':
            income_range = (40000, 180000)
            stability_loc, stability_scale = 0.9, 0.05
            bureau_range = (680, 850)
            upi_ratio = random.uniform(0.30, 0.60)
            cc_ratio = random.uniform(0.20, 0.50)
            aum_base = random.uniform(50000, 600000)
            loan_interest_paid = random.uniform(15000, 120000)

        elif segment == 'MSME/Entrepreneur':
            income_range = (60000, 500000)
            stability_loc, stability_scale = 0.6, 0.25
            bureau_range = (600, 820)
            upi_ratio = random.uniform(0.40, 0.70)
            cc_ratio = random.uniform(0.10, 0.40)
            aum_base = random.uniform(100000, 1500000)
            loan_interest_paid = random.uniform(50000, 350000)

        elif segment == 'HNI':
            income_range = (600000, 5000000)
            stability_loc, stability_scale = 0.85, 0.1
            bureau_range = (750, 900)
            upi_ratio = random.uniform(0.10, 0.30)
            cc_ratio = random.uniform(0.50, 0.80)
            aum_base = random.uniform(2500000, 40000000)
            loan_interest_paid = random.uniform(100000, 800000)

        avg_monthly_income = float(np.random.uniform(income_range[0], income_range[1]))
        income_stability_score = float(np.clip(np.random.normal(stability_loc, stability_scale), 0.01, 1.0))

        avg_monthly_spend = avg_monthly_income * random.uniform(0.40, 0.90)
        spend_variability = random.uniform(0.05, 0.45)

        bureau_score = int(np.random.randint(bureau_range[0], bureau_range[1]))
        credit_utilization = float(0.0 if cc_ratio == 0 else np.clip(np.random.beta(2, 5), 0.0, 1.0))

        repayment_base = (bureau_score - 300) / 600.0
        repayment_score = float(np.clip(repayment_base - random.uniform(-0.1, 0.15), 0.0, 1.0))

        app_logins_30d = int(np.random.poisson(lam=12 if segment in ['Student', 'Salaried Middle-Class'] else 5))
        distinct_products_used = int(random.randint(1, 3) if segment in ['Student', 'Low-Income/Jan Dhan'] else random.randint(3, 7))

        bounce_count_3m = int(np.random.choice([0, 1, 2, 3], p=[0.88, 0.08, 0.03, 0.01]))
        if repayment_score < 0.5:
            bounce_count_3m += random.randint(1, 2)

        is_fraudster = int(np.random.choice([0, 1], p=[0.996, 0.004]))

        fee_income = (avg_monthly_spend * cc_ratio * 0.018) + random.uniform(100, 1500)
        servicing_cost = float(random.uniform(150, 600))

        data.append({
            'customer_id': cust_id, 'segment_tag': segment, 'aa_consent_linked': random.choice([True, False]),
            'avg_monthly_income_inr': round(avg_monthly_income, 2), 'income_stability_score': round(income_stability_score, 4),
            'avg_monthly_spend_inr': round(avg_monthly_spend, 2), 'spend_variability': round(spend_variability, 4),
            'upi_transaction_ratio': round(upi_ratio, 4), 'cc_transaction_ratio': round(cc_ratio, 4),
            'bureau_score': bureau_score, 'credit_utilization_ratio': round(credit_utilization, 4),
            'repayment_score': round(repayment_score, 4), 'bounce_count_3m': bounce_count_3m,
            'wealth_liquidity_aum_inr': round(aum_base, 2), 'app_logins_30d': app_logins_30d,
            'distinct_products_used': distinct_products_used, 'loan_interest_paid_12m': round(loan_interest_paid, 2),
            'fee_income_earned_12m': round(fee_income, 2), 'servicing_cost_12m': round(servicing_cost, 2),
            'is_fraudster': is_fraudster
        })

    return pd.DataFrame(data)

raw_df = generate_indian_banking_dataset(10000)

# %%
# ==========================================
# CELL 3: FEATURE ENGINEERING & TARGET MATRIX EXTRACTION
# ==========================================
def execute_feature_engineering(df):
    processed_df = df.copy()

    # Compute Historical Lifetime Value
    processed_df['ltv_historical_12m'] = (
        processed_df['loan_interest_paid_12m'] + processed_df['fee_income_earned_12m']
    ) - processed_df['servicing_cost_12m']

    # Build Behavioral & Composite Risk Indexes
    processed_df['risk_composite_index'] = (
        (1.0 - processed_df['repayment_score']) * 0.40 +
        (processed_df['bounce_count_3m'] / 5.0) * 0.40 +
        (processed_df['credit_utilization_ratio'] * 0.20)
    )

    processed_df['engagement_score'] = (
        (processed_df['app_logins_30d'] / 35.0) * 0.50 +
        (processed_df['distinct_products_used'] / 7.0) * 0.50
    ).clip(0.0, 1.0)

    # Future Targets
    trend_factor = np.random.normal(1.08, 0.05, size=len(processed_df))
    processed_df['target_future_ltv_12m'] = processed_df['ltv_historical_12m'] * trend_factor

    processed_df['target_default_risk'] = np.where(
        (processed_df['repayment_score'] < 0.45) & (processed_df['bounce_count_3m'] >= 2) |
        (processed_df['is_fraudster'] == 1), 1, 0
    )

    return processed_df

engineered_df = execute_feature_engineering(raw_df)


# %%
# ==========================================
# CELL 4: DATA QUALITY AUDIT
# ==========================================
def run_banking_data_quality_audit(df):
    print("STARTING ENTERPRISE DATA QUALITY AUDIT\n" + "=" * 60)
    validation_passed = True

    if df.isnull().sum().sum() > 0:
        print("FAIL: Found missing cells inside feature space."); validation_passed = False
    else: print("PASS: Zero missing values detected across columns.")

    if df['customer_id'].duplicated().sum() > 0:
        print("FAIL: Duplicate customer_id collision keys found."); validation_passed = False
    else: print("PASS: Primary constraint index keys are completely unique.")

    low_inc_cc_leak = df[(df['segment_tag'] == 'Low-Income/Jan Dhan') & (df['cc_transaction_ratio'] > 0)]
    if len(low_inc_cc_leak) > 0:
        print(f"FAIL: Underwriting Leak! Low-income users found with card transactional histories."); validation_passed = False
    else: print("PASS: Credit card isolation parameters for Jan Dhan verified.")

    invalid_bureau = df[(df['bureau_score'] < 300) | (df['bureau_score'] > 900)]
    if len(invalid_bureau) > 0:
        print("FAIL: Out-of-bounds Bureau Scores found."); validation_passed = False
    else: print("PASS: Credit bureau files scale strictly inside the Indian 300-900 framework.")

    print("=" * 60 + f"\nSTATUS: {'PASSED CLEANLY' if validation_passed else 'CRITICAL RE-AUDIT REQUIRED'}\n" + "=" * 60)
    return validation_passed

is_clean = run_banking_data_quality_audit(engineered_df)

# %%
# ==========================================
# CELL 5: DATA MATRICES SEPARATION & SAFE ENCODING
# ==========================================
print("CELL 5: ISOLATING FEATURE MATRICES & DATA SPLITTING")
print("=" * 60)

model_features = [
    'segment_tag_encoded', 'avg_monthly_income_inr', 'income_stability_score',
    'avg_monthly_spend_inr', 'spend_variability', 'upi_transaction_ratio',
    'cc_transaction_ratio', 'bureau_score', 'credit_utilization_ratio',
    'repayment_score', 'bounce_count_3m', 'wealth_liquidity_aum_inr',
    'engagement_score', 'risk_composite_index'
]

X_raw = engineered_df.drop(columns=['target_future_ltv_12m', 'target_default_risk'])
y_ltv = engineered_df['target_future_ltv_12m']

X_train_raw, X_test_raw, y_train, y_test = train_test_split(X_raw, y_ltv, test_size=0.2, random_state=42)

# Leakage Protection: Target Encode segment tags strictly inside split limits
encoder = TargetEncoder(cols=['segment_tag'])
X_train_raw['segment_tag_encoded'] = encoder.fit_transform(X_train_raw['segment_tag'], y_train)
X_test_raw['segment_tag_encoded'] = encoder.transform(X_test_raw['segment_tag'])

X_train = X_train_raw[model_features]
X_test = X_test_raw[model_features]

# Scale arrays for core benchmarks
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"Balanced Training Matrix Features Shape : {X_train.shape}")
print(f"Testing Evaluation Matrix Shape       : {X_test.shape}")

# %%
# ==========================================
# CELL 6: MACHINE LEARNING REVENUE MODEL COMPETITION
# ==========================================

print("=" * 60)
model_perf = {}

# Model 1: LightGBM Regressor
lgb_train = lgb.Dataset(X_train, label=y_train)
lgb_test = lgb.Dataset(X_test, label=y_test, reference=lgb_train)

lgb_params = {
    'objective': 'regression', 'metric': 'rmse', 'boosting_type': 'gbdt',
    'learning_rate': 0.05, 'num_leaves': 31, 'max_depth': 6, 'verbose': -1, 'random_state': 42
}
lgb_mdl = lgb.train(lgb_params, lgb_train, num_boost_round=500, valid_sets=[lgb_test], callbacks=[lgb.early_stopping(50, verbose=False)])
y_pred_lgb = lgb_mdl.predict(X_test)

model_perf['LightGBM'] = {
    'MAE': mean_absolute_error(y_test, y_pred_lgb), 'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_lgb)), 'R2': r2_score(y_test, y_pred_lgb)
}

# Model 2: XGBoost Regressor
xgb_mdl = xgb.XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8, random_state=42)
xgb_mdl.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
y_pred_xgb = xgb_mdl.predict(X_test)

model_perf['XGBoost'] = {
    'MAE': mean_absolute_error(y_test, y_pred_xgb), 'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_xgb)), 'R2': r2_score(y_test, y_pred_xgb)
}

# Generate Results Summary Table
performance_df = pd.DataFrame(model_perf).T
print("\n" + "="*60 + "\nMULTI-MODEL PREDICTIVE COMPARISON DASHBOARD\n" + "="*60)
print(performance_df.to_string(formatters={'MAE': '₹{:,.2f}'.format, 'RMSE': '₹{:,.2f}'.format, 'R2': '{:.4f}'.format}))
print("="*60)

# %%
# ==========================================
# CELL 7: RISK ENGINE & SHAP AUDITING
# ==========================================
print("\nCELL 7: RISK MODELING ENGINE & BIAS ATTRIBUTION")
print("=" * 60)

y_cls = engineered_df['target_default_risk']
X_full_encoded = X_raw.copy()
X_full_encoded['segment_tag_encoded'] = encoder.transform(X_full_encoded['segment_tag'])
X_features_full = X_full_encoded[model_features]

X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X_features_full, y_cls, test_size=0.2, stratify=y_cls, random_state=42)

scale_weight_ratio = (y_train_c == 0).sum() / (y_train_c == 1).sum()

risk_model = xgb.XGBClassifier(
    n_estimators=300, max_depth=5, learning_rate=0.05,
    scale_pos_weight=scale_weight_ratio, objective='binary:logistic', eval_metric='logloss', random_state=42
)
risk_model.fit(X_train_c, y_train_c, eval_set=[(X_test_c, y_test_c)], verbose=False)

# Assign global predictions cleanly back onto baseline dataset space
engineered_df['predicted_future_ltv_12m'] = lgb_mdl.predict(X_features_full)
engineered_df['probability_of_default'] = risk_model.predict_proba(X_features_full)[:, 1]

explainer = shap.TreeExplainer(risk_model)
shap_values = explainer(X_test_c)

print("Plotting SHAP Summary Matrix to isolate default driving elements:")
plt.figure(figsize=(10, 5))
shap.summary_plot(shap_values, X_test_c, show=False)
plt.title("Regulatory Audit: SHAP Explainer Values for Default Risk Models", fontsize=12, pad=15)
plt.tight_layout()
plt.show()

# %%
# ==========================================
# CELL 8: CALCULATING SCORECARD STRATIFICATIONS (CFVS)
# ==========================================
print("\nCELL 8: COMPILING COMPONENT STRATIFICATIONS & SYNTHESIZING CFVS VALUES")
print("=" * 60)

# FIX: Switch to log-transformed scaling arrays to eliminate absolute asset distortion
engineered_df['log_ltv_hist'] = np.log1p(engineered_df['ltv_historical_12m'].clip(lower=0))
engineered_df['log_ltv_pred'] = np.log1p(engineered_df['predicted_future_ltv_12m'].clip(lower=0))

m_scaler = MinMaxScaler(feature_range=(0, 100))
engineered_df['norm_ltv_hist'] = m_scaler.fit_transform(engineered_df[['log_ltv_hist']])
engineered_df['norm_ltv_pred'] = m_scaler.fit_transform(engineered_df[['log_ltv_pred']])
engineered_df['norm_engagement'] = m_scaler.fit_transform(engineered_df[['engagement_score']])

def compute_cfvs_score(row):
    if row['is_fraudster'] == 1 or row['bounce_count_3m'] > 3 or row['bureau_score'] < 500:
        return 0.0

    segment = row['segment_tag']
    w = {
        'Low-Income/Jan Dhan':   {'w_h': 0.10, 'w_p': 0.20, 'w_b': 0.40, 'w_r': 0.30},
        'Student':               {'w_h': 0.05, 'w_p': 0.55, 'w_b': 0.25, 'w_r': 0.15},
        'Salaried Middle-Class': {'w_h': 0.30, 'w_p': 0.30, 'w_b': 0.20, 'w_r': 0.20},
        'MSME/Entrepreneur':     {'w_h': 0.35, 'w_p': 0.25, 'w_b': 0.15, 'w_r': 0.25},
        'HNI':                   {'w_h': 0.50, 'w_p': 0.30, 'w_b': 0.10, 'w_r': 0.10}
    }[segment]

    base_value = (w['w_h'] * row['norm_ltv_hist']) + (w['w_p'] * row['norm_ltv_pred']) + (w['w_b'] * row['norm_engagement'])
    final_score = base_value * (1.0 - (w['w_r'] * row['probability_of_default']))

    return float(np.clip(final_score, 0.0, 100.0))

engineered_df['CFVS'] = engineered_df.apply(compute_cfvs_score, axis=1)
print("CFVS Score Arrays calculated across multi-segment population vectors.")

# %%
# ==========================================
# CELL 9: DYNAMIC PERCENTILE DECISION LAYER
# ==========================================

print("=" * 60)

# Calculate dynamic distribution boundaries based on the current run's population
cfvs_distribution = engineered_df[engineered_df['CFVS'] > 0.0]['CFVS']

# Map boundaries to actual statistical tiers
tier_low_cutoff = float(cfvs_distribution.quantile(0.35))   # Top 65% get nurtured/approved
tier_high_cutoff = float(cfvs_distribution.quantile(0.75))  # Top 25% get auto-approved

print(f"Calibration Complete for this Data Run:")
print(f"   -> Auto-Approval Threshold (Top 25%): CFVS >= {tier_high_cutoff:.2f}")
print(f"   -> Nurture/Cross-Sell Threshold (Top 65%): CFVS >= {tier_low_cutoff:.2f}")

def execution_decision_engine_dynamic(row):
    cfvs = row['CFVS']
    pd_risk = row['probability_of_default']

    if cfvs == 0.0 or pd_risk > 0.65:
        return "CRITICAL RISK FREEZE: Deny Credit / Trigger Manual Account Compliance Audit"
    elif cfvs >= tier_high_cutoff:
        return "AUTO-APPROVAL TRIGGER: Pre-approved Personal Loan / Instant Credit Upgrades Eligible"
    elif cfvs >= tier_low_cutoff:
        return "NURTURE / CROSS-SELL: Target Standard Credit Cards & SIP Investment Offers"
    else:
        return "MANUAL REVIEW REJECT: Traditional Micro-Lending Assessment Required"

# Re-apply calibrated decisions to the feature store
engineered_df['automated_action_strategy'] = engineered_df.apply(execution_decision_engine_dynamic, axis=1)

# Plot updated distributions
plt.figure(figsize=(11, 5))
sns.histplot(data=engineered_df, x='CFVS', hue='segment_tag', multiple='stack', bins=45, palette='tab10')
plt.axvline(tier_low_cutoff, color='orange', linestyle='--', linewidth=2, label=f'Nurture Cutoff ({tier_low_cutoff:.1f})')
plt.axvline(tier_high_cutoff, color='green', linestyle='--', linewidth=2, label=f'Auto-Approve Cutoff ({tier_high_cutoff:.1f})')
plt.title("Distribution of CFVS with Calibrated Decision Boundaries", fontsize=12, fontweight='bold')
plt.xlabel("CFVS Score Range (0 - 100)", fontsize=10)
plt.ylabel("Customer Volume Count", fontsize=10)
plt.legend()
plt.grid(axis='y', alpha=0.25)
plt.tight_layout()
plt.show()

# %%
# ==========================================
# CELL 10: PRIVACY PROTECTION VAULT (DPDP COMPLIANCE)
# ==========================================
print("\nCELL 10: DPDP ACT COMPLIANCE SECURITY CONSTRAINTS")
print("=" * 60)

engineered_df['raw_customer_fullname'] = [f"Bank_Customer_Record_{i}" for i in range(len(engineered_df))]
engineered_df['raw_aadhaar_masked_uid'] = [f"XXXX-XXXX-{random.randint(1000,9999)}" for _ in range(len(engineered_df))]

dpdp_compliance_token_vault = engineered_df[['customer_id', 'raw_customer_fullname', 'raw_aadhaar_masked_uid', 'segment_tag']].copy()
production_feature_store = engineered_df.drop(columns=['raw_customer_fullname', 'raw_aadhaar_masked_uid'])

print(f"Vault Separation Isolation Complete. Production Feature Store Row Total: {len(production_feature_store)}")
print("Compliance Alert: Identity keys isolated. Underwriting modeling is running 100% anonymized.")
print("=" * 60)

# %%
# ==========================================
# CELL 11: INTERACTIVE USER ENGINE INTERFACE
# ==========================================
style = {'description_width': 'initial'}

profile_name_input = widgets.Text(value="Rajesh Kumar", description="Customer Name:", style=style)
segment_input = widgets.Dropdown(
    options=['Student', 'Low-Income/Jan Dhan', 'Salaried Middle-Class', 'MSME/Entrepreneur', 'HNI'],
    value='Salaried Middle-Class', description='Customer Segment Tier:', style=style
)
income_input = widgets.FloatText(value=45000.0, description="Monthly Income (₹):", style=style)
spend_input = widgets.FloatText(value=22000.0, description="Monthly Spend (₹):", style=style)
bureau_input = widgets.IntSlider(value=780, min=300, max=900, step=1, description="CIBIL Bureau Score:", style=style)
bounces_input = widgets.Dropdown(options=[0, 1, 2, 3, 4], value=0, description="Cheque/EMI Bounces (Past 3M):", style=style)
aum_input = widgets.FloatText(value=35000.0, description="Savings & FD Balance (₹):", style=style)
logins_input = widgets.IntSlider(value=14, min=0, max=30, step=1, description="Mobile App Logins (Past 30 Days):", style=style)

run_button = widgets.Button(description="Process Financial Assessment", button_style='primary', layout=widgets.Layout(width='350px'))
output_panel = widgets.Output()

def get_segment_encoding_live(segment_name):
    try:
        encoded_val = encoder.transform(pd.DataFrame([{'segment_tag': segment_name}]))['segment_tag_encoded'].iloc[0]
        return encoded_val
    except Exception:
        return 1.0

def compute_interactive_inference(b):
    with output_panel:
        clear_output()

        user_segment = segment_input.value
        user_income = income_input.value
        user_spend = spend_input.value
        user_bureau = bureau_input.value
        user_bounces = bounces_input.value
        user_aum = aum_input.value
        user_logins = logins_input.value

        # Dynamically derive missing features using the exact anchors from generation phase
        upi_ratio = 0.80 if user_segment in ['Student', 'Low-Income/Jan Dhan'] else 0.40
        cc_ratio = 0.00 if user_segment == 'Low-Income/Jan Dhan' else (0.50 if user_segment == 'HNI' else 0.30)
        stability = 0.90 if user_segment == 'Salaried Middle-Class' else 0.60
        utilization = 0.35 if cc_ratio > 0 else 0.00

        repayment_calc = np.clip((user_bureau - 300) / 600.0 - (user_bounces * 0.15), 0.0, 1.0)
        risk_composite = (1.0 - repayment_calc) * 0.40 + (user_bounces / 5.0) * 0.40 + (utilization * 0.20)
        engagement = ((user_logins / 35.0) * 0.50 + (4 / 7.0) * 0.50)

        input_data = pd.DataFrame([{
            'segment_tag_encoded': get_segment_encoding_live(user_segment),
            'avg_monthly_income_inr': user_income,
            'income_stability_score': stability,
            'avg_monthly_spend_inr': user_spend,
            'spend_variability': 0.15,
            'upi_transaction_ratio': upi_ratio,
            'cc_transaction_ratio': cc_ratio,
            'bureau_score': user_bureau,
            'credit_utilization_ratio': utilization,
            'repayment_score': repayment_calc,
            'bounce_count_3m': user_bounces,
            'wealth_liquidity_aum_inr': user_aum,
            'engagement_score': engagement,
            'risk_composite_index': risk_composite
        }])

        # Generate Real Predictions using Deployed Framework Models
        predicted_value_inr = lgb_mdl.predict(input_data)[0]
        default_risk_probability = risk_model.predict_proba(input_data)[:, 1][0]

        # FIX: Implement Logarithmic Scaling Bounds tracking Cell 8 updates
        hist_min = np.log1p(max(0, production_feature_store['ltv_historical_12m'].min()))
        hist_max = np.log1p(production_feature_store['ltv_historical_12m'].max())
        pred_min = np.log1p(max(0, production_feature_store['predicted_future_ltv_12m'].min()))
        pred_max = np.log1p(production_feature_store['predicted_future_ltv_12m'].max())

        estimated_hist = (user_income * 0.12) + (user_aum * 0.02)
        log_estimated_hist = np.log1p(max(0, estimated_hist))
        log_predicted_value = np.log1p(max(0, predicted_value_inr))

        norm_hist = np.clip(((log_estimated_hist - hist_min) / (hist_max - hist_min)) * 100, 0, 100)
        norm_pred = np.clip(((log_predicted_value - pred_min) / (pred_max - pred_min)) * 100, 0, 100)
        norm_engagement = np.clip(engagement * 100, 0, 100)

        weights = {
            'Low-Income/Jan Dhan':   {'w_h': 0.10, 'w_p': 0.20, 'w_b': 0.40, 'w_r': 0.30},
            'Student':               {'w_h': 0.05, 'w_p': 0.55, 'w_b': 0.25, 'w_r': 0.15},
            'Salaried Middle-Class': {'w_h': 0.30, 'w_p': 0.30, 'w_b': 0.20, 'w_r': 0.20},
            'MSME/Entrepreneur':     {'w_h': 0.35, 'w_p': 0.25, 'w_b': 0.15, 'w_r': 0.25},
            'HNI':                   {'w_h': 0.50, 'w_p': 0.30, 'w_b': 0.10, 'w_r': 0.10}
        }[user_segment]

        score_base = (weights['w_h'] * norm_hist) + (weights['w_p'] * norm_pred) + (weights['w_b'] * norm_engagement)
        customer_health_score = float(np.clip(score_base * (1.0 - (weights['w_r'] * default_risk_probability)), 0.0, 100.0))

        # Core Knockout Policy Rules Overrides
        # Core Knockout Policy Rules Overrides
        if user_bounces > 3 or user_bureau < 500:
            customer_health_score = 0.0

        # FIX: Match live ui feedback to the dynamically calculated population quantiles
        if customer_health_score == 0.0 or default_risk_probability > 0.65:
            decision_text = "CRITICAL RISK REJECT: Deny Credit Applications. Account flag raised for active delinquency review."
            alert_color = "#f8d7da"; text_color = "#721c24"
        elif customer_health_score >= tier_high_cutoff:
            decision_text = "AUTOMATED IMMEDIATE APPROVAL: Customer is eligible for pre-approved credit extensions and premium upgrades."
            alert_color = "#d4edda"; text_color = "#155724"
        elif customer_health_score >= tier_low_cutoff:
            decision_text = "STANDARD CROSS-SELL ROUTE: Eligible for foundational retail cards and structured mutual fund / SIP recommendations."
            alert_color = "#fff3cd"; text_color = "#856404"
        else:
            decision_text = "MANUAL RISK ASSESSMENT REQUIRED: Score sits below automated thresholds. Route to local branch credit officer."
            alert_color = "#e2e3e5"; text_color = "#383d41"

        html_output = f"""
        <div style='font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ccc; border-radius: 8px; margin-top: 15px;'>
            <h3 style='margin-top: 0; color: #333;'>Account Evaluation Summary: {profile_name_input.value}</h3>
            <table style='width: 100%; border-collapse: collapse; margin-bottom: 15px;'>
                <tr style='background-color: #f9f9f9;'>
                    <td style='padding: 8px; font-weight: bold; border-bottom: 1px solid #ddd;'>Customer Financial Health Score (CFVS):</td>
                    <td style='padding: 8px; border-bottom: 1px solid #ddd; font-size: 16px; font-weight: bold;'>{customer_health_score:.1f} / 100</td>
                </tr>
                <tr>
                    <td style='padding: 8px; font-weight: bold; border-bottom: 1px solid #ddd;'>Projected 12-Month Future Value:</td>
                    <td style='padding: 8px; border-bottom: 1px solid #ddd; font-size: 14px;'>₹{predicted_value_inr:,.2f}</td>
                </tr>
                <tr style='background-color: #f9f9f9;'>
                    <td style='padding: 8px; font-weight: bold; border-bottom: 1px solid #ddd;'>Calculated Default Probability:</td>
                    <td style='padding: 8px; border-bottom: 1px solid #ddd; font-size: 14px;'>{default_risk_probability * 100:.2f}%</td>
                </tr>
            </table>
            <div style='padding: 15px; background-color: {alert_color}; color: {text_color}; border-radius: 5px; font-weight: bold;'>
                System Underwriting Directive:<br>
                <span style='font-weight: normal; font-size: 14px;'>{decision_text}</span>
            </div>
        </div>
        """
        display(HTML(html_output))

run_button.on_click(compute_interactive_inference)

input_ui = widgets.VBox([
    widgets.HTML("<h2>System Underwriting & Value Core Interface</h2>"),
    profile_name_input, segment_input, income_input, spend_input,
    bureau_input, bounces_input, aum_input, logins_input,
    widgets.HTML("<br>"), run_button
])

display(widgets.HBox([input_ui, output_panel]))

# %%



