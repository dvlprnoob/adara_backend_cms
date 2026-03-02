from pydantic import BaseModel
from typing import Optional

class ServiceBase(BaseModel):
    category: str
    service_name: str
    owner_name: str
    phone: str
    gmaps_link: str
    is_active: bool
    
class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    category: Optional[str]
    service_name: Optional[str]
    owner_name: Optional[str]
    phone: Optional[str]
    gmaps_link: Optional[str]
    is_active : Optional[bool]
    
class ServiceResponse(ServiceBase):
    id: int
    
    class Config:
        from_attributes = True
    