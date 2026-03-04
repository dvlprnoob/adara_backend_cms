from pydantic import BaseModel
from decimal import Decimal

class IPLCreate(BaseModel):
    user_id: int
    month: int
    amount: Decimal
    due_day: int

class IPLResponse(BaseModel):
    id: int
    user_id: int
    month: str
    amount: Decimal
    due_day: int
    status: str
    proof: str | None
    
    class Config:
        from_attributes = True