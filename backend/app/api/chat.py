# from sqlalchemy.orm import Session
# from fastapi import APIRouter, Depends, HTTPException, Request

# from backend.app.core.database import get_db
# from backend.app.models.user import User
# from backend.app.models.conversations import Conversation
# from backend.app.core.auth import get_current_user
# from backend.app.schemas.chat import ChatRequest, ChatResponse
# from backend.app.services.conversation_services import (create_conversation, add_message,generate_conversation_title)
# from backend.app.services.memory_service import add_episodic_memory
# from backend.app.repositories.conversation_repository import ConversationRepository
# from backend.app.rag.graph import build_graph
# from backend.app.rag.checkpoint import get_checkpointer
# from fastapi.responses import StreamingResponse
# from langchain_core.messages import AIMessage

# from colorama import Fore

# router = APIRouter(prefix="/chat",tags=["chat"])
# @router.post("",response_model=ChatResponse)
# def chat(
#     chat_in:ChatRequest,
#     request: Request,
#     db: Session=Depends(get_db),
#     current_user: User=Depends(get_current_user)
# ):
#     title = ""
#     document_id = ""
#     #validate input
#     if not chat_in.conversation_id and not chat_in.document_id:
#         return HTTPException(
#             status_code=400,
#             detail="document_id is required to start a conversation"
#         )
    
#     print(Fore.YELLOW + f"\n\n=====conversation_id in api/chat.py is: {chat_in.conversation_id}=========\n\n" + Fore.RESET)
#     print(Fore.YELLOW + f"\n\n=====document_id in api/chat.py is : {chat_in.document_id}=========\n\n" + Fore.RESET)

#     conversation_repo = ConversationRepository(db)
#     if chat_in.conversation_id:
#         conversation_id=chat_in.conversation_id
#         conversation = conversation_repo.get_by_id(user_id = str(current_user.id), conversation_id = conversation_id)
#         if not conversation:
#             raise HTTPException(status_code=404, detail="Conversation not found")
        
#         # Derive document_id safely from backend state, ignoring whatever the frontend sent
#         document_id = str(conversation.document_id)
        
#     else:
#         conversation= create_conversation(
#             db,
#             user_id=str(current_user.id),
#             document_id=chat_in.document_id
#         )
#         document_id = chat_in.document_id
#         conversation_id=str(conversation.id)
#         title = generate_conversation_title(chat_in.question)
                
#     add_message(
#         db=db,
#         conversation_id=conversation_id,
#         role= "user",
#         content=chat_in.question
#     )
    
    
#     chat_history=[
#         f"{m.role}={m.content}"
#         for m in conversation.messages
#     ]
#     print(Fore.YELLOW + f"\n\n===========chat history in api/chat.py is: {chat_history}===================\n\n" + Fore.RESET)
    
    
#     state={
#         "user_id":str(current_user.id),
#         "document_id":document_id,
#         "user_question": chat_in.question,
#         "chat_history":chat_history,
#         "retrieved_chunks":None,
#         "recalled_memories": None,
#         "generated_answer":None
#     }
    
#     graph = request.app.state.graph


#     def event_generator():
#         final_answer = ""
#         try:
#             for event,metadata in graph.stream(
#                 state,
#                 config={
#                     "configurable": {
#                         "thread_id": conversation_id
#                     }
#                 },
#                 stream_mode='messages'
#             ):

#                 if isinstance(event,AIMessage):
#                     final_answer+= event.content
#                     yield event.content
        
        
#         finally:
                       
#             if final_answer:
#                 add_message(
#                     db,
#                     conversation_id,
#                     role="assistant",
#                     content=final_answer
#                 )
                
#                 chat_turn_text = f"User:{chat_in.question}\nAssistant:{final_answer}"
                
#                 add_episodic_memory(
#                     db=db,
#                     user_id = str(current_user.id),
#                     conversation_id = conversation_id,
#                     chat_turn_text = chat_turn_text
#                 )
                
#     return StreamingResponse(
#     event_generator(),
#     media_type="text/plain",
#     headers={"x-conversation-id": conversation_id,
#              "x-conversation-title":title if title else conversation_id[:8]
#              }
#     )

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from langchain_core.messages import AIMessage

from backend.app.core.database import get_db
from backend.app.core.auth import get_current_user
from backend.app.models.user import User
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.chat_service import ChatService # Import service layer

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

@router.post("", response_model=ChatResponse)
def chat(
    chat_in: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Enforce fast edge-validation constraints
    if not chat_in.conversation_id and not chat_in.document_id:
        logger.warning(f"Rejected malformed chat submission from user workspace: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_id is required to start a conversation"
        )
    
    # Instantiate service layer
    chat_service = ChatService(db)
    
    # Delegate core context processing execution steps to the service manager
    context_bundle = chat_service.orchestrate_chat_state(chat_in, user_id=str(current_user.id))
    if not context_bundle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation lookup context invalid")
        
    conversation_id = context_bundle["conversation_id"]
    
    # Initialize state map matching your graph parameters
    state = {
        "user_id": str(current_user.id),
        "document_id": context_bundle["document_id"],
        "user_question": chat_in.question,
        "chat_history": context_bundle["chat_history"],
        "retrieved_chunks": None,
        "recalled_memories": None,
        "generated_answer": None
    }
    
    graph = request.app.state.graph
    
    def event_generator():
        final_answer = ""
        try:
            for event, metadata in graph.stream(
                state,
                config={"configurable": {"thread_id": conversation_id}},
                stream_mode='messages'
            ):
                if isinstance(event, AIMessage):
                    final_answer += event.content
                    yield event.content
        finally:
            if final_answer:
                # Delegate secondary background processing out of the stream execution line
                chat_service.execute_post_chat_cleanup(
                    user_id=str(current_user.id),
                    conversation_id=conversation_id,
                    question=chat_in.question,
                    final_answer=final_answer
                )
                
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "x-conversation-id": conversation_id,
            "x-conversation-title": context_bundle["title"] if context_bundle["title"] else conversation_id[:8]
        }
    )