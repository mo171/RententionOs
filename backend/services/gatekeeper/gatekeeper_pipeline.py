from typing import Any, Dict, List, Optional
import pandas as pd
import json
import traceback

from services.ltv.ltv_service import score_customer as score_ltv_customer
from services.churn.churn_service import score_customer as score_churn_customer
from services.causal.uplift_service import score_customer as score_causal_customer
from models.compliance_models import InterventionPayload
from inngest_client import inngest_client

# ────────────────────────────────────────────────────────────────────────────
# Gatekeeper Configuration Constants
# ────────────────────────────────────────────────────────────────────────────

LTV_THRESHOLD = 0.2  # Predictive 12-month LTV threshold
CHURN_THRESHOLD = 0.5  # Churn probability threshold for high-risk
PROFIT_THRESHOLD = 0.0  # Minimum expected profit to intervene
MIN_UPLIFT_THRESHOLD = 0.0  # Minimum uplift for "Persuadable"


def _validate_customer_record(customer: Dict[str, Any]) -> bool:
    """Validate that a customer record has required fields."""
    required_fields = ["id", "user_id", "segment"]
    # At least one id field must exist
    if not (customer.get("id") or customer.get("user_id")):
        return False
    return True


def _extract_user_id(customer: Dict[str, Any]) -> int:
    """Safely extract user_id from customer record."""
    user_id = customer.get("user_id") or customer.get("id")
    if isinstance(user_id, str):
        try:
            return int(user_id)
        except ValueError:
            return hash(user_id) % (2**31)
    return int(user_id) if user_id else 0


def process_gatekeeper_pipeline(
    customers: List[Dict[str, Any]], 
    trigger_inngest: bool = False,
    dry_run: bool = False,
) -> tuple[List[InterventionPayload], Dict[str, int]]:
    """
    Run the full Gatekeeper ML pipeline:
    Layer 2: LTV Gate -> 
    Layer 3: Churn Filter -> 
    Layer 4: Causal Uplift & Treatment Optimizer -> 
    Ingress Payload
    
    Returns:
        - payloads: List of InterventionPayload objects passed all gates
        - stats: Dict with filtering statistics
    """
    payloads = []
    stats = {
        "total_customers": len(customers),
        "ltv_filter_passed": 0,
        "churn_filter_passed": 0,
        "uplift_passed": 0,
        "profit_threshold_passed": 0,
        "errors": 0,
    }
    
    for i, customer in enumerate(customers):
        try:
            # Validate customer record
            if not _validate_customer_record(customer):
                print(f"[Gatekeeper] Customer {i} validation failed — skipping.")
                continue
                
            user_id = _extract_user_id(customer)
            
            # ──────────────────────────────────────────────────────────────
            # Layer 2: LTV Eligibility Gate
            # ──────────────────────────────────────────────────────────────
            try:
                ltv_response = score_ltv_customer(customer)
            except Exception as e:
                print(f"[Gatekeeper] LTV scoring failed for user {user_id}: {str(e)}")
                stats["errors"] += 1
                continue
                
            if not ltv_response.is_eligible_for_retention:
                print(f"[Gatekeeper] User {user_id} failed LTV eligibility check.")
                continue
                
            if (ltv_response.predictive_12m_ltv or 0) <= LTV_THRESHOLD:
                print(f"[Gatekeeper] User {user_id} LTV too low: {ltv_response.predictive_12m_ltv}")
                continue
                
            stats["ltv_filter_passed"] += 1
            
            # ──────────────────────────────────────────────────────────────
            # Layer 3: Churn Risk Filter
            # ──────────────────────────────────────────────────────────────
            try:
                churn_response = score_churn_customer(customer)
            except Exception as e:
                print(f"[Gatekeeper] Churn scoring failed for user {user_id}: {str(e)}")
                stats["errors"] += 1
                continue
                
            if (churn_response.churn_probability or 0) < CHURN_THRESHOLD:
                print(f"[Gatekeeper] User {user_id} churn risk too low: {churn_response.churn_probability}")
                continue
                
            stats["churn_filter_passed"] += 1
            
            # ──────────────────────────────────────────────────────────────
            # Layer 4: Causal Uplift & Treatment Optimizer
            # ──────────────────────────────────────────────────────────────
            try:
                causal_response = score_causal_customer(
                    customer, 
                    clv=ltv_response.predictive_12m_ltv
                )
            except Exception as e:
                print(f"[Gatekeeper] Causal scoring failed for user {user_id}: {str(e)}")
                stats["errors"] += 1
                continue
            
            # Only pass Persuadables: where uplift score > 0
            if causal_response.segment != "Persuadables":
                print(f"[Gatekeeper] User {user_id} segment not 'Persuadables': {causal_response.segment}")
                continue
                
            if (causal_response.uplift_score or 0) <= MIN_UPLIFT_THRESHOLD:
                print(f"[Gatekeeper] User {user_id} uplift score too low: {causal_response.uplift_score}")
                continue
                
            stats["uplift_passed"] += 1
            
            # ──────────────────────────────────────────────────────────────
            # Treatment Optimizer Decision
            # ──────────────────────────────────────────────────────────────
            best_treatment = causal_response.best_treatment
            if not best_treatment:
                print(f"[Gatekeeper] User {user_id} no treatment recommendation.")
                continue
                
            expected_profit = best_treatment.expected_profit or 0
            if expected_profit <= PROFIT_THRESHOLD:
                print(f"[Gatekeeper] User {user_id} expected profit <= threshold: {expected_profit}")
                continue
                
            stats["profit_threshold_passed"] += 1
            
            # ──────────────────────────────────────────────────────────────
            # Build Intervention Payload
            # ──────────────────────────────────────────────────────────────
            payload = InterventionPayload(
                user_id=user_id,
                best_discount=best_treatment.treatment,
                expected_profit=expected_profit,
                ltv=ltv_response.predictive_12m_ltv,
                churn_prob=churn_response.churn_probability,
                uplift_score=causal_response.uplift_score,
                recommended_incentive=best_treatment.treatment,
                segment=customer.get("segment", "Unknown")
            )
            payloads.append(payload)
            print(f"[Gatekeeper] ✓ User {user_id} passed all gates. Expected profit: ${expected_profit:.2f}")
            
            # ──────────────────────────────────────────────────────────────
            # Trigger Inngest Workflow
            # ──────────────────────────────────────────────────────────────
            if trigger_inngest and not dry_run:
                try:
                    inngest_client.send_sync({
                        "name": "gatekeeper/process.retention",
                        "data": payload.model_dump()
                    })
                    print(f"[Gatekeeper] → Inngest event queued for user {user_id}")
                except Exception as e:
                    print(f"[Gatekeeper] Failed to queue Inngest event: {str(e)}")
                    
        except Exception as e:
            print(f"[Gatekeeper] Unexpected error processing customer {i}: {str(e)}")
            traceback.print_exc()
            stats["errors"] += 1
    
    print(f"\n[Gatekeeper Summary]")
    print(f"  Total processed: {stats['total_customers']}")
    print(f"  LTV filter: {stats['ltv_filter_passed']}")
    print(f"  Churn filter: {stats['churn_filter_passed']}")
    print(f"  Uplift filter: {stats['uplift_passed']}")
    print(f"  Profit filter: {stats['profit_threshold_passed']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Final payloads: {len(payloads)}\n")
    
    return payloads, stats
