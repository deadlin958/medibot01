"""
Session Manager — creates and tracks anonymous session tokens.

Sessions are ephemeral (in-memory only). No PII is persisted.
Each session gets a UUID that is also used as the triage session_id
and conversation memory key.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

log = logging.getLogger(__name__)

@dataclass
class SessionMeta:
    session_id: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_active: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


_sessions: dict[str, SessionMeta] = {}


def create_session() -> SessionMeta:
    """Generate a new anonymous session and register it."""
    sid = str(uuid.uuid4())
    meta = SessionMeta(session_id=sid)
    _sessions[sid] = meta
    log.info(f"New session created: {sid}")
    return meta


def touch_session(session_id: str) -> None:
    """Update last_active timestamp for an existing session."""
    if session_id in _sessions:
        _sessions[session_id].last_active = datetime.now(timezone.utc).isoformat()


def get_session_meta(session_id: str) -> SessionMeta | None:
    return _sessions.get(session_id)


def session_exists(session_id: str) -> bool:
    return session_id in _sessions


def remove_session(session_id: str) -> None:
    """Remove session metadata (called on full reset)."""
    _sessions.pop(session_id, None)
