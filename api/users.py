from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from models.user import User
from models.resident_profile import ResidentProfile
from models.role import Role
from schemas.user import (
    ResidentCreate,
    AdminCreate,
    UserResponse,
    ResidentDetailResponse,
    ResidentProfileResponse,
    UpdateMyProfile,
    ChangePasswordRequest,
    ResetPasswordRequest,
    UpdateRoleRequest
)
from core.security import hash_password, verify_password
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

@router.post("/")
def create_user(
    payload: AdminCreate,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["super_admin"]))
):
    role = db.query(Role).filter(Role.name == payload.role).first()

    if not role:
        raise HTTPException(status_code=400, detail="Role not found")

    new_user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        role_id=role.id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully"}

@router.get("/", response_model=list[UserResponse])
def get_all_user(
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    users = db.query(User).all()

    return [
        UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.name,
            is_active=user.is_active
        )
        for user in users
    ]

@router.get("/me", response_model=UserResponse | ResidentDetailResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["resident", "admin", "super_admin"]))
):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role.name == "resident":
        profile = db.query(ResidentProfile).filter(
            ResidentProfile.user_id == user.id
        ).first()

        return ResidentDetailResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.name,
            is_active=user.is_active,
            profile=ResidentProfileResponse(
                address=profile.address,
                block=profile.block,
                phone=profile.phone,
                total_people=profile.total_people,
                npwp=profile.npwp,
                ktp_number=profile.ktp_number
            )
        )

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.name,
        is_active=user.is_active
    )
    
@router.put("/me")
def update_my_profile(
    payload: UpdateMyProfile,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["resident", "admin", "super_admin"]))
):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update basic fields
    if payload.name is not None:
        user.name = payload.name

    if payload.email is not None:
        existing_email = db.query(User).filter(
            User.email == payload.email,
            User.id != user.id
        ).first()

        if existing_email:
            raise HTTPException(status_code=400, detail="Email already used")

        user.email = payload.email

    if payload.phone is not None:
        user.phone = payload.phone

    # Kalau resident → update profile juga
    if user.role.name == "resident":
        profile = db.query(ResidentProfile).filter(
            ResidentProfile.user_id == user.id
        ).first()

        if payload.address is not None:
            profile.address = payload.address

        if payload.block is not None:
            profile.block = payload.block

        if payload.total_people is not None:
            profile.total_people = payload.total_people

        if payload.npwp is not None:
            profile.npwp = payload.npwp

        if payload.ktp_number is not None:
            profile.ktp_number = payload.ktp_number

    db.commit()
    db.refresh(user)

    return {"message": "Profile updated successfully"}

@router.get("/{user_id}", response_model=UserResponse | ResidentDetailResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Jika Resident → include profile
    if user.role.name == "resident":
        profile = db.query(ResidentProfile).filter(
            ResidentProfile.user_id == user.id
        ).first()

        return ResidentDetailResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.name,
            profile=ResidentProfileResponse(
                address=profile.address,
                block=profile.block,
                phone=profile.phone,
                total_people=profile.total_people,
                npwp=profile.npwp,
                ktp_number=profile.ktp_number
            )
        )

    # Jika Admin / Super Admin
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.name
    )
    

@router.put("/me/password")
def change_my_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["resident", "admin", "super_admin"]))
):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validasi old password
    if not verify_password(payload.old_password, user.password):
        raise HTTPException(status_code=400, detail="Old password incorrect")

    user.password = hash_password(payload.new_password)

    db.commit()

    return {"message": "Password changed successfully"}

@router.put("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
): 
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    #Admin tidak boleh reset super_admin
    if user.role.name == "super_admin":
        raise HTTPException(status_code=403, detail="Can't Reset Super Admin Password")
    
    user.password = hash_password(payload.new_password)
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.put("/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: UpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["super_admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.name == payload.role_name).first()

    if not role:
        raise HTTPException(status_code=400, detail="Role not found")

    # Tidak boleh ubah super_admin jadi admin sembarangan (opsional rule)
    if user.role.name == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot modify super admin")

    user.role_id = role.id
    db.commit()

    return {"message": "Role updated successfully"}

@router.put("/{user_id}")
def update_user(
    user_id: int,
    payload: UpdateMyProfile,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.name is not None:
        user.name = payload.name

    if payload.email is not None:
        existing_email = db.query(User).filter(
            User.email == payload.email,
            User.id != user.id
        ).first()

        if existing_email:
            raise HTTPException(status_code=400, detail="Email already used")

        user.email = payload.email

    db.commit()

    return {"message": "User updated successfully"}

@router.put("/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    db.commit()

    return {
        "message": "User status updated",
        "is_active": user.is_active
    }