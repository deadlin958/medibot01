"""
RAG Retriever — wraps ChromaDB as a retriever and provides a clean
`retrieve(query, k)` function that returns the most relevant chunks.
"""

import logging
from functools import lru_cache

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from backend.config import (
    CHROMA_DB_DIR,
    CHROMA_COLLECTION,
    EMBEDDING_MODEL,
    TOP_K_RESULTS,
)

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_collection() -> chromadb.Collection:
    """Load (and cache) the ChromaDB collection once per process."""
    log.info(f"Loading ChromaDB collection '{CHROMA_COLLECTION}' from {CHROMA_DB_DIR}")
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    return client.get_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embedding_fn,
    )


def retrieve(query: str, k: int = TOP_K_RESULTS) -> list[dict]:
    """
    Retrieve the top-k most relevant chunks for a query.

    Returns a list of dicts, each with:
        - text       : the stored chunk text
        - metadata   : pubid, question, final_decision, mesh_terms, etc.
        - distance   : cosine distance (lower = more similar)
    """
    collection = _get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append(
            {
                "text":     doc,
                "metadata": meta,
                "distance": dist,
            }
        )

    log.debug(f"Retrieved {len(hits)} chunks for query='{query[:60]}…'")
    return hits


def retrieve_text_only(query: str, k: int = TOP_K_RESULTS) -> list[str]:
    """Convenience wrapper — returns just the text strings of hits."""
    return [hit["text"] for hit in retrieve(query, k)]
