import pytest
from backend.app.models.memories import Memories
from backend.app.services.retrieval import memories_retrieval
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.conversations import Conversation
import uuid

def test_memories_retrieval_isolation_boundaries(db_session, test_user):
    target_user_id = str(test_user.id)
    
    # 1. Provision an alternative user to evaluate isolation checks
    alt_user = User(username="isolated_tenant", password_hash="secure_fallback_hash")
    db_session.add(alt_user)
    db_session.commit()
    
    # 2. Provision parent document entries
    doc_target = Document(user_id=test_user.id, filename="target.pdf", file_path="")
    doc_alt = Document(user_id=alt_user.id, filename="alt.pdf", file_path="")
    db_session.add_all([doc_target, doc_alt])
    db_session.commit()
    
    # 3. Provision parent conversation entities to satisfy the foreign keys
    conv_target = Conversation(user_id=test_user.id, document_id=doc_target.id, title="Main Context")
    conv_alt = Conversation(user_id=alt_user.id, document_id=doc_alt.id, title="Leak Check Context")
    db_session.add_all([conv_target, conv_alt])
    db_session.commit()
    
    #the above 3 steps solves the issue of foreign key dilema as the conversation table will have the id which the memories table is using
    
    base_vector = [0.25] * 384


    # Match the vector dimensions
    mem_target = Memories(
        id=uuid.uuid4(),
        user_id=target_user_id,
        conversation_id=conv_target.id,
        memory_type="episodic_memory",
        content="Target profile summary text asset",
        embedding=base_vector
    )
    mem_leak_block = Memories(
        id=uuid.uuid4(),
        user_id=alt_user.id,
        conversation_id=conv_alt.id,
        memory_type="episodic_memory",
        content="Cross-tenant leakage vector block",
        embedding=base_vector
    )
    
    db_session.add_all([mem_target, mem_leak_block])
    db_session.commit()
    
    results = memories_retrieval(db=db_session, query_embedding=base_vector, user_id=target_user_id, top_k=5)
    
    assert len(results) == 1
    assert results[0].content == "Target profile summary text asset"
    assert "Cross-tenant leakage vector block" not in [r.content for r in results]