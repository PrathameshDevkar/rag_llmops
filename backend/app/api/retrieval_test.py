# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session

# from backend.app.core.database import get_db
# from backend.app.services.retrieval import similarity_search

# router= APIRouter(prefix="/retrieval", tags=["retrieval"])

# @router.get("/test")
# def test_retrieval(
#     query: str,
#     document_id: str,
#     db: Session=Depends(get_db)
# ):
#     results=similarity_search(db,query,document_id)
    
#     return [
#         {
#             "content":r.content[:200],
#             "metadata":r.content_metadata
#         }
#         for r in results]
