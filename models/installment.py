from sqlalchemy import Column, Integer, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship
from decimal import Decimal

from db.base import Base


class Installment(Base):
    __tablename__ = "installments"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"), nullable=False)

    total_amount = Column(Numeric(12, 2), nullable=False)
    total_terms = Column(Integer, nullable=False)

    paid_terms = Column(Integer, default=0, nullable=False)

    # running | done
    status = Column(String(20), default="running", nullable=False)

    # Relationships
    user = relationship("User", back_populates="installments")

    payment_method = relationship(
        "PaymentMethod",
        back_populates="installments"
    )

    payment_logs = relationship(
        "InstallmentPaymentLog",
        back_populates="installment",
        cascade="all, delete-orphan",
        order_by="InstallmentPaymentLog.term_number",
    )

    @property
    def amount_per_term(self) -> Decimal:
        if self.total_terms == 0:
            return Decimal("0")
        return Decimal(self.total_amount) / Decimal(self.total_terms)


    @property
    def remaining_terms(self) -> int:
        return self.total_terms - self.paid_terms


    @property
    def remaining_payment(self) -> Decimal:
        return Decimal(self.amount_per_term) * Decimal(self.remaining_terms)


    @property
    def next_term(self):
        if self.paid_terms >= self.total_terms:
            return None
        return self.paid_terms + 1