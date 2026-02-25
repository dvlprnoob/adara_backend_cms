from pydantic import BaseModel, EmailStr
from typing import Optional

# =========================
# CREATE SCHEMAS
# =========================

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
    password: str


# =========================
# RESPONSE SCHEMAS
# =========================

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

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
    total_people: Optional[int] = None
    npwp: Optional[str] = None
    ktp_number: Optional[str] = None
    
# =========================
# CHANGE PASSWORD
# =========================   

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    
class ResetPasswordRequest(BaseModel):
    new_password: str
    
class UpdateRoleRequest(BaseModel):
    role_name: str