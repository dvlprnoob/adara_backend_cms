from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from core.uploads import save_upload_image
from db.session import get_db
from models.ipl import IPL, IPLStatus
from models.payment_method import PaymentMethod, PaymentMethodType
from models.user import User
from schemas.ipl import IPLCreate, IPLResponse, PaymentRejectRequest
from api.deps import role_required

router = APIRouter()


@router.post("/", response_model=IPLResponse)
def create_ipl(
    payload: IPLCreate,
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

    if method.type != PaymentMethodType.monthly_due:
        raise HTTPException(status_code=400, detail="Payment method must be monthly_due type")

    if method.due_day and payload.due_day != method.due_day:
        raise HTTPException(status_code=400, detail="Due day must match payment method")

    # prevent duplicate IPL (user + payment_method + month)
    existing = db.query(IPL).filter(
        IPL.user_id == payload.user_id,
        IPL.payment_method_id == payload.payment_method_id,
        IPL.month == payload.month
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="IPL for this month already exists"
        )

    ipl = IPL(**payload.model_dump())

    db.add(ipl)
    db.commit()
    db.refresh(ipl)

    return ipl


@router.get("/me", response_model=list[IPLResponse])
def get_my_ipl(
    db: Session = Depends(get_db),
    user=Depends(role_required(["resident"]))
):
    return db.query(IPL).filter(
        IPL.user_id == user.id
    ).order_by(IPL.month.desc()).all()


@router.get("/", response_model=list[IPLResponse])
def get_all_ipl(
    db: Session = Depends(get_db),
    user=Depends(role_required(["admin", "super_admin"]))
):
    return db.query(IPL).order_by(IPL.month.desc()).all()


@router.post("/{ipl_id}/upload-proof")
async def upload_ipl_proof(
    ipl_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(role_required(["resident"]))
):
    ipl = db.query(IPL).filter(
        IPL.id == ipl_id,
        IPL.user_id == user.id
    ).first()

    if not ipl:
        raise HTTPException(status_code=404, detail="IPL not found")

    if ipl.proof_url:
        raise HTTPException(status_code=400, detail="Proof already uploaded")

    if ipl.status == IPLStatus.paid:
        raise HTTPException(status_code=400, detail="IPL already paid")

    ipl.proof_url = await save_upload_image(file, "payment-proofs/ipls")
    ipl.rejection_reason = None

    db.commit()
    db.refresh(ipl)

    return {
        "message": "Proof uploaded successfully",
        "proof_url": ipl.proof_url
    }


@router.post("/{ipl_id}/admin-upload-proof")
async def admin_upload_ipl_proof(
    ipl_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(role_required(["admin", "super_admin"]))
):
    ipl = db.query(IPL).filter(
        IPL.id == ipl_id
    ).first()

    if not ipl:
        raise HTTPException(status_code=404, detail="IPL not found")

    if ipl.status == IPLStatus.paid:
        raise HTTPException(status_code=400, detail="IPL already paid")

    ipl.proof_url = await save_upload_image(file, "payment-proofs/ipls")
    ipl.rejection_reason = None

    db.commit()
    db.refresh(ipl)

    return {
        "message": "Proof uploaded successfully",
        "proof_url": ipl.proof_url
    }


@router.patch("/{ipl_id}/approve")
def approve_ipl(
    ipl_id: int,
    db: Session = Depends(get_db),
    user=Depends(role_required(["admin", "super_admin"]))
):
    ipl = db.query(IPL).filter(
        IPL.id == ipl_id
    ).first()

    if not ipl:
        raise HTTPException(status_code=404, detail="IPL not found")

    if not ipl.proof_url:
        raise HTTPException(
            status_code=400,
            detail="Proof required before approval"
        )

    if ipl.status == IPLStatus.paid:
        raise HTTPException(status_code=400, detail="Already paid")

    ipl.status = IPLStatus.paid
    ipl.rejection_reason = None

    db.commit()
    db.refresh(ipl)

    return {"message": "IPL approved"}


@router.patch("/{ipl_id}/reject")
def reject_ipl(
    ipl_id: int,
    payload: PaymentRejectRequest,
    db: Session = Depends(get_db),
    user=Depends(role_required(["admin", "super_admin"]))
):
    ipl = db.query(IPL).filter(
        IPL.id == ipl_id
    ).first()

    if not ipl:
        raise HTTPException(status_code=404, detail="IPL not found")

    if not ipl.proof_url:
        raise HTTPException(status_code=400, detail="No proof to reject")

    if ipl.status == IPLStatus.paid:
        raise HTTPException(status_code=400, detail="Already paid")

    reason = payload.reason.strip()
    if not reason:
        raise HTTPException(status_code=400, detail="Reject reason is required")

    ipl.proof_url = None
    ipl.rejection_reason = reason

    db.commit()
    db.refresh(ipl)

    return {"message": "IPL rejected", "reason": reason}
