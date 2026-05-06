"""
System Prompt Loader — reads the system prompt from the text file in the
project root and returns it as a LangChain SystemMessage.
"""

from functools import lru_cache
from pathlib import Path

from langchain_core.messages import SystemMessage

from backend.config import SYSTEM_PROMPT_FILE


@lru_cache(maxsize=1)
def get_system_prompt_text() -> str:
    """Read and cache the raw system prompt string."""
    path = Path(SYSTEM_PROMPT_FILE)
    if not path.exists():
        raise FileNotFoundError(f"System prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def get_system_message() -> SystemMessage:
    """Return the system prompt as a LangChain SystemMessage."""
    return SystemMessage(content=get_system_prompt_text())
