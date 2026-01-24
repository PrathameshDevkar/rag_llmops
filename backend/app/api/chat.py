# from sqlalchemy.orm import Session
# from fastapi import APIRouter, Depends, HTTPException

# from backend.app.core.database import get_db
# from backend.app.models.user import User
# from backend.app.core.auth import get_current_user
# from backend.app.schemas.chat import ChatRequest, ChatResponse
# from backend.app.services.conversation_services import (create_conversation, add_message, get_conversation_messages)
# from backend.app.rag.graph import build_graph
# from backend.app.rag.checkpoint import get_checkpointer


# router = APIRouter(prefix="/chat",tags=["chat"])

# @router.post("",response_model=ChatResponse)
# def chat(
#     chat_in:ChatRequest,
#     db: Session=Depends(get_db),
#     current_user: User=Depends(get_current_user)
# ):
#     #validate input
#     if not chat_in.conversation_id and not chat_in.document_id:
#         return HTTPException(
#             status_code=400,
#             detail="document_id is required to start a conversation"
#         )
    
#     if chat_in.conversation_id:
#         conversation_id=chat_in.conversation_id
#     else:
#         conversation= create_conversation(
#             db,
#             user_id=current_user.id,
#             document_id=chat_in.document_id
#         )
#         conversation_id=str(conversation.id)
        
#     add_message(
#         db=db,
#         conversation_id=conversation_id,
#         role= "user",
#         content=chat_in.question
#     )
    
#     messages=get_conversation_messages(db,conversation_id)
    
#     chat_history=[
#         f"{m.role}={m.content}"
#         for m in messages
#     ]
        
#     state={
#         "user_id":str(current_user.id),
#         "document_id":chat_in.document_id,
#         "user_question": chat_in.question,
#         "chat_history":chat_history,
#         "retrieved_chunks":None,
#         "generated_answer":None
#     }
    
#     with get_checkpointer() as checkpointer:
#         graph = build_graph(checkpointer)

#         result = graph.invoke(
#             state,
#             config={
#                 "configurable": {
#                     "thread_id": conversation_id
#                 }
#             }
#         )

    
#     # result= graph.invoke(state)
#     answer=result["generated_answer"]
    
#     add_message(
#         db,
#         conversation_id,
#         role="assistant",
#         content=answer
#     )
    
#     return ChatResponse(
#         conversation_id=conversation_id,
#         answer=answer
#     )

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.core.auth import get_current_user
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.conversation_services import (create_conversation, add_message, get_conversation_messages)
from backend.app.rag.graph import build_graph
from backend.app.rag.checkpoint import get_checkpointer
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage

router = APIRouter(prefix="/chat",tags=["chat"])

@router.post("",response_model=ChatResponse)
def chat(
    chat_in:ChatRequest,
    db: Session=Depends(get_db),
    current_user: User=Depends(get_current_user)
):
    #validate input
    if not chat_in.conversation_id and not chat_in.document_id:
        return HTTPException(
            status_code=400,
            detail="document_id is required to start a conversation"
        )
    
    if chat_in.conversation_id:
        conversation_id=chat_in.conversation_id
        print("*"*50)
        with open(r"C:\Users\Prathamesh\prathamesh\llmops_rag_langgraph\backend\error.txt","a") as f_1:
            f_1.write(f"conversation id exists {conversation_id}")
            f_1.write("\n\n")
        print("conversation id exists" ,conversation_id)
        print("*"*50)

    else:
        conversation= create_conversation(
            db,
            user_id=current_user.id,
            document_id=chat_in.document_id
        )
        conversation_id=str(conversation.id)
        print("*"*50)
        with open(r"C:\Users\Prathamesh\prathamesh\llmops_rag_langgraph\backend\error.txt","a") as f_1:
            f_1.write(f"conversation id doesnt exists {conversation_id}")
            f_1.write("\n\n")
        print("conversation id doesnt exists" ,conversation_id)
        print("*"*50)

        
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
        
    state={
        "user_id":str(current_user.id),
        "document_id":chat_in.document_id,
        "user_question": chat_in.question,
        "chat_history":chat_history,
        "retrieved_chunks":None,
        "generated_answer":None
    }
    
    def event_generator():
        final_answer = ""
        try:
            with get_checkpointer() as checkpointer:
                checkpointer.setup()
                graph = build_graph(checkpointer)

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
            print("*"*20)
            with open(r"C:\Users\Prathamesh\prathamesh\llmops_rag_langgraph\backend\error.txt","a") as f_1:
                f_1.write(f"final_answer {final_answer}")
                f_1.write("\n\n")
            print("final answer is",final_answer)
            print("final answer type is",type(final_answer))
            print("*"*20)            
            if final_answer:
                add_message(
                    db,
                    conversation_id,
                    role="assistant",
                    content=final_answer
                )


    
    # result= graph.invoke(state)
    # answer=result["generated_answer"]
    
   
    
    # return ChatResponse(
    #     conversation_id=conversation_id,
    #     answer=answer
    # )
    return StreamingResponse(
    event_generator(),
    media_type="text/plain"
    )