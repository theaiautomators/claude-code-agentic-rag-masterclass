"""Tests for environment variable configuration (US-018)."""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client


def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)


class TestEnvConfig:
    """Test environment variable configuration for arr-stack."""

    def test_supabase_url_is_arr_stack(self):
        """Test SUPABASE_URL points to arr-stack (local IP, not localhost)."""
        load_env()
        url = os.getenv("SUPABASE_URL")
        assert url is not None, "SUPABASE_URL not set"
        assert "192.168.0.105" in url, f"Expected arr-stack IP, got: {url}"
        assert "localhost" not in url, "Should use local IP, not localhost"
        assert url.startswith("http://"), f"Expected http:// URL, got: {url}"

    def test_supabase_service_role_key_present(self):
        """Test SUPABASE_SERVICE_ROLE_KEY is configured."""
        load_env()
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        assert key is not None, "SUPABASE_SERVICE_ROLE_KEY not set"
        assert len(key) > 50, "Service role key should be a valid JWT"
        assert key.startswith("eyJ"), "Service role key should be JWT format"

    def test_gemini_api_key_present(self):
        """Test GEMINI_API_KEY is configured."""
        load_env()
        key = os.getenv("GEMINI_API_KEY")
        assert key is not None, "GEMINI_API_KEY not set"
        assert len(key) > 30, "Gemini API key should be a valid key"
        assert key.startswith("AIza"), "Gemini API key should start with AIza"

    def test_supabase_client_can_connect(self):
        """Test Supabase client can be instantiated with env vars."""
        load_env()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        assert url is not None and key is not None
        client = create_client(url, key)
        assert client is not None
        assert client.rpc is not None

    def test_env_file_exists(self):
        """Test .env file exists in project root."""
        env_path = Path(__file__).parent.parent / ".env"
        assert env_path.exists(), ".env file not found"

    def test_env_file_has_required_vars(self):
        """Test .env contains all required variables."""
        env_path = Path(__file__).parent.parent / ".env"
        content = env_path.read_text()
        required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "GEMINI_API_KEY"]
        for var in required_vars:
            assert var in content, f"{var} not found in .env"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
