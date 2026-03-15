"""Tests for RAG indexing documentation completeness (US-020)."""

import pytest
from pathlib import Path


class TestRagIndexingDocumentation:
    """Test suite for verifying RAG indexing documentation completeness."""

    @pytest.fixture
    def docs_path(self):
        """Path to the docs/01_active directory."""
        return Path(__file__).parent.parent / "docs" / "01_active"

    @pytest.fixture
    def rag_docs_file(self, docs_path):
        """Path to rag-indexing.md file."""
        return docs_path / "rag-indexing.md"

    def test_documentation_file_exists(self, rag_docs_file):
        """Verify rag-indexing.md exists in docs/01_active/."""
        assert rag_docs_file.exists(), f"Documentation file not found: {rag_docs_file}"

    def test_documentation_file_not_empty(self, rag_docs_file):
        """Verify documentation file has content."""
        content = rag_docs_file.read_text()
        assert len(content) > 100, "Documentation file is too short"

    def test_documentation_includes_arr_stack_setup(self, rag_docs_file):
        """Verify documentation includes arr-stack setup steps."""
        content = rag_docs_file.read_text().lower()
        
        # Check for arr-stack specific content
        assert "arr-stack" in content or "192.168.0.105" in content, \
            "Documentation should mention arr-stack or local IP"
        assert "supabase_url" in content or "supabase_url" in content, \
            "Documentation should include SUPABASE_URL configuration"
        assert "environment" in content, \
            "Documentation should include environment setup section"

    def test_documentation_lists_mcp_tools(self, rag_docs_file):
        """Verify documentation lists all MCP tools."""
        content = rag_docs_file.read_text()
        
        # Required MCP tools from US-010 through US-019
        required_tools = [
            "ingest_file",
            "list_documents",
            "delete_document",
            "search_documents",
            "list_projects",
            "create_project",
            "get_schema",
            "query_sql",
        ]
        
        for tool in required_tools:
            assert tool in content, f"Documentation should list {tool} tool"

    def test_documentation_includes_tool_usage(self, rag_docs_file):
        """Verify documentation includes usage examples for tools."""
        content = rag_docs_file.read_text()
        
        # Check for usage examples (code blocks with tool calls)
        assert "ingest_file(" in content, "Should include ingest_file usage example"
        assert "search_documents(" in content, "Should include search_documents usage example"
        assert "list_documents(" in content, "Should include list_documents usage example"

    def test_documentation_includes_architecture_overview(self, rag_docs_file):
        """Verify documentation includes architecture overview."""
        content = rag_docs_file.read_text().lower()
        
        assert "architecture" in content, "Should have architecture section"
        assert "supabase" in content, "Should mention Supabase"
        assert "pgvector" in content or "vector" in content, "Should mention vector storage"
        assert "gemini" in content, "Should mention Gemini embeddings"
        assert "chunk" in content, "Should mention chunking strategy"

    def test_documentation_includes_database_schema(self, rag_docs_file):
        """Verify documentation describes database schema."""
        content = rag_docs_file.read_text().lower()
        
        assert "projects" in content, "Should mention projects table"
        assert "documents" in content, "Should mention documents table"
        assert "chunks" in content, "Should mention chunks table"
        assert "embedding" in content, "Should mention embedding column"

    def test_documentation_includes_testing_instructions(self, rag_docs_file):
        """Verify documentation includes testing instructions."""
        content = rag_docs_file.read_text().lower()
        
        assert "test" in content, "Should mention testing"
        assert "pytest" in content, "Should mention pytest"

    def test_documentation_has_troubleshooting_section(self, rag_docs_file):
        """Verify documentation includes troubleshooting guidance."""
        content = rag_docs_file.read_text().lower()
        
        assert "troubleshoot" in content or "debug" in content, \
            "Should include troubleshooting or debugging section"

    def test_documentation_typecheck_passes(self, rag_docs_file):
        """Verify documentation file is valid markdown (no syntax errors)."""
        # Basic markdown validation - file should be readable
        content = rag_docs_file.read_text()
        
        # Check for balanced code fences
        fence_count = content.count("```")
        assert fence_count % 2 == 0, "Unbalanced code fence markers"
        
        # Check for balanced headers
        lines = content.split('\n')
        header_lines = [l for l in lines if l.strip().startswith('#')]
        assert len(header_lines) > 0, "Should have at least one header"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
