import os
from fastapi import APIRouter, HTTPException, Depends,UploadFile, File
from sqlalchemy.orm import Session
import shutil

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.core.auth import get_current_user
from backend.app.models.document import Document
from backend.app.models.base import Chunk
from backend.app.services.pdf_loader_chunker import load_and_chunk_pdf
from backend.app.services.embeddings import embed_text

router=APIRouter(prefix="/documents",tags=["documents"])

@router.post("/upload")
def upload_document(
    file:UploadFile=File(...),
    db:Session=Depends(get_db),
    current_user: User=Depends(get_current_user)
):
            
    if file.content_type!="application/pdf":
        raise HTTPException(status_code=400, detail="only PDF files are allowed")
    
    #Create document DB entry first
    document=Document(
        user_id=current_user.id,
        filename=file.filename,
        file_path=""
    )

    db.add(document)
    db.commit()
    db.refresh(document)
    
    #create user folder
    user_folder=f"backend/pdf_storage_2/{current_user.id}"
    os.makedirs(user_folder,exist_ok=True)
    
        #final file path
    file_path=f"{user_folder}/{document.id}.pdf"
    
    #save file
    with open(file_path,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)
        
    #update path in db
    document.file_path=file_path
    db.commit()
    
    lc_chunks=load_and_chunk_pdf(file_path)
    
    for idx,lc_doc in enumerate(lc_chunks):
        embeddings= embed_text(lc_doc.page_content)

        chunk=Chunk(
            document_id=document.id,
            chunk_index=idx,
            content=lc_doc.page_content,
            content_metadata=lc_doc.metadata,
            embedding=embeddings
        )
        
        db.add(chunk)
    
    db.commit()
    
    return{
        "document_id":str(document.id),
        "filename":document.filename,
        "file_path":document.file_path
    }
    
@router.get("/document_list")
def list_documents(                
        db: Session=Depends(get_db),
        current_user: User= Depends(get_current_user)
            ):
    documents=(
        db.query(Document)
        .filter(Document.user_id==current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    for doc in documents:
        print("*"*50)
                    
    return [
        {
            "document_id":str(doc.id),
            "document_name":doc.filename,
            "uploaded_at":doc.uploaded_at
        }
        for doc in documents
    ]