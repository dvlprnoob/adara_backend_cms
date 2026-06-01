from sqlalchemy import Boolean, Column, Integer, String, Text
from db.base import Base

class Service(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True)
    service_name = Column(String, nullable=False)
    owner_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    phone = Column(String, nullable=False)
    gmaps_link = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
