from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from dependencies import get_current_user
from models.schemas import MessageSend, ThreadMessagesResponse
from services.chat_service import ChatService
from services.thread_service import ThreadService

router = APIRouter()


@router.get("/{thread_id}/messages", response_model=ThreadMessagesResponse)
async def get_messages(thread_id: str, user: dict = Depends(get_current_user)):
    service = ThreadService(user["user_id"])
    thread = service.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    messages = service.list_messages(thread_id)
    return {"messages": messages}


@router.post("/{thread_id}/messages")
async def send_message(
    thread_id: str,
    body: MessageSend,
    user: dict = Depends(get_current_user),
):
    thread_service = ThreadService(user["user_id"])
    thread = thread_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    chat_service = ChatService(user["user_id"])
    return EventSourceResponse(
        chat_service.stream_response(
            thread_id=thread_id,
            content=body.content,
        )
    )
