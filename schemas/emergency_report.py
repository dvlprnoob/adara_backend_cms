from pydantic import BaseModel
from datetime import datetime

class EmergencyReportResponse(BaseModel):
    id: int
    user_name: str
    block: str
    type_name: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True  