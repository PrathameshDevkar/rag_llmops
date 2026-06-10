import uuid 
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Memories(Base):
    __tablename__ = "memories"
     
    id = Column(UUID(as_uuid=True),primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    conversation_id = Column(UUID(as_uuid=True),ForeignKey("conversations.id",ondelete="CASCADE"),nullable=False)
    memory_type = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    embedding=Column(Vector)
    created_at=Column(DateTime(timezone=True),server_default=func.now())

    user = relationship("User", back_populates="memories")
    conversation = relationship("Conversation", back_populates="memories")