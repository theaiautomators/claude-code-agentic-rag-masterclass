"""Tests for Supabase connectivity and pgvector extension verification."""

import os
import pytest
from pathlib import Path

# Add server directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from main import supabase_health, _get_supabase


class TestSupabaseHealth:
    """Test suite for Supabase connectivity verification."""

    def test_supabase_health_connected(self):
        """Test that supabase_health returns status=connected when .env is configured."""
        result = supabase_health()
        assert result["status"] == "connected", f"Expected connected, got: {result}"
        assert "supabase_url" in result
        assert result["supabase_url"] == os.getenv("SUPABASE_URL")

    def test_supabase_env_vars_present(self):
        """Test that required Supabase env vars are present in .env."""
        assert os.getenv("SUPABASE_URL"), "SUPABASE_URL not set in .env"
        assert os.getenv("SUPABASE_SERVICE_ROLE_KEY"), "SUPABASE_SERVICE_ROLE_KEY not set in .env"

    def test_supabase_client_instantiation(self):
        """Test that Supabase client can be instantiated from env vars."""
        client = _get_supabase()
        assert client is not None
        assert hasattr(client, "auth")
        assert hasattr(client, "table")

    def test_pgvector_migration_exists(self):
        """Test that pgvector enable migration exists in supabase/migrations."""
        migrations_dir = Path(__file__).parent.parent / "supabase" / "migrations"
        assert migrations_dir.exists(), "supabase/migrations directory not found"
        
        # Find the pgvector enable migration
        pgvector_migrations = list(migrations_dir.glob("*enable_pgvector*.sql"))
        assert len(pgvector_migrations) > 0, "No pgvector enable migration found"
        
        # Verify migration content
        migration_path = pgvector_migrations[0]
        content = migration_path.read_text()
        assert "create extension" in content.lower()
        assert "vector" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
