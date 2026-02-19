from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ThreadCreate(BaseModel):
    title: Optional[str] = "New Chat"


class ThreadResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ThreadListResponse(BaseModel):
    threads: list[ThreadResponse]


class MessageSend(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    thread_id: str
    role: str
    content: str
    created_at: datetime


class ThreadMessagesResponse(BaseModel):
    messages: list[MessageResponse]


# Documents
class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    chunk_count: int = 0
    is_shared: bool = False
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
