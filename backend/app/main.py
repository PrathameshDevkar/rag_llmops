from fastapi import FastAPI, Request, status
from backend.app.api.health import router as health_router
from backend.app.core.config import settings
from backend.app.api.users import router as user_router
from backend.app.api.auth import router as auth_router
from backend.app.api.documents import router as document_router
from backend.app.api.chat import router as chat_router
from backend.app.api.conversations import router as conversation_router
from backend.app.api.messages import router as get_messages
from backend.app.rag.checkpoint import get_checkpointer
from backend.app.rag.graph import build_graph
from backend.app.core.custom_exception import DocumentPortalException
from backend.app.core.logging import GLOBAL_LOGGER as log

from contextlib import asynccontextmanager
from colorama import Fore
from fastapi.responses import JSONResponse
@asynccontextmanager
async def lifespan(app:FastAPI):
    #this runs on startup
    print(Fore.YELLOW + "=========Initializing the production langgraph state runner============" + Fore.RESET)

    with get_checkpointer() as checkpointer:
        checkpointer.setup()
        app.state.graph = build_graph(checkpointer) 

        yield
    #This runs on shutdown
    print(Fore.YELLOW + "=========Shutting down the production langgraph state runner============" + Fore.RESET)
    
app = FastAPI(title=settings.PROJECT_NAME, lifespan = lifespan)


app.include_router(health_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(document_router)
app.include_router(chat_router)
app.include_router(conversation_router)
app.include_router(get_messages)


@app.get("/")
def root():
    return {"message": "Backend running"}


@app.exception_handler(DocumentPortalException)
def document_portal_exception_handler(request: Request, exc: DocumentPortalException):
    """ Intercepts custom tracking errors, logs JSON strings, and returns clean API errors """
    
    # 1. Log the structured error with its embedded file and line parameters
    log.error("application_exception_intercepted",
              source_file=exc.file_name,
              line_number=exc.lineno,
              message=exc.error_message)
              
    # 2. Return a clean payload back to your Streamlit frontend client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerProcessingError",
            "message": exc.error_message,
            "location": f"{exc.file_name} L#{exc.lineno}"
        }
    )

