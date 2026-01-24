from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.conversations import Conversation
from backend.app.models.user import User
from backend.app.core.auth import get_current_user

router = APIRouter(prefix="/conversations",tags=["conversatio"])

@router.get("")
def list_conversation(
    db: Session=Depends(get_db),
    document_id: str= Query(...),
    current_user: User= Depends(get_current_user)
):

    conversations= (
        db.query(Conversation)
        .filter(
            Conversation.user_id==current_user.id,
            Conversation.document_id==document_id
        )
        .order_by(Conversation.created_at.desc())
        .all()
    )
    for conv in conversations:
        print("*"*50)
        with open(r"C:\Users\Prathamesh\prathamesh\llmops_rag_langgraph\backend\error.txt","a") as f_1:
            f_1.write(f"returned conversations id from endpoint conversations are {str(conv.id)}")
            f_1.write("\n\n")
        print("returned conversations id from endpoint conversations are",str(conv.id))
        print("*"*50)

    return [
        {
            "conversation_id":str(conv.id),
            "created_at":conv.created_at
        }
        for conv in conversations
    ]