"""
Compliance Service: Orchestrates the full 6-step CRAG pipeline for Node 1.
"""
import json
from langchain_core.messages import HumanMessage

from prompts.compliance_prompts import (
    MULTI_QUERY_PROMPT,
    REASONING_PROMPT,
    FINAL_VERDICT_PROMPT,
)
from models.compliance_models import (
    InterventionPayload,
    ComplianceResult,
)
from services.rag.retriever import retrieve_multi_query
from services.rag.reranker import rerank_and_fuse
from services.rag.grader import grade_chunks
from utils.llm import get_llm


def _parse_json_response(raw: str) -> dict | list:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def _format_chunks_for_prompt(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        doc = chunk.get("doc_name", "unknown")
        parts.append(f"[Chunk {i} | {doc}]\n{chunk['chunk_text']}")
    return "\n\n".join(parts)


def generate_queries(payload: InterventionPayload) -> list[str]:
    """Step 1: LLM generates 3 distinct policy search queries."""
    llm = get_llm(model_name="gpt-4o-mini", temperature=0.0)
    prompt = MULTI_QUERY_PROMPT.format(
        user_id=payload.user_id,
        best_discount=payload.best_discount,
        expected_profit=payload.expected_profit,
    )
    print("[Compliance] Step 1: Generating multi-queries...")
    response = llm.invoke([HumanMessage(content=prompt)])
    queries = _parse_json_response(response.content)
    if not isinstance(queries, list) or len(queries) < 1:
        raise ValueError(f"Expected JSON array of queries, got: {queries}")
    queries = [str(q) for q in queries[:3]]
    for i, q in enumerate(queries, start=1):
        print(f"  Query {i}: {q}")
    return queries


def generate_reasoning_trace(
    payload: InterventionPayload,
    graded_chunks: list[dict],
) -> str:
    """Step 5: Verbose chain-of-thought for UI display."""
    llm = get_llm(model_name="gpt-4o", temperature=0.0)
    prompt = REASONING_PROMPT.format(
        user_id=payload.user_id,
        best_discount=payload.best_discount,
        expected_profit=payload.expected_profit,
        relevant_chunks=_format_chunks_for_prompt(graded_chunks),
    )
    print("[Compliance] Step 5: Generating reasoning trace...")
    response = llm.invoke([HumanMessage(content=prompt)])
    trace = response.content.strip()
    print(f"[Compliance] Reasoning trace ({len(trace)} chars):")
    print(trace[:500] + ("..." if len(trace) > 500 else ""))
    return trace


def generate_verdict(
    reasoning_trace: str,
    graded_chunks: list[dict],
) -> ComplianceResult:
    """Step 6: Structured final compliance verdict."""
    llm = get_llm(model_name="gpt-4o-mini", temperature=0.0)
    doc_name = graded_chunks[0].get("doc_name", "unknown") if graded_chunks else "none"
    prompt = FINAL_VERDICT_PROMPT.format(
        reasoning_trace=reasoning_trace,
        relevant_chunks=_format_chunks_for_prompt(graded_chunks),
        doc_name=doc_name,
    )
    print("[Compliance] Step 6: Generating final verdict...")
    response = llm.invoke([HumanMessage(content=prompt)])
    data = _parse_json_response(response.content)
    return ComplianceResult(**data)


def run_compliance_check(
    payload: InterventionPayload,
    supabase_client,
) -> tuple[ComplianceResult, dict]:
    """
    Runs the full CRAG pipeline. Returns (ComplianceResult, trace_dict).
    trace_dict holds intermediate state for LangGraph / test output.
    """
    trace: dict = {"payload": payload.model_dump()}

    queries = generate_queries(payload)
    trace["queries"] = queries
    primary_query = queries[0]
    trace["primary_query"] = primary_query

    print("[Compliance] Step 2: Vector retrieval...")
    raw_chunks, query_grouped = retrieve_multi_query(
        queries, supabase_client, top_k_per_query=3
    )
    trace["raw_chunks"] = raw_chunks
    print(f"  Retrieved {len(raw_chunks)} unique chunks across {len(queries)} queries.")

    print("[Compliance] Step 3: Rerank + RRF fusion...")
    fused_chunks = rerank_and_fuse(
        primary_query=primary_query,
        all_chunks=raw_chunks,
        query_grouped=query_grouped,
        top_n=5,
    )
    trace["fused_chunks"] = fused_chunks
    print(f"  Fused to top {len(fused_chunks)} chunks.")

    print("[Compliance] Step 4: Relevance grading...")
    graded_chunks = grade_chunks(primary_query, fused_chunks)
    trace["graded_chunks"] = graded_chunks

    if not graded_chunks:
        print("[Compliance] HARD STOP: No relevant policy chunks found.")
        result = ComplianceResult(
            intervene=False,
            reasoning=(
                f"No relevant company policy was found for subscriber {payload.user_id} "
                f"regarding a {payload.best_discount} discount offer. "
                "Intervention cannot be approved without policy backing."
            ),
            policy_source="none",
            confidence=1,
        )
        trace["reasoning_trace"] = result.reasoning
        trace["compliance_result"] = result.model_dump()
        return result, trace

    reasoning_trace = generate_reasoning_trace(payload, graded_chunks)
    trace["reasoning_trace"] = reasoning_trace

    result = generate_verdict(reasoning_trace, graded_chunks)
    trace["compliance_result"] = result.model_dump()

    print("[Compliance] Final verdict:")
    print(f"  intervene: {result.intervene}")
    print(f"  policy_source: {result.policy_source}")
    print(f"  confidence: {result.confidence}")
    print(f"  reasoning: {result.reasoning}")

    return result, trace
