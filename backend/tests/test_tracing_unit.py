"""Unit tests for LangSmith tracing setup — no API keys needed."""

import inspect
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


# ── Test 1: OpenAI client gets wrapped ──────────────────────────────

def test_openai_client_is_wrapped():
    """wrap_openai() is called when creating the OpenAI singleton."""
    import services.openai_client as mod

    # Reset the singleton so get_openai_client() creates a fresh one
    original = mod._client
    mod._client = None

    try:
        with patch.object(mod, "wrap_openai", wraps=lambda c: c) as mock_wrap:
            with patch("openai.OpenAI", return_value=MagicMock()):
                client = mod.get_openai_client()
                mock_wrap.assert_called_once()
    finally:
        mod._client = original


# ── Test 2: stream_response is traceable ────────────────────────────

def test_stream_response_is_traceable():
    """ChatService.stream_response has the @traceable decorator."""
    from langsmith.run_helpers import is_traceable_function
    from services.chat_service import ChatService

    # Access the unbound method from the class
    assert is_traceable_function(ChatService.stream_response), (
        "stream_response should be decorated with @traceable"
    )


# ── Test 3: @traceable has correct params ───────────────────────────

def test_traceable_decorator_params():
    """@traceable has name='chat_stream_response' and run_type='chain'."""
    from services.chat_service import ChatService

    source = inspect.getsource(ChatService)
    assert 'name="chat_stream_response"' in source, (
        "Expected @traceable(name=\"chat_stream_response\")"
    )
    assert 'run_type="chain"' in source, (
        "Expected @traceable(run_type=\"chain\")"
    )


# ── Test 4: OpenAI client is a singleton ────────────────────────────

def test_openai_client_is_singleton():
    """Repeated calls to get_openai_client() return the same instance."""
    import services.openai_client as mod

    original = mod._client
    mod._client = None

    try:
        with patch("openai.OpenAI", return_value=MagicMock()):
            first = mod.get_openai_client()
            second = mod.get_openai_client()
            assert first is second, "get_openai_client() should return a singleton"
    finally:
        mod._client = original


# ── Test 5: Health endpoint has LangSmith fields ────────────────────

def test_health_endpoint_structure():
    """/api/health/services returns langsmith.enabled and langsmith.project."""
    from main import app

    client = TestClient(app)
    resp = client.get("/api/health/services")
    assert resp.status_code == 200

    data = resp.json()
    assert "langsmith" in data, "Response should contain 'langsmith' key"
    ls = data["langsmith"]
    assert "enabled" in ls, "langsmith object should have 'enabled' field"
    assert "project" in ls, "langsmith object should have 'project' field"
