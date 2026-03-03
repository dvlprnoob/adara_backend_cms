from pydantic import BaseModel, EmailStr
from typing import Literal

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device: Literal["web", "mobile"]

class TokenResponse(BaseModel):
    access_token: str
    role: str