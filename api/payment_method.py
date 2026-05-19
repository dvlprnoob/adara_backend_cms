from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from models.payment_method import PaymentMethod
from schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodResponse,
    PaymentMethodUpdate
)

from api.deps import role_required

router = APIRouter()

#GET LIST
@router.get("/", response_model=list[PaymentMethodResponse])
def get_payment_methods(
    db: Session = Depends(get_db),
    user = Depends(role_required(["admin", "super_admin"]))
):
    methods = db.query(PaymentMethod).filter(
        PaymentMethod.is_active == True
    ).all()
    return methods


@router.get("/admin", response_model=list[PaymentMethodResponse])
def get_all_payment_methods(
    db: Session = Depends(get_db),
    user = Depends(role_required(["admin", "super_admin"]))
):
    return db.query(PaymentMethod).all()

#Create Payment Method
@router.post("/", response_model=PaymentMethodResponse)
def create_payment_method(
    payload: PaymentMethodCreate,
    db: Session = Depends(get_db),
    user = Depends(role_required(["admin", "super_admin"]))
):
    existing = db.query(PaymentMethod).filter(
        PaymentMethod.name == payload.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Payment Method name already exists")

    method = PaymentMethod(**payload.model_dump())
    
    db.add(method)
    db.commit()
    db.refresh(method)

    return method

#Update Settings
@router.patch("/{method_id}", response_model=PaymentMethodResponse)
def update_payment_method(
    method_id: int,
    payload: PaymentMethodUpdate,
    db: Session = Depends(get_db),
    user = Depends(role_required(["admin", "super_admin"]))
):
    method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_id
    ).first()

    if not method: 
        raise HTTPException(status_code=404, detail="Payment Method not Found")
    
    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(method, key, value)

    db.commit()
    db.refresh(method)

    return method


#Delete payment method
@router.delete("/{method_id}")
def delete_payment_method(
    method_id: int,
    db: Session = Depends(get_db),
    user = Depends(role_required(["super_admin"]))
):
    method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_id
    ).first()

    if not method:
        raise HTTPException(status_code=404, detail="Payment Method not Found")

    if method.installments or method.ipls:
        raise HTTPException(
            status_code=400,
            detail="Payment Method already used, deactivate it instead"
        )
    
    db.delete(method)
    db.commit()

    return {"message": "Payment Method Deleted"}
