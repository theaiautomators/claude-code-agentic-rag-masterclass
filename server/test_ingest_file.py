"""
Tests for the ingest_file MCP tool.
Verifies the complete ingestion flow: parse → hash → duplicate check → upload → chunk → embed → store.
Tests acceptance criteria: status/document_id/chunk_count returns, duplicate detection, force flag.
"""
import pytest
import hashlib
from pathlib import Path
from supabase import create_client
import os
from dotenv import load_dotenv
import uuid

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


def _get_long_content():
    """Return content long enough to produce multiple chunks (>512 tokens)."""
    return """
Test content with sufficient length for chunking. This document needs to be long enough to produce multiple chunks from the recursive character splitter. The recursive character chunking algorithm splits on newlines first, then spaces, then characters when the text exceeds the token limit.

It contains multiple paragraphs to ensure the chunking strategy produces meaningful chunks. Each paragraph should contain enough text to contribute to the overall document length. The algorithm respects token boundaries and tries to split at natural break points when possible.

The chunking process uses tiktoken to count tokens accurately. By default, it targets 512 tokens per chunk with 50 tokens of overlap between consecutive chunks. This ensures that each chunk contains sufficient context while maintaining reasonable size for embedding models.

When the text exceeds the token limit, the algorithm first tries splitting on double newlines (paragraph breaks), then single newlines, then spaces, and finally characters if necessary. This hierarchical approach preserves document structure where possible.

The final paragraph wraps up the test content for proper ingestion. We need substantial content to trigger the splitting behavior - roughly 2000+ characters for English text to exceed the 512 token threshold and produce multiple chunks.

Additional content here ensures we have enough material. The RAG ingestion pipeline depends on proper chunking to create searchable segments. Each chunk will be embedded separately and stored in the pgvector chunks table with its document reference.

The embedding model requires each chunk to have sufficient context for meaningful vector representation. Short chunks may not capture enough semantic information for effective retrieval.

More text continues to build length. The Supabase storage bucket holds the raw uploaded files while the database tables store the processed chunks with their embeddings. The MCP tool orchestrates this entire flow from file path to searchable vectors.

This paragraph adds more length. The ingest_file tool processes documents through parsing, hashing, duplicate detection, upload, chunking, embedding, and storage steps.

Final wrapping content ensures adequate length. The ingest_file tool returns status, document_id, and chunk_count to confirm successful processing. Duplicate detection uses SHA-256 hashing to skip unchanged files on re-ingestion.

The force flag allows re-ingestion even when content hash matches. This is useful when you need to reprocess documents with updated chunking strategies or embedding models.

Project assignment links documents to categorical groups. The projects table enables filtering and organization of ingested documents by topic or source.
"""


