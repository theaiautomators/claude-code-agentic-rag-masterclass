from typing import Optional

import httpx

from config import settings

# Direct REST API calls to Supabase PostgREST
BASE_URL = f"{settings.supabase_url}/rest/v1"
HEADERS = {
    "apikey": settings.supabase_service_role_key,
    "Authorization": f"Bearer {settings.supabase_service_role_key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


class ThreadService:
    def __init__(self, user_id: str):
        self.user_id = user_id

    def list_threads(self) -> list[dict]:
        resp = httpx.get(
            f"{BASE_URL}/threads",
            headers=HEADERS,
            params={
                "user_id": f"eq.{self.user_id}",
                "order": "updated_at.desc",
            },
        )
        resp.raise_for_status()
        return resp.json()

    def create_thread(self, title: str = "New Chat") -> dict:
        resp = httpx.post(
            f"{BASE_URL}/threads",
            headers=HEADERS,
            json={"user_id": self.user_id, "title": title},
        )
        resp.raise_for_status()
        return resp.json()[0]

    def get_thread(self, thread_id: str) -> Optional[dict]:
        resp = httpx.get(
            f"{BASE_URL}/threads",
            headers=HEADERS,
            params={
                "id": f"eq.{thread_id}",
                "user_id": f"eq.{self.user_id}",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None

    def update_thread(self, thread_id: str, updates: dict) -> Optional[dict]:
        resp = httpx.patch(
            f"{BASE_URL}/threads",
            headers=HEADERS,
            params={
                "id": f"eq.{thread_id}",
                "user_id": f"eq.{self.user_id}",
            },
            json=updates,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None

    def delete_thread(self, thread_id: str) -> None:
        httpx.delete(
            f"{BASE_URL}/threads",
            headers=HEADERS,
            params={
                "id": f"eq.{thread_id}",
                "user_id": f"eq.{self.user_id}",
            },
        )

    def list_messages(self, thread_id: str) -> list[dict]:
        resp = httpx.get(
            f"{BASE_URL}/messages",
            headers=HEADERS,
            params={
                "thread_id": f"eq.{thread_id}",
                "user_id": f"eq.{self.user_id}",
                "order": "created_at.asc",
            },
        )
        resp.raise_for_status()
        return resp.json()

    def save_message(self, thread_id: str, role: str, content: str, **kwargs) -> dict:
        data = {
            "thread_id": thread_id,
            "user_id": self.user_id,
            "role": role,
            "content": content,
            **kwargs,
        }
        resp = httpx.post(
            f"{BASE_URL}/messages",
            headers=HEADERS,
            json=data,
        )
        resp.raise_for_status()
        return resp.json()[0]
