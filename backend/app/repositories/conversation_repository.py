from sqlalchemy.orm import Session
from backend.app.models.conversations import Conversation


class ConversationRepository:
    def __init__(self, db:Session):
        self.db = db
    
    def get_by_id(self, user_id: str, conversation_id: str) -> Conversation | None:
        return self.db.query(Conversation).filter(Conversation.id==conversation_id, Conversation.user_id == user_id).first()
    
    def create(self, conversation:Conversation):
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
