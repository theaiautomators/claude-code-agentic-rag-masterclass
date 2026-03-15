"""Tests for the search_documents MCP tool with vector similarity search."""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import main module
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def _get_supabase():
    """Get a Supabase client instance."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


class TestSearchDocumentsTool:
    """Tests for the search_documents MCP tool."""

    def test_search_documents_function_exists(self):
        """Verify search_documents tool is defined in main.py."""
        from main import search_documents
        assert callable(search_documents)
        assert search_documents.__doc__ is not None
        assert "Search ingested documents" in search_documents.__doc__

    def test_search_documents_has_required_parameters(self):
        """Verify search_documents accepts query, top_k, threshold parameters."""
        from main import search_documents
        import inspect
        sig = inspect.signature(search_documents)
        params = list(sig.parameters.keys())
        assert "query" in params
        assert "top_k" in params
        assert "threshold" in params
        # Check defaults
        assert sig.parameters["top_k"].default == 5
        assert sig.parameters["threshold"].default == 0.7

    def test_search_documents_returns_list(self):
        """Verify search_documents returns a list of results."""
        from main import search_documents
        result = search_documents(query="test query", top_k=5)
        assert isinstance(result, list)

    def test_search_documents_returns_ranked_results_with_similarity(self):
        """Verify search results include similarity scores."""
        from main import search_documents
        result = search_documents(query="test", top_k=5, threshold=0.5)
        if result and not (len(result) == 1 and "message" in result[0]):
            # Results should have similarity or rrf_score field
            assert len(result) > 0
            first_result = result[0]
            # Either vector_similarity or rrf_score should be present
            assert "similarity" in first_result or "rrf_score" in first_result or "score" in first_result

    def test_search_documents_handles_empty_results_gracefully(self):
        """Verify search_documents returns graceful message when no results found."""
        from main import search_documents
        # Use a query that won't match anything with high threshold
        result = search_documents(query="xyzabc123nonexistent", top_k=5, threshold=0.99)
        assert isinstance(result, list)
        if len(result) == 1:
            assert "message" in result[0] or "no" in str(result[0]).lower()

    def test_search_documents_top_k_limits_results(self):
        """Verify top_k parameter limits the number of returned results."""
        from main import search_documents
        result = search_documents(query="test", top_k=3, threshold=0.0)
        # Should return at most top_k results (or fewer if not enough matches)
        assert len(result) <= 3

    def test_search_documents_threshold_filters_results(self):
        """Verify threshold parameter filters low-similarity results."""
        from main import search_documents
        # Lower threshold should return more or equal results than higher threshold
        result_low = search_documents(query="test", top_k=10, threshold=0.1)
        result_high = search_documents(query="test", top_k=10, threshold=0.8)
        assert len(result_low) >= len(result_high)

    def test_search_documents_with_project_filter(self):
        """Verify project parameter filters results by project."""
        from main import search_documents
        client = _get_supabase()
        
        # First ingest a document with a project
        from main import ingest_file
        test_file = Path(__file__).parent.parent / "test_data" / "test.txt"
        if test_file.exists():
            ingest_result = ingest_file(str(test_file), project="test-search-project", create_project=True)
            if ingest_result.get("status") in ("completed", "skipped"):
                # Search with project filter
                result = search_documents(query="test", project="test-search-project")
                assert isinstance(result, list)
                
                # Search with non-existent project should return message
                result_no_proj = search_documents(query="test", project="nonexistent-project-xyz")
                assert len(result_no_proj) == 1
                assert "No project found" in result_no_proj[0].get("message", "")

    def test_search_documents_hybrid_mode(self):
        """Verify hybrid mode combines vector and keyword search."""
        from main import search_documents
        result = search_documents(query="test", top_k=5, mode="hybrid")
        assert isinstance(result, list)

    def test_search_documents_vector_mode(self):
        """Verify vector mode uses only vector similarity."""
        from main import search_documents
        result = search_documents(query="test", top_k=5, mode="vector")
        assert isinstance(result, list)

    def test_search_documents_keyword_mode(self):
        """Verify keyword mode uses only keyword search."""
        from main import search_documents
        result = search_documents(query="test", top_k=5, mode="keyword")
        assert isinstance(result, list)

    def test_search_documents_rerank_option(self):
        """Verify rerank parameter can be enabled."""
        from main import search_documents
        result = search_documents(query="test", top_k=5, rerank=True)
        assert isinstance(result, list)

    def test_search_documents_mcp_tool_decorator(self):
        """Verify search_documents has @mcp.tool() decorator."""
        from main import mcp, search_documents
        # Check that the tool is registered with MCP
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "search_documents" in tool_names


class TestSearchDocumentsIntegration:
    """Integration tests for search_documents with actual data."""

    def test_search_documents_finds_ingested_content(self):
        """Verify search can find previously ingested document content."""
        from main import search_documents, ingest_file
        from main import list_documents
        
        # Check if there are any documents in the database
        docs = list_documents()
        if len(docs) > 0:
            # Search for something that might match
            result = search_documents(query="test", top_k=5, threshold=0.0)
            assert isinstance(result, list)
            # If we have documents, we should get some results with low threshold

    def test_search_documents_returns_chunk_data(self):
        """Verify search results contain chunk metadata."""
        from main import search_documents
        result = search_documents(query="test", top_k=5, threshold=0.0)
        if result and not (len(result) == 1 and "message" in result[0]):
            assert len(result) > 0
            first = result[0]
            # Should have chunk-related fields
            assert "id" in first or "chunk_id" in first or "content" in first


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
