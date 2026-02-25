from pydantic import BaseModel, EmailStr
from typing import Optional

class ResidentCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    address: str
    block: str
    phone: str
    total_people: int
    npwp: Optional[str] = None
    ktp_number: Optional[str] = None
    
class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    # phone: str
    password: str
    
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    # phone: Optional[str] = None
    role: str
    
    class Config:
        from_attributes = True