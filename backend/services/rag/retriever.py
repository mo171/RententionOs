"""
Retriever: Runs similarity search against Supabase pgvector.
Uses the offline all-MiniLM-L6-v2 model for query embedding.
"""
from services.rag.ingestor import embed_texts


def retrieve_chunks(
    query: str,
    supabase_client,
    top_k: int = 3,
    match_threshold: float = 0.2,
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
