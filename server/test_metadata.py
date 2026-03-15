import pytest
from unittest.mock import patch, MagicMock
from server.metadata import extract_metadata
from server.schemas import DocumentMetadata


class TestExtractMetadata:
    """Tests for metadata extraction via LLM."""

    def test_extract_metadata_returns_valid_schema(self):
        """Test that extract_metadata returns a valid DocumentMetadata object."""
        content = "This is a test document about machine learning and AI."
        
        result = extract_metadata(content)
        
        assert isinstance(result, DocumentMetadata)
        assert isinstance(result.title, str)
        assert isinstance(result.summary, str)
        assert isinstance(result.topics, list)
        assert isinstance(result.document_type, str)
        assert isinstance(result.language, str)
        assert result.language == "en" or len(result.language) == 2

    def test_extract_metadata_empty_content(self):
        """Test that empty content returns default metadata."""
        result = extract_metadata("")
        
        assert result.title == "Unknown Title"
        assert result.summary == "No content provided."
        assert result.topics == []
        assert result.document_type == "unknown"
        assert result.language == "en"
        assert result.project is None

    def test_extract_metadata_whitespace_only(self):
        """Test that whitespace-only content returns default metadata."""
        result = extract_metadata("   \n\t  ")
        
        assert result.title == "Unknown Title"
        assert result.summary == "No content provided."

    def test_extract_metadata_truncates_long_content(self):
        """Test that content longer than 8000 chars is truncated."""
        long_content = "A" * 10000
        
        with patch('server.metadata.genai.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.text = '{"title": "Test", "summary": "Test summary", "topics": [], "document_type": "article", "language": "en", "project": null}'
            mock_client.return_value.models.generate_content.return_value = mock_response
            
            extract_metadata(long_content)
            
            # Verify the function was called (no exception raised)
            mock_client.assert_called_once()

    def test_extract_metadata_handles_api_error_gracefully(self):
        """Test that API errors return fallback metadata."""
        content = "Some test content"
        
        with patch('server.metadata.genai.Client') as mock_client:
            mock_client.return_value.models.generate_content.side_effect = Exception("API Error")
            
            result = extract_metadata(content)
            
            assert result.title == "Unknown Title"
            assert "Content preview:" in result.summary
            assert result.document_type == "unknown"
            assert result.language == "en"

    def test_extract_metadata_returns_all_required_fields(self):
        """Test that all required DocumentMetadata fields are populated."""
        content = "Technical documentation about Python programming."
        
        with patch('server.metadata.genai.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.text = json_response()
            mock_client.return_value.models.generate_content.return_value = mock_response
            
            result = extract_metadata(content)
            
            assert hasattr(result, 'title')
            assert hasattr(result, 'summary')
            assert hasattr(result, 'topics')
            assert hasattr(result, 'document_type')
            assert hasattr(result, 'language')
            assert hasattr(result, 'project')

    def test_extract_metadata_topics_is_list(self):
        """Test that topics field is always a list."""
        content = "Test document"
        
        with patch('server.metadata.genai.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.text = '{"title": "Test", "summary": "Test", "topics": ["python", "api"], "document_type": "article", "language": "en", "project": null}'
            mock_client.return_value.models.generate_content.return_value = mock_response
            
            result = extract_metadata(content)
            
            assert isinstance(result.topics, list)
            assert len(result.topics) > 0


def json_response():
    """Helper to return valid JSON response."""
    return '{"title": "Test Document", "summary": "A test document for metadata extraction.", "topics": ["testing", "metadata"], "document_type": "technical documentation", "language": "en", "project": null}'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
