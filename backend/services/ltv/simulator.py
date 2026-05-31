"""
Synthetic BFSI Data Simulator — Phase 1
Generates 10,000 realistic customer profiles split into five Indian banking
archetypes to validate the Gatekeeper ML pipeline.

Archetypes:
  1. Students — High digital engagement, low balance
  2. Jan Dhan / Low-Income — Heavy UPI reliance, zero credit cards
  3. Salaried Middle-Class — Steady income, standard credit usage
  4. MSME Owners — Fluctuating income, high loan interest
  5. HNIs — Multi-crore balances and high monthly income

Feature Spec (IDEA 2.0 Section 5):
  - upi_frequency_drop: float [0, 1] — drop in UPI transaction frequency
  - app_login_decay: float [0, 1] — decay in app login frequency
  - life event flags: job_change (bool), relocation (bool)
"""

import json
import math
import os
import random
from typing import Any

# ────────────────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────────────────

SEGMENTS = ["Student", "Jan Dhan", "Salaried Middle-Class", "MSME", "HNI"]
SEGMENT_WEIGHTS = [0.15, 0.25, 0.40, 0.15, 0.05]

DEFAULT_NUM_PROFILES = 10_000
DEFAULT_SEED = 42

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
OUTPUT_JSON_PATH = os.path.join(OUTPUT_DIR, "synthetic_bfsi_profiles.json")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _poisson(rng: random.Random, lam: float) -> int:
    limit = math.exp(-lam)
    k = 0
    product = 1.0
    while product > limit:
        k += 1
        product *= rng.random()
    return k - 1


# ────────────────────────────────────────────────────────────────────────────
# Per-archetype feature anchors
# ────────────────────────────────────────────────────────────────────────────

def _student_anchors(rng: random.Random) -> dict[str, Any]:
    return {
        "income_range": (5_000, 25_000),
        "balance_range": (100, 5_000),
        "stability_loc": 0.4,
        "stability_scale": 0.15,
        "bureau_range": (300, 650),
        "upi_ratio": rng.uniform(0.70, 0.95),
        "cc_ratio": rng.uniform(0.00, 0.05),
        "cc_count": rng.choices([0, 1], weights=[0.9, 0.1])[0],
        "aum_base": rng.uniform(1_000, 15_000),
        "loan_interest_paid": 0.0,
        "loan_interest_rate": 0.0,
        "app_logins_lam": 18,  # High digital engagement
        "products_range": (1, 3),
        # IDEA 2.0 features
        "upi_freq_drop_range": (0.2, 0.8),
        "app_login_decay_range": (0.3, 0.9),
        "job_change_prob": 0.08,
        "relocation_prob": 0.12,
    }


def _jandhan_anchors(rng: random.Random) -> dict[str, Any]:
    return {
        "income_range": (8_000, 35_000),
        "balance_range": (0, 10_000),
        "stability_loc": 0.5,
        "stability_scale": 0.2,
        "bureau_range": (450, 700),
        "upi_ratio": rng.uniform(0.50, 0.85),
        "cc_ratio": 0.0,
        "cc_count": 0,
        "aum_base": rng.uniform(500, 8_000),
        "loan_interest_paid": rng.uniform(0, 1_200),
        "loan_interest_rate": rng.uniform(0, 4.0),
        "app_logins_lam": 4,
        "products_range": (1, 2),
        # IDEA 2.0 features — heavy UPI reliance makes drop significant
        "upi_freq_drop_range": (0.4, 0.9),
        "app_login_decay_range": (0.0, 0.3),
        "job_change_prob": 0.05,
        "relocation_prob": 0.08,
    }


def _salaried_anchors(rng: random.Random) -> dict[str, Any]:
    return {
        "income_range": (40_000, 180_000),
        "balance_range": (10_000, 500_000),
        "stability_loc": 0.9,
        "stability_scale": 0.05,
        "bureau_range": (680, 850),
        "upi_ratio": rng.uniform(0.30, 0.60),
        "cc_ratio": rng.uniform(0.20, 0.50),
        "cc_count": rng.randint(1, 3),
        "aum_base": rng.uniform(50_000, 600_000),
        "loan_interest_paid": rng.uniform(15_000, 120_000),
        "loan_interest_rate": rng.uniform(7.0, 11.0),
        "app_logins_lam": 12,
        "products_range": (3, 7),
        "upi_freq_drop_range": (0.0, 0.4),
        "app_login_decay_range": (0.0, 0.5),
        "job_change_prob": 0.10,
        "relocation_prob": 0.06,
    }


