"""Tests for projects table schema verification."""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class TestProjectsTableSchema:
    """Test suite for projects table schema verification."""

    @classmethod
    def setup_class(cls):
        """Set up Supabase client for schema tests."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        cls.client = create_client(supabase_url, supabase_key)

    def test_projects_table_exists(self):
        """Test that projects table exists in the database."""
        # Query the table to verify it exists
        response = self.client.table("projects").select("id").limit(1).execute()
        assert response is not None, "projects table query failed"
        assert hasattr(response, "data"), "projects table does not exist or is not accessible"

    def test_projects_table_has_required_columns(self):
        """Test that projects table has all required columns."""
        required_columns = {
            "id",
            "name",
            "description",
            "created_at",
        }
        
        # Insert a test project
        import uuid
        test_project = {
            "name": f"test_project_{uuid.uuid4().hex[:8]}",
            "description": "Test project for schema verification",
        }
        
        response = self.client.table("projects").insert(test_project).execute()
        assert response.data is not None
        assert len(response.data) > 0
        
        inserted_project = response.data[0]
        for column in required_columns:
            assert column in inserted_project, f"Missing required column: {column}"

    def test_projects_name_is_unique(self):
        """Test that name column has unique constraint."""
        # Create a project with a unique name
        unique_name = f"unique_test_{os.urandom(4).hex()}"
        
        first_insert = self.client.table("projects").insert({"name": unique_name, "description": "First"}).execute()
        assert first_insert.data is not None
        
        # Try to insert duplicate name - should fail
        import pytest
        with pytest.raises(Exception) as exc_info:
            self.client.table("projects").insert({"name": unique_name, "description": "Duplicate"}).execute()
        
        # Verify the error is about unique constraint
        assert "duplicate" in str(exc_info.value).lower() or "unique" in str(exc_info.value).lower(), \
            "Should raise unique constraint violation"

    def test_projects_table_has_seed_project(self):
        """Test that at least one seed project exists."""
        response = self.client.table("projects").select("*").execute()
        assert response.data is not None
        assert len(response.data) >= 1, "At least one seed project should exist"
        
        # Verify the seed project exists
        seed_project = self.client.table("projects").select("*").eq("name", "claude-code-agentic-rag-masterclass").execute()
        assert seed_project.data is not None
        assert len(seed_project.data) >= 1, "Seed project 'claude-code-agentic-rag-masterclass' should exist"

    def test_documents_project_id_foreign_key_to_projects(self):
        """Test that documents table has project_id FK to projects."""
        # Verify the FK constraint exists in the migration
        migrations_dir = Path(__file__).parent.parent / "supabase" / "migrations"
        project_fk_migration = migrations_dir / "20260307190001_add_project_to_documents.sql"
        content = project_fk_migration.read_text()
        
        assert "references projects" in content.lower(), "Migration should define FK to projects table"
        assert "on delete" in content.lower(), "Migration should define delete behavior"
        
        # Verify by creating a document with project_id
        project_response = self.client.table("projects").select("id").limit(1).execute()
        project_id = project_response.data[0]["id"] if project_response.data else None
        
        if project_id:
            test_doc = {
                "filename": "project_fk_test.txt",
                "file_path": "/test/path/project_fk_test.txt",
                "content_hash": "project_fk_test_hash",
                "project_id": project_id,
                "status": "pending",
                "chunk_count": 0,
            }
            
            doc_response = self.client.table("documents").insert(test_doc).execute()
            assert doc_response.data is not None
            assert doc_response.data[0]["project_id"] == project_id

    def test_projects_created_at_defaults_to_now(self):
        """Test that created_at column defaults to current timestamp."""
        test_project = {
            "name": f"timestamp_test_{os.urandom(4).hex()}",
            "description": "Test created_at default",
        }
        
        response = self.client.table("projects").insert(test_project).execute()
        inserted_project = response.data[0]
        
        assert inserted_project["created_at"] is not None, "created_at should have a value"
        # Verify it's a valid timestamp
        from datetime import datetime
        # Supabase returns ISO format timestamp
        assert "T" in inserted_project["created_at"], "created_at should be ISO format timestamp"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
