"""
Image Routes — multimodal image upload with memory tracking.

POST /api/image-query
  Multipart form: image=<file>, question=<str>, session_id=<str>
"""

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from backend.llm.vision import analyze_image
from backend.rag.pipeline import run_rag, _EMERGENCY_RESPONSE
from backend.memory.store import add_turn, get_history_as_prompt_string
from backend.triage.flow import build_triage_summary, is_complete
from backend.session.manager import touch_session

log = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_MIME   = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}
MAX_SIZE_BYTES = 10 * 1024 * 1024


class ImageQueryResponse(BaseModel):
    type:              str
    content:           str
    image_description: str
    is_emergency:      bool        = False
    sources:           list[dict]  = []


@router.post("/image-query", response_model=ImageQueryResponse,
             summary="Upload a medical image and ask a question")
async def image_query(
    image:      UploadFile = File(...),
    question:   str        = Form(""),
    session_id: str        = Form("default"),
) -> ImageQueryResponse:
    """
    Multimodal endpoint:
    1. GPT-4o vision → clinical text description + emergency flag
    2. Description + triage context → RAG pipeline
    3. Response tracked in conversation memory
    """
    touch_session(session_id)

    mime_type = image.content_type or "image/jpeg"
    if mime_type not in ALLOWED_MIME:
        raise HTTPException(status_code=415,
            detail=f"Unsupported image type '{mime_type}'.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty.")
    if len(image_bytes) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 10 MB).")

    log.info(f"Image ({len(image_bytes)//1024} KB) session={session_id}")

    # ── Vision analysis ───────────────────────────────────────────────────────
    try:
        analysis = analyze_image(image_bytes, question.strip(), mime_type)
    except Exception as e:
        log.error(f"Error during vision analysis: {e}")
        error_msg = str(e)
        if "insufficient_quota" in error_msg.lower() or "429" in error_msg:
            error_msg = "OpenAI API quota exceeded. Please check your API key billing details."
        return ImageQueryResponse(
            type="error",
            content=f"Image analysis failed: {error_msg}",
            image_description="",
        )

    # Emergency flag from vision
    if analysis["emergency_flag"]:
        add_turn(session_id, "human",     f"[Image upload] {question}")
        add_turn(session_id, "assistant", _EMERGENCY_RESPONSE)
        return ImageQueryResponse(
            type="answer", content=_EMERGENCY_RESPONSE,
            image_description=analysis["description"], is_emergency=True,
        )

    # ── Enrich with triage context ────────────────────────────────────────────
    rag_query = analysis["rag_query"]
    if is_complete(session_id):
        triage_ctx = build_triage_summary(session_id)
        if triage_ctx:
            rag_query = f"{triage_ctx}\n\n{rag_query}"

    # ── RAG pipeline with history ─────────────────────────────────────────────
    history_string = get_history_as_prompt_string(session_id)
    try:
        result = run_rag(rag_query, history_string=history_string)
    except Exception as e:
        log.error(f"Error during RAG pipeline for image: {e}")
        error_msg = str(e)
        if "insufficient_quota" in error_msg.lower() or "429" in error_msg:
            error_msg = "OpenAI API quota exceeded. Please check your API key billing details."
        return ImageQueryResponse(
            type="error",
            content=f"Medical guidance failed: {error_msg}",
            image_description=analysis["description"],
        )

    # Track in memory
    add_turn(session_id, "human",     f"[Image] {question or 'Image uploaded'}")
    add_turn(session_id, "assistant", result["answer"])

    return ImageQueryResponse(
        type="answer",
        content=result["answer"],
        image_description=analysis["description"],
        is_emergency=result["is_emergency"],
        sources=result["sources"],
    )
