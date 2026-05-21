"""
Ingestor: Loads a document, chunks it, embeds with all-MiniLM-L6-v2,
and upserts into Supabase pgvector.
"""
import os
import uuid
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from sentence_transformers import SentenceTransformer

load_dotenv()

# Load the offline embedding model once at module level (cached after first load)
_embedding_model = None

def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        print("[Ingestor] Loading all-MiniLM-L6-v2 embedding model...")
        _embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("[Ingestor] Embedding model loaded.")
    return _embedding_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings using the offline MiniLM model."""
    model = _get_embedding_model()
    return model.encode(texts, normalize_embeddings=True).tolist()


def ingest_from_url(url: str, doc_name: str, supabase_client) -> int:
    """
    Scrapes a URL, chunks the content, embeds it, and upserts into
    Supabase policy_chunks table.

    Returns the number of chunks upserted.
    """
    print(f"[Ingestor] Loading document from URL: {url}")
    loader = WebBaseLoader(url)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_documents(docs)
    chunk_texts = [c.page_content.strip() for c in chunks if c.page_content.strip()] # type: ignore /n all that are ignoreed only raw text chunks are used

    print(f"[Ingestor] Split into {len(chunk_texts)} chunks. Embedding...")
    embeddings = embed_texts(chunk_texts)

    rows = [
        {
            "id": str(uuid.uuid4()),
            "doc_name": doc_name,
            "chunk_text": text,
            "embedding": embedding,
        }
        for text, embedding in zip(chunk_texts, embeddings)
    ]

    print(f"[Ingestor] Upserting {len(rows)} rows into Supabase policy_chunks...")
    supabase_client.table("policy_chunks").upsert(rows).execute()
    print(f"[Ingestor] Done. {len(rows)} chunks stored for doc '{doc_name}'.")
    return len(rows)


def ingest_from_text(text: str, doc_name: str, supabase_client) -> int:
    """
    Chunks a raw text string, embeds it, and upserts into Supabase.
    Useful for testing without a live URL.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.create_documents([text])
    chunk_texts = [c.page_content.strip() for c in chunks if c.page_content.strip()]

    embeddings = embed_texts(chunk_texts)

    rows = [
        {
            "id": str(uuid.uuid4()),
            "doc_name": doc_name,
            "chunk_text": text,
            "embedding": embedding,
        }
        for text, embedding in zip(chunk_texts, embeddings)
    ]

    supabase_client.table("policy_chunks").upsert(rows).execute()
    return len(rows)
