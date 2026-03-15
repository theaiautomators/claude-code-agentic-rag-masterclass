import os
import time
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIMENSIONS = 768  # Must match pgvector vector(768)


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT", max_retries: int = 3, retry_delay: float = 1.0) -> list[list[float]]:
    """
    Embed a batch of texts via Gemini API.
    Returns a list of embedding vectors (one per input text).
    
    Args:
        texts: List of text strings to embed
        task_type: Task type for embedding (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.)
        max_retries: Maximum number of retry attempts on failure
        retry_delay: Delay between retries in seconds
    
    Returns:
        List of embedding vectors, each with 768 dimensions
    
    Raises:
        Exception: If all retries fail
    """
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    for attempt in range(max_retries):
        try:
            # Batch embed all texts in a single API call for efficiency
            response = client.models.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                contents=texts,  # type: ignore
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=EMBEDDING_DIMENSIONS
                )
            )
            
            # Extract embeddings from response
            if not response.embeddings:
                raise ValueError("No embeddings returned from API")
            
            embeddings: list[list[float]] = []
            for embedding in response.embeddings:
                if not embedding.values:
                    raise ValueError("Embedding values are empty")
                emb_list = list(embedding.values)
                if len(emb_list) != EMBEDDING_DIMENSIONS:
                    raise ValueError(f"Embedding dimension {len(emb_list)} does not match required {EMBEDDING_DIMENSIONS}")
                embeddings.append(emb_list)
            
            return embeddings
            
        except Exception as e:
            if attempt < max_retries - 1:
                # Wait before retrying
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            else:
                raise Exception(f"Failed to embed texts after {max_retries} attempts: {str(e)}")
    
    # This line should never be reached, but satisfies mypy
    raise RuntimeError("Unreachable: loop should always return or raise")


def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY", max_retries: int = 3, retry_delay: float = 1.0) -> list[float]:
    """
    Embed a single text string.
    
    Args:
        text: Text string to embed
        task_type: Task type for embedding
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        Single embedding vector with 768 dimensions
    """
    return embed_texts([text], task_type=task_type, max_retries=max_retries, retry_delay=retry_delay)[0]


def embed_chunks_with_context(
    full_document: str,
    chunks: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[list[float]]:
    """
    Route chunk embedding through the configured provider.
    Only jina_late uses full_document; gemini/ollama call embed_texts() as before.
    
    Args:
        full_document: Full document text (used only by jina_late provider)
        chunks: List of chunk texts to embed
        task_type: Task type for embedding
    
    Returns:
        List of embedding vectors for each chunk
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "gemini")
    if provider == "jina_late":
        from server.late_chunking import late_chunk_embed  # type: ignore
        return late_chunk_embed(full_document, chunks)
    return embed_texts(chunks, task_type=task_type)
