from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import role_required
from db.session import get_db
from models.service_report import ServiceReport
from models.user import User
from schemas.service_report import ServiceReportCreate, ServiceReportResolve, ServiceReportResponse

router = APIRouter()


def serialize_report(report: ServiceReport) -> ServiceReportResponse:
    return ServiceReportResponse(
        id=report.id,
        user_id=report.user_id,
        user_name=report.user.name if report.user else None,
        user_email=report.user.email if report.user else None,
        report_type=report.report_type,
        subject=report.subject,
        description=report.description,
        status=report.status,
        admin_note=report.admin_note,
        created_at=report.created_at,
        resolved_at=report.resolved_at,
    )


def get_report_or_404(db: Session, report_id: int) -> ServiceReport:
    report = db.query(ServiceReport).filter(ServiceReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/", response_model=ServiceReportResponse)
def create_report(
    payload: ServiceReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["resident"])),
):
    report = ServiceReport(
        user_id=current_user.id,
        report_type=payload.report_type,
        subject=payload.subject.strip(),
        description=payload.description.strip(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return serialize_report(report)


@router.get("/", response_model=list[ServiceReportResponse])
def get_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"])),
):
    reports = db.query(ServiceReport).order_by(ServiceReport.created_at.desc()).all()
    return [serialize_report(report) for report in reports]


@router.get("/me", response_model=list[ServiceReportResponse])
def get_my_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["resident"])),
):
    reports = (
        db.query(ServiceReport)
        .filter(ServiceReport.user_id == current_user.id)
        .order_by(ServiceReport.created_at.desc())
        .all()
    )
    return [serialize_report(report) for report in reports]


@router.patch("/{report_id}/resolve", response_model=ServiceReportResponse)
def resolve_report(
    report_id: int,
    payload: ServiceReportResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"])),
):
    report = get_report_or_404(db, report_id)
    report.status = "resolved"
    report.admin_note = payload.admin_note
    report.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return serialize_report(report)


@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(["admin", "super_admin"])),
):
    report = get_report_or_404(db, report_id)
    db.delete(report)
    db.commit()
    return {"message": "Report deleted successfully"}
