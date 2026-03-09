from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, func
from sqlalchemy.orm import relationship

from db.base import Base


class InstallmentPaymentLog(Base):
    __tablename__ = "installment_payment_logs"

    id = Column(Integer, primary_key=True, index=True)

    installment_id = Column(
        Integer,
        ForeignKey("installments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    term_number = Column(Integer, nullable=False)

    proof_url = Column(String, nullable=False)

    # pending | approved | rejected
    status = Column(String(20), default="pending", nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    approved_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    installment = relationship(
        "Installment",
        back_populates="payment_logs"
    )