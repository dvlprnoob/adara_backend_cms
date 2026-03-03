from pydantic import BaseModel
from typing import Optional

class EmergencyTypeBase(BaseModel):
    name: str
    is_active: Optional[bool] = True


class EmergencyTypeCreate(EmergencyTypeBase):
    pass


class EmergencyTypeUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class EmergencyTypeResponse(EmergencyTypeBase):
    id: int
    created_by: Optional[int]

    class Config:
        from_attributes = True