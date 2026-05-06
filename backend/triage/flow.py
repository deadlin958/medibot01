"""
Triage Flow — 6-step pre-consultation state machine.

Steps (in order):
  1. age            — "What is your age?"
  2. main_symptom   — "What is your main symptom or concern?"
  3. duration       — "How long have you had this symptom?"
  4. severity       — "How would you rate the severity (mild, moderate, severe)?"
  5. other_symptoms — "Have you noticed any other symptoms?"
  6. medical_history— "Do you have any known medical conditions or allergies?"
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)

TRIAGE_STEPS = [
    {
        "key":      "age",
        "question": "What is your age?",
        "label":    "Age",
    },
    {
        "key":      "main_symptom",
        "question": "What is your main symptom or concern?",
        "label":    "Symptom",
    },
    {
        "key":      "duration",
        "question": "How long have you had this symptom?",
        "label":    "Duration",
    },
    {
        "key":      "severity",
        "question": "How would you rate the severity of your symptom? (mild, moderate, or severe)",
        "label":    "Severity",
    },
    {
        "key":      "other_symptoms",
        "question": (
            "Have you noticed any other symptoms? "
            "(e.g., fever, shortness of breath, chest pain, nausea)"
        ),
        "label":    "Other Symptoms",
    },
    {
        "key":      "medical_history",
        "question": (
            "Do you have any known medical conditions or allergies? "
            "(e.g., diabetes, hypertension, penicillin allergy)"
        ),
        "label":    "Medical History",
    },
]

NUM_STEPS = len(TRIAGE_STEPS)   # 6


@dataclass
class TriageSession:
    session_id: str
    step_index: int  = 0
    answers:    dict = field(default_factory=dict)
    complete:   bool = False


_sessions: dict[str, TriageSession] = {}


def get_or_create_session(session_id: str) -> TriageSession:
    if session_id not in _sessions:
        _sessions[session_id] = TriageSession(session_id=session_id)
    return _sessions[session_id]


def reset_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def next_question(session_id: str) -> Optional[str]:
    session = get_or_create_session(session_id)
    if session.complete or session.step_index >= NUM_STEPS:
        return None
    return TRIAGE_STEPS[session.step_index]["question"]


def record_answer(session_id: str, answer: str) -> None:
    session = get_or_create_session(session_id)
    if session.complete:
        return
    step = TRIAGE_STEPS[session.step_index]
    session.answers[step["key"]] = answer.strip()
    session.step_index += 1
    if session.step_index >= NUM_STEPS:
        session.complete = True
        log.info(f"Triage complete for session {session_id}")


def is_complete(session_id: str) -> bool:
    return get_or_create_session(session_id).complete


def get_triage_status(session_id: str) -> dict:
    """Return progress info for the frontend progress bar."""
    session = get_or_create_session(session_id)
    return {
        "step":             session.step_index,   # answers given so far
        "total":            NUM_STEPS,
        "is_complete":      session.complete,
        "current_question": (
            TRIAGE_STEPS[session.step_index]["question"]
            if not session.complete and session.step_index < NUM_STEPS
            else None
        ),
        "current_label": (
            TRIAGE_STEPS[session.step_index]["label"]
            if not session.complete and session.step_index < NUM_STEPS
            else None
        ),
        "answers": session.answers,
    }


def build_triage_summary(session_id: str) -> str:
    session = get_or_create_session(session_id)
    a = session.answers
    parts = []
    if a.get("age"):            parts.append(f"Age: {a['age']}")
    if a.get("main_symptom"):   parts.append(f"Main symptom: {a['main_symptom']}")
    if a.get("duration"):       parts.append(f"Duration: {a['duration']}")
    if a.get("severity"):       parts.append(f"Severity: {a['severity']}")
    if a.get("other_symptoms"): parts.append(f"Other symptoms: {a['other_symptoms']}")
    if a.get("medical_history"):parts.append(f"Medical history/allergies: {a['medical_history']}")
    return "Patient context — " + " | ".join(parts) if parts else ""


def build_enriched_query(session_id: str, user_message: str) -> str:
    summary = build_triage_summary(session_id)
    if summary:
        return f"{summary}\n\nUser question: {user_message}"
    return user_message
