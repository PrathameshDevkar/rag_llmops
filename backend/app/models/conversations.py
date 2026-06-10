from sqlalchemy import Column, ForeignKey, DateTime, String
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    user_id=Column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    document_id=Column(UUID(as_uuid=True),ForeignKey("documents.id",ondelete="CASCADE"),nullable=False)
    title = Column(String, nullable=True)
    created_at=Column(DateTime(timezone=True),server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    document = relationship("Document", back_populates="conversations")
    messages = relationship("Messages", back_populates="conversation", cascade="all, delete-orphan", order_by="Messages.created_at")
    memories = relationship("Memories", back_populates="conversation", cascade="all, delete-orphan")