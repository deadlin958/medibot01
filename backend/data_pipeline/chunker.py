"""
Chunker — splits cleaned PubMedQA records into overlapping text chunks.

Strategy
--------
Each record has two semantically distinct fields to embed:
  1. `question`      — the research question (short, already a good query)
  2. `full_context`  — multi-section abstract (can be long)

We chunk *full_context* with LangChain's RecursiveCharacterTextSplitter and
prepend the question to each chunk so embeddings carry the research intent.
The `question` itself is also stored in metadata for hybrid lookup later.
"""

import json
import logging
from pathlib import Path
from typing import Generator

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import CLEANED_JSONL, CHUNK_SIZE, CHUNK_OVERLAP

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# ── Splitter ──────────────────────────────────────────────────────────────────
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)


def iter_chunks(
    jsonl_path: Path = CLEANED_JSONL,
) -> Generator[dict, None, None]:
    """
    Yield dicts with keys:
        text       — embeddable text (question + context chunk)
        metadata   — pubid, question, final_decision, mesh_terms, chunk_index
    """
    with jsonl_path.open("r", encoding="utf-8") as fin:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)

            question       = record["question"]
            full_context   = record["full_context"]
            long_answer    = record["long_answer"]
            final_decision = record["final_decision"]
            pubid          = record["pubid"]
            mesh_terms     = record.get("mesh_terms", [])

            # Split the abstract context into chunks
            context_chunks = _splitter.split_text(full_context)

            # Also include the long_answer as a standalone chunk
            # so retrieval can surface conclusions directly
            answer_chunks = _splitter.split_text(long_answer)

            all_chunks = context_chunks + answer_chunks
            chunk_source = (
                ["context"] * len(context_chunks)
                + ["long_answer"] * len(answer_chunks)
            )

            for idx, (chunk_text, source) in enumerate(
                zip(all_chunks, chunk_source)
            ):
                # Prepend the research question so the embedding anchors
                # the chunk to its clinical intent
                embeddable_text = f"Question: {question}\n\n{chunk_text}"

                yield {
                    "text": embeddable_text,
                    "metadata": {
                        "pubid":          pubid,
                        "question":       question,
                        "final_decision": final_decision,
                        "mesh_terms":     ", ".join(mesh_terms[:10]),  # Chroma needs str
                        "chunk_index":    idx,
                        "source":         source,  # "context" or "long_answer"
                    },
                }


def get_all_chunks(jsonl_path: Path = CLEANED_JSONL) -> list[dict]:
    """Return all chunks as a list (loads everything into memory)."""
    chunks = list(iter_chunks(jsonl_path))
    log.info(f"Total chunks generated: {len(chunks)}")
    return chunks


if __name__ == "__main__":
    chunks = get_all_chunks()
    print(f"Sample chunk:\n{json.dumps(chunks[0], indent=2)}")
