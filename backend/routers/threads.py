from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_current_user
from models.schemas import ThreadCreate, ThreadResponse, ThreadListResponse
from services.thread_service import ThreadService

router = APIRouter()


@router.get("/", response_model=ThreadListResponse)
async def list_threads(user: dict = Depends(get_current_user)):
    service = ThreadService(user["user_id"])
    threads = service.list_threads()
    return {"threads": threads}


@router.post("/", response_model=ThreadResponse, status_code=201)
async def create_thread(
    body: ThreadCreate, user: dict = Depends(get_current_user)
):
    service = ThreadService(user["user_id"])
    thread = service.create_thread(title=body.title)
    return thread


@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str, user: dict = Depends(get_current_user)):
    service = ThreadService(user["user_id"])
    thread = service.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.delete("/{thread_id}", status_code=204)
async def delete_thread(thread_id: str, user: dict = Depends(get_current_user)):
    service = ThreadService(user["user_id"])
    thread = service.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    service.delete_thread(thread_id)
