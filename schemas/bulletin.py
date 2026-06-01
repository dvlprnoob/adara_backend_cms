from datetime import datetime

from pydantic import BaseModel, Field


class BulletinCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=2000)
    photo: str | None = None
    is_active: bool = True


class BulletinUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    message: str | None = Field(default=None, min_length=1, max_length=2000)
    photo: str | None = None
    is_active: bool | None = None


class BulletinResponse(BaseModel):
    id: int
    title: str
    message: str
    photo: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
