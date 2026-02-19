from typing import List

from langsmith import traceable

from services.openai_client import get_embedding_client

EMBEDDING_MODEL = "text-embedding-3-small"
MAX_BATCH_SIZE = 2048


@traceable(name="generate_embeddings", run_type="embedding")
def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts. Batches automatically."""
    client = get_embedding_client()
    all_embeddings = []

    for i in range(0, len(texts), MAX_BATCH_SIZE):
        batch = texts[i:i + MAX_BATCH_SIZE]
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


@traceable(name="generate_single_embedding", run_type="embedding")
def generate_single_embedding(text: str) -> List[float]:
    """Generate embedding for a single text."""
    client = get_embedding_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding
