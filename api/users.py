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


def get_user_or_404(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def ensure_can_manage_user(current_user: User, target_user: User):
    if current_user.role.name == "super_admin":
        return
    if target_user.role.name != "resident":
        raise HTTPException(status_code=403, detail="Operation not permitted")

# =================================================
# CREATE RESIDENT (ADMIN / SUPER ADMIN)
# =================================================
@router.post("/residents")
def create_resident(
    payload: ResidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"]))
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


# =================================================
# CREATE ADMIN (SUPER ADMIN ONLY)
# =================================================
@router.post("/")
def create_user(
    payload: AdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["super_admin"]))
):
    role = db.query(Role).filter(Role.name == payload.role).first()
    if not role:
        raise HTTPException(status_code=400, detail="Role not found")

    if role.name == "resident":
        raise HTTPException(status_code=400, detail="Use /users/residents to create resident users")

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

    return {"message": "User created successfully"}


# =================================================
# GET ALL USERS (ADMIN)
# =================================================
@router.get("/", response_model=list[UserResponse])
def get_all_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"]))
):
    users = db.query(User).all()

    return [
        UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role_name=user.role.name,
            is_active=user.is_active
        )
        for user in users
    ]


# =================================================
# GET MY PROFILE
# =================================================
@router.get("/me", response_model=UserResponse | ResidentDetailResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["resident", "admin", "super_admin"]))
):
    user = current_user

    if user.role.name == "resident":
        profile = db.query(ResidentProfile).filter(
            ResidentProfile.user_id == user.id
        ).first()

        if not profile:
            raise HTTPException(status_code=404, detail="Resident profile not found")

        return ResidentDetailResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role_name=user.role.name,
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
        role_name=user.role.name,
        is_active=user.is_active
    )


# =================================================
# UPDATE MY PROFILE
# =================================================
@router.put("/me")
def update_my_profile(
    payload: UpdateMyProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["resident", "admin", "super_admin"]))
):
    user = current_user

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

    if user.role.name == "resident":
        profile = db.query(ResidentProfile).filter(
            ResidentProfile.user_id == user.id
        ).first()

        if not profile:
            raise HTTPException(status_code=404, detail="Resident profile not found")

        if payload.phone is not None:
            profile.phone = payload.phone

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

    return {"message": "Profile updated successfully"}


# =================================================
# CHANGE MY PASSWORD
# =================================================
@router.put("/me/password")
def change_my_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["resident", "admin", "super_admin"]))
):
    user = current_user

    if not verify_password(payload.old_password, user.password):
        raise HTTPException(status_code=400, detail="Old password incorrect")

    user.password = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


# =================================================
# GET USER DETAIL (ADMIN)
# =================================================
@router.get("/{user_id}", response_model=UserResponse | ResidentDetailResponse)
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"]))
):
    user = get_user_or_404(db, user_id)
    ensure_can_manage_user(current_user, user)

    if user.role.name == "resident":
        profile = db.query(ResidentProfile).filter(
            ResidentProfile.user_id == user.id
        ).first()

        if not profile:
            raise HTTPException(status_code=404, detail="Resident profile not found")

        return ResidentDetailResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role_name=user.role.name,
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
        role_name=user.role.name,
        is_active=user.is_active
    )


# =================================================
# RESET USER PASSWORD (ADMIN)
# =================================================
@router.patch("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"]))
):
    user = get_user_or_404(db, user_id)
    ensure_can_manage_user(current_user, user)

    user.password = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password reset successfully"}


# =================================================
# UPDATE USER ROLE (SUPER ADMIN ONLY)
# =================================================
@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    payload: UpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["super_admin"]))
):
    user = get_user_or_404(db, user_id)

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    role = db.query(Role).filter(Role.name == payload.role_name).first()
    if not role:
        raise HTTPException(status_code=400, detail="Role not found")

    if role.name == "resident":
        raise HTTPException(status_code=400, detail="Use resident creation flow for resident users")

    user.role_id = role.id
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role_name=user.role.name,
        is_active=user.is_active
    )


# =================================================
# TOGGLE USER ACTIVE STATUS (ADMIN)
# =================================================
@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"]))
):
    user = get_user_or_404(db, user_id)
    ensure_can_manage_user(current_user, user)

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own active status")

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role_name=user.role.name,
        is_active=user.is_active
    )
