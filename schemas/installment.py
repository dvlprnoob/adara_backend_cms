from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class InstallmentCreate(BaseModel):
    user_id: int
    method: str
    total_amount: Decimal
    total_terms: int
    
class InstallmentResponse(BaseModel):
    id: int
    user_id: int
    method: str
    total_amount: Decimal
    total_terms: int
    paid_terms: int
    status: str
    
    class Config:
        from_attributes = True
        
        