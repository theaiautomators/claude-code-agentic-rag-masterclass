"""Tests for metadata-filtered retrieval in search_documents (US-016).

Tests verify that document_type and topics parameters filter search results correctly.
"""

import pytest
import os
import sys
from pathlib import Path
import uuid

# Add parent directory to path so we can import main module
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv
from main import search_documents

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def _get_supabase():
    """Get a Supabase client instance."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


class TestSearchDocumentsMetadataFilter:
    """Tests for metadata filtering in search_documents."""

    def test_search_documents_accepts_document_type_parameter(self):
        """Verify search_documents accepts document_type parameter."""
        from main import search_documents
        import inspect
        sig = inspect.signature(search_documents)
        params = list(sig.parameters.keys())
        assert "document_type" in params
        assert sig.parameters["document_type"].default is None

    def test_search_documents_accepts_topics_parameter(self):
        """Verify search_documents accepts topics parameter."""
        from main import search_documents
        import inspect
        sig = inspect.signature(search_documents)
        params = list(sig.parameters.keys())
        assert "topics" in params
        assert sig.parameters["topics"].default is None

    def test_search_documents_passes_filters_to_rpc(self):
        """Verify search_documents passes document_type and topics to RPC call."""
        from main import search_documents, _get_supabase
        from unittest.mock import patch, MagicMock
        
        # Create mock client
        mock_client = MagicMock()
        mock_client.rpc.return_value.execute.return_value = MagicMock(data=[])
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "test-project-id"}])
        
        # Mock _get_supabase to return our mock client
        with patch('main._get_supabase', return_value=mock_client):
            search_documents(
                query="test",
                top_k=5,
                threshold=0.0,
                document_type="article",
                topics=["testing"],
                mode="vector"
            )
            
            # Verify RPC was called with filter arguments
            mock_client.rpc.assert_called()
            call_args = mock_client.rpc.call_args
            
            # Check positional args: first arg should be function name, second is params dict
            assert call_args[0][0] == "search_chunks"
            params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
            
            # Params dict should contain filter keys
            assert "filter_document_type" in params
            assert "filter_topics" in params
            assert params["filter_document_type"] == "article"
            assert params["filter_topics"] == ["testing"]

    def test_search_documents_sql_migration_exists(self):
        """Verify US-016 migration file exists with correct filter SQL."""
        migration_path = Path(__file__).parent.parent / "supabase" / "migrations"
        migration_files = list(migration_path.glob("*us016*.sql"))
        assert len(migration_files) > 0, "US-016 migration file should exist"
        
        # Check the migration contains filter logic
        with open(migration_files[0], 'r') as f:
            content = f.read()
        
        assert "filter_document_type" in content
        assert "filter_topics" in content
        assert "d.document_type = filter_document_type" in content
        assert "d.topics && filter_topics" in content

    def test_search_documents_sql_uses_array_overlap_operator(self):
        """Verify topics filter uses PostgreSQL array overlap operator."""
        migration_path = Path(__file__).parent.parent / "supabase" / "migrations"
        migration_files = list(migration_path.glob("*us016*.sql"))
        
        with open(migration_files[0], 'r') as f:
            content = f.read()
        
        # Array overlap operator && for text[] matching
        assert "&&" in content, "Should use array overlap operator for topics"

    def test_search_documents_sql_has_optional_filter_pattern(self):
        """Verify filter uses optional pattern (NULL OR condition)."""
        migration_path = Path(__file__).parent.parent / "supabase" / "migrations"
        migration_files = list(migration_path.glob("*us016*.sql"))
        
        with open(migration_files[0], 'r') as f:
            content = f.read()
        
        # Optional filter pattern: column IS NULL OR column = value
        assert "filter_document_type is null or" in content.lower()
        assert "filter_topics         is null or" in content.lower()

    def test_search_documents_returns_table_with_metadata_columns(self):
        """Verify search_chunks RPC returns metadata columns."""
        migration_path = Path(__file__).parent.parent / "supabase" / "migrations"
        migration_files = list(migration_path.glob("*us016*.sql"))
        
        with open(migration_files[0], 'r') as f:
            content = f.read()
        
        # Check return table includes metadata columns
        assert "document_type text" in content
        assert "topics       text[]" in content
        assert "project_id   uuid" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
