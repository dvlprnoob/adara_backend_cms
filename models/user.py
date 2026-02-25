from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from db.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role")
    
    is_active = Column(Boolean, default=True)