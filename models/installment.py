from sqlalchemy import Column, Integer, ForeignKey, Numeric, Enum
from sqlalchemy.orm import relationship
import enum

from db.session import Base


class InstallmentStatus(str, enum.Enum):
    running = "running"
    done = "done"


class Installment(Base):
    __tablename__ = "installments"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    payment_method_id = Column(
        Integer,
        ForeignKey("payment_methods.id"),
        nullable=False
    )

    total_amount = Column(Numeric(15, 2), nullable=False)

    total_terms = Column(Integer, nullable=False)

    paid_terms = Column(Integer, default=0)

    status = Column(
        Enum(InstallmentStatus),
        default=InstallmentStatus.running
    )

    user = relationship("User", back_populates="installments")
    payment_method = relationship("PaymentMethod", back_populates="installments")