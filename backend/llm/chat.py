"""
LLM Chat Wrapper — initialises the LangChain ChatOpenAI client with GPT-4o
and provides a simple invoke helper.
"""

from functools import lru_cache

from langchain_openai import ChatOpenAI

from backend.config import OPENAI_API_KEY, GPT_TEXT_MODEL, LLM_TEMPERATURE


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """Return a cached ChatOpenAI instance."""
    if not OPENAI_API_KEY:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. "
            "Add it to the .env file in the project root."
        )
    return ChatOpenAI(
        model=GPT_TEXT_MODEL,
        temperature=LLM_TEMPERATURE,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=1024,
    )


def invoke_llm(messages: list) -> str:
    """
    Invoke the LLM with a list of LangChain messages.

    Args:
        messages: List of BaseMessage objects (System, Human, AI, etc.)

    Returns:
        The assistant's reply as a plain string.
    """
    llm     = get_llm()
    result  = llm.invoke(messages)
    return result.content.strip()
