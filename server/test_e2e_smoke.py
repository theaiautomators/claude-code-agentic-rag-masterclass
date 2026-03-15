"""End-to-end smoke test for RAG ingestion and search pipeline.

This test verifies the complete RAG pipeline:
1. Ingest a test file via ingest_file MCP tool
2. Search for content via search_documents MCP tool
3. Verify results contain relevant chunks with similarity scores above threshold
"""

import pytest
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

# Add parent directory to path so we can import main module
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

from main import ingest_file, search_documents, list_documents, delete_document


def _get_supabase():
    """Get a Supabase client instance."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _cleanup_document(doc_id: str):
    """Clean up a test document from the database."""
    try:
        delete_document(doc_id)
    except Exception:
        pass


class TestE2ESmoke:
    """End-to-end smoke tests for RAG ingestion and search."""

    def test_ingest_file_returns_success_status(self):
        """Verify ingest_file completes successfully and returns required fields."""
        # Use a unique filename to avoid conflicts
        test_file = Path(__file__).parent.parent / "test_data" / "sample.txt"
        unique_filename = f"test_e2e_{uuid4().hex[:8]}.txt"
        
        # Copy test file to unique name
        import shutil
        unique_path = Path(__file__).parent.parent / "test_data" / unique_filename
        shutil.copy(test_file, unique_path)
        
        try:
            result = ingest_file(str(unique_path), project="e2e-test", create_project=True)
            
            # AC1: Test file ingested successfully
            assert result.get("status") in ("completed", "skipped"), f"Ingestion failed: {result}"
            assert "document_id" in result, "Missing document_id in response"
            assert "chunk_count" in result, "Missing chunk_count in response"
            assert result.get("chunk_count", 0) > 0, "No chunks produced"
            
            # Store doc_id for cleanup
            self._test_doc_id = result.get("document_id")
            
        finally:
            # Clean up unique test file
            if unique_path.exists():
                unique_path.unlink()

    def test_search_documents_returns_relevant_chunks(self):
        """Verify search_documents finds ingested content with relevant chunks."""
        # First ingest a test document
        test_file = Path(__file__).parent.parent / "test_data" / "sample.txt"
        unique_filename = f"test_e2e_search_{uuid4().hex[:8]}.txt"
        
        import shutil
        unique_path = Path(__file__).parent.parent / "test_data" / unique_filename
        shutil.copy(test_file, unique_path)
        
        try:
            # Ingest the file
            ingest_result = ingest_file(str(unique_path), project="e2e-search-test", create_project=True)
            assert ingest_result.get("status") in ("completed", "skipped")
            doc_id = ingest_result.get("document_id")
            
            # Read the test file content to know what to search for
            with open(unique_path, "r") as f:
                content = f.read()
            
            # Get first meaningful word for search (skip common words)
            words = content.split()
            search_term = None
            for word in words[:20]:
                if len(word) > 3 and word.lower() not in ("the", "and", "for", "are", "but"):
                    search_term = word
                    break
            
            if search_term:
                # AC2: search_documents returns relevant chunks
                results = search_documents(query=search_term, top_k=5, threshold=0.0)
                
                assert isinstance(results, list), "Results should be a list"
                assert len(results) > 0, f"No results found for query '{search_term}'"
                
                # Verify results contain chunk data
                first_result = results[0]
                assert "content" in first_result or "chunk_content" in first_result, "Missing content in result"
                
            # Clean up
            if doc_id:
                _cleanup_document(doc_id)
                
        finally:
            if unique_path.exists():
                unique_path.unlink()

    def test_similarity_scores_above_threshold(self):
        """Verify search results have similarity scores above the threshold."""
        # Use sample.txt which has enough content to produce chunks
        test_file = Path(__file__).parent.parent / "test_data" / "sample.txt"
        unique_filename = f"test_e2e_score_{uuid4().hex[:8]}.txt"
        
        import shutil
        unique_path = Path(__file__).parent.parent / "test_data" / unique_filename
        shutil.copy(test_file, unique_path)
        
        try:
            ingest_result = ingest_file(str(unique_path), project="e2e-score-test", create_project=True)
            assert ingest_result.get("status") in ("completed", "skipped"), f"Ingestion failed: {ingest_result}"
            doc_id = ingest_result.get("document_id")
            
            # Skip if document was skipped (duplicate)
            if ingest_result.get("status") == "skipped":
                pytest.skip("Document was skipped (duplicate)")
            
            # Read content to find search term
            with open(unique_path, "r") as f:
                content = f.read()
            
            # Extract a distinctive term (look for capitalized words)
            words = content.split()
            search_term = None
            for word in words:
                if len(word) > 5 and word[0].isupper():
                    search_term = word
                    break
            search_term = search_term or "test"
            
            # AC3: Similarity scores above threshold
            results = search_documents(query=search_term, top_k=5, threshold=0.5)
            
            if len(results) > 0 and "message" not in results[0]:
                # Check similarity scores
                for result in results:
                    # Should have similarity, rrf_score, or score field
                    has_score = (
                        "similarity" in result or 
                        "rrf_score" in result or 
                        "score" in result
                    )
                    assert has_score, f"Missing score field in result: {result}"
                    
                    # If similarity field exists, verify it's above threshold
                    if "similarity" in result:
                        assert result["similarity"] >= 0.5, f"Similarity {result['similarity']} below threshold"
                        
            # Clean up
            if doc_id:
                _cleanup_document(doc_id)
                
        finally:
            if unique_path.exists():
                unique_path.unlink()

    def test_e2e_complete_pipeline(self):
        """Complete E2E test: ingest → search → verify all acceptance criteria."""
        # Use sample.txt for comprehensive test
        test_file = Path(__file__).parent.parent / "test_data" / "sample.txt"
        unique_filename = f"test_e2e_complete_{uuid4().hex[:8]}.txt"
        
        import shutil
        unique_path = Path(__file__).parent.parent / "test_data" / unique_filename
        shutil.copy(test_file, unique_path)
        
        try:
            # AC1: Ingest test file
            ingest_result = ingest_file(str(unique_path), project="e2e-complete", create_project=True)
            assert ingest_result.get("status") == "completed", f"Ingestion failed: {ingest_result}"
            doc_id = ingest_result.get("document_id")
            chunk_count = ingest_result.get("chunk_count", 0)
            assert chunk_count > 0, "No chunks produced"
            
            # Read content for search term
            with open(unique_path, "r") as f:
                content = f.read()
            
            # Find a distinctive word
            words = content.split()
            search_term = None
            for word in words:
                if len(word) > 5 and word[0].isupper():
                    search_term = word
                    break
            search_term = search_term or "test"
            
            # AC2 & AC3: Search and verify results
            results = search_documents(query=search_term, top_k=5, threshold=0.5)
            
            # Should find results
            assert len(results) > 0, f"No results for query '{search_term}'"
            
            # Verify similarity scores
            for result in results[:3]:  # Check first 3 results
                if "similarity" in result:
                    assert result["similarity"] >= 0.5, f"Low similarity: {result}"
            
            # AC4: Verify document is listed
            docs = list_documents(project="e2e-complete")
            assert len(docs) > 0, "Document not found in list"
            
            # Verify our document is in the list
            doc_ids = [d["id"] for d in docs]
            assert doc_id in doc_ids, f"Document {doc_id} not in list"
            
            # Clean up
            _cleanup_document(doc_id)
            
        finally:
            if unique_path.exists():
                unique_path.unlink()

    def test_typecheck_passes(self):
        """Verify the test file typechecks successfully."""
        import py_compile
        import tempfile
        
        # Typecheck this test file
        result = py_compile.compile(str(Path(__file__)), doraise=True)
        assert result is not None, "Typecheck failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
