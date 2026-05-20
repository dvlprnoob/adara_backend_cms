from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    id: int
    thread_id: int
    sender_id: int
    sender_name: str
    sender_role: str
    message: str
    created_at: datetime


class ChatThreadSummary(BaseModel):
    id: int
    resident_id: int
    resident_name: str
    resident_email: str
    status: str
    last_message: str | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0


class ChatThreadDetail(ChatThreadSummary):
    messages: list[ChatMessageResponse]
