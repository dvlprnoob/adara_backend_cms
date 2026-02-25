from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device: str

class TokenResponse(BaseModel):
    access_token: str
    role: str