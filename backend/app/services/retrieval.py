from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.services.embeddings import embed_text

def similarity_search(
    db: Session,
    query:str,
    document_id:str,
    top_k:int=5
):
    query_embedding=embed_text(query)
    
    sql=text("""
        SELECT content,content_metadata
        FROM chunks
        WHERE document_id = :document_id
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :top_k
        """)
    results=db.execute(
        sql,
        {
            "document_id":document_id,
            "query_embedding":query_embedding,
            "top_k":top_k
        }
    ).fetchall()
    
    return results