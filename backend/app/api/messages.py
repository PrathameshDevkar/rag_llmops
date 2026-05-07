from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.conversation_services import get_conversation_messages

router= APIRouter(prefix="/messages",tags=["messages"])

@router.get("")
def get_messages(
    conversation_id:str =Query(...),
    db: Session=Depends(get_db)    
):
    messages = get_conversation_messages(db,conversation_id )
    return messages