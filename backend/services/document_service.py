from typing import Optional, List

import httpx

from config import settings

BASE_URL = f"{settings.supabase_url}/rest/v1"
HEADERS = {
    "apikey": settings.supabase_service_role_key,
    "Authorization": f"Bearer {settings.supabase_service_role_key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


class DocumentService:
    def __init__(self, user_id: str):
        self.user_id = user_id

    def list_documents(self) -> list:
        resp = httpx.get(
            f"{BASE_URL}/documents",
            headers=HEADERS,
            params={
                "or": f"(user_id.eq.{self.user_id},is_shared.eq.true)",
                "order": "created_at.desc",
            },
        )
        resp.raise_for_status()
        return resp.json()

    def create_document(
        self,
        filename: str,
        file_type: str,
        file_size: int,
        storage_path: str,
    ) -> dict:
        resp = httpx.post(
            f"{BASE_URL}/documents",
            headers=HEADERS,
            json={
                "user_id": self.user_id,
                "filename": filename,
                "file_type": file_type,
                "file_size": file_size,
                "storage_path": storage_path,
                "status": "pending",
            },
        )
        resp.raise_for_status()
        return resp.json()[0]

    def get_document(self, document_id: str) -> Optional[dict]:
        resp = httpx.get(
            f"{BASE_URL}/documents",
            headers=HEADERS,
            params={
                "id": f"eq.{document_id}",
                "user_id": f"eq.{self.user_id}",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None

    def update_document(self, document_id: str, updates: dict) -> Optional[dict]:
        resp = httpx.patch(
            f"{BASE_URL}/documents",
            headers=HEADERS,
            params={
                "id": f"eq.{document_id}",
                "user_id": f"eq.{self.user_id}",
            },
            json=updates,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None

    def delete_document(self, document_id: str) -> None:
        httpx.delete(
            f"{BASE_URL}/documents",
            headers=HEADERS,
            params={
                "id": f"eq.{document_id}",
                "user_id": f"eq.{self.user_id}",
            },
        )

    def save_chunks(self, document_id: str, chunks: List[dict]) -> None:
        """Bulk insert chunks. Each chunk dict has: content, chunk_index, embedding, metadata."""
        rows = []
        for chunk in chunks:
            embedding = chunk["embedding"]
            # Format embedding as string for pgvector via PostgREST
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
            rows.append({
                "document_id": document_id,
                "user_id": self.user_id,
                "content": chunk["content"],
                "chunk_index": chunk["chunk_index"],
                "embedding": embedding_str,
                "metadata": chunk.get("metadata", {}),
            })

        resp = httpx.post(
            f"{BASE_URL}/document_chunks",
            headers=HEADERS,
            json=rows,
            timeout=120.0,
        )
        resp.raise_for_status()
