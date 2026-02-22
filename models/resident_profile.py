from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.session import Base

class ResidentProfile(Base):
    __tablename__ = 'resident_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    address = Column(String)
    block = Column(String)
    phone = Column(String)
    npwp = Column(String, nullable=True)
    total_people = Column(Integer)
    ktp_number = Column(String ,nullable=True)
    
    user = relationship("User")