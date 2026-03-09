from pydantic import BaseModel
from typing import Optional

class PaymentMethodCreate(BaseModel):
    name: str
    type: str
    max_installment: Optional[int] = None
    due_day: Optional[int] = None


class PaymentMethodUpdate(BaseModel):
    max_installment: Optional[int] = None
    due_day: Optional[int] = None
    is_active: Optional[bool] = None


class PaymentMethodResponse(BaseModel):
    id: int
    name: str
    type: str
    max_installment: Optional[int]
    due_day: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True