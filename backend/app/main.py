from fastapi import FastAPI
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

from contextlib import asynccontextmanager

from colorama import Fore

from backend.app.core.logger import setup_logging
setup_logging()

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




