from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.services.embeddings import embed_text

def chunks_retrieval(
    db: Session,
    query_embedding:list[float],
    document_id:str,
    top_k:int=5
):
    
    chunks_sql=text("""
        SELECT content,content_metadata
        FROM chunks
        WHERE document_id = :document_id
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :top_k
        """)
    results=db.execute(
        chunks_sql,
        {
            "document_id":document_id,
            "query_embedding":query_embedding,
            "top_k":top_k
        }
    ).fetchall()
    
    return results

def memories_retrieval(
    db:Session,
    query_embedding:list[float],
    user_id: str,
    top_k :int =5 
):
    memory_sql = text("""
                      SELECT content from memories
                      WHERE user_id = :user_id AND memory_type = 'episodic_memory'
                      ORDER BY embedding <=> CAST(:query_embedding AS vector)
                      LIMIT :top_k
                      """)
    
    results = db.execute(
        memory_sql,
        {
            "user_id": user_id,
            "query_embedding": query_embedding,
            "top_k" : top_k
        }
    ).fetchall()
    
    return results
