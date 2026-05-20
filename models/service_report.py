from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.session import Base


class ServiceReport(Base):
    __tablename__ = "service_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    report_type = Column(String, nullable=False)  # employee, environment
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="open", nullable=False)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
