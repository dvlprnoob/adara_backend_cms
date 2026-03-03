from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from models.service import Service
from schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from api.deps import role_required

router = APIRouter()

# =========================
# CREATE SERVICE (ADMIN ONLY)
# =========================
@router.post("/", response_model=ServiceResponse)
def create_service(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    new_service = Service(**payload.dict())
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return new_service


# =========================
# GET ALL SERVICES
# (Bisa diakses semua, atau tambahkan role_required kalau khusus CMS)
# =========================
@router.get("/", response_model=list[ServiceResponse])
def get_services(db: Session = Depends(get_db)):
    return db.query(Service).all()


# =========================
# GET SINGLE SERVICE
# =========================
@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    return service


# =========================
# UPDATE SERVICE (ADMIN ONLY)
# =========================
@router.put("/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: int,
    payload: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(service, key, value)

    db.commit()
    db.refresh(service)

    return service


# =========================
# DELETE SERVICE (ADMIN ONLY)
# =========================
@router.delete("/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    db.delete(service)
    db.commit()

    return {"message": "Service deleted successfully"}


# =========================
# TOGGLE STATUS (ADMIN ONLY)
# =========================
@router.patch("/{service_id}/toggle", response_model=ServiceResponse)
def toggle_status(
    service_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["admin", "super_admin"]))
):
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    service.is_active = not service.is_active

    db.commit()
    db.refresh(service)

    return service