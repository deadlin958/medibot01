"""
RAG Pipeline — Retrieval-Augmented Generation chain with conversation memory.

Flow:
  1. Emergency keyword check → immediate escalation
  2. Retrieve top-k chunks from ChromaDB (with full metadata)
  3. Inject conversation history + retrieved context into prompt
  4. Call GPT-4o via LangChain
  5. Guarantee disclaimer present
  6. Return structured sources for frontend citation display
"""

import logging

from backend.config import DISCLAIMER, EMERGENCY_KEYWORDS
from backend.llm.chat import invoke_llm
from backend.prompts.templates import RAG_PROMPT, build_rag_prompt_vars
from backend.rag.retriever import retrieve

log = logging.getLogger(__name__)

_EMERGENCY_RESPONSE = (
    "⚠️ **This may indicate a medical emergency.**\n\n"
    "Based on the symptoms you described, please **seek urgent medical care "
    "or go to the nearest emergency department immediately.** "
    "Do not wait or try to self-treat.\n\n"
    "If you are in the UK, call **999**. In the US, call **911**. "
    "In India, call **112**. Use your local emergency number.\n\n"
    f"{DISCLAIMER}"
)


def _is_emergency(query: str) -> bool:
    lower = query.lower()
    return any(kw in lower for kw in EMERGENCY_KEYWORDS)


def _ensure_disclaimer(response: str) -> str:
    if DISCLAIMER.lower() not in response.lower():
        return f"{response}\n\n{DISCLAIMER}"
    return response


def _build_sources(hits: list[dict]) -> list[dict]:
    """Convert raw ChromaDB hits into structured source dicts for the API."""
    sources = []
    seen_pubids = set()
    for hit in hits:
        meta   = hit.get("metadata", {})
        pubid  = meta.get("pubid", 0)
        # Deduplicate by pubid — different chunks of same article
        if pubid in seen_pubids:
            continue
        seen_pubids.add(pubid)
        snippet = hit.get("text", "")[:250].strip()
        if len(hit.get("text", "")) > 250:
            snippet += "…"
        sources.append({
            "pubid":          pubid,
            "question":       meta.get("question", ""),
            "final_decision": meta.get("final_decision", "maybe"),
            "snippet":        snippet,
        })
    return sources


def run_rag(
    query: str,
    k: int = 5,
    history_string: str = "",
) -> dict:
    """
    Execute the full RAG pipeline.

    Args:
        query:          User's medical question (text or image-derived)
        k:              Number of chunks to retrieve
        history_string: Formatted conversation history for context injection

    Returns:
        {
            answer:       str
            sources:      list[dict]  — pubid, question, final_decision, snippet
            is_emergency: bool
        }
    """
    # ── Emergency guard ───────────────────────────────────────────────────────
    if _is_emergency(query):
        log.warning(f"Emergency detected: '{query[:80]}'")
        return {"answer": _EMERGENCY_RESPONSE, "sources": [], "is_emergency": True}

    # ── Retrieval ─────────────────────────────────────────────────────────────
    log.info(f"Retrieving top-{k} chunks for: '{query[:80]}'")
    hits = retrieve(query, k=k)

    if not hits:
        fallback = (
            "I was unable to find relevant biomedical evidence in the PubMedQA "
            "dataset for your query.\n\nPlease consult a qualified healthcare "
            f"professional for guidance.\n\n{DISCLAIMER}"
        )
        return {"answer": fallback, "sources": [], "is_emergency": False}

    context_docs = [h["text"] for h in hits]
    sources      = _build_sources(hits)

    # ── Prompt construction ───────────────────────────────────────────────────
    prompt_vars = build_rag_prompt_vars(query, context_docs, history_string)
    messages    = RAG_PROMPT.format_messages(**prompt_vars)

    # ── LLM call ─────────────────────────────────────────────────────────────
    log.info("Calling GPT-4o …")
    answer = invoke_llm(messages)
    answer = _ensure_disclaimer(answer)

    return {"answer": answer, "sources": sources, "is_emergency": False}
