from sqlalchemy import Column, Integer, String, Boolean
from db.base import Base

class Banner(Base):
    __tablename__ = "banners"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    link = Column(String, nullable=True)
    photo = Column(String, nullable=False)
    is_active  = Column(Boolean, default=True)