from sqlalchemy import Column, Integer, String, Boolean, Enum
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import relationship
import enum

from db.session import Base


class PaymentMethodType(str, enum.Enum):
    installment = "installment"
    monthly_due = "monthly_due"
    one_time = "one_time"


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    type = Column(
        Enum(PaymentMethodType, name="payment_method_type"),
        nullable=False
    )

    max_installment = Column(Integer, nullable=True)

    due_day = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    installments = relationship(
        "Installment",
        back_populates="payment_method"
    )

    ipls = relationship(
        "IPL",
        back_populates="payment_method"
    )

    __table_args__ = (
        CheckConstraint(
            "max_installment IS NULL OR max_installment > 0",
            name="check_payment_method_max_installment_positive"
        ),
        CheckConstraint(
            "due_day IS NULL OR (due_day >= 1 AND due_day <= 31)",
            name="check_payment_method_due_day_range"
        ),
    )
