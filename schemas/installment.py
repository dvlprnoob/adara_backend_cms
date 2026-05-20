from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date

class InstallmentCreate(BaseModel):
    user_id: int
    payment_method_id: int
    total_amount: Decimal = Field(gt=0)
    total_terms: int = Field(gt=0)
    next_due_date: date


class InstallmentDueDateUpdate(BaseModel):
    next_due_date: date
    
class InstallmentResponse(BaseModel):
    id: int
    user_id: int
    payment_method_id: int
    total_amount: Decimal
    total_terms: int
    paid_terms: int
    status: str
    proof_url: str | None
    next_due_date: date | None

    amount_per_term: Decimal
    remaining_terms: int
    remaining_payment: Decimal
    next_term: int | None
    
    class Config:
        from_attributes = True
        
        
