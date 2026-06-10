from sqlalchemy.orm import Session
from backend.app.models.messages import Messages

class MessagesRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def create(self, messages : Messages):
        self.db.add(messages)
        self.db.commit()