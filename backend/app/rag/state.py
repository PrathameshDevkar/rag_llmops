from typing import TypedDict, List, Optional

class RAGState(TypedDict):
    user_id:str
    document_id: str
    user_question: str 
    retrieved_chunks:Optional[List[str]]
    recalled_memories: Optional[List[dict]]
    generated_answer:Optional[str]
    chat_history:Optional[List[str]]
    