import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from backend.app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)


"""

class User(Base):
 __tablename__ = "users"
 
 id = Column(uuid(), primary_key)
 username = COlumn(string)
 password = Column(string)

"""