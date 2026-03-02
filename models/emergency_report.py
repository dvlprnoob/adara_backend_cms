from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from db.base import Base

class EmergencyReport(Base):
    __tablename__ = 'emergency_reports'
    
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    user_name = Column(String, nullable=False)
    block = Column(String, nullable=False)

    type_id = Column(Integer, ForeignKey("emergency_types.id"))
    type_name = Column(String, nullable=False)
    
    status = Column(String , default="active") # active , resolved
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())