from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from models.role import Role
from api.deps import role_required

router = APIRouter()

@router.get("/")
def get_roles(
    db: Session = Depends(get_db),
    current_user = Depends(role_required(["super_admin", "admin"]))
):
    roles = db.query(Role).all()
    return [{"id": r.id, "name": r.name} for r in roles]