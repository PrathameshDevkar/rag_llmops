from sqlalchemy.orm import Session
from backend.app.models.memories import Memories

class MemoriesRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def create(self, memory : Memories):
        self.db.add(memory)
        self.db.commit()