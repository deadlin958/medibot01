"""
Indexer — embeds chunks and persists them into a ChromaDB vector store.

Embedding model : sentence-transformers/all-MiniLM-L6-v2 (local, free)
Vector store    : ChromaDB (persistent, on-disk)
"""

import logging
import uuid
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from backend.config import (
    CHROMA_DB_DIR,
    CHROMA_COLLECTION,
    CLEANED_JSONL,
    EMBEDDING_MODEL,
)
from backend.data_pipeline.chunker import get_all_chunks

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

BATCH_SIZE = 500   # ChromaDB add() works well in batches


def _get_client() -> chromadb.PersistentClient:
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DB_DIR))


def _get_embedding_fn() -> SentenceTransformerEmbeddingFunction:
    log.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    return SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)


def build_index(jsonl_path: Path = CLEANED_JSONL, reset: bool = False) -> int:
    """
    Embed all chunks and store them in ChromaDB.

    Args:
        jsonl_path: path to the cleaned JSONL file
        reset:      if True, delete and recreate the collection

    Returns:
        Number of vectors stored.
    """
    client       = _get_client()
    embedding_fn = _get_embedding_fn()

    # Handle reset
    if reset:
        try:
            client.delete_collection(CHROMA_COLLECTION)
            log.info(f"Deleted existing collection '{CHROMA_COLLECTION}'")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    existing_count = collection.count()
    if existing_count > 0 and not reset:
        log.info(
            f"Collection '{CHROMA_COLLECTION}' already contains "
            f"{existing_count} vectors. Skipping indexing. "
            "Pass reset=True to rebuild."
        )
        return existing_count

    log.info("Generating chunks …")
    chunks = get_all_chunks(jsonl_path)
    total  = len(chunks)
    log.info(f"Total chunks to index: {total}")

    stored = 0
    for batch_start in range(0, total, BATCH_SIZE):
        batch = chunks[batch_start : batch_start + BATCH_SIZE]

        ids        = [str(uuid.uuid4()) for _ in batch]
        documents  = [c["text"]     for c in batch]
        metadatas  = [c["metadata"] for c in batch]

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        stored += len(batch)
        log.info(f"  Indexed {stored}/{total} chunks …")

    log.info(f"Indexing complete — {stored} vectors persisted to {CHROMA_DB_DIR}")
    return stored


def load_collection() -> chromadb.Collection:
    """Return the persisted ChromaDB collection (must already be built)."""
    client       = _get_client()
    embedding_fn = _get_embedding_fn()
    return client.get_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embedding_fn,
    )


if __name__ == "__main__":
    build_index()