def _msme_anchors(rng: random.Random) -> dict[str, Any]:
    return {
        "income_range": (60_000, 500_000),
        "balance_range": (50_000, 2_000_000),
        "stability_loc": 0.6,
        "stability_scale": 0.25,
        "bureau_range": (600, 820),
        "upi_ratio": rng.uniform(0.40, 0.70),
        "cc_ratio": rng.uniform(0.10, 0.40),
        "cc_count": rng.randint(1, 5),
        "aum_base": rng.uniform(100_000, 1_500_000),
        "loan_interest_paid": rng.uniform(50_000, 350_000),
        "loan_interest_rate": rng.uniform(8.0, 14.0),
        "app_logins_lam": 6,
        "products_range": (3, 6),
        "upi_freq_drop_range": (0.1, 0.7),
        "app_login_decay_range": (0.1, 0.6),
        "job_change_prob": 0.03,
        "relocation_prob": 0.04,
    }


def _hni_anchors(rng: random.Random) -> dict[str, Any]:
    return {
        "income_range": (600_000, 5_000_000),
        "balance_range": (2_000_000, 50_000_000),
        "stability_loc": 0.85,
        "stability_scale": 0.1,
        "bureau_range": (750, 900),
        "upi_ratio": rng.uniform(0.10, 0.30),
        "cc_ratio": rng.uniform(0.50, 0.80),
        "cc_count": rng.randint(2, 10),
        "aum_base": rng.uniform(2_500_000, 40_000_000),
        "loan_interest_paid": rng.uniform(100_000, 800_000),
        "loan_interest_rate": rng.uniform(6.5, 10.0),
        "app_logins_lam": 5,
        "products_range": (4, 7),
        "upi_freq_drop_range": (0.0, 0.2),
        "app_login_decay_range": (0.0, 0.2),
        "job_change_prob": 0.02,
        "relocation_prob": 0.02,
    }


_ANCHOR_MAP = {
    "Student": _student_anchors,
    "Jan Dhan": _jandhan_anchors,
    "Salaried Middle-Class": _salaried_anchors,
    "MSME": _msme_anchors,
    "HNI": _hni_anchors,
}


# ────────────────────────────────────────────────────────────────────────────
# Profile generation
# ────────────────────────────────────────────────────────────────────────────

