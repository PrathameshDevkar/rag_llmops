from colorama import Fore
from sqlalchemy.orm import Session
from backend.app.models.conversations import Conversation
from backend.app.models.messages import Messages

from langchain_core.messages import HumanMessage
import os

from backend.app.repositories.conversation_repository import ConversationRepository

from backend.app.repositories.messages_repository import MessagesRepository
from backend.app.services.model_loader import get_llm

model = get_llm()

def generate_conversation_title(question: str) -> str:
    prompt = f"Generate a short 5-7 word title that summarizes this question. Return only the title, nothing else:\n\n{question}"
    response = model.invoke([HumanMessage(content=prompt)])
    print(Fore.CYAN + f"\n\nresponse:{response.content}\ntype is{type(response.content)}\n\n" + Fore.RESET)

    title = response.content.strip()
    # safety fallback in case LLM returns something too long
    if len(title) > 60:
        title = title[:57] + "..."
    return title


def create_conversation(
    db: Session,
    user_id:str,
    document_id:str
) -> Conversation:
    conv=Conversation(
        user_id=user_id,
        document_id=document_id
    )
    conversation_repo = ConversationRepository(db)
    conversation_repo.create(conv)
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
    messages_repo = MessagesRepository(db)
    messages_repo.create(msg)
    
    
# def get_conversation_messages(
#     db:Session,
#     conversation_id=str
# ):
#     return (
#         db.query(Messages)
#         .filter(Messages.conversation_id==conversation_id)
#         .order_by(Messages.created_at)
#         .all()
#     )