from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from models.ipl import IPL, IPLStatus
from schemas.ipl import IPLCreate, IPLResponse
from schemas.payment import UploadProof
from api.deps import role_required

router = APIRouter()


@router.post("/", response_model=IPLResponse)
def create_ipl(
    payload: IPLCreate,
    db: Session = Depends(get_db),
    user=Depends(role_required(["admin", "super_admin"]))
):
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


@router.patch("/{ipl_id}/pay")
def pay_ipl(
    ipl_id: int,
    db: Session = Depends(get_db),
    user=Depends(role_required(["resident"]))
):
    ipl = db.query(IPL).filter(
        IPL.id == ipl_id,
        IPL.user_id == user.id
    ).first()

    if not ipl:
        raise HTTPException(status_code=404, detail="IPL not found")

    if ipl.status == IPLStatus.paid:
        raise HTTPException(status_code=400, detail="IPL already paid")

    # kalau pakai approval flow → jangan langsung paid
    if ipl.proof_url:
        raise HTTPException(
            status_code=400,
            detail="Use approval flow (upload proof already used)"
        )

    ipl.status = IPLStatus.paid

    db.commit()
    db.refresh(ipl)

    return {"message": "IPL paid successfully"}


@router.post("/{ipl_id}/upload-proof")
def upload_ipl_proof(
    ipl_id: int,
    payload: UploadProof,
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

    ipl.proof_url = payload.proof_url

    db.commit()
    db.refresh(ipl)

    return {"message": "Proof uploaded successfully"}


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

    db.commit()
    db.refresh(ipl)

    return {"message": "IPL approved"}