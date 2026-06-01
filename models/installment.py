from sqlalchemy import Column, Date, Integer, ForeignKey, Numeric, Enum, String
from sqlalchemy.orm import relationship
from sqlalchemy import CheckConstraint
import enum

from db.session import Base


class InstallmentStatus(str, enum.Enum):
    running = "running"
    done = "done"
    overdue = "overdue"       # future-proof
    cancelled = "cancelled"   # optional tapi berguna


class Installment(Base):
    __tablename__ = "installments"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    payment_method_id = Column(
        Integer,
        ForeignKey("payment_methods.id"),
        nullable=False,
        index=True
    )

    total_amount = Column(Numeric(15, 2), nullable=False)

    total_terms = Column(Integer, nullable=False)

    paid_terms = Column(Integer, default=0, nullable=False)

    proof_url = Column(String, nullable=True)

    rejection_reason = Column(String, nullable=True)

    next_due_date = Column(Date, nullable=True)

    status = Column(
        Enum(InstallmentStatus, name="installment_status"),
        default=InstallmentStatus.running,
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("total_amount > 0", name="check_total_amount_positive"),
        CheckConstraint("total_terms > 0", name="check_total_terms_positive"),
        CheckConstraint("paid_terms >= 0", name="check_paid_terms_non_negative"),
        CheckConstraint("paid_terms <= total_terms", name="check_paid_not_exceed_total"),
    )

    user = relationship(
        "User",
        back_populates="installments"
    )

    payment_method = relationship(
        "PaymentMethod",
        back_populates="installments"
    )

    @property
    def amount_per_term(self):
        return self.total_amount / self.total_terms

    @property
    def remaining_terms(self):
        return self.total_terms - self.paid_terms

    @property
    def remaining_payment(self):
        return self.amount_per_term * self.remaining_terms

    @property
    def next_term(self):
        if self.status == InstallmentStatus.done:
            return None
        return self.paid_terms + 1

    @property
    def payment_method_name(self):
        return self.payment_method.name
