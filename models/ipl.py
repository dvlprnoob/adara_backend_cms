from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, Enum, Date
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
import enum

from db.session import Base


class IPLStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"


class IPL(Base):
    __tablename__ = "ipl"

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

    # Simpan sebagai tanggal (recommend: pakai tanggal 1 tiap bulan)
    month = Column(Date, nullable=False, index=True)

    amount = Column(Numeric(15, 2), nullable=False)

    # Idealnya 1 - 31
    due_day = Column(Integer, nullable=False)

    status = Column(
        Enum(IPLStatus, name="ipl_status"),
        default=IPLStatus.pending,
        nullable=False
    )

    proof_url = Column(String, nullable=True)

    user = relationship(
        "User",
        back_populates="ipls"
    )

    payment_method = relationship(
        "PaymentMethod",
        back_populates="ipls"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "payment_method_id",
            "month",
            name="uq_ipl_user_method_month"
        ),
        CheckConstraint("amount > 0", name="check_ipl_amount_positive"),
        CheckConstraint("due_day >= 1 AND due_day <= 31", name="check_ipl_due_day_range"),
    )
