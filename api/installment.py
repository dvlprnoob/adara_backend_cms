from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from models.installment import Installment, InstallmentStatus
from schemas.installment import InstallmentCreate, InstallmentResponse
from schemas.payment import UploadProof
from api.deps import role_required

router = APIRouter()


@router.post("/", response_model=InstallmentResponse)
def create_installment(
    payload: InstallmentCreate,
    db: Session = Depends(get_db),
    user=Depends(role_required(["admin", "super_admin"]))
):
    installment = Installment(
        user_id=payload.user_id,
        payment_method_id=payload.payment_method_id,
        total_amount=payload.total_amount,
        total_terms=payload.total_terms,
        paid_terms=0,
        status=InstallmentStatus.running
    )

    db.add(installment)
    db.commit()
    db.refresh(installment)

    return installment


@router.get("/me", response_model=list[InstallmentResponse])
def get_my_installments(
    db: Session = Depends(get_db),
    user=Depends(role_required(["resident"]))
):
    installments = db.query(Installment).filter(
        Installment.user_id == user.id
    ).all()

    result = []

    for inst in installments:
        amount_per_term = inst.total_amount / inst.total_terms
        remaining_terms = inst.total_terms - inst.paid_terms
        remaining_payment = amount_per_term * remaining_terms

        next_term = None
        if inst.status != InstallmentStatus.done:
            next_term = inst.paid_terms + 1

        data = InstallmentResponse.model_validate(inst).model_dump()

        data.update({
            "amount_per_term": amount_per_term,
            "remaining_terms": remaining_terms,
            "remaining_payment": remaining_payment,
            "next_term": next_term
        })

        result.append(data)

    return result


@router.get("/", response_model=list[InstallmentResponse])
def get_all_installments(
    db: Session = Depends(get_db),
    user=Depends(role_required(["admin", "super_admin"]))
):
    return db.query(Installment).all()


@router.post("/{installment_id}/upload-proof")
def upload_installment_proof(
    installment_id: int,
    payload: UploadProof,
    db: Session = Depends(get_db),
    user=Depends(role_required(["resident"]))
):
    installment = db.query(Installment).filter(
        Installment.id == installment_id,
        Installment.user_id == user.id
    ).first()

    if not installment:
        raise HTTPException(status_code=404, detail="Installment not found")

    if installment.proof_url:
        raise HTTPException(status_code=400, detail="Proof already uploaded")

    installment.proof_url = payload.proof_url

    db.commit()
    db.refresh(installment)

    return {"message": "Proof uploaded successfully"}


@router.patch("/{installment_id}/approve")
def approve_installment(
    installment_id: int,
    db: Session = Depends(get_db),
    user=Depends(role_required(["admin", "super_admin"]))
):
    installment = db.query(Installment).filter(
        Installment.id == installment_id
    ).first()

    if not installment:
        raise HTTPException(status_code=404, detail="Installment not found")

    if installment.status == InstallmentStatus.done:
        raise HTTPException(status_code=400, detail="Installment already completed")

    # increment paid terms
    installment.paid_terms += 1

    # update status kalau sudah lunas
    if installment.paid_terms >= installment.total_terms:
        installment.status = InstallmentStatus.done

    db.commit()
    db.refresh(installment)

    return {"message": "Installment payment approved"}