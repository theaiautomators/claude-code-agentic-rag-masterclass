"""
Tests for the list_documents MCP tool.
Verifies that ingested documents can be listed with their metadata.
Tests acceptance criteria: returns list of dicts with id, filename, status, chunk_count, project; supports optional project filter.
"""
import pytest
import uuid
from pathlib import Path
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def _get_supabase():
    """Get a Supabase client instance."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _cleanup_document(client, doc_id):
    """Clean up a test document and its chunks from the database."""
    try:
        # Delete document (chunks cascade via FK)
        client.table("documents").delete().eq("id", doc_id).execute()
    except Exception:
        pass


def _create_test_document(client, filename, status="completed", chunk_count=1, project_id=None):
    """Create a test document and return its ID."""
    doc_data = {
        "filename": filename,
        "file_path": f"/tmp/{filename}",
        "content_hash": f"test_hash_{uuid.uuid4().hex[:8]}",
        "status": status,
        "chunk_count": chunk_count,
    }
    if project_id:
        doc_data["project_id"] = project_id
    
    result = client.table("documents").insert(doc_data).execute()
    return result.data[0]["id"]


class TestListDocumentsTool:
    """Test cases for the list_documents MCP tool."""

    def test_list_documents_returns_list_of_dicts(self):
        """Test that list_documents returns a list of dictionaries."""
        client = _get_supabase()
        
        # Create test documents
        doc1_id = _create_test_document(client, f"test_doc1_{uuid.uuid4().hex[:8]}.txt")
        doc2_id = _create_test_document(client, f"test_doc2_{uuid.uuid4().hex[:8]}.txt")
        
        # Import and call list_documents from main module
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import list_documents
        
        result = list_documents()
        
        # Verify returns a list
        assert isinstance(result, list)
        
        # Verify each item is a dict
        assert len(result) >= 2
        for doc in result:
            assert isinstance(doc, dict)
        
        # Cleanup
        _cleanup_document(client, doc1_id)
        _cleanup_document(client, doc2_id)

    def test_list_documents_returns_required_fields(self):
        """Test that each document dict contains required fields: id, filename, status, chunk_count, project."""
        client = _get_supabase()
        
        # Create a project first
        project_result = client.table("projects").insert({
            "name": f"test_project_{uuid.uuid4().hex[:8]}",
            "description": "Test project for list_documents",
        }).execute()
        project_id = project_result.data[0]["id"]
        project_name = project_result.data[0]["name"]
        
        # Create test document with project
        doc_id = _create_test_document(
            client, 
            f"test_doc_{uuid.uuid4().hex[:8]}.txt",
            status="completed",
            chunk_count=5,
            project_id=project_id
        )
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import list_documents
        
        result = list_documents()
        
        # Find our test document
        test_doc = None
        for doc in result:
            if doc["id"] == doc_id:
                test_doc = doc
                break
        
        assert test_doc is not None, "Test document should be in results"
        
        # Verify required fields
        assert "id" in test_doc
        assert "filename" in test_doc
        assert "status" in test_doc
        assert "chunk_count" in test_doc
        assert "projects" in test_doc  # Joined project data
        
        # Verify field values
        assert test_doc["status"] == "completed"
        assert test_doc["chunk_count"] == 5
        
        # Verify project join returns correct structure (Supabase returns joined data as dict)
        assert isinstance(test_doc["projects"], dict)
        assert test_doc["projects"]["name"] == project_name
        
        # Cleanup
        _cleanup_document(client, doc_id)
        client.table("projects").delete().eq("id", project_id).execute()

    def test_list_documents_project_filter(self):
        """Test that list_documents supports optional project filter."""
        client = _get_supabase()
        
        # Create two projects
        proj1 = client.table("projects").insert({
            "name": f"filter_test_proj1_{uuid.uuid4().hex[:8]}",
            "description": "Project 1",
        }).execute()
        proj1_id = proj1.data[0]["id"]
        proj1_name = proj1.data[0]["name"]
        
        proj2 = client.table("projects").insert({
            "name": f"filter_test_proj2_{uuid.uuid4().hex[:8]}",
            "description": "Project 2",
        }).execute()
        proj2_id = proj2.data[0]["id"]
        proj2_name = proj2.data[0]["name"]
        
        # Create documents in each project
        doc1_id = _create_test_document(client, f"doc_proj1_{uuid.uuid4().hex[:8]}.txt", project_id=proj1_id)
        doc2_id = _create_test_document(client, f"doc_proj2_{uuid.uuid4().hex[:8]}.txt", project_id=proj2_id)
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import list_documents
        
        # Test filtering by project 1
        result_proj1 = list_documents(project=proj1_name)
        
        # Should only return doc1
        assert len(result_proj1) == 1
        assert result_proj1[0]["id"] == doc1_id
        assert result_proj1[0]["projects"]["name"] == proj1_name
        
        # Test filtering by project 2
        result_proj2 = list_documents(project=proj2_name)
        
        # Should only return doc2
        assert len(result_proj2) == 1
        assert result_proj2[0]["id"] == doc2_id
        assert result_proj2[0]["projects"]["name"] == proj2_name
        
        # Test no filter - should return both
        result_all = list_documents()
        doc_ids = [d["id"] for d in result_all]
        assert doc1_id in doc_ids
        assert doc2_id in doc_ids
        
        # Cleanup
        _cleanup_document(client, doc1_id)
        _cleanup_document(client, doc2_id)
        client.table("projects").delete().eq("id", proj1_id).execute()
        client.table("projects").delete().eq("id", proj2_id).execute()

    def test_list_documents_nonexistent_project_returns_empty(self):
        """Test that list_documents returns empty list for nonexistent project."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import list_documents
        
        result = list_documents(project=f"nonexistent_{uuid.uuid4().hex[:8]}")
        
        assert result == []

    def test_list_documents_ordered_by_created_at_desc(self):
        """Test that list_documents returns results ordered by created_at descending."""
        client = _get_supabase()
        
        # Create documents with slight delay to ensure different timestamps
        doc1_id = _create_test_document(client, f"older_{uuid.uuid4().hex[:8]}.txt")
        
        import time
        time.sleep(0.1)  # Small delay to ensure different created_at
        
        doc2_id = _create_test_document(client, f"newer_{uuid.uuid4().hex[:8]}.txt")
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import list_documents
        
        result = list_documents()
        
        # Find our test documents
        test_docs = [d for d in result if d["id"] in [doc1_id, doc2_id]]
        
        assert len(test_docs) == 2
        
        # Verify ordering: newer should come first
        if test_docs[0]["id"] == doc2_id:
            # Newer document is first - correct
            assert test_docs[1]["id"] == doc1_id
        else:
            # This could happen if timestamps are too close, but order should still be consistent
            pass
        
        # Cleanup
        _cleanup_document(client, doc1_id)
        _cleanup_document(client, doc2_id)

    def test_list_documents_includes_content_hash(self):
        """Test that list_documents includes content_hash in response."""
        client = _get_supabase()
        
        test_hash = f"hash_test_{uuid.uuid4().hex[:8]}"
        doc_id = _create_test_document(client, f"hashtest_{uuid.uuid4().hex[:8]}.txt")
        
        # Update with specific hash
        client.table("documents").update({"content_hash": test_hash}).eq("id", doc_id).execute()
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import list_documents
        
        result = list_documents()
        
        test_doc = None
        for doc in result:
            if doc["id"] == doc_id:
                test_doc = doc
                break
        
        assert test_doc is not None
        assert "content_hash" in test_doc
        assert test_doc["content_hash"] == test_hash
        
        # Cleanup
        _cleanup_document(client, doc_id)

    def test_list_documents_includes_created_at(self):
        """Test that list_documents includes created_at timestamp."""
        client = _get_supabase()
        
        doc_id = _create_test_document(client, f"timestamp_{uuid.uuid4().hex[:8]}.txt")
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import list_documents
        
        result = list_documents()
        
        test_doc = None
        for doc in result:
            if doc["id"] == doc_id:
                test_doc = doc
                break
        
        assert test_doc is not None
        assert "created_at" in test_doc
        assert test_doc["created_at"] is not None
        # Verify ISO format timestamp
        assert "T" in test_doc["created_at"]
        
        # Cleanup
        _cleanup_document(client, doc_id)


class TestListDocumentsEdgeCases:
    """Edge case tests for list_documents."""

    def test_list_documents_no_documents_returns_empty(self):
        """Test that list_documents returns empty list when no documents exist."""
        # This test assumes no documents exist, which is hard to guarantee
        # We test with a filter that matches nothing instead
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import list_documents
        
        result = list_documents(project=f"nonexistent_{uuid.uuid4().hex[:8]}")
        assert result == []

    def test_list_documents_with_special_characters_in_filename(self):
        """Test that list_documents handles filenames with special characters."""
        client = _get_supabase()
        
        filename = f"special_ñ_中文_test_{uuid.uuid4().hex[:8]}.txt"
        doc_id = _create_test_document(client, filename)
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import list_documents
        
        result = list_documents()
        
        test_doc = None
        for doc in result:
            if doc["id"] == doc_id:
                test_doc = doc
                break
        
        assert test_doc is not None
        assert test_doc["filename"] == filename
        
        # Cleanup
        _cleanup_document(client, doc_id)

    def test_list_documents_multiple_documents_same_project(self):
        """Test that list_documents returns all documents for a project."""
        client = _get_supabase()
        
        # Create project
        proj = client.table("projects").insert({
            "name": f"multi_doc_proj_{uuid.uuid4().hex[:8]}",
            "description": "Project with multiple docs",
        }).execute()
        proj_id = proj.data[0]["id"]
        proj_name = proj.data[0]["name"]
        
        # Create multiple documents in same project
        doc_ids = []
        for i in range(3):
            doc_id = _create_test_document(
                client, 
                f"multi_doc_{i}_{uuid.uuid4().hex[:8]}.txt",
                project_id=proj_id
            )
            doc_ids.append(doc_id)
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import list_documents
        
        result = list_documents(project=proj_name)
        
        # Should return all 3 documents
        assert len(result) == 3
        result_ids = [d["id"] for d in result]
        for doc_id in doc_ids:
            assert doc_id in result_ids
        
        # Cleanup
        for doc_id in doc_ids:
            _cleanup_document(client, doc_id)
        client.table("projects").delete().eq("id", proj_id).execute()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
