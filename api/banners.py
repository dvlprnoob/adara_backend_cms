from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from models.banner import Banner
from schemas.banner import BannerCreate, BannerResponse, BannerUpdate
from api.deps import role_required

router = APIRouter()

@router.post("/", response_model=BannerResponse)
def create_banner(
    payload: BannerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    banner = Banner(**payload.dict())
    
    db.add(banner)
    db.commit()
    db.refresh(banner)
    
    return banner


@router.get("/", response_model=list[BannerResponse])
def get_all_banners(
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    return db.query(Banner).all()

@router.get("/active", response_model=list[BannerResponse])
def get_active_banner(
    db: Session = Depends(get_db)
):
    return db.query(Banner).filter(Banner.is_active == True).all()

@router.get("/{banner_id}", response_model=BannerResponse)
def get_banner(
  banner_id: int,
  db: Session = Depends(get_db),
  current_user = Depends(role_required(["admin", "super_admin"]))
):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    return banner

@router.put("/{banner_id}", response_model=BannerResponse)
def update_banner(
  banner_id: int,
  payload: BannerUpdate,
  db: Session = Depends(get_db),
  current_user = Depends(role_required(["admin", "super_admin"]))
):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(banner, key, value)
        
    db.commit()
    db.refresh(banner)
    
    return banner

@router.delete("/{banner_id}")
def delete_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    db.delete(banner)
    db.commit()
    
    return {"message": "Banner deleted successfully"}

@router.put("/{banner_id}/toggle", response_model=BannerResponse)
def toggle_banner_status(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    banner.is_active = not banner.is_active
    
    db.commit()
    db.refresh(banner)
    
    return banner