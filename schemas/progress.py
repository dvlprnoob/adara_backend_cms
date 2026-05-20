from datetime import date, datetime
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
    note: str | None = None
    photos: list[str] = Field(default_factory=list, max_length=6)
    handover_date: date | None = None
    warranty_end_date: date | None = None


class ProgressWarrantyUpdate(BaseModel):
    handover_date: date | None = None
    warranty_end_date: date | None = None


class ProgressUpdateResponse(BaseModel):
    id: int
    date: datetime
    note: str
    photos: list[str]


class ProgressResponse(BaseModel):
    id: int
    user_id: int
    user_name: str | None = None
    user_email: str | None = None
    status: str
    percent: int
    is_done: bool
    handover_date: date | None = None
    warranty_end_date: date | None = None
    updates: list[ProgressUpdateResponse]
