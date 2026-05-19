from datetime import datetime
from pydantic import BaseModel, Field


class ProgressCreate(BaseModel):
    user_id: int
    status: str = "pondasi"
    percent: int = Field(default=10, ge=0, le=100)
    note: str = "Progress pembangunan dimulai (Pondasi)"
    photos: list[str] = Field(default_factory=list, max_length=6)


class ProgressUpdateCreate(BaseModel):
    note: str = Field(min_length=1)
    photos: list[str] = Field(default_factory=list, max_length=6)


class ProgressStatusUpdate(BaseModel):
    status: str
    percent: int = Field(ge=0, le=100)


class ProgressUpdateResponse(BaseModel):
    id: int
    date: datetime
    note: str
    photos: list[str]


class ProgressResponse(BaseModel):
    id: int
    user_id: int
    status: str
    percent: int
    is_done: bool
    updates: list[ProgressUpdateResponse]
