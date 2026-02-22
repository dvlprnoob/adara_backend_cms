#models/role.py
from sqlalchemy import Column, Integer, String
from db.session import Base

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True) #super_admin, admin, resident