import pytest
import uuid
from backend.app.models.document import Document
from backend.app.models.conversations import Conversation
from backend.app.models.messages import Messages
from backend.app.models.memories import Memories

from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.repositories.messages_repository import MessagesRepository
from backend.app.repositories.memories_repositories import MemoriesRepository

def test_document_repository_workflow(db_session, test_user):
    doc_repo = DocumentRepository(db_session)
    doc = Document(user_id=test_user.id, filename="architecture.pdf", file_path="/path/to/file")
    
    doc_repo.create(doc)
    assert doc.id is not None

    user_docs = doc_repo.get_user_documents(str(test_user.id))
    assert len(user_docs) == 1
    assert user_docs[0].filename == "architecture.pdf"

def test_conversation_repository_workflow(db_session, test_user):
    doc = Document(user_id=test_user.id, filename="specs.pdf", file_path="")
    db_session.add(doc)
    db_session.commit()

    conv_repo = ConversationRepository(db_session)
    conv = Conversation(user_id=test_user.id, document_id=doc.id, title="Specs Review")
    
    conv_repo.create(conv)
    
    fetched = conv_repo.get_by_id(user_id=str(test_user.id), conversation_id=str(conv.id))
    assert fetched is not None
    assert fetched.title == "Specs Review"

def test_messages_and_memories_repositories(db_session, test_user):
    doc = Document(user_id=test_user.id, filename="data.pdf", file_path="")
    db_session.add(doc)
    db_session.commit()
    
    conv = Conversation(user_id=test_user.id, document_id=doc.id, title="Data Run")
    db_session.add(conv)
    db_session.commit()

    msg_repo = MessagesRepository(db_session)
    msg = Messages(conversation_id=conv.id, role="assistant", content="Answer statement")
    msg_repo.create(msg)
    assert msg.id is not None

    mem_repo = MemoriesRepository(db_session)
    memory = Memories(
        user_id=test_user.id, 
        conversation_id=conv.id, 
        memory_type="episodic_memory", 
        content="{}", 
        embedding=[0.0]*384
    )
    mem_repo.create(memory)
    assert memory.id is not None