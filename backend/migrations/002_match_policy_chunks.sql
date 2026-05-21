-- RPC for cosine similarity search (run if 001 was already applied without this function)
CREATE OR REPLACE FUNCTION match_policy_chunks(
  query_embedding vector(384),
  match_threshold float,
  match_count int
)
RETURNS TABLE (chunk_text text, doc_name text, similarity float)
LANGUAGE sql STABLE AS $$
  SELECT chunk_text, doc_name,
         1 - (embedding <=> query_embedding) AS similarity
  FROM policy_chunks
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
