from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from models.user import User
from core.security import verify_password, create_access_token

router = APIRouter()

@router.post("/login")
def login(email: str, password: str, device: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
    if user.role.name == "resident" and device != "mobile":
        raise HTTPException(status_code=403, detail="Residents can only log in from mobile devices")
    
    token = create_access_token({
        "user_id": user.id,
        "role": user.role.name
    })
    
    return {
        "access_token" : token,
        "role" : user.role.name
    }