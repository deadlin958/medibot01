"""
Prompt Templates — RAG + triage + image prompts with safety guardrails.
Now includes {history_section} for multi-turn conversation context.
"""

from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage

from backend.config import DISCLAIMER, EMERGENCY_KEYWORDS
from backend.prompts.system_prompt import get_system_prompt_text

# ── RAG Answer Template ───────────────────────────────────────────────────────
_RAG_HUMAN_TEMPLATE = """\
{history_section}\
=== RETRIEVED EVIDENCE FROM PubMedQA ===
{context}
=========================================

Current user query: {question}

Instructions (follow exactly):
1. Use ONLY the retrieved evidence above to form your answer. Do not invent facts.
2. Structure your answer as:
   • Short Answer (1–2 sentences): A yes/no/maybe summary of what the evidence suggests.
   • Explanation (2–4 sentences): Plain-language explanation based on the evidence.
   • Next Step (1–2 sentences): Whether to seek urgent care, see a doctor soon, or monitor.
3. Use cautious language — never say "you have…" or "this is definitely…".
   Use phrases like: "may suggest", "could indicate", "evidence points to", "warrants evaluation".
4. If the user describes ANY of the following: {emergency_keywords} — immediately say:
   "⚠️ This may indicate a medical emergency. Please seek urgent care or go to the nearest emergency department immediately."
5. End EVERY response with this exact disclaimer on its own line:
   {disclaimer}
"""

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=get_system_prompt_text()),
        HumanMessagePromptTemplate.from_template(_RAG_HUMAN_TEMPLATE),
    ]
)


def build_rag_prompt_vars(
    question: str,
    context_docs: list[str],
    history_string: str = "",
) -> dict:
    """Build variable dict to fill RAG_PROMPT."""
    formatted_context = "\n\n---\n\n".join(
        f"[Source {i+1}]\n{doc}" for i, doc in enumerate(context_docs)
    )
    # Format history block with header if present
    history_section = ""
    if history_string.strip():
        history_section = (
            "=== CONVERSATION HISTORY (for context only) ===\n"
            f"{history_string}\n"
            "================================================\n\n"
        )
    return {
        "question":           question,
        "context":            formatted_context,
        "disclaimer":         DISCLAIMER,
        "emergency_keywords": ", ".join(EMERGENCY_KEYWORDS),
        "history_section":    history_section,
    }


# ── Image Description Prompt ──────────────────────────────────────────────────
IMAGE_DESCRIPTION_SYSTEM = """\
You are a medical image description assistant. Your task is to describe what is
visible in the provided medical image in clear, plain language that can be used
as a clinical query. Do NOT make a diagnosis. Describe observable findings only
(e.g., shadow, opacity, lesion, rash characteristics, size, location).
Limit your description to 3–5 sentences.
Also note briefly whether anything in the image appears to require urgent attention.
"""
