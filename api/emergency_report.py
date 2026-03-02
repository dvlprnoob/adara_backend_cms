from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from models.emergency_report import EmergencyReport
from schemas.emergency_report import EmergencyReportResponse

router = APIRouter()

@router.get("/", response_model=list[EmergencyReportResponse])
def get_reports(db: Session = Depends(get_db)):
    return db.query(EmergencyReport).order_by(EmergencyReport.created_at.desc())

@router.patch("/{report_id}/resolve", response_model=EmergencyReportResponse)
def resolve_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(EmergencyReport).filter(EmergencyReport.id == report_id).first()

    if report:
        report.status = "resolved"
        db.commit()
        db.refresh(report)

    return report

@router.delete("/{report_id}")
def delete_report(report_id:  int, db: Session = Depends(get_db)):
    report = db.query(EmergencyReport).filter(EmergencyReport.id == report_id).first()

    if report:
        db.delete(report)
        db.commit()

    return {"messasge": "Deleted"}