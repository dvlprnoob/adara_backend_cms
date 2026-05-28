from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from core.uploads import save_upload_image
from db.session import get_db
from models.installment import Installment, InstallmentStatus
from models.installment_payment_history import InstallmentPaymentHistory
from models.payment_method import PaymentMethod, PaymentMethodType
from models.user import User
from schemas.installment import InstallmentCreate, InstallmentDueDateUpdate, InstallmentPaymentHistoryResponse, InstallmentResponse, PaymentRejectRequest
from api.deps import role_required

router = APIRouter()


def add_months(value: date, months: int = 1) -> date:
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    days_in_month = [
        31,
        29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ][month - 1]
    return date(year, month, min(value.day, days_in_month))


@router.post("/", response_model=InstallmentResponse)
def create_installment(
    payload: InstallmentCreate,
    db: Session = Depends(get_db),
    user=Depends(role_required(["admin", "super_admin"]))
):
    resident = db.query(User).filter(User.id == payload.user_id).first()
    if not resident or resident.role.name != "resident":
        raise HTTPException(status_code=400, detail="Resident user not found")

    method = db.query(PaymentMethod).filter(
        PaymentMethod.id == payload.payment_method_id
    ).first()
    if not method or not method.is_active:
        raise HTTPException(status_code=400, detail="Active payment method not found")

    if method.type != PaymentMethodType.installment:
        raise HTTPException(status_code=400, detail="Payment method must be installment type")

    if method.max_installment and payload.total_terms > method.max_installment:
        raise HTTPException(status_code=400, detail="Total terms exceeds payment method limit")

    if payload.next_due_date < date.today():
        raise HTTPException(status_code=400, detail="Next due date cannot be in the past")

    existing = db.query(Installment).filter(
        Installment.user_id == payload.user_id,
        Installment.status != InstallmentStatus.cancelled
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Resident already has assigned KPR/installment")

    installment = Installment(
        user_id=payload.user_id,
        payment_method_id=payload.payment_method_id,
        total_amount=payload.total_amount,
        total_terms=payload.total_terms,
        paid_terms=0,
        status=InstallmentStatus.running,
        next_due_date=payload.next_due_date
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
    return db.query(Installment).filter(
        Installment.user_id == user.id
    ).all()


@router.get("/me/history", response_model=list[InstallmentPaymentHistoryResponse])
def get_my_installment_history(
    db: Session = Depends(get_db),
    user=Depends(role_required(["resident"]))
):
    installments = db.query(Installment).filter(
        Installment.user_id == user.id
    ).all()
    histories = db.query(InstallmentPaymentHistory).filter(
        InstallmentPaymentHistory.user_id == user.id
    ).order_by(InstallmentPaymentHistory.created_at.desc()).all()

    result = list(histories)
    approved_terms = {
        (item.installment_id, item.term)
        for item in histories
        if item.status == "approved"
    }

    for installment in installments:
        for term in range(1, installment.paid_terms + 1):
            if (installment.id, term) in approved_terms:
                continue
            result.append({
                "id": -(installment.id * 1000 + term),
                "installment_id": installment.id,
                "user_id": installment.user_id,
                "term": term,
                "amount": installment.amount_per_term,
                "status": "approved",
                "proof_url": None,
                "rejection_reason": None,
                "created_at": None,
            })

    return result


@router.get("/", response_model=list[InstallmentResponse])
def get_all_installments(
    db: Session = Depends(get_db),
    user=Depends(role_required(["admin", "super_admin"]))
):
    return db.query(Installment).all()


@router.post("/{installment_id}/upload-proof")
async def upload_installment_proof(
    installment_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(role_required(["resident"]))
):
    installment = db.query(Installment).filter(
        Installment.id == installment_id,
        Installment.user_id == user.id
    ).first()

    if not installment:
        raise HTTPException(status_code=404, detail="Installment not found")

    if installment.status != InstallmentStatus.running:
        raise HTTPException(status_code=400, detail="Installment is not payable")

    if installment.proof_url:
        raise HTTPException(status_code=400, detail="Proof already uploaded")

    installment.proof_url = await save_upload_image(file, "payment-proofs/installments")
    installment.rejection_reason = None

    db.commit()
    db.refresh(installment)

    return {
        "message": "Proof uploaded successfully",
        "proof_url": installment.proof_url
    }


@router.post("/{installment_id}/admin-upload-proof")
async def admin_upload_installment_proof(
    installment_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(role_required(["admin", "super_admin"]))
):
    installment = db.query(Installment).filter(
        Installment.id == installment_id
    ).first()

    if not installment:
        raise HTTPException(status_code=404, detail="Installment not found")

    if installment.status != InstallmentStatus.running:
        raise HTTPException(status_code=400, detail="Installment is not payable")

    installment.proof_url = await save_upload_image(file, "payment-proofs/installments")
    installment.rejection_reason = None

    db.commit()
    db.refresh(installment)

    return {
        "message": "Proof uploaded successfully",
        "proof_url": installment.proof_url
    }


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

    if not installment.proof_url:
        raise HTTPException(status_code=400, detail="Proof required before approval")

    term = installment.paid_terms + 1
    amount = installment.amount_per_term
    proof_url = installment.proof_url

    db.add(InstallmentPaymentHistory(
        installment_id=installment.id,
        user_id=installment.user_id,
        term=term,
        amount=amount,
        status="approved",
        proof_url=proof_url,
    ))

    # increment paid terms
    installment.paid_terms += 1

    # update status kalau sudah lunas
    if installment.paid_terms >= installment.total_terms:
        installment.status = InstallmentStatus.done
        installment.next_due_date = None
    elif installment.next_due_date:
        installment.next_due_date = add_months(installment.next_due_date)
    term = installment.paid_terms + 1
    amount = installment.amount_per_term
    proof_url = installment.proof_url

    db.add(InstallmentPaymentHistory(
        installment_id=installment.id,
        user_id=installment.user_id,
        term=term,
        amount=amount,
        status="rejected",
        proof_url=proof_url,
        rejection_reason=reason,
    ))

    installment.proof_url = None
    installment.rejection_reason = None

    db.commit()
    db.refresh(installment)

    return {"message": "Installment payment approved"}


@router.patch("/{installment_id}/due-date", response_model=InstallmentResponse)
def update_installment_due_date(
    installment_id: int,
    payload: InstallmentDueDateUpdate,
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

    installment.next_due_date = payload.next_due_date
    db.commit()
    db.refresh(installment)

    return installment


@router.patch("/{installment_id}/reject")
def reject_installment(
    installment_id: int,
    payload: PaymentRejectRequest,
    db: Session = Depends(get_db),
    user=Depends(role_required(["admin", "super_admin"]))
):
    installment = db.query(Installment).filter(
        Installment.id == installment_id
    ).first()

    if not installment:
        raise HTTPException(status_code=404, detail="Installment not found")

    if not installment.proof_url:
        raise HTTPException(status_code=400, detail="No proof to reject")

    reason = payload.reason.strip()
    if not reason:
        raise HTTPException(status_code=400, detail="Reject reason is required")

    installment.proof_url = None
    installment.rejection_reason = reason

    db.commit()
    db.refresh(installment)

    return {"message": "Installment payment rejected", "reason": reason}
