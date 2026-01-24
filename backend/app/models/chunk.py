import uuid
from sqlalchemy import Column, ForeignKey, Text, Integer,JSON
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from backend.app.core.database import Base

class Chunk(Base):
    __tablename__ = "chunks" 
    
    id= Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    document_id=Column(UUID(as_uuid=True), ForeignKey("documents.id",ondelete="CASCADE"),
                       nullable=False)
    chunk_index=Column(Integer, nullable=False)
    content=Column(Text,nullable=False)
    content_metadata = Column(JSON, nullable=True)
    
    embedding = Column(Vector(384))
