import os
import sys

# Ensure backend/ is on sys.path so "from config import ..." works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Marker for integration tests that need a real LangSmith API key
import pytest


def pytest_collection_modifyitems(config, items):
    """Auto-skip integration tests when LANGSMITH_API_KEY is not set."""
    skip_integration = pytest.mark.skip(
        reason="LANGSMITH_API_KEY not set — skipping integration test"
    )
    for item in items:
        if "test_tracing_integration" in str(item.fspath):
            if not os.environ.get("LANGSMITH_API_KEY"):
                item.add_marker(skip_integration)
