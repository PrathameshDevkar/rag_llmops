from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.conversation_services import get_conversation_messages

from colorama import Fore

router= APIRouter(prefix="/messages",tags=["messages"])

@router.get("")
def get_messages(
    conversation_id:str =Query(...),
    db: Session=Depends(get_db)    
):
    messages = get_conversation_messages(db,conversation_id )
    print(Fore.YELLOW + f"\n\nmessages in the get_message are:{messages}\n\n" + Fore.RESET)
    return [
        {
            "role": m.role,
            "content": m.content,
            "created_at": str(m.created_at)
        }
        for m in messages  # ← serialize properly
    ]