def _generate_one_profile(index: int, rng: random.Random) -> dict[str, Any]:
    """Generate a single synthetic BFSI customer profile."""
    segment = rng.choices(SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]
    anchors = _ANCHOR_MAP[segment](rng)

    income = rng.uniform(*anchors["income_range"])
    balance = rng.uniform(*anchors["balance_range"])
    stability = _clamp(rng.gauss(anchors["stability_loc"], anchors["stability_scale"]), 0.01, 1.0)
    spend = income * rng.uniform(0.40, 0.90)
    bureau_score = rng.randint(*anchors["bureau_range"])

    credit_utilization = 0.0 if anchors["cc_ratio"] == 0 else _clamp(rng.betavariate(2, 5), 0.0, 1.0)
    repayment_base = (bureau_score - 300) / 600.0
    repayment_score = _clamp(repayment_base - rng.uniform(-0.1, 0.15), 0.0, 1.0)

    app_logins = _poisson(rng, anchors["app_logins_lam"])
    products = rng.randint(*anchors["products_range"])
    bounce_count = rng.choices([0, 1, 2, 3], weights=[0.88, 0.08, 0.03, 0.01], k=1)[0]
    if repayment_score < 0.5:
        bounce_count += rng.randint(1, 2)

    is_fraudster = 1 if rng.random() < 0.004 else 0
    fee_income = (spend * anchors["cc_ratio"] * 0.018) + rng.uniform(100, 1500)
    servicing_cost = rng.uniform(150, 600)

    # ── IDEA 2.0 Section 5 features ──
    upi_frequency_drop = round(rng.uniform(*anchors["upi_freq_drop_range"]), 4)
    app_login_decay = round(rng.uniform(*anchors["app_login_decay_range"]), 4)
    job_change = 1 if rng.random() < anchors["job_change_prob"] else 0
    relocation = 1 if rng.random() < anchors["relocation_prob"] else 0

    # ── Derived engagement / risk ──
    engagement_score = _clamp(
        (app_logins / 35.0) * 0.50 + (products / 7.0) * 0.50,
        0.0, 1.0,
    )
    risk_composite = (
        (1.0 - repayment_score) * 0.40
        + (bounce_count / 5.0) * 0.40
        + credit_utilization * 0.20
    )
    historical_ltv = (
        anchors["loan_interest_paid"]
        + fee_income
        - servicing_cost
    )

    # ── Churn proxy (mirrors generate_synthetic_data.py logic) ──
    churn_risk = 0.0
    if job_change == 1:
        churn_risk += 0.2
    if relocation == 1:
        churn_risk += 0.3
    if upi_frequency_drop > 0.4:
        churn_risk += 0.2
    if app_login_decay > 0.5:
        churn_risk += 0.2
    if balance < 1000:
        churn_risk += 0.1
    if segment == "HNI":
        churn_risk -= 0.3
    churn_proxy = _clamp(0.3 + churn_risk, 0.05, 0.95)

    return {
        "id": index + 1,
        "user_id": index + 1,
        "customer_id": f"sim_bfsi_{index + 1:05d}",
        "segment": segment,
        # Core banking
        "avg_monthly_income_inr": round(income, 2),
        "income_stability_score": round(stability, 4),
        "avg_monthly_spend_inr": round(spend, 2),
        "spend_variability": round(rng.uniform(0.05, 0.45), 4),
        "balance": round(balance, 2),
        "bureau_score": bureau_score,
        "credit_utilization_ratio": round(credit_utilization, 4),
        "repayment_score": round(repayment_score, 4),
        "bounce_count_3m": bounce_count,
        # Channels
        "upi_transaction_ratio": round(anchors["upi_ratio"], 4),
        "cc_transaction_ratio": round(anchors["cc_ratio"], 4),
        "credit_card_count": anchors["cc_count"],
        # Wealth and products
        "wealth_liquidity_aum_inr": round(anchors["aum_base"], 2),
        "avg_monthly_balance": round(balance * rng.uniform(0.8, 1.2), 2),
        "app_logins_30d": app_logins,
        "distinct_products_used": products,
        "loan_interest_paid_12m": round(anchors["loan_interest_paid"], 2),
        "loan_interest_rate": round(anchors["loan_interest_rate"], 2),
        "fee_income_earned_12m": round(fee_income, 2),
        "servicing_cost_12m": round(servicing_cost, 2),
        "is_fraudster": is_fraudster,
        # IDEA 2.0 Section 5
        "upi_frequency_drop": upi_frequency_drop,
        "app_login_decay": app_login_decay,
        "job_change": job_change,
        "relocation": relocation,
        # Derived
        "engagement_score": round(engagement_score, 4),
        "risk_composite_index": round(risk_composite, 4),
        "ltv_historical_12m": round(historical_ltv, 2),
        "churn_proxy": round(churn_proxy, 4),
    }


def generate_bfsi_profiles(
    num_profiles: int = DEFAULT_NUM_PROFILES,
    seed: int = DEFAULT_SEED,
) -> list[dict[str, Any]]:
    """
    Generate `num_profiles` synthetic BFSI customer records.

    Returns a list of dicts, each containing every field the
    Gatekeeper pipeline and /approvals UI expect.
    """
    rng = random.Random(seed)
    return [_generate_one_profile(i, rng) for i in range(num_profiles)]


def save_profiles_json(
    profiles: list[dict[str, Any]] | None = None,
    output_path: str = OUTPUT_JSON_PATH,
) -> str:
    """Generate profiles (if not provided) and write to JSON."""
    if profiles is None:
        profiles = generate_bfsi_profiles()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)
    print(f"[Simulator] Wrote {len(profiles)} profiles to {output_path}")
    return output_path


def get_segment_summary(profiles: list[dict[str, Any]]) -> dict[str, int]:
    """Return a count of profiles per segment."""
    counts: dict[str, int] = {}
    for p in profiles:
        seg = p.get("segment", "Unknown")
        counts[seg] = counts.get(seg, 0) + 1
    return counts


# ────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    profiles = generate_bfsi_profiles()
    path = save_profiles_json(profiles)
    summary = get_segment_summary(profiles)
    print(f"[Simulator] Segment distribution: {summary}")
    print(f"[Simulator] Sample profile keys: {list(profiles[0].keys())}")
