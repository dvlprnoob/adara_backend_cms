from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from models.emergency_type import EmergencyType
from schemas.emergency_type import *

router = APIRouter()

