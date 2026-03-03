from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from api.deps import role_required
from models.emergency_type import EmergencyType
from models.emergency_report import EmergencyReport
from models.resident_profile import ResidentProfile
from models.user import User
from schemas.emergency_report import EmergencyReportResponse, EmergencyReportCreate

router = APIRouter()

# =================================================
# CREATE REPORT (RESIDENT ONLY)
# =================================================
@router.post("/", response_model=EmergencyReportResponse)
def create_report(
    payload: EmergencyReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["resident"]))
):
    profile = db.query(ResidentProfile).filter(
        ResidentProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=400, detail="Resident profile not found")

    emergency_type = db.query(EmergencyType).filter(
        EmergencyType.id == payload.emergency_type_id,
        EmergencyType.is_active == True
    ).first()

    if not emergency_type:
        raise HTTPException(status_code=404, detail="Emergency type not found")

    new_report = EmergencyReport(
        user_id=current_user.id,
        user_name=current_user.name,
        block=profile.block,
        type_id=emergency_type.id,
        type_name=emergency_type.name,
        status="active"
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return new_report


# =================================================
# GET ALL REPORTS (ADMIN CMS)
# =================================================
@router.get("/", response_model=list[EmergencyReportResponse])
def get_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"]))
):
    return db.query(EmergencyReport)\
        .order_by(EmergencyReport.created_at.desc())\
        .all()


# =================================================
# RESOLVE REPORT (ADMIN)
# =================================================
@router.patch("/{report_id}/resolve", response_model=EmergencyReportResponse)
def resolve_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"]))
):
    report = db.query(EmergencyReport)\
        .filter(EmergencyReport.id == report_id)\
        .first()

    if not report:
        raise HTTPException(status_code=404, detail="Not found")

    report.status = "resolved"
    db.commit()
    db.refresh(report)

    return report