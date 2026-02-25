from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from models.user import User
from models.resident_profile import ResidentProfile
from models.role import Role
from schemas.user import ResidentCreate, AdminCreate, UserResponse

from core.security import hash_password
from api.deps import role_required

router = APIRouter()

@router.post("/residents")
def create_resident(
    payload: ResidentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    role = db.query(Role).filter(Role.name == "resident").first()

    if not role:
        raise HTTPException(status_code=400, detail="Resident role not found")

    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        role_id=role.id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    profile = ResidentProfile(
        user_id=new_user.id,
        address=payload.address,
        block=payload.block,
        phone=payload.phone,
        total_people=payload.total_people,
        npwp=payload.npwp,
        ktp_number=payload.ktp_number
    )

    db.add(profile)
    db.commit()

    return {"message": "Resident created successfully"}

@router.post("/admin")
def create_admin(
    payload: AdminCreate,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["super_admin"]))
): 
    role = db.query(Role).filter(Role.name == "admin").first()
    
    if not role:
        raise HTTPException(status_code=400, detail="Admin role not found")
    
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_admin = User(
        name = payload.name,
        email = payload.email,
        # phone = payload.phone,
        password = hash_password(payload.password),
        role_id = role.id
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return {"message": "Admin created successfully"}

@router.get("/", response_model=list[UserResponse])
def get_all_user(
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    users = db.query(User).all()
    
    result = []
    for user in users:
        result.append(
            UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                # phone=user.phone,
                role=user.role.name
            )
        )
        
    return result