from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.conversations import Conversation
from backend.app.models.user import User
from backend.app.core.auth import get_current_user

router = APIRouter(prefix="/conversations",tags=["conversation"])

@router.get("/conversation_list")
def list_conversation(
    db: Session=Depends(get_db),
    document_id: str= Query(...),
    current_user: User= Depends(get_current_user)
):
    conversations = [
    c for c in current_user.conversations 
    if str(c.document_id) == document_id
    ]    
    return [
        {
            "conversation_id":str(conv.id),
            "title": conv.title,
            "created_at":conv.created_at
        }
        for conv in conversations
    ]