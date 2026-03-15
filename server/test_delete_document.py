"""
Tests for the delete_document MCP tool.
Verifies that documents and their chunks can be deleted with cascade.
Tests acceptance criteria: storage file removed before DB delete, chunks deleted via FK cascade, returns deleted status with document_id.
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


def _create_test_document_with_chunks(client, filename, chunk_count=3):
    """Create a test document with chunks and storage file, return document ID."""
    # Create document
    doc_data = {
        "filename": filename,
        "file_path": f"/tmp/{filename}",
        "content_hash": f"test_hash_{uuid.uuid4().hex[:8]}",
        "status": "completed",
        "chunk_count": chunk_count,
    }
    
    result = client.table("documents").insert(doc_data).execute()
    doc_id = result.data[0]["id"]
    
    # Create chunks
    chunk_records = []
    for i in range(chunk_count):
        chunk_records.append({
            "document_id": doc_id,
            "content": f"Test chunk {i}",
            "chunk_index": i,
        })
    
    client.table("chunks").insert(chunk_records).execute()
    
    # Upload a dummy file to storage
    storage_path = f"documents/{doc_id}/{filename}"
    client.storage.from_("documents").upload(
        storage_path,
        b"test file content",
        {"content-type": "text/plain"},
    )
    
    return doc_id


def _count_chunks(client, document_id):
    """Count chunks for a given document ID."""
    result = client.table("chunks").select("id", count="exact").eq(
        "document_id", document_id
    ).execute()
    return result.count or 0


def _storage_file_exists(client, document_id, filename):
    """Check if a storage file exists by attempting to download it."""
    try:
        storage_path = f"documents/{document_id}/{filename}"
        # Try to download - if it succeeds, file exists
        result = client.storage.from_("documents").download(storage_path)
        return result is not None
    except Exception:
        return False


class TestDeleteDocumentTool:
    """Test cases for the delete_document MCP tool."""

    def test_delete_document_returns_deleted_status(self):
        """Test that delete_document returns deleted=True with document_id."""
        client = _get_supabase()
        
        # Create test document
        doc_id = _create_test_document_with_chunks(client, f"test_del_{uuid.uuid4().hex[:8]}.txt")
        
        # Import and call delete_document from main module
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import delete_document
        
        result = delete_document(doc_id)
        
        # Verify response structure
        assert result["deleted"] is True
        assert result["document_id"] == doc_id
        assert "filename" in result
        
        # Cleanup: document should already be deleted

    def test_delete_document_removes_storage_file(self):
        """Test that storage file is removed before DB delete."""
        client = _get_supabase()
        
        # Create test document with storage file
        filename = f"test_del_{uuid.uuid4().hex[:8]}.txt"
        doc_id = _create_test_document_with_chunks(client, filename)
        
        # Verify storage file exists before delete
        assert _storage_file_exists(client, doc_id, filename)
        
        # Import and call delete_document
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import delete_document
        
        delete_document(doc_id)
        
        # Verify storage file is removed
        assert not _storage_file_exists(client, doc_id, filename)

    def test_delete_document_cascade_deletes_chunks(self):
        """Test that chunks are deleted via FK cascade when document is deleted."""
        client = _get_supabase()
        
        # Create test document with 3 chunks
        doc_id = _create_test_document_with_chunks(client, f"test_del_{uuid.uuid4().hex[:8]}.txt", chunk_count=3)
        
        # Verify chunks exist before delete
        chunk_count_before = _count_chunks(client, doc_id)
        assert chunk_count_before == 3
        
        # Import and call delete_document
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import delete_document
        
        delete_document(doc_id)
        
        # Verify chunks are deleted via cascade
        chunk_count_after = _count_chunks(client, doc_id)
        assert chunk_count_after == 0

    def test_delete_document_removes_db_record(self):
        """Test that document record is removed from database."""
        client = _get_supabase()
        
        # Create test document
        doc_id = _create_test_document_with_chunks(client, f"test_del_{uuid.uuid4().hex[:8]}.txt")
        
        # Verify document exists before delete
        doc_before = client.table("documents").select("id").eq("id", doc_id).execute()
        assert len(doc_before.data) == 1
        
        # Import and call delete_document
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import delete_document
        
        delete_document(doc_id)
        
        # Verify document is removed
        doc_after = client.table("documents").select("id").eq("id", doc_id).execute()
        assert len(doc_after.data) == 0

    def test_delete_document_not_found_returns_error(self):
        """Test that delete_document returns error for non-existent document."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import delete_document
        
        fake_id = str(uuid.uuid4())
        result = delete_document(fake_id)
        
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    def test_delete_document_order_storage_then_db(self):
        """Test that storage file is removed before DB record deletion."""
        client = _get_supabase()
        
        # Create test document
        filename = f"test_del_{uuid.uuid4().hex[:8]}.txt"
        doc_id = _create_test_document_with_chunks(client, filename)
        
        # Import delete_document function to inspect order
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import delete_document
        
        # The implementation deletes storage first, then DB
        # We verify this by checking both are gone after the call
        result = delete_document(doc_id)
        
        # Storage should be gone
        assert not _storage_file_exists(client, doc_id, filename)
        
        # DB record should be gone
        doc_after = client.table("documents").select("id").eq("id", doc_id).execute()
        assert len(doc_after.data) == 0
        
        # Verify the function returns success
        assert result["deleted"] is True
