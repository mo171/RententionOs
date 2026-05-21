-- IVFFlat with lists=100 requires many rows; small test corpora return no matches.
-- Recreate index tuned for low row counts (or remove for exact sequential scan).

DROP INDEX IF EXISTS policy_chunks_embedding_idx;

CREATE INDEX IF NOT EXISTS policy_chunks_embedding_idx
    ON policy_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 1);

ANALYZE policy_chunks;
