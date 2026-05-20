from datetime import datetime

from pydantic import BaseModel, Field


class ServiceReportCreate(BaseModel):
    report_type: str = Field(pattern="^(employee|environment)$")
    subject: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2000)


class ServiceReportResolve(BaseModel):
    admin_note: str | None = Field(default=None, max_length=2000)


class ServiceReportResponse(BaseModel):
    id: int
    user_id: int
    user_name: str | None = None
    user_email: str | None = None
    report_type: str
    subject: str
    description: str
    status: str
    admin_note: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None
