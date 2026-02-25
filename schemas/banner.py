from pydantic import BaseModel
from typing import Optional

class BannerCreate(BaseModel):
    name: str
    link: Optional[str] = None
    photo: str
    is_active: Optional[bool] = True

class BannerUpdate(BaseModel):
    name: Optional[str] = None
    link: Optional[str] = None
    photo: Optional[str] = None
    is_active: Optional[bool] = None
    
class BannerResponse(BaseModel):
    id: int
    name: str
    photo: str
    is_active: bool
    
    class Config:
        from_attributes = True