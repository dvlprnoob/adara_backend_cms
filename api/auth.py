from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from db.session import get_db
from models.user import User
from schemas.auth import LoginRequest, TokenResponse
from schemas.user import ResidentCreate
from core.security import verify_password, create_access_token

router = APIRouter()

@router.post("/login")
def login(email: str, password: str, device: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    # 🚨 Cegah resident login ke web
    if device == "web" and user.role.name == "resident":
        raise HTTPException(
            status_code=403,
            detail="Residents cannot access CMS"
        )

    # 🚨 Cegah admin login dari mobile (opsional)
    if device == "mobile" and user.role.name != "resident":
        raise HTTPException(
            status_code=403,
            detail="Admin cannot login from mobile"
        )

    token = create_access_token({
        "user_id": user.id,
        "role": user.role.name
    })

    return {
        "access_token": token,
        "role": user.role.name
    }