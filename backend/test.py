"""
Demo: Full intervention pipeline with APPROVED outcome (intervene=True + strategy).

Run from backend/: python test.py

Shows:
  1. Compliance (CRAG) approves the discount
  2. Strategy picks channel + send time for subscriber 99
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from models.compliance_models import InterventionPayload, ComplianceResult
from models.strategy_models import StrategyResult
from services.rag.ingestor import ingest_from_text
from services.agents.intervention_graph import run_intervention_graph
from utils.supabase_client import get_supabase_client

POLICY_DOC = "company_retention_policy"

POLICY_TEXT = """
Company Retention Discount Policy (Test Document)

Section 1 - Authorized Discount Levels
Subscribers may receive promotional discounts between 5% and 20% inclusive.
Discounts above 20% require executive approval.

Section 2 - Eligibility
All active subscribers with expected intervention profit above $500 are eligible
for standard retention discounts.

Section 3 - Profit Requirements
Interventions with expected profit of at least $800 at a 15% discount level
are automatically approved when the subscriber is in good standing.

Section 4 - Compliance
Discount offers must be documented in the customer record. Maximum one retention
offer per subscriber per 90-day period.
"""

TEST_PAYLOAD = InterventionPayload(
    user_id=99,
    best_discount="15%",
    expected_profit=800.0,
)


def validate_environment() -> bool:
    load_dotenv()
    ok = True
    for key in ("OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        val = os.getenv(key, "")
        if not val or "your_" in val:
            print(f"[FAIL] {key} missing.")
            ok = False
        else:
            print(f"[OK] {key}")
    return ok


def setup_test_data(supabase) -> None:
    print("\n[Setup] Ingest policy + verify subscriber 99")
    for doc in ("test_discount_policy", POLICY_DOC, "debug_policy"):
        supabase.table("policy_chunks").delete().eq("doc_name", doc).execute()
    n = ingest_from_text(POLICY_TEXT, POLICY_DOC, supabase)
    print(f"  Policy chunks stored: {n}")

    sub = supabase.table("subscribers").select("user_id, full_name").eq("user_id", 99).execute()
    if not sub.data:
        raise RuntimeError("Run migrations/003_subscribers_and_interactions.sql first.")
    print(f"  Subscriber: {sub.data[0]['full_name']} (user_id=99)")


def print_final_results(state: dict) -> None:
    cr = state.get("compliance_result")
    if isinstance(cr, dict):
        cr = ComplianceResult(**cr)
    sr = state.get("strategy_result")
    if isinstance(sr, dict):
        sr = StrategyResult(**sr)

    profile = state.get("subscriber_profile") or {}

    print("\n" + "=" * 60)
    print("FINAL PIPELINE RESULT (what downstream agents / UI receive)")
    print("=" * 60)

    print("\n--- ML input (unchanged through graph) ---")
    print(json.dumps(TEST_PAYLOAD.model_dump(), indent=2))

    print("\n--- Node 1: Compliance (CRAG) ---")
    if cr:
        print(f"  intervene:       {cr.intervene}")
        print(f"  policy_source:   {cr.policy_source}")
        print(f"  confidence:      {cr.confidence}/10")
        print(f"  reasoning:       {cr.reasoning}")
    else:
        print("  (no compliance_result)")

    print("\n--- Node 2: Strategy (channel + timing) ---")
    if sr:
        print(f"  channel:         {sr.channel}")
        print(f"  scheduled_time:  {sr.scheduled_time}")
        print(f"  confidence:      {sr.confidence}/10")
        print(f"  reasoning:       {sr.reasoning}")
    else:
        print("  (strategy skipped - intervene was False)")

    print("\n--- Subscriber context used by strategist ---")
    print(f"  name:            {profile.get('full_name')}")
    print(f"  preferred:       {profile.get('preferred_channel')}")
    print(f"  timezone:        {profile.get('timezone')}")
    print(f"  events_loaded:   {len(state.get('interaction_history') or [])}")

    print("\n--- Graph flags ---")
    print(f"  should_intervene: {state.get('should_intervene')}")
    print("=" * 60)


def assert_approved_path(state: dict) -> None:
    assert state.get("should_intervene") is True, "Expected compliance to approve (intervene=True)"

    cr = state.get("compliance_result")
    if isinstance(cr, dict):
        cr = ComplianceResult(**cr)
    assert cr and cr.intervene is True
    assert cr.policy_source.lower() != "none"

    sr = state.get("strategy_result")
    if isinstance(sr, dict):
        sr = StrategyResult(**sr)
    assert sr is not None, "Strategy must run when intervene=True"

    scheduled = datetime.fromisoformat(sr.scheduled_time.replace("Z", "+00:00"))
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)
    assert scheduled > datetime.now(timezone.utc)

    assert sr.channel in {"Email", "SMS", "Push Notification"}
    print("\n[SUCCESS] Pipeline approved intervention and produced strategy plan.")


def main() -> None:
    print("=" * 60)
    print("RetentionOS - Approved Intervention Demo (user 99, 15% discount)")
    print("=" * 60)

    if not validate_environment():
        sys.exit(1)

    supabase = get_supabase_client()
    setup_test_data(supabase)

    print("\n[Run] LangGraph: compliance -> (if approved) strategy")
    state = run_intervention_graph(TEST_PAYLOAD)

    print_final_results(state)
    assert_approved_path(state)


if __name__ == "__main__":
    main()
