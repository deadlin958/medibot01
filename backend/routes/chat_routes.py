"""
Chat Routes — text-based Q&A with triage, memory, and source citations.

Endpoints:
  GET  /api/session/new     — create anonymous session
  POST /api/greet           — initial greeting + first triage question
  POST /api/chat            — main triage → RAG chat endpoint
  POST /api/reset           — reset session (triage + memory)
  GET  /api/history         — get conversation history
"""

import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.triage.flow import (
    build_enriched_query, get_triage_status, is_complete,
    next_question, record_answer, reset_session,
)
from backend.rag.pipeline import run_rag, _EMERGENCY_RESPONSE
from backend.memory.store import (
    add_turn, clear_memory, get_history, get_history_as_prompt_string,
)
from backend.session.manager import create_session, touch_session
from backend.config import EMERGENCY_KEYWORDS

log = logging.getLogger(__name__)
router = APIRouter()

_GREETING = (
    "Hello! I am a **Clinical Guidance Assistant** powered by PubMedQA "
    "biomedical research data.\n\n"
    "I can help you understand possible explanations for your symptoms and "
    "whether you should see a doctor soon.\n\n"
    "Before we start, I need to ask you **6 quick questions** — one at a time. "
    "Please answer honestly.\n\n"
    "> ⚠️ **Remember:** This is not a medical diagnosis. Always consult a "
    "qualified doctor for proper advice.\n\n"
    "Let's begin:\n\n"
)


# ── Pydantic models ───────────────────────────────────────────────────────────

class Source(BaseModel):
    pubid:          int
    question:       str
    final_decision: str
    snippet:        str


class ChatRequest(BaseModel):
    session_id: str = "default"
    message:    str

    class Config:
        json_schema_extra = {
            "example": {"session_id": "uuid-here", "message": "I have a headache"}
        }


class ChatResponse(BaseModel):
    type:          str            # "greeting" | "triage" | "answer"
    content:       str
    is_emergency:  bool          = False
    triage_step:   int           = 0    # answers given so far (0–6)
    triage_total:  int           = 6
    sources:       list[Source]  = []


class SessionRequest(BaseModel):
    session_id: str = "default"


class SessionResponse(BaseModel):
    status:  str
    message: str


class NewSessionResponse(BaseModel):
    session_id:  str
    created_at:  str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/session/new", response_model=NewSessionResponse,
            summary="Create a new anonymous session")
def new_session() -> NewSessionResponse:
    """Generate a fresh UUID session_id and register it server-side."""
    meta = create_session()
    return NewSessionResponse(session_id=meta.session_id, created_at=meta.created_at)


@router.post("/greet", response_model=ChatResponse, summary="Start a session")
def greet(body: SessionRequest) -> ChatResponse:
    """Returns welcome message + first triage question."""
    touch_session(body.session_id)
    first_q  = next_question(body.session_id)
    status   = get_triage_status(body.session_id)
    content  = _GREETING + (first_q or "How can I help you today?")
    return ChatResponse(
        type="greeting", content=content,
        triage_step=status["step"], triage_total=status["total"],
    )


@router.post("/chat", response_model=ChatResponse, summary="Send a chat message")
def chat(body: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint:
    1. Emergency keyword guard (always first)
    2. Triage phase (6 questions)
    3. RAG answer with conversation history + source citations
    """
    session_id = body.session_id
    message    = body.message.strip()
    touch_session(session_id)

    if not message:
        return ChatResponse(type="error", content="Message cannot be empty.")

    # ── Emergency guard ───────────────────────────────────────────────────────
    if any(kw in message.lower() for kw in EMERGENCY_KEYWORDS):
        add_turn(session_id, "human",     message)
        add_turn(session_id, "assistant", _EMERGENCY_RESPONSE)
        return ChatResponse(
            type="answer", content=_EMERGENCY_RESPONSE, is_emergency=True,
        )

    # ── Triage phase ──────────────────────────────────────────────────────────
    if not is_complete(session_id):
        q = next_question(session_id)
        if q is not None:
            record_answer(session_id, message)
            next_q = next_question(session_id)
            status = get_triage_status(session_id)
            if next_q:
                return ChatResponse(
                    type="triage", content=next_q,
                    triage_step=status["step"], triage_total=status["total"],
                )
            # triage just completed — fall through to RAG

    # ── RAG phase ─────────────────────────────────────────────────────────────
    try:
        history_string = get_history_as_prompt_string(session_id)
        enriched_query = build_enriched_query(session_id, message)
        result = run_rag(enriched_query, history_string=history_string)

        # Store turn in memory
        add_turn(session_id, "human",     message)
        add_turn(session_id, "assistant", result["answer"])

        status = get_triage_status(session_id)
        return ChatResponse(
            type="answer",
            content=result["answer"],
            is_emergency=result["is_emergency"],
            triage_step=status["step"],
            triage_total=status["total"],
            sources=[Source(**s) for s in result["sources"]],
        )
    except Exception as e:
        import traceback
        import sys
        
        # Write to file because terminal is hiding it
        with open("error_debug.txt", "a") as f:
            f.write(f"EXCEPTION CAUGHT:\n{str(e)}\n")
            f.write("TRACEBACK:\n")
            f.write(traceback.format_exc())
            f.write("-" * 50 + "\n")

        traceback.print_exc()
        log.error(f"Error during RAG pipeline: {e}")
        status = get_triage_status(session_id)
        error_msg = str(e)
        if "insufficient_quota" in error_msg.lower() or "429" in error_msg:
            error_msg = "OpenAI API quota exceeded. Please check your API key billing details."
            
        return ChatResponse(
            type="error",
            content=f"An error occurred while generating the response: {error_msg}",
            triage_step=status["step"],
            triage_total=status["total"],
        )


@router.post("/reset", response_model=SessionResponse, summary="Reset a session")
def reset(body: SessionRequest) -> SessionResponse:
    """Reset triage state and conversation memory for a session."""
    reset_session(body.session_id)
    clear_memory(body.session_id)
    return SessionResponse(status="ok", message="Session reset successfully.")


@router.get("/history", summary="Get conversation history")
def history(session_id: str = Query("default", description="Session ID")) -> dict:
    """Returns full conversation turn history for a session."""
    return {"session_id": session_id, "turns": get_history(session_id)}
