from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from models.installment import Installment, InstallmentStatus
from schemas.installment import InstallmentCreate, InstallmentResponse
from api.deps import role_required

router = APIRouter()

@router.post("/", response_model=InstallmentResponse)
def create_installment(
    payload: InstallmentCreate,
    db: Session = Depends(get_db),
    user = Depends(role_required(["admin", "super_admin"]))
): 
    installment = Installment(
        user_id=payload.user_id,
        method=payload.method,
        total_amount=payload.total_amount,
        total_terms=payload.total_terms,
        paid_terms=0
    )
    
    db.add(installment)
    db.commit()
    db.refresh(installment)
    
    return installment

@router.get("/me", response_model=list[InstallmentResponse])
def get_my_installments(
    db: Session = Depends(get_db),
    user = Depends(role_required(["resident"]))
):
    return db.query(Installment).filter(
        Installment.user_id == user.id
    ).all()
    
@router.get("/", response_model=list[InstallmentResponse])
def get_all_installments(
    db: Session = Depends(get_db),
    user = Depends(role_required(["admin", "super_admin"]))
):
    return db.query(Installment).all()