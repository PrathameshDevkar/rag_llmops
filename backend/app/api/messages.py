from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.core.auth import get_current_user

from colorama import Fore

router= APIRouter(prefix="/messages",tags=["messages"])

@router.get("")
def get_messages(
    conversation_id:str =Query(...),
    db: Session=Depends(get_db) ,
    current_user: User = Depends(get_current_user)   
):
    conversation_repo = ConversationRepository(db)
    conversation = conversation_repo.get_by_id(conversation_id = conversation_id, user_id = str(current_user.id))
    
    #add the defensive validation here, because the conversation returned by get_by_id could be None
    #and the pylance is indicating that if the return is None then the code will crash
    
    if conversation == None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Conversation not found or access denied"
        )
    messages = conversation.messages
    return [
        {
            "role": m.role,
            "content": m.content,
            "created_at": str(m.created_at)
        }
        for m in messages  # ← serialize properly
    ]