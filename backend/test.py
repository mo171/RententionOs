"""
Full pipeline demo: Compliance -> Strategy -> Writer <-> Reviewer -> Dispatch (email).

Requires:
  OPENAI_API_KEY, SUPABASE_*, COHERE_API_KEY (optional)
  RESEND_API_KEY, RESEND_FROM_EMAIL (verified domain)
  TEST_RECIPIENT_EMAIL=movindsouza79@gmail.com
  FORCE_EMAIL_CHANNEL=true
  TEST_MODE=true

Run: python test.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from models.compliance_models import InterventionPayload, ComplianceResult
from models.strategy_models import StrategyResult
from models.message_models import MessageDraft, ReviewResult, SendMessageResult
from services.rag.ingestor import ingest_from_text
from services.agents.intervention_graph import run_intervention_graph
from utils.supabase_client import get_supabase_client

POLICY_DOC = "company_retention_policy"
POLICY_TEXT = """
Company Retention Discount Policy (Test Document)
Section 1 - Authorized Discount Levels: 5% to 20% inclusive.
Section 3 - Interventions with expected profit at least $800 at 15% are automatically approved.
"""

TEST_PAYLOAD = InterventionPayload(user_id=99, best_discount="15%", expected_profit=800.0)


def validate_environment() -> bool:
    load_dotenv()
    os.environ.setdefault("FORCE_EMAIL_CHANNEL", "true")
    os.environ.setdefault("TEST_MODE", "true")
    os.environ.setdefault("TEST_RECIPIENT_EMAIL", "movindsouza79@gmail.com")

    ok = True
    for key in ("OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        if not os.getenv(key) or "your_" in os.getenv(key, ""):
            print(f"[FAIL] {key}")
            ok = False
        else:
            print(f"[OK] {key}")

    for key in ("RESEND_API_KEY", "RESEND_FROM_EMAIL"):
        if not os.getenv(key) or "your_" in os.getenv(key, ""):
            print(f"[WARN] {key} missing — email send will fail")
        else:
            print(f"[OK] {key}")

    print(f"[OK] TEST_RECIPIENT_EMAIL={os.getenv('TEST_RECIPIENT_EMAIL')}")
    return ok


def setup(supabase):
    for doc in ("test_discount_policy", POLICY_DOC, "debug_policy"):
        supabase.table("policy_chunks").delete().eq("doc_name", doc).execute()
    ingest_from_text(POLICY_TEXT, POLICY_DOC, supabase)


def print_results(state: dict):
    cr = state.get("compliance_result")
    if isinstance(cr, dict):
        cr = ComplianceResult(**cr)
    sr = state.get("strategy_result")
    if isinstance(sr, dict):
        sr = StrategyResult(**sr)
    draft = state.get("current_draft")
    if isinstance(draft, dict):
        draft = MessageDraft(**draft)
    review = state.get("last_review")
    if isinstance(review, dict):
        review = ReviewResult(**review)
    send = state.get("send_result")
    if isinstance(send, dict):
        send = SendMessageResult(**send)

    print("\n" + "=" * 60)
    print("FULL PIPELINE RESULT")
    print("=" * 60)
    print("\nNode 1 Compliance:", "APPROVED" if cr and cr.intervene else "DENIED")
    if cr:
        print(f"  policy: {cr.policy_source} | confidence: {cr.confidence}")
    print("\nNode 2 Strategy:")
    if sr:
        print(f"  channel: {sr.channel} | scheduled: {sr.scheduled_time}")
    print("\nNode 3 Writer draft:")
    if draft:
        print(f"  subject: {draft.subject}")
        print(f"  cta: {draft.cta_text}")
        print(f"  body (snippet): {draft.body_plain[:120]}...")
    print("\nNode 4 Reviewer:")
    print(f"  revisions: {state.get('revision_count', 0)}")
    if review:
        print(f"  approved: {review.approved} | score: {review.score}/10")
        print(f"  feedback: {review.feedback[:120]}...")
    print("\nDispatch (send_message):")
    if send:
        print(f"  success: {send.success} | provider: {send.provider} | id: {send.message_id}")
        if send.error:
            print(f"  error: {send.error}")
    print("=" * 60)


def assert_success(state: dict):
    assert state.get("should_intervene") is True
    draft = state.get("current_draft")
    if isinstance(draft, dict):
        draft = MessageDraft(**draft)
    assert draft is not None
    assert draft.channel == "Email"
    assert draft.body_html

    send = state.get("send_result")
    if isinstance(send, dict):
        send = SendMessageResult(**send)
    assert send is not None, "Dispatch must run"
    assert send.success, f"Email send failed: {send.error}"
    assert send.provider == "resend"
    print("\n[SUCCESS] Full pipeline including email send.")
    print(f"  Check inbox: {os.getenv('TEST_RECIPIENT_EMAIL')}")


def main():
    print("RetentionOS - Full 4-Node Pipeline + Email Send")
    if not validate_environment():
        sys.exit(1)

    supabase = get_supabase_client()
    setup(supabase)

    print("\n[Run] LangGraph full graph...")
    state = run_intervention_graph(TEST_PAYLOAD)
    print_results(state)
    assert_success(state)


if __name__ == "__main__":
    main()
