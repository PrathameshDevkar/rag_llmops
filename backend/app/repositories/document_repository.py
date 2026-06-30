from sqlalchemy.orm import Session
from backend.app.models.document import Document

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def get_by_id(self, document_id: str) ->Document | None:
        return self.db.query(Document).filter(Document.id == document_id).first()
        
    def get_user_documents(self, user_id: str) -> list[Document]:
        return(
            self.db.query(Document)
            .filter(Document.user_id==user_id)
            .order_by(Document.uploaded_at.desc())
            .all()
        )
    
    def create(self, document:Document):
        self.db.add(document)
        self.db.flush()
        self.db.refresh(document)
        
    
    