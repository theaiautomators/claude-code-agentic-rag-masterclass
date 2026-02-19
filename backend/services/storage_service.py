import httpx

from config import settings

STORAGE_URL = f"{settings.supabase_url}/storage/v1"
HEADERS = {
    "apikey": settings.supabase_service_role_key,
    "Authorization": f"Bearer {settings.supabase_service_role_key}",
}


class StorageService:
    def __init__(self, user_id: str):
        self.user_id = user_id

    def upload_file(self, filename: str, content: bytes, content_type: str) -> str:
        """Upload file to Supabase Storage. Returns the storage path."""
        path = f"{self.user_id}/{filename}"
        headers = {
            **HEADERS,
            "Content-Type": content_type,
        }
        resp = httpx.post(
            f"{STORAGE_URL}/object/documents/{path}",
            headers=headers,
            content=content,
            timeout=60.0,
        )
        resp.raise_for_status()
        return path

    def download_file(self, storage_path: str) -> bytes:
        """Download file from Supabase Storage."""
        resp = httpx.get(
            f"{STORAGE_URL}/object/documents/{storage_path}",
            headers=HEADERS,
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.content

    def delete_file(self, storage_path: str) -> None:
        """Delete file from Supabase Storage."""
        resp = httpx.delete(
            f"{STORAGE_URL}/object/documents/{storage_path}",
            headers=HEADERS,
            timeout=30.0,
        )
        resp.raise_for_status()
