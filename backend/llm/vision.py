"""
Vision Module — converts uploaded images into clinical text descriptions
using GPT-4o vision, with emergency flag detection and structured output.
"""

import base64
import logging

from openai import OpenAI

from backend.config import OPENAI_API_KEY, GPT_VISION_MODEL
from backend.prompts.templates import IMAGE_DESCRIPTION_SYSTEM

log = logging.getLogger(__name__)

_EMERGENCY_VISUAL_KEYWORDS = [
    "severe", "emergency", "critical", "urgent", "unconscious",
    "unresponsive", "profuse bleeding", "significant injury",
    "stroke", "heart attack", "anaphylaxis",
]


def _encode_image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def analyze_image(
    image_bytes: bytes,
    user_question: str = "",
    mime_type: str = "image/jpeg",
) -> dict:
    """
    Send image to GPT-4o vision and return structured analysis.

    Returns:
        {
            description:    str   — plain-text clinical description
            emergency_flag: bool  — True if urgent signs detected
            rag_query:      str   — combined query for RAG pipeline
        }
    """
    if not OPENAI_API_KEY:
        raise EnvironmentError("OPENAI_API_KEY is not set in .env")

    client    = OpenAI(api_key=OPENAI_API_KEY)
    b64_image = _encode_image_to_base64(image_bytes)

    if user_question:
        prompt_text = (
            f"The user asked: '{user_question}'\n\n"
            "First, describe in 3–5 sentences what is visually observable in this "
            "medical image (do NOT diagnose). Then note which part of your description "
            "is most relevant to the user's question. Finally, on the last line write "
            "'URGENT: YES' if anything appears to require immediate medical attention, "
            "otherwise write 'URGENT: NO'."
        )
    else:
        prompt_text = (
            "Describe in 3–5 sentences what is visually observable in this medical "
            "image (do NOT diagnose). On the last line write 'URGENT: YES' if "
            "anything appears to require immediate medical attention, otherwise "
            "write 'URGENT: NO'."
        )

    log.info("Calling GPT-4o vision …")
    response = OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
        model=GPT_VISION_MODEL,
        messages=[
            {"role": "system", "content": IMAGE_DESCRIPTION_SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url":    f"data:{mime_type};base64,{b64_image}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
        max_tokens=600,
        temperature=0.1,
    )

    full_text      = response.choices[0].message.content.strip()
    emergency_flag = "URGENT: YES" in full_text.upper()

    # Strip the URGENT line from the description shown to the user
    description = "\n".join(
        line for line in full_text.splitlines()
        if not line.strip().upper().startswith("URGENT:")
    ).strip()

    log.info(f"Vision analysis done ({len(description)} chars, emergency={emergency_flag})")

    rag_query = f"{user_question} — {description}" if user_question else description

    return {
        "description":    description,
        "emergency_flag": emergency_flag,
        "rag_query":      rag_query,
    }


# ── Backward-compat wrapper ───────────────────────────────────────────────────
def image_to_rag_query(
    image_bytes: bytes,
    user_question: str = "",
    mime_type: str = "image/jpeg",
) -> str:
    """Legacy wrapper — returns just the rag_query string."""
    return analyze_image(image_bytes, user_question, mime_type)["rag_query"]
