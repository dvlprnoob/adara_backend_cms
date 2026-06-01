from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.session import Base


class InstallmentPaymentHistory(Base):
    __tablename__ = "installment_payment_histories"

    id = Column(Integer, primary_key=True, index=True)
    installment_id = Column(Integer, ForeignKey("installments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    term = Column(Integer, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String, nullable=False)
    proof_url = Column(String, nullable=True)
    rejection_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    installment = relationship("Installment")

    @property
    def payment_method_name(self):
        return self.installment.payment_method.name
