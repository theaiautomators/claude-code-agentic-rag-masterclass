import openai
from langsmith.wrappers import wrap_openai

from config import settings

_llm_client = None
_embedding_client = None


def get_llm_client() -> openai.OpenAI:
    """Return a LangSmith-wrapped LLM client (singleton).

    Uses OpenRouter if OPENROUTER_API_KEY is set, otherwise falls back
    to OpenAI directly (uses OPENAI_API_KEY).
    """
    global _llm_client
    if _llm_client is None:
        if settings.openrouter_api_key:
            raw_client = openai.OpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        else:
            raw_client = openai.OpenAI(api_key=settings.openai_api_key)
        _llm_client = wrap_openai(raw_client)
    return _llm_client


def get_embedding_client() -> openai.OpenAI:
    """Return a LangSmith-wrapped OpenAI client for embeddings (singleton)."""
    global _embedding_client
    if _embedding_client is None:
        raw_client = openai.OpenAI(api_key=settings.openai_api_key)
        _embedding_client = wrap_openai(raw_client)
    return _embedding_client
