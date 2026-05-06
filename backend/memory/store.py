"""
Conversation Memory Store — per-session sliding-window conversation history.

Stores the last MEMORY_WINDOW_SIZE exchanges (human + assistant turns)
in a simple in-memory dict. Provides the history as a formatted string
to inject into the RAG prompt for multi-turn context.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from backend.config import MEMORY_WINDOW_SIZE

log = logging.getLogger(__name__)

Role = Literal["human", "assistant"]


@dataclass
class Turn:
    role: Role
    content: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ConversationMemory:
    session_id: str
    turns: list[Turn] = field(default_factory=list)


# ── In-memory store ──────────────────────────────────────────────────────────
_memories: dict[str, ConversationMemory] = {}


def _get_or_create(session_id: str) -> ConversationMemory:
    if session_id not in _memories:
        _memories[session_id] = ConversationMemory(session_id=session_id)
    return _memories[session_id]


def add_turn(session_id: str, role: Role, content: str) -> None:
    """Append a human or assistant turn to the session memory."""
    mem = _get_or_create(session_id)
    mem.turns.append(Turn(role=role, content=content))
    log.debug(f"Memory [{session_id}]: added {role} turn ({len(content)} chars)")


def get_history(session_id: str) -> list[dict]:
    """Return all turns as list of dicts (for API serialization)."""
    mem = _get_or_create(session_id)
    return [
        {"role": t.role, "content": t.content, "timestamp": t.timestamp}
        for t in mem.turns
    ]


def get_history_as_prompt_string(session_id: str) -> str:
    """
    Return the last MEMORY_WINDOW_SIZE turns formatted as a prompt-injectable
    string. Returns empty string if no history yet.
    """
    mem = _get_or_create(session_id)
    # Take last N turns (window)
    window = mem.turns[-(MEMORY_WINDOW_SIZE * 2):]
    if not window:
        return ""

    lines = []
    for t in window:
        label = "User" if t.role == "human" else "Assistant"
        # Truncate very long turns so prompt stays manageable
        body = t.content[:400] + "…" if len(t.content) > 400 else t.content
        lines.append(f"{label}: {body}")

    return "\n".join(lines)


def clear_memory(session_id: str) -> None:
    """Wipe conversation memory for a session (called on reset)."""
    _memories.pop(session_id, None)
