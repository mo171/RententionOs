"""
Reranker: Cohere cross-encoder rerank + Reciprocal Rank Fusion (RRF)
across multiple query result lists.
"""
import os
import cohere
from dotenv import load_dotenv

load_dotenv()

_cohere_client = None

def _get_cohere_client() -> cohere.Client:
    global _cohere_client
    if _cohere_client is None:
        api_key = os.getenv("COHERE_API_KEY", "")
        _cohere_client = cohere.Client(api_key=api_key)
    return _cohere_client


def cohere_rerank(
    primary_query: str,
    chunks: list[dict],
    top_n: int = 5,
) -> list[dict]:
    """
    Uses Cohere rerank-english-v3.0 to score all chunks against
    the primary query, then returns the top_n highest-scored chunks.
    Falls back to original order if Cohere key is missing.
    """
    if not os.getenv("COHERE_API_KEY") or os.getenv("COHERE_API_KEY") == "your_cohere_api_key_here":
        print("[Reranker] No Cohere API key — skipping rerank, using similarity order.")
        return chunks[:top_n]

    client = _get_cohere_client()
    documents = [c["chunk_text"] for c in chunks]

    if not documents:
        return []

    response = client.rerank(
        model="rerank-english-v3.0",
        query=primary_query,
        documents=documents,
        top_n=min(top_n, len(documents)),
    )

    reranked = []
    for result in response.results:
        chunk = dict(chunks[result.index])  # copy original chunk
        chunk["rerank_score"] = result.relevance_score
        reranked.append(chunk)

    return reranked


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    k: int = 60,
    top_n: int = 5,
) -> list[dict]:
    """
    Fuses multiple ranked lists using Reciprocal Rank Fusion (RRF).
    Formula: score(d) = sum(1 / (k + rank_i(d))) across all lists.

    Deduplicates chunks by chunk_text before scoring.
    Returns top_n unique chunks sorted by fused score descending.
    """
    scores: dict[str, float] = {}
    chunk_registry: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list, start=1):
            key = chunk["chunk_text"]
            scores[key] = scores.get(key, 0.0) + (1.0 / (k + rank))
            chunk_registry[key] = chunk

    sorted_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)

    fused = []
    for key in sorted_keys[:top_n]:
        chunk = dict(chunk_registry[key])
        chunk["rrf_score"] = scores[key]
        fused.append(chunk)

    return fused


def rerank_and_fuse(
    primary_query: str,
    all_chunks: list[dict],
    query_grouped: list[list[dict]],
    top_n: int = 5,
    rrf_pool_size: int = 10,
) -> list[dict]:
    """
    Full rerank + fusion pipeline:
    1. RRF fuses per-query ranked lists into a candidate pool
    2. Cohere reranks that pool against the primary query for final top_n
    """
    print("[Reranker] Applying Reciprocal Rank Fusion across query groups...")
    rrf_candidates = reciprocal_rank_fusion(query_grouped, top_n=rrf_pool_size)

    if not rrf_candidates:
        print("[Reranker] No RRF candidates - falling back to flat chunk list.")
        rrf_candidates = all_chunks[:rrf_pool_size]

    print(f"[Reranker] Cohere reranking {len(rrf_candidates)} RRF candidates...")
    final = cohere_rerank(primary_query, rrf_candidates, top_n=top_n)
    print(f"[Reranker] Final top {len(final)} chunks selected.")
    return final
