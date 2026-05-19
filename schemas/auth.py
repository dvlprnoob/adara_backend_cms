from pydantic import BaseModel, EmailStr, Field
from typing import Literal

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    device: Literal["web", "mobile"]

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)
