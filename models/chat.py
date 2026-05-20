from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.session import Base


class ChatThread(Base):
    __tablename__ = "chat_threads"

    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    status = Column(String, default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    resident = relationship("User", foreign_keys=[resident_id], back_populates="chat_thread")
    messages = relationship(
        "ChatMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("chat_threads.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_role = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read_by_admin = Column(Boolean, default=False)
    is_read_by_resident = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    thread = relationship("ChatThread", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
