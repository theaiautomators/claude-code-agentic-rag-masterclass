"""Integration tests that verify traces land in LangSmith.

Auto-skipped if LANGSMITH_API_KEY is not set (see conftest.py).
"""

import asyncio
import json
import time
import uuid
from unittest.mock import MagicMock

import pytest
from langsmith import Client as LangSmithClient

from config import settings
from services.chat_service import ChatService


# ── Helpers ──────────────────────────────────────────────────────────

def _make_chat_service() -> ChatService:
    """Create a ChatService with a mocked ThreadService (no Supabase needed)."""
    svc = ChatService.__new__(ChatService)
    svc.user_id = "test-user"

    # Real OpenAI client (needs OPENAI_API_KEY in env)
    from services.openai_client import get_openai_client
    svc.openai = get_openai_client()

    # Mock the ThreadService so we don't hit Supabase
    mock_ts = MagicMock()
    mock_ts.get_thread.return_value = None  # no previous response ID
    mock_ts.save_message.return_value = None
    mock_ts.update_thread.return_value = None
    svc.thread_service = mock_ts

    return svc


async def _drain_stream(gen):
    """Consume the async generator returned by stream_response and return events."""
    events = []
    async for chunk in gen:
        events.append(chunk)
    return events


def _poll_for_run(ls_client, project_name, tag, timeout=30, poll_interval=2):
    """Poll LangSmith until a run with the given tag appears or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        runs = list(ls_client.list_runs(
            project_name=project_name,
            filter=f'has(tags, "{tag}")',
            limit=1,
        ))
        if runs:
            return runs[0]
        time.sleep(poll_interval)
    return None


# ── Test 1: Trace appears in LangSmith ──────────────────────────────

@pytest.mark.asyncio
async def test_trace_appears_in_langsmith():
    """A call to stream_response creates a trace visible in LangSmith."""
    tag = f"test-{uuid.uuid4()}"
    svc = _make_chat_service()

    # Call stream_response with langsmith_extra to tag the trace
    gen = svc.stream_response(
        thread_id="thread-test-1",
        content="Say hello in one word.",
        langsmith_extra={"tags": [tag]},
    )
    events = await _drain_stream(gen)

    # Verify we got streaming events back
    assert any(e["event"] == "done" for e in events), "Should have a 'done' event"

    # Poll LangSmith for the trace
    ls = LangSmithClient()
    project = settings.langsmith_project
    run = _poll_for_run(ls, project, tag)

    assert run is not None, f"Trace with tag '{tag}' not found in LangSmith within timeout"
    assert run.name == "chat_stream_response", f"Expected run name 'chat_stream_response', got '{run.name}'"
    assert run.run_type == "chain", f"Expected run_type 'chain', got '{run.run_type}'"
    assert run.status == "success", f"Expected status 'success', got '{run.status}'"


# ── Test 2: Trace captures correct inputs ───────────────────────────

@pytest.mark.asyncio
async def test_trace_has_correct_inputs():
    """The trace's inputs field captures the message content."""
    tag = f"test-{uuid.uuid4()}"
    message = f"Integration test message {uuid.uuid4()}"
    svc = _make_chat_service()

    gen = svc.stream_response(
        thread_id="thread-test-2",
        content=message,
        langsmith_extra={"tags": [tag]},
    )
    await _drain_stream(gen)

    ls = LangSmithClient()
    project = settings.langsmith_project
    run = _poll_for_run(ls, project, tag)

    assert run is not None, f"Trace with tag '{tag}' not found in LangSmith within timeout"
    assert run.inputs is not None, "Trace should have inputs recorded"

    # The inputs should contain our message content somewhere
    inputs_str = json.dumps(run.inputs)
    assert message in inputs_str, (
        f"Expected message '{message}' in trace inputs, got: {inputs_str}"
    )