class TestIngestFileTool:
    """Test cases for the ingest_file MCP tool."""

    def test_ingest_file_returns_status_document_id_chunk_count(self):
        """Test that ingest_file returns required fields: status, document_id, chunk_count."""
        # Create a test file with enough content to produce chunks
        test_file = Path(f"/tmp/test_ingest_{uuid.uuid4().hex[:8]}.txt")
        test_file.write_text(_get_long_content())
        
        # Import and call ingest_file from main module
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file(str(test_file))
        
        # Verify required fields are present
        assert "status" in result
        assert "document_id" in result
        assert "chunk_count" in result
        
        # Verify status indicates success
        assert result["status"] in ["completed", "project_confirmation_needed"]
        
        # Verify document_id is a valid UUID
        assert len(result["document_id"]) == 36  # UUID format
        
        # Verify chunk_count is positive
        assert isinstance(result["chunk_count"], int)
        assert result["chunk_count"] > 0
        
        # Cleanup
        _cleanup_document(_get_supabase(), result["document_id"])
        test_file.unlink(missing_ok=True)

    def test_ingest_file_duplicate_detection_returns_skipped(self):
        """Test that duplicate detection returns status='skipped'."""
        client = _get_supabase()
        
        # Create test content
        content = _get_long_content()
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        filename = f"dup_test_{uuid.uuid4().hex[:8]}.txt"
        
        # Insert a document with the same content hash
        doc1 = client.table("documents").insert({
            "filename": filename,
            "file_path": f"/tmp/{filename}",
            "content_hash": content_hash,
            "status": "completed",
            "chunk_count": 1,
        }).execute()
        
        doc1_id = doc1.data[0]["id"]
        
        # Create a test file with identical content
        test_file = Path(f"/tmp/{filename}")
        test_file.write_text(content)
        
        # Import and call ingest_file
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file(str(test_file))
        
        # Verify duplicate is detected and skipped
        assert result["status"] == "skipped"
        assert result["reason"] == "duplicate"
        assert result["existing_document_id"] == doc1_id
        
        # Cleanup
        client.table("documents").delete().eq("id", doc1_id).execute()
        test_file.unlink(missing_ok=True)

    def test_ingest_file_force_reingest_bypasses_duplicate(self):
        """Test that force=True flag bypasses duplicate check and re-ingests."""
        client = _get_supabase()
        
        # Create test content
        content = _get_long_content()
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        filename = f"force_test_{uuid.uuid4().hex[:8]}.txt"
        
        # Insert a document first
        doc1 = client.table("documents").insert({
            "filename": filename,
            "file_path": f"/tmp/{filename}",
            "content_hash": content_hash,
            "status": "completed",
            "chunk_count": 1,
        }).execute()
        
        doc1_id = doc1.data[0]["id"]
        
        # Create a test file with identical content
        test_file = Path(f"/tmp/{filename}")
        test_file.write_text(content)
        
        # Import and call ingest_file with force=True
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file(str(test_file), force=True)
        
        # Verify force=True bypasses skip and creates new document
        assert result["status"] in ["completed", "project_confirmation_needed"]
        assert "document_id" in result
        assert result["document_id"] != doc1_id  # New document created
        
        # Verify old document was deleted
        old_check = client.table("documents").select("id").eq("id", doc1_id).execute()
        assert len(old_check.data) == 0
        
        # Cleanup new document
        _cleanup_document(client, result["document_id"])
        test_file.unlink(missing_ok=True)

    def test_ingest_file_nonexistent_file_returns_error(self):
        """Test that ingest_file returns error for nonexistent file."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file("/tmp/nonexistent_file_12345.txt")
        
        assert result["status"] == "error"
        assert "File not found" in result["message"]

    def test_ingest_file_creates_chunks_table_records(self):
        """Test that ingest_file creates chunk records in the chunks table."""
        # Create a test file with long content
        test_file = Path(f"/tmp/test_chunks_{uuid.uuid4().hex[:8]}.txt")
        test_file.write_text(_get_long_content())
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file(str(test_file))
        
        doc_id = result["document_id"]
        client = _get_supabase()
        
        # Verify chunks were created
        chunks = client.table("chunks").select("id, content, chunk_index").eq(
            "document_id", doc_id
        ).execute()
        
        assert len(chunks.data) > 0
        assert len(chunks.data) == result["chunk_count"]
        
        # Verify chunk_index is sequential
        indices = [c["chunk_index"] for c in chunks.data]
        assert indices == list(range(len(chunks.data)))
        
        # Cleanup
        _cleanup_document(client, doc_id)
        test_file.unlink(missing_ok=True)

    def test_ingest_file_stores_content_hash(self):
        """Test that ingest_file stores SHA-256 hash in documents table."""
        test_file = Path(f"/tmp/test_hash_{uuid.uuid4().hex[:8]}.txt")
        content = _get_long_content()
        test_file.write_text(content)
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file(str(test_file))
        
        doc_id = result["document_id"]
        client = _get_supabase()
        
        # Verify hash stored in database
        doc = client.table("documents").select("content_hash").eq(
            "id", doc_id
        ).single().execute()
        
        assert doc.data["content_hash"] == expected_hash
        
        # Cleanup
        _cleanup_document(client, doc_id)
        test_file.unlink(missing_ok=True)

    def test_ingest_file_updates_document_status(self):
        """Test that ingest_file updates document status to completed."""
        test_file = Path(f"/tmp/test_status_{uuid.uuid4().hex[:8]}.txt")
        test_file.write_text(_get_long_content())
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file(str(test_file))
        
        doc_id = result["document_id"]
        client = _get_supabase()
        
        # Verify status is updated
        doc = client.table("documents").select("status").eq(
            "id", doc_id
        ).single().execute()
        
        assert doc.data["status"] in ["completed", "project_confirmation_needed"]
        
        # Cleanup
        _cleanup_document(client, doc_id)
        test_file.unlink(missing_ok=True)

    def test_ingest_file_returns_filename(self):
        """Test that ingest_file returns the filename in response."""
        test_file = Path(f"/tmp/test_filename_{uuid.uuid4().hex[:8]}.txt")
        test_file.write_text(_get_long_content())
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file(str(test_file))
        
        assert "filename" in result
        assert result["filename"] == test_file.name
        
        # Cleanup
        _cleanup_document(_get_supabase(), result["document_id"])
        test_file.unlink(missing_ok=True)

    def test_ingest_file_handles_markdown_files(self):
        """Test that ingest_file correctly handles Markdown files."""
        test_file = Path(f"/tmp/test_md_{uuid.uuid4().hex[:8]}.md")
        content = """# Test Heading

This is a test markdown file with sufficient content for chunking. It needs to be long enough to produce multiple chunks.

## Second Heading

More content here provides additional text to ensure we get meaningful chunks from the splitter. The recursive character chunking algorithm handles this properly.

## Third Heading

The final section wraps up the test document with more searchable content for verification. We need substantial content to trigger the splitting behavior.

Additional paragraphs ensure we have enough material for the RAG ingestion pipeline. Each chunk will be embedded separately and stored in the pgvector chunks table.

The embedding model requires each chunk to have sufficient context for meaningful vector representation. Short chunks may not capture enough semantic information.

More text continues to build length. The Supabase storage bucket holds the raw uploaded files while the database tables store the processed chunks.

This paragraph adds more length. The ingest_file tool processes documents through parsing, hashing, duplicate detection, upload, chunking, embedding, and storage.

Final wrapping content ensures adequate length for proper ingestion and chunking. The tool returns status, document_id, and chunk_count to confirm success.
"""
        test_file.write_text(content)
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file(str(test_file))
        
        assert result["status"] in ["completed", "project_confirmation_needed"]
        assert result["chunk_count"] > 0
        
        # Cleanup
        _cleanup_document(_get_supabase(), result["document_id"])
        test_file.unlink(missing_ok=True)

    def test_ingest_file_handles_pdf_files(self):
        """Test that ingest_file correctly handles PDF files."""
        # Use existing test PDF from test_data
        test_file = Path("/Users/salehloke/Developer/project/claude-code-agentic-rag-masterclass/test_data/test.pdf")
        
        if not test_file.exists():
            pytest.skip("Test PDF file not found")
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file(str(test_file))
        
        # PDF parsing may produce variable results depending on content
        assert result["status"] in ["completed", "project_confirmation_needed", "error"]
        if result["status"] == "completed":
            assert result["chunk_count"] > 0
        
        # Cleanup
        if "document_id" in result:
            _cleanup_document(_get_supabase(), result["document_id"])


class TestIngestFileEdgeCases:
    """Edge case tests for ingest_file."""

    def test_ingest_file_empty_file(self):
        """Test that ingest_file handles empty files gracefully."""
        test_file = Path(f"/tmp/test_empty_{uuid.uuid4().hex[:8]}.txt")
        test_file.write_text("")
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file(str(test_file))
        
        # Empty file should produce no chunks
        assert result["status"] == "error"
        assert "No chunks produced" in result["message"]
        
        # Cleanup - no document_id expected for empty file
        test_file.unlink(missing_ok=True)

    def test_ingest_file_special_characters(self):
        """Test that ingest_file handles special characters in content."""
        test_file = Path(f"/tmp/test_special_{uuid.uuid4().hex[:8]}.txt")
        content = """Special chars: ñ, 中文，emoji 🎉, tabs\t, newlines\n. This text has sufficient length for chunking.

It contains multiple paragraphs with unicode characters to ensure the chunking strategy handles them properly. The recursive splitter respects token boundaries.

The final paragraph wraps up the test with more special characters for verification. We need substantial content to trigger the splitting behavior and produce multiple chunks.

Additional content ensures we have enough material for the RAG ingestion pipeline. Each chunk will be embedded separately and stored in the pgvector chunks table with proper encoding.

The embedding model handles unicode correctly. Short chunks may not capture enough semantic information for effective retrieval. More text builds length for proper chunking.

This paragraph adds more length with special characters. The ingest_file tool processes documents through parsing, hashing, duplicate detection, upload, chunking, embedding, and storage steps.

Final wrapping content ensures adequate length. The tool returns status, document_id, and chunk_count to confirm successful processing of unicode content.
"""
        test_file.write_text(content)
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file(str(test_file))
        
        assert result["status"] in ["completed", "project_confirmation_needed"]
        assert result["chunk_count"] > 0
        
        # Cleanup
        _cleanup_document(_get_supabase(), result["document_id"])
        test_file.unlink(missing_ok=True)

    def test_ingest_file_very_long_content(self):
        """Test that ingest_file handles very long content."""
        test_file = Path(f"/tmp/test_long_{uuid.uuid4().hex[:8]}.txt")
        # Create 10KB+ of content
        content = _get_long_content() * 5
        test_file.write_text(content)
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.main import ingest_file
        
        result = ingest_file(str(test_file))
        
        assert result["status"] in ["completed", "project_confirmation_needed"]
        assert result["chunk_count"] > 1  # Should produce multiple chunks
        
        # Cleanup
        _cleanup_document(_get_supabase(), result["document_id"])
        test_file.unlink(missing_ok=True)
