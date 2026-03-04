from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class InstallmentCreate(BaseModel):
    user_id: int
    payment_method_id: int
    total_amount: Decimal
    total_terms: int
    
class InstallmentResponse(BaseModel):
    id: int
    user_id: int
    payment_method_id: int
    total_amount: Decimal
    total_terms: int
    paid_terms: int
    status: str

    amount_per_term: Decimal
    remaining_terms: int
    remaining_payment: Decimal
    next_term: int | None
    
    class Config:
        from_attributes = True
        
        