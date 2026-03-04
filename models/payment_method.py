from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from db.session import Base


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    type = Column(String, nullable=False)
    # installment
    # monthly_due
    # one_time

    max_installment = Column(Integer, nullable=True)

    due_day = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True)

    installments = relationship("Installment", back_populates="payment_method")
    ipls = relationship("IPL", back_populates="payment_method")