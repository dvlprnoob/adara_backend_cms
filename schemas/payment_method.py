from pydantic import BaseModel, Field, model_validator
from typing import Optional
from models.payment_method import PaymentMethodType

class PaymentMethodCreate(BaseModel):
    name: str
    type: PaymentMethodType
    max_installment: Optional[int] = Field(default=None, gt=0)
    due_day: Optional[int] = Field(default=None, ge=1, le=31)

    @model_validator(mode="after")
    def validate_settings(self):
        if self.type == PaymentMethodType.installment and self.max_installment is None:
            raise ValueError("max_installment is required for installment payment methods")
        if self.type == PaymentMethodType.monthly_due and self.due_day is None:
            raise ValueError("due_day is required for monthly_due payment methods")
        return self


class PaymentMethodUpdate(BaseModel):
    max_installment: Optional[int] = Field(default=None, gt=0)
    due_day: Optional[int] = Field(default=None, ge=1, le=31)
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
