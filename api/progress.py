import json
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from api.deps import role_required
from core.uploads import save_upload_image
from db.session import get_db
from models.progress import ConstructionProgress, ConstructionProgressUpdate
from models.user import User
from schemas.progress import (
    ProgressCreate,
    ProgressResponse,
    ProgressStatusUpdate,
    ProgressUpdateCreate,
    ProgressUpdateResponse,
    ProgressWarrantyUpdate,
)

router = APIRouter()


def serialize_update(update: ConstructionProgressUpdate) -> ProgressUpdateResponse:
    photos = []
    if update.photos:
        try:
            photos = json.loads(update.photos)
        except json.JSONDecodeError:
            photos = []

    return ProgressUpdateResponse(
        id=update.id,
        date=update.created_at,
        note=update.note,
        photos=photos,
    )


def serialize_progress(progress: ConstructionProgress) -> ProgressResponse:
    return ProgressResponse(
        id=progress.id,
        user_id=progress.user_id,
        user_name=progress.user.name if progress.user else None,
        user_email=progress.user.email if progress.user else None,
        status=progress.status,
        percent=progress.percent,
        is_done=progress.is_done,
        handover_date=progress.handover_date,
        warranty_end_date=progress.warranty_end_date,
        updates=[serialize_update(update) for update in progress.updates],
    )


def get_progress_or_404(db: Session, progress_id: int):
    progress = db.query(ConstructionProgress).filter(
        ConstructionProgress.id == progress_id
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    return progress


@router.get("/", response_model=list[ProgressResponse])
def get_all_progress(
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin", "super_admin"]))
):
    progress_items = db.query(ConstructionProgress).all()
    return [serialize_progress(item) for item in progress_items]


@router.get("/user/{user_id}", response_model=ProgressResponse)
def get_progress_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["resident", "admin", "super_admin"]))
):
    if current_user.role.name == "resident" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Operation not permitted")

    progress = db.query(ConstructionProgress).filter(
        ConstructionProgress.user_id == user_id
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    return serialize_progress(progress)


@router.get("/{progress_id}", response_model=ProgressResponse)
def get_progress(
    progress_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin", "super_admin"]))
):
    return serialize_progress(get_progress_or_404(db, progress_id))


@router.post("/", response_model=ProgressResponse)
def create_progress(
    payload: ProgressCreate,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin", "super_admin"]))
):
    resident = db.query(User).filter(User.id == payload.user_id).first()
    if not resident or resident.role.name != "resident":
        raise HTTPException(status_code=400, detail="Resident user not found")

    existing = db.query(ConstructionProgress).filter(
        ConstructionProgress.user_id == payload.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already has progress")

    progress = ConstructionProgress(
        user_id=payload.user_id,
        status=payload.status,
        percent=payload.percent,
        is_done=payload.status == "done",
    )
    db.add(progress)
    db.flush()

    db.add(ConstructionProgressUpdate(
        progress_id=progress.id,
        note=payload.note,
        photos=json.dumps(payload.photos[:6]),
    ))

    db.commit()
    db.refresh(progress)

    return serialize_progress(progress)


@router.post("/{progress_id}/updates", response_model=ProgressResponse)
def add_progress_update(
    progress_id: int,
    payload: ProgressUpdateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin", "super_admin"]))
):
    progress = get_progress_or_404(db, progress_id)

    if progress.is_done:
        raise HTTPException(status_code=400, detail="Progress is already done")

    db.add(ConstructionProgressUpdate(
        progress_id=progress.id,
        note=payload.note,
        photos=json.dumps(payload.photos[:6]),
    ))
    db.commit()
    db.refresh(progress)

    return serialize_progress(progress)


@router.patch("/{progress_id}/status", response_model=ProgressResponse)
def update_progress_status(
    progress_id: int,
    payload: ProgressStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin", "super_admin"]))
):
    progress = get_progress_or_404(db, progress_id)

    if progress.is_done:
        raise HTTPException(status_code=400, detail="Progress is already done")

    progress.status = payload.status
    progress.percent = payload.percent
    progress.is_done = payload.status == "done" or payload.percent >= 100

    if progress.is_done:
        progress.handover_date = payload.handover_date or progress.handover_date or date.today()
        progress.warranty_end_date = payload.warranty_end_date or progress.warranty_end_date
    else:
        progress.handover_date = payload.handover_date
        progress.warranty_end_date = payload.warranty_end_date

    note = payload.note or f"Status progress diupdate ke {payload.status} ({payload.percent}%)"
    db.add(ConstructionProgressUpdate(
        progress_id=progress.id,
        note=note,
        photos=json.dumps(payload.photos[:6]),
    ))

    db.commit()
    db.refresh(progress)

    return serialize_progress(progress)


@router.delete("/{progress_id}")
def delete_progress(
    progress_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin", "super_admin"]))
):
    progress = get_progress_or_404(db, progress_id)
    db.delete(progress)
    db.commit()
    return {"message": "Progress deleted successfully"}


@router.patch("/{progress_id}/warranty", response_model=ProgressResponse)
def update_progress_warranty(
    progress_id: int,
    payload: ProgressWarrantyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin", "super_admin"]))
):
    progress = get_progress_or_404(db, progress_id)
    progress.handover_date = payload.handover_date
    progress.warranty_end_date = payload.warranty_end_date
    db.commit()
    db.refresh(progress)
    return serialize_progress(progress)


@router.post("/photos/upload")
async def upload_progress_photos(
    request: Request,
    current_user=Depends(role_required(["admin", "super_admin"]))
):
    form = await request.form()
    files = []

    for key in ("files", "file", "photos", "photo"):
        files.extend(form.getlist(key))

    files = [
        file for file in files
        if hasattr(file, "filename") and hasattr(file, "read")
    ]

    if not files:
        raise HTTPException(
            status_code=400,
            detail="No photos uploaded. Use multipart form field 'files'."
        )

    if len(files) > 6:
        raise HTTPException(status_code=400, detail="Maximum 6 photos are allowed")

    urls = []
    for file in files:
        urls.append(await save_upload_image(file, "progress"))

    return {"photos": urls}
