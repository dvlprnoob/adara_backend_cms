from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from models.user import User
from models.resident_profile import ResidentProfile
from models.role import Role
from core.security import hash_password
from api.deps import role_required

router = APIRouter()

@router.post("/residents")
def create_resident(
    name: str,
    email: str,
    password: str,
    address: str,
    block: str,
    phone: str,
    total_people: int,
    npwp: str = None,
    ktp_number: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin, super_admin"]))
):
    role = db.query(Role).filter(Role.name == "resident").first()

    new_user = User(
        name = name,
        email = email,
        password = hash_password(password),
        role_id = role.id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh()

    profile = ResidentProfile(
        user_id = new_user.id,
        address = address,
        block = block,
        phone = phone,
        total_people = total_people,
        npwp = npwp,
        ktp_number = ktp_number
    )

    db.add(profile)
    db.commit()

    return {"message": "Resident created Successfully"}