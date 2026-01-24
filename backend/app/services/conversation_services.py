from sqlalchemy.orm import Session
from backend.app.models.conversations import Conversation
from backend.app.models.messages import Messages

def create_conversation(
    db: Session,
    user_id:str,
    document_id:str
) -> Conversation:
    conv=Conversation(
        user_id=user_id,
        document_id=document_id
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

def add_message(
    db:Session,
    conversation_id:str,
    role:str,
    content:str
    ):
    
    msg=Messages(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    
    db.add(msg)
    db.commit()
    
    
def get_conversation_messages(
    db:Session,
    conversation_id=str
):
    return (
        db.query(Messages)
        .filter(Messages.conversation_id==conversation_id)
        .order_by(Messages.created_at)
        .all()
    )