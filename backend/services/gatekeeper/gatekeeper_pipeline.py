from typing import Any, Dict, List
import pandas as pd
import json

from services.ltv.ltv_service import score_customer as score_ltv_customer
from services.churn.churn_service import score_customer as score_churn_customer
from services.causal.uplift_service import score_customer as score_causal_customer
from models.compliance_models import InterventionPayload
from inngest_client import inngest_client

def process_gatekeeper_pipeline(customers: List[Dict[str, Any]], trigger_inngest: bool = False) -> List[InterventionPayload]:
    """
    Run the full Gatekeeper ML pipeline:
    LTV Gate -> Churn Filter -> Causal Uplift -> Treatment Optimizer -> Ingress Payload
    """
    payloads = []
    
    for customer in customers:
        user_id = customer.get("id", customer.get("user_id", hash(str(customer))))
        
        # 1. LTV Gate
        ltv_response = score_ltv_customer(customer)
        if not ltv_response.is_eligible_for_retention or ltv_response.predictive_12m_ltv <= 0.2:
            continue
            
        # 2. Churn Filter
        churn_response = score_churn_customer(customer)
        if churn_response.churn_probability < 0.5: # Example threshold for moderate-high risk
            continue
            
        # 3. Causal Uplift & Treatment Optimizer
        causal_response = score_causal_customer(
            customer, 
            clv=ltv_response.predictive_12m_ltv
        )
        
        # Filter only Persuadables
        if causal_response.segment != "Persuadables":
            continue
            
        best_treatment = causal_response.best_treatment
        if not best_treatment or best_treatment.expected_profit <= 0:
            continue
            
        # 4. Build Ingress Payload
        payload = InterventionPayload(
            user_id=user_id,
            best_discount=best_treatment.treatment,
            expected_profit=best_treatment.expected_profit,
            ltv=ltv_response.predictive_12m_ltv,
            churn_prob=churn_response.churn_probability,
            uplift_score=causal_response.uplift_score,
            recommended_incentive=best_treatment.treatment,
            segment=customer.get("segment")
        )
        payloads.append(payload)
        
        # 5. Trigger Inngest Event
        if trigger_inngest:
            inngest_client.send_sync({
                "name": "gatekeeper/process.retention",
                "data": payload.model_dump()
            })
            print(f"[Gatekeeper] Triggered Inngest for User {user_id}")
            
    return payloads
