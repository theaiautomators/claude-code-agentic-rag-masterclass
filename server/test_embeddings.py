import pytest
import os
from embeddings import embed_text, embed_texts, GEMINI_EMBEDDING_MODEL, EMBEDDING_DIMENSIONS


class TestEmbeddings:
    """Tests for Gemini API embedding functions."""

    def test_embed_text_returns_list(self):
        """Test that embed_text returns a list of floats."""
        text = "This is a test document for embedding."
        embedding = embed_text(text)
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_text_dimension_is_768(self):
        """Test that embedding dimension matches pgvector requirement (768)."""
        text = "Test document for pgvector compatibility."
        embedding = embed_text(text)
        assert len(embedding) == EMBEDDING_DIMENSIONS, f"Expected {EMBEDDING_DIMENSIONS} dimensions, got {len(embedding)}"

    def test_embed_texts_batch_returns_correct_count(self):
        """Test that batch embedding returns correct number of embeddings."""
        texts = ["First document", "Second document", "Third document"]
        embeddings = embed_texts(texts)
        assert len(embeddings) == len(texts)

    def test_embed_texts_all_have_768_dimensions(self):
        """Test that all batch embeddings have 768 dimensions."""
        texts = ["Document one", "Document two", "Document three"]
        embeddings = embed_texts(texts)
        for emb in embeddings:
            assert len(emb) == EMBEDDING_DIMENSIONS, f"Embedding has {len(emb)} dimensions, expected {EMBEDDING_DIMENSIONS}"

    def test_embed_text_with_different_task_type(self):
        """Test embedding with different task types."""
        text = "Query for retrieval"
        embedding_doc = embed_text(text, task_type="RETRIEVAL_DOCUMENT")
        embedding_query = embed_text(text, task_type="RETRIEVAL_QUERY")
        assert len(embedding_doc) == EMBEDDING_DIMENSIONS
        assert len(embedding_query) == EMBEDDING_DIMENSIONS

    def test_gemini_model_name(self):
        """Test that the correct Gemini embedding model is configured."""
        assert GEMINI_EMBEDDING_MODEL == "gemini-embedding-001"

    def test_api_key_loaded_from_env(self):
        """Test that GEMINI_API_KEY is loaded from environment."""
        api_key = os.getenv("GEMINI_API_KEY")
        assert api_key is not None, "GEMINI_API_KEY not found in .env"
        assert len(api_key) > 0, "GEMINI_API_KEY is empty"

    def test_embed_empty_string_raises(self):
        """Test that embedding an empty string raises an error (Gemini API limitation)."""
        with pytest.raises(Exception):
            embed_text("")

    def test_embed_special_characters(self):
        """Test embedding text with special characters."""
        text = "Test with special chars: ñ, é, 中文，emoji 🎉"
        embedding = embed_text(text)
        assert len(embedding) == EMBEDDING_DIMENSIONS

    def test_embed_long_text(self):
        """Test embedding a longer document."""
        text = "This is a longer document. " * 100
        embedding = embed_text(text)
        assert len(embedding) == EMBEDDING_DIMENSIONS
