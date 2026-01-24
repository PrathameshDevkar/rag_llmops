import uuid
from sqlalchemy import Column, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.app.core.database import Base

class Messages(Base):
    __tablename__= "messages"
    
    id=Column(UUID(as_uuid=True),primary_key=True ,default=uuid.uuid4)
    
    conversation_id=Column(UUID(as_uuid=True),ForeignKey("conversations.id",ondelete="CASCADE"),nullable=False)
    
    role=Column(Text,nullable=False)
    content=Column(Text,nullable=False)
    
    created_at=Column(DateTime(timezone=True),server_default=func.now())
    
    
    