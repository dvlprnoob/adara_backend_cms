from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date

class IPLCreate(BaseModel):
    user_id: int
    payment_method_id: int
    month: date
    amount: Decimal = Field(gt=0)
    due_day: int = Field(ge=1, le=31)

class IPLResponse(BaseModel):
    id: int
    user_id: int
    payment_method_id: int
    month: date
    amount: Decimal
    due_day: int
    status: str
    proof_url: str | None
    
    class Config:
        from_attributes = True
