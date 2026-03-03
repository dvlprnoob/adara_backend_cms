from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from db.session import get_db
from models.emergency_type import EmergencyType
from schemas.emergency_type import *

router = APIRouter()

# =========================
# MOBILE - GET AVAILABLE TYPES
# =========================
# User melihat:
# - Global types
# - Personal types miliknya
@router.get("/", response_model=list[EmergencyTypeResponse])
def get_types(user_id: int, db: Session = Depends(get_db)):
    return db.query(EmergencyType).filter(
        EmergencyType.is_active == True,
        or_(
            EmergencyType.created_by == None,
            EmergencyType.created_by == user_id
        )
    ).all()


# =========================
# CMS - GET ALL TYPES
# =========================
@router.get("/admin", response_model=list[EmergencyTypeResponse])
def get_all_types(db: Session = Depends(get_db)):
    return db.query(EmergencyType).all()


# =========================
# CMS - CREATE GLOBAL TYPE
# =========================
@router.post("/admin", response_model=EmergencyTypeResponse)
def create_admin_type(payload: EmergencyTypeCreate, db: Session = Depends(get_db)):
    new_type = EmergencyType(
        name=payload.name,
        is_active=True,
        created_by=None   # GLOBAL
    )

    db.add(new_type)
    db.commit()
    db.refresh(new_type)

    return new_type


# =========================
# MOBILE - CREATE PERSONAL TYPE
# =========================
@router.post("/mobile", response_model=EmergencyTypeResponse)
def create_mobile_type(payload: EmergencyTypeCreate, user_id: int, db: Session = Depends(get_db)):
    new_type = EmergencyType(
        name=payload.name,
        is_active=True,
        created_by=user_id   # PERSONAL
    )

    db.add(new_type)
    db.commit()
    db.refresh(new_type)

    return new_type


# =========================
# UPDATE TYPE (ADMIN FULL ACCESS)
# =========================
@router.put("/{type_id}", response_model=EmergencyTypeResponse)
def update_type(type_id: int, payload: EmergencyTypeUpdate, db: Session = Depends(get_db)):
    item = db.query(EmergencyType).filter(EmergencyType.id == type_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)

    return item


# =========================
# DELETE TYPE (ADMIN FULL ACCESS)
# =========================
@router.delete("/{type_id}")
def delete_type(type_id: int, db: Session = Depends(get_db)):
    item = db.query(EmergencyType).filter(EmergencyType.id == type_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    db.delete(item)
    db.commit()

    return {"message": "Deleted"}


# =========================
# TOGGLE ACTIVE (ADMIN)
# =========================
@router.patch("/{type_id}/toggle", response_model=EmergencyTypeResponse)
def toggle_status(type_id: int, db: Session = Depends(get_db)):
    item = db.query(EmergencyType).filter(EmergencyType.id == type_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    item.is_active = not item.is_active

    db.commit()
    db.refresh(item)

    return item