"""
CRAG Compliance Agent — end-to-end test.
Ingest embedded policy only → run full pipeline → print trace → assert pass criteria.
Run from backend/: python test.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from models.compliance_models import InterventionPayload
from services.rag.ingestor import ingest_from_text
from services.rag.compliance_service import run_compliance_check
from services.agents.compliance_agent import run_compliance_graph
from utils.supabase_client import get_supabase_client
from utils.llm import get_llm

POLICY_DOC = "company_retention_policy"
# Legacy test doc — cleared so retrieval only hits company_retention_policy
LEGACY_DOC = "test_discount_policy"

POLICY_TEXT = """
Company Retention Discount Policy (Test Document)

Section 1 — Authorized Discount Levels
Subscribers may receive promotional discounts between 5% and 20% inclusive.
Discounts above 20% require executive approval.

Section 2 — Eligibility
All active subscribers with expected intervention profit above $500 are eligible
for standard retention discounts.

Section 3 — Profit Requirements
Interventions with expected profit of at least $800 at a 15% discount level
are automatically approved when the subscriber is in good standing.

Section 4 — Compliance
Discount offers must be documented in the customer record. Maximum one retention
offer per subscriber per 90-day period.
"""

RETRIEVAL_QUESTION = (
    "Are 15% discounts allowed for subscriber user_id 99 with expected profit $800?"
)

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
            print(f"[FAIL] {key} is missing or not configured.")
            ok = False
        else:
            print(f"[OK] {key} configured.")

    cohere = os.getenv("COHERE_API_KEY", "")
    if not cohere or cohere == "your_cohere_api_key_here":
        print("[WARN] COHERE_API_KEY missing — reranker will use RRF-only fallback.")
    else:
        print("[OK] COHERE_API_KEY configured.")
    return ok


def ingest_policy(supabase) -> int:
    """Test-only ingest: clear noise docs, store embedded retention policy only."""
    print("\n--- Ingest: company_retention_policy only (test mode) ---")
    for doc in (LEGACY_DOC, POLICY_DOC):
        supabase.table("policy_chunks").delete().eq("doc_name", doc).execute()
        print(f"[Ingest] Cleared prior chunks for '{doc}'.")

    count = ingest_from_text(POLICY_TEXT, POLICY_DOC, supabase)
    print(f"[Ingest] Stored {count} chunk(s) for '{POLICY_DOC}'.")
    return count


def print_trace(trace: dict) -> None:
    print("\n--- Pipeline Trace ---")
    print(f"Retrieval question: {RETRIEVAL_QUESTION}")
    print("\nGenerated queries:")
    for i, q in enumerate(trace.get("queries", []), start=1):
        print(f"  {i}. {q}")

    print(f"\nRaw chunks retrieved: {len(trace.get('raw_chunks', []))}")
    for c in trace.get("raw_chunks", [])[:3]:
        print(f"  - [{c.get('doc_name')}] sim={c.get('similarity', 0):.3f} | {c['chunk_text'][:80]}...")

    print(f"\nFused top chunks: {len(trace.get('fused_chunks', []))}")
    for c in trace.get("fused_chunks", []):
        score = c.get("rerank_score") or c.get("rrf_score") or c.get("similarity", 0)
        print(f"  - [{c.get('doc_name')}] score={score} | {c['chunk_text'][:80]}...")

    print(f"\nGraded relevant chunks: {len(trace.get('graded_chunks', []))}")
    for c in trace.get("graded_chunks", []):
        print(f"  - RELEVANT: {c.get('relevance_explanation', 'N/A')}")

    print("\nReasoning trace:")
    print(trace.get("reasoning_trace", "(none)")[:800])
    print("..." if len(trace.get("reasoning_trace", "")) > 800 else "")


def self_rate_result(result, trace: dict) -> None:
    llm = get_llm(model_name="gpt-4o-mini", temperature=0.0)
    prompt = f"""You are evaluating a compliance RAG system output.

Retrieval question: {RETRIEVAL_QUESTION}
Test payload: user_id=99, best_discount=15%, expected_profit=800

System output:
- intervene: {result.intervene}
- policy_source: {result.policy_source}
- confidence: {result.confidence}
- reasoning: {result.reasoning}

Chunks graded relevant: {len(trace.get('graded_chunks', []))}

Rate this system response 1-10 for quality and explain why in 2-3 sentences.
Respond JSON only: {{"score": int, "explanation": "..."}}"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        print("\n--- Agent Self-Rating ---")
        print(response.content)
    except Exception as e:
        print(f"[WARN] Self-rating failed: {e}")


def assert_pass_criteria(result, trace: dict) -> None:
    assert result is not None, "ComplianceResult is empty"
    assert result.reasoning and len(result.reasoning) > 20, "Reasoning is too short"
    assert result.policy_source, "policy_source must be set"
    assert 1 <= result.confidence <= 10, "confidence must be 1-10"
    assert len(trace.get("graded_chunks", [])) > 0, (
        "Expected relevant graded chunks from company_retention_policy"
    )
    assert result.intervene is True, (
        "Test policy approves 15% / $800 profit — expected intervene=True"
    )
    assert result.policy_source.lower() != "none", (
        "policy_source must cite a document when intervene is true"
    )
    assert "reasoning_trace" in trace and len(trace["reasoning_trace"]) > 50, (
        "Full pipeline should produce a reasoning trace (steps 5–6)"
    )

    print("\n[PASS] All success criteria met (approval path).")
    print(f"  intervene={result.intervene}")
    print(f"  policy_source={result.policy_source}")
    print(f"  confidence={result.confidence}")


def main() -> None:
    print("=" * 60)
    print("CRAG Compliance Agent — End-to-End Test")
    print("=" * 60)

    if not validate_environment():
        sys.exit(1)

    supabase = get_supabase_client()
    ingest_policy(supabase)

    print("\n--- Run: Full CRAG pipeline (compliance_service) ---")
    result, trace = run_compliance_check(TEST_PAYLOAD, supabase)
    print_trace(trace)
    self_rate_result(result, trace)
    assert_pass_criteria(result, trace)

    print("\n--- Run: LangGraph compliance node ---")
    graph_state = run_compliance_graph(TEST_PAYLOAD)
    graph_result = graph_state.get("compliance_result")
    assert graph_result is not None
    assert graph_state.get("should_intervene") == graph_result.intervene
    print(f"[OK] LangGraph state: should_intervene={graph_state['should_intervene']}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE — CRAG pipeline operational")
    print("=" * 60)


if __name__ == "__main__":
    main()
