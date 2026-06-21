import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.app.core.database import Base
from sqlalchemy.orm import relationship

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    user_id=Column(
        UUID(as_uuid=True),
        ForeignKey("users.id",ondelete="CASCADE"),
        nullable=False
    )
    
    filename=Column(String,nullable=False)
    file_path=Column(String,nullable=False)
    
    uploaded_at=Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan", order_by ="and_(Chunk.document_id, Chunk.chunk_index)")
    conversations = relationship("Conversation", back_populates="document", cascade="all, delete-orphan")