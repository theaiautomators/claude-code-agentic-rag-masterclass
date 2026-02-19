import httpx
from typing import List

from langsmith import traceable

from config import settings
from services.embedding_service import generate_single_embedding

BASE_URL = f"{settings.supabase_url}/rest/v1"
HEADERS = {
    "apikey": settings.supabase_service_role_key,
    "Authorization": f"Bearer {settings.supabase_service_role_key}",
    "Content-Type": "application/json",
}


class RetrievalService:
    def __init__(self, user_id: str):
        self.user_id = user_id

    @traceable(name="search_documents", run_type="retriever")
    def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.5,
    ) -> List[dict]:
        """
        Embed query, call search_chunks RPC, return relevant chunks.
        """
        # 1. Generate embedding for the query
        query_embedding = generate_single_embedding(query)

        # 2. Call the search_chunks function via PostgREST RPC
        resp = httpx.post(
            f"{BASE_URL}/rpc/search_chunks",
            headers=HEADERS,
            json={
                "query_embedding": "[" + ",".join(str(v) for v in query_embedding) + "]",
                "match_count": top_k,
                "filter_user_id": self.user_id,
                "similarity_threshold": similarity_threshold,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        results = resp.json()

        return results
