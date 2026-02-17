import openai
from langsmith.wrappers import wrap_openai

from config import settings

_client = None


def get_openai_client() -> openai.OpenAI:
    """Return a LangSmith-wrapped OpenAI client (singleton)."""
    global _client
    if _client is None:
        raw_client = openai.OpenAI(api_key=settings.openai_api_key)
        _client = wrap_openai(raw_client)
    return _client
