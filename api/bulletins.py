from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import role_required
from db.session import get_db
from models.bulletin import Bulletin
from schemas.bulletin import BulletinCreate, BulletinResponse, BulletinUpdate

router = APIRouter()


def get_bulletin_or_404(db: Session, bulletin_id: int) -> Bulletin:
    bulletin = db.query(Bulletin).filter(Bulletin.id == bulletin_id).first()
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin not found")
    return bulletin


@router.post("/", response_model=BulletinResponse)
def create_bulletin(
    payload: BulletinCreate,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin", "super_admin"])),
):
    bulletin = Bulletin(**payload.dict())
    db.add(bulletin)
    db.commit()
    db.refresh(bulletin)
    return bulletin


@router.get("/", response_model=list[BulletinResponse])
def get_bulletins(
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin", "super_admin"])),
):
    return db.query(Bulletin).order_by(Bulletin.created_at.desc()).all()


@router.get("/active", response_model=list[BulletinResponse])
def get_active_bulletins(db: Session = Depends(get_db)):
    return (
        db.query(Bulletin)
        .filter(Bulletin.is_active == True)
        .order_by(Bulletin.created_at.desc())
        .all()
    )


@router.put("/{bulletin_id}", response_model=BulletinResponse)
def update_bulletin(
    bulletin_id: int,
    payload: BulletinUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin", "super_admin"])),
):
    bulletin = get_bulletin_or_404(db, bulletin_id)
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(bulletin, key, value)
    db.commit()
    db.refresh(bulletin)
    return bulletin


@router.patch("/{bulletin_id}/toggle", response_model=BulletinResponse)
def toggle_bulletin(
    bulletin_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin", "super_admin"])),
):
    bulletin = get_bulletin_or_404(db, bulletin_id)
    bulletin.is_active = not bulletin.is_active
    db.commit()
    db.refresh(bulletin)
    return bulletin


@router.delete("/{bulletin_id}")
def delete_bulletin(
    bulletin_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin", "super_admin"])),
):
    bulletin = get_bulletin_or_404(db, bulletin_id)
    db.delete(bulletin)
    db.commit()
    return {"message": "Bulletin deleted successfully"}
