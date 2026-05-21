-- Enable pgvector extension (must be enabled in Supabase dashboard first)
CREATE EXTENSION IF NOT EXISTS vector;

-- Policy document chunks vector store
CREATE TABLE IF NOT EXISTS policy_chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_name    TEXT NOT NULL,
    chunk_text  TEXT NOT NULL,
    embedding   VECTOR(384),   -- matches all-MiniLM-L6-v2 output dimensions
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFlat index for fast approximate nearest-neighbor cosine search
-- Run ANALYZE on the table after inserting data for best performance
CREATE INDEX IF NOT EXISTS policy_chunks_embedding_idx
    ON policy_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Cosine similarity search RPC (also in 002_match_policy_chunks.sql for existing DBs)
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
