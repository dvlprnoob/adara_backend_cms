from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.session import Base


class ConstructionProgress(Base):
    __tablename__ = "construction_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    status = Column(String, default="pondasi", nullable=False)
    percent = Column(Integer, default=10, nullable=False)
    is_done = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="construction_progress")
    updates = relationship(
        "ConstructionProgressUpdate",
        back_populates="progress",
        cascade="all, delete-orphan",
        order_by="ConstructionProgressUpdate.created_at.desc()",
    )


class ConstructionProgressUpdate(Base):
    __tablename__ = "construction_progress_updates"

    id = Column(Integer, primary_key=True, index=True)
    progress_id = Column(Integer, ForeignKey("construction_progress.id"), nullable=False, index=True)
    note = Column(Text, nullable=False)
    photos = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    progress = relationship("ConstructionProgress", back_populates="updates")
