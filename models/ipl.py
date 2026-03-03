from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, Enum
from sqlalchemy.orm import relationship
import enum

from db.base import Base

class IPLStatus(enum.Enum):
    pending = "pending"
    paid = "paid"
    
class IPL(Base):
    __tablename__ = "ipl"
    
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id", nullable=False))
    
    month = Column(String, nullable=False)
    amount = Column(Numeric(15, 2,), nullable=False)
    due_day = Column(Integer, nullable=False)
    
    status = Column(Enum(IPLStatus), default=IPLStatus.pending)
    
    proof = Column(String , nullable=True)
    
    #relationship
    user = relationship("User", back_populates="ipls")
    payments = relationship("Payment", back_populates="ipl", cascade="all, delete")