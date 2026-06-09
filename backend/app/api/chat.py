from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Request

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.conversations import Conversation
from backend.app.core.auth import get_current_user
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.conversation_services import (create_conversation, add_message, get_conversation_messages,generate_conversation_title)
from backend.app.services.memory_service import add_episodic_memory
from backend.app.rag.graph import build_graph
from backend.app.rag.checkpoint import get_checkpointer
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage

from colorama import Fore

router = APIRouter(prefix="/chat",tags=["chat"])
@router.post("",response_model=ChatResponse)
def chat(
    chat_in:ChatRequest,
    request: Request,
    db: Session=Depends(get_db),
    current_user: User=Depends(get_current_user)
):
    title = ""
    document_id = ""
    #validate input
    if not chat_in.conversation_id and not chat_in.document_id:
        return HTTPException(
            status_code=400,
            detail="document_id is required to start a conversation"
        )
    
    print(Fore.YELLOW + f"\n\n=====conversation_id in api/chat.py is: {chat_in.conversation_id}=========\n\n" + Fore.RESET)
    print(Fore.YELLOW + f"\n\n=====document_id in api/chat.py is : {chat_in.document_id}=========\n\n" + Fore.RESET)

    if chat_in.conversation_id:
        conversation_id=chat_in.conversation_id
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Derive document_id safely from backend state, ignoring whatever the frontend sent
        document_id = str(conversation.document_id)
        
    else:
        conversation= create_conversation(
            db,
            user_id=current_user.id,
            document_id=chat_in.document_id
        )
        document_id = chat_in.document_id
        conversation_id=str(conversation.id)
        title = generate_conversation_title(chat_in.question)
                
    add_message(
        db=db,
        conversation_id=conversation_id,
        role= "user",
        content=chat_in.question
    )
    
    messages=get_conversation_messages(db,conversation_id)
    
    chat_history=[
        f"{m.role}={m.content}"
        for m in messages
    ]
    print(Fore.YELLOW + f"\n\n===========chat history in api/chat.py is: {chat_history}===================\n\n" + Fore.RESET)
    
    graph = request.app.state.graph
    
    state={
        "user_id":str(current_user.id),
        "document_id":document_id,
        "user_question": chat_in.question,
        "chat_history":chat_history,
        "retrieved_chunks":None,
        "recalled_memories": None,
        "generated_answer":None
    }
    
    def event_generator():
        final_answer = ""
        try:
            for event,metadata in graph.stream(
                state,
                config={
                    "configurable": {
                        "thread_id": conversation_id
                    }
                },
                stream_mode='messages'
            ):

                if isinstance(event,AIMessage):

                    final_answer+= event.content
                    yield event.content
        
        
        finally:
                       
            if final_answer:
                add_message(
                    db,
                    conversation_id,
                    role="assistant",
                    content=final_answer
                )
                
                chat_turn_text = f"User:{chat_in.question}\nAssistant:{final_answer}"
                
                add_episodic_memory(
                    db=db,
                    user_id = str(current_user.id),
                    conversation_id = conversation_id,
                    chat_turn_text = chat_turn_text
                )
                
    return StreamingResponse(
    event_generator(),
    media_type="text/plain",
    headers={"x-conversation-id": conversation_id,
             "x-conversation-title":title if title else conversation_id[:8]
             }
    )