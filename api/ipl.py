from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from models.ipl import IPL
from schemas.ipl import IPLCreate, IPLResponse
from api.deps import role_required

router = APIRouter()

@router.post("/", response_model=IPLResponse)
def create_ipl(
    payload: IPLCreate,
    db: Session = Depends(get_db),
    user = Depends(role_required(["admin", "super_admin"]))
): 
    ipl = IPL(**payload.model_dump())
    
    db.add(ipl)
    db.commit()
    db.refresh(ipl)
    
    return ipl

@router.get("/me", response_model=list[IPLResponse])
def get_my_ipl(
    db: Session = Depends(get_db),
    user = Depends(role_required(["resident"]))
):
    return db.query(IPL).filter(
        IPL.user_id == user.id
    ).all()
    
@router.get("/", response_model=list[IPLResponse])
def get_all_ipl(
    db: Session = Depends(get_db),
    user = Depends(role_required(["admin", "super_admin"]))
):
    return db.query(IPL).all()