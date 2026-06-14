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

from backend.app.core.logging import GLOBAL_LOGGER as log

router = APIRouter(prefix="/chat", tags=["chat"])
# logger = logging.getLogger(__name__)

@router.post("", response_model=ChatResponse)
def chat(
    chat_in: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Enforce fast edge-validation constraints
    if not chat_in.conversation_id and not chat_in.document_id:
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
                config={"configurable": {"thread_id": conversation_id},
                "metadata": {
                        "user_id": state["user_id"],
                        "document_id": state["document_id"],
                        "conversation_id": conversation_id
                    },
                    "tags": ["production", "streaming-endpoint"]},
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