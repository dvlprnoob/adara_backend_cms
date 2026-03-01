from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from db.base import Base

class EmergencyType(Base):
    __tablename__ = 'emergency_types'
    
    id =  Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    is_active = Column(Boolean, default=True)
    
    # NULL = Global(admin CMS)
    # NOT NULL = personal( resident mobile )
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    