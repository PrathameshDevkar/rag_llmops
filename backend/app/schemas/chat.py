from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    question:str
    conversation_id:Optional[str]=None
    document_id:Optional[str]=None
    
class ChatResponse(BaseModel):
    conversation_id:str
    answer:str