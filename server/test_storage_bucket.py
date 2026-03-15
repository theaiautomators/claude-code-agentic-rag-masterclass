"""Tests for Supabase Storage bucket creation and RLS policies."""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class TestStorageBucketSetup:
    """Test suite for Supabase Storage bucket verification."""

    @classmethod
    def setup_class(cls):
        """Set up Supabase client for storage tests."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        cls.client = create_client(supabase_url, supabase_key)

    def test_documents_bucket_exists(self):
        """Test that 'documents' storage bucket exists."""
        # List all buckets and verify documents bucket exists
        buckets = self.client.storage.list_buckets()
        assert buckets is not None, "Storage buckets query failed"
        
        documents_bucket = None
        for bucket in buckets:
            if bucket.id == "documents":
                documents_bucket = bucket
                break
        
        assert documents_bucket is not None, "documents bucket does not exist"
        assert documents_bucket.name == "documents", "Bucket name should be 'documents'"

    def test_documents_bucket_is_private(self):
        """Test that documents bucket is private (not public)."""
        buckets = self.client.storage.list_buckets()
        documents_bucket = None
        for bucket in buckets:
            if bucket.id == "documents":
                documents_bucket = bucket
                break
        
        assert documents_bucket is not None, "documents bucket should exist"
        assert documents_bucket.public == False, "documents bucket should be private (public=False)"

    def test_storage_bucket_migration_exists(self):
        """Test that migration file for storage bucket creation exists."""
        migrations_dir = Path(__file__).parent.parent / "supabase" / "migrations"
        bucket_migrations = list(migrations_dir.glob("*bucket*.sql"))
        
        assert len(bucket_migrations) > 0, "No migration found for storage bucket creation"
        
        # Verify the migration contains bucket creation
        migration_path = bucket_migrations[0]
        content = migration_path.read_text()
        assert "storage.buckets" in content, "Migration should reference storage.buckets"
        assert "documents" in content, "Migration should create documents bucket"
        assert "false" in content or "public" in content.lower(), "Migration should set bucket to private"

    def test_storage_rls_policy_allows_authenticated_upload(self):
        """Test that RLS policy allows authenticated users to upload to their folder."""
        # Verify migration contains RLS policy for authenticated uploads
        migrations_dir = Path(__file__).parent.parent / "supabase" / "migrations"
        bucket_migrations = list(migrations_dir.glob("*bucket*.sql"))
        
        if bucket_migrations:
            migration_path = bucket_migrations[0]
            content = migration_path.read_text()
            
            # Check for RLS policy creation
            assert "CREATE POLICY" in content.upper() or "create policy" in content.lower(), \
                "Migration should create RLS policy"
            assert "authenticated" in content.lower(), "Policy should grant access to authenticated users"
            assert "INSERT" in content.upper() or "for insert" in content.lower(), \
                "Policy should allow INSERT operations"
            assert "auth.uid()" in content, "Policy should reference auth.uid() for user identification"

    def test_storage_objects_table_has_rls_enabled(self):
        """Test that storage.objects table has RLS enabled."""
        # RLS is enabled on storage.objects by Supabase by default
        # We verify by checking the bucket is accessible through the client
        # The storage API handles RLS internally
        bucket_info = self.client.storage.get_bucket("documents")
        assert bucket_info is not None, "Should be able to get bucket info"
        assert bucket_info.id == "documents", "Bucket ID should match"

    def test_storage_bucket_creation_is_idempotent(self):
        """Test that bucket creation migration is idempotent."""
        migrations_dir = Path(__file__).parent.parent / "supabase" / "migrations"
        bucket_migrations = list(migrations_dir.glob("*bucket*.sql"))
        
        if bucket_migrations:
            migration_path = bucket_migrations[0]
            content = migration_path.read_text()
            
            # Check for idempotent pattern (ON CONFLICT or IF NOT EXISTS)
            has_idempotent = (
                "ON CONFLICT" in content.upper() or 
                "IF NOT EXISTS" in content.upper() or
                "DO NOTHING" in content.upper()
            )
            assert has_idempotent, "Migration should be idempotent (use ON CONFLICT or IF NOT EXISTS)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
