from fastapi import FastAPI
from backend.app.api.health import router as health_router
# from backend.app.api.db_test import router as db_router
from backend.app.core.config import settings
from backend.app.api.users import router as user_router
from backend.app.api.auth import router as auth_router
# from backend.app.api.me import router as me_router
from backend.app.api.documents import router as document_router
# from backend.app.api.retrieval_test import router as retrieval_router
from backend.app.api.chat import router as chat_router
from backend.app.api.conversations import router as conversation_router
from backend.app.api.messages import router as get_messages

app = FastAPI(title=settings.PROJECT_NAME)


app.include_router(health_router)
# app.include_router(db_router)
app.include_router(user_router)
app.include_router(auth_router)
# app.include_router(me_router)
app.include_router(document_router)
# app.include_router(retrieval_router)
app.include_router(chat_router)
app.include_router(conversation_router)
app.include_router(get_messages)


@app.get("/")
def root():
    return {"message": "Backend running"}




