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

    # ✅ Virtual field
    @property
    def role_name(self):
        return self.role.name if self.role else None
    
    
    installments = relationship("Installment", back_populates="user")
    ipls = relationship("IPL", back_populates="user")
    # payments = relationship("Payment", back_populates="user")