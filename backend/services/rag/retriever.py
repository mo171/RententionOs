"""
Retriever: Runs similarity search against Supabase pgvector.
Uses the offline all-MiniLM-L6-v2 model for query embedding.
"""
import json
import math
from services.rag.ingestor import embed_texts


def _parse_embedding(raw) -> list[float]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [float(x) for x in raw]
    if isinstance(raw, str):
        return [float(x) for x in json.loads(raw)]
    return []


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _retrieve_chunks_local(
    query_embedding: list[float],
    supabase_client,
    top_k: int,
    match_threshold: float,
) -> list[dict]:
    """Fallback when RPC/IVFFlat returns nothing (common with tiny corpora)."""
    response = supabase_client.table("policy_chunks").select(
        "chunk_text, doc_name, embedding"
    ).execute()
    scored = []
    for row in response.data or []:
        emb = _parse_embedding(row.get("embedding"))
        sim = _cosine_similarity(query_embedding, emb)
        if sim > match_threshold:
            scored.append(
                {
                    "chunk_text": row["chunk_text"],
                    "doc_name": row.get("doc_name", "unknown"),
                    "similarity": sim,
                }
            )
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


def retrieve_chunks(
    query: str,
    supabase_client,
    top_k: int = 3,
    match_threshold: float = 0.1,
) -> list[dict]:
    """
    Embeds a single query and retrieves the top-k most similar chunks
    from Supabase policy_chunks via pgvector cosine similarity.

    Returns a list of dicts: { chunk_text, doc_name, similarity }
    """
    query_embedding = embed_texts([query])[0]

    # Call the Supabase RPC function (match_policy_chunks defined in migration)
    response = supabase_client.rpc(
        "match_policy_chunks",
        {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": top_k,
        }
    ).execute()

    results = response.data or []
    if not results:
        results = _retrieve_chunks_local(
            query_embedding, supabase_client, top_k, match_threshold
        )
        if results:
            print("[Retriever] RPC empty - used local cosine fallback.")
        elif match_threshold > 0:
            results = _retrieve_chunks_local(
                query_embedding, supabase_client, top_k, 0.0
            )
    return [
        {
            "chunk_text": r["chunk_text"],
            "doc_name": r.get("doc_name", "unknown"),
            "similarity": r.get("similarity", 0.0),
        }
        for r in results
    ]


def retrieve_multi_query(
    queries: list[str],
    supabase_client,
    top_k_per_query: int = 3,
) -> tuple[list[dict], list[list[dict]]]:
    """
    Runs retrieval for each query and returns:
    - flat deduplicated chunks (by chunk_text)
    - per-query ranked lists for RRF fusion
    """
    query_grouped: list[list[dict]] = []
    seen_texts: set[str] = set()
    flat_results: list[dict] = []

    for i, query in enumerate(queries):
        chunks = retrieve_chunks(query, supabase_client, top_k=top_k_per_query)
        per_query: list[dict] = []
        for chunk in chunks:
            tagged = dict(chunk)
            tagged["query_index"] = i
            per_query.append(tagged)
            key = chunk["chunk_text"]
            if key not in seen_texts:
                seen_texts.add(key)
                flat_results.append(tagged)
        query_grouped.append(per_query)

    return flat_results, query_grouped
