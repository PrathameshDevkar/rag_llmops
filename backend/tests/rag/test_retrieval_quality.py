import pytest
from sqlalchemy import text
from backend.app.models.document import Document
from backend.app.models.chunk import Chunk
from backend.app.services.retrieval import chunks_retrieval
import uuid

def test_pgvector_chunks_cosine_similarity_sorting(db_session,test_user):
    
    # Provision the parent Document record first to maintain relational sanity
    document = Document(
        user_id=test_user.id,
        filename="attention_research.pdf",
        file_path="/mock/storage/path.pdf"
    )
    db_session.add(document)
    db_session.commit()
    
    doc_id = document.id
    
    # Seed distinct vectors of 384 dimensions
    vec_a = [1.0] + [0.0] * 383  # Facing Axis X
    vec_b = [0.0] + [1.0] * 383  # Perpendicular
    vec_c = [0.9] + [0.1] * 383  # Highly similar to Axis X
    
    chunk_a = Chunk(id=uuid.uuid4(), document_id=doc_id, chunk_index=0, content="Target Content Source", embedding=vec_a)
    chunk_b = Chunk(id=uuid.uuid4(), document_id=doc_id, chunk_index=1, content="Irrelevant Noise Content", embedding=vec_b)
    chunk_c = Chunk(id=uuid.uuid4(), document_id=doc_id, chunk_index=2, content="Partial Match Source Context", embedding=vec_c)
    
    db_session.add_all([chunk_a, chunk_b, chunk_c])
    db_session.commit()
    
    # Query with a vector targeting Axis X directly
    query_vector = [1.0] + [0.0] * 383
    results = chunks_retrieval(db=db_session, query_embedding=query_vector, document_id=doc_id, top_k=2)
    
    assert len(results) == 2
    # Chunk A should always be the top result based on cosine distance (<=>) minimization
    assert results[0].content == "Target Content Source"
    assert results[1].content == "Partial Match Source Context"