from sqlalchemy import Column, Integer, ForeignKey, Numeric, Enum
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

    status = Column(
        Enum(InstallmentStatus, name="installment_status"),
        default=InstallmentStatus.running,
        nullable=False
    )

    __table_args__ = (
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