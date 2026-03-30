from pydantic import BaseModel
from decimal import Decimal
from datetime import date

class IPLCreate(BaseModel):
    user_id: int
    payment_method_id: int
    month: str
    amount: Decimal
    due_day: int

class IPLResponse(BaseModel):
    id: int
    user_id: int
    payment_method_id: int
    month: date
    amount: Decimal
    due_day: int
    status: str
    proof: str | None
    
    class Config:
        from_attributes = True