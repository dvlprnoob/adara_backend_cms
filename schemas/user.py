from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# =========================
# CREATE SCHEMAS
# =========================

class ResidentCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    address: str
    block: str
    phone: str
    total_people: int = Field(gt=0)
    npwp: Optional[str] = None
    ktp_number: Optional[str] = None


class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: str


# =========================
# RESPONSE SCHEMAS
# =========================

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role_name: str
    is_active: bool

    class Config:
        from_attributes = True


class ResidentProfileResponse(BaseModel):
    address: str
    block: str
    phone: str
    total_people: int
    npwp: Optional[str]
    ktp_number: Optional[str]

    class Config:
        from_attributes = True


class ResidentDetailResponse(UserResponse):
    profile: ResidentProfileResponse
    
# =========================
# UPDATE PROFILE
# =========================

class UpdateMyProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    block: Optional[str] = None
    total_people: Optional[int] = Field(default=None, gt=0)
    npwp: Optional[str] = None
    ktp_number: Optional[str] = None
    
# =========================
# CHANGE PASSWORD
# =========================   

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)
    
class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)
    
class UpdateRoleRequest(BaseModel):
    role_name: str
