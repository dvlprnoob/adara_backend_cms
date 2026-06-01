from pydantic import BaseModel
from typing import Optional

class ServiceBase(BaseModel):
    category: str
    service_name: str
    owner_name: str
    description: Optional[str] = None
    phone: str
    gmaps_link: Optional[str] = None
    is_active: bool = True
    
class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    category: Optional[str] = None
    service_name: Optional[str] = None
    owner_name: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    gmaps_link: Optional[str] = None
    is_active: Optional[bool] = None
    
class ServiceResponse(ServiceBase):
    id: int
    
    class Config:
        from_attributes = True
    
