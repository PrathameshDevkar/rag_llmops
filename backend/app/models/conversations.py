from sqlalchemy import Column, ForeignKey, DateTime 
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.app.core.database import Base

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    user_id=Column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    document_id=Column(UUID(as_uuid=True),ForeignKey("documents.id",ondelete="CASCADE"),nullable=False)
    
    created_at=Column(DateTime(timezone=True),server_default=func.now